"""
Unix-like Artifacts Collector (UAC) for forensic collection on Unix/Linux/macOS systems.
"""

import os
import re
import shutil
import time
import tarfile
import tempfile
from typing import List, Optional, Dict
from pathlib import Path
from datetime import datetime
from fnerd_falconpy.core.base import (
    HostInfo, RTRSession, Platform,
    ILogger, DefaultLogger, IConfigProvider
)
from fnerd_falconpy.managers.managers import FileManager, SessionManager
from fnerd_falconpy.utils.cloud_storage import CloudStorageManager
from fnerd_falconpy.utils.workspace_cleanup import WorkspaceCleanupManager
from fnerd_falconpy.utils.pre_execution_cleanup import PreExecutionCleanupManager


class UACCollector:
    """Handles UAC (Unix-like Artifacts Collector) forensic collection operations"""
    
    def __init__(self, file_manager: FileManager, session_manager: SessionManager,
                 cloud_storage: CloudStorageManager, config: IConfigProvider,
                 logger: Optional[ILogger] = None):
        """
        Initialize UAC collector
        
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
        self.logger = logger or DefaultLogger("UACCollector")
        
        # Initialize workspace cleanup manager
        self.cleanup_manager = WorkspaceCleanupManager(session_manager, config, self.logger)
        
        # Initialize pre-execution cleanup manager
        self.pre_cleanup_manager = PreExecutionCleanupManager(session_manager, config, self.logger)
        
    def _execute_with_retry(self, session: RTRSession, base_command: str, command: str, 
                           is_admin: bool = True, max_retries: int = 3, backoff_base: float = 2.0):
        """
        Execute command with retry logic for network resilience
        
        Args:
            session: RTR session
            base_command: Base command 
            command: Command string
            is_admin: Admin privileges
            max_retries: Maximum retry attempts
            backoff_base: Exponential backoff base
            
        Returns:
            Command result or None
        """
        for attempt in range(max_retries + 1):
            try:
                result = self.session_manager.execute_command(session, base_command, command, is_admin)
                if result:
                    return result
                    
                # If result is None but no exception, it might be a temporary issue
                if attempt < max_retries:
                    wait_time = backoff_base ** attempt
                    self.logger.debug(f"Command returned None, retrying in {wait_time}s (attempt {attempt + 1}/{max_retries + 1})")
                    time.sleep(wait_time)
                    
            except Exception as e:
                if attempt < max_retries:
                    # Check if this is a network-related error
                    error_str = str(e).lower()
                    if any(net_error in error_str for net_error in ['resolve', 'connection', 'network', 'timeout', 'dns']):
                        wait_time = backoff_base ** attempt
                        self.logger.warning(f"Network error on attempt {attempt + 1}, retrying in {wait_time}s: {e}")
                        time.sleep(wait_time)
                        continue
                    else:
                        # Non-network error, don't retry
                        self.logger.error(f"Non-network error, not retrying: {e}")
                        return None
                else:
                    self.logger.error(f"All retry attempts failed: {e}")
                    return None
                    
        return None
        
    def run_uac_collection(self, host_info: HostInfo, profile: str = "ir_triage") -> Optional[str]:
        """
        Run UAC forensic collection on Unix/Linux/macOS systems
        
        Args:
            host_info: Target host information
            profile: UAC profile to use (default: ir_triage)
            
        Returns:
            Collection file name or None
        """
        session = None
        try:
            # Validate platform
            platform = Platform(host_info.platform.lower())
            if platform == Platform.WINDOWS:
                self.logger.error("UAC is not supported on Windows. Use KAPE instead.")
                return None
                
            self.logger.info(f"Starting UAC collection on {host_info.hostname} with profile: {profile}")
            print(f"[*] Starting UAC collection on {host_info.hostname} with profile: {profile}")
            
            # Check for UAC in cloud files first
            self.logger.info("Checking cloud files for UAC package")
            
            # Upload UAC to cloud
            self.logger.info("Uploading UAC to cloud")
            cloud_files = self.file_manager.list_cloud_files(host_info.cid)
            
            # Use fixed filename but force fresh upload
            uac_file = 'uac.zip'
            
            # Delete existing UAC package to ensure fresh upload
            if uac_file in cloud_files:
                self.logger.info(f"Deleting existing {uac_file} from cloud")
                self.file_manager.delete_from_cloud(host_info.cid, uac_file)
                # Wait for deletion to complete
                time.sleep(5)
                
            # Use pre-existing UAC package from resources
            # NEVER create temporary files
            package_root = Path(__file__).parent.parent
            uac_package = package_root / "resources" / "uac" / "uac.zip"
            
            if not uac_package.exists():
                self.logger.error("UAC package not found in resources. Please ensure uac.zip exists at fnerd_falconpy/resources/uac/uac.zip")
                print("[!] UAC package not found in resources")
                return None
                
            self.logger.info(f"Using UAC package from: {uac_package}")
            print(f"[*] Using UAC package from resources")
            
            # Log package details for debugging
            self.logger.info(f"UAC package path: {uac_package}")
            self.logger.info(f"Package exists: {uac_package.exists()}")
            self.logger.info(f"Package size: {uac_package.stat().st_size if uac_package.exists() else 'N/A'}")
            
            # Verify package contains custom profiles
            import zipfile
            with zipfile.ZipFile(uac_package, 'r') as zf:
                profiles_in_package = [n for n in zf.namelist() if 'profiles/' in n and n.endswith('.yaml')]
                custom_profiles = [p for p in profiles_in_package if any(custom in p for custom in ['quick_triage_optimized', 'ir_triage_no_hash', 'network_compromise', 'malware_hunt_fast'])]
                self.logger.info(f"Package contains {len(profiles_in_package)} profiles, including {len(custom_profiles)} custom profiles")
                print(f"[*] UAC package contains {len(profiles_in_package)} profiles ({len(custom_profiles)} custom)")
            
            if not self.file_manager.upload_to_cloud(
                host_info.cid, 
                str(uac_package), 
                'UAC Unix Artifacts Collector Upload', 
                '4n6 UAC Tool'
            ):
                self.logger.error("Failed to upload uac.zip")
                return None
                
            # Wait longer for cloud sync to ensure file is available
            self.logger.info("Waiting for cloud sync...")
            time.sleep(30)  # Increased from 15 to 30 seconds
            
            # Refresh cloud files list after waiting
            cloud_files = self.file_manager.list_cloud_files(host_info.cid)
            
            # Verify file is in cloud
            cloud_files = self.file_manager.list_cloud_files(host_info.cid)
            self.logger.info(f"Cloud files after upload: {cloud_files}")
            
            if uac_file not in cloud_files:
                self.logger.error(f"{uac_file} not found in cloud files after upload")
                self.logger.error(f"Available files: {cloud_files}")
                return None
                
            self.logger.info(f"Uploaded fresh UAC package: {uac_file}")
            print(f"[*] Uploaded fresh UAC package: {uac_file}")
                
            # Start RTR session
            session = self.session_manager.start_session(host_info.aid)
            if not session:
                self.logger.error("Failed to start RTR session")
                return None
            
            # CRITICAL: Ensure clean environment before starting collection
            # Check for existing UAC processes and workspace directories
            self.logger.info("Performing pre-execution cleanup check...")
            print("[*] Performing pre-execution cleanup check...")
            
            if not self.pre_cleanup_manager.ensure_clean_environment(session, host_info):
                self.logger.error("Pre-execution cleanup failed - aborting collection")
                print("[!] Pre-execution cleanup failed - aborting collection for safety")
                return None
                
            # Deploy and execute UAC
            self.logger.info("Deploying UAC on target host")
            print(f"[*] Deploying UAC on target host using {uac_file}")
            
            # Use configurable workspace path for deployment (directory created by pre-execution cleanup)
            deploy_path = self.config.get_uac_setting("base_path")
            evidence_path = f"{deploy_path}/evidence"
            
            # CRITICAL: Change to deployment directory FIRST before put (directory created by pre-execution cleanup)
            # NEVER attempt to write to root directory
            self.logger.info(f"Changing to deployment directory: {deploy_path}")
            cd_result = self.session_manager.execute_command(
                session, "cd", f"cd {deploy_path}", is_admin=True
            )
            
            if not cd_result or cd_result.return_code != 0:
                self.logger.error(f"Failed to change to deployment directory: {deploy_path}")
                if cd_result and cd_result.stderr:
                    self.logger.error(f"cd command stderr: {cd_result.stderr}")
                if cd_result and cd_result.stdout:
                    self.logger.error(f"cd command stdout: {cd_result.stdout}")
                return None
            
            # Verify current working directory after cd
            pwd_result = self.session_manager.execute_command(
                session, "runscript", f"runscript -Raw=```pwd```", is_admin=True
            )
            
            if pwd_result and pwd_result.stdout:
                current_dir = pwd_result.stdout.strip()
                self.logger.info(f"Current working directory: {current_dir}")
                if current_dir != deploy_path:
                    self.logger.warning(f"Working directory is {current_dir}, expected {deploy_path}")
            
            # Put UAC package to configured workspace
            self.logger.info(f"Transferring {uac_file} to {deploy_path}")
            put_result = self.session_manager.execute_command(
                session, "put", f"put {uac_file}", is_admin=True
            )
            
            if not put_result or put_result.return_code != 0:
                self.logger.error(f"Failed to transfer {uac_file} to target host")
                if put_result:
                    self.logger.error(f"PUT return code: {put_result.return_code}")
                    if put_result.stderr:
                        self.logger.error(f"PUT stderr: {put_result.stderr}")
                    if put_result.stdout:
                        self.logger.error(f"PUT stdout: {put_result.stdout}")
                else:
                    self.logger.error("PUT command returned None result")
                
                # Check if file exists in cloud files (common cause of PUT failure)
                cloud_files = self.file_manager.list_cloud_files(host_info.cid)
                if uac_file not in cloud_files:
                    self.logger.error(f"{uac_file} not found in cloud files. Available files: {cloud_files}")
                    return None
                else:
                    self.logger.info(f"{uac_file} exists in cloud files, investigating other causes...")
                    
                # If PUT fails, check if file already exists on host
                check_existing = self.session_manager.execute_command(
                    session, "runscript", f"runscript -Raw=```test -f {deploy_path}/{uac_file} && echo 'EXISTS' || echo 'NOT_FOUND'```", is_admin=True
                )
                if check_existing and "EXISTS" in check_existing.stdout:
                    self.logger.warning(f"{uac_file} already exists on host, continuing with existing file")
                    print(f"[!] {uac_file} already exists on host, continuing with existing file")
                else:
                    return None
            
            # Extract UAC - file is now already in the right location
            self.logger.info("Extracting UAC package")
            if uac_file.endswith('.zip'):
                # Use -o to overwrite existing files and capture all output
                extract_cmd = f"runscript -Raw=```cd {deploy_path} && unzip -o {uac_file} 2>&1```"
            else:
                extract_cmd = f"runscript -Raw=```cd {deploy_path} && tar -xzf {uac_file} 2>&1```"
            
            extract_result = self.session_manager.execute_command(
                session, "runscript", extract_cmd, is_admin=True
            )
            
            if not extract_result or extract_result.return_code != 0:
                self.logger.error("Failed to extract UAC package")
                if extract_result:
                    if extract_result.stderr:
                        self.logger.error(f"Extract error: {extract_result.stderr}")
                    if extract_result.stdout:
                        self.logger.error(f"Extract output: {extract_result.stdout}")
                    self.logger.error(f"Extract return code: {extract_result.return_code}")
                print("[!] Failed to extract UAC package - check logs for details")
                return None
                
            # Log extraction output for debugging
            if extract_result and extract_result.stdout:
                self.logger.info(f"Extract output: {extract_result.stdout}")
                # Count how many profiles were extracted
                profile_count = extract_result.stdout.count('/profiles/') + extract_result.stdout.count('profiles/')
                if profile_count > 0:
                    self.logger.info(f"Extracted approximately {profile_count} profile files")
                    # Show which custom profiles were extracted
                    for custom_profile in ['quick_triage_optimized', 'ir_triage_no_hash', 'network_compromise', 'malware_hunt_fast']:
                        if custom_profile in extract_result.stdout:
                            self.logger.info(f"✓ Custom profile extracted: {custom_profile}.yaml")
                            print(f"[*] ✓ Custom profile extracted: {custom_profile}.yaml")
                        else:
                            self.logger.warning(f"✗ Custom profile NOT found in extraction: {custom_profile}.yaml")
                            print(f"[!] ✗ Custom profile NOT found in extraction: {custom_profile}.yaml")
            
            # List what was extracted
            self.logger.info("Checking extracted files...")
            ls_extracted = self.session_manager.execute_command(
                session, "runscript", f"runscript -Raw=```ls -la {deploy_path}```", is_admin=True
            )
            if ls_extracted and ls_extracted.stdout:
                self.logger.info(f"Extracted files:\n{ls_extracted.stdout}")
                
            # Find UAC directory - it extracts as 'uac-main' not 'uac-X.X.X'
            # Use find command to avoid shell globbing issues
            find_cmd = f"runscript -Raw=```find {deploy_path} -maxdepth 1 -type d -name 'uac*' | head -1```"
            ls_result = self.session_manager.execute_command(
                session, "runscript", find_cmd, is_admin=True
            )
            
            if not ls_result or not ls_result.stdout.strip():
                # Fallback: list all directories to debug
                debug_cmd = f"runscript -Raw=```ls -la {deploy_path}```"
                debug_result = self.session_manager.execute_command(
                    session, "runscript", debug_cmd, is_admin=True
                )
                self.logger.error("Could not find UAC directory after extraction")
                if debug_result:
                    self.logger.error(f"Directory contents: {debug_result.stdout}")
                return None
                
            # Extract directory name from full path
            uac_path = ls_result.stdout.strip()
            uac_dir = os.path.basename(uac_path)
            
            self.logger.info(f"Found UAC directory: {uac_dir} at {uac_path}")
            
            # Make UAC executable
            self.session_manager.execute_command(
                session, "runscript", f"runscript -Raw=```chmod +x {uac_path}/uac```", is_admin=True
            )
            
            # Check UAC version
            version_result = self.session_manager.execute_command(
                session, "runscript", f"runscript -Raw=```cd {uac_path} && ./uac --version 2>&1```", is_admin=True
            )
            if version_result and version_result.stdout:
                self.logger.info(f"UAC version: {version_result.stdout.strip()}")
                print(f"[*] UAC version: {version_result.stdout.strip()}")
                
            # Test if UAC can find the requested profile
            test_profile_cmd = f"runscript -Raw=```cd {uac_path} && ./uac -p {profile} --validate-only 2>&1 || echo 'Profile validation result: '$?```"
            test_result = self.session_manager.execute_command(
                session, "runscript", test_profile_cmd, is_admin=True
            )
            if test_result:
                self.logger.info(f"Profile validation test: {test_result.stdout}")
                if "profile not found" in test_result.stdout:
                    self.logger.error(f"UAC cannot find profile '{profile}'")
                    print(f"[!] UAC cannot find profile '{profile}'")
                    # Try without quotes just in case
                    print(f"[*] Testing profile validation with different approaches...")
                    test_cmd2 = f"runscript -Raw=```cd {uac_path} && ./uac --profile list | grep -i {profile}```"
                    test_result2 = self.session_manager.execute_command(
                        session, "runscript", test_cmd2, is_admin=True
                    )
                    if test_result2:
                        print(f"[*] Profile grep result: {test_result2.stdout}")
            
            # List profiles directory to debug
            self.logger.info("Listing UAC profiles directory...")
            profiles_list_cmd = f"runscript -Raw=```ls -la {uac_path}/profiles/```"
            profiles_result = self.session_manager.execute_command(
                session, "runscript", profiles_list_cmd, is_admin=True
            )
            if profiles_result and profiles_result.stdout:
                self.logger.info(f"UAC profiles directory contents:\n{profiles_result.stdout}")
                print(f"[*] Available UAC profiles:")
                # Parse and display profile names
                for line in profiles_result.stdout.split('\n'):
                    if '.yaml' in line and not line.startswith('total'):
                        profile_name = line.split()[-1].replace('.yaml', '')
                        print(f"    - {profile_name}")
            else:
                self.logger.error("Failed to list profiles directory")
                print("[!] Failed to list UAC profiles directory")
            
            # Create evidence directory
            self.session_manager.execute_command(
                session, "runscript", f"runscript -Raw=```mkdir -p {evidence_path}```", is_admin=True
            )
            
            # Execute UAC collection
            self.logger.info(f"Executing UAC collection with profile: {profile}")
            print(f"[*] Executing UAC collection with profile: {profile}")
            print(f"[*] Collection will run in background. Progress updates every 30 seconds...")
            
            # Build UAC command to run in background to avoid timeout
            # Use shell backgrounding instead of nohup (which fails in RTR environment due to TTY limitations)
            # UAC must be executed from within its own directory to find required files
            uac_cmd = f"(cd {uac_path} && ./uac -p {profile} --output-format tar {evidence_path} < /dev/null > {deploy_path}/uac_output.log 2>&1; echo $? > {deploy_path}/uac_exit_code) & echo $! > {deploy_path}/uac.pid && echo 'UAC started in background'"
            
            # Log the exact command for debugging
            self.logger.info(f"UAC command to execute: {uac_cmd}")
                
            # Execute UAC in background (spawns process and returns immediately)
            uac_result = self.session_manager.execute_command(
                session, "runscript", f"runscript -Raw=```{uac_cmd}```", is_admin=True
            )
            
            # Give it a moment to start
            time.sleep(3)
            
            # Check if UAC process started by verifying PID file and process existence
            pid_check_cmd = f"runscript -Raw=```test -f {deploy_path}/uac.pid && cat {deploy_path}/uac.pid```"
            pid_result = self.session_manager.execute_command(
                session, "runscript", pid_check_cmd, is_admin=True
            )
            
            if pid_result and pid_result.stdout.strip().isdigit():
                pid = pid_result.stdout.strip()
                # Verify the process is actually running
                proc_check_cmd = f"runscript -Raw=```ps -p {pid} | grep -v PID | wc -l```"
                proc_result = self.session_manager.execute_command(
                    session, "runscript", proc_check_cmd, is_admin=True
                )
                
                if proc_result and proc_result.stdout.strip() == "1":
                    self.logger.info(f"UAC process started successfully in background (PID: {pid})")
                    print(f"[+] UAC process started successfully in background (PID: {pid})")
                else:
                    # This is expected - the PID is for the subshell that launches UAC and exits
                    self.logger.info(f"UAC launcher process (PID: {pid}) has completed - UAC is running independently")
            else:
                self.logger.info("UAC started in background mode")
            
            if not uac_result:
                self.logger.error("UAC execution failed")
                return None
                
            # Monitor UAC execution
            collection_file = self.monitor_uac_execution(session, evidence_path, host_info.hostname, deploy_path, profile=profile)
            
            if not collection_file:
                self.logger.error("UAC collection monitoring failed")
                return None
                
            self.logger.info(f"UAC collection completed: {collection_file}")
            print(f"[+] UAC collection completed: {collection_file}")
            
            # Return the collection file name - upload/download will be handled by orchestrator
            return collection_file
            
        except Exception as e:
            self.logger.error(f"Error in run_uac_collection: {e}", exc_info=True)
            return None
        finally:
            # Close RTR session but DO NOT cleanup workspace yet
            # Cleanup will be handled after upload/download by the calling method
            if session:
                try:
                    self.session_manager.end_session(session)
                    self.logger.debug("RTR session closed")
                except Exception as e:
                    self.logger.warning(f"Failed to close RTR session: {e}")
                    
    # REMOVED prepare_uac_package method - NEVER create files dynamically
    # UAC package must be pre-built using scripts/build_uac_package.py
    # and stored at resources/uac/uac.zip
                
    def monitor_uac_execution(self, session: RTRSession, evidence_path: str, 
                             hostname: str, deploy_path: str, timeout: Optional[int] = None,
                             profile: str = "ir_triage") -> Optional[str]:
        """
        Monitor UAC execution and wait for completion
        
        Args:
            session: Active RTR session
            evidence_path: Path where UAC stores evidence
            hostname: Hostname for matching output files
            deploy_path: Path where UAC is deployed (for status files)
            timeout: Maximum wait time in seconds (uses profile-specific or default from config)
            profile: UAC profile being used (for timeout selection)
            
        Returns:
            Collection file name or None
        """
        try:
            # Get timeout from configuration
            if timeout is None:
                profile_timeouts = self.config.get_uac_setting("profile_timeouts") or {}
                timeout = profile_timeouts.get(profile, self.config.get_uac_setting("timeout") or 18000)
            
            interval = self.config.get_uac_setting("monitoring_interval") or 30
            start_time = time.time()
            last_progress_time = start_time
            last_file_count = 0
            last_pulse_time = start_time  # Track when we last pulsed the session
            
            self.logger.info(f"Monitoring UAC execution for profile '{profile}' (timeout: {timeout/60:.0f} minutes)")
            print(f"[*] Monitoring UAC execution for profile '{profile}' (timeout: {timeout/60:.0f} minutes)")
            
            while True:
                elapsed_seconds = time.time() - start_time
                
                # Pulse session every 5 minutes to prevent timeout (session timeout is 10 minutes)
                if time.time() - last_pulse_time >= 300:  # Changed from 60 to 300 seconds (5 minutes)
                    try:
                        # Use the proper pulse_session method instead of echo command workaround
                        if self.session_manager.pulse_session(session):
                            self.logger.debug(f"Session pulsed successfully after {(time.time() - last_pulse_time)/60:.1f} minutes")
                        else:
                            self.logger.warning("Failed to pulse session - session may timeout")
                        
                        last_pulse_time = time.time()
                    except Exception as e:
                        # Don't fail the entire operation if pulse fails - just log and continue
                        self.logger.debug(f"Session pulse failed: {e}")
                        last_pulse_time = time.time()
                
                # Try to read UAC output log for real progress with retry logic
                # First check if log file exists and has content
                # Simplified check to avoid timeout - just check if file exists
                log_check = self._execute_with_retry(
                    session, "runscript", f"runscript -Raw=```test -f {deploy_path}/uac_output.log && echo 1 || echo 0```", 
                    is_admin=True, max_retries=1
                )
                
                # Debug: Check what's in the UAC output log if it exists
                if int(elapsed_seconds) % 300 == 0:  # Every 5 minutes, show debug info
                    debug_log = self._execute_with_retry(
                        session, "runscript", f"runscript -Raw=```test -f {deploy_path}/uac_output.log && tail -n 10 {deploy_path}/uac_output.log || echo 'Log file not found'```", 
                        is_admin=True, max_retries=1
                    )
                    if debug_log:
                        # Filter out UAC validation messages that contain __EOF__ (these are normal validation artifacts)
                        log_lines = debug_log.stdout.strip().split('\n')
                        filtered_lines = []
                        for line in log_lines:
                            if '__EOF__' in line and 'artifact not found' in line:
                                # This is a normal UAC validation message, log at debug level only
                                self.logger.debug(f"UAC validation message: {line}")
                            else:
                                filtered_lines.append(line)
                        
                        if filtered_lines:
                            self.logger.info(f"UAC output log (last 10 lines): {chr(10).join(filtered_lines)}")
                
                if log_check and log_check.stdout.strip() == "1":
                    # Log exists with content, try to get progress
                    # Simplified command to avoid timeout - just get last few lines
                    # Use _execute_with_retry with minimal retries to prevent timeout
                    log_result = self._execute_with_retry(
                        session, "runscript", f"runscript -Raw=```tail -n 5 {deploy_path}/uac_output.log 2>/dev/null```", 
                        is_admin=True, max_retries=1
                    )
                else:
                    log_result = None
                
                if log_result and log_result.stdout.strip():
                    # Extract progress from UAC output like: [001/105] 2025-05-28 12:47:03 -0400 artifact_name
                    # Look through the last 5 lines for progress indicator
                    for line in log_result.stdout.strip().split('\n'):
                        if "[" in line and "/" in line and "]" in line:
                            try:
                                progress_part = line.split("]")[0].split("[")[1]
                                if "/" in progress_part:
                                    current, total = progress_part.split("/")
                                    artifact_name = line.split("] ")[-1] if "] " in line else ""
                                    percentage = (int(current) / int(total)) * 100
                                    print(f"\r[*] UAC progress: [{current}/{total}] {percentage:.1f}% - {artifact_name}", end="", flush=True)
                                    # Store progress for smart pulse logic
                                    self._last_uac_progress = artifact_name
                                    break  # Use the first valid progress line found
                            except:
                                pass
                
                # Check for timeout, but be intelligent about it
                if elapsed_seconds > timeout:
                    # Before timing out, check if UAC process is still running
                    pid_check = self.session_manager.execute_command(
                        session, "runscript", f"runscript -Raw=```test -f {deploy_path}/uac.pid && cat {deploy_path}/uac.pid```", is_admin=True
                    )
                    
                    if pid_check and pid_check.stdout.strip().isdigit():
                        pid = pid_check.stdout.strip()
                        proc_check = self.session_manager.execute_command(
                            session, "runscript", f"runscript -Raw=```ps -p {pid} | grep -v PID | wc -l```", is_admin=True
                        )
                        
                        if proc_check and proc_check.stdout.strip() == "1":
                            self.logger.warning(f"UAC exceeded timeout ({timeout/60:.0f} min) but process still running (PID: {pid}). Extending timeout...")
                            print(f"[!] UAC exceeded timeout ({timeout/60:.0f} min) but process still running (PID: {pid}). Extending timeout...")
                            timeout += 1800  # Extend by 30 minutes
                            continue
                    
                    self.logger.error(f"UAC execution exceeded maximum wait time of {timeout/60:.0f} minutes and process not running")
                    return None
                    
                # Check for UAC output files first (primary completion indicator)
                ls_result = self._execute_with_retry(
                    session, "runscript", f"runscript -Raw=```ls -la {evidence_path}```", is_admin=True
                )
                
                if not ls_result:
                    self.logger.error("Failed to list evidence directory")
                    return None
                    
                # UAC creates files with pattern: uac-hostname-os-YYYYMMDDHHMMSS.tar.gz (no T separator)
                # Look for completed archive (timestamp format: YYYYMMDDHHMMSS without T separator)
                pattern = rf"(uac-{hostname}-\w+-\d{{14}}\.tar\.gz)"
                match = re.search(pattern, ls_result.stdout)
                
                if match:
                    collection_file = match.group(1)
                    self.logger.info(f"UAC collection file found: {collection_file}")
                    print(f"\n[+] UAC collection complete: {collection_file}")
                    
                    # Verify file is complete by checking file size stability
                    base_name = collection_file.replace('.tar.gz', '')
                    
                    # Check file size stability over time to ensure compression is complete
                    stability_start = time.time()
                    stability_timeout = 300  # 5 minutes to verify stability (increased for very large files)
                    last_size = None
                    stable_count = 0
                    required_stable_checks = 2  # Require 2 consecutive stable size checks (reduced from 3)
                    # TODO: Research better approach - potentially wait indefinitely with reasonable max timeout
                    
                    while time.time() - stability_start < stability_timeout:
                        # Cross-platform file size check (stat -c for Linux, stat -f for macOS)
                        size_check = self.session_manager.execute_command(
                            session, "runscript", f"runscript -Raw=```if [ -f {evidence_path}/{collection_file} ]; then ls -la {evidence_path}/{collection_file} | awk '{{print $5}}'; else echo ''; fi```", is_admin=True
                        )
                        
                        if size_check and size_check.stdout.strip().isdigit():
                            current_size = int(size_check.stdout.strip())
                            
                            if last_size == current_size:
                                stable_count += 1
                                self.logger.info(f"File size stable: {current_size} bytes (check {stable_count}/{required_stable_checks})")
                                
                                if stable_count >= required_stable_checks:
                                    self.logger.info(f"UAC archive verified stable and ready: {current_size} bytes")
                                    print("[+] UAC archive verified and ready")
                                    return base_name
                            else:
                                stable_count = 0  # Reset if size changed
                                if last_size is not None:
                                    self.logger.info(f"File size changed: {last_size} -> {current_size} bytes, resetting stability check")
                            
                            last_size = current_size
                        else:
                            # File might not exist yet or stat failed, reset stability
                            stable_count = 0
                            last_size = None
                        
                        time.sleep(10)  # Check every 10 seconds
                    
                    # If we timeout on stability check, still return the file (it likely exists)
                    self.logger.warning(f"File stability timeout reached, proceeding with archive: {collection_file}")
                    print("[+] UAC archive found (stability timeout)")
                    return base_name
                
                # Archive not found yet, check if UAC process has finished
                # FIXED: UAC writes exit code to deploy directory where the script runs
                exit_code_check = self.session_manager.execute_command(
                    session, "runscript", f"runscript -Raw=```test -f {deploy_path}/uac_exit_code && cat {deploy_path}/uac_exit_code```", is_admin=True
                )
                
                # If UAC finished (exit code exists), but no archive yet, it might be creating the archive
                if exit_code_check and exit_code_check.stdout.strip().isdigit():
                    exit_code = int(exit_code_check.stdout.strip())
                    self.logger.info(f"UAC process completed with exit code: {exit_code}")
                    
                    if exit_code == 0:
                        # UAC finished successfully, now waiting for archive creation
                        print(f"\n[*] UAC process finished, waiting for archive creation...")
                        # Give it extra time to create the archive
                        archive_wait_start = time.time()
                        archive_timeout = 900  # 15 minutes for archiving (large collections need more time)
                        
                        while time.time() - archive_wait_start < archive_timeout:
                            ls_result = self.session_manager.execute_command(
                                session, "runscript", f"runscript -Raw=```ls -la {evidence_path}```", is_admin=True
                            )
                            
                            if ls_result:
                                # UAC creates files with pattern: uac-hostname-os-YYYYMMDDHHMMSS.tar.gz (no T separator)
                                pattern = rf"(uac-{hostname}-\w+-\d{{14}}\.tar\.gz)"
                                match = re.search(pattern, ls_result.stdout)
                                if match:
                                    collection_file = match.group(1)
                                    base_name = collection_file.replace('.tar.gz', '')
                                    self.logger.info(f"Archive created successfully: {collection_file}")
                                    print(f"\n[+] Archive created: {collection_file}")
                                    return base_name
                            
                            print(f"\r[*] Waiting for archive creation... {int(time.time() - archive_wait_start)}s", end="", flush=True)
                            time.sleep(10)
                        
                        self.logger.error("Archive creation timed out after 15 minutes")
                        print(f"\n[!] Archive creation timed out after 15 minutes")
                        return None
                    else:
                        self.logger.error(f"UAC completed with error exit code: {exit_code}")
                        print(f"\n[!] UAC completed with error (exit code: {exit_code})")
                        
                        # Check for specific EOF artifact error in the log
                        debug_log = self.session_manager.execute_command(
                            session, "runscript", f"runscript -Raw=```tail -n 50 {deploy_path}/uac_output.log 2>/dev/null | grep -E '__EOF__.*artifact not found'```", is_admin=True
                        )
                        
                        if debug_log and debug_log.stdout.strip():
                            self.logger.warning("Detected UAC EOF artifact validation error - this is a known YAML formatting issue")
                            self.logger.warning(f"EOF artifact error details: {debug_log.stdout.strip()}")
                            print("[!] UAC failed due to EOF artifact validation error (known YAML formatting issue)")
                            print("[*] This error indicates malformed YAML files in the UAC package")
                            print("[*] Consider rebuilding the UAC package or using a different profile")
                        
                        return None
                    
                        
                # Still running - log progress and check if we can see intermediate files
                minutes_passed = elapsed_seconds / 60
                
                # Look for UAC working directory for actual progress
                # UAC creates a temporary directory like uac-data.tmp
                uac_data_result = self.session_manager.execute_command(
                    session, "runscript", f"runscript -Raw=```find {evidence_path} -type f -name '*.yaml' 2>/dev/null | wc -l```", is_admin=True
                )
                
                if uac_data_result and uac_data_result.stdout.strip().isdigit():
                    file_count = int(uac_data_result.stdout.strip())
                else:
                    # Fallback to counting items in evidence directory
                    if ls_result and ls_result.stdout:
                        file_lines = [line for line in ls_result.stdout.split('\n') if line.strip() and not line.startswith('total') and not line.endswith('.') and not line.endswith('..')]  
                        file_count = len(file_lines)
                    else:
                        file_count = 0
                    
                # Update progress tracking if file count increased
                if file_count > last_file_count:
                    last_file_count = file_count
                    last_progress_time = time.time()
                
                # Show progress
                if file_count > 0:
                    self.logger.info(f"UAC still running... {minutes_passed:.1f} minutes elapsed ({file_count} artifacts collected so far)")
                    # Only print if we didn't already show real progress
                    if not (log_result and log_result.stdout.strip() and "[" in log_result.stdout.strip()):
                        print(f"[*] UAC still running... {minutes_passed:.1f} minutes elapsed ({file_count} artifacts collected)")
                else:
                    self.logger.info(f"UAC still running... {minutes_passed:.1f} minutes elapsed")
                    if not (log_result and log_result.stdout.strip() and "[" in log_result.stdout.strip()):
                        print(f"[*] UAC still running... {minutes_passed:.1f} minutes elapsed (initializing...)")
                
                # Wait before next check
                time.sleep(interval)
                
        except Exception as e:
            self.logger.error(f"Error monitoring UAC execution: {e}", exc_info=True)
            return None
            
    def upload_uac_results(self, host_info: HostInfo, collection_file: str, 
                          evidence_path: str = None, 
                          existing_session: Optional[RTRSession] = None) -> bool:
        """
        Upload UAC collection results to cloud storage
        
        Args:
            host_info: Target host information
            collection_file: Name of the collection file (without extension)
            evidence_path: Path where evidence is stored (defaults to config value)
            existing_session: Optional existing RTR session to reuse
            
        Returns:
            True if successful, False otherwise
        """
        # Use config value if evidence_path not provided
        if evidence_path is None:
            evidence_path = self.config.get_uac_setting("evidence_path")
            
        session_created = False
        try:
            # Use existing session if provided, otherwise create new one
            if existing_session:
                # Validate the existing session is still active
                try:
                    # Test the session with a simple command (with network resilience)
                    test_result = self._execute_with_retry(
                        existing_session, "runscript", "runscript -Raw=```echo 'session_test'```", is_admin=True, max_retries=2, backoff_base=1.5
                    )
                    if test_result and test_result.stdout and 'session_test' in test_result.stdout:
                        session = existing_session
                        self.logger.info("Reusing existing RTR session for upload")
                    else:
                        self.logger.warning("Existing session invalid, creating new session for upload")
                        session = self.session_manager.start_session(host_info.aid)
                        if not session:
                            self.logger.error("Failed to start new RTR session")
                            return False
                        session_created = True
                except Exception as e:
                    self.logger.warning(f"Session validation failed: {e}, creating new session for upload")
                    session = self.session_manager.start_session(host_info.aid)
                    if not session:
                        self.logger.error("Failed to start new RTR session")
                        return False
                    session_created = True
            else:
                session = self.session_manager.start_session(host_info.aid)
                if not session:
                    self.logger.error("Failed to start RTR session")
                    return False
                session_created = True
                
            # The actual file has .tar.gz extension
            actual_file = f"{collection_file}.tar.gz"
            full_path = f"{evidence_path}/{actual_file}"
            
            # Get actual file size using cross-platform method
            # FIXED: Use actual file size instead of estimate for accurate upload tracking
            size_cmd = f"runscript -Raw=```if [ -f {full_path} ]; then ls -la {full_path} | awk '{{print $5}}'; else echo '0'; fi```"
            size_result = self.session_manager.execute_command(
                session, "runscript", size_cmd, is_admin=True
            )
            
            if size_result and size_result.stdout.strip().isdigit():
                file_size = int(size_result.stdout.strip())
                size_mb = file_size / (1024 * 1024)
                self.logger.info(f"Actual file size: {file_size} bytes ({size_mb:.1f} MB)")
                print(f"[*] Proceeding with upload (file size: {size_mb:.1f} MB)")
            else:
                # Fallback to estimate if size check fails
                file_size = 350 * 1024 * 1024  # Estimate 350MB for typical UAC collection
                self.logger.warning(f"Could not determine actual file size, using estimate")
                print(f"[*] Proceeding with upload (estimated size: ~350 MB)")
            
            # Generate S3 upload URL using configuration
            bucket_name = self.config.get_s3_bucket()
            proxy_host = self.config.get_proxy_host()
            
            # Use simple filename like KAPE (no subdirectory path)
            # Use .7z extension since CrowdStrike RTR converts to 7z format
            s3_filename = f"{collection_file}.7z"
            
            url, key = self.cloud_storage.generate_upload_url(
                bucket_name,
                filename=s3_filename
            )
            
            if not url:
                self.logger.error("Failed to generate upload URL")
                return False
                
            # Replace S3 URL with proxy URL if proxy is enabled
            if self.config.is_proxy_enabled():
                proxied_url = url.replace(f"{bucket_name}.s3.amazonaws.com", proxy_host)
            else:
                proxied_url = url
            
            self.logger.info(f"Generated S3 upload URL for key: {s3_filename}")
            print(f"[*] Generated S3 upload URL for key: {s3_filename}")
            
            # Calculate estimated upload time based on file size 
            # Use realistic upload rate based on actual performance testing:
            # - Test showed 3.57 MB/s actual speed for 321MB file
            # - Using 2 MB/s as conservative baseline (allows for network variation)
            UPLOAD_RATE = self.config.get_file_setting("upload_rate") or 2000000  # 2 MB/s realistic conservative rate
            base_upload_time = file_size / UPLOAD_RATE
            
            # Dynamic timeout calculation based on file size
            if file_size < 1000000000:  # < 1GB: normal timeout
                safety_margin = 1.5
                buffer_time = 300  # 5 minutes
            elif file_size < 5000000000:  # 1-5GB: longer timeout
                safety_margin = 2.0
                buffer_time = 600  # 10 minutes
            else:  # >5GB: very long timeout with warning
                safety_margin = 2.5
                buffer_time = 1200  # 20 minutes
                self.logger.warning(f"Large file detected ({file_size / (1024*1024*1024):.1f}GB). Upload may take several hours.")
                print(f"[!] Large file detected ({file_size / (1024*1024*1024):.1f}GB). Upload may take several hours.")
                
            estimated_upload_time = int(base_upload_time * safety_margin) + buffer_time
            self.logger.info(f"Estimated upload time: {estimated_upload_time / 60:.1f} minutes for {file_size / (1024 * 1024):.1f} MB")
            print(f"[*] Estimated upload time: {estimated_upload_time / 60:.1f} minutes for {file_size / (1024 * 1024):.1f} MB")
            
            # For Unix systems, we'll use curl for upload
            platform = Platform(host_info.platform.lower())
            
            # Use curl with progress output and timeout (match KAPE approach - explicitly no Content-Type header)
            # FIXED: Use -T for file streaming instead of --data-binary to avoid memory issues
            upload_cmd = (
                f"runscript -Raw=```curl -X PUT -T '{full_path}' "
                f"-H 'Content-Type:' "
                f"--max-time {int(estimated_upload_time)} "
                f"--progress-bar "
                f"'{proxied_url}' 2>&1```"
            )
                
            # Add hosts file entries dynamically from configuration
            hosts_cmd = self.config.generate_hosts_command(platform="unix")
            
            if hosts_cmd:
                self.logger.info(f"Adding {len(self.config.get_host_entries())} host entries to /etc/hosts")
                self.session_manager.execute_command(
                    session, "runscript", hosts_cmd, is_admin=True
                )
            
            self.logger.info("Starting upload to S3...")
            print("[*] Starting upload to S3...")
            
            # Execute upload command with dynamic timeout
            # Since execute_command has hardcoded 2-min timeout, we need to work around it
            # by running the upload in background and monitoring it
            # FIXED: Use -T for file streaming instead of --data-binary to avoid memory issues
            background_upload_cmd = (
                f"runscript -Raw=```("
                f"curl -X PUT -T '{full_path}' "
                f"-H 'Content-Type:' "
                f"--max-time {int(estimated_upload_time)} "
                f"--connect-timeout 30 "
                f"--retry 3 "
                f"--retry-delay 5 "
                f"--progress-bar "
                f"--fail "
                f"'{proxied_url}' > {evidence_path}/upload.log 2>&1; "
                f"echo $? > {evidence_path}/upload_exit_code"
                f") & echo $! > {evidence_path}/upload.pid && echo 'Upload started in background'```"
            )
            
            # Start upload in background
            upload_start = self.session_manager.execute_command(
                session, "runscript", background_upload_cmd, is_admin=True
            )
            
            if not upload_start:
                self.logger.error("Failed to start upload process")
                return False
                
            # Monitor the upload progress
            start_time = time.time()
            last_pulse_time = time.time()
            pulse_interval = 120  # Pulse every 2 minutes to be safe (session timeout is 10 minutes)
            check_interval = 10  # Check every 10 seconds
            session_recreation_attempts = 0
            max_session_recreations = 3
            
            while True:
                elapsed = time.time() - start_time
                
                # Pulse session if needed to prevent timeout during long uploads
                time_since_last_pulse = time.time() - last_pulse_time
                if time_since_last_pulse >= pulse_interval:
                    if self.session_manager.pulse_session(session):
                        self.logger.debug(f"Session pulsed during upload after {time_since_last_pulse/60:.1f} minutes")
                        last_pulse_time = time.time()
                    else:
                        self.logger.warning("Failed to pulse session during upload - session may timeout")
                
                # Check upload progress from log file
                progress_result = self.session_manager.execute_command(
                    session, "runscript", 
                    f"runscript -Raw=```test -f {evidence_path}/upload.log && tail -1 {evidence_path}/upload.log | grep -o '[0-9]\\+\\.[0-9]%' | tail -1```",
                    is_admin=True
                )
                
                # Check if session expired (command failed)
                if progress_result is None:
                    self.logger.warning("Session appears to have expired during upload monitoring")
                    
                    # Try to recreate session
                    if session_recreation_attempts < max_session_recreations:
                        session_recreation_attempts += 1
                        self.logger.info(f"Attempting to recreate session (attempt {session_recreation_attempts}/{max_session_recreations})")
                        
                        # Close old session
                        if session:
                            try:
                                self.session_manager.end_session(session)
                            except:
                                pass
                        
                        # Create new session
                        new_session = self.session_manager.start_session(host_info.aid)
                        if new_session:
                            session = new_session
                            session_created = True
                            last_pulse_time = time.time()
                            self.logger.info("Successfully recreated RTR session")
                            continue  # Retry the loop with new session
                        else:
                            self.logger.error("Failed to recreate RTR session")
                            # Continue anyway - let S3 verification be the final check
                            break
                    else:
                        self.logger.error("Max session recreation attempts reached")
                        # Continue anyway - let S3 verification be the final check
                        break
                
                if progress_result and progress_result.stdout.strip():
                    progress_str = progress_result.stdout.strip()
                    try:
                        progress_pct = float(progress_str.rstrip('%'))
                        # Show progress every 10 seconds or at milestones
                        if int(elapsed) % 10 == 0 or progress_pct in [25.0, 50.0, 75.0, 100.0]:
                            print(f"[*] Upload progress: {progress_pct:.1f}% ({elapsed/60:.1f} minutes elapsed)")
                        
                        # Check if upload is complete
                        if progress_pct >= 100.0:
                            self.logger.info(f"Upload reached 100% completion in {elapsed/60:.1f} minutes")
                            print(f"[+] Upload reached 100% completion")
                            # Wait a short time for curl to finish cleanly
                            print("[*] Waiting 30 seconds for upload finalization...")
                            time.sleep(30)
                            
                            # Verify upload by checking S3 bucket
                            print("[*] Verifying upload in S3 bucket...")
                            if self._verify_s3_upload_success(bucket_name, s3_filename):
                                self.logger.info(f"Successfully uploaded and verified {actual_file} to S3 in {(elapsed+30)/60:.1f} minutes")
                                print(f"[+] Successfully uploaded and verified {actual_file} to S3 in {(elapsed+30)/60:.1f} minutes")
                            else:
                                self.logger.warning(f"Upload completed but S3 verification failed for {actual_file}")
                                print(f"[!] Upload completed but S3 verification failed for {actual_file}")
                            break
                    except ValueError:
                        pass
                
                # Also check exit code as fallback
                exit_code_result = self.session_manager.execute_command(
                    session, "runscript", 
                    f"runscript -Raw=```test -f {evidence_path}/upload_exit_code && cat {evidence_path}/upload_exit_code```",
                    is_admin=True
                )
                
                if exit_code_result and exit_code_result.stdout.strip().isdigit():
                    exit_code = int(exit_code_result.stdout.strip())
                    if exit_code == 0:
                        # Verify upload by checking S3 bucket
                        print("[*] Verifying upload in S3 bucket...")
                        if self._verify_s3_upload_success(bucket_name, s3_filename):
                            self.logger.info(f"Successfully uploaded and verified {actual_file} to S3 in {elapsed/60:.1f} minutes")
                            print(f"[+] Successfully uploaded and verified {actual_file} to S3 in {elapsed/60:.1f} minutes")
                        else:
                            self.logger.warning(f"Upload completed but S3 verification failed for {actual_file}")
                            print(f"[!] Upload completed but S3 verification failed for {actual_file}")
                        break
                    else:
                        # Get error details from log
                        log_result = self.session_manager.execute_command(
                            session, "runscript", 
                            f"runscript -Raw=```tail -20 {evidence_path}/upload.log```",
                            is_admin=True
                        )
                        error_msg = log_result.stdout if log_result else "Unknown error"
                        self.logger.warning(f"Upload process reported error (exit code {exit_code}): {error_msg}")
                        # Don't return False here - let S3 verification be the final arbiter
                        break  # Exit monitoring loop and proceed to final verification
                
                # Check if upload is still running
                pid_result = self.session_manager.execute_command(
                    session, "runscript", 
                    f"runscript -Raw=```test -f {evidence_path}/upload.pid && cat {evidence_path}/upload.pid```",
                    is_admin=True
                )
                
                if pid_result and pid_result.stdout.strip().isdigit():
                    pid = pid_result.stdout.strip()
                    # Check if process is still alive
                    proc_check = self.session_manager.execute_command(
                        session, "runscript", 
                        f"runscript -Raw=```ps -p {pid} | grep -v PID | wc -l```",
                        is_admin=True
                    )
                    
                    if proc_check and proc_check.stdout.strip() == "0":
                        # Process died - check if exit code was written
                        time.sleep(2)  # Give a moment for exit code to be written
                        exit_code_result = self.session_manager.execute_command(
                            session, "runscript", 
                            f"runscript -Raw=```test -f {evidence_path}/upload_exit_code && cat {evidence_path}/upload_exit_code```",
                            is_admin=True
                        )
                        
                        if exit_code_result and exit_code_result.stdout.strip().isdigit():
                            exit_code = int(exit_code_result.stdout.strip())
                            if exit_code == 0:
                                self.logger.info("Upload completed successfully (process finished)")
                                print("[+] Upload completed successfully")
                                break
                            else:
                                # Get error details from log
                                log_result = self.session_manager.execute_command(
                                    session, "runscript", 
                                    f"runscript -Raw=```tail -20 {evidence_path}/upload.log```",
                                    is_admin=True
                                )
                                error_msg = log_result.stdout if log_result else "Unknown error"
                                self.logger.warning(f"Upload process reported error (exit code {exit_code}): {error_msg}")
                                # Don't return False here - let S3 verification be the final arbiter
                                break  # Exit monitoring loop and proceed to final verification
                        else:
                            # Process died without writing exit code - log as warning, don't fail yet
                            self.logger.warning("Upload process terminated without exit code (possible race condition)")
                            # Get last lines from upload log for debugging
                            log_result = self.session_manager.execute_command(
                                session, "runscript", 
                                f"runscript -Raw=```tail -10 {evidence_path}/upload.log```",
                                is_admin=True
                            )
                            if log_result and log_result.stdout:
                                self.logger.warning(f"Upload log for debugging: {log_result.stdout}")
                            # Don't return False here - let S3 verification be the final arbiter
                            break  # Exit monitoring loop and proceed to S3 verification
                
                # Check for timeout
                if elapsed > estimated_upload_time + 60:  # Give extra minute buffer
                    self.logger.warning(f"Upload monitoring exceeded estimated time of {estimated_upload_time/60:.1f} minutes")
                    # Try to kill the curl process
                    if pid_result and pid_result.stdout.strip().isdigit():
                        self.session_manager.execute_command(
                            session, "runscript", 
                            f"runscript -Raw=```kill {pid_result.stdout.strip()}```",
                            is_admin=True
                        )
                    # Don't return False here - let S3 verification be the final arbiter
                    break  # Exit monitoring loop and proceed to final verification
                
                # Log progress
                if int(elapsed) % 30 == 0:  # Every 30 seconds
                    self.logger.info(f"Upload in progress... {elapsed/60:.1f} minutes elapsed")
                    print(f"[*] Upload in progress... {elapsed/60:.1f} minutes elapsed")
                
                time.sleep(check_interval)
            
            # NOTE: The static wait time below is now SKIPPED when we detect 100% upload completion
            # We only fall through to this code if the upload monitoring loop exits via timeout or error
            # In those cases, we still want to wait before cleanup to avoid deleting files prematurely
            
            # Check if we exited the loop due to session issues or timeout
            # In either case, skip the long wait and go straight to S3 verification
            if elapsed > estimated_upload_time + 60 or session_recreation_attempts > 0:
                if elapsed > estimated_upload_time + 60:
                    self.logger.warning("Upload monitoring timed out")
                else:
                    self.logger.warning("Upload monitoring stopped due to session issues")
                
                # Wait a short time then check S3 directly
                wait_time = 60  # Just 1 minute instead of 5+ minutes
                self.logger.info(f"Waiting {wait_time} seconds before S3 verification...")
                print(f"[*] Waiting {wait_time} seconds before checking S3...")
                time.sleep(wait_time)
            
            # FINAL S3 VERIFICATION - This is the authoritative check for upload success
            print("[*] Performing final S3 verification...")
            if self._verify_s3_upload_success(bucket_name, s3_filename):
                self.logger.info(f"✅ Upload verification successful: {actual_file} confirmed in S3")
                print(f"[+] Upload verification successful: {actual_file} confirmed in S3")
                upload_success = True
            else:
                self.logger.error(f"❌ Upload verification failed: {actual_file} not found in S3")
                print(f"[!] Upload verification failed: {actual_file} not found in S3")
                upload_success = False
            
            # Perform workspace cleanup after successful upload
            if upload_success:
                self._cleanup_workspace_after_operation(session, host_info, "upload")
            
            return upload_success
            
        except Exception as e:
            self.logger.error(f"Error uploading UAC results: {e}", exc_info=True)
            return False
        finally:
            # Only close session if we created it (don't close reused sessions)
            if session_created and session:
                try:
                    self.session_manager.end_session(session)
                    self.logger.debug("RTR session closed after upload")
                except Exception as e:
                    self.logger.warning(f"Failed to close RTR session after upload: {e}")
    
    def _verify_s3_upload_success(self, bucket_name: str, object_key: str) -> bool:
        """
        Verify that the file was successfully uploaded to S3 by checking bucket contents
        
        Args:
            bucket_name: S3 bucket name
            object_key: S3 object key (filename)
            
        Returns:
            True if file exists in S3, False otherwise
        """
        try:
            self.logger.info(f"Verifying S3 upload: s3://{bucket_name}/{object_key}")
            
            # Use cloud storage manager to verify upload (no size check - just existence)
            verification_result = self.cloud_storage.verify_s3_upload(bucket_name, object_key)
            
            if verification_result:
                self.logger.info("S3 upload verification successful")
                return True
            else:
                self.logger.error("S3 upload verification failed")
                
                # Try to get object info for debugging
                object_info = self.cloud_storage.get_s3_object_info(bucket_name, object_key)
                if object_info:
                    self.logger.info(f"S3 object found with size: {object_info['size']} bytes")
                    return True  # File exists, that's sufficient
                else:
                    self.logger.error("S3 object not found in bucket")
                return False
                
        except Exception as e:
            self.logger.error(f"Error during S3 verification: {e}", exc_info=True)
            return False
    
    def download_uac_results(self, host_info: HostInfo, collection_file: str,
                            evidence_path: str = None,
                            existing_session: Optional[RTRSession] = None) -> bool:
        """
        Download UAC collection results to current working directory
        
        Args:
            host_info: Target host information
            collection_file: Name of the collection file
            evidence_path: Path to evidence directory on remote host (defaults to config value)
            existing_session: Optional existing RTR session to reuse
            
        Returns:
            True if successful, False otherwise
        """
        # Use config value if evidence_path not provided
        if evidence_path is None:
            evidence_path = self.config.get_uac_setting("evidence_path")
            
        session = None
        session_created = False
        
        try:
            # Use existing session or create new one
            if existing_session:
                session = existing_session
                self.logger.debug("Reusing existing RTR session for download")
            else:
                session = self.session_manager.start_session(host_info.aid)
                session_created = True
                if not session:
                    self.logger.error("Failed to start RTR session for download")
                    return False
                    
            # Add .tar.gz extension if not present (collection_file comes without extension)
            if not collection_file.endswith('.tar.gz'):
                actual_file = f"{collection_file}.tar.gz"
            else:
                actual_file = collection_file
                
            # Get the actual filename
            ls_result = self.session_manager.execute_command(
                session, "runscript",
                f"runscript -Raw=```ls -la {evidence_path}/{actual_file} 2>/dev/null || echo 'FILE_NOT_FOUND'```",
                is_admin=True
            )
            
            if not ls_result or "FILE_NOT_FOUND" in ls_result.stdout:
                self.logger.error(f"Collection file not found: {evidence_path}/{actual_file}")
                print(f"[!] Collection file not found: {evidence_path}/{actual_file}")
                return False
                
            # Extract file size from ls output
            expected_file_size = 0
            try:
                ls_lines = ls_result.stdout.strip().split('\n')
                for line in ls_lines:
                    if actual_file in line:
                        parts = line.split()
                        if len(parts) >= 5:
                            expected_file_size = int(parts[4])  # 5th column is file size
                            break
                            
                if expected_file_size > 0:
                    self.logger.info(f"Remote file size: {expected_file_size:,} bytes ({expected_file_size/1024/1024:.1f} MB)")
                    print(f"[*] Remote file size: {expected_file_size:,} bytes ({expected_file_size/1024/1024:.1f} MB)")
                else:
                    self.logger.warning("Could not determine remote file size")
                    
            except (ValueError, IndexError) as e:
                self.logger.warning(f"Could not parse file size: {e}")
                print("[*] Could not determine file size")
                
            # Use current working directory instead of Downloads
            from pathlib import Path
            import os
            current_dir = Path(os.getcwd())
            # Save with .7z extension since CrowdStrike RTR converts to 7z format
            local_filename = actual_file.replace('.tar.gz', '.7z')
            local_file_path = current_dir / local_filename
            
            # Check if local file already exists and remove it
            if local_file_path.exists():
                self.logger.info(f"Removing existing local file: {local_file_path}")
                print(f"[*] Removing existing local file: {local_file_path}")
                local_file_path.unlink()
            
            # Use the file manager to download the file
            self.logger.info(f"Downloading {actual_file} to {local_file_path}")
            print(f"[*] Downloading {actual_file} to {local_file_path}")
            print(f"[*] This may take several minutes for large files...")
            
            download_success = self.file_manager.download_file(
                session=session,
                device_id=host_info.aid,
                remote_path=f"{evidence_path}/{actual_file}",
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
                    self._cleanup_workspace_after_operation(session, host_info, "download")
                    
                    return True
                else:
                    self.logger.error(f"Downloaded file not found at {local_file_path}")
                    print(f"[!] Downloaded file not found at {local_file_path}")
                    return False
            else:
                self.logger.error(f"❌ Failed to download {actual_file}")
                print(f"[!] Failed to download {actual_file}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error downloading UAC results: {e}", exc_info=True)
            print(f"[!] Error downloading UAC results: {e}")
            return False
            
        finally:
            # Only close session if we created it (don't close reused sessions)
            if session_created and session:
                try:
                    self.session_manager.end_session(session)
                    self.logger.debug("RTR session closed after download")
                except Exception as e:
                    self.logger.warning(f"Failed to close RTR session after download: {e}")
                    
    def _cleanup_workspace_after_operation(self, session: RTRSession, host_info: HostInfo, 
                                          operation_type: str) -> None:
        """
        Perform workspace cleanup after successful upload or download
        CRITICAL: Must cd away from the directory first in case RTR session is holding it open!
        
        Args:
            session: Active RTR session
            host_info: Target host information
            operation_type: Type of operation ("upload" or "download")
        """
        try:
            self.logger.info(f"Performing post-{operation_type} workspace cleanup...")
            
            platform = Platform(host_info.platform.lower())
            
            # CRITICAL: Change directory away from workspace first!
            # The RTR session might be in the workspace directory which would prevent cleanup
            if platform == Platform.WINDOWS:
                workspace_path = self.config.get_workspace_path(Platform.WINDOWS)
                # Change to root directory to release any potential handle
                self.logger.info("Changing directory away from workspace before cleanup...")
                self.session_manager.execute_command(session, "cd", "cd C:\\", is_admin=True)
                
                # Now we can remove the directory
                cleanup_cmd = f"runscript -Raw=```if (Test-Path '{workspace_path}') {{ Remove-Item -Path '{workspace_path}' -Recurse -Force -ErrorAction Stop }}```"
            else:
                workspace_path = self.config.get_uac_setting("base_path")
                # Change to root directory to release any potential handle
                self.logger.info("Changing directory away from workspace before cleanup...")
                self.session_manager.execute_command(session, "cd", "cd /", is_admin=True)
                
                # Unix cleanup - simple and direct
                cleanup_cmd = f"runscript -Raw=```rm -rf {workspace_path} 2>/dev/null || true```"
            
            # Small delay to ensure cd completes
            time.sleep(2)
            
            self.logger.info(f"Cleaning workspace directory: {workspace_path}")
            result = self.session_manager.execute_command(session, "runscript", cleanup_cmd, is_admin=True)
            
            if result:
                self.logger.info(f"✅ Post-{operation_type} workspace cleanup completed")
                print(f"[+] Post-{operation_type} workspace cleanup completed")
            else:
                self.logger.warning("Workspace cleanup command had no result (may have already been cleaned)")
                    
        except Exception as e:
            self.logger.error(f"Error during post-{operation_type} cleanup: {e}", exc_info=True)
            print(f"[!] Error during post-{operation_type} cleanup: {e}")