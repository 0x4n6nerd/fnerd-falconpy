"""
Host isolation and containment management.
"""

import time
from typing import Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed

from fnerd_falconpy.core.base import HostInfo, ILogger, DefaultLogger
from fnerd_falconpy.managers.managers import HostManager


class IsolationAction(Enum):
    """Available isolation actions"""
    CONTAIN = "contain"
    LIFT_CONTAINMENT = "lift_containment"


class IsolationStatus(Enum):
    """Host isolation status"""
    NORMAL = "normal"
    CONTAINED = "contained"
    CONTAINING = "containing"  # In process of isolation
    LIFTING = "lifting"  # In process of un-isolation
    UNKNOWN = "unknown"


@dataclass
class IsolationResult:
    """Result of an isolation action"""
    hostname: str
    aid: str
    action: IsolationAction
    success: bool
    status: IsolationStatus
    message: str
    timestamp: datetime
    
    
@dataclass
class BatchIsolationResult:
    """Result of batch isolation operations"""
    total: int
    successful: int
    failed: int
    results: List[IsolationResult]
    duration: float
    
    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.total == 0:
            return 0.0
        return (self.successful / self.total) * 100


class HostIsolationManager:
    """Manages host isolation and containment actions"""
    
    def __init__(self, host_manager: HostManager, hosts_api_client,
                 logger: Optional[ILogger] = None):
        """
        Initialize isolation manager
        
        Args:
            host_manager: Host manager instance
            hosts_api_client: FalconPy Hosts API client
            logger: Optional logger instance
        """
        self.host_manager = host_manager
        self.hosts_client = hosts_api_client
        self.logger = logger or DefaultLogger("HostIsolationManager")
        
    def isolate_host(self, hostname: str, reason: Optional[str] = None) -> IsolationResult:
        """
        Isolate a single host (network containment)
        
        Args:
            hostname: Target hostname
            reason: Optional reason for isolation
            
        Returns:
            IsolationResult object
        """
        try:
            # Get host info
            host_info = self.host_manager.get_host_by_hostname(hostname)
            if not host_info:
                return IsolationResult(
                    hostname=hostname,
                    aid="",
                    action=IsolationAction.CONTAIN,
                    success=False,
                    status=IsolationStatus.UNKNOWN,
                    message=f"Host '{hostname}' not found",
                    timestamp=datetime.now()
                )
            
            # Log the action
            self.logger.info(f"Isolating host {hostname} (AID: {host_info.aid})")
            if reason:
                self.logger.info(f"Reason: {reason}")
            
            # Perform isolation
            response = self.hosts_client.perform_device_action_v2(
                action_name="contain",
                ids=[host_info.aid]
            )
            
            # Check response
            if response and response.get("status_code") == 202:
                # Action accepted
                return IsolationResult(
                    hostname=hostname,
                    aid=host_info.aid,
                    action=IsolationAction.CONTAIN,
                    success=True,
                    status=IsolationStatus.CONTAINING,
                    message="Isolation initiated successfully",
                    timestamp=datetime.now()
                )
            else:
                # Handle error
                error_msg = self._extract_error_message(response)
                return IsolationResult(
                    hostname=hostname,
                    aid=host_info.aid,
                    action=IsolationAction.CONTAIN,
                    success=False,
                    status=IsolationStatus.NORMAL,
                    message=f"Failed to isolate: {error_msg}",
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            self.logger.error(f"Error isolating host {hostname}: {e}", exc_info=True)
            return IsolationResult(
                hostname=hostname,
                aid=host_info.aid if 'host_info' in locals() else "",
                action=IsolationAction.CONTAIN,
                success=False,
                status=IsolationStatus.UNKNOWN,
                message=f"Error: {str(e)}",
                timestamp=datetime.now()
            )
            
    def release_host(self, hostname: str, reason: Optional[str] = None) -> IsolationResult:
        """
        Release a host from isolation (lift containment)
        
        Args:
            hostname: Target hostname
            reason: Optional reason for release
            
        Returns:
            IsolationResult object
        """
        try:
            # Get host info
            host_info = self.host_manager.get_host_by_hostname(hostname)
            if not host_info:
                return IsolationResult(
                    hostname=hostname,
                    aid="",
                    action=IsolationAction.LIFT_CONTAINMENT,
                    success=False,
                    status=IsolationStatus.UNKNOWN,
                    message=f"Host '{hostname}' not found",
                    timestamp=datetime.now()
                )
            
            # Log the action
            self.logger.info(f"Releasing host {hostname} from isolation (AID: {host_info.aid})")
            if reason:
                self.logger.info(f"Reason: {reason}")
            
            # Perform release
            response = self.hosts_client.perform_device_action_v2(
                action_name="lift_containment",
                ids=[host_info.aid]
            )
            
            # Check response
            if response and response.get("status_code") == 202:
                # Action accepted
                return IsolationResult(
                    hostname=hostname,
                    aid=host_info.aid,
                    action=IsolationAction.LIFT_CONTAINMENT,
                    success=True,
                    status=IsolationStatus.LIFTING,
                    message="Release initiated successfully",
                    timestamp=datetime.now()
                )
            else:
                # Handle error
                error_msg = self._extract_error_message(response)
                return IsolationResult(
                    hostname=hostname,
                    aid=host_info.aid,
                    action=IsolationAction.LIFT_CONTAINMENT,
                    success=False,
                    status=IsolationStatus.CONTAINED,
                    message=f"Failed to release: {error_msg}",
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            self.logger.error(f"Error releasing host {hostname}: {e}", exc_info=True)
            return IsolationResult(
                hostname=hostname,
                aid=host_info.aid if 'host_info' in locals() else "",
                action=IsolationAction.LIFT_CONTAINMENT,
                success=False,
                status=IsolationStatus.UNKNOWN,
                message=f"Error: {str(e)}",
                timestamp=datetime.now()
            )
            
    def get_isolation_status(self, hostname: str) -> IsolationStatus:
        """
        Check the current isolation status of a host
        
        Args:
            hostname: Target hostname
            
        Returns:
            IsolationStatus enum value
        """
        try:
            # Get host info
            host_info = self.host_manager.get_host_by_hostname(hostname)
            if not host_info:
                return IsolationStatus.UNKNOWN
            
            # Get current device details
            response = self.hosts_client.get_device_details(ids=[host_info.aid])
            
            if response and 'body' in response and 'resources' in response['body']:
                resources = response['body']['resources']
                if resources and len(resources) > 0:
                    device = resources[0]
                    
                    # Check containment status
                    containment_status = device.get('containment_status', 'normal')
                    
                    # Map to our enum
                    status_map = {
                        'normal': IsolationStatus.NORMAL,
                        'contained': IsolationStatus.CONTAINED,
                        'containing': IsolationStatus.CONTAINING,
                        'lifting': IsolationStatus.LIFTING
                    }
                    
                    return status_map.get(containment_status.lower(), IsolationStatus.UNKNOWN)
                    
            return IsolationStatus.UNKNOWN
            
        except Exception as e:
            self.logger.error(f"Error checking isolation status for {hostname}: {e}")
            return IsolationStatus.UNKNOWN
            
    def isolate_hosts_batch(self, hostnames: List[str], reason: Optional[str] = None,
                           max_concurrent: int = 10) -> BatchIsolationResult:
        """
        Isolate multiple hosts in batch
        
        Args:
            hostnames: List of hostnames to isolate
            reason: Optional reason for isolation
            max_concurrent: Maximum concurrent operations
            
        Returns:
            BatchIsolationResult object
        """
        start_time = time.time()
        results = []
        
        self.logger.info(f"Starting batch isolation for {len(hostnames)} hosts")
        
        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            # Submit all isolation tasks
            future_to_hostname = {
                executor.submit(self.isolate_host, hostname, reason): hostname
                for hostname in hostnames
            }
            
            # Collect results
            for future in as_completed(future_to_hostname):
                hostname = future_to_hostname[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    # Log progress
                    if result.success:
                        self.logger.info(f"✓ Successfully isolated {hostname}")
                    else:
                        self.logger.error(f"✗ Failed to isolate {hostname}: {result.message}")
                        
                except Exception as e:
                    self.logger.error(f"Exception isolating {hostname}: {e}")
                    results.append(IsolationResult(
                        hostname=hostname,
                        aid="",
                        action=IsolationAction.CONTAIN,
                        success=False,
                        status=IsolationStatus.UNKNOWN,
                        message=f"Exception: {str(e)}",
                        timestamp=datetime.now()
                    ))
        
        # Calculate summary
        duration = time.time() - start_time
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        
        return BatchIsolationResult(
            total=len(results),
            successful=successful,
            failed=failed,
            results=results,
            duration=duration
        )
        
    def release_hosts_batch(self, hostnames: List[str], reason: Optional[str] = None,
                           max_concurrent: int = 10) -> BatchIsolationResult:
        """
        Release multiple hosts from isolation in batch
        
        Args:
            hostnames: List of hostnames to release
            reason: Optional reason for release
            max_concurrent: Maximum concurrent operations
            
        Returns:
            BatchIsolationResult object
        """
        start_time = time.time()
        results = []
        
        self.logger.info(f"Starting batch release for {len(hostnames)} hosts")
        
        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            # Submit all release tasks
            future_to_hostname = {
                executor.submit(self.release_host, hostname, reason): hostname
                for hostname in hostnames
            }
            
            # Collect results
            for future in as_completed(future_to_hostname):
                hostname = future_to_hostname[future]
                try:
                    result = future.result()
                    results.append(result)
                    
                    # Log progress
                    if result.success:
                        self.logger.info(f"✓ Successfully released {hostname}")
                    else:
                        self.logger.error(f"✗ Failed to release {hostname}: {result.message}")
                        
                except Exception as e:
                    self.logger.error(f"Exception releasing {hostname}: {e}")
                    results.append(IsolationResult(
                        hostname=hostname,
                        aid="",
                        action=IsolationAction.LIFT_CONTAINMENT,
                        success=False,
                        status=IsolationStatus.UNKNOWN,
                        message=f"Exception: {str(e)}",
                        timestamp=datetime.now()
                    ))
        
        # Calculate summary
        duration = time.time() - start_time
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        
        return BatchIsolationResult(
            total=len(results),
            successful=successful,
            failed=failed,
            results=results,
            duration=duration
        )
        
    def isolate_by_detection(self, detection_id: str, auto_release_hours: Optional[int] = None) -> IsolationResult:
        """
        Isolate a host based on a detection ID
        
        Args:
            detection_id: Detection ID that triggered isolation
            auto_release_hours: Hours until automatic release (if implemented)
            
        Returns:
            IsolationResult object
        """
        # TODO: This would require integration with the Detects API
        # For now, this is a placeholder showing the interface
        raise NotImplementedError("Detection-based isolation requires Detects API integration")
        
    def schedule_release(self, hostname: str, release_time: datetime, reason: Optional[str] = None):
        """
        Schedule a future release from isolation
        
        Args:
            hostname: Target hostname
            release_time: When to release the host
            reason: Optional reason for scheduled release
        """
        # TODO: This would require a scheduling mechanism
        # For now, this is a placeholder showing the interface
        raise NotImplementedError("Scheduled release requires a task scheduling system")
        
    def get_isolated_hosts(self) -> List[Dict[str, str]]:
        """
        Get list of all currently isolated hosts
        
        Returns:
            List of dictionaries with host information
        """
        try:
            # Query for contained hosts
            response = self.hosts_client.query_devices_by_filter(
                filter="containment_status:'contained'",
                limit=500
            )
            
            if response and 'body' in response and 'resources' in response['body']:
                device_ids = response['body']['resources']
                
                if device_ids:
                    # Get details for all contained devices
                    details_response = self.hosts_client.get_device_details(ids=device_ids)
                    
                    if details_response and 'body' in details_response and 'resources' in details_response['body']:
                        isolated_hosts = []
                        
                        for device in details_response['body']['resources']:
                            isolated_hosts.append({
                                'hostname': device.get('hostname', ''),
                                'aid': device.get('device_id', ''),
                                'platform': device.get('platform_name', ''),
                                'os_version': device.get('os_version', ''),
                                'containment_status': device.get('containment_status', ''),
                                'last_seen': device.get('last_seen', '')
                            })
                            
                        return isolated_hosts
                        
            return []
            
        except Exception as e:
            self.logger.error(f"Error getting isolated hosts: {e}", exc_info=True)
            return []
            
    def _extract_error_message(self, response: Dict) -> str:
        """Extract error message from API response"""
        if not response:
            return "No response received"
            
        # Check for errors in body
        if 'body' in response and 'errors' in response['body']:
            errors = response['body']['errors']
            if errors and len(errors) > 0:
                return errors[0].get('message', 'Unknown error')
                
        # Check status code
        status_code = response.get('status_code', 0)
        if status_code >= 400:
            return f"HTTP {status_code} error"
            
        return "Unknown error"