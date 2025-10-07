"""
API client for CrowdStrike Hosts service.
"""

from typing import Dict, List, Optional
from falconpy import Hosts, ResponsePolicies
from fnerd_falconpy.core.base import ILogger, DefaultLogger


class HostsAPIClient:
    """Handles interactions with CrowdStrike Hosts API"""
    
    def __init__(self, client_id: str, client_secret: str, 
                 logger: Optional[ILogger] = None):
        """
        Initialize Hosts API client
        
        Args:
            client_id: CrowdStrike API client ID
            client_secret: CrowdStrike API client secret
            logger: Logger instance (uses DefaultLogger if not provided)
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.logger = logger or DefaultLogger("HostsAPIClient")
        self._hosts = None
        
    def initialize(self) -> None:
        """Initialize the Hosts API connection"""
        try:
            self._hosts = Hosts(client_id=self.client_id, client_secret=self.client_secret)
            self.logger.info("Successfully initialized Hosts API")
        except Exception as e:
            self.logger.error(f"Failed to initialize Hosts API: {e}")
            raise RuntimeError(f"Failed to initialize Hosts API: {e}")
            
    def get_device_details(self, ids: List[str]) -> Optional[Dict]:
        """
        Get device details for one or more hosts
        
        Args:
            ids: List of Agent IDs (AIDs)
            
        Returns:
            Response dictionary or None
        """
        try:
            if not self._hosts:
                raise RuntimeError("Hosts API not initialized")
                
            return self._hosts.get_device_details(ids=ids)
            
        except Exception as e:
            self.logger.error(f"Failed to get device details: {e}")
            return None
            
    def query_devices_by_filter(self, filter: str, limit: int = 100, 
                               offset: int = 0, sort: Optional[str] = None) -> Optional[Dict]:
        """
        Query devices by filter
        
        Args:
            filter: FQL filter string
            limit: Maximum number of results
            offset: Starting offset
            sort: Sort order
            
        Returns:
            Response dictionary or None
        """
        try:
            if not self._hosts:
                raise RuntimeError("Hosts API not initialized")
                
            return self._hosts.query_devices_by_filter(
                filter=filter,
                limit=limit,
                offset=offset,
                sort=sort
            )
            
        except Exception as e:
            self.logger.error(f"Failed to query devices: {e}")
            return None
            
    def perform_device_action_v2(self, action_name: str, ids: List[str]) -> Optional[Dict]:
        """
        Perform an action on one or more devices
        
        Args:
            action_name: Action to perform (contain, lift_containment, etc.)
            ids: List of Agent IDs (AIDs)
            
        Returns:
            Response dictionary or None
        """
        try:
            if not self._hosts:
                raise RuntimeError("Hosts API not initialized")
                
            return self._hosts.perform_action(
                action_name=action_name,
                ids=ids
            )
            
        except Exception as e:
            self.logger.error(f"Failed to perform device action: {e}")
            return None
            
    def update_device_tags(self, action: str, ids: List[str], tags: List[str]) -> Optional[Dict]:
        """
        Update tags on devices
        
        Args:
            action: 'add' or 'remove'
            ids: List of Agent IDs
            tags: List of tags
            
        Returns:
            Response dictionary or None
        """
        try:
            if not self._hosts:
                raise RuntimeError("Hosts API not initialized")
                
            return self._hosts.update_device_tags(
                action=action,
                body={
                    "ids": ids,
                    "tags": tags
                }
            )
            
        except Exception as e:
            self.logger.error(f"Failed to update device tags: {e}")
            return None


class ResponsePoliciesAPIClient:
    """Handles interactions with CrowdStrike Response Policies API"""
    
    def __init__(self, client_id: str, client_secret: str,
                 logger: Optional[ILogger] = None):
        """
        Initialize Response Policies API client
        
        Args:
            client_id: CrowdStrike API client ID
            client_secret: CrowdStrike API client secret
            logger: Logger instance (uses DefaultLogger if not provided)
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.logger = logger or DefaultLogger("ResponsePoliciesAPIClient")
        self._policies = None
        
    def initialize(self) -> None:
        """Initialize the Response Policies API connection"""
        try:
            self._policies = ResponsePolicies(
                client_id=self.client_id, 
                client_secret=self.client_secret
            )
            self.logger.info("Successfully initialized Response Policies API")
        except Exception as e:
            self.logger.error(f"Failed to initialize Response Policies API: {e}")
            raise RuntimeError(f"Failed to initialize Response Policies API: {e}")
            
    def query_response_policies(self, filter: Optional[str] = None, 
                               limit: int = 100, offset: int = 0) -> Optional[Dict]:
        """
        Query response policy IDs
        
        Args:
            filter: Optional FQL filter
            limit: Maximum results
            offset: Starting offset
            
        Returns:
            Response dictionary or None
        """
        try:
            if not self._policies:
                raise RuntimeError("Response Policies API not initialized")
                
            params = {"limit": limit, "offset": offset}
            if filter:
                params["filter"] = filter
                
            return self._policies.query_combined_policies(**params)
            
        except Exception as e:
            self.logger.error(f"Failed to query response policies: {e}")
            return None
            
    def get_response_policies(self, ids: List[str]) -> Optional[Dict]:
        """
        Get response policy details
        
        Args:
            ids: List of policy IDs
            
        Returns:
            Response dictionary or None
        """
        try:
            if not self._policies:
                raise RuntimeError("Response Policies API not initialized")
                
            return self._policies.get_policies(ids=ids)
            
        except Exception as e:
            self.logger.error(f"Failed to get response policies: {e}")
            return None
            
    def create_response_policies(self, body: Dict) -> Optional[Dict]:
        """
        Create new response policies
        
        Args:
            body: Policy data
            
        Returns:
            Response dictionary or None
        """
        try:
            if not self._policies:
                raise RuntimeError("Response Policies API not initialized")
                
            return self._policies.create_policies(body=body)
            
        except Exception as e:
            self.logger.error(f"Failed to create response policies: {e}")
            return None
            
    def update_response_policies(self, body: Dict) -> Optional[Dict]:
        """
        Update response policies
        
        Args:
            body: Policy update data
            
        Returns:
            Response dictionary or None
        """
        try:
            if not self._policies:
                raise RuntimeError("Response Policies API not initialized")
                
            return self._policies.update_policies(body=body)
            
        except Exception as e:
            self.logger.error(f"Failed to update response policies: {e}")
            return None
            
    def delete_response_policies(self, ids: List[str]) -> Optional[Dict]:
        """
        Delete response policies
        
        Args:
            ids: List of policy IDs to delete
            
        Returns:
            Response dictionary or None
        """
        try:
            if not self._policies:
                raise RuntimeError("Response Policies API not initialized")
                
            return self._policies.delete_policies(ids=ids)
            
        except Exception as e:
            self.logger.error(f"Failed to delete response policies: {e}")
            return None
            
    def query_response_policy_members(self, id: str, filter: Optional[str] = None,
                                     limit: int = 100, offset: int = 0) -> Optional[Dict]:
        """
        Query members of a response policy
        
        Args:
            id: Policy ID
            filter: Optional FQL filter
            limit: Maximum results
            offset: Starting offset
            
        Returns:
            Response dictionary or None
        """
        try:
            if not self._policies:
                raise RuntimeError("Response Policies API not initialized")
                
            params = {"id": id, "limit": limit, "offset": offset}
            if filter:
                params["filter"] = filter
                
            return self._policies.query_policy_members(**params)
            
        except Exception as e:
            self.logger.error(f"Failed to query policy members: {e}")
            return None