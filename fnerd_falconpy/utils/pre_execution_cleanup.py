"""
Pre-execution cleanup utilities for ensuring clean environment before forensic collection.

This module provides comprehensive pre-execution checks and cleanup to ensure no
conflicting processes or workspace directories exist before starting new collections.
This prevents data corruption and process conflicts.

Critical Pre-Execution Checks:
1. Check for running UAC/KAPE processes
2. Terminate any existing processes  
3. Clean up existing workspace directories
4. Verify clean environment before proceeding
"""

import time
import os
from typing import Optional, List, Dict, Tuple
from fnerd_falconpy.core.base import HostInfo, RTRSession, Platform, ILogger, DefaultLogger, IConfigProvider
from fnerd_falconpy.managers.managers import SessionManager


class PreExecutionCleanupManager:
    """Manages pre-execution cleanup operations to ensure clean environment"""
    
    def __init__(self, session_manager: SessionManager, config: Optional[IConfigProvider] = None, logger: Optional[ILogger] = None):
        """
        Initialize pre-execution cleanup manager
        
        Args:
            session_manager: Session manager for RTR operations
            config: Configuration provider (optional, will use defaults if not provided)
            logger: Logger instance (uses DefaultLogger if not provided)
        """
        self.session_manager = session_manager
        self.config = config
        self.logger = logger or DefaultLogger("PreExecutionCleanupManager")
        self.current_pid = str(os.getpid())
        
        # Initialize workspace paths from config if available
        self._init_workspace_paths()
        
        # Process patterns to look for - ONLY actual forensic tool processes
        self._init_process_patterns()
    
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
    
    def _init_process_patterns(self):
        """Initialize process patterns, updating paths based on workspace configuration"""
        # Get the Unix workspace path for process patterns
        unix_path = self.workspace_paths.get(Platform.LINUX, "/opt/0x4n6nerd")
        
        self.process_patterns = {
            Platform.WINDOWS: ["kape.exe", "KAPE.exe", "powershell.*KAPE"],
            Platform.MAC: [rf"{unix_path}/uac-main/uac", r"\./uac\s", r"\buac\s.*--", "curl.*s3.*amazonaws.*uac-"],
            Platform.LINUX: [rf"{unix_path}/uac-main/uac", r"\./uac\s", r"\buac\s.*--", "curl.*s3.*amazonaws.*uac-"]
        }
    
    def ensure_clean_environment(self, session: RTRSession, host_info: HostInfo) -> bool:
        """
        Ensure clean environment before starting forensic collection
        
        Args:
            session: Active RTR session
            host_info: Target host information
            
        Returns:
            True if environment is clean or was successfully cleaned, False if cleanup failed
        """
        try:
            platform = Platform(host_info.platform.lower())
            
            self.logger.info(f"Starting pre-execution cleanup for {host_info.hostname} ({platform.value})")
            print(f"[*] Checking for existing processes/workspace on {host_info.hostname}...")
            
            # Step 1: Check for running processes
            running_processes = self._check_running_processes(session, platform)
            
            if running_processes:
                self.logger.warning(f"Found {len(running_processes)} running processes that need termination")
                print(f"[!] Found {len(running_processes)} existing processes - terminating...")
                
                # Step 2: Terminate existing processes
                if not self._terminate_existing_processes(session, platform, running_processes):
                    self.logger.error("Failed to terminate existing processes")
                    print("[!] Failed to terminate existing processes")
                    return False
                
                # Step 3: Wait for processes to terminate
                self._wait_for_process_termination(session, platform)
            else:
                self.logger.info("No conflicting processes found")
                print("[+] No existing processes found")
            
            # Step 4: Check and clean workspace directory (AFTER process termination)
            workspace_path = self.workspace_paths.get(platform)
            if workspace_path:
                if self._workspace_exists(session, workspace_path, platform):
                    self.logger.warning(f"Existing workspace found: {workspace_path}")
                    print(f"[!] Existing workspace found: {workspace_path} - removing...")
                    
                    if not self._clean_workspace_directory(session, workspace_path, platform):
                        self.logger.error("Failed to clean existing workspace")
                        print("[!] Failed to clean existing workspace")
                        return False
                    
                    print("[+] Existing workspace removed successfully")
                else:
                    self.logger.info("No existing workspace found")
                    print("[+] No existing workspace found")
                
                # Step 5: Create fresh workspace directory
                if not self._create_fresh_workspace(session, workspace_path, platform):
                    self.logger.error("Failed to create fresh workspace directory")
                    print("[!] Failed to create fresh workspace directory")
                    return False
            
            # Step 6: Final verification
            if self._verify_clean_environment(session, platform):
                self.logger.info("✅ Environment is clean and ready for collection")
                print("[+] Environment verified clean and ready")
                return True
            else:
                self.logger.error("❌ Environment verification failed")
                print("[!] Environment verification failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Error during pre-execution cleanup: {e}", exc_info=True)
            print(f"[!] Pre-execution cleanup error: {e}")
            return False
    
    def _check_running_processes(self, session: RTRSession, platform: Platform) -> List[Dict[str, str]]:
        """
        Check for running UAC/KAPE processes
        
        Args:
            session: Active RTR session
            platform: Target platform
            
        Returns:
            List of running processes with PID and command info
        """
        try:
            running_processes = []
            process_patterns = self.process_patterns.get(platform, [])
            
            for pattern in process_patterns:
                processes = self._find_processes_by_pattern(session, platform, pattern)
                running_processes.extend(processes)
            
            # Remove duplicates based on PID
            unique_processes = []
            seen_pids = set()
            for proc in running_processes:
                if proc['pid'] not in seen_pids:
                    unique_processes.append(proc)
                    seen_pids.add(proc['pid'])
            
            return unique_processes
            
        except Exception as e:
            self.logger.error(f"Error checking running processes: {e}")
            return []
    
    def _find_processes_by_pattern(self, session: RTRSession, platform: Platform, pattern: str) -> List[Dict[str, str]]:
        """
        Find processes matching a specific pattern
        
        Args:
            session: Active RTR session
            platform: Target platform
            pattern: Process pattern to search for
            
        Returns:
            List of matching processes
        """
        try:
            if platform == Platform.WINDOWS:
                # Use Get-Process and Get-WmiObject for Windows
                ps_cmd = f"runscript -Raw=```Get-WmiObject Win32_Process | Where-Object {{ $_.Name -like '*{pattern}*' -or $_.CommandLine -like '*{pattern}*' }} | Select-Object ProcessId,Name,CommandLine | Format-Table -AutoSize```"
            else:
                # Use ps and grep for Unix-like systems
                ps_cmd = f"runscript -Raw=```ps aux | grep -E '{pattern}' | grep -v grep```"
            
            result = self.session_manager.execute_command(session, "runscript", ps_cmd, is_admin=True)
            
            if not result or not result.stdout.strip():
                return []
            
            return self._parse_process_output(result.stdout, platform)
            
        except Exception as e:
            self.logger.debug(f"Error finding processes for pattern {pattern}: {e}")
            return []
    
    def _is_current_fnerd_falconpy_process(self, pid: str, command: str) -> bool:
        """
        Check if a process is a fnerd_falconpy process (which we should never kill)
        
        Args:
            pid: Process ID
            command: Process command line
            
        Returns:
            True if this is a falcon-client process, False otherwise
        """
        # Never kill falcon-client processes (avoid killing ourselves or other falcon-client instances)
        if 'falcon-client' in command:
            return True
            
        # Never kill Python processes that contain falcon-client in their command line
        if 'python' in command.lower() and ('falcon-client' in command or 'fnerd-falconpy' in command or 'fnerd_falconpy' in command):
            return True
            
        return False
    
    def _parse_process_output(self, output: str, platform: Platform) -> List[Dict[str, str]]:
        """
        Parse process output to extract PID and command information
        
        Args:
            output: Raw process output
            platform: Target platform
            
        Returns:
            List of parsed process information
        """
        try:
            processes = []
            lines = output.strip().split('\n')
            
            for line in lines:
                if not line.strip() or 'grep' in line:
                    continue
                
                if platform == Platform.WINDOWS:
                    # Parse Windows Get-WmiObject output
                    if 'ProcessId' in line or '--------' in line:
                        continue
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            pid = parts[0]
                            name = parts[1] if len(parts) > 1 else "unknown"
                            command = ' '.join(parts[2:]) if len(parts) > 2 else name
                            
                            # Skip current fnerd_falconpy process
                            if not self._is_current_fnerd_falconpy_process(pid, command):
                                processes.append({
                                    'pid': pid,
                                    'name': name,
                                    'command': command
                                })
                        except:
                            continue
                else:
                    # Parse Unix ps aux output
                    parts = line.split()
                    if len(parts) >= 11:  # ps aux has at least 11 columns
                        try:
                            pid = parts[1]
                            command = ' '.join(parts[10:])
                            name = parts[10].split('/')[-1] if '/' in parts[10] else parts[10]
                            
                            # Skip current fnerd_falconpy process
                            if not self._is_current_fnerd_falconpy_process(pid, command):
                                processes.append({
                                    'pid': pid,
                                    'name': name,
                                    'command': command
                                })
                        except:
                            continue
            
            return processes
            
        except Exception as e:
            self.logger.debug(f"Error parsing process output: {e}")
            return []
    
    def _terminate_existing_processes(self, session: RTRSession, platform: Platform, processes: List[Dict[str, str]]) -> bool:
        """
        Terminate existing processes
        
        Args:
            session: Active RTR session
            platform: Target platform
            processes: List of processes to terminate
            
        Returns:
            True if termination successful, False otherwise
        """
        try:
            success = True
            
            for proc in processes:
                pid = proc['pid']
                name = proc['name']
                
                self.logger.info(f"Terminating process: {name} (PID: {pid})")
                print(f"[*] Terminating process: {name} (PID: {pid})")
                
                if platform == Platform.WINDOWS:
                    # Use taskkill for Windows
                    kill_cmd = f"runscript -Raw=```taskkill /F /PID {pid}```"
                else:
                    # Use kill for Unix-like systems
                    kill_cmd = f"runscript -Raw=```kill -9 {pid}```"
                
                result = self.session_manager.execute_command(session, "runscript", kill_cmd, is_admin=True)
                
                if not result or result.return_code != 0:
                    self.logger.warning(f"Failed to terminate process {name} (PID: {pid})")
                    print(f"[!] Failed to terminate process {name} (PID: {pid})")
                    success = False
                else:
                    self.logger.info(f"Successfully terminated process {name} (PID: {pid})")
                    print(f"[+] Terminated process {name} (PID: {pid})")
                
                # Brief pause between kills
                time.sleep(1)
            
            return success
            
        except Exception as e:
            self.logger.error(f"Error terminating processes: {e}")
            return False
    
    def _wait_for_process_termination(self, session: RTRSession, platform: Platform, max_wait: int = 30) -> bool:
        """
        Wait for processes to fully terminate
        
        Args:
            session: Active RTR session
            platform: Target platform
            max_wait: Maximum wait time in seconds
            
        Returns:
            True if all processes terminated, False if timeout
        """
        try:
            self.logger.info("Waiting for process termination to complete...")
            print("[*] Waiting for process termination...")
            
            start_time = time.time()
            
            while time.time() - start_time < max_wait:
                # Check if any target processes are still running
                remaining_processes = self._check_running_processes(session, platform)
                
                if not remaining_processes:
                    self.logger.info("All processes successfully terminated")
                    print("[+] All processes terminated")
                    return True
                
                self.logger.debug(f"{len(remaining_processes)} processes still running, waiting...")
                time.sleep(2)
            
            self.logger.warning(f"Process termination timed out after {max_wait} seconds")
            print(f"[!] Process termination timed out after {max_wait} seconds")
            return False
            
        except Exception as e:
            self.logger.error(f"Error waiting for process termination: {e}")
            return False
    
    def _workspace_exists(self, session: RTRSession, workspace_path: str, platform: Platform) -> bool:
        """
        Check if workspace directory exists
        
        Args:
            session: Active RTR session
            workspace_path: Path to workspace directory
            platform: Target platform
            
        Returns:
            True if workspace exists, False otherwise
        """
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
    
    def _clean_workspace_directory(self, session: RTRSession, workspace_path: str, platform: Platform) -> bool:
        """
        Clean existing workspace directory
        
        Args:
            session: Active RTR session
            workspace_path: Path to workspace directory
            platform: Target platform
            
        Returns:
            True if cleanup successful, False otherwise
        """
        try:
            if platform == Platform.WINDOWS:
                # Windows cleanup - first kill any processes, then remove directory
                # This prevents "in use" errors
                cleanup_commands = [
                    # Kill any KAPE processes
                    "runscript -Raw=```Get-Process -Name 'kape' -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue```",
                    # Kill processes with handles to the directory
                    f"runscript -Raw=```Get-Process | Where-Object {{$_.Path -like '{workspace_path}*'}} | Stop-Process -Force -ErrorAction SilentlyContinue```",
                    # Small delay to let processes release handles
                    "runscript -Raw=```Start-Sleep -Seconds 2```",
                    # Now remove the directory
                    f"runscript -Raw=```if (Test-Path '{workspace_path}') {{ Remove-Item -Path '{workspace_path}' -Recurse -Force -ErrorAction Stop }}```"
                ]
                
                # Execute all cleanup commands
                all_success = True
                for cmd in cleanup_commands:
                    result = self.session_manager.execute_command(session, "runscript", cmd, is_admin=True)
                    if not result and "Remove-Item" in cmd:  # Only fail if the actual removal fails
                        all_success = False
                    time.sleep(1)
                
                if not all_success:
                    self.logger.warning("Workspace cleanup had issues")
                    return False
            else:
                # Unix cleanup commands - use robust bash approach to avoid race conditions
                # First remove contents, then remove directory, then sync and wait longer
                cleanup_cmd = f"runscript -Raw=```rm -rf {workspace_path}/* 2>/dev/null || true; rm -rf {workspace_path} 2>/dev/null || true; sync; sleep 3```"
                
                self.logger.info(f"Cleaning workspace directory: {workspace_path}")
                result = self.session_manager.execute_command(session, "runscript", cleanup_cmd, is_admin=True)
                
                if not result:
                    self.logger.warning("Workspace cleanup command failed")
                    return False
            
            # Wait for filesystem operations to complete and verify cleanup
            self.logger.info("Waiting for filesystem operations to complete...")
            time.sleep(8)  # Increased to 8 seconds for better race condition prevention with root directories
            
            # Verify cleanup completed
            if not self._workspace_exists(session, workspace_path, platform):
                self.logger.info("Workspace directory successfully cleaned")
                return True
            else:
                self.logger.warning("Workspace directory still exists after cleanup, attempting force removal...")
                
                # Fallback: Try more aggressive cleanup
                if platform == Platform.WINDOWS:
                    # Use cmd.exe rmdir which can be more forceful
                    fallback_cmd = f"runscript -Raw=```cmd.exe /c 'rmdir /s /q {workspace_path} 2>nul'```"
                else:
                    fallback_cmd = f"runscript -Raw=```rm -rf {workspace_path} 2>/dev/null || true; sync; sleep 1```"
                
                fallback_result = self.session_manager.execute_command(session, "runscript", fallback_cmd, is_admin=True)
                time.sleep(2)
                
                if not self._workspace_exists(session, workspace_path, platform):
                    self.logger.info("Workspace directory successfully cleaned on fallback attempt")
                    return True
                
                self.logger.warning("Workspace directory still exists after all cleanup attempts")
                return False
                
        except Exception as e:
            self.logger.error(f"Error cleaning workspace directory: {e}")
            return False
    
    def _create_fresh_workspace(self, session: RTRSession, workspace_path: str, platform: Platform) -> bool:
        """
        Create fresh workspace directory for forensic collection
        
        Args:
            session: Active RTR session
            workspace_path: Path to workspace directory
            platform: Target platform
            
        Returns:
            True if creation successful, False otherwise
        """
        try:
            self.logger.info(f"Creating fresh workspace directory: {workspace_path}")
            print(f"[*] Creating fresh workspace directory: {workspace_path}")
            
            # Add extra wait before creation to avoid race condition with previous deletion
            self.logger.info("Waiting for filesystem to stabilize before creation...")
            time.sleep(10)  # Increased to 10 seconds to prevent race conditions with root-owned directories
            
            if platform == Platform.WINDOWS:
                # Windows directory creation - use proper PowerShell syntax
                create_cmd = f"runscript -Raw=```New-Item -ItemType Directory -Path '{workspace_path}' -Force```"
            else:
                # Unix directory creation - use robust bash approach with sync and verification
                create_cmd = f"runscript -Raw=```mkdir -p {workspace_path} && sync && sleep 1```"
            
            result = self.session_manager.execute_command(session, "runscript", create_cmd, is_admin=True)
            
            if not result:
                self.logger.error(f"Failed to execute create command for workspace directory: {workspace_path}")
                return False
            
            # For mkdir commands, return_code might be 0 even if directory exists (mkdir -p)
            # So we rely on verification rather than return code
            if result.return_code != 0 and result.stderr and "File exists" not in result.stderr:
                self.logger.warning(f"Create command returned non-zero code: {result.return_code}")
                if result.stderr:
                    self.logger.warning(f"Error details: {result.stderr}")
                # Don't return False yet, let verification be the final check
            
            # Wait for filesystem operations to complete  
            time.sleep(3)  # Increased from 2 to 3 seconds for better stability
            
            # Verify directory was created
            if self._workspace_exists(session, workspace_path, platform):
                self.logger.info(f"Fresh workspace directory created successfully: {workspace_path}")
                print(f"[+] Fresh workspace directory created: {workspace_path}")
                return True
            else:
                self.logger.error(f"Workspace directory verification failed: {workspace_path}")
                print(f"[!] Failed to verify workspace directory creation: {workspace_path}")
                
                # Try one more time with additional wait to resolve race conditions
                self.logger.info("Race condition detected - waiting longer and retrying...")
                time.sleep(3)  # Additional wait to resolve race condition
                
                if platform == Platform.WINDOWS:
                    fallback_cmd = f"runscript -Raw=```New-Item -ItemType Directory -Path '{workspace_path}' -Force; if (Test-Path '{workspace_path}') {{ Write-Output 'SUCCESS' }} else {{ Write-Output 'FAILED' }}```"
                else:
                    fallback_cmd = f"runscript -Raw=```mkdir -p {workspace_path} && sync && sleep 1; ls -ld {workspace_path} 2>/dev/null || echo 'FAILED'```"
                
                fallback_result = self.session_manager.execute_command(session, "runscript", fallback_cmd, is_admin=True)
                
                if fallback_result and fallback_result.stdout:
                    if platform == Platform.WINDOWS:
                        success_check = "SUCCESS" in fallback_result.stdout
                    else:
                        success_check = "FAILED" not in fallback_result.stdout
                    
                    if success_check:
                        self.logger.info("Fallback directory creation succeeded")
                        print(f"[+] Fallback directory creation succeeded: {workspace_path}")
                        return True
                
                return False
                
        except Exception as e:
            self.logger.error(f"Error creating workspace directory: {e}")
            return False
    
    def _verify_clean_environment(self, session: RTRSession, platform: Platform) -> bool:
        """
        Verify that environment is clean and ready
        
        Args:
            session: Active RTR session
            platform: Target platform
            
        Returns:
            True if environment is clean, False otherwise
        """
        try:
            # Check for any remaining processes
            remaining_processes = self._check_running_processes(session, platform)
            if remaining_processes:
                self.logger.warning(f"Found {len(remaining_processes)} remaining processes")
                return False
            
            # Check that fresh workspace directory exists and is empty
            workspace_path = self.workspace_paths.get(platform)
            if workspace_path:
                if not self._workspace_exists(session, workspace_path, platform):
                    self.logger.warning(f"Fresh workspace directory not found: {workspace_path}")
                    return False
                
                # Verify workspace is empty (fresh)
                if not self._workspace_is_empty(session, workspace_path, platform):
                    self.logger.warning(f"Workspace directory is not empty: {workspace_path}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error verifying clean environment: {e}")
            return False
    
    def _workspace_is_empty(self, session: RTRSession, workspace_path: str, platform: Platform) -> bool:
        """
        Check if workspace directory is empty
        
        Args:
            session: Active RTR session
            workspace_path: Path to workspace directory
            platform: Target platform
            
        Returns:
            True if workspace is empty, False otherwise
        """
        try:
            if platform == Platform.WINDOWS:
                # Windows check for empty directory
                check_cmd = f"runscript -Raw=```(Get-ChildItem '{workspace_path}' -Force | Measure-Object).Count```"
            else:
                # Unix check for empty directory
                check_cmd = f"runscript -Raw=```ls -la {workspace_path} | wc -l```"
            
            result = self.session_manager.execute_command(session, "runscript", check_cmd, is_admin=True)
            
            if result and result.stdout.strip().isdigit():
                count = int(result.stdout.strip())
                if platform == Platform.WINDOWS:
                    # Windows: 0 means empty
                    return count == 0
                else:
                    # Unix: 3 means empty (. .. and total line from ls -la)
                    return count <= 3
            
            return False
            
        except Exception as e:
            self.logger.debug(f"Error checking if workspace is empty: {e}")
            return False


def ensure_clean_environment_safe(session_manager: SessionManager, session: RTRSession, 
                                 host_info: HostInfo, logger: Optional[ILogger] = None) -> bool:
    """
    Safe wrapper for pre-execution cleanup that handles all exceptions
    
    Args:
        session_manager: Session manager for RTR operations
        session: Active RTR session
        host_info: Target host information
        logger: Optional logger instance
        
    Returns:
        True if environment is clean or was successfully cleaned, False if cleanup failed
    """
    try:
        cleanup_manager = PreExecutionCleanupManager(session_manager, logger)
        return cleanup_manager.ensure_clean_environment(session, host_info)
    except Exception as e:
        if logger:
            logger.error(f"Pre-execution cleanup wrapper error: {e}", exc_info=True)
        print(f"[!] Pre-execution cleanup error: {e}")
        return False