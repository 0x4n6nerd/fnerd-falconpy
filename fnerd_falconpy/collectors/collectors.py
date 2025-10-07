"""
Collector classes for specialized data collection operations.
"""

import re
import time
import zipfile
import hashlib
import concurrent.futures
from typing import List, Optional, Dict, Tuple, NamedTuple
from pathlib import Path, PurePath
from datetime import datetime
from fnerd_falconpy.core.base import (
    HostInfo, RTRSession, Platform,
    ILogger, DefaultLogger, IConfigProvider
)
from fnerd_falconpy.managers.managers import FileManager, SessionManager
from fnerd_falconpy.utils.cloud_storage import CloudStorageManager
from fnerd_falconpy.utils.workspace_cleanup import WorkspaceCleanupManager
from fnerd_falconpy.utils.pre_execution_cleanup import PreExecutionCleanupManager


class BrowserArtifact(NamedTuple):
    """Represents a browser artifact to be collected"""
    browser_name: str
    profile: str
    artifact_type: str
    file_path: str
    local_filename: str

class BrowserHistoryCollector:
    """Handles browser history collection operations"""
    
    def __init__(self, file_manager: FileManager, session_manager: SessionManager,
                 config: IConfigProvider, logger: Optional[ILogger] = None):
        """
        Initialize browser history collector
        
        Args:
            file_manager: File manager instance
            session_manager: Session manager instance
            config: Configuration provider
            logger: Logger instance (uses DefaultLogger if not provided)
        """
        self.file_manager = file_manager
        self.session_manager = session_manager
        self.config = config
        self.logger = logger or DefaultLogger("BrowserHistoryCollector")
        
        # Track downloaded files to prevent collisions
        self._downloaded_files = set()
        
    def _sanitize_filename_component(self, component: str, max_length: int = 50) -> str:
        """
        Sanitize a filename component to be filesystem-safe
        
        Args:
            component: String component to sanitize
            max_length: Maximum length for the component
            
        Returns:
            Sanitized string safe for use in filenames
        """
        if not component:
            return "unknown"
            
        # Remove or replace unsafe characters
        # Windows forbidden: < > : " | ? * \ /
        # Also handle spaces, dots, and other problematic chars
        unsafe_chars = '<>:"|?*\\/\x00\r\n\t'
        sanitized = ''.join(c if c not in unsafe_chars else '_' for c in component)
        
        # Replace multiple underscores with single
        sanitized = re.sub('_+', '_', sanitized)
        
        # Remove leading/trailing dots and spaces (Windows issue)
        sanitized = sanitized.strip('. ')
        
        # Ensure not empty after sanitization
        if not sanitized:
            sanitized = "unknown"
            
        # Truncate if too long, but preserve some uniqueness
        if len(sanitized) > max_length:
            # Keep first part and add hash of full string for uniqueness
            hash_suffix = hashlib.md5(component.encode()).hexdigest()[:8]
            truncate_length = max_length - 9  # 8 chars hash + 1 underscore
            sanitized = f"{sanitized[:truncate_length]}_{hash_suffix}"
            
        return sanitized
    
    def _generate_safe_filename(self, username: str, browser: str, profile: str, 
                               file_type: str, hostname: str = None) -> str:
        """
        Generate a safe, unique filename for browser history files
        
        Args:
            username: Target username
            browser: Browser name (Chrome, Firefox, etc.)
            profile: Browser profile name (can be None for single-profile browsers)
            file_type: Type of file (History, places, etc.)
            hostname: Target hostname (for additional uniqueness)
            
        Returns:
            Safe filename with .7z extension
        """
        # Get timestamp for uniqueness
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Sanitize all components
        safe_username = self._sanitize_filename_component(username, 20)
        safe_browser = self._sanitize_filename_component(browser, 15)
        safe_profile = self._sanitize_filename_component(profile, 30) if profile else None
        safe_hostname = self._sanitize_filename_component(hostname, 15) if hostname else None
        
        # Build filename components
        components = [safe_username, safe_browser]
        
        if safe_hostname:
            components.append(safe_hostname)
            
        if safe_profile and safe_profile != "unknown":
            components.append(safe_profile)
            
        components.extend([file_type, timestamp])
        
        # Join with hyphens and add extension
        base_filename = "-".join(components) + ".7z"
        
        # Handle collisions by adding counter
        final_filename = base_filename
        counter = 1
        while final_filename in self._downloaded_files:
            name_without_ext = base_filename[:-3]  # Remove .7z
            final_filename = f"{name_without_ext}_{counter:03d}.7z"
            counter += 1
            
        # Track this filename
        self._downloaded_files.add(final_filename)
        
        return final_filename
    
    def collect_browser_history(self, host_info: HostInfo, username: str) -> bool:
        """
        Collect browser history for a user
        
        Args:
            host_info: Target host information
            username: Target username
            
        Returns:
            True if successful, False otherwise
        """
        session = None
        try:
            # Start RTR session
            session = self.session_manager.start_session(host_info.aid)
            if not session:
                self.logger.error(f"Failed to start RTR session for agent ID: {host_info.aid}")
                return False
                
            # Convert platform string to Platform enum
            try:
                platform = Platform(host_info.platform.lower())
            except ValueError:
                self.logger.error(f"Unsupported platform: {host_info.platform}")
                return False
                
            # Find active browsers
            browsers = self.find_installed_browsers(session, username, platform)
            if not browsers:
                self.logger.info(f"No active browsers found for user {username} on {platform.value}")
                return True  # Not an error if no browsers found
                
            # Build complete artifact list first (discovery phase)
            self.logger.info(f"Building artifact list for {len(browsers)} browsers...")
            artifacts = self._build_artifact_list(session, browsers, username, host_info, platform)
            
            if not artifacts:
                self.logger.info("No browser artifacts found to collect")
                return True
                
            self.logger.info(f"Found {len(artifacts)} total artifacts across all browsers and profiles")
            
            # Collect all artifacts concurrently
            success = self._collect_artifacts_concurrently(session, artifacts, host_info)
                
            return success
            
        except Exception as e:
            self.logger.error(f"Error in collect_browser_history: {e}", exc_info=True)
            return False
        finally:
            # Ensure RTR session is closed
            if session:
                try:
                    self.session_manager.end_session(session)
                except Exception as e:
                    self.logger.error(f"Failed to close RTR session: {e}")
                    
    def _build_artifact_list(self, session: RTRSession, browsers: List[str], 
                           username: str, host_info: HostInfo, platform: Platform) -> List[BrowserArtifact]:
        """
        Build complete list of all browser artifacts to collect (discovery phase)
        
        Args:
            session: Active RTR session
            browsers: List of detected browsers
            username: Target username
            host_info: Host information
            platform: Target platform
            
        Returns:
            List of BrowserArtifact objects ready for concurrent collection
        """
        artifacts = []
        
        for browser in browsers:
            try:
                if platform == Platform.WINDOWS:
                    browser_artifacts = self._discover_windows_browser_artifacts(
                        session, browser, username, host_info)
                elif platform == Platform.MAC:
                    browser_artifacts = self._discover_mac_browser_artifacts(
                        session, browser, username, host_info)
                elif platform == Platform.LINUX:
                    browser_artifacts = self._discover_linux_browser_artifacts(
                        session, browser, username, host_info)
                else:
                    self.logger.warning(f"Unsupported platform for browser discovery: {platform}")
                    continue
                    
                artifacts.extend(browser_artifacts)
                self.logger.info(f"Found {len(browser_artifacts)} artifacts for {browser}")
                
            except Exception as e:
                self.logger.error(f"Error discovering artifacts for {browser}: {e}")
                continue
                
        return artifacts
        
    def _discover_windows_browser_artifacts(self, session: RTRSession, browser: str, 
                                          username: str, host_info: HostInfo) -> List[BrowserArtifact]:
        """Discover all Windows browser artifacts for a specific browser"""
        artifacts = []
        
        try:
            if browser == "Microsoft":
                browser_path = self.config.get_browser_path("edge", Platform.WINDOWS, username)
                profiles = self.get_browser_profiles(session, browser_path, "chromium", "Edge")
                edge_artifacts = [("History", "History"), ("Bookmarks", "Bookmarks")]
                
                for profile in profiles:
                    for artifact_file, artifact_type in edge_artifacts:
                        file_path = f"{browser_path}'{profile}'\\{artifact_file}"
                        file_size = self.file_manager.get_file_size(session, file_path, Platform.WINDOWS)
                        if file_size is not None:
                            local_filename = self._generate_safe_filename(
                                username, "Edge", profile, artifact_type, host_info.hostname)
                            artifacts.append(BrowserArtifact(
                                browser_name="Edge",
                                profile=profile,
                                artifact_type=artifact_type,
                                file_path=file_path,
                                local_filename=local_filename
                            ))
                            
            elif browser == "Google":
                browser_path = self.config.get_browser_path("chrome", Platform.WINDOWS, username)
                profiles = self.get_browser_profiles(session, browser_path, "chromium", "Chrome")
                chrome_artifacts = [("History", "History"), ("Bookmarks", "Bookmarks")]
                
                for profile in profiles:
                    for artifact_file, artifact_type in chrome_artifacts:
                        file_path = f"{browser_path}'{profile}'\\{artifact_file}"
                        file_size = self.file_manager.get_file_size(session, file_path, Platform.WINDOWS)
                        if file_size is not None:
                            local_filename = self._generate_safe_filename(
                                username, "Chrome", profile, artifact_type, host_info.hostname)
                            artifacts.append(BrowserArtifact(
                                browser_name="Chrome",
                                profile=profile,
                                artifact_type=artifact_type,
                                file_path=file_path,
                                local_filename=local_filename
                            ))
                            
            elif browser == "BraveSoftware":
                browser_path = self.config.get_browser_path("brave", Platform.WINDOWS, username)
                profiles = self.get_browser_profiles(session, browser_path, "chromium", "Brave")
                
                for profile in profiles:
                    file_path = f"{browser_path}'{profile}'\\History"
                    file_size = self.file_manager.get_file_size(session, file_path, Platform.WINDOWS)
                    if file_size is not None:
                        local_filename = self._generate_safe_filename(
                            username, "Brave", profile, "History", host_info.hostname)
                        artifacts.append(BrowserArtifact(
                            browser_name="Brave",
                            profile=profile,
                            artifact_type="History",
                            file_path=file_path,
                            local_filename=local_filename
                        ))
                        
            elif browser == "Mozilla":
                browser_path = self.config.get_browser_path("firefox", Platform.WINDOWS, username)
                profiles = self.get_browser_profiles(session, browser_path, "firefox", "Firefox")
                firefox_artifacts = [
                    ("places.sqlite", "Places"),
                    ("cookies.sqlite", "Cookies"),
                    ("logins.json", "Logins"),
                    ("bookmarks.html", "Bookmarks"),
                    ("permissions.sqlite", "Permissions")
                ]
                
                for profile in profiles:
                    for artifact_file, artifact_type in firefox_artifacts:
                        file_path = f"{browser_path}'{profile}'\\{artifact_file}"
                        file_size = self.file_manager.get_file_size(session, file_path, Platform.WINDOWS)
                        if file_size is not None:
                            local_filename = self._generate_safe_filename(
                                username, "Firefox", profile, artifact_type, host_info.hostname)
                            artifacts.append(BrowserArtifact(
                                browser_name="Firefox",
                                profile=profile,
                                artifact_type=artifact_type,
                                file_path=file_path,
                                local_filename=local_filename
                            ))
                            
        except Exception as e:
            self.logger.error(f"Error discovering Windows artifacts for {browser}: {e}")
            
        return artifacts
        
    def _discover_mac_browser_artifacts(self, session: RTRSession, browser: str, 
                                      username: str, host_info: HostInfo) -> List[BrowserArtifact]:
        """Discover all macOS browser artifacts for a specific browser"""
        artifacts = []
        
        try:
            if browser == "Google":
                browser_path = self.config.get_browser_path("chrome", Platform.MAC, username)
                profiles = self.get_browser_profiles(session, browser_path, "chromium", "Chrome")
                chrome_artifacts = [("History", "History"), ("Bookmarks", "Bookmarks")]
                
                for profile in profiles:
                    for artifact_file, artifact_type in chrome_artifacts:
                        file_path = f"{browser_path}'{profile}'/{artifact_file}"
                        file_size = self.file_manager.get_file_size(session, file_path, Platform.MAC)
                        if file_size is not None:
                            local_filename = self._generate_safe_filename(
                                username, "Chrome", profile, artifact_type, host_info.hostname)
                            artifacts.append(BrowserArtifact(
                                browser_name="Chrome",
                                profile=profile,
                                artifact_type=artifact_type,
                                file_path=file_path,
                                local_filename=local_filename
                            ))
                            
            elif browser == "Safari":
                browser_path = self.config.get_browser_path("safari", Platform.MAC, username)
                safari_artifacts = [("History.db", "History"), ("Bookmarks.plist", "Bookmarks")]
                
                for artifact_file, artifact_type in safari_artifacts:
                    file_path = f"{browser_path}/{artifact_file}"
                    file_size = self.file_manager.get_file_size(session, file_path, Platform.MAC)
                    if file_size is not None:
                        local_filename = self._generate_safe_filename(
                            username, "Safari", "Default", artifact_type, host_info.hostname)
                        artifacts.append(BrowserArtifact(
                            browser_name="Safari",
                            profile="Default",
                            artifact_type=artifact_type,
                            file_path=file_path,
                            local_filename=local_filename
                        ))
                        
            # Add other Mac browsers (Firefox, Brave, etc.) as needed
                        
        except Exception as e:
            self.logger.error(f"Error discovering Mac artifacts for {browser}: {e}")
            
        return artifacts
        
    def _discover_linux_browser_artifacts(self, session: RTRSession, browser: str, 
                                        username: str, host_info: HostInfo) -> List[BrowserArtifact]:
        """Discover all Linux browser artifacts for a specific browser"""
        artifacts = []
        
        try:
            if browser == "Google":
                browser_path = self.config.get_browser_path("chrome", Platform.LINUX, username)
                profiles = self.get_browser_profiles(session, browser_path, "chromium", "Chrome")
                chrome_artifacts = [("History", "History"), ("Bookmarks", "Bookmarks")]
                
                for profile in profiles:
                    for artifact_file, artifact_type in chrome_artifacts:
                        file_path = f"{browser_path}/{profile}/{artifact_file}"
                        file_size = self.file_manager.get_file_size(session, file_path, Platform.LINUX)
                        if file_size is not None:
                            local_filename = self._generate_safe_filename(
                                username, "Chrome", profile, artifact_type, host_info.hostname)
                            artifacts.append(BrowserArtifact(
                                browser_name="Chrome",
                                profile=profile,
                                artifact_type=artifact_type,
                                file_path=file_path,
                                local_filename=local_filename
                            ))
                            
            elif browser == "Mozilla":
                browser_path = self.config.get_browser_path("firefox", Platform.LINUX, username)
                profiles = self.get_browser_profiles(session, browser_path, "firefox", "Firefox")
                firefox_artifacts = [("places.sqlite", "Places"), ("cookies.sqlite", "Cookies")]
                
                for profile in profiles:
                    for artifact_file, artifact_type in firefox_artifacts:
                        file_path = f"{browser_path}/{profile}/{artifact_file}"
                        file_size = self.file_manager.get_file_size(session, file_path, Platform.LINUX)
                        if file_size is not None:
                            local_filename = self._generate_safe_filename(
                                username, "Firefox", profile, artifact_type, host_info.hostname)
                            artifacts.append(BrowserArtifact(
                                browser_name="Firefox",
                                profile=profile,
                                artifact_type=artifact_type,
                                file_path=file_path,
                                local_filename=local_filename
                            ))
                            
            # Add other Linux browsers as needed
                            
        except Exception as e:
            self.logger.error(f"Error discovering Linux artifacts for {browser}: {e}")
            
        return artifacts
        
    def _collect_artifacts_concurrently(self, session: RTRSession, artifacts: List[BrowserArtifact], 
                                      host_info: HostInfo) -> bool:
        """
        Collect all browser artifacts concurrently for maximum efficiency
        
        Args:
            session: Active RTR session  
            artifacts: List of artifacts to collect
            host_info: Host information
            
        Returns:
            True if all collections successful, False otherwise
        """
        self.logger.info(f"Starting concurrent collection of {len(artifacts)} artifacts...")
        print(f"[*] Collecting {len(artifacts)} browser artifacts concurrently...")
        
        # Use ThreadPoolExecutor for concurrent downloads
        max_workers = min(len(artifacts), self.config.get_browser_setting("max_concurrent_downloads") or 5)
        success_count = 0
        completed_count = 0
        
        self.logger.info(f"Using {max_workers} concurrent workers for download")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all download tasks
            future_to_artifact = {
                executor.submit(self._download_single_artifact, session, artifact, host_info): artifact 
                for artifact in artifacts
            }
            
            # Process completed downloads with progress reporting
            for future in concurrent.futures.as_completed(future_to_artifact):
                artifact = future_to_artifact[future]
                completed_count += 1
                
                try:
                    success = future.result()
                    if success:
                        success_count += 1
                        self.logger.debug(f"✅ Collected {artifact.browser_name} {artifact.artifact_type} from {artifact.profile}")
                        print(f"[+] ({completed_count}/{len(artifacts)}) {artifact.browser_name} {artifact.artifact_type} from {artifact.profile}")
                    else:
                        self.logger.warning(f"❌ Failed to collect {artifact.browser_name} {artifact.artifact_type} from {artifact.profile}")
                        print(f"[!] ({completed_count}/{len(artifacts)}) Failed: {artifact.browser_name} {artifact.artifact_type} from {artifact.profile}")
                except Exception as e:
                    self.logger.error(f"❌ Exception collecting {artifact.browser_name} {artifact.artifact_type}: {e}")
                    print(f"[!] ({completed_count}/{len(artifacts)}) Error: {artifact.browser_name} {artifact.artifact_type} - {e}")
                    
        self.logger.info(f"Concurrent collection complete: {success_count}/{len(artifacts)} artifacts collected")
        print(f"[+] Browser collection complete: {success_count}/{len(artifacts)} artifacts collected successfully")
        
        # Return True if at least some artifacts were collected successfully
        return success_count > 0
        
    def _download_single_artifact(self, session: RTRSession, artifact: BrowserArtifact, 
                                 host_info: HostInfo) -> bool:
        """
        Download a single browser artifact (thread-safe)
        
        Args:
            session: Active RTR session
            artifact: Artifact to download
            host_info: Host information
            
        Returns:
            True if download successful, False otherwise
        """
        try:
            # Get file size again to ensure file still exists
            platform = Platform(host_info.platform.lower())
            file_size = self.file_manager.get_file_size(session, artifact.file_path, platform)
            
            if file_size is None:
                self.logger.debug(f"File no longer available: {artifact.file_path}")
                return False
                
            # Download the file
            success = self.file_manager.download_file(
                session, host_info.aid, artifact.file_path, artifact.local_filename, file_size
            )
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error downloading {artifact.file_path}: {e}")
            return False
    
    def _collect_windows_browsers(self, session: RTRSession, browsers: List[str], 
                                 username: str, host_info: HostInfo) -> bool:
        """Collect browser history on Windows"""
        all_success = True
        
        for browser in browsers:
            try:
                if browser == "Microsoft":
                    browser_path = self.config.get_browser_path("edge", Platform.WINDOWS, username)
                    profiles = self.get_browser_profiles(session, browser_path, "chromium", "Edge")
                    for profile in profiles:
                        try:
                            # Edge artifacts: History and Bookmarks
                            edge_artifacts = [("History", "History"), ("Bookmarks", "Bookmarks")]
                            
                            for artifact_file, artifact_type in edge_artifacts:
                                file_path = f"{browser_path}'{profile}'\\{artifact_file}"
                                file_size = self.file_manager.get_file_size(session, file_path, Platform.WINDOWS)
                                if file_size is not None:
                                    local_filename = self._generate_safe_filename(
                                        username, "Edge", profile, artifact_type, host_info.hostname)
                                    if not self.file_manager.download_file(session, host_info.aid, file_path, local_filename, file_size):
                                        all_success = False
                                    else:
                                        self.logger.debug(f"Collected Edge {artifact_type} for profile {profile}")
                                else:
                                    self.logger.debug(f"Edge {artifact_type} not found for profile {profile}")
                        except Exception as e:
                            self.logger.error(f"Error processing Edge profile {profile}: {e}")
                            all_success = False
                            
                elif browser == "Google":
                    browser_path = self.config.get_browser_path("chrome", Platform.WINDOWS, username)
                    profiles = self.get_browser_profiles(session, browser_path, "chromium", "Chrome")
                    for profile in profiles:
                        try:
                            # Chrome artifacts: History and Bookmarks
                            chrome_artifacts = [("History", "History"), ("Bookmarks", "Bookmarks")]
                            
                            for artifact_file, artifact_type in chrome_artifacts:
                                file_path = f"{browser_path}'{profile}'\\{artifact_file}"
                                file_size = self.file_manager.get_file_size(session, file_path, Platform.WINDOWS)
                                if file_size is not None:
                                    local_filename = self._generate_safe_filename(
                                        username, "Chrome", profile, artifact_type, host_info.hostname)
                                    if not self.file_manager.download_file(session, host_info.aid, file_path, local_filename, file_size):
                                        all_success = False
                                    else:
                                        self.logger.debug(f"Collected Chrome {artifact_type} for profile {profile}")
                                else:
                                    self.logger.debug(f"Chrome {artifact_type} not found for profile {profile}")
                        except Exception as e:
                            self.logger.error(f"Error processing Chrome profile {profile}: {e}")
                            all_success = False
                            
                elif browser == "BraveSoftware":
                    browser_path = self.config.get_browser_path("brave", Platform.WINDOWS, username)
                    profiles = self.get_browser_profiles(session, browser_path, "chromium", "Brave")
                    for profile in profiles:
                        try:
                            file_path = f"{browser_path}'{profile}'\\History"
                            file_size = self.file_manager.get_file_size(session, file_path, Platform.WINDOWS)
                            if file_size is None:
                                self.logger.debug(f"File not found or empty: {file_path}")
                                continue
                            local_filename = self._generate_safe_filename(
                                username, "Brave", profile, "History", host_info.hostname)
                            if not self.file_manager.download_file(session, host_info.aid, file_path, local_filename, file_size):
                                all_success = False
                        except Exception as e:
                            self.logger.error(f"Error processing Brave profile {profile}: {e}")
                            all_success = False
                            
                elif browser == "Mozilla":
                    browser_path = self.config.get_browser_path("firefox", Platform.WINDOWS, username)
                    profiles = self.get_browser_profiles(session, browser_path, "firefox", "Firefox")
                    for profile in profiles:
                        try:
                            # Firefox artifacts: prioritize most common files
                            # places.sqlite is the most important (contains history and bookmarks)
                            firefox_artifacts = [
                                ("places.sqlite", "Places"),  # History and bookmarks (most important)
                                ("cookies.sqlite", "Cookies"),  # User sessions
                                ("logins.json", "Logins"),  # Saved passwords (if available)
                                ("bookmarks.html", "Bookmarks"),  # Backup bookmarks (may not exist)
                                ("permissions.sqlite", "Permissions")  # Site permissions (may not exist)
                            ]
                            
                            for artifact_file, artifact_type in firefox_artifacts:
                                file_path = f"{browser_path}'{profile}'\\{artifact_file}"
                                file_size = self.file_manager.get_file_size(session, file_path, Platform.WINDOWS)
                                if file_size is not None:
                                    local_filename = self._generate_safe_filename(
                                        username, "Firefox", profile, artifact_type, host_info.hostname)
                                    if not self.file_manager.download_file(session, host_info.aid, file_path, local_filename, file_size):
                                        all_success = False
                                    else:
                                        self.logger.debug(f"Collected Firefox {artifact_type} for profile {profile}")
                                else:
                                    self.logger.debug(f"Firefox {artifact_type} not found for profile {profile}")
                        except Exception as e:
                            self.logger.error(f"Error processing Firefox profile {profile}: {e}")
                            all_success = False
                            
                elif browser == "Opera Software":
                    # Handle both Opera and Opera GX
                    # Try Opera GX first (more specific path)
                    try:
                        browser_path = self.config.get_browser_path("opera_gx", Platform.WINDOWS, username)
                        profiles = self.get_browser_profiles(session, browser_path, "chromium", "Opera GX")
                        if profiles:
                            for profile in profiles:
                                try:
                                    file_path = f"{browser_path}'{profile}'\\History"
                                    file_size = self.file_manager.get_file_size(session, file_path, Platform.WINDOWS)
                                    if file_size is None:
                                        self.logger.debug(f"File not found or empty: {file_path}")
                                        continue
                                    local_filename = self._generate_safe_filename(
                                        username, "OperaGX", profile, "History", host_info.hostname)
                                    if not self.file_manager.download_file(session, host_info.aid, file_path, local_filename, file_size):
                                        all_success = False
                                except Exception as e:
                                    self.logger.error(f"Error processing Opera GX profile {profile}: {e}")
                                    all_success = False
                    except:
                        pass
                    
                    # Try regular Opera
                    try:
                        browser_path = self.config.get_browser_path("opera", Platform.WINDOWS, username)
                        profiles = self.get_browser_profiles(session, browser_path, "chromium", "Opera")
                        if profiles:
                            for profile in profiles:
                                try:
                                    file_path = f"{browser_path}'{profile}'\\History"
                                    file_size = self.file_manager.get_file_size(session, file_path, Platform.WINDOWS)
                                    if file_size is None:
                                        self.logger.debug(f"File not found or empty: {file_path}")
                                        continue
                                    local_filename = self._generate_safe_filename(
                                        username, "Opera", profile, "History", host_info.hostname)
                                    if not self.file_manager.download_file(session, host_info.aid, file_path, local_filename, file_size):
                                        all_success = False
                                except Exception as e:
                                    self.logger.error(f"Error processing Opera profile {profile}: {e}")
                                    all_success = False
                    except:
                        pass
                        
                elif browser == "Vivaldi":
                    browser_path = self.config.get_browser_path("vivaldi", Platform.WINDOWS, username)
                    profiles = self.get_browser_profiles(session, browser_path, "chromium", "Vivaldi")
                    for profile in profiles:
                        try:
                            file_path = f"{browser_path}'{profile}'\\History"
                            file_size = self.file_manager.get_file_size(session, file_path, Platform.WINDOWS)
                            if file_size is None:
                                self.logger.debug(f"File not found or empty: {file_path}")
                                continue
                            local_filename = self._generate_safe_filename(
                                username, "Vivaldi", profile, "History", host_info.hostname)
                            if not self.file_manager.download_file(session, host_info.aid, file_path, local_filename, file_size):
                                all_success = False
                        except Exception as e:
                            self.logger.error(f"Error processing Vivaldi profile {profile}: {e}")
                            all_success = False
                            
                elif browser == "Arc":
                    browser_path = self.config.get_browser_path("arc", Platform.WINDOWS, username)
                    profiles = self.get_browser_profiles(session, browser_path, "chromium", "Arc")
                    for profile in profiles:
                        try:
                            file_path = f"{browser_path}'{profile}'\\History"
                            file_size = self.file_manager.get_file_size(session, file_path, Platform.WINDOWS)
                            if file_size is None:
                                self.logger.debug(f"File not found or empty: {file_path}")
                                continue
                            local_filename = self._generate_safe_filename(
                                username, "Arc", profile, "History", host_info.hostname)
                            if not self.file_manager.download_file(session, host_info.aid, file_path, local_filename, file_size):
                                all_success = False
                        except Exception as e:
                            self.logger.error(f"Error processing Arc profile {profile}: {e}")
                            all_success = False
                            
                elif browser == "Opera Software" or browser == "Opera":
                    # Handle both Opera and Opera GX on Windows
                    # Try Opera GX first (more specific path)
                    try:
                        browser_path = self.config.get_browser_path("opera_gx", Platform.WINDOWS, username)
                        profiles = self.get_browser_profiles(session, browser_path, "chromium", "Opera GX")
                        for profile in profiles:
                            try:
                                file_path = f"{browser_path}'{profile}'\\History"
                                file_size = self.file_manager.get_file_size(session, file_path, Platform.WINDOWS)
                                if file_size is not None:
                                    local_filename = self._generate_safe_filename(
                                        username, "OperaGX", profile, "History", host_info.hostname)
                                    if not self.file_manager.download_file(session, host_info.aid, file_path, local_filename, file_size):
                                        all_success = False
                                else:
                                    self.logger.debug(f"Opera GX history not found for profile {profile}")
                            except Exception as e:
                                self.logger.error(f"Error processing Opera GX profile {profile}: {e}")
                                all_success = False
                    except Exception:
                        pass  # Opera GX not found, try regular Opera
                        
                    # Try regular Opera
                    try:
                        browser_path = self.config.get_browser_path("opera", Platform.WINDOWS, username)
                        profiles = self.get_browser_profiles(session, browser_path, "chromium", "Opera")
                        for profile in profiles:
                            try:
                                file_path = f"{browser_path}'{profile}'\\History"
                                file_size = self.file_manager.get_file_size(session, file_path, Platform.WINDOWS)
                                if file_size is not None:
                                    local_filename = self._generate_safe_filename(
                                        username, "Opera", profile, "History", host_info.hostname)
                                    if not self.file_manager.download_file(session, host_info.aid, file_path, local_filename, file_size):
                                        all_success = False
                                else:
                                    self.logger.debug(f"Opera history not found for profile {profile}")
                            except Exception as e:
                                self.logger.error(f"Error processing Opera profile {profile}: {e}")
                                all_success = False
                    except Exception:
                        pass  # Opera not found
                        
                elif browser == "Tor Browser":
                    browser_path = self.config.get_browser_path("tor", Platform.WINDOWS, username)
                    # Tor Browser uses Firefox engine but has a single profile
                    try:
                        file_path = f"{browser_path}places.sqlite"
                        file_size = self.file_manager.get_file_size(session, file_path, Platform.WINDOWS)
                        if file_size is not None:
                            local_filename = self._generate_safe_filename(
                                username, "TorBrowser", None, "Places", host_info.hostname)
                            if not self.file_manager.download_file(session, host_info.aid, file_path, local_filename, file_size):
                                all_success = False
                        else:
                            self.logger.debug(f"Tor Browser history not found at: {file_path}")
                    except Exception as e:
                        self.logger.error(f"Error processing Tor Browser: {e}")
                        all_success = False
                        
                else:
                    self.logger.warning(f"Unsupported browser type: {browser}")
                    
            except Exception as e:
                self.logger.error(f"Error processing {browser} browser: {e}")
                all_success = False
                
        return all_success
        
    def _collect_mac_browsers(self, session: RTRSession, browsers: List[str], 
                             username: str, host_info: HostInfo) -> bool:
        """Collect browser history on macOS"""
        all_success = True
        
        for browser in browsers:
            try:
                if browser == "Google":
                    browser_path = self.config.get_browser_path("chrome", Platform.MAC, username)
                    profiles = self.get_browser_profiles(session, browser_path, "chromium", "Chrome")
                    for profile in profiles:
                        try:
                            # Chrome artifacts: History and Bookmarks
                            chrome_artifacts = [("History", "History"), ("Bookmarks", "Bookmarks")]
                            
                            for artifact_file, artifact_type in chrome_artifacts:
                                file_path = f"{browser_path}'{profile}'/{artifact_file}"
                                file_size = self.file_manager.get_file_size(session, file_path, Platform.MAC)
                                if file_size is not None:
                                    local_filename = self._generate_safe_filename(
                                        username, "Chrome", profile, artifact_type, host_info.hostname)
                                    if not self.file_manager.download_file(session, host_info.aid, file_path, local_filename, file_size):
                                        all_success = False
                                    else:
                                        self.logger.debug(f"Collected Chrome {artifact_type} for profile {profile}")
                                else:
                                    self.logger.debug(f"Chrome {artifact_type} not found for profile {profile}")
                        except Exception as e:
                            self.logger.error(f"Error processing Chrome profile {profile}: {e}")
                            all_success = False
                            
                elif browser == "Microsoft":
                    browser_path = self.config.get_browser_path("edge", Platform.MAC, username)
                    profiles = self.get_browser_profiles(session, browser_path, "chromium", "Edge")
                    for profile in profiles:
                        try:
                            # Edge artifacts: History and Bookmarks
                            edge_artifacts = [("History", "History"), ("Bookmarks", "Bookmarks")]
                            
                            for artifact_file, artifact_type in edge_artifacts:
                                file_path = f"{browser_path}'{profile}'/{artifact_file}"
                                file_size = self.file_manager.get_file_size(session, file_path, Platform.MAC)
                                if file_size is not None:
                                    local_filename = self._generate_safe_filename(
                                        username, "Edge", profile, artifact_type, host_info.hostname)
                                    if not self.file_manager.download_file(session, host_info.aid, file_path, local_filename, file_size):
                                        all_success = False
                                    else:
                                        self.logger.debug(f"Collected Edge {artifact_type} for profile {profile}")
                                else:
                                    self.logger.debug(f"Edge {artifact_type} not found for profile {profile}")
                        except Exception as e:
                            self.logger.error(f"Error processing Edge profile {profile}: {e}")
                            all_success = False
                            
                elif browser == "BraveSoftware":
                    browser_path = self.config.get_browser_path("brave", Platform.MAC, username)
                    profiles = self.get_browser_profiles(session, browser_path, "chromium", "Brave")
                    for profile in profiles:
                        try:
                            file_path = f"{browser_path}'{profile}'/History"
                            file_size = self.file_manager.get_file_size(session, file_path, Platform.MAC)
                            if file_size is None:
                                self.logger.debug(f"File not found or empty: {file_path}")
                                continue
                            local_filename = self._generate_safe_filename(
                                username, "Brave", profile, "History", host_info.hostname)
                            if not self.file_manager.download_file(session, host_info.aid, file_path, local_filename, file_size):
                                all_success = False
                        except Exception as e:
                            self.logger.error(f"Error processing Brave profile {profile}: {e}")
                            all_success = False
                            
                elif browser == "Mozilla":
                    browser_path = self.config.get_browser_path("firefox", Platform.MAC, username)
                    profiles = self.get_browser_profiles(session, browser_path, "firefox", "Firefox")
                    for profile in profiles:
                        try:
                            # Firefox artifacts: places.sqlite, bookmarks.html, logins.json, permissions.sqlite, cookies.sqlite
                            firefox_artifacts = [
                                ("places.sqlite", "Places"),
                                ("bookmarks.html", "Bookmarks"),
                                ("logins.json", "Logins"),
                                ("permissions.sqlite", "Permissions"),
                                ("cookies.sqlite", "Cookies")
                            ]
                            
                            for artifact_file, artifact_type in firefox_artifacts:
                                file_path = f"{browser_path}'{profile}'/{artifact_file}"
                                file_size = self.file_manager.get_file_size(session, file_path, Platform.MAC)
                                if file_size is not None:
                                    local_filename = self._generate_safe_filename(
                                        username, "Firefox", profile, artifact_type, host_info.hostname)
                                    if not self.file_manager.download_file(session, host_info.aid, file_path, local_filename, file_size):
                                        all_success = False
                                    else:
                                        self.logger.debug(f"Collected Firefox {artifact_type} for profile {profile}")
                                else:
                                    self.logger.debug(f"Firefox {artifact_type} not found for profile {profile}")
                        except Exception as e:
                            self.logger.error(f"Error processing Firefox profile {profile}: {e}")
                            all_success = False
                            
                elif browser == "Safari":
                    browser_path = self.config.get_browser_path("safari", Platform.MAC, username)
                    # Enhanced Safari collection: History.db, Downloads.plist, Bookmarks.plist, TopSites.plist
                    safari_artifacts = [
                        ("History.db", "History"),
                        ("Downloads.plist", "Downloads"),
                        ("Bookmarks.plist", "Bookmarks"),
                        ("TopSites.plist", "TopSites")
                    ]
                    
                    safari_collected = 0
                    safari_failed = 0
                    
                    for artifact_file, artifact_type in safari_artifacts:
                        try:
                            file_path = f"{browser_path}{artifact_file}"
                            file_size = self.file_manager.get_file_size(session, file_path, Platform.MAC)
                            if file_size is not None:
                                local_filename = self._generate_safe_filename(
                                    username, "Safari", None, artifact_type, host_info.hostname)
                                if self.file_manager.download_file(session, host_info.aid, file_path, local_filename, file_size):
                                    safari_collected += 1
                                    self.logger.info(f"Successfully collected Safari {artifact_type} ({file_size:,} bytes)")
                                else:
                                    safari_failed += 1
                                    self.logger.error(f"Failed to download Safari {artifact_type}")
                                    all_success = False
                            else:
                                self.logger.debug(f"Safari {artifact_type} not found at: {file_path}")
                        except Exception as e:
                            safari_failed += 1
                            self.logger.error(f"Error processing Safari {artifact_type}: {e}")
                            all_success = False
                    
                    self.logger.info(f"Safari collection summary: {safari_collected} artifacts collected, {safari_failed} failed")
                        
                elif browser == "Opera Software":
                    # Handle both Opera and Opera GX on macOS
                    # Try Opera GX first
                    try:
                        browser_path = self.config.get_browser_path("opera_gx", Platform.MAC, username)
                        profiles = self.get_browser_profiles(session, browser_path, "chromium", "Opera GX")
                        if profiles:
                            for profile in profiles:
                                try:
                                    file_path = f"{browser_path}'{profile}'/History"
                                    file_size = self.file_manager.get_file_size(session, file_path, Platform.MAC)
                                    if file_size is None:
                                        self.logger.debug(f"File not found or empty: {file_path}")
                                        continue
                                    local_filename = self._generate_safe_filename(
                                        username, "OperaGX", profile, "History", host_info.hostname)
                                    if not self.file_manager.download_file(session, host_info.aid, file_path, local_filename, file_size):
                                        all_success = False
                                except Exception as e:
                                    self.logger.error(f"Error processing Opera GX profile {profile}: {e}")
                                    all_success = False
                    except:
                        pass
                    
                    # Try regular Opera
                    try:
                        browser_path = self.config.get_browser_path("opera", Platform.MAC, username)
                        profiles = self.get_browser_profiles(session, browser_path, "chromium", "Opera")
                        if profiles:
                            for profile in profiles:
                                try:
                                    file_path = f"{browser_path}'{profile}'/History"
                                    file_size = self.file_manager.get_file_size(session, file_path, Platform.MAC)
                                    if file_size is None:
                                        self.logger.debug(f"File not found or empty: {file_path}")
                                        continue
                                    local_filename = self._generate_safe_filename(
                                        username, "Opera", profile, "History", host_info.hostname)
                                    if not self.file_manager.download_file(session, host_info.aid, file_path, local_filename, file_size):
                                        all_success = False
                                except Exception as e:
                                    self.logger.error(f"Error processing Opera profile {profile}: {e}")
                                    all_success = False
                    except:
                        pass
                        
                elif browser == "Vivaldi":
                    browser_path = self.config.get_browser_path("vivaldi", Platform.MAC, username)
                    profiles = self.get_browser_profiles(session, browser_path, "chromium", "Vivaldi")
                    for profile in profiles:
                        try:
                            file_path = f"{browser_path}'{profile}'/History"
                            file_size = self.file_manager.get_file_size(session, file_path, Platform.MAC)
                            if file_size is None:
                                self.logger.debug(f"File not found or empty: {file_path}")
                                continue
                            local_filename = self._generate_safe_filename(
                                username, "Vivaldi", profile, "History", host_info.hostname)
                            if not self.file_manager.download_file(session, host_info.aid, file_path, local_filename, file_size):
                                all_success = False
                        except Exception as e:
                            self.logger.error(f"Error processing Vivaldi profile {profile}: {e}")
                            all_success = False
                            
                elif browser == "Arc":
                    browser_path = self.config.get_browser_path("arc", Platform.MAC, username)
                    profiles = self.get_browser_profiles(session, browser_path, "chromium", "Arc")
                    for profile in profiles:
                        try:
                            file_path = f"{browser_path}'{profile}'/History"
                            file_size = self.file_manager.get_file_size(session, file_path, Platform.MAC)
                            if file_size is None:
                                self.logger.debug(f"File not found or empty: {file_path}")
                                continue
                            local_filename = self._generate_safe_filename(
                                username, "Arc", profile, "History", host_info.hostname)
                            if not self.file_manager.download_file(session, host_info.aid, file_path, local_filename, file_size):
                                all_success = False
                        except Exception as e:
                            self.logger.error(f"Error processing Arc profile {profile}: {e}")
                            all_success = False
                            
                elif browser == "Tor Browser":
                    browser_path = self.config.get_browser_path("tor", Platform.MAC, username)
                    # Tor Browser uses Firefox engine but has a single profile
                    try:
                        file_path = f"{browser_path}places.sqlite"
                        file_size = self.file_manager.get_file_size(session, file_path, Platform.MAC)
                        if file_size is not None:
                            local_filename = self._generate_safe_filename(
                                username, "TorBrowser", None, "Places", host_info.hostname)
                            if not self.file_manager.download_file(session, host_info.aid, file_path, local_filename, file_size):
                                all_success = False
                        else:
                            self.logger.debug(f"Tor Browser history not found at: {file_path}")
                    except Exception as e:
                        self.logger.error(f"Error processing Tor Browser: {e}")
                        all_success = False
                        
                else:
                    self.logger.warning(f"Unsupported browser type: {browser}")
                    
            except Exception as e:
                self.logger.error(f"Error processing {browser} browser: {e}")
                all_success = False
                
        return all_success
        
    def _collect_linux_browsers(self, session: RTRSession, browsers: List[str], 
                               username: str, host_info: HostInfo) -> bool:
        """Collect browser history on Linux"""
        all_success = True
        
        for browser in browsers:
            try:
                if browser == "Google":
                    browser_path = self.config.get_browser_path("chrome", Platform.LINUX, username)
                    profiles = self.get_browser_profiles(session, browser_path, "chromium", "Chrome")
                    for profile in profiles:
                        try:
                            # Chrome artifacts: History and Bookmarks
                            chrome_artifacts = [("History", "History"), ("Bookmarks", "Bookmarks")]
                            
                            for artifact_file, artifact_type in chrome_artifacts:
                                file_path = f"{browser_path}'{profile}'/{artifact_file}"
                                file_size = self.file_manager.get_file_size(session, file_path, Platform.LINUX)
                                if file_size is not None:
                                    local_filename = self._generate_safe_filename(
                                        username, "Chrome", profile, artifact_type, host_info.hostname)
                                    if not self.file_manager.download_file(session, host_info.aid, file_path, local_filename, file_size):
                                        all_success = False
                                    else:
                                        self.logger.debug(f"Collected Chrome {artifact_type} for profile {profile}")
                                else:
                                    self.logger.debug(f"Chrome {artifact_type} not found for profile {profile}")
                        except Exception as e:
                            self.logger.error(f"Error processing Chrome profile {profile}: {e}")
                            all_success = False
                            
                elif browser == "BraveSoftware":
                    browser_path = self.config.get_browser_path("brave", Platform.LINUX, username)
                    profiles = self.get_browser_profiles(session, browser_path, "chromium", "Brave")
                    for profile in profiles:
                        try:
                            file_path = f"{browser_path}'{profile}'/History"
                            file_size = self.file_manager.get_file_size(session, file_path, Platform.LINUX)
                            if file_size is None:
                                self.logger.debug(f"File not found or empty: {file_path}")
                                continue
                            local_filename = self._generate_safe_filename(
                                username, "Brave", profile, "History", host_info.hostname)
                            if not self.file_manager.download_file(session, host_info.aid, file_path, local_filename, file_size):
                                all_success = False
                        except Exception as e:
                            self.logger.error(f"Error processing Brave profile {profile}: {e}")
                            all_success = False
                            
                elif browser == "Mozilla":
                    browser_path = self.config.get_browser_path("firefox", Platform.LINUX, username)
                    profiles = self.get_browser_profiles(session, browser_path, "firefox", "Firefox")
                    for profile in profiles:
                        try:
                            # Firefox artifacts: places.sqlite, bookmarks.html, logins.json, permissions.sqlite, cookies.sqlite
                            firefox_artifacts = [
                                ("places.sqlite", "Places"),
                                ("bookmarks.html", "Bookmarks"),
                                ("logins.json", "Logins"),
                                ("permissions.sqlite", "Permissions"),
                                ("cookies.sqlite", "Cookies")
                            ]
                            
                            for artifact_file, artifact_type in firefox_artifacts:
                                file_path = f"{browser_path}'{profile}'/{artifact_file}"
                                file_size = self.file_manager.get_file_size(session, file_path, Platform.LINUX)
                                if file_size is not None:
                                    local_filename = self._generate_safe_filename(
                                        username, "Firefox", profile, artifact_type, host_info.hostname)
                                    if not self.file_manager.download_file(session, host_info.aid, file_path, local_filename, file_size):
                                        all_success = False
                                    else:
                                        self.logger.debug(f"Collected Firefox {artifact_type} for profile {profile}")
                                else:
                                    self.logger.debug(f"Firefox {artifact_type} not found for profile {profile}")
                        except Exception as e:
                            self.logger.error(f"Error processing Firefox profile {profile}: {e}")
                            all_success = False
                            
                elif browser == "Microsoft":
                    browser_path = self.config.get_browser_path("edge", Platform.LINUX, username)
                    profiles = self.get_browser_profiles(session, browser_path, "chromium", "Edge")
                    for profile in profiles:
                        try:
                            # Edge artifacts: History and Bookmarks
                            edge_artifacts = [("History", "History"), ("Bookmarks", "Bookmarks")]
                            
                            for artifact_file, artifact_type in edge_artifacts:
                                file_path = f"{browser_path}'{profile}'/{artifact_file}"
                                file_size = self.file_manager.get_file_size(session, file_path, Platform.LINUX)
                                if file_size is not None:
                                    local_filename = self._generate_safe_filename(
                                        username, "Edge", profile, artifact_type, host_info.hostname)
                                    if not self.file_manager.download_file(session, host_info.aid, file_path, local_filename, file_size):
                                        all_success = False
                                    else:
                                        self.logger.debug(f"Collected Edge {artifact_type} for profile {profile}")
                                else:
                                    self.logger.debug(f"Edge {artifact_type} not found for profile {profile}")
                        except Exception as e:
                            self.logger.error(f"Error processing Edge profile {profile}: {e}")
                            all_success = False
                            
                elif browser == "Opera Software":
                    # Handle both Opera and Opera GX on Linux
                    # Try Opera GX first
                    try:
                        browser_path = self.config.get_browser_path("opera_gx", Platform.LINUX, username)
                        profiles = self.get_browser_profiles(session, browser_path, "chromium", "Opera GX")
                        if profiles:
                            for profile in profiles:
                                try:
                                    file_path = f"{browser_path}'{profile}'/History"
                                    file_size = self.file_manager.get_file_size(session, file_path, Platform.LINUX)
                                    if file_size is None:
                                        self.logger.debug(f"File not found or empty: {file_path}")
                                        continue
                                    local_filename = self._generate_safe_filename(
                                        username, "OperaGX", profile, "History", host_info.hostname)
                                    if not self.file_manager.download_file(session, host_info.aid, file_path, local_filename, file_size):
                                        all_success = False
                                except Exception as e:
                                    self.logger.error(f"Error processing Opera GX profile {profile}: {e}")
                                    all_success = False
                    except:
                        pass
                    
                    # Try regular Opera
                    try:
                        browser_path = self.config.get_browser_path("opera", Platform.LINUX, username)
                        profiles = self.get_browser_profiles(session, browser_path, "chromium", "Opera")
                        if profiles:
                            for profile in profiles:
                                try:
                                    file_path = f"{browser_path}'{profile}'/History"
                                    file_size = self.file_manager.get_file_size(session, file_path, Platform.LINUX)
                                    if file_size is None:
                                        self.logger.debug(f"File not found or empty: {file_path}")
                                        continue
                                    local_filename = self._generate_safe_filename(
                                        username, "Opera", profile, "History", host_info.hostname)
                                    if not self.file_manager.download_file(session, host_info.aid, file_path, local_filename, file_size):
                                        all_success = False
                                except Exception as e:
                                    self.logger.error(f"Error processing Opera profile {profile}: {e}")
                                    all_success = False
                    except:
                        pass
                        
                elif browser == "Vivaldi":
                    browser_path = self.config.get_browser_path("vivaldi", Platform.LINUX, username)
                    profiles = self.get_browser_profiles(session, browser_path, "chromium", "Vivaldi")
                    for profile in profiles:
                        try:
                            file_path = f"{browser_path}'{profile}'/History"
                            file_size = self.file_manager.get_file_size(session, file_path, Platform.LINUX)
                            if file_size is None:
                                self.logger.debug(f"File not found or empty: {file_path}")
                                continue
                            local_filename = self._generate_safe_filename(
                                username, "Vivaldi", profile, "History", host_info.hostname)
                            if not self.file_manager.download_file(session, host_info.aid, file_path, local_filename, file_size):
                                all_success = False
                        except Exception as e:
                            self.logger.error(f"Error processing Vivaldi profile {profile}: {e}")
                            all_success = False
                            
                elif browser == "Tor Browser":
                    browser_path = self.config.get_browser_path("tor", Platform.LINUX, username)
                    # Tor Browser uses Firefox engine but has a single profile
                    try:
                        file_path = f"{browser_path}places.sqlite"
                        file_size = self.file_manager.get_file_size(session, file_path, Platform.LINUX)
                        if file_size is not None:
                            local_filename = self._generate_safe_filename(
                                username, "TorBrowser", None, "Places", host_info.hostname)
                            if not self.file_manager.download_file(session, host_info.aid, file_path, local_filename, file_size):
                                all_success = False
                        else:
                            self.logger.debug(f"Tor Browser history not found at: {file_path}")
                    except Exception as e:
                        self.logger.error(f"Error processing Tor Browser: {e}")
                        all_success = False
                        
                else:
                    self.logger.warning(f"Unsupported browser type: {browser}")
                    
            except Exception as e:
                self.logger.error(f"Error processing {browser} browser: {e}")
                all_success = False
                
        return all_success
        
    def find_installed_browsers(self, session: RTRSession, username: str, 
                              platform: Platform) -> List[str]:
        """
        Find installed browsers on system
        
        Args:
            session: Active RTR session
            username: Target username
            platform: Target platform
            
        Returns:
            List of installed browser names
        """
        try:
            # Validate inputs
            if not session:
                self.logger.warning("Invalid RTR session provided")
                return []
                
            # Get browser root paths for platform
            browser_roots = self.config.get_browser_root_paths(platform)
            if not browser_roots:
                self.logger.error(f"No browser paths configured for platform: {platform.value}")
                return []
                
            active_browsers = []
            
            # Search each configured path
            for path_key, path_template in browser_roots.items():
                try:
                    resolved_path = path_template.format(user=username)
                    
                    # Get browser info from directory
                    browsers = self._get_browser_info(session, resolved_path)
                    active_browsers.extend(browsers)
                    
                except KeyError as e:
                    self.logger.warning(f"Missing browser path key: {e}")
                    continue
                except Exception as e:
                    self.logger.warning(f"Error resolving path: {e}")
                    continue
                    
            # Return unique list
            unique_browsers = list(set(active_browsers))
            if unique_browsers:
                self.logger.info(f"Found {len(unique_browsers)} installed browser(s): {', '.join(unique_browsers)}")
            else:
                self.logger.info("No browsers found")
            return unique_browsers
            
        except Exception as e:
            self.logger.error(f"Unexpected error in find_installed_browsers: {e}", exc_info=True)
            return []
        
    def get_browser_profiles(self, session: RTRSession, browser_path: str, 
                           browser_type: str, browser_name: str = None) -> List[str]:
        """
        Get browser profiles
        
        Args:
            session: Active RTR session
            browser_path: Browser installation path
            browser_type: Type of browser (chromium/firefox)
            
        Returns:
            List of profile names
        """
        try:
            if not session:
                self.logger.warning("Invalid RTR session provided")
                return []
                
            # Execute ls command to list directory
            result = self.session_manager.execute_command(
                session=session,
                base_command="runscript",
                command=f"ls {browser_path}",
                is_admin=False,
                suppress_stderr_warnings=True  # Discovery command - missing directories are expected
            )
            
            if not result:
                self.logger.info(f"No results from directory listing: {browser_path}")
                return []
                
            stdout = result.stdout
            if not stdout:
                self.logger.info(f"Empty stdout in command response for path: {browser_path}")
                return []
                
            # Parse profiles based on browser type
            profiles = []
            
            if browser_type.lower() == "chromium":
                # Enhanced pattern for Chromium-based browsers
                # Includes: Default, Default Profile, Guest Profile, Profile 1-999, Person 1-999, etc.
                patterns = [
                    r"\bDefault\b",
                    r"\bDefault\s+Profile\b",
                    r"\bGuest\s+Profile\b", 
                    r"\bProfile\s+\d+\b",
                    r"\bPerson\s+\d+\b"  # Some Chrome versions use Person 1, Person 2, etc.
                ]
                
                profiles = []
                for pattern in patterns:
                    found = re.findall(pattern, stdout, re.IGNORECASE)
                    profiles.extend([p.strip() for p in found])
                
                # Fallback: Look for directory names that are likely profiles
                # This catches cases where the exact patterns don't match
                if not profiles:
                    # Look for directory-like entries that could be profiles
                    lines = stdout.split('\n')
                    for line in lines:
                        line = line.strip()
                        # Skip empty lines, files, and known non-profile directories
                        if (line and 
                            not line.startswith('.') and 
                            not line.endswith('.db') and
                            not line.endswith('.log') and
                            not line.endswith('.txt') and
                            not line.endswith('.json') and
                            # Skip known browser system directories
                            line not in ['Cache', 'Temp', 'Logs', 'User Data', 'NativeMessagingHosts', 
                                        'Crash Reports', 'Application Cache', 'Local Storage',
                                        'Session Storage', 'IndexedDB', 'Service Worker',
                                        'blob_storage', 'File System', 'databases'] and
                            'Cache' not in line and
                            'Temp' not in line and
                            'Log' not in line):
                            profiles.append(line)
                
                # Remove duplicates while preserving order
                profiles = list(dict.fromkeys(profiles))
                
            elif browser_type.lower() == "firefox":
                # Enhanced pattern for Firefox profiles
                # Firefox profiles follow pattern: 8-char-random.profile-name
                patterns = [
                    # Standard Firefox profile pattern
                    r"([a-zA-Z0-9]{8}\.[a-zA-Z0-9\-_.]+)",
                    # Alternative pattern for profile directories
                    r"([a-zA-Z0-9]{8}\.[^\s<>:/\\|?*\"]+)"
                ]
                
                profiles = []
                for pattern in patterns:
                    found = re.findall(pattern, stdout)
                    profiles.extend([p.strip() for p in found if p.strip()])
                
                # Remove duplicates and filter out invalid entries
                profiles = list(dict.fromkeys([p for p in profiles if '.' in p and len(p) > 9]))
                
            elif browser_type.lower() == "safari":
                # Safari doesn't use profiles in the traditional sense
                profiles = ["Main"]
                
            elif browser_type.lower() == "tor":
                # Tor Browser typically has a single default profile
                profiles = ["default"]
                
            else:
                self.logger.warning(f"Unknown browser type: {browser_type}")
                profiles = []
                
            display_name = browser_name or browser_type
            if profiles:
                self.logger.info(f"Found {len(profiles)} {display_name} profile(s): {', '.join(profiles)}")
            else:
                self.logger.debug(f"No {display_name} profiles found in {browser_path}")
            return profiles
            
        except Exception as e:
            self.logger.error(f"Error getting browser profiles: {e}", exc_info=True)
            return []
        
    def _get_browser_info(self, session: RTRSession, file_path: str) -> List[str]:
        """
        Get browser information from directory listing
        
        Args:
            session: Active RTR session
            file_path: Directory path to list
            
        Returns:
            List of browser-related items found
        """
        try:
            if not session:
                self.logger.warning("Invalid RTR session provided")
                return []
                
            # Execute ls command
            result = self.session_manager.execute_command(
                session=session,
                base_command="runscript",
                command=f"ls {file_path}",
                is_admin=False,
                suppress_stderr_warnings=True  # Discovery command - missing directories are expected
            )
            
            if not result:
                self.logger.info(f"No results from directory listing: {file_path}")
                return []
                
            stdout = result.stdout
            if not stdout:
                self.logger.info(f"Empty stdout in command response for path: {file_path}")
                return []
                
            # Pattern to find browser-related directories
            pattern = r"\b(?:BraveSoftware|Google|Microsoft|Opera|Opera Software|Chromium|Mozilla|Safari|Vivaldi|Arc|Tor Browser)\b"
            
            try:
                browsers = re.findall(pattern, stdout)
                return browsers
            except re.error as e:
                self.logger.error(f"Regex error when finding browsers: {e}")
                return []
                
        except Exception as e:
            self.logger.error(f"Error executing RTR command: {e}")
            return []

class ForensicCollector:
    """Handles forensic collection operations (KAPE, etc.)"""
    
    def __init__(self, file_manager: FileManager, session_manager: SessionManager,
                 cloud_storage: CloudStorageManager, config: IConfigProvider, 
                 logger: Optional[ILogger] = None):
        """
        Initialize forensic collector
        
        Args:
            file_manager: File manager instance
            session_manager: Session manager instance
            cloud_storage: Cloud storage manager instance
            config: Configuration provider
            logger: Logger instance (uses DefaultLogger if not provided)
        """
        self.file_manager = file_manager
        self.session_manager = session_manager
        self.cloud_storage = cloud_storage
        self.config = config
        self.logger = logger or DefaultLogger("ForensicCollector")
        
        # Initialize workspace cleanup manager
        self.cleanup_manager = WorkspaceCleanupManager(session_manager, config, self.logger)
        
        # Initialize pre-execution cleanup manager
        self.pre_cleanup_manager = PreExecutionCleanupManager(session_manager, config, self.logger)
        
    def run_kape_collection(self, host_info: HostInfo, target: str) -> Optional[str]:
        """
        Run KAPE forensic collection
        
        Args:
            host_info: Target host information
            target: KAPE target specification
            
        Returns:
            Collection file name or None
            
        Note:
            ServerTriage target is UNTESTED on desktop Windows systems.
            This target requires Windows Server OS for proper functionality.
            Testing has only been performed on Windows 10/11 desktop systems.
        """
        session = None
        try:
            # Prepare KAPE package
            self.logger.info("Preparing KAPE package")
            kape_zip = self.prepare_kape_package(target)
            
            # Upload files to cloud
            self.logger.info("Uploading KAPE files to cloud")
            
            # Get current cloud files
            cloud_files = self.file_manager.list_cloud_files(host_info.cid)
            
            # Delete existing kape.zip if present
            if 'kape.zip' in cloud_files:
                self.file_manager.delete_from_cloud(host_info.cid, 'kape.zip')
                
            # Upload kape.zip
            if not self.file_manager.upload_to_cloud(
                host_info.cid, 
                str(kape_zip), 
                'Kape Triage Tool Upload', 
                '4n6 Triage Tool'
            ):
                self.logger.error("Failed to upload kape.zip")
                return None
                
            # Delete existing deploy_kape.ps1 if present
            if 'deploy_kape.ps1' in cloud_files:
                self.file_manager.delete_from_cloud(host_info.cid, 'deploy_kape.ps1')
                
            # Upload deploy script
            # Get deploy script from package resources
            try:
                # Try to use importlib.resources (Python 3.9+)
                try:
                    from importlib import resources
                    with resources.path('fnerd_falconpy.resources', 'deploy_kape.ps1') as p:
                        deploy_script = Path(p)
                except:
                    # Fallback to pkg_resources
                    import pkg_resources
                    deploy_script = Path(pkg_resources.resource_filename('fnerd_falconpy', 'resources/deploy_kape.ps1'))
            except:
                # Fallback for development
                package_root = Path(__file__).parent.parent
                deploy_script = package_root / "resources" / "deploy_kape.ps1"
            
            if not deploy_script.exists():
                self.logger.error("deploy_kape.ps1 not found")
                return None
                
            if not self.file_manager.upload_to_cloud(
                host_info.cid,
                str(deploy_script),
                'Kape Triage Execution Script',
                'Kape Launcher Script'
            ):
                self.logger.error("Failed to upload deploy_kape.ps1")
                return None
                
            # Start RTR session
            session = self.session_manager.start_session(host_info.aid)
            if not session:
                self.logger.error("Failed to start RTR session")
                return None
            
            # CRITICAL: Ensure clean environment before starting collection
            # Check for existing KAPE processes and workspace directories
            self.logger.info("Performing pre-execution cleanup check...")
            print("[*] Checking for existing KAPE processes and workspace...")
            
            if not self.pre_cleanup_manager.ensure_clean_environment(session, host_info):
                self.logger.error("Pre-execution cleanup failed - aborting collection")
                print("[!] Pre-execution cleanup failed - aborting collection for safety")
                return None
                
            # Execute KAPE deployment
            self.logger.info("Deploying KAPE on target host")
            
            # CRITICAL: Change to deployment directory FIRST (directory created by pre-execution cleanup)
            # NEVER write files to root directory
            workspace_path = self.config.get_kape_setting("base_path")
            self.session_manager.execute_command(
                session, "cd", f"cd {workspace_path}", is_admin=True
            )
            
            # Create temp subdirectory for KAPE output (required by KAPE command)
            temp_result = self.session_manager.execute_command(
                session, "mkdir", "mkdir temp", is_admin=True
            )
            
            # Verify temp directory was created
            if temp_result:
                self.logger.info(f"Temp directory creation result: {temp_result.return_code}")
                if temp_result.stderr:
                    self.logger.warning(f"Temp directory creation stderr: {temp_result.stderr}")
                    
                # Verify it exists
                workspace_path = self.config.get_kape_setting("base_path")
                verify_result = self.session_manager.execute_command(
                    session, "runscript", 
                    f"runscript -Raw=```Test-Path '{workspace_path}\\temp'```", 
                    is_admin=True
                )
                if verify_result:
                    self.logger.info(f"Temp directory exists check: {verify_result.stdout.strip()}")
            else:
                self.logger.error("Temp directory creation returned None")
            
            # Put files to configured workspace
            self.session_manager.execute_command(
                session, "put", "put kape.zip", is_admin=True
            )
            self.session_manager.execute_command(
                session, "put", "put deploy_kape.ps1", is_admin=True
            )
            
            # Execute KAPE deployment script from workspace
            self.logger.info("Executing KAPE deployment script...")
            deploy_result = self.session_manager.execute_command(
                session, 
                "runscript",
                f"runscript -Raw=```powershell.exe -noprofile -executionpolicy bypass -file {workspace_path}\\deploy_kape.ps1```",
                is_admin=True
            )
            
            # Log deployment script output for debugging
            if deploy_result:
                if deploy_result.stdout:
                    self.logger.info(f"Deploy script output: {deploy_result.stdout}")
                if deploy_result.stderr:
                    self.logger.warning(f"Deploy script errors: {deploy_result.stderr}")
                if deploy_result.return_code != 0:
                    self.logger.error(f"Deploy script failed with return code: {deploy_result.return_code}")
            else:
                self.logger.error("Deploy script execution returned None")
            
            # Wait a moment for KAPE to start
            time.sleep(3)
            
            # Verify KAPE is running
            ps_result = self.session_manager.execute_command(
                session, "ps", "ps", is_admin=True
            )
            
            if not ps_result or 'kape.exe' not in ps_result.stdout:
                self.logger.error("KAPE failed to start execution")
                
                # Check if KAPE files exist
                workspace_path = self.config.get_kape_setting("base_path")
                kape_check = self.session_manager.execute_command(
                    session, "runscript", 
                    f"runscript -Raw=```Get-ChildItem '{workspace_path}\\' | Select-Object Name```", 
                    is_admin=True
                )
                if kape_check:
                    self.logger.info(f"Files in {workspace_path}: {kape_check.stdout}")
                
                # Check CLI file content
                workspace_path = self.config.get_kape_setting("base_path")
                cli_check = self.session_manager.execute_command(
                    session, "runscript", 
                    f"runscript -Raw=```Get-Content '{workspace_path}\\_kape.cli' -ErrorAction SilentlyContinue```", 
                    is_admin=True
                )
                if cli_check and cli_check.stdout:
                    self.logger.info(f"KAPE CLI content: {cli_check.stdout}")
                else:
                    self.logger.error("CLI file not found or empty")
                
                return None
                
            self.logger.info("KAPE execution started")
            
            # Monitor execution
            if not self.monitor_kape_execution(session):
                self.logger.error("KAPE execution monitoring failed")
                return None
                
            # Get collection results
            workspace_path = self.config.get_kape_setting("base_path")
            ls_result = self.session_manager.execute_command(
                session, "runscript", f"ls {workspace_path}\\temp\\", is_admin=False
            )
            
            if not ls_result:
                self.logger.error("Failed to list results directory")
                return None
                
            # Find triage file - handle both with and without extension
            # Pattern now optionally matches .vhdx, .zip, or .7z extensions
            triage_pattern = r"(\d{4}-\d{2}-\d{2}T\d+)(_)([a-zA-Z0-9\-]+)(-triage)(?:\.(vhdx|zip|7z))?"
            matches = re.findall(triage_pattern, ls_result.stdout)
            
            if not matches:
                self.logger.error("No KAPE archive found")
                self.logger.info(f"Directory contents: {ls_result.stdout}")
                return None
                
            # Return the full match without extension (for backward compatibility)
            # The extension will be added later in download_kape_results if needed
            full_match = ''.join(matches[0][:4]).strip()  # Take first 4 groups (without extension)
            self.logger.info(f"KAPE collection completed: {full_match}")
            return full_match
            
        except Exception as e:
            self.logger.error(f"Error in run_kape_collection: {e}", exc_info=True)
            return None
        finally:
            # Always attempt to close RTR session
            if session:
                try:
                    self.session_manager.end_session(session)
                except Exception as e:
                    self.logger.warning(f"Failed to close RTR session: {e}")
        
    def prepare_kape_package(self, target: str) -> Path:
        """
        Prepare KAPE package for deployment
        
        Args:
            target: KAPE target specification
            
        Returns:
            Path to prepared package
        """
        try:
            # Get KAPE directory from package resources
            try:
                # Try to use importlib.resources (Python 3.9+)
                try:
                    from importlib import resources
                    with resources.path('fnerd_falconpy.resources', 'kape') as p:
                        kape_dir = Path(p)
                except:
                    # Fallback to pkg_resources
                    import pkg_resources
                    kape_dir = Path(pkg_resources.resource_filename('fnerd_falconpy', 'resources/kape'))
            except:
                # Fallback for development
                package_root = Path(__file__).parent.parent
                kape_dir = package_root / "resources" / "kape"
            
            kape_cli_file = kape_dir / "_kape.cli"
            
            if not kape_dir.exists():
                raise FileNotFoundError(f"KAPE directory not found at: {kape_dir}")
                
            # Write CLI command
            # TEMPORARY FIX: Use only --vhdx since 7z.exe is missing from package
            # TODO: Add 7z.exe and 7z.dll to KAPE package for .7z compression
            workspace_path = self.config.get_kape_setting("base_path")
            command = (
                f'.\\kape.exe --tsource C: --tdest {workspace_path}\\temp '
                f'--target {target} --vhdx "%m-triage"'
            )
            
            try:
                kape_cli_file.write_text(command)
                self.logger.info(f"KAPE command file written to: {kape_cli_file}")
            except PermissionError as e:
                self.logger.error(f"Permission denied when writing CLI file: {e}")
                raise
            except OSError as e:
                self.logger.error(f"OS error when writing CLI file: {e}")
                raise
                
            # Zip KAPE directory
            return self._zip_kape_directory(kape_dir)
            
        except Exception as e:
            self.logger.error(f"Error preparing KAPE package: {e}", exc_info=True)
            raise
            
    def _zip_kape_directory(self, kape_dir: Path) -> Path:
        """Zip the KAPE directory for deployment"""
        try:
            if not kape_dir.exists():
                raise FileNotFoundError(f"KAPE directory not found at: {kape_dir}")
                
            if not kape_dir.is_dir():
                raise NotADirectoryError(f"Path exists but is not a directory: {kape_dir}")
                
            zip_path = kape_dir.parent / "kape.zip"
            
            # Delete existing zip if it exists
            if zip_path.exists():
                try:
                    zip_path.unlink()
                except Exception as e:
                    raise OSError(f"Failed to remove existing zip file: {e}")
                    
            # Create zip file
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                files_added = False
                
                for file in kape_dir.rglob('*'):
                    try:
                        if file.is_file() and file.name != '.DS_Store':
                            arcname = file.relative_to(kape_dir)
                            zipf.write(file, arcname=arcname)
                            files_added = True
                    except (PermissionError, OSError) as e:
                        self.logger.warning(f"Skipping file {file} due to error: {e}")
                        
                if not files_added:
                    raise FileNotFoundError("No files found to add to zip archive")
                    
            # Verify the zip file
            if not zip_path.exists() or zip_path.stat().st_size == 0:
                raise OSError(f"Zip file wasn't created properly or is empty: {zip_path}")
                
            self.logger.info(f"KAPE directory zipped to: {zip_path}")
            return zip_path
            
        except Exception as e:
            self.logger.error(f"Error zipping KAPE directory: {e}", exc_info=True)
            raise
        
    def monitor_kape_execution(self, session: RTRSession, timeout: int = 7200) -> bool:
        """
        Monitor KAPE execution progress
        
        Args:
            session: Active RTR session
            timeout: Maximum wait time in seconds
            
        Returns:
            True if completed successfully, False otherwise
        """
        try:
            interval = 60  # Check every 60 seconds
            start_time = time.time()
            last_pulse_time = time.time()
            pulse_interval = 300  # Pulse every 5 minutes (session timeout is 10 minutes)
            
            self.logger.info(f"Monitoring KAPE execution (timeout: {timeout/60} minutes)")
            
            while True:
                elapsed_seconds = time.time() - start_time
                
                # Check for timeout
                if elapsed_seconds > timeout:
                    self.logger.error(f"KAPE execution exceeded maximum wait time of {timeout/60} minutes")
                    return False
                
                # Pulse session if needed to prevent timeout (CRITICAL FIX)
                time_since_last_pulse = time.time() - last_pulse_time
                if time_since_last_pulse >= pulse_interval:
                    if self.session_manager.pulse_session(session):
                        self.logger.debug(f"Session pulsed successfully after {time_since_last_pulse/60:.1f} minutes")
                        last_pulse_time = time.time()
                    else:
                        self.logger.warning("Failed to pulse session - session may timeout")
                    
                # Check if KAPE is still running
                ps_result = self.session_manager.execute_command(
                    session, "ps", "ps", is_admin=True
                )
                
                if not ps_result:
                    self.logger.error("Failed to get process status during KAPE monitoring")
                    return False
                    
                # Check if kape.exe is still in process list
                if 'kape.exe' not in ps_result.stdout:
                    # KAPE has finished
                    self.logger.info("KAPE execution completed")
                    return True
                    
                # Still running - log progress
                minutes_passed = elapsed_seconds / 60
                self.logger.info(f"KAPE still running... {minutes_passed:.1f} minutes elapsed")
                
                # Wait before next check
                time.sleep(interval)
                
        except Exception as e:
            self.logger.error(f"Error monitoring KAPE execution: {e}", exc_info=True)
            return False
        
    def upload_kape_results(self, host_info: HostInfo, collection_file: str) -> bool:
        """
        Upload KAPE collection results to cloud storage
        
        Args:
            host_info: Target host information
            collection_file: Name of the collection file
            
        Returns:
            True if successful, False otherwise
        """
        session = None
        try:
            # Start RTR session
            session = self.session_manager.start_session(host_info.aid)
            if not session:
                self.logger.error("Failed to start RTR session")
                return False
                
            # First, check what files KAPE actually created
            workspace_path = self.config.get_kape_setting("base_path")
            ls_result = self.session_manager.execute_command(
                session, "runscript", f"ls {workspace_path}\\temp\\", is_admin=False
            )
            
            if not ls_result:
                self.logger.error("Failed to list results directory")
                return False
                
            # Find triage file - handle both with and without extension
            # Pattern now optionally matches .vhdx, .zip, or .7z extensions
            triage_pattern = r"(\d{4}-\d{2}-\d{2}T\d+)(_)([a-zA-Z0-9\-]+)(-triage)(?:\.(vhdx|zip|7z))?"
            matches = re.findall(triage_pattern, ls_result.stdout)
            
            if not matches:
                self.logger.error("No KAPE archive found")
                print(f"[!] No KAPE archive found in temp directory")
                self.logger.info(f"Directory contents: {ls_result.stdout}")
                return False
                
            # Get the actual filename (without extension for backward compatibility)
            triage_name = ''.join(matches[0][:4]).strip()  # Take first 4 groups (without extension)
            
            # Generate upload URL using configuration
            bucket_name = self.config.get_s3_bucket()
            proxy_host = self.config.get_proxy_host()
            
            # Use .7z extension since CrowdStrike RTR converts to 7z format
            url, key = self.cloud_storage.generate_upload_url(
                bucket_name, 
                filename=f"{triage_name}.7z"
            )
            
            if not url:
                self.logger.error("Failed to generate upload URL")
                return False
                
            # Replace S3 URL with proxy URL if proxy is enabled
            if self.config.is_proxy_enabled():
                proxied_url = url.replace(f"{bucket_name}.s3.amazonaws.com", proxy_host)
            else:
                proxied_url = url
            
            # Add hosts file entries dynamically from configuration
            hosts_cmd = self.config.generate_hosts_command(platform="windows")
            
            if hosts_cmd:
                self.logger.info(f"Adding {len(self.config.get_host_entries())} host entries to /etc/hosts")
                self.session_manager.execute_command(
                    session, "runscript", hosts_cmd, is_admin=True
                )
            
            # Now construct the full path - look for .zip extension
            workspace_path = self.config.get_kape_setting("base_path")  
            file_path = f"{workspace_path}\\temp\\{triage_name}.zip"
            
            # Wait for ZIP file to be stable before starting upload
            self.logger.info(f"Found KAPE file: {triage_name}, waiting for stability...")
            print(f"[*] Found KAPE file: {triage_name}, waiting for stability...")
            
            zip_ready = self._wait_for_file_stability(session, file_path, max_wait=600)  # 10 minutes max
            
            if not zip_ready:
                self.logger.error("ZIP file never became stable, upload cannot proceed")
                print("[!] ZIP file never became stable, upload cannot proceed")
                return False
                
            # Get file size now that we know it's stable
            stat_result = self.session_manager.execute_command(
                session, "runscript", 
                f"runscript -Raw=```(Get-Item '{file_path}').Length```", 
                is_admin=True
            )
            
            file_size = 0
            if stat_result and stat_result.stdout.strip().isdigit():
                file_size = int(stat_result.stdout.strip())
                self.logger.info(f"KAPE collection file size: {file_size} bytes ({file_size/1024/1024:.1f} MB)")
            else:
                self.logger.warning("Could not determine file size, using default wait time")
                file_size = 5 * 1024 * 1024 * 1024  # Assume 5GB if we can't get size
                
            self.logger.info("Starting upload process after KAPE completion")
            
            # Now execute upload command
            upload_cmd = (
                f"runscript -Raw=```"
                f"Set-ItemProperty -Path 'HKLM:\\SOFTWARE\\Microsoft\\Internet Explorer\\Main' "
                f"-Name 'DisableFirstRunCustomize' -Value 2; "
                f"Start-Process powershell -WindowStyle hidden -ArgumentList "
                f"\"Invoke-WebRequest -Method PUT -Infile '{workspace_path}\\temp\\{triage_name}.zip' "
                f"-Uri '{proxied_url}'\""
                f"```"
            )
            
            self.session_manager.execute_command(
                session, "runscript", upload_cmd, is_admin=True
            )
            
            self.logger.info(f"Upload of {triage_name}.zip has begun")
            
            # IMPORTANT: Dynamic wait time before cleanup based on file size
            # Using same logic as UAC for consistency
            UPLOAD_RATE = 1 * 1024 * 1024  # 1MB/s realistic upload rate
            min_wait_time = 300  # 5 minutes minimum
            safety_multiplier = 1.5  # 50% safety margin
            calculated_wait = int((file_size / UPLOAD_RATE) * safety_multiplier)
            
            # Use the larger of minimum wait or calculated wait
            actual_wait_time = max(min_wait_time, calculated_wait)
            
            # Cap at 30 minutes to avoid excessive waits
            max_wait_time = 1800  # 30 minutes
            actual_wait_time = min(actual_wait_time, max_wait_time)
            
            self.logger.info(f"Calculated wait time: {actual_wait_time} seconds ({actual_wait_time/60:.1f} minutes)")
            self.logger.info(f"Based on file size {file_size/1024/1024:.1f}MB with safety margin")
            
            # Monitor upload progress instead of static wait
            # PowerShell's Invoke-WebRequest runs in background, so we monitor for completion
            start_time = time.time()
            last_pulse_time = time.time()
            pulse_interval = 300  # Pulse every 5 minutes (session timeout is 10 minutes)
            check_interval = 10  # Check every 10 seconds
            upload_complete = False
            
            while not upload_complete:
                elapsed = time.time() - start_time
                
                # Pulse session if needed to prevent timeout during long uploads
                time_since_last_pulse = time.time() - last_pulse_time
                if time_since_last_pulse >= pulse_interval:
                    if self.session_manager.pulse_session(session):
                        self.logger.debug(f"Session pulsed during upload after {time_since_last_pulse/60:.1f} minutes")
                        last_pulse_time = time.time()
                    else:
                        self.logger.warning("Failed to pulse session during upload - session may timeout")
                
                # Check if PowerShell upload process is still running using WMI for command line access
                ps_check = self.session_manager.execute_command(
                    session, "runscript",
                    "runscript -Raw=```Get-WmiObject Win32_Process -Filter \"Name='powershell.exe'\" | Where-Object { $_.CommandLine -like '*Invoke-WebRequest*' -and $_.CommandLine -like '*PUT*' } | Measure-Object | Select-Object -ExpandProperty Count```",
                    is_admin=True
                )
                
                if ps_check and ps_check.stdout.strip().isdigit():
                    ps_count = int(ps_check.stdout.strip())
                    if ps_count == 0:
                        # No PowerShell upload processes running - upload is complete
                        self.logger.info("Upload process completed")
                        # Wait a bit for finalization
                        time.sleep(30)
                        upload_complete = True
                        break
                
                # Check for timeout
                if elapsed > actual_wait_time:
                    self.logger.warning(f"Upload monitoring exceeded calculated time of {actual_wait_time/60:.1f} minutes")
                    upload_complete = True
                    break
                
                # Log progress
                if int(elapsed) % 30 == 0:  # Every 30 seconds
                    self.logger.info(f"Upload in progress... {elapsed/60:.1f} minutes elapsed")
                
                time.sleep(check_interval)
            
            # FINAL S3 VERIFICATION - This is the authoritative check for upload success
            self.logger.info("Performing final S3 verification...")
            s3_filename = f"{triage_name}.7z"
            if self._verify_s3_upload_success(bucket_name, s3_filename, file_size):
                self.logger.info(f"✅ Upload verification successful: {s3_filename} confirmed in S3")
                upload_success = True
            else:
                self.logger.error(f"❌ Upload verification failed: {s3_filename} not found in S3 or size mismatch")
                upload_success = False
            
            return upload_success
            
        except Exception as e:
            self.logger.error(f"Error uploading KAPE results: {e}", exc_info=True)
            return False
        finally:
            # CRITICAL: Always perform workspace cleanup for operational security
            if session:
                try:
                    self.logger.info("Performing post-upload workspace cleanup...")
                    print("[*] Cleaning up workspace after upload...")
                    
                    # Create a minimal host info for Windows (since this is KAPE)
                    class MinimalHostInfo:
                        def __init__(self):
                            self.platform = "windows"
                            self.hostname = getattr(host_info, 'hostname', 'unknown')
                    
                    cleanup_host_info = MinimalHostInfo()
                    
                    # Attempt cleanup
                    cleanup_success = self.cleanup_manager.cleanup_workspace(session, cleanup_host_info)
                    
                    if cleanup_success:
                        self.logger.info("✅ Post-upload workspace cleanup completed")
                        print("[+] Post-upload workspace cleanup completed")
                    else:
                        # Emergency cleanup if normal fails
                        self.logger.warning("Normal post-upload cleanup failed, attempting emergency cleanup...")
                        emergency_success = self.cleanup_manager.emergency_cleanup(session, cleanup_host_info)
                        if emergency_success:
                            self.logger.warning("⚠️ Emergency post-upload cleanup completed")
                            print("[+] Emergency post-upload cleanup completed")
                        else:
                            self.logger.error("❌ Post-upload cleanup failed")
                            print("[!] Post-upload cleanup failed")
                    
                except Exception as cleanup_error:
                    self.logger.error(f"Post-upload cleanup error: {cleanup_error}", exc_info=True)
                    print(f"[!] Post-upload cleanup error: {cleanup_error}")
                
                # Always attempt to close RTR session
                try:
                    self.session_manager.end_session(session)
                except Exception as e:
                    self.logger.warning(f"Failed to close RTR session: {e}")
    
    def download_kape_results(self, host_info: HostInfo, collection_file: str) -> bool:
        """
        Download KAPE collection results to current working directory
        
        Args:
            host_info: Target host information
            collection_file: Name of the collection file
            
        Returns:
            True if successful, False otherwise
        """
        session = None
        try:
            # Start new RTR session for download
            session = self.session_manager.start_session(host_info.aid)
            if not session:
                self.logger.error("Failed to start RTR session for download")
                return False
                
            # Change to the collection directory
            workspace_path = self.config.get_kape_setting("base_path")
            self.session_manager.execute_command(
                session, "cd", f"cd {workspace_path}\\temp", is_admin=True
            )
            
            # Add .zip extension if not present
            if not collection_file.endswith('.zip'):
                collection_file = f"{collection_file}.zip"
                self.logger.info(f"Looking for collection file: {collection_file}")
            
            # Get file size for verification
            file_size_result = self.session_manager.execute_command(
                session, "runscript", 
                f"runscript -Raw=```(Get-Item '{collection_file}').Length```",
                is_admin=True
            )
            
            expected_file_size = 0
            if file_size_result and file_size_result.stdout.strip().isdigit():
                expected_file_size = int(file_size_result.stdout.strip())
                self.logger.info(f"Remote file size: {expected_file_size:,} bytes ({expected_file_size/1024/1024:.1f} MB)")
                print(f"[*] Remote file size: {expected_file_size:,} bytes ({expected_file_size/1024/1024:.1f} MB)")
            else:
                self.logger.warning("Could not determine remote file size")
            
            # Use current working directory instead of Downloads
            import os
            current_dir = Path(os.getcwd())
            # Save with .7z extension since CrowdStrike RTR converts to 7z format
            local_filename = collection_file.replace('.zip', '.7z')
            local_file_path = current_dir / local_filename
            
            
            # Use the file manager to download the file
            self.logger.info(f"Downloading {collection_file} to {local_file_path}")
            print(f"[*] Downloading {collection_file} to {local_file_path}")
            print(f"[*] This may take several minutes for large files...")
            
            download_success = self.file_manager.download_file(
                session=session,
                device_id=host_info.aid,
                remote_path=f"{workspace_path}\\temp\\{collection_file}",
                local_path=str(local_file_path),
                file_size=expected_file_size
            )
            
            if download_success:
                # Verify downloaded file exists and has correct size
                if local_file_path.exists():
                    actual_file_size = local_file_path.stat().st_size
                    self.logger.info(f"Downloaded file size: {actual_file_size:,} bytes")
                    print(f"[*] Downloaded file size: {actual_file_size:,} bytes")
                    
                    # Compare file sizes if we have expected size
                    if expected_file_size > 0:
                        size_diff = abs(actual_file_size - expected_file_size)
                        size_threshold = max(1024, expected_file_size * 0.01)  # 1KB or 1% tolerance
                        
                        if size_diff > size_threshold:
                            self.logger.error(f"File size mismatch: expected {expected_file_size:,}, got {actual_file_size:,}")
                            print(f"[!] File size mismatch: expected {expected_file_size:,}, got {actual_file_size:,}")
                            return False
                    
                    self.logger.info(f"✅ Successfully downloaded and verified {local_filename}")
                    print(f"[+] Successfully downloaded and verified {local_filename}")
                    print(f"[+] Local file: {local_file_path} ({actual_file_size:,} bytes)")
                    print(f"[*] Note: File is in 7z format (CrowdStrike RTR automatic conversion)")
                    
                    # Perform workspace cleanup after successful download
                    self._cleanup_workspace_after_download(session, host_info)
                    return True
                else:
                    self.logger.error(f"Downloaded file not found at {local_file_path}")
                    print(f"[!] Downloaded file not found at {local_file_path}")
                    return False
            else:
                self.logger.error(f"❌ Failed to download {collection_file}")
                print(f"[!] Failed to download {collection_file}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error downloading KAPE results: {e}", exc_info=True)
            print(f"[!] Error downloading KAPE results: {e}")
            return False
            
        finally:
            # Always attempt to close RTR session
            if session:
                try:
                    self.session_manager.end_session(session)
                    self.logger.info("Download RTR session closed")
                except Exception as e:
                    self.logger.warning(f"Failed to close download RTR session: {e}")
                    
    def _cleanup_workspace_after_download(self, session: RTRSession, host_info: HostInfo) -> None:
        """
        Perform workspace cleanup after successful download
        CRITICAL: Must cd away from the directory first since RTR session is holding it open!
        
        Args:
            session: Active RTR session
            host_info: Target host information
        """
        try:
            self.logger.info("Performing post-download workspace cleanup...")
            
            platform = Platform(host_info.platform.lower())
            
            # CRITICAL: Change directory AWAY from workspace first!
            # The RTR session is currently in workspace\temp which is why cleanup fails
            if platform == Platform.WINDOWS:
                workspace_path = self.config.get_kape_setting("base_path")
                # Change to root directory to release the handle
                self.logger.info("Changing directory away from workspace before cleanup...")
                self.session_manager.execute_command(session, "cd", "cd C:\\", is_admin=True)
                
                # Now we can remove the directory since we're not in it anymore
                cleanup_cmd = f"runscript -Raw=```if (Test-Path '{workspace_path}') {{ Remove-Item -Path '{workspace_path}' -Recurse -Force -ErrorAction Stop }}```"
            else:
                workspace_path = self.config.get_workspace_path(Platform.LINUX)
                # Change to root directory to release the handle
                self.logger.info("Changing directory away from workspace before cleanup...")
                self.session_manager.execute_command(session, "cd", "cd /", is_admin=True)
                
                # Unix cleanup - simple and direct
                cleanup_cmd = f"runscript -Raw=```rm -rf {workspace_path} 2>/dev/null || true```"
            
            # Small delay to ensure cd completes
            time.sleep(2)
            
            self.logger.info(f"Cleaning workspace directory: {workspace_path}")
            result = self.session_manager.execute_command(session, "runscript", cleanup_cmd, is_admin=True)
            
            if result:
                self.logger.info("✅ Post-download workspace cleanup completed")
                print("[+] Post-download workspace cleanup completed")
            else:
                self.logger.warning("Workspace cleanup command had no result (may have already been cleaned)")
                    
        except Exception as e:
            self.logger.error(f"Error during post-download cleanup: {e}", exc_info=True)
            print(f"[!] Error during post-download cleanup: {e}")
            
    def _wait_for_file_stability(self, session: RTRSession, file_path: str, max_wait: int = 300) -> bool:
        """
        DEPRECATED: Complex file monitoring approach that caused race conditions.
        This method is no longer used. KAPE now uses simple process monitoring only.
        
        Args:
            session: Active RTR session
            file_path: Path to the file to check
            max_wait: Maximum time to wait in seconds
            
        Returns:
            True if file is stable, False if timeout or still being written
        """
        try:
            start_time = time.time()
            last_size = -1
            stable_count = 0
            required_stable_checks = 3  # File must be same size for 3 consecutive checks
            
            # Determine file type for better logging
            file_type = "VHDX" if file_path.endswith('.vhdx') else "7z archive"
            self.logger.info(f"Checking {file_type} file stability for: {file_path}")
            
            # Track if we've seen the file at all
            file_ever_existed = False
            
            while time.time() - start_time < max_wait:
                elapsed = time.time() - start_time
                
                # Check if file exists and get its size
                size_result = self.session_manager.execute_command(
                    session, "runscript",
                    f"runscript -Raw=```if (Test-Path '{file_path}') {{ (Get-Item '{file_path}').Length }} else {{ Write-Output '' }}```",
                    is_admin=True
                )
                
                if not size_result or not size_result.stdout.strip():
                    # File doesn't exist yet
                    if not file_ever_existed:
                        # Log only occasionally to avoid spam
                        if int(elapsed) % 30 == 0:  # Every 30 seconds
                            self.logger.debug(f"{file_type} file doesn't exist yet after {elapsed:.0f}s: {file_path}")
                    else:
                        # File existed before but now missing - this is unusual
                        self.logger.warning(f"{file_type} file disappeared: {file_path}")
                    time.sleep(10)
                    continue
                
                # File exists now
                if not file_ever_existed:
                    file_ever_existed = True
                    self.logger.info(f"{file_type} file appeared after {elapsed:.0f}s")
                    
                try:
                    current_size = int(size_result.stdout.strip())
                except (ValueError, AttributeError):
                    self.logger.debug(f"Could not parse {file_type} file size for: {file_path}")
                    time.sleep(10)
                    continue
                
                if current_size == last_size and current_size > 0:
                    stable_count += 1
                    self.logger.debug(f"{file_type} size stable: {current_size} bytes (check {stable_count}/{required_stable_checks})")
                    
                    if stable_count >= required_stable_checks:
                        # File has been same size for required number of checks
                        # Additional check: try to verify file is not locked
                        lock_check = self.session_manager.execute_command(
                            session, "runscript",
                            f"runscript -Raw=```try {{ [System.IO.File]::OpenWrite('{file_path}').Close(); Write-Output 'UNLOCKED' }} catch {{ Write-Output 'LOCKED' }}```",
                            is_admin=True
                        )
                        
                        if lock_check and 'UNLOCKED' in lock_check.stdout:
                            self.logger.info(f"{file_type} is stable and unlocked: {current_size} bytes ({current_size/1024/1024:.1f} MB)")
                            return True
                        else:
                            self.logger.debug(f"{file_type} still locked, continuing to wait...")
                            stable_count = 0  # Reset counter if file is locked
                else:
                    # File size changed, reset counter
                    if current_size != last_size:
                        size_mb = current_size / 1024 / 1024
                        last_size_mb = last_size / 1024 / 1024 if last_size > 0 else 0
                        self.logger.debug(f"{file_type} size changed: {last_size_mb:.1f}MB -> {size_mb:.1f}MB")
                        stable_count = 0
                        last_size = current_size
                
                time.sleep(10)  # Check every 10 seconds
                
            self.logger.warning(f"{file_type} stability check timed out after {max_wait} seconds (file ever existed: {file_ever_existed})")
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking file stability: {e}", exc_info=True)
            return False
    
    def _verify_s3_upload_success(self, bucket_name: str, object_key: str, expected_size: int) -> bool:
        """
        Verify that the file was successfully uploaded to S3 by checking bucket contents
        
        Args:
            bucket_name: S3 bucket name
            object_key: S3 object key (filename)
            expected_size: Expected file size in bytes
            
        Returns:
            True if file exists in S3 and matches expected size, False otherwise
        """
        try:
            self.logger.info(f"Verifying S3 upload: s3://{bucket_name}/{object_key}")
            
            # Use cloud storage manager to verify upload
            verification_result = self.cloud_storage.verify_s3_upload(bucket_name, object_key, expected_size)
            
            if verification_result:
                self.logger.info("S3 upload verification successful")
                return True
            else:
                self.logger.error("S3 upload verification failed")
                
                # Try to get object info for debugging
                object_info = self.cloud_storage.get_s3_object_info(bucket_name, object_key)
                if object_info:
                    self.logger.error(f"S3 object exists but size mismatch: expected {expected_size}, got {object_info['size']}")
                else:
                    self.logger.error("S3 object not found in bucket")
                return False
                
        except Exception as e:
            self.logger.error(f"Error during S3 verification: {e}", exc_info=True)
            return False