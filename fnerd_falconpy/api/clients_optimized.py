"""
Optimized API client classes with batch operations support.
"""

from typing import Dict, List, Optional, Union, Tuple
from falconpy import Hosts, RealTimeResponse, RealTimeResponseAdmin
from fnerd_falconpy.core.base import ILogger, DefaultLogger
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

class OptimizedDiscoverAPIClient:
    """Optimized Discover API client with caching and pagination support"""
    
    def __init__(self, client_id: str, client_secret: str, logger: Optional[ILogger] = None):
        """
        Initialize Optimized Discover API client
        
        Args:
            client_id: CrowdStrike API client ID
            client_secret: CrowdStrike API client secret
            logger: Logger instance (uses DefaultLogger if not provided)
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.logger = logger or DefaultLogger("OptimizedDiscoverAPIClient")
        self._hosts = None  # Using Hosts service for better performance
        self._host_cache = {}  # Cache for host details
        self._cache_expiry = 300  # 5 minutes cache expiry
        self._last_cache_time = 0
        
    def initialize(self) -> None:
        """Initialize the Hosts API connection"""
        try:
            self._hosts = Hosts(client_id=self.client_id, client_secret=self.client_secret)
            self.logger.info("Successfully initialized Falcon Hosts API")
        except Exception as e:
            self.logger.error(f"Failed to initialize Falcon Hosts API: {e}")
            raise RuntimeError(f"Failed to initialize Falcon Hosts API: {e}")
    
    def query_hosts(self, filter: str) -> Optional[List[str]]:
        """
        Query hosts with a filter (compatibility method for HostManager)
        
        Args:
            filter: Query filter string
            
        Returns:
            List of host IDs or None if not found
        """
        try:
            if not self._hosts:
                raise RuntimeError("Hosts API not initialized")
            
            response = self._hosts.query_devices_by_filter(filter=filter, limit=100)
            
            if response.get('status_code') != 200:
                self.logger.error(f"Failed to query hosts: {response}")
                return None
            
            resources = response.get('body', {}).get('resources', [])
            if not resources:
                self.logger.info(f"No hosts found for filter: {filter}")
                return None
            
            return resources
            
        except Exception as e:
            self.logger.error(f"Failed to query hosts: {e}")
            return None
    
    def get_host_details(self, host_ids: List[str]) -> Optional[Dict]:
        """
        Get detailed information for hosts (compatibility method for HostManager)
        
        Args:
            host_ids: List of host IDs
            
        Returns:
            Host details dictionary or None
        """
        try:
            if not self._hosts:
                raise RuntimeError("Hosts API not initialized")
                
            if not host_ids:
                self.logger.warning("No host IDs provided")
                return None
                
            response = self._hosts.get_device_details(ids=host_ids)
            
            if response.get('status_code') != 200:
                self.logger.error(f"Failed to get host details: {response}")
                return None
                
            if 'body' not in response or 'resources' not in response['body']:
                self.logger.warning("Invalid response format from get_device_details")
                return None
                
            if not response['body']['resources']:
                self.logger.warning("No host details returned")
                return None
                
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to get host details: {e}")
            return None
    
    def query_hosts_scroll(self, filter: str, limit: int = 500) -> List[str]:
        """
        Query hosts using scroll pagination for large result sets
        
        Args:
            filter: Query filter string
            limit: Max hosts per page (max 500)
            
        Returns:
            Complete list of host IDs
        """
        try:
            if not self._hosts:
                raise RuntimeError("Hosts API not initialized")
            
            all_host_ids = []
            offset = None
            
            while True:
                # Use scroll endpoint for better performance
                response = self._hosts.query_devices_by_filter_scroll(
                    filter=filter,
                    limit=limit,
                    offset=offset
                )
                
                if response.get('status_code') != 200:
                    self.logger.error(f"Failed to query hosts: {response}")
                    break
                
                resources = response.get('body', {}).get('resources', [])
                if not resources:
                    break
                
                all_host_ids.extend(resources)
                
                # Get next page token
                meta = response.get('body', {}).get('meta', {})
                pagination = meta.get('pagination', {})
                offset = pagination.get('offset')
                
                if not offset:
                    break
                
                self.logger.debug(f"Retrieved {len(resources)} hosts, total so far: {len(all_host_ids)}")
            
            self.logger.info(f"Query complete. Total hosts found: {len(all_host_ids)}")
            return all_host_ids
            
        except Exception as e:
            self.logger.error(f"Failed to query hosts: {e}")
            return []
    
    def get_host_details_batch(self, host_ids: List[str], batch_size: int = 100) -> Dict[str, Dict]:
        """
        Get host details in batches for better performance
        
        Args:
            host_ids: List of host IDs
            batch_size: Number of hosts per API call (max 100)
            
        Returns:
            Dictionary mapping host ID to host details
        """
        try:
            if not self._hosts:
                raise RuntimeError("Hosts API not initialized")
            
            # Check cache first
            current_time = time.time()
            if current_time - self._last_cache_time < self._cache_expiry:
                cached_results = {}
                uncached_ids = []
                
                for host_id in host_ids:
                    if host_id in self._host_cache:
                        cached_results[host_id] = self._host_cache[host_id]
                    else:
                        uncached_ids.append(host_id)
                
                if not uncached_ids:
                    self.logger.info(f"All {len(host_ids)} hosts found in cache")
                    return cached_results
                
                host_ids = uncached_ids
                self.logger.info(f"Found {len(cached_results)} hosts in cache, fetching {len(host_ids)} from API")
            else:
                # Cache expired, clear it
                self._host_cache.clear()
                cached_results = {}
            
            # Fetch uncached hosts in batches
            all_hosts = {}
            
            for i in range(0, len(host_ids), batch_size):
                batch = host_ids[i:i + batch_size]
                
                response = self._hosts.get_device_details(ids=batch)
                
                if response.get('status_code') != 200:
                    self.logger.error(f"Failed to get host details: {response}")
                    continue
                
                resources = response.get('body', {}).get('resources', [])
                
                for host in resources:
                    host_id = host.get('device_id')
                    if host_id:
                        all_hosts[host_id] = host
                        self._host_cache[host_id] = host
                
                self.logger.debug(f"Retrieved details for {len(resources)} hosts")
            
            # Update cache timestamp
            if all_hosts:
                self._last_cache_time = current_time
            
            # Merge with cached results
            all_hosts.update(cached_results)
            
            return all_hosts
            
        except Exception as e:
            self.logger.error(f"Failed to get host details: {e}")
            return {}


class OptimizedRTRAPIClient:
    """Optimized RTR API client with batch operations support"""
    
    def __init__(self, client_id: str, client_secret: str, member_cid: str, 
                 logger: Optional[ILogger] = None):
        """
        Initialize Optimized RTR API clients
        
        Args:
            client_id: CrowdStrike API client ID
            client_secret: CrowdStrike API client secret  
            member_cid: Member CID for RTR operations
            logger: Logger instance
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.member_cid = member_cid
        self.logger = logger or DefaultLogger("OptimizedRTRAPIClient")
        self._rtr = None
        self._rtr_admin = None
        self._active_sessions = {}  # Track active sessions
        
    def initialize(self) -> None:
        """Initialize RTR API connections"""
        try:
            self._rtr = RealTimeResponse(
                client_id=self.client_id,
                client_secret=self.client_secret,
                member_cid=self.member_cid
            )
            
            self._rtr_admin = RealTimeResponseAdmin(
                client_id=self.client_id,
                client_secret=self.client_secret,
                member_cid=self.member_cid
            )
            
            self.logger.info(f"Successfully initialized RTR clients for CID: {self.member_cid}")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize RTR clients: {e}")
            raise RuntimeError(f"Failed to initialize RTR clients: {e}")
    
    def batch_init_sessions(self, device_ids: List[str], existing_session_ids: Optional[List[str]] = None) -> Dict[str, str]:
        """
        Initialize RTR sessions for multiple devices in batch
        
        Args:
            device_ids: List of device IDs
            existing_session_ids: Optional list of existing session IDs to refresh
            
        Returns:
            Dictionary mapping device ID to session ID
        """
        try:
            if not self._rtr:
                raise RuntimeError("RTR client not initialized")
            
            # Prepare batch init request
            body = {
                "host_ids": device_ids,
                "queue_offline": True
            }
            
            if existing_session_ids:
                body["existing_batch_id"] = existing_session_ids[0]  # Use first as batch ID
            
            response = self._rtr.batch_init_sessions(body=body)
            
            if response.get('status_code') != 201:
                self.logger.error(f"Failed to init batch sessions: {response}")
                return {}
            
            # Extract batch ID
            batch_id = response.get('body', {}).get('batch_id')
            if not batch_id:
                self.logger.error("No batch ID returned from batch_init_sessions")
                return {}
            
            # Get session info
            resources = response.get('body', {}).get('resources', {})
            
            sessions = {}
            for device_id in device_ids:
                device_info = resources.get(device_id, {})
                session_id = device_info.get('session_id')
                if session_id:
                    sessions[device_id] = session_id
                    self._active_sessions[device_id] = {
                        'session_id': session_id,
                        'batch_id': batch_id,
                        'timestamp': time.time()
                    }
                else:
                    self.logger.warning(f"No session ID for device {device_id}")
            
            self.logger.info(f"Initialized {len(sessions)} sessions in batch {batch_id}")
            return sessions
            
        except Exception as e:
            self.logger.error(f"Failed to init batch sessions: {e}")
            return {}
    
    def batch_refresh_sessions(self, batch_id: str) -> bool:
        """
        Refresh all sessions in a batch
        
        Args:
            batch_id: Batch ID to refresh
            
        Returns:
            True if successful
        """
        try:
            if not self._rtr:
                raise RuntimeError("RTR client not initialized")
            
            response = self._rtr.batch_refresh_sessions(
                batch_id=batch_id,
                hosts_to_remove=[]
            )
            
            if response.get('status_code') == 200:
                self.logger.info(f"Successfully refreshed batch {batch_id}")
                # Update timestamps
                current_time = time.time()
                for device_id, session_info in self._active_sessions.items():
                    if session_info.get('batch_id') == batch_id:
                        session_info['timestamp'] = current_time
                return True
            else:
                self.logger.error(f"Failed to refresh batch: {response}")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to refresh batch sessions: {e}")
            return False
    
    def batch_command(self, batch_id: str, base_command: str, command_string: str, 
                     device_ids: Optional[List[str]] = None) -> Dict[str, Dict]:
        """
        Execute command on multiple devices in batch
        
        Args:
            batch_id: Batch session ID
            base_command: Base RTR command
            command_string: Full command string
            device_ids: Optional list of specific device IDs (uses all if not provided)
            
        Returns:
            Dictionary mapping device ID to command result
        """
        try:
            if not self._rtr:
                raise RuntimeError("RTR client not initialized")
            
            body = {
                "base_command": base_command,
                "batch_id": batch_id,
                "command_string": command_string
            }
            
            if device_ids:
                body["optional_hosts"] = device_ids
            
            response = self._rtr.batch_command(body=body)
            
            if response.get('status_code') != 201:
                self.logger.error(f"Failed to execute batch command: {response}")
                return {}
            
            # Return the response for processing
            return response.get('body', {}).get('combined', {}).get('resources', {})
            
        except Exception as e:
            self.logger.error(f"Failed to execute batch command: {e}")
            return {}
    
    def batch_get_command(self, batch_id: str, file_path: str, 
                         device_ids: Optional[List[str]] = None) -> Tuple[str, Dict[str, str]]:
        """
        Get files from multiple devices in batch
        
        Args:
            batch_id: Batch session ID
            file_path: Path to file to retrieve
            device_ids: Optional list of specific device IDs
            
        Returns:
            Tuple of (batch_get_cmd_req_id, device_status_dict)
        """
        try:
            if not self._rtr:
                raise RuntimeError("RTR client not initialized")
            
            body = {
                "batch_id": batch_id,
                "file_path": file_path
            }
            
            if device_ids:
                body["optional_hosts"] = device_ids
            
            response = self._rtr.batch_get_command(body=body)
            
            if response.get('status_code') != 201:
                self.logger.error(f"Failed to execute batch get command: {response}")
                return "", {}
            
            # Extract batch get command request ID
            batch_get_cmd_req_id = response.get('body', {}).get('batch_get_cmd_req_id', '')
            
            # Extract device statuses
            resources = response.get('body', {}).get('combined', {}).get('resources', {})
            device_status = {}
            
            for device_id, info in resources.items():
                status = info.get('stdout', '')
                if 'error' in info:
                    status = f"Error: {info['error']}"
                device_status[device_id] = status
            
            return batch_get_cmd_req_id, device_status
            
        except Exception as e:
            self.logger.error(f"Failed to execute batch get command: {e}")
            return "", {}
    
    def batch_get_command_status(self, batch_get_cmd_req_id: str, timeout: int = 60) -> Dict[str, Dict]:
        """
        Check status of batch get command and retrieve results
        
        Args:
            batch_get_cmd_req_id: Batch get command request ID
            timeout: Timeout in seconds
            
        Returns:
            Dictionary mapping device ID to file info
        """
        try:
            if not self._rtr:
                raise RuntimeError("RTR client not initialized")
            
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                response = self._rtr.batch_get_command_status(
                    batch_get_cmd_req_id=batch_get_cmd_req_id
                )
                
                if response.get('status_code') != 200:
                    self.logger.error(f"Failed to get batch command status: {response}")
                    return {}
                
                resources = response.get('body', {}).get('resources', {})
                
                # Check if all files are ready
                all_ready = True
                for device_id, info in resources.items():
                    if not info.get('complete'):
                        all_ready = False
                        break
                
                if all_ready:
                    self.logger.info(f"All files ready for batch {batch_get_cmd_req_id}")
                    return resources
                
                # Wait before checking again
                time.sleep(2)
            
            self.logger.warning(f"Timeout waiting for batch get command: {batch_get_cmd_req_id}")
            return resources  # Return partial results
            
        except Exception as e:
            self.logger.error(f"Failed to get batch command status: {e}")
            return {}
    
    def cleanup_expired_sessions(self, max_age: int = 540):
        """
        Clean up sessions older than max_age seconds (default 9 minutes)
        
        Args:
            max_age: Maximum session age in seconds
        """
        current_time = time.time()
        expired_devices = []
        
        for device_id, session_info in self._active_sessions.items():
            if current_time - session_info['timestamp'] > max_age:
                expired_devices.append(device_id)
        
        for device_id in expired_devices:
            session_info = self._active_sessions.pop(device_id)
            self.logger.info(f"Removed expired session for device {device_id}")
        
        if expired_devices:
            self.logger.info(f"Cleaned up {len(expired_devices)} expired sessions")
    
    # Keep all the single-host methods from the original implementation
    def init_session(self, device_id: str) -> Optional[Dict]:
        """Initialize RTR session (single host)"""
        try:
            if not self._rtr:
                raise RuntimeError("RTR client not initialized")
            
            response = self._rtr.init_session(device_id=device_id)
            
            if response and response.get('status_code') == 201:
                resources = response.get('body', {}).get('resources', [])
                if resources:
                    session_id = resources[0].get('session_id')
                    if session_id:
                        self._active_sessions[device_id] = {
                            'session_id': session_id,
                            'batch_id': None,
                            'timestamp': time.time()
                        }
            
            return response
            
        except Exception as e:
            self.logger.error(f"Error initializing RTR session: {e}")
            return None
    
    def delete_session(self, session_id: str) -> Optional[Dict]:
        """Delete RTR session"""
        try:
            if not self._rtr:
                raise RuntimeError("RTR client not initialized")
            
            # Remove from active sessions
            for device_id, session_info in list(self._active_sessions.items()):
                if session_info.get('session_id') == session_id:
                    self._active_sessions.pop(device_id)
                    break
            
            return self._rtr.delete_session(session_id=session_id)
            
        except Exception as e:
            self.logger.error(f"Error deleting RTR session: {e}")
            return None
    
    # Include all other single-host methods from original implementation...
    def execute_command(self, session_id: str, base_command: str, command_string: str) -> Optional[Dict]:
        """Execute RTR command"""
        try:
            if not self._rtr:
                raise RuntimeError("RTR client not initialized")
                
            return self._rtr.execute_command(
                session_id=session_id,
                base_command=base_command,
                command_string=command_string
            )
            
        except Exception as e:
            self.logger.error(f"Failed to execute command: {e}")
            return None
    
    def execute_admin_command(self, session_id: str, base_command: str, command_string: str) -> Optional[Dict]:
        """Execute RTR admin command"""
        try:
            if not self._rtr_admin:
                raise RuntimeError("RTR admin client not initialized")
                
            return self._rtr_admin.execute_admin_command(
                session_id=session_id,
                base_command=base_command,
                command_string=command_string
            )
            
        except Exception as e:
            self.logger.error(f"Failed to execute admin command: {e}")
            return None
    
    def get_extracted_file_contents(self, session_id: str, sha256: str, filename: str) -> Optional[Union[bytes, Dict]]:
        """Get extracted file contents"""
        try:
            if not self._rtr:
                raise RuntimeError("RTR client not initialized")
                
            return self._rtr.get_extracted_file_contents(
                session_id=session_id,
                sha256=sha256,
                filename=filename
            )
            
        except Exception as e:
            self.logger.error(f"Failed to get file contents: {e}")
            return None
    
    def check_command_status(self, cloud_request_id: str, sequence_id: int = 0) -> Optional[Dict]:
        """Check command execution status"""
        try:
            if not self._rtr:
                raise RuntimeError("RTR client not initialized")
                
            return self._rtr.check_command_status(
                cloud_request_id=cloud_request_id,
                sequence_id=sequence_id
            )
            
        except Exception as e:
            self.logger.error(f"Failed to check command status: {e}")
            return None
    
    def check_admin_command_status(self, cloud_request_id: str, sequence_id: int = 0) -> Optional[Dict]:
        """Check admin command execution status"""
        try:
            if not self._rtr_admin:
                raise RuntimeError("RTR admin client not initialized")
                
            return self._rtr_admin.check_admin_command_status(
                cloud_request_id=cloud_request_id,
                sequence_id=sequence_id
            )
            
        except Exception as e:
            self.logger.error(f"Failed to check admin command status: {e}")
            return None
    
    def check_active_responder_command_status(self, cloud_request_id: str) -> Optional[Dict]:
        """Check active responder command status"""
        try:
            if not self._rtr:
                raise RuntimeError("RTR client not initialized")
                
            return self._rtr.check_active_responder_command_status(
                cloud_request_id=cloud_request_id
            )
            
        except Exception as e:
            self.logger.error(f"Failed to check active responder command status: {e}")
            return None
    
    def execute_active_responder_command(self, base_command: str, command_string: str,
                                       device_id: str, session_id: str) -> Optional[Dict]:
        """Execute active responder command (for file operations)"""
        try:
            if not self._rtr:
                raise RuntimeError("RTR client not initialized")
                
            return self._rtr.execute_active_responder_command(
                base_command=base_command,
                command_string=command_string,
                device_id=device_id,
                session_id=session_id
            )
            
        except Exception as e:
            self.logger.error(f"Failed to execute active responder command: {e}")
            return None
    
    def list_files_v2(self, session_id: str) -> Optional[Dict]:
        """List files in RTR session"""
        try:
            if not self._rtr:
                raise RuntimeError("RTR client not initialized")
                
            return self._rtr.list_files_v2(session_id=session_id)
            
        except Exception as e:
            self.logger.error(f"Failed to list session files: {e}")
            return None
    
    def pulse_session(self, device_id: str) -> Optional[Dict]:
        """Keep RTR session alive"""
        try:
            if not self._rtr:
                raise RuntimeError("RTR client not initialized")
                
            return self._rtr.pulse_session(device_id=device_id)
            
        except Exception as e:
            self.logger.warning(f"Session pulse failed: {e}")
            return None
    
    # Admin-specific methods for compatibility
    def list_put_files(self) -> Optional[Dict]:
        """List files in cloud repository"""
        try:
            if not self._rtr_admin:
                raise RuntimeError("RTR admin client not initialized")
                
            return self._rtr_admin.list_put_files()
            
        except Exception as e:
            self.logger.error(f"Failed to list put files: {e}")
            return None
    
    def get_put_files_v2(self, ids: List[str]) -> Optional[Dict]:
        """Get details of files in cloud repository"""
        try:
            if not self._rtr_admin:
                raise RuntimeError("RTR admin client not initialized")
                
            return self._rtr_admin.get_put_files_v2(ids=ids)
            
        except Exception as e:
            self.logger.error(f"Failed to get put files details: {e}")
            return None
    
    def create_put_files(self, comments_for_audit_log: str, description: str, 
                        name: str, files: List) -> Optional[Dict]:
        """Upload files to cloud repository"""
        try:
            if not self._rtr_admin:
                raise RuntimeError("RTR admin client not initialized")
                
            return self._rtr_admin.create_put_files(
                comments_for_audit_log=comments_for_audit_log,
                description=description,
                name=name,
                files=files
            )
            
        except Exception as e:
            self.logger.error(f"Failed to upload file: {e}")
            return None
    
    def delete_put_files(self, ids: str) -> Optional[Dict]:
        """Delete files from cloud repository"""
        try:
            if not self._rtr_admin:
                raise RuntimeError("RTR admin client not initialized")
                
            return self._rtr_admin.delete_put_files(ids=ids)
            
        except Exception as e:
            self.logger.error(f"Failed to delete put file: {e}")
            return None