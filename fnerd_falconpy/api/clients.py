"""
API client classes for interacting with CrowdStrike Falcon APIs.
"""

from typing import Dict, List, Optional, Union
from falconpy import Discover, RealTimeResponse, RealTimeResponseAdmin
from fnerd_falconpy.core.base import ILogger, DefaultLogger

class DiscoverAPIClient:
    """Handles all interactions with CrowdStrike Discover API"""
    
    def __init__(self, client_id: str, client_secret: str, logger: Optional[ILogger] = None):
        """
        Initialize Discover API client
        
        Args:
            client_id: CrowdStrike API client ID
            client_secret: CrowdStrike API client secret
            logger: Logger instance (uses DefaultLogger if not provided)
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.logger = logger or DefaultLogger("DiscoverAPIClient")
        self._discover = None  # Will hold Discover instance
        
    def initialize(self) -> None:
        """Initialize the Discover API connection"""
        try:
            self._discover = Discover(client_id=self.client_id, client_secret=self.client_secret)
            self.logger.info("Successfully initialized Falcon Discover API")
        except Exception as e:
            self.logger.error(f"Failed to initialize Falcon Discover API: {e}")
            raise RuntimeError(f"Failed to initialize Falcon Discover API: {e}")
        
    def query_hosts(self, filter: str) -> Optional[List[str]]:
        """
        Query hosts by filter
        
        Args:
            filter: Query filter string
            
        Returns:
            List of host IDs or None if not found
        """
        try:
            if not self._discover:
                raise RuntimeError("Discover API not initialized")
                
            response = self._discover.query_hosts(filter=filter)
            
            if 'body' not in response:
                self.logger.warning(f"Invalid response format from query_hosts: {response}")
                return None
                
            if 'resources' not in response['body']:
                self.logger.warning("No 'resources' field in query_hosts response")
                return None
                
            resources = response['body']['resources']
            if not resources:
                self.logger.info(f"No hosts found for filter: {filter}")
                return None
                
            return resources
            
        except Exception as e:
            self.logger.error(f"Failed to query hosts: {e}")
            return None
        
    def get_host_details(self, host_ids: List[str]) -> Optional[Dict]:
        """
        Get detailed information for hosts
        
        Args:
            host_ids: List of host IDs
            
        Returns:
            Host details dictionary or None
        """
        try:
            if not self._discover:
                raise RuntimeError("Discover API not initialized")
                
            if not host_ids:
                self.logger.warning("No host IDs provided")
                return None
                
            response = self._discover.get_hosts(ids=host_ids)
            
            if 'body' not in response:
                self.logger.warning(f"Invalid response format from get_hosts: {response}")
                return None
                
            if 'resources' not in response['body'] or not response['body']['resources']:
                self.logger.warning("No host details returned from get_hosts")
                return None
                
            return response
            
        except Exception as e:
            self.logger.error(f"Failed to get host details: {e}")
            return None

class RTRAPIClient:
    """Handles all interactions with CrowdStrike RTR APIs"""
    
    def __init__(self, client_id: str, client_secret: str, member_cid: str, 
                 logger: Optional[ILogger] = None):
        """
        Initialize RTR API clients
        
        Args:
            client_id: CrowdStrike API client ID
            client_secret: CrowdStrike API client secret  
            member_cid: Member CID for RTR operations
            logger: Logger instance (uses DefaultLogger if not provided)
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.member_cid = member_cid
        self.logger = logger or DefaultLogger("RTRAPIClient")
        self._rtr = None  # Will hold RealTimeResponse instance
        self._rtr_admin = None  # Will hold RealTimeResponseAdmin instance
        
    def initialize(self) -> None:
        """Initialize RTR API connections"""
        try:
            # Initialize standard RTR client
            self._rtr = RealTimeResponse(
                client_id=self.client_id,
                client_secret=self.client_secret,
                member_cid=self.member_cid
            )
            
            # Initialize admin RTR client
            self._rtr_admin = RealTimeResponseAdmin(
                client_id=self.client_id,
                client_secret=self.client_secret,
                member_cid=self.member_cid
            )
            
            self.logger.info(f"Successfully initialized RTR clients for CID: {self.member_cid}")
            
        except AttributeError as e:
            self.logger.error(f"Missing required attributes for RTR initialization: {e}")
            raise RuntimeError(f"Missing required attributes for RTR initialization: {e}")
        except Exception as e:
            self.logger.error(f"Failed to initialize RTR clients: {e}")
            raise RuntimeError(f"Failed to initialize RTR clients: {e}")
        
    def init_session(self, device_id: str) -> Optional[Dict]:
        """Initialize RTR session"""
        try:
            if not self._rtr:
                raise RuntimeError("RTR client not initialized")
                
            return self._rtr.init_session(device_id=device_id)
            
        except Exception as e:
            self.logger.error(f"Error initializing RTR session: {e}")
            return None
        
    def delete_session(self, session_id: str) -> Optional[Dict]:
        """Delete RTR session"""
        try:
            if not self._rtr:
                raise RuntimeError("RTR client not initialized")
                
            return self._rtr.delete_session(session_id=session_id)
            
        except Exception as e:
            self.logger.error(f"Error deleting RTR session: {e}")
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
        
    def list_files_v2(self, session_id: str) -> Optional[Dict]:
        """List files in RTR session"""
        try:
            if not self._rtr:
                raise RuntimeError("RTR client not initialized")
                
            return self._rtr.list_files_v2(session_id=session_id)
            
        except Exception as e:
            self.logger.error(f"Failed to list session files: {e}")
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
            self.logger.error(f"Failed to get extracted file contents: {e}")
            return None
        
    # Admin-specific methods
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