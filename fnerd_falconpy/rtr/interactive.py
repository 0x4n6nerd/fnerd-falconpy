"""
Interactive RTR session implementation.
"""

import os
import sys
import time
import threading
import readline  # For command history
from typing import Optional, Dict, List
from pathlib import Path
from datetime import datetime

from fnerd_falconpy.core.base import (
    HostInfo, RTRSession, CommandResult,
    ILogger, DefaultLogger
)
from fnerd_falconpy.api.clients import RTRAPIClient
from fnerd_falconpy.managers.managers import SessionManager, FileManager
from fnerd_falconpy.orchestrator import FalconForensicOrchestrator
from .commands import RTRCommandParser, CommandType, RTRCommand


class RTRInteractiveSession:
    """Interactive RTR session handler"""
    
    def __init__(self, orchestrator: FalconForensicOrchestrator, 
                 logger: Optional[ILogger] = None):
        """
        Initialize interactive RTR session
        
        Args:
            orchestrator: Falcon forensic orchestrator instance
            logger: Optional logger instance
        """
        self.orchestrator = orchestrator
        self.logger = logger or DefaultLogger("RTRInteractiveSession")
        
        # Session state
        self.host_info: Optional[HostInfo] = None
        self.session: Optional[RTRSession] = None
        self.command_parser: Optional[RTRCommandParser] = None
        self.prompt_prefix = "RTR"
        self.working_directory = ""
        
        # Command history
        self.history_file = Path.home() / ".falcon_rtr_history"
        self._setup_readline()
        
        # File tracking for get commands
        self.retrieved_files: Dict[str, Dict] = {}  # sha256 -> file info
        
        # Session keepalive
        self._keepalive_running = False
        self._keepalive_thread = None
        
    def _setup_readline(self):
        """Setup readline for command history"""
        try:
            # Load history if it exists
            if self.history_file.exists():
                readline.read_history_file(str(self.history_file))
            
            # Set history length
            readline.set_history_length(1000)
            
            # Enable tab completion
            readline.parse_and_bind("tab: complete")
            readline.set_completer(self._completer)
            
        except Exception as e:
            self.logger.warning(f"Failed to setup readline: {e}")
            
    def _completer(self, text: str, state: int) -> Optional[str]:
        """Tab completion for commands"""
        if state == 0:
            # Build list of matches
            self.matches = []
            
            # Get available commands
            if self.command_parser:
                commands = self.command_parser.get_available_commands(include_admin=True)
                for cmd in commands:
                    if cmd.name.startswith(text.lower()):
                        self.matches.append(cmd.name)
                        
        try:
            return self.matches[state]
        except IndexError:
            return None
            
    def start(self, hostname: str) -> bool:
        """
        Start interactive RTR session
        
        Args:
            hostname: Target hostname
            
        Returns:
            True if session started successfully
        """
        try:
            # Banner
            self._print_banner()
            
            # Initialize host
            print(f"Connecting to {hostname}...")
            self.host_info = self.orchestrator.initialize_for_host(hostname)
            
            if not self.host_info:
                print(f"Error: Failed to find host '{hostname}'")
                return False
                
            print(f"✓ Connected to {self.host_info.hostname}")
            print(f"  Platform: {self.host_info.platform}")
            print(f"  OS: {self.host_info.os_name} {self.host_info.os_version}")
            print(f"  AID: {self.host_info.aid}")
            print()
            
            # Initialize command parser for platform
            platform = self.host_info.platform.lower()
            if platform not in ['windows', 'mac', 'linux']:
                # Map platform names
                if 'windows' in platform:
                    platform = 'windows'
                elif 'mac' in platform or 'darwin' in platform:
                    platform = 'mac'
                else:
                    platform = 'linux'
                    
            self.command_parser = RTRCommandParser(platform)
            
            # Start RTR session
            print("Initializing RTR session...")
            self.session = self.orchestrator.session_manager.start_session(self.host_info.aid)
            
            if not self.session:
                print("Error: Failed to initialize RTR session")
                return False
                
            print(f"✓ RTR session established (ID: {self.session.session_id[:8]}...)")
            print("\nType 'help' for available commands or 'exit' to quit\n")
            
            # Start session keepalive
            self._start_session_keepalive()
            
            # Run interactive loop
            self._run_interactive_loop()
            
            return True
            
        except KeyboardInterrupt:
            print("\n\nSession interrupted by user")
            return False
        except Exception as e:
            self.logger.error(f"Failed to start RTR session: {e}", exc_info=True)
            print(f"\nError: {e}")
            return False
        finally:
            self._cleanup()
            
    def _print_banner(self):
        """Print session banner"""
        print("\n" + "=" * 70)
        print("CrowdStrike Falcon RTR Interactive Session")
        print("=" * 70)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70 + "\n")
        
    def _run_interactive_loop(self):
        """Main interactive command loop"""
        while True:
            try:
                # Build prompt
                prompt = self._build_prompt()
                
                # Get user input
                try:
                    command_line = input(prompt).strip()
                except EOFError:
                    # Ctrl+D pressed
                    print()
                    break
                    
                if not command_line:
                    continue
                    
                # Parse command
                command, command_string = self.command_parser.parse_command(command_line)
                
                if not command:
                    # Error message is in command_string
                    print(command_string)
                    continue
                    
                # Handle local commands
                if command.command_type == CommandType.LOCAL:
                    if not self._handle_local_command(command, command_string):
                        break  # Exit requested
                    continue
                    
                # Execute RTR command
                self._execute_rtr_command(command, command_string)
                
            except KeyboardInterrupt:
                print("\nUse 'exit' or 'quit' to leave the session")
                continue
            except Exception as e:
                self.logger.error(f"Error in command loop: {e}", exc_info=True)
                print(f"Error: {e}")
                
    def _build_prompt(self) -> str:
        """Build command prompt"""
        if self.host_info:
            host_part = self.host_info.hostname.split('.')[0]  # Short hostname
        else:
            host_part = "unknown"
            
        if self.working_directory:
            dir_part = self.working_directory
        else:
            dir_part = "~"
            
        return f"{self.prompt_prefix} [{host_part}:{dir_part}]> "
        
    def _handle_local_command(self, command: RTRCommand, command_line: str) -> bool:
        """
        Handle local (non-RTR) commands
        
        Args:
            command: RTRCommand object
            command_line: Full command line
            
        Returns:
            True to continue, False to exit
        """
        parts = command_line.split(maxsplit=1)
        cmd_name = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        if cmd_name in ['exit', 'quit']:
            print("\nExiting RTR session...")
            return False
            
        elif cmd_name == 'help':
            help_text = self.command_parser.format_help(args if args else None)
            print(help_text)
            
        elif cmd_name == 'clear':
            os.system('clear' if os.name != 'nt' else 'cls')
            
        elif cmd_name == 'files':
            self._list_session_files()
            
        elif cmd_name == 'download':
            if args:
                self._download_file(args)
            else:
                print("Usage: download <sha256>")
                
        elif cmd_name == 'upload':
            if args:
                self._upload_file(args)
            else:
                print("Usage: upload <local_file_path>")
                
        return True
        
    def _execute_rtr_command(self, command: RTRCommand, command_string: str):
        """Execute RTR command and display results"""
        try:
            # Show what we're executing
            print(f"Executing: {command_string}")
            
            # Determine which API method to use
            if command.command_type == CommandType.READ_ONLY:
                # Standard command
                response = self.orchestrator.rtr_client.execute_command(
                    session_id=self.session.session_id,
                    base_command=command.base_command,
                    command_string=command_string
                )
            elif command.command_type == CommandType.ACTIVE_RESPONDER:
                # Active responder command
                if command.name == "get":
                    # Special handling for get command
                    self._handle_get_command(command_string)
                    return
                else:
                    response = self.orchestrator.rtr_client.execute_active_responder_command(
                        base_command=command.base_command,
                        command_string=command_string,
                        device_id=self.host_info.aid,
                        session_id=self.session.session_id
                    )
            else:  # ADMIN
                # Admin command
                response = self.orchestrator.rtr_client.execute_admin_command(
                    session_id=self.session.session_id,
                    base_command=command.base_command,
                    command_string=command_string
                )
                
            if not response:
                print("Error: No response from command execution")
                return
                
            # Check if we need to wait for command completion
            if response.get('status_code') == 201:
                # Command accepted, need to check status
                cloud_request_id = None
                sequence_id = 0
                
                # Extract cloud_request_id
                if 'body' in response and 'resources' in response['body']:
                    resources = response['body']['resources']
                    if resources and len(resources) > 0:
                        cloud_request_id = resources[0].get('cloud_request_id')
                        
                if cloud_request_id:
                    # Poll for completion
                    result = self._wait_for_command_completion(
                        cloud_request_id, 
                        sequence_id,
                        command.command_type
                    )
                    if result:
                        self._display_command_result(result)
                else:
                    print("Error: No cloud_request_id in response")
            else:
                # Direct response
                self._display_command_result(response)
                
            # Update working directory if cd command
            if command.name == "cd":
                parts = command_string.split(maxsplit=1)
                if len(parts) > 1:
                    self.working_directory = parts[1]
                    
        except Exception as e:
            self.logger.error(f"Failed to execute command: {e}", exc_info=True)
            print(f"Error executing command: {e}")
            
    def _wait_for_command_completion(self, cloud_request_id: str, sequence_id: int,
                                    command_type: CommandType) -> Optional[Dict]:
        """Wait for command to complete and return result"""
        max_attempts = 30  # 60 seconds timeout
        interval = 2
        
        print("Waiting for command to complete", end="", flush=True)
        
        for attempt in range(max_attempts):
            try:
                # Check status based on command type
                if command_type == CommandType.READ_ONLY:
                    status = self.orchestrator.rtr_client.check_command_status(
                        cloud_request_id=cloud_request_id,
                        sequence_id=sequence_id
                    )
                elif command_type == CommandType.ACTIVE_RESPONDER:
                    status = self.orchestrator.rtr_client.check_active_responder_command_status(
                        cloud_request_id=cloud_request_id
                    )
                else:  # ADMIN
                    status = self.orchestrator.rtr_client.check_admin_command_status(
                        cloud_request_id=cloud_request_id,
                        sequence_id=sequence_id
                    )
                    
                if status and 'body' in status and 'resources' in status['body']:
                    resources = status['body']['resources']
                    if resources and len(resources) > 0:
                        resource = resources[0]
                        if resource.get('complete', False):
                            print()  # New line after dots
                            return status
                            
                print(".", end="", flush=True)
                time.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"Error checking command status: {e}")
                
        print("\nCommand timed out")
        return None
        
    def _display_command_result(self, response: Dict):
        """Display command execution result"""
        try:
            if 'body' in response and 'resources' in response['body']:
                resources = response['body']['resources']
                if resources and len(resources) > 0:
                    resource = resources[0]
                    
                    # Get stdout and stderr
                    stdout = resource.get('stdout', '')
                    stderr = resource.get('stderr', '')
                    
                    # Display output
                    if stdout:
                        print(stdout)
                    if stderr:
                        print(f"[STDERR]: {stderr}", file=sys.stderr)
                        
                    # Check for errors
                    if 'errors' in resource and resource['errors']:
                        for error in resource['errors']:
                            print(f"[ERROR]: {error}")
                else:
                    print("No output from command")
            else:
                print(f"Unexpected response format: {response}")
                
        except Exception as e:
            self.logger.error(f"Error displaying command result: {e}")
            print(f"Error parsing command output: {e}")
            
    def _handle_get_command(self, command_string: str):
        """Special handling for get command"""
        try:
            # Parse the file path from command
            parts = command_string.split(maxsplit=1)
            if len(parts) < 2:
                print("Usage: get <file_path>")
                return
                
            file_path = parts[1]
            filename = os.path.basename(file_path)
            
            print(f"Retrieving file: {file_path}")
            
            # Execute get command
            response = self.orchestrator.rtr_client.execute_active_responder_command(
                base_command="get",
                command_string=command_string,
                device_id=self.host_info.aid,
                session_id=self.session.session_id
            )
            
            if not response:
                print("Error: No response from get command")
                return
                
            # Extract cloud request ID
            cloud_request_id = None
            if 'body' in response and 'resources' in response['body']:
                resources = response['body']['resources']
                if resources and len(resources) > 0:
                    cloud_request_id = resources[0].get('cloud_request_id')
                    
            if not cloud_request_id:
                print("Error: Failed to get cloud request ID")
                return
                
            # Wait for command completion
            print("Waiting for file transfer", end="", flush=True)
            result = self._wait_for_command_completion(
                cloud_request_id, 0, CommandType.ACTIVE_RESPONDER
            )
            
            if not result:
                print("\nError: File retrieval timed out")
                return
                
            # Check for errors in result
            if 'body' in result and 'resources' in result['body']:
                resources = result['body']['resources']
                if resources and len(resources) > 0:
                    resource = resources[0]
                    if resource.get('stderr'):
                        print(f"\nError: {resource['stderr']}")
                        return
                        
            # Now wait for the file to appear in the file list
            print("\nWaiting for file to be available in cloud storage", end="", flush=True)
            file_sha = None
            file_size = None  # Initialize as None to properly handle missing size
            
            # Poll for the file to appear
            for i in range(30):  # Wait up to 30 seconds
                files_resp = self.orchestrator.rtr_client.list_files_v2(
                    session_id=self.session.session_id
                )
                
                if files_resp and files_resp.get("status_code") == 200:
                    try:
                        files_list = files_resp["body"]["resources"]
                        for file_info in files_list:
                            if file_info.get("cloud_request_id") == cloud_request_id:
                                file_sha = file_info.get("sha256")
                                file_size = file_info.get("size")  # Don't default to 0, keep as None if missing
                                break
                    except (KeyError, IndexError):
                        pass
                        
                if file_sha:
                    break
                    
                print(".", end="", flush=True)
                time.sleep(1)
                
            print()  # New line
            
            if file_sha:
                # If we didn't get file size, try one more time with a fresh list
                if file_size is None:
                    time.sleep(2)  # Wait a bit for metadata to populate
                    files_resp = self.orchestrator.rtr_client.list_files_v2(
                        session_id=self.session.session_id
                    )
                    if files_resp and files_resp.get("status_code") == 200:
                        try:
                            files_list = files_resp["body"]["resources"]
                            for file_info in files_list:
                                if file_info.get("sha256") == file_sha:
                                    file_size = file_info.get("size")
                                    if file_size:
                                        self.logger.info(f"Retrieved file size on second attempt: {file_size}")
                                    break
                        except (KeyError, IndexError):
                            pass
                
                # Store file info
                self.retrieved_files[file_sha] = {
                    'filename': filename,
                    'path': file_path,
                    'timestamp': datetime.now(),
                    'size': file_size,
                    'cloud_request_id': cloud_request_id
                }
                
                # Format file size (handle None case)
                if file_size is not None and file_size > 0:
                    if file_size > 1024 * 1024:
                        size_str = f"{file_size / (1024 * 1024):.2f} MB"
                    elif file_size > 1024:
                        size_str = f"{file_size / 1024:.2f} KB"
                    else:
                        size_str = f"{file_size} bytes"
                else:
                    size_str = "Unknown"
                
                print(f"\n✓ File retrieved successfully")
                print(f"  Filename: {filename}")
                print(f"  SHA256: {file_sha}")
                print(f"  Size: {size_str}")
                print(f"\nUse 'download {file_sha}' to save the file locally")
                print("Or use 'files' to list all retrieved files\n")
            else:
                print("\nWarning: File was retrieved but SHA256 not found")
                print("Try 'files' command to check if it appears\n")
                            
        except Exception as e:
            self.logger.error(f"Error in get command: {e}", exc_info=True)
            print(f"Error executing get command: {e}")
            
    def _list_session_files(self):
        """List files in current RTR session"""
        try:
            response = self.orchestrator.rtr_client.list_files_v2(
                session_id=self.session.session_id
            )
            
            if response and 'body' in response and 'resources' in response['body']:
                resources = response['body']['resources']
                if resources and len(resources) > 0:
                    print("\nFiles in current session:")
                    print("-" * 70)
                    print(f"{'SHA256':<64} {'Filename':<30} {'Size':<10}")
                    print("-" * 70)
                    
                    for file_info in resources:
                        sha256 = file_info.get('sha256', '')
                        filename = file_info.get('name', 'unknown')
                        size = file_info.get('size', 0)
                        
                        # Update our tracking
                        if sha256 not in self.retrieved_files:
                            self.retrieved_files[sha256] = {
                                'filename': filename,
                                'size': size,
                                'timestamp': datetime.now()
                            }
                            
                        print(f"{sha256:<64} {filename:<30} {size:<10}")
                        
                    print()
                else:
                    print("\nNo files in current session")
            else:
                print("Error: Failed to list session files")
                
        except Exception as e:
            self.logger.error(f"Error listing files: {e}", exc_info=True)
            print(f"Error listing files: {e}")
            
    def _download_file(self, sha256: str):
        """Download a file from the session with .7z extension handling"""
        try:
            # Clean up SHA256 if needed
            sha256 = sha256.strip().lower()
            
            # Get file info from our tracking or from session
            file_info = self.retrieved_files.get(sha256)
            filename = "unknown"
            file_size = None  # Initialize as None
            
            if not file_info:
                # Try to get from current session files
                response = self.orchestrator.rtr_client.list_files_v2(
                    session_id=self.session.session_id
                )
                if response and 'body' in response and 'resources' in response['body']:
                    for res in response['body']['resources']:
                        if res.get('sha256') == sha256:
                            file_info = {
                                'filename': res.get('name', 'unknown'),
                                'size': res.get('size', 0)
                            }
                            break
                            
            if not file_info:
                print(f"Error: File with SHA256 {sha256} not found in session")
                return
                
            filename = file_info.get('filename', 'unknown')
            file_size = file_info.get('size')  # Can be None
            
            # Create downloads directory in current working directory
            download_dir = Path.cwd() / "rtr_downloads"
            download_dir.mkdir(exist_ok=True)
            
            print(f"Downloading {filename}...")
            if file_size is not None and file_size > 0:
                print(f"[*] File size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
                print("[*] Note: Large files may take several minutes...")
            else:
                print("[*] File size: Unknown")
                print("[*] Note: Download may take several minutes...")
            
            # Set up retry mechanism for large files
            max_retries = 120
            retry_count = 0
            file_content = None
            
            while retry_count < max_retries:
                file_content = self.orchestrator.rtr_client.get_extracted_file_contents(
                    session_id=self.session.session_id,
                    sha256=sha256,
                    filename=filename
                )
                
                if isinstance(file_content, bytes):
                    break
                    
                # Check for error response
                if isinstance(file_content, dict):
                    try:
                        error_message = file_content.get('body', {}).get('errors', [{}])[0].get('message')
                        if error_message == "Unknown file":
                            if retry_count % 10 == 0:  # Log every 10 attempts
                                print(f"[*] File not ready yet, continuing to wait... (attempt {retry_count + 1}/{max_retries})")
                    except Exception:
                        pass
                
                retry_count += 1
                time.sleep(5)  # Wait 5 seconds between retries
            
            if isinstance(file_content, bytes):
                # Adjust filename to use .7z extension for archives (CrowdStrike RTR converts to 7z)
                name_parts = os.path.splitext(filename)
                base_name = name_parts[0]
                original_ext = name_parts[1].lower() if name_parts[1] else ''
                
                # Check if file might be compressed and adjust extension
                compressed_extensions = ['.zip', '.tar', '.gz', '.vhdx', '.rar', '.bz2', '.7z']
                # Also check for compound extensions
                if original_ext in compressed_extensions or filename.lower().endswith('.tar.gz'):
                    # Replace with .7z if not already
                    if original_ext != '.7z':
                        output_filename = base_name + '.7z'
                    else:
                        output_filename = filename
                else:
                    # Check if it's likely a collection/triage archive
                    keywords = ['collection', 'triage', 'forensic', 'kape', 'uac', 'evidence']
                    if any(keyword in filename.lower() for keyword in keywords):
                        output_filename = base_name + '.7z'
                    else:
                        output_filename = filename  # Keep original for regular files
                
                output_path = download_dir / output_filename
                
                # Handle name conflicts
                counter = 1
                while output_path.exists():
                    name, ext = os.path.splitext(output_filename)
                    output_path = download_dir / f"{name}_{counter}{ext}"
                    counter += 1
                    
                # Write file
                output_path.write_bytes(file_content)
                
                # Verify file was written
                saved_size = output_path.stat().st_size
                print(f"✓ File saved to: {output_path}")
                print(f"[+] Downloaded size: {saved_size:,} bytes ({saved_size/1024/1024:.1f} MB)")
                
                if output_filename != filename:
                    print(f"[*] Note: File saved with .7z extension (CrowdStrike RTR automatic conversion)")
                    
            else:
                print(f"Error: Failed to download file content after {max_retries} attempts")
                print("[!] This may indicate the file is still being processed or is too large.")
                print("[!] Try again in a few minutes or contact support for large files.")
                
        except Exception as e:
            self.logger.error(f"Error downloading file: {e}", exc_info=True)
            print(f"Error downloading file: {e}")
            
    def _upload_file(self, file_path: str):
        """
        Upload a local file to CrowdStrike cloud storage
        
        Args:
            file_path: Path to local file to upload
        """
        try:
            # Resolve path
            path = Path(file_path).expanduser().resolve()
            
            if not path.exists():
                print(f"Error: File not found: {file_path}")
                return
                
            if not path.is_file():
                print(f"Error: Not a file: {file_path}")
                return
                
            # Get file size
            file_size = path.stat().st_size
            print(f"Uploading: {path.name} ({file_size:,} bytes)")
            
            # Upload to cloud
            print("Uploading to CrowdStrike cloud storage...")
            
            success = self.orchestrator.file_manager.upload_to_cloud(
                cid=self.host_info.cid,
                file_path=str(path),
                comments=f"RTR Interactive Upload: {path.name}",
                description=f"Uploaded via RTR session to {self.host_info.hostname}"
            )
            
            if success:
                print(f"✓ File uploaded successfully: {path.name}")
                print(f"  You can now use: put {path.name}")
                
                # Track uploaded files for this session
                if not hasattr(self, 'uploaded_files'):
                    self.uploaded_files = []
                self.uploaded_files.append(path.name)
            else:
                print(f"✗ Failed to upload file to cloud storage")
                
        except Exception as e:
            self.logger.error(f"Error uploading file: {e}", exc_info=True)
            print(f"Error uploading file: {e}")
            
    def _start_session_keepalive(self):
        """Start background thread to keep session alive"""
        def keepalive():
            self.logger.info("Starting session keepalive thread")
            while self._keepalive_running and self.session:
                try:
                    time.sleep(30)  # Pulse every 30 seconds
                    if self._keepalive_running and self.session:
                        self.orchestrator.session_manager.pulse_session(self.session)
                        self.logger.debug("Session pulse sent")
                except Exception as e:
                    self.logger.error(f"Error in keepalive thread: {e}")
                    # Don't crash the thread on errors
                    
        self._keepalive_running = True
        self._keepalive_thread = threading.Thread(target=keepalive, daemon=True)
        self._keepalive_thread.start()
        self.logger.info("Session keepalive started")
    
    def _cleanup(self):
        """Cleanup session resources"""
        try:
            # Stop keepalive thread
            self._keepalive_running = False
            if self._keepalive_thread:
                self._keepalive_thread.join(timeout=1)
                
            # Save command history
            try:
                readline.write_history_file(str(self.history_file))
            except:
                pass
                
            # Close RTR session
            if self.session and self.orchestrator.session_manager:
                print("\nClosing RTR session...")
                self.orchestrator.session_manager.end_session(self.session)
                print("✓ Session closed")
                
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")
            
        print("\nGoodbye!\n")