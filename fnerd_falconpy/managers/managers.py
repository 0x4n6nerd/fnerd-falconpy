"""
Manager classes for handling business logic.
"""

import time
from typing import Dict, List, Optional
from pathlib import Path
from fnerd_falconpy.core.base import (
    HostInfo, RTRSession, CommandResult, 
    ILogger, DefaultLogger, Platform
)
from fnerd_falconpy.api.clients import DiscoverAPIClient, RTRAPIClient
from fnerd_falconpy.utils.platform_handlers import PlatformFactory
from fnerd_falconpy.core.configuration import Configuration

class HostManager:
    """Manages host discovery and information retrieval"""
    
    def __init__(self, discover_client: DiscoverAPIClient, logger: Optional[ILogger] = None):
        """
        Initialize host manager
        
        Args:
            discover_client: Discover API client instance
            logger: Logger instance (uses DefaultLogger if not provided)
        """
        self.discover_client = discover_client
        self.logger = logger or DefaultLogger("HostManager")
        
    def get_host_by_hostname(self, hostname: str) -> Optional[HostInfo]:
        """
        Get host information by hostname
        
        Args:
            hostname: Target hostname
            
        Returns:
            HostInfo object or None if not found
        """
        try:
            # Validate input
            if not hostname:
                self.logger.error("Hostname cannot be empty")
                return None
                
            # Query for host IDs
            filter_str = f"hostname:*'*{hostname}*'"
            host_ids = self.discover_client.query_hosts(filter_str)
            
            if not host_ids:
                self.logger.info(f"No hosts found matching hostname: {hostname}")
                return None
                
            # Get host details
            host_data = self.discover_client.get_host_details(host_ids)
            
            if not host_data:
                self.logger.warning("Failed to get host details")
                return None
                
            # Extract and return host info
            return self.extract_host_info(host_data)
            
        except Exception as e:
            self.logger.error(f"Unexpected error in get_host_by_hostname: {e}", exc_info=True)
            return None
        
    def extract_host_info(self, host_data: Dict) -> Optional[HostInfo]:
        """
        Extract host information from API response
        
        Args:
            host_data: Raw host data from API
            
        Returns:
            HostInfo object or None
        """
        try:
            # Validate input
            if not host_data:
                self.logger.error("Host data cannot be None or empty")
                return None
                
            if not isinstance(host_data, dict):
                self.logger.error(f"Host data must be a dictionary, got {type(host_data).__name__}")
                return None
                
            # Extract resource data
            if 'body' not in host_data:
                self.logger.warning("Host data missing 'body' key")
                return None
                
            if 'resources' not in host_data['body'] or not host_data['body']['resources']:
                self.logger.warning("Host data missing 'resources' array or it's empty")
                return None
                
            resource = host_data['body']['resources'][0]
            
            # Extract fields with defaults
            # Handle both Discover API (aid) and Hosts API (device_id) formats
            hostname = resource.get('hostname', '')
            aid = resource.get('aid', '') or resource.get('device_id', '')
            cid = resource.get('cid', '')
            platform_name = resource.get('platform_name', '')
            os_version = resource.get('os_version', '')
            cpu_name = resource.get('cpu_processor_name', '')
            
            # Validate required fields
            if not aid:
                self.logger.warning("Agent ID is missing")
                return None
                
            if not cid:
                self.logger.warning("Customer ID is missing")
                return None
                
            # Create and return HostInfo object
            return HostInfo(
                hostname=hostname,
                aid=aid,
                cid=cid,
                os_name=platform_name,
                os_version=os_version,
                cpu_name=cpu_name,
                platform=platform_name.lower()
            )
            
        except (KeyError, IndexError) as e:
            self.logger.error(f"Failed to extract host information: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error in extract_host_info: {e}", exc_info=True)
            return None

class SessionManager:
    """Manages RTR session lifecycle"""
    
    def __init__(self, rtr_client: RTRAPIClient, logger: Optional[ILogger] = None):
        """
        Initialize session manager
        
        Args:
            rtr_client: RTR API client instance
            logger: Logger instance (uses DefaultLogger if not provided)
        """
        self.rtr_client = rtr_client
        self.logger = logger or DefaultLogger("SessionManager")
        self._active_sessions: Dict[str, RTRSession] = {}
        self.config = Configuration()
        
    def start_session(self, device_id: str) -> Optional[RTRSession]:
        """
        Start RTR session
        
        Args:
            device_id: Target device ID (AID)
            
        Returns:
            RTRSession object or None
        """
        try:
            # Validate input
            if not device_id:
                self.logger.error("Agent ID cannot be empty")
                return None
                
            # Initialize RTR session
            session_response = self.rtr_client.init_session(device_id)
            
            if not session_response:
                self.logger.error("Failed to initialize RTR session")
                return None
                
            # Check response status
            if session_response.get("status_code") == 201:
                try:
                    session_id = session_response['body']['resources'][0]['session_id']
                    self.logger.info(f"Successfully initiated RTR session: {session_id}")
                    
                    # Create RTRSession object
                    rtr_session = RTRSession(
                        session_id=session_id,
                        device_id=device_id,
                        status_code=session_response["status_code"],
                        created_at=time.time(),
                        raw_response=session_response
                    )
                    
                    # Store in active sessions
                    self._active_sessions[session_id] = rtr_session
                    
                    return rtr_session
                    
                except (KeyError, IndexError) as e:
                    self.logger.error(f"Failed to extract session ID from successful response: {e}")
                    return None
            else:
                # Handle unsuccessful status code
                self.logger.error(f"Failed to initiate session: {session_response}")
                
                # Attempt to extract detailed error information
                try:
                    if 'body' in session_response and 'errors' in session_response['body']:
                        errors = session_response['body']['errors']
                        self.logger.error(f"Session initialization errors: {errors}")
                except Exception:
                    pass
                    
                return None
                
        except Exception as e:
            self.logger.error(f"Unexpected error in start_session: {e}", exc_info=True)
            return None
        
    def end_session(self, session: RTRSession) -> bool:
        """
        End RTR session
        
        Args:
            session: RTRSession to end
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate session
            if not session:
                self.logger.error("Session cannot be None")
                return False
                
            if not isinstance(session, RTRSession):
                self.logger.error(f"Invalid session type: {type(session)}")
                return False
                
            # Delete the session
            delete_response = self.rtr_client.delete_session(session.session_id)
            
            if not delete_response:
                self.logger.error("Failed to delete RTR session")
                return False
                
            # Check delete response
            if delete_response.get('status_code') == 204:
                self.logger.info(f"RTR Session {session.session_id} successfully deleted.")
                
                # Remove from active sessions
                if session.session_id in self._active_sessions:
                    del self._active_sessions[session.session_id]
                    
                return True
            else:
                self.logger.error(f"Failed to delete session: {delete_response}")
                
                # Check for specific error types
                try:
                    if 'body' in delete_response and 'errors' in delete_response['body']:
                        errors = delete_response['body']['errors']
                        self.logger.error(f"Delete session errors: {errors}")
                except Exception:
                    pass
                    
                return False
                
        except Exception as e:
            self.logger.error(f"Unexpected error in end_session: {e}", exc_info=True)
            return False
        
    def execute_command(self, session: RTRSession, base_command: str, 
                       command: str, is_admin: bool = False, 
                       suppress_stderr_warnings: bool = False) -> Optional[CommandResult]:
        """
        Execute command in session
        
        Args:
            session: Active RTR session
            base_command: Base RTR command
            command: Command string
            is_admin: Whether to use admin privileges
            suppress_stderr_warnings: If True, don't log stderr as warnings (for discovery commands)
            
        Returns:
            CommandResult or None
        """
        try:
            # Validate inputs
            if not session:
                self.logger.error("Session cannot be None")
                return None
                
            if not base_command or not command:
                self.logger.error("Base command and command string cannot be empty")
                return None
                
            # Check session status
            if session.status_code != 201:
                self.logger.error(f"Invalid session status: {session.status_code}")
                return None
                
            # Execute command
            if is_admin:
                command_response = self.rtr_client.execute_admin_command(
                    session_id=session.session_id,
                    base_command=base_command,
                    command_string=command
                )
            else:
                command_response = self.rtr_client.execute_command(
                    session_id=session.session_id,
                    base_command=base_command,
                    command_string=command
                )
                
            if not command_response:
                self.logger.error("Failed to execute command")
                return None
                
            # Verify command execution started
            if command_response.get("status_code") != 201:
                self.logger.error(f"Failed to execute command: {command_response}")
                return None
                
            try:
                cloud_request_id = command_response["body"]["resources"][0]["cloud_request_id"]
                self.logger.info(f"Command execution started, Cloud Request ID: {cloud_request_id}")
            except (KeyError, IndexError) as e:
                self.logger.error(f"Failed to extract cloud request ID: {e}")
                return None
                
            # Initial wait before checking status
            time.sleep(2)
            
            # Check command status with configurable timeout
            command_timeout = self.config.TIMEOUTS['command_execution']  # Configurable timeout (default 600s)
            check_interval = self.config.TIMEOUTS['command_status_check']  # 2 seconds
            max_retries = command_timeout // check_interval  # Calculate retries based on timeout
            retry_count = 0
            
            # Poll until command is complete
            while retry_count < max_retries:
                # Check status
                if is_admin:
                    result_response = self.rtr_client.check_admin_command_status(
                        cloud_request_id=cloud_request_id,
                        sequence_id=0
                    )
                else:
                    result_response = self.rtr_client.check_command_status(
                        cloud_request_id=cloud_request_id,
                        sequence_id=0
                    )
                    
                if not result_response:
                    self.logger.error(f"Failed to check command status on retry {retry_count}")
                    return None
                    
                try:
                    resource = result_response['body']['resources'][0]
                    
                    # Check if command is complete
                    if resource.get('complete', False):
                        # Extract output
                        stdout = resource.get('stdout', '')
                        stderr = resource.get('stderr', '')
                        
                        # Check for errors
                        if stderr and not suppress_stderr_warnings:
                            self.logger.warning(f"Command errors (stderr): {stderr}")
                            
                        # Create and return CommandResult
                        return CommandResult(
                            stdout=stdout,
                            stderr=stderr,
                            return_code=0 if not stderr else 1,  # Simplified return code
                            cloud_request_id=cloud_request_id,
                            complete=True
                        )
                        
                except (KeyError, IndexError) as e:
                    self.logger.error(f"Failed to parse command status response: {e}")
                    
                # Wait before next retry
                time.sleep(check_interval)
                retry_count += 1
                
            # Timeout reached
            self.logger.error(f"Command execution timed out after {command_timeout} seconds")
            return None
            
        except Exception as e:
            self.logger.error(f"Unexpected error in execute_command: {e}", exc_info=True)
            return None
        
    def pulse_session(self, session: RTRSession) -> bool:
        """
        Keep session alive
        
        Args:
            session: RTRSession to pulse
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not session:
                self.logger.error("Session cannot be None")
                return False
                
            result = self.rtr_client.pulse_session(session.device_id)
            return result is not None
            
        except Exception as e:
            self.logger.warning(f"Failed to pulse session: {e}")
            return False

class FileManager:
    """Manages file operations via RTR"""
    
    def __init__(self, rtr_client: RTRAPIClient, session_manager: SessionManager,
                 logger: Optional[ILogger] = None):
        """
        Initialize file manager
        
        Args:
            rtr_client: RTR API client instance
            session_manager: Session manager instance
            logger: Logger instance (uses DefaultLogger if not provided)
        """
        self.rtr_client = rtr_client
        self.session_manager = session_manager
        self.logger = logger or DefaultLogger("FileManager")
        
    def get_file_size(self, session: RTRSession, file_path: str, platform: Platform) -> Optional[int]:
        """
        Get remote file size
        
        Args:
            session: Active RTR session
            file_path: Remote file path
            platform: Target platform
            
        Returns:
            File size in bytes or None
        """
        try:
            # Validate inputs
            if not session:
                self.logger.warning("Invalid RTR session provided")
                return None
                
            if not file_path:
                self.logger.warning("Empty file path provided")
                return None
                
            # Get platform-specific handler
            platform_handler = PlatformFactory.create_handler(platform)
            
            # Get platform-specific command
            base_command, command_string = platform_handler.get_file_size_command(file_path)
            
            # Execute command
            result = self.session_manager.execute_command(
                session=session,
                base_command=base_command,
                command=command_string,
                is_admin=False
            )
            
            if not result:
                self.logger.info(f"Command returned None for file: {file_path}")
                return None
                
            # Parse output using platform-specific handler
            file_size = platform_handler.parse_file_size_output(result.stdout, file_path)
            
            if file_size is None:
                self.logger.info(f"File not found or could not parse size: {file_path}")
                
            return file_size
            
        except NotImplementedError as e:
            self.logger.error(f"Unsupported platform: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Error getting file size: {e}", exc_info=True)
            return None
        
    def download_file(self, session: RTRSession, device_id: str, 
                     remote_path: str, local_path: str, file_size: int) -> bool:
        """
        Download file from remote host with robust handling for large files
        
        Args:
            session: Active RTR session
            device_id: Target device ID
            remote_path: Remote file path
            local_path: Local save path (will be adjusted to .7z extension)
            file_size: Expected file size
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Check if the local_path already has .7z extension (from KAPE/UAC)
            from pathlib import Path
            local_path_obj = Path(local_path)
            
            # Only adjust if not already .7z
            if local_path_obj.suffix == '.7z':
                # Already has .7z extension (from KAPE/UAC collectors)
                local_path_7z = local_path
                self.logger.info(f"Local path already has .7z extension: {local_path_7z}")
            else:
                # For direct RTR downloads, replace extension with .7z
                if local_path_obj.suffix in ['.zip', '.tar', '.gz', '.tar.gz', '.vhdx']:
                    local_path_7z = str(local_path_obj.with_suffix('.7z'))
                else:
                    # Add .7z if no recognized extension
                    local_path_7z = str(local_path_obj) + '.7z'
                
                self.logger.info(f"Adjusted local path for 7z format: {local_path_7z}")
            
            # Issue the 'get' command
            self.logger.info(f"Issuing get command for: {remote_path}")
            cmd_response = self.rtr_client.execute_active_responder_command(
                base_command="get",
                command_string=f"get {remote_path}",
                device_id=device_id,
                session_id=session.session_id
            )
            
            if not cmd_response or cmd_response.get("status_code") != 201:
                self.logger.error("Failed to execute 'get' command")
                return False
                
            # Extract cloud request ID
            try:
                cloud_request_id = cmd_response["body"]["resources"][0]["cloud_request_id"]
                self.logger.info(f"'get' command issued. Cloud Request ID: {cloud_request_id}")
            except (KeyError, IndexError) as e:
                self.logger.error(f"Failed to extract cloud request ID: {e}")
                return False
                
            # CRITICAL: Dynamic timeout calculation based on file size
            # Production testing showed:
            # - 1.6GB file took 61 minutes over RTR (446 KB/s average)
            # - 3.4GB file took ~3 hours over slow VPN (30 KB/s worst case)
            # DO NOT REDUCE THESE TIMEOUTS - they are based on real-world testing
            if file_size and file_size > 0:
                # Calculate timeout assuming 30KB/s transfer rate (worst-case VPN scenario)
                # This gives 3.4GB files about 31 hours, but we cap at 5 hours (RTR practical limit)
                estimated_timeout = max(600, file_size / (30 * 1024))  # Minimum 10 minutes, 30KB/s for VPN
                self.logger.info(f"Using dynamic timeout of {estimated_timeout:.0f} seconds for {file_size:,} bytes")
            else:
                # IMPORTANT: Unknown file size gets maximum timeout
                # This happens when file metadata isn't available yet
                estimated_timeout = 18000  # 5 HOURS - DO NOT REDUCE
                self.logger.info(f"File size unknown, using maximum timeout of {estimated_timeout:.0f} seconds (5 hours)")
                
            poll_start = time.time()
            
            while True:
                elapsed = time.time() - poll_start
                if elapsed > estimated_timeout:
                    self.logger.error(f"Command polling exceeded timeout of {estimated_timeout:.0f} seconds")
                    return False
                    
                status_resp = self.rtr_client.check_active_responder_command_status(
                    cloud_request_id=cloud_request_id
                )
                
                if status_resp:
                    try:
                        result = status_resp["body"]["resources"][0]
                        if result.get("complete"):
                            if result.get("stderr"):
                                self.logger.error(f"Error during get command: {result['stderr']}")
                                return False
                            break
                    except (KeyError, IndexError):
                        pass
                
                # Log progress periodically
                if int(elapsed) % 30 == 0:
                    self.logger.info(f"Still waiting for file transfer... ({elapsed:.0f}s elapsed)")
                        
                time.sleep(2)  # Check every 2 seconds instead of 1
                    
            self.logger.info("get command completed successfully")
            
            # CRITICAL: Get file SHA with timeout protection
            # CrowdStrike Cloud needs time to process large files before SHA is available
            # DO NOT REDUCE THIS TIMEOUT - tested with 3.4GB files
            file_sha = None
            sha_wait_start = time.time()
            sha_timeout = 2000  # ~33.3 minutes to get SHA (production-tested for 3.4GB+ files)
            
            # IMPORTANT: Keep session alive during SHA retrieval
            # RTR sessions timeout after 10 minutes of inactivity
            # We pulse every 5 minutes to be safe (half of timeout period)
            last_sha_pulse_time = time.time()
            sha_pulse_interval = 300  # 5 minutes - MUST be less than 10-minute RTR timeout
            sha_check_count = 0
            
            while not file_sha:
                sha_check_count += 1
                elapsed_time = time.time() - sha_wait_start
                
                if elapsed_time > sha_timeout:
                    self.logger.error(f"Timeout waiting for file SHA after {sha_timeout} seconds ({sha_timeout/60:.1f} minutes)")
                    return False
                
                # Pulse session during SHA retrieval to prevent 10-minute timeout
                time_since_last_pulse = time.time() - last_sha_pulse_time
                if time_since_last_pulse >= sha_pulse_interval:
                    self.logger.info(f"Pulsing session during SHA retrieval (elapsed: {elapsed_time/60:.1f} min)")
                    if self.session_manager.pulse_session(session):
                        self.logger.info(f"Session pulsed successfully during SHA retrieval after {time_since_last_pulse/60:.1f} minutes")
                        last_sha_pulse_time = time.time()
                    else:
                        self.logger.error("Failed to pulse session during SHA retrieval - session may timeout")
                        return False  # Exit early if we can't pulse the session
                    
                files_resp = self.rtr_client.list_files_v2(session_id=session.session_id)
                
                if files_resp and files_resp.get("status_code") == 200:
                    try:
                        files_list = files_resp["body"]["resources"]
                        for file_info in files_list:
                            if file_info.get("cloud_request_id") == cloud_request_id:
                                file_sha = file_info.get("sha256")
                                break
                    except (KeyError, IndexError):
                        pass
                        
                if not file_sha:
                    # Log progress every 30 seconds
                    if int(elapsed_time) % 30 == 0 and elapsed_time > 0:
                        self.logger.info(f"Still waiting for file SHA... ({elapsed_time:.0f}s elapsed, check #{sha_check_count})")
                    time.sleep(4)
                    
            self.logger.info(f"Retrieved file SHA-256: {file_sha}")
            
            # Extract filename from path
            from pathlib import PurePath
            file_name = PurePath(remote_path).name
            if not file_name:
                file_name = "unknown_file"
            
            # Wait before requesting content
            time.sleep(5)
            
            # CRITICAL: Poll for file content with extended timeout
            # Production testing showed 3.4GB files need up to 5 hours over slow VPN
            # DO NOT REDUCE THIS TIMEOUT - it will break large file downloads
            content_wait_start = time.time()
            # RTR has a 4GB file size limit, we support up to that with 5-hour timeout
            content_timeout = 18000  # 5 HOURS - tested with 3.4GB files over 30KB/s VPN
            retry_count = 0
            # Calculate max retries based on timeout and retry interval (5 seconds)
            max_retries = content_timeout // 5  # 3600 retries for 5 hours with 5-second intervals
            
            # IMPORTANT: Prevent session timeout during long downloads
            # Without this, downloads >10 minutes fail with "session not found"
            last_pulse_time = time.time()
            pulse_interval = 300  # 5 minutes - keeps session alive during multi-hour downloads
            
            while retry_count < max_retries:
                if time.time() - content_wait_start > content_timeout:
                    self.logger.error(f"Timeout waiting for file content after {content_timeout} seconds")
                    return False
                
                # Pulse session if needed to prevent timeout
                time_since_last_pulse = time.time() - last_pulse_time
                if time_since_last_pulse >= pulse_interval:
                    if self.session_manager.pulse_session(session):
                        self.logger.debug(f"Session pulsed successfully after {time_since_last_pulse/60:.1f} minutes")
                        last_pulse_time = time.time()
                    else:
                        self.logger.warning("Failed to pulse session during file download - session may timeout")
                    
                file_contents = self.rtr_client.get_extracted_file_contents(
                    session_id=session.session_id,
                    sha256=file_sha,
                    filename=file_name
                )
                
                if isinstance(file_contents, bytes):
                    self.logger.info(f"File downloaded successfully: {len(file_contents):,} bytes")
                    
                    try:
                        # Save with .7z extension
                        with open(local_path_7z, "wb") as f:
                            f.write(file_contents)
                        
                        # Verify file was written correctly
                        saved_size = Path(local_path_7z).stat().st_size
                        if saved_size != len(file_contents):
                            self.logger.error(f"File size mismatch: expected {len(file_contents):,}, got {saved_size:,}")
                            return False
                            
                        self.logger.info(f"✅ File saved to: {local_path_7z} ({saved_size:,} bytes)")
                        self.logger.info("Note: File is in 7z format (CrowdStrike RTR automatic conversion)")
                        return True
                        
                    except IOError as e:
                        self.logger.error(f"Failed to write file: {e}")
                        return False
                        
                # Check for error response
                if isinstance(file_contents, dict):
                    try:
                        error_message = file_contents.get('body', {}).get('errors', [{}])[0].get('message')
                        if error_message == "Unknown file":
                            self.logger.info(f"File not ready yet, retrying... (attempt {retry_count + 1}/{max_retries})")
                    except Exception:
                        pass
                
                retry_count += 1        
                time.sleep(5)
            
            self.logger.error(f"Maximum retries ({max_retries}) exceeded while waiting for file content")
            return False
            
        except Exception as e:
            self.logger.error(f"Error downloading file: {e}", exc_info=True)
            return False
        
    def upload_to_cloud(self, cid: str, file_path: str, 
                       comments: str, description: str) -> bool:
        """
        Upload file to CrowdStrike cloud
        
        Args:
            cid: Customer ID
            file_path: Local file path
            comments: Audit log comments
            description: File description
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate input parameters
            if not cid:
                self.logger.error("CID cannot be empty")
                return False
                
            if not file_path:
                self.logger.error("Filename cannot be empty")
                return False
                
            # Check if file exists
            path = Path(file_path)
            if not path.exists():
                self.logger.error(f"File not found: {file_path}")
                return False
                
            # Read file for upload
            try:
                with open(file_path, "rb") as upload_file:
                    file_content = upload_file.read()
                    
                    if not file_content:
                        self.logger.warning(f"File {file_path} is empty")
                        
                    filename = path.name
                    file_upload = [('file', (filename, file_content, 'application/octet-stream'))]
                    
            except PermissionError:
                self.logger.error(f"Permission denied when reading file: {file_path}")
                return False
            except IOError as e:
                self.logger.error(f"IO Error when reading file: {e}")
                return False
                
            # Upload file
            self.logger.info(f"Uploading file: {filename} ({len(file_content)} bytes)")
            upload_response = self.rtr_client.create_put_files(
                comments_for_audit_log=comments,
                description=description,
                name=filename,
                files=file_upload
            )
            
            if not upload_response:
                self.logger.error("Failed to upload file - no response")
                return False
                
            # Log full response for debugging
            self.logger.info(f"Upload response status: {upload_response.get('status_code', 'N/A')}")
            
            # Check for errors in response
            if 'body' in upload_response and 'errors' in upload_response['body']:
                errors = upload_response['body']['errors']
                self.logger.error(f"Upload errors: {errors}")
                return False
                
            # Verify upload was successful
            try:
                if ('body' in upload_response and 'meta' in upload_response['body'] and 
                    'writes' in upload_response['body']['meta'] and
                    upload_response['body']['meta']['writes']['resources_affected'] == 1):
                    self.logger.info("File uploaded successfully")
                    return True
                else:
                    self.logger.warning(f"Upload API returned but resources_affected != 1")
                    self.logger.warning(f"Full upload response: {upload_response}")
                    return False
            except (KeyError, TypeError) as e:
                self.logger.error(f"Invalid upload response format: {e}")
                return False
                
        except Exception as e:
            self.logger.error(f"Unexpected error in upload_to_cloud: {e}", exc_info=True)
            return False
        
    def delete_from_cloud(self, cid: str, filename: str) -> bool:
        """
        Delete file from CrowdStrike cloud
        
        Args:
            cid: Customer ID
            filename: File name to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Validate input parameters
            if not cid:
                self.logger.error("CID cannot be empty")
                return False
                
            if not filename:
                self.logger.error("Filename cannot be empty")
                return False
                
            # List available put files
            response = self.rtr_client.list_put_files()
            
            if not response or 'body' not in response or 'resources' not in response['body']:
                self.logger.warning("No files available or invalid response")
                return False
                
            ids_list = response['body']['resources']
            
            if not ids_list:
                self.logger.info("No files found in put files repository")
                return False
                
            # Get detailed file information
            file_ids = self.rtr_client.get_put_files_v2(ids=ids_list)
            
            if not file_ids or 'body' not in file_ids or 'resources' not in file_ids['body']:
                self.logger.warning("Failed to get file details")
                return False
                
            # Find and delete the target file
            for file in file_ids['body']['resources']:
                try:
                    if file.get('name') == filename:
                        resource_id = file['id']
                        
                        # Delete the file
                        delete_response = self.rtr_client.delete_put_files(ids=resource_id)
                        
                        if not delete_response:
                            self.logger.error("Failed to delete file")
                            return False
                            
                        # Verify deletion was successful
                        if ('body' in delete_response and 'meta' in delete_response['body'] and 
                            'writes' in delete_response['body']['meta'] and
                            delete_response['body']['meta']['writes']['resources_affected'] == 1):
                            self.logger.info(f"File '{filename}' removed successfully")
                            return True
                        else:
                            self.logger.warning(f"Deletion API returned success but no resources affected: {delete_response}")
                            return False
                            
                except KeyError as e:
                    self.logger.warning(f"File object missing required key: {e}")
                    continue
                    
            # No matching file found
            self.logger.info(f"File '{filename}' not found")
            return False
            
        except Exception as e:
            self.logger.error(f"Unexpected error in delete_from_cloud: {e}", exc_info=True)
            return False
        
    def list_cloud_files(self, cid: str) -> List[str]:
        """
        List files in CrowdStrike cloud
        
        Args:
            cid: Customer ID
            
        Returns:
            List of file names
        """
        try:
            # Validate input
            if not cid:
                self.logger.error("CID cannot be empty")
                return []
                
            file_list = []
            
            # List put files
            response = self.rtr_client.list_put_files()
            
            if not response or 'body' not in response or 'resources' not in response['body']:
                self.logger.warning("Invalid response format from list_put_files")
                return []
                
            ids_list = response['body']['resources']
            
            if not ids_list:
                self.logger.info("No files found in put files repository")
                return []
                
            # Get detailed file information
            file_ids = self.rtr_client.get_put_files_v2(ids=ids_list)
            
            if not file_ids or 'body' not in file_ids or 'resources' not in file_ids['body']:
                self.logger.warning("Invalid response format from get_put_files_v2")
                return []
                
            # Extract file names
            for file in file_ids['body']['resources']:
                try:
                    if 'name' in file:
                        file_list.append(file['name'])
                    else:
                        self.logger.warning(f"File object missing 'name' key: {file}")
                except (TypeError, KeyError) as e:
                    self.logger.warning(f"Error processing file object: {e}")
                    continue
                    
            return file_list
            
        except Exception as e:
            self.logger.error(f"Unexpected error in list_cloud_files: {e}", exc_info=True)
            return []