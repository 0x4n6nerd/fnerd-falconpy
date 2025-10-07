"""
Response policy management for automated actions.
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from datetime import datetime

from fnerd_falconpy.core.base import ILogger, DefaultLogger


class PolicyAction(Enum):
    """Available policy actions"""
    ISOLATE = "isolate"
    NOTIFY = "notify"
    COLLECT_FORENSICS = "collect_forensics"
    KILL_PROCESS = "kill_process"
    DELETE_FILE = "delete_file"
    QUARANTINE_FILE = "quarantine_file"


@dataclass
class ResponsePolicy:
    """Response policy definition"""
    id: str
    name: str
    description: str
    enabled: bool
    priority: int
    conditions: Dict[str, any]  # Detection conditions
    actions: List[PolicyAction]  # Actions to take
    created_at: datetime
    updated_at: datetime
    
    
class ResponsePolicyManager:
    """Manages automated response policies"""
    
    def __init__(self, response_policies_client, logger: Optional[ILogger] = None):
        """
        Initialize policy manager
        
        Args:
            response_policies_client: FalconPy ResponsePolicies API client
            logger: Optional logger instance
        """
        self.policies_client = response_policies_client
        self.logger = logger or DefaultLogger("ResponsePolicyManager")
        
    def get_policies(self) -> List[ResponsePolicy]:
        """
        Retrieve all response policies
        
        Returns:
            List of ResponsePolicy objects
        """
        try:
            # Query policy IDs
            response = self.policies_client.query_response_policies(limit=500)
            
            if response and 'body' in response and 'resources' in response['body']:
                policy_ids = response['body']['resources']
                
                if policy_ids:
                    # Get policy details
                    details_response = self.policies_client.get_response_policies(ids=policy_ids)
                    
                    if details_response and 'body' in details_response and 'resources' in details_response['body']:
                        policies = []
                        
                        for policy_data in details_response['body']['resources']:
                            policy = self._parse_policy(policy_data)
                            if policy:
                                policies.append(policy)
                                
                        return policies
                        
            return []
            
        except Exception as e:
            self.logger.error(f"Error retrieving policies: {e}", exc_info=True)
            return []
            
    def get_policy(self, policy_id: str) -> Optional[ResponsePolicy]:
        """
        Get a specific policy by ID
        
        Args:
            policy_id: Policy ID
            
        Returns:
            ResponsePolicy object or None
        """
        try:
            response = self.policies_client.get_response_policies(ids=[policy_id])
            
            if response and 'body' in response and 'resources' in response['body']:
                resources = response['body']['resources']
                if resources and len(resources) > 0:
                    return self._parse_policy(resources[0])
                    
            return None
            
        except Exception as e:
            self.logger.error(f"Error retrieving policy {policy_id}: {e}")
            return None
            
    def create_policy(self, name: str, description: str, 
                     conditions: Dict, actions: List[str],
                     enabled: bool = True) -> Optional[ResponsePolicy]:
        """
        Create a new response policy
        
        Args:
            name: Policy name
            description: Policy description
            conditions: Detection conditions
            actions: List of actions to take
            enabled: Whether policy is enabled
            
        Returns:
            Created ResponsePolicy or None
        """
        try:
            policy_data = {
                "name": name,
                "description": description,
                "enabled": enabled,
                "settings": {
                    "conditions": conditions,
                    "actions": actions
                }
            }
            
            response = self.policies_client.create_response_policies(
                body={"resources": [policy_data]}
            )
            
            if response and response.get("status_code") == 201:
                # Get the created policy
                if 'body' in response and 'resources' in response['body']:
                    resources = response['body']['resources']
                    if resources and len(resources) > 0:
                        policy_id = resources[0].get('id')
                        if policy_id:
                            return self.get_policy(policy_id)
                            
            return None
            
        except Exception as e:
            self.logger.error(f"Error creating policy: {e}", exc_info=True)
            return None
            
    def update_policy(self, policy_id: str, updates: Dict) -> bool:
        """
        Update an existing policy
        
        Args:
            policy_id: Policy ID to update
            updates: Dictionary of updates
            
        Returns:
            True if successful
        """
        try:
            # Get current policy
            current_policy = self.get_policy(policy_id)
            if not current_policy:
                self.logger.error(f"Policy {policy_id} not found")
                return False
            
            # Prepare update data
            update_data = {
                "id": policy_id,
                "name": updates.get("name", current_policy.name),
                "description": updates.get("description", current_policy.description),
                "enabled": updates.get("enabled", current_policy.enabled)
            }
            
            # Add settings if provided
            if "conditions" in updates or "actions" in updates:
                update_data["settings"] = {}
                if "conditions" in updates:
                    update_data["settings"]["conditions"] = updates["conditions"]
                if "actions" in updates:
                    update_data["settings"]["actions"] = updates["actions"]
            
            response = self.policies_client.update_response_policies(
                body={"resources": [update_data]}
            )
            
            return response and response.get("status_code") == 200
            
        except Exception as e:
            self.logger.error(f"Error updating policy {policy_id}: {e}", exc_info=True)
            return False
            
    def delete_policy(self, policy_id: str) -> bool:
        """
        Delete a response policy
        
        Args:
            policy_id: Policy ID to delete
            
        Returns:
            True if successful
        """
        try:
            response = self.policies_client.delete_response_policies(ids=[policy_id])
            return response and response.get("status_code") == 200
            
        except Exception as e:
            self.logger.error(f"Error deleting policy {policy_id}: {e}", exc_info=True)
            return False
            
    def enable_policy(self, policy_id: str) -> bool:
        """
        Enable a response policy
        
        Args:
            policy_id: Policy ID to enable
            
        Returns:
            True if successful
        """
        return self.update_policy(policy_id, {"enabled": True})
        
    def disable_policy(self, policy_id: str) -> bool:
        """
        Disable a response policy
        
        Args:
            policy_id: Policy ID to disable
            
        Returns:
            True if successful
        """
        return self.update_policy(policy_id, {"enabled": False})
        
    def get_policy_members(self, policy_id: str) -> List[str]:
        """
        Get hosts assigned to a policy
        
        Args:
            policy_id: Policy ID
            
        Returns:
            List of host AIDs
        """
        try:
            response = self.policies_client.query_response_policy_members(
                id=policy_id,
                limit=1000
            )
            
            if response and 'body' in response and 'resources' in response['body']:
                return response['body']['resources']
                
            return []
            
        except Exception as e:
            self.logger.error(f"Error getting policy members: {e}", exc_info=True)
            return []
            
    def _parse_policy(self, policy_data: Dict) -> Optional[ResponsePolicy]:
        """Parse policy data into ResponsePolicy object"""
        try:
            # Extract settings
            settings = policy_data.get('settings', {})
            conditions = settings.get('conditions', {})
            actions = settings.get('actions', [])
            
            # Convert action strings to enums
            action_enums = []
            for action in actions:
                try:
                    action_enums.append(PolicyAction(action))
                except ValueError:
                    self.logger.warning(f"Unknown action: {action}")
                    
            return ResponsePolicy(
                id=policy_data.get('id', ''),
                name=policy_data.get('name', ''),
                description=policy_data.get('description', ''),
                enabled=policy_data.get('enabled', False),
                priority=policy_data.get('priority', 0),
                conditions=conditions,
                actions=action_enums,
                created_at=self._parse_timestamp(policy_data.get('created_timestamp')),
                updated_at=self._parse_timestamp(policy_data.get('modified_timestamp'))
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing policy data: {e}")
            return None
            
    def _parse_timestamp(self, timestamp_str: Optional[str]) -> datetime:
        """Parse timestamp string to datetime"""
        if not timestamp_str:
            return datetime.now()
            
        try:
            # Handle various timestamp formats
            # ISO format: 2023-01-01T00:00:00Z
            if 'T' in timestamp_str:
                return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            # Unix timestamp
            elif timestamp_str.isdigit():
                return datetime.fromtimestamp(int(timestamp_str))
            else:
                return datetime.now()
        except:
            return datetime.now()