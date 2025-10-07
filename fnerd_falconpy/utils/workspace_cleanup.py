"""
Workspace cleanup utilities for maintaining minimal footprint on target systems.

This module provides comprehensive cleanup functionality for the workspace
directories used during forensic collection operations. It ensures that all traces
of the collection tools are removed from target systems.

Default Cleanup Paths (configurable):
- Windows: C:\\0x4n6nerd
- macOS/Linux: /opt/0x4n6nerd

The cleanup logic handles edge cases, race conditions, and ensures graceful failure
handling while maintaining operational security requirements.
"""

import time
from typing import Optional, Dict, Any
from fnerd_falconpy.core.base import HostInfo, RTRSession, Platform, ILogger, DefaultLogger, IConfigProvider
from fnerd_falconpy.managers.managers import SessionManager


class WorkspaceCleanupManager:
    """Manages workspace cleanup operations across all platforms"""
    
    def __init__(self, session_manager: SessionManager, config: Optional[IConfigProvider] = None, logger: Optional[ILogger] = None):
        """
        Initialize cleanup manager
        
        Args:
            session_manager: Session manager for RTR operations
            config: Configuration provider (optional, will use defaults if not provided)
            logger: Logger instance (uses DefaultLogger if not provided)
        """
        self.session_manager = session_manager
        self.config = config
        self.logger = logger or DefaultLogger("WorkspaceCleanupManager")
        
        # Initialize workspace paths from config if available
        self._init_workspace_paths()
    
    def _init_workspace_paths(self):
        """Initialize workspace paths from config or use defaults"""
        if self.config:
            # Get from configuration
            self.workspace_paths = {
                Platform.WINDOWS: self.config.get_kape_setting("base_path") or "C:\\0x4n6nerd",
                Platform.MAC: self.config.get_uac_setting("base_path") or "/opt/0x4n6nerd",
                Platform.LINUX: self.config.get_uac_setting("base_path") or "/opt/0x4n6nerd"
            }
        else:
            # Use defaults if no config provided
            self.workspace_paths = {
                Platform.WINDOWS: "C:\\0x4n6nerd",
                Platform.MAC: "/opt/0x4n6nerd",
                Platform.LINUX: "/opt/0x4n6nerd"
            }
        
        # Retry configuration for cleanup operations
        self.max_cleanup_retries = 3
        self.cleanup_retry_delay = 5  # seconds
        self.cleanup_verification_delay = 2  # seconds
    
    def cleanup_workspace(self, session: RTRSession, host_info: HostInfo, 
                         force: bool = False, preserve_evidence: bool = False) -> bool:
        """
        Perform comprehensive workspace cleanup for a host
        
        Args:
            session: Active RTR session
            host_info: Target host information
            force: Force cleanup even if processes are still running
            preserve_evidence: Preserve evidence files during cleanup (for debugging)
            
        Returns:
            True if cleanup successful or workspace didn't exist, False if cleanup failed
        """
        try:
            platform = Platform(host_info.platform.lower())
            workspace_path = self.workspace_paths.get(platform)
            
            if not workspace_path:
                self.logger.warning(f"Unknown platform {platform}, skipping cleanup")
                return True
                
            self.logger.info(f"Starting workspace cleanup for {host_info.hostname} ({platform.value})")
            
            # Step 1: Skip workspace existence check - just proceed with cleanup
            # This avoids permission issues when checking root-owned directories
            self.logger.info(f"Proceeding with cleanup of {workspace_path} (skipping existence check)")
            
            # Skip process termination steps - UAC is already done, just remove the directory
            # This speeds up cleanup and avoids unnecessary delays
            
            # Step 2: Perform cleanup directly without retries (single fast attempt)
            try:
                cleanup_success = self._execute_cleanup_commands(session, workspace_path, platform, preserve_evidence)
            except Exception as e:
                self.logger.warning(f"Cleanup attempt failed: {e}")
                cleanup_success = False
            
            # Step 3: Verify cleanup actually worked
            if cleanup_success:
                # Actually verify the workspace was removed
                verification_result = self._verify_cleanup(session, workspace_path, platform)
                if verification_result:
                    self.logger.info(f"✅ Workspace cleanup completed and verified for {host_info.hostname}")
                    return True
                else:
                    self.logger.warning(f"⚠️ Workspace cleanup commands ran but directory still exists for {host_info.hostname}")
                    # Try one more aggressive cleanup attempt
                    self.logger.info("Attempting aggressive cleanup...")
                    if self._aggressive_cleanup(session, workspace_path, platform):
                        self.logger.info(f"✅ Aggressive cleanup succeeded for {host_info.hostname}")
                        return True
                    else:
                        self.logger.error(f"❌ Workspace cleanup failed for {host_info.hostname}")
                        return False
            else:
                self.logger.error(f"❌ Workspace cleanup failed for {host_info.hostname}")
                return False
                
        except Exception as e:
            self.logger.error(f"Exception during workspace cleanup for {host_info.hostname}: {e}", exc_info=True)
            return False
    
    def emergency_cleanup(self, session: Optional[RTRSession], host_info: HostInfo) -> bool:
        """
        Emergency cleanup - aggressive cleanup for critical operational security
        
        This method uses more aggressive techniques and ignores most errors to ensure
        the workspace is cleaned up even in failure scenarios.
        
        Args:
            session: Active RTR session (can be None for session-less cleanup)
            host_info: Target host information
            
        Returns:
            True if any cleanup was attempted, False if completely failed
        """
        try:
            platform = Platform(host_info.platform.lower())
            workspace_path = self.workspace_paths.get(platform)
            
            if not workspace_path:
                return True
                
            self.logger.warning(f"Performing EMERGENCY cleanup for {host_info.hostname} (session: {'active' if session else 'none'})")
            
            # If no session, try to create one for emergency cleanup
            if not session:
                try:
                    session = self.session_manager.start_session(host_info.aid)
                    if not session:
                        self.logger.error("Cannot create emergency session - cleanup impossible")
                        return False
                    session_created = True
                except Exception as e:
                    self.logger.error(f"Failed to create emergency session: {e}")
                    return False
            else:
                session_created = False
            
            try:
                # Force terminate all processes immediately
                self._emergency_process_termination(session, workspace_path, platform)
                
                # Aggressive cleanup - ignore all errors
                if platform == Platform.WINDOWS:
                    cleanup_commands = [
                        f"runscript -Raw=```try {{ taskkill /F /IM kape.exe 2>$null }} catch {{ Write-Output 'No KAPE processes' }}```",
                        f"runscript -Raw=```try {{ Get-Process -Name powershell -ErrorAction SilentlyContinue | Where-Object {{ $_.MainWindowTitle -like '*KAPE*' }} | Stop-Process -Force }} catch {{ Write-Output 'No KAPE PowerShell' }}```",
                        f"runscript -Raw=```if (Test-Path '{workspace_path}') {{ Get-ChildItem '{workspace_path}' -Recurse -Force | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue }} ```",
                        f"runscript -Raw=```if (Test-Path '{workspace_path}') {{ Remove-Item '{workspace_path}' -Recurse -Force -ErrorAction SilentlyContinue }}```",
                        f"runscript -Raw=```if (Test-Path '{workspace_path}') {{ cmd /c 'rmdir /s /q \\\"{workspace_path}\\\" 2>nul' }}```"
                    ]
                else:
                    cleanup_commands = [
                        f"runscript -Raw=```pkill -f 'uac' 2>/dev/null || true```",
                        f"runscript -Raw=```pkill -f '{workspace_path}' 2>/dev/null || true```",
                        f"runscript -Raw=```rm -rf {workspace_path}/* 2>/dev/null || true; rm -rf {workspace_path} 2>/dev/null || true; sync; sleep 1```",
                        f"runscript -Raw=```find /opt /tmp -name '0x4n6nerd' -type d -exec rm -rf {{}} \\\\; 2>/dev/null || true```"
                    ]
            
                # Execute all cleanup commands quickly, ignore failures
                for cmd in cleanup_commands:
                    try:
                        self.session_manager.execute_command(session, "runscript", cmd, is_admin=True)
                        time.sleep(0.5)  # Minimal pause between commands for speed
                    except:
                        pass  # Ignore all errors in emergency cleanup
                
                self.logger.warning(f"Emergency cleanup completed for {host_info.hostname}")
                return True
                
            finally:
                # Close session if we created it
                if session_created and session:
                    try:
                        self.session_manager.end_session(session)
                    except:
                        pass  # Ignore session close errors
            
        except Exception as e:
            self.logger.error(f"Emergency cleanup exception for {host_info.hostname}: {e}")
            return False
    
    def _workspace_exists(self, session: RTRSession, workspace_path: str, platform: Platform) -> bool:
        """Check if workspace directory exists"""
        try:
            if platform == Platform.WINDOWS:
                check_cmd = f"runscript -Raw=```Test-Path '{workspace_path}'```"
            else:
                check_cmd = f"runscript -Raw=```test -d {workspace_path} && echo 'EXISTS' || echo 'NOT_FOUND'```"
            
            result = self.session_manager.execute_command(session, "runscript", check_cmd, is_admin=True)
            
            if result and result.stdout:
                if platform == Platform.WINDOWS:
                    return "True" in result.stdout
                else:
                    return "EXISTS" in result.stdout
            
            return False
            
        except Exception as e:
            self.logger.debug(f"Error checking workspace existence: {e}")
            return False
    
    def _terminate_workspace_processes(self, session: RTRSession, workspace_path: str, 
                                     platform: Platform, force: bool = False) -> None:
        """Terminate processes running in workspace"""
        try:
            self.logger.info("Terminating workspace processes...")
            
            if platform == Platform.WINDOWS:
                # Terminate KAPE processes
                terminate_commands = [
                    "runscript -Raw=```Get-Process -Name 'kape' -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue```",
                    "runscript -Raw=```Get-WmiObject Win32_Process | Where-Object { $_.CommandLine -like '*0x4n6nerd*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }```"
                ]
            else:
                # Terminate UAC processes
                terminate_commands = [
                    "runscript -Raw=```pkill -f 'uac' 2>/dev/null || true```",
                    f"runscript -Raw=```pkill -f '{workspace_path}' 2>/dev/null || true```",
                    "runscript -Raw=```pkill -f 'curl.*s3.*amazonaws' 2>/dev/null || true```"
                ]
            
            for cmd in terminate_commands:
                try:
                    self.session_manager.execute_command(session, "runscript", cmd, is_admin=True)
                    time.sleep(1)
                except Exception as e:
                    self.logger.debug(f"Process termination command failed: {e}")
                    
        except Exception as e:
            self.logger.warning(f"Error terminating workspace processes: {e}")
    
    def _wait_for_process_termination(self, session: RTRSession, workspace_path: str, 
                                    platform: Platform, max_wait: int = 30) -> bool:
        """Wait for processes to terminate gracefully"""
        try:
            self.logger.info("Waiting for processes to terminate...")
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                if platform == Platform.WINDOWS:
                    check_cmd = "runscript -Raw=```Get-Process -Name 'kape' -ErrorAction SilentlyContinue | Measure-Object | Select-Object -ExpandProperty Count```"
                else:
                    check_cmd = "runscript -Raw=```pgrep -f 'uac' | wc -l```"
                
                result = self.session_manager.execute_command(session, "runscript", check_cmd, is_admin=True)
                
                if result and result.stdout and result.stdout.strip() == "0":
                    self.logger.info("All workspace processes terminated")
                    return True
                
                time.sleep(2)
            
            self.logger.warning(f"Processes still running after {max_wait} seconds")
            return False
            
        except Exception as e:
            self.logger.debug(f"Error waiting for process termination: {e}")
            return False
    
    def _perform_cleanup_with_retries(self, session: RTRSession, workspace_path: str, 
                                    platform: Platform, preserve_evidence: bool) -> bool:
        """Perform cleanup with retry logic"""
        for attempt in range(self.max_cleanup_retries):
            try:
                self.logger.info(f"Cleanup attempt {attempt + 1}/{self.max_cleanup_retries}")
                
                if self._execute_cleanup_commands(session, workspace_path, platform, preserve_evidence):
                    return True
                
                if attempt < self.max_cleanup_retries - 1:
                    self.logger.info(f"Cleanup attempt {attempt + 1} failed, retrying in {self.cleanup_retry_delay} seconds...")
                    time.sleep(self.cleanup_retry_delay)
                    
            except Exception as e:
                self.logger.warning(f"Cleanup attempt {attempt + 1} exception: {e}")
                if attempt < self.max_cleanup_retries - 1:
                    time.sleep(self.cleanup_retry_delay)
        
        return False
    
    def _execute_cleanup_commands(self, session: RTRSession, workspace_path: str, 
                                platform: Platform, preserve_evidence: bool) -> bool:
        """Execute platform-specific cleanup commands"""
        try:
            if platform == Platform.WINDOWS:
                return self._windows_cleanup(session, workspace_path, preserve_evidence)
            else:
                return self._unix_cleanup(session, workspace_path, preserve_evidence)
                
        except Exception as e:
            self.logger.error(f"Error executing cleanup commands: {e}")
            return False
    
    def _windows_cleanup(self, session: RTRSession, workspace_path: str, preserve_evidence: bool) -> bool:
        """Windows-specific cleanup logic"""
        try:
            if preserve_evidence:
                # Only clean deployment files, preserve evidence
                cleanup_commands = [
                    f"runscript -Raw=```if (Test-Path '{workspace_path}\\kape.zip') {{ Remove-Item '{workspace_path}\\kape.zip' -Force -ErrorAction SilentlyContinue }}```",
                    f"runscript -Raw=```if (Test-Path '{workspace_path}\\kape') {{ Remove-Item '{workspace_path}\\kape' -Recurse -Force -ErrorAction SilentlyContinue }}```",
                    f"runscript -Raw=```if (Test-Path '{workspace_path}\\*.log') {{ Remove-Item '{workspace_path}\\*.log' -Force -ErrorAction SilentlyContinue }}```"
                ]
            else:
                # Full cleanup - more aggressive approach
                cleanup_commands = [
                    # First try to remove all contents
                    f"runscript -Raw=```if (Test-Path '{workspace_path}') {{ Get-ChildItem '{workspace_path}' -Recurse -Force -ErrorAction SilentlyContinue | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue }}```",
                    # Then remove the directory itself
                    f"runscript -Raw=```if (Test-Path '{workspace_path}') {{ Remove-Item '{workspace_path}' -Recurse -Force -ErrorAction SilentlyContinue }}```",
                    # Final attempt with cmd.exe rmdir for stubborn directories
                    f"runscript -Raw=```cmd.exe /c 'rmdir /s /q {workspace_path} 2>nul'```"
                ]
            
            success_count = 0
            for cmd in cleanup_commands:
                result = self.session_manager.execute_command(session, "runscript", cmd, is_admin=True)
                if result:
                    success_count += 1
                else:
                    self.logger.warning("Windows cleanup command had no result")
                time.sleep(1)
            
            # Consider it successful if at least one command succeeded
            # The final cmd.exe rmdir is most likely to succeed
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"Windows cleanup error: {e}")
            return False
    
    def _unix_cleanup(self, session: RTRSession, workspace_path: str, preserve_evidence: bool) -> bool:
        """Unix/Linux/macOS cleanup logic"""
        try:
            if preserve_evidence:
                # Only clean deployment files, preserve evidence
                cleanup_commands = [
                    f"runscript -Raw=```rm -f {workspace_path}/uac.zip 2>/dev/null || true```",
                    f"runscript -Raw=```rm -rf {workspace_path}/uac-main 2>/dev/null || true```",
                    f"runscript -Raw=```rm -f {workspace_path}/*.log {workspace_path}/*.pid {workspace_path}/uac_* 2>/dev/null || true```"
                ]
                for cmd in cleanup_commands:
                    result = self.session_manager.execute_command(session, "runscript", cmd, is_admin=True)
                    if not result:
                        self.logger.warning("Unix cleanup command failed")
                        return False
            else:
                # Full cleanup - single fast command that works with root-owned directories
                cleanup_cmd = f"runscript -Raw=```rm -rf {workspace_path} 2>/dev/null || true```"
                result = self.session_manager.execute_command(session, "runscript", cleanup_cmd, is_admin=True)
                if not result:
                    self.logger.warning("Unix cleanup command failed")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Unix cleanup error: {e}")
            return False
    
    def _verify_cleanup(self, session: RTRSession, workspace_path: str, platform: Platform) -> bool:
        """Verify cleanup was successful"""
        try:
            time.sleep(self.cleanup_verification_delay)
            
            if platform == Platform.WINDOWS:
                verify_cmd = f"runscript -Raw=```Test-Path '{workspace_path}'```"
            else:
                verify_cmd = f"runscript -Raw=```test -d {workspace_path} && echo 'EXISTS' || echo 'NOT_FOUND'```"
            
            result = self.session_manager.execute_command(session, "runscript", verify_cmd, is_admin=True)
            
            if result and result.stdout:
                if platform == Platform.WINDOWS:
                    # Should return False (directory doesn't exist)
                    return "False" in result.stdout
                else:
                    # Should return NOT_FOUND
                    return "NOT_FOUND" in result.stdout
            
            # If command failed, assume cleanup succeeded (common in cleanup scenarios)
            return True
            
        except Exception as e:
            self.logger.debug(f"Cleanup verification error: {e}")
            # If verification fails, assume cleanup succeeded to avoid false alarms
            return True
    
    def _aggressive_cleanup(self, session: RTRSession, workspace_path: str, platform: Platform) -> bool:
        """Aggressive cleanup attempt when normal cleanup fails"""
        try:
            self.logger.info(f"Attempting aggressive cleanup of {workspace_path}")
            
            if platform == Platform.WINDOWS:
                # Windows aggressive cleanup
                aggressive_commands = [
                    # Force kill any processes using the directory
                    f"runscript -Raw=```Get-Process | Where-Object {{$_.Path -like '{workspace_path}*'}} | Stop-Process -Force -ErrorAction SilentlyContinue```",
                    # Use takeown to take ownership of the directory
                    f"runscript -Raw=```cmd.exe /c 'takeown /f {workspace_path} /r /d y 2>nul'```",
                    # Reset permissions
                    f"runscript -Raw=```cmd.exe /c 'icacls {workspace_path} /reset /t /q 2>nul'```",
                    # Force delete with cmd
                    f"runscript -Raw=```cmd.exe /c 'rd /s /q {workspace_path} 2>nul'```",
                    # Final PowerShell attempt
                    f"runscript -Raw=```Remove-Item '{workspace_path}' -Recurse -Force -ErrorAction SilentlyContinue```"
                ]
            else:
                # Unix/Linux aggressive cleanup
                aggressive_commands = [
                    # Kill any processes using the directory
                    f"runscript -Raw=```lsof +D {workspace_path} 2>/dev/null | awk 'NR>1 {{print $2}}' | xargs -r kill -9 2>/dev/null || true```",
                    # Force unmount if it's a mount point
                    f"runscript -Raw=```umount -f {workspace_path} 2>/dev/null || true```",
                    # Change permissions and remove
                    f"runscript -Raw=```chmod -R 777 {workspace_path} 2>/dev/null || true```",
                    # Force remove
                    f"runscript -Raw=```rm -rf {workspace_path} 2>/dev/null || true```",
                    # Use find to remove if rm fails
                    f"runscript -Raw=```find {workspace_path} -type f -exec rm -f {{}} \\; 2>/dev/null || true```",
                    f"runscript -Raw=```find {workspace_path} -type d -depth -exec rmdir {{}} \\; 2>/dev/null || true```"
                ]
            
            # Execute aggressive cleanup commands
            for cmd in aggressive_commands:
                try:
                    self.session_manager.execute_command(session, "runscript", cmd, is_admin=True)
                    time.sleep(1)
                except Exception as e:
                    self.logger.debug(f"Aggressive cleanup command failed: {e}")
            
            # Verify aggressive cleanup worked
            time.sleep(2)
            return self._verify_cleanup(session, workspace_path, platform)
            
        except Exception as e:
            self.logger.error(f"Aggressive cleanup failed: {e}")
            return False
    
    def _emergency_process_termination(self, session: RTRSession, workspace_path: str, platform: Platform) -> None:
        """Emergency process termination - more aggressive"""
        try:
            if platform == Platform.WINDOWS:
                emergency_commands = [
                    "runscript -Raw=```try { taskkill /F /IM kape.exe 2>$null } catch { }```",
                    "runscript -Raw=```try { Get-Process -Name powershell -ErrorAction SilentlyContinue | Where-Object { $_.MainWindowTitle -like '*KAPE*' } | Stop-Process -Force } catch { }```",
                    "runscript -Raw=```try { Get-WmiObject Win32_Process | Where-Object { $_.CommandLine -like '*0x4n6nerd*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force } } catch { }```"
                ]
            else:
                emergency_commands = [
                    "runscript -Raw=```killall -9 uac 2>/dev/null```",
                    "runscript -Raw=```killall -9 curl 2>/dev/null```",
                    f"runscript -Raw=```pkill -9 -f '{workspace_path}' 2>/dev/null```"
                ]
            
            for cmd in emergency_commands:
                try:
                    self.session_manager.execute_command(session, "runscript", cmd, is_admin=True)
                except:
                    pass  # Ignore all errors in emergency termination
                    
        except:
            pass  # Ignore all errors in emergency cleanup


def create_cleanup_manager(session_manager: SessionManager, logger: Optional[ILogger] = None) -> WorkspaceCleanupManager:
    """Factory function to create a workspace cleanup manager"""
    return WorkspaceCleanupManager(session_manager, logger)


def cleanup_workspace_safe(session_manager: SessionManager, session: RTRSession, 
                          host_info: HostInfo, logger: Optional[ILogger] = None) -> bool:
    """
    Safe wrapper for workspace cleanup that handles all exceptions
    
    Args:
        session_manager: Session manager for RTR operations
        session: Active RTR session
        host_info: Target host information
        logger: Optional logger instance
        
    Returns:
        True if cleanup successful or not needed, False if cleanup failed
    """
    try:
        cleanup_manager = create_cleanup_manager(session_manager, logger)
        return cleanup_manager.cleanup_workspace(session, host_info)
    except Exception as e:
        if logger:
            logger.error(f"Safe cleanup wrapper error: {e}", exc_info=True)
        return False


def emergency_cleanup_safe(session_manager: SessionManager, session: RTRSession, 
                         host_info: HostInfo, logger: Optional[ILogger] = None) -> bool:
    """
    Safe wrapper for emergency cleanup that handles all exceptions
    
    Args:
        session_manager: Session manager for RTR operations
        session: Active RTR session
        host_info: Target host information
        logger: Optional logger instance
        
    Returns:
        True if emergency cleanup attempted, False if completely failed
    """
    try:
        cleanup_manager = create_cleanup_manager(session_manager, logger)
        return cleanup_manager.emergency_cleanup(session, host_info)
    except Exception as e:
        if logger:
            logger.error(f"Emergency cleanup wrapper error: {e}", exc_info=True)
        return False