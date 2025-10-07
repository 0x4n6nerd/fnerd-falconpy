"""
Device discovery module for querying and exporting device information from CrowdStrike Falcon.
"""

import json
import csv
import os
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Set, Tuple
from pathlib import Path
from falconpy import Hosts, FlightControl
from fnerd_falconpy.core.base import ILogger, DefaultLogger


class DeviceDiscovery:
    """Discovers and exports device information from CrowdStrike Falcon."""
    
    # OS platform mappings
    OS_FILTERS = {
        'windows': "platform_name:'Windows'",
        'mac': "platform_name:'Mac'",
        'macos': "platform_name:'Mac'",
        'linux': "platform_name:'Linux'"
    }
    
    # Fields to export for each device
    EXPORT_FIELDS = [
        'hostname',
        'device_id',
        'cid',
        'platform_name',
        'os_version',
        'agent_version',
        'local_ip',
        'external_ip',
        'mac_address',
        'last_seen',
        'status',
        'online_status',  # Calculated field based on last_seen
        'minutes_since_seen',  # How many minutes since last seen
        'product_type_desc',
        'system_manufacturer',
        'system_product_name',
        'tags',
        'groups'
    ]
    
    # Default online threshold in minutes (devices seen within this time are considered online)
    DEFAULT_ONLINE_THRESHOLD_MINUTES = 30
    
    def __init__(self, client_id: str, client_secret: str, logger: Optional[ILogger] = None,
                 online_threshold_minutes: int = None):
        """
        Initialize device discovery.
        
        Args:
            client_id: CrowdStrike API client ID
            client_secret: CrowdStrike API client secret
            logger: Logger instance
            online_threshold_minutes: Minutes threshold for online status (default: 30)
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.logger = logger or DefaultLogger("DeviceDiscovery")
        self.online_threshold_minutes = online_threshold_minutes or self.DEFAULT_ONLINE_THRESHOLD_MINUTES
        
        # Initialize API clients
        self.hosts_client = None
        self.flight_control_client = None
        self._initialized = False
        
    def initialize(self) -> None:
        """Initialize API clients."""
        if self._initialized:
            return
            
        try:
            # Initialize Hosts API client
            self.hosts_client = Hosts(
                client_id=self.client_id,
                client_secret=self.client_secret
            )
            self.logger.info("Initialized Hosts API client")
            
            # Try to initialize Flight Control for multi-CID scenarios
            try:
                self.flight_control_client = FlightControl(
                    client_id=self.client_id,
                    client_secret=self.client_secret
                )
                self.logger.info("Initialized Flight Control API client (multi-CID support)")
            except Exception as e:
                self.logger.info(f"Flight Control not available (single CID mode): {e}")
                self.flight_control_client = None
            
            self._initialized = True
            
        except Exception as e:
            self.logger.error(f"Failed to initialize API clients: {e}")
            raise RuntimeError(f"Failed to initialize API clients: {e}")
    
    def get_available_cids(self) -> Set[str]:
        """
        Get list of unique member CIDs by querying all devices and extracting their CIDs.
        
        Returns:
            Set of unique CID strings
        """
        self.initialize()
        
        cids = set()
        
        # Query a sample of devices to get their CIDs
        # The parent CID can see all devices, and each device has its member CID
        try:
            self.logger.info("Discovering available CIDs by querying devices...")
            
            # Query up to 5000 devices to get a good sample of CIDs
            response = self.hosts_client.query_devices_by_filter(limit=5000)
            if response and response.get('status_code') == 200:
                device_ids = response.get('body', {}).get('resources', [])
                
                if device_ids:
                    # Get details in batches to extract CIDs
                    batch_size = 100
                    for i in range(0, min(len(device_ids), 1000), batch_size):  # Sample up to 1000 devices
                        batch_ids = device_ids[i:i + batch_size]
                        
                        details_response = self.hosts_client.get_device_details_v2(ids=batch_ids)
                        if details_response and details_response.get('status_code') == 200:
                            devices = details_response.get('body', {}).get('resources', [])
                            
                            for device in devices:
                                device_cid = device.get('cid')
                                if device_cid:
                                    cids.add(device_cid)
                    
                    self.logger.info(f"Found {len(cids)} unique CID(s) from device query")
        except Exception as e:
            self.logger.error(f"Could not determine CIDs: {e}")
        
        if not cids:
            self.logger.warning("No CIDs found - will use 'default' placeholder")
            cids = {'default'}  # Use 'default' as placeholder
        
        return cids
    
    def query_devices_by_os(self, os_type: str, cid: Optional[str] = None, 
                           online_only: bool = True) -> Dict[str, List[Dict]]:
        """
        Query devices by operating system type and organize by member CID.
        
        Args:
            os_type: Operating system type (windows, mac, linux)
            cid: Optional specific CID to filter results
            online_only: If True, only return devices marked as online (seen within 30 minutes)
            
        Returns:
            Dictionary mapping member CID to list of device details
        """
        self.initialize()
        
        # Validate OS type
        os_type = os_type.lower()
        if os_type not in self.OS_FILTERS:
            raise ValueError(f"Invalid OS type: {os_type}. Must be one of: {list(self.OS_FILTERS.keys())}")
        
        # Build filter - don't use API's status field as it's unreliable
        filter_parts = [self.OS_FILTERS[os_type]]
        # Note: We don't add status:'online' to filter anymore since it's unreliable
        # We'll filter by calculated online_status instead
        filter_str = " + ".join(filter_parts)
        
        self.logger.info(f"Querying devices with filter: {filter_str}")
        
        # Query all devices matching the filter (parent CID sees all)
        all_devices = self._query_all_devices(filter_str)
        
        # Filter by online status if requested
        if online_only:
            self.logger.info(f"Filtering for online devices (seen within {self.online_threshold_minutes} minutes)")
            all_devices = [d for d in all_devices if d.get('online_status') == 'Online']
            self.logger.info(f"Found {len(all_devices)} online devices out of total queried")
        
        # Group devices by their member CID
        results = {}
        for device in all_devices:
            device_cid = device.get('cid')
            
            # If specific CID requested, filter to only that CID
            if cid and device_cid != cid:
                continue
            
            if device_cid:
                if device_cid not in results:
                    results[device_cid] = []
                results[device_cid].append(device)
        
        # Log summary with online/offline breakdown
        for member_cid, devices in results.items():
            online_count = sum(1 for d in devices if d.get('online_status') == 'Online')
            offline_count = sum(1 for d in devices if d.get('online_status') == 'Offline')
            unknown_count = sum(1 for d in devices if d.get('online_status') == 'Unknown')
            
            self.logger.info(f"CID {member_cid}: {len(devices)} {os_type} devices "
                           f"(Online: {online_count}, Offline: {offline_count}, Unknown: {unknown_count})")
        
        if not results:
            if cid:
                self.logger.info(f"No {os_type} devices found in CID {cid}")
            else:
                self.logger.info(f"No {os_type} devices found")
        
        return results
    
    def _query_all_devices(self, filter_str: str) -> List[Dict]:
        """
        Query all devices matching the filter from the parent CID.
        
        Args:
            filter_str: FQL filter string
            
        Returns:
            List of device details with their member CIDs
        """
        all_devices = []
        offset = 0
        limit = 5000  # Maximum allowed by API
        
        while True:
            try:
                # Query for device IDs from parent CID
                response = self.hosts_client.query_devices_by_filter(
                    filter=filter_str,
                    limit=limit,
                    offset=offset
                )
                
                if not response or response.get('status_code') != 200:
                    self.logger.error(f"Failed to query devices: {response}")
                    break
                
                device_ids = response.get('body', {}).get('resources', [])
                total = response.get('body', {}).get('meta', {}).get('pagination', {}).get('total', 0)
                
                if not device_ids:
                    break
                
                self.logger.info(f"Retrieved {len(device_ids)} device IDs (offset {offset}, total {total})")
                
                # Get device details in batches
                batch_size = 100  # API limit for device details
                for i in range(0, len(device_ids), batch_size):
                    batch_ids = device_ids[i:i + batch_size]
                    
                    details_response = self.hosts_client.get_device_details_v2(ids=batch_ids)
                    
                    if details_response and details_response.get('status_code') == 200:
                        devices = details_response.get('body', {}).get('resources', [])
                        
                        # Extract relevant fields
                        for device in devices:
                            device_info = {}
                            
                            # First extract basic fields (excluding calculated ones)
                            basic_fields = [f for f in self.EXPORT_FIELDS 
                                          if f not in ['online_status', 'minutes_since_seen']]
                            for field in basic_fields:
                                value = device.get(field, '')
                                # Handle list fields
                                if isinstance(value, list):
                                    value = ', '.join(str(v) for v in value)
                                device_info[field] = value
                            
                            # Calculate online status based on last_seen
                            online_status, minutes_since = self._calculate_online_status(device.get('last_seen'))
                            device_info['online_status'] = online_status
                            device_info['minutes_since_seen'] = minutes_since
                            
                            # Add computed fields
                            device_info['queried_at'] = datetime.utcnow().isoformat()
                            
                            # CID should come from the device itself (member CID)
                            # Each device knows which CID it belongs to
                            
                            all_devices.append(device_info)
                
                # Check if we've retrieved all devices
                offset += len(device_ids)
                if offset >= total:
                    break
                    
            except Exception as e:
                self.logger.error(f"Error querying devices: {e}")
                break
        
        return all_devices
    
    def _calculate_online_status(self, last_seen: str) -> Tuple[str, int]:
        """
        Calculate if a device is online based on last_seen timestamp.
        
        Args:
            last_seen: Last seen timestamp string from API
            
        Returns:
            Tuple of (online_status, minutes_since_seen)
            online_status: "Online", "Offline", or "Unknown"
            minutes_since_seen: Number of minutes since last seen (or -1 if unknown)
        """
        if not last_seen:
            return "Unknown", -1
        
        try:
            # Parse the last_seen timestamp
            # CrowdStrike uses ISO format: "2025-08-21T12:34:56Z"
            if last_seen.endswith('Z'):
                last_seen_dt = datetime.fromisoformat(last_seen.replace('Z', '+00:00'))
            else:
                last_seen_dt = datetime.fromisoformat(last_seen)
            
            # Ensure timezone awareness
            if last_seen_dt.tzinfo is None:
                last_seen_dt = last_seen_dt.replace(tzinfo=timezone.utc)
            
            # Calculate time difference
            now = datetime.now(timezone.utc)
            time_diff = now - last_seen_dt
            minutes_since = int(time_diff.total_seconds() / 60)
            
            # Determine online status based on threshold
            if minutes_since <= self.online_threshold_minutes:
                return "Online", minutes_since
            else:
                return "Offline", minutes_since
                
        except Exception as e:
            self.logger.debug(f"Error parsing last_seen timestamp '{last_seen}': {e}")
            return "Unknown", -1
    
    def export_to_csv(self, devices_by_cid: Dict[str, List[Dict]], 
                      os_type: str, output_dir: str = '.') -> List[str]:
        """
        Export devices to CSV files.
        
        Args:
            devices_by_cid: Dictionary mapping CID to list of devices
            os_type: Operating system type for filename
            output_dir: Directory to save files
            
        Returns:
            List of created file paths
        """
        created_files = []
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        for cid, devices in devices_by_cid.items():
            if not devices:
                continue
            
            # Create filename
            cid_label = cid if cid != 'default' else 'current'
            filename = f"{os_type}_devices_{cid_label}_{timestamp}.csv"
            filepath = os.path.join(output_dir, filename)
            
            try:
                with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                    # Get all unique fields from all devices
                    all_fields = set()
                    for device in devices:
                        all_fields.update(device.keys())
                    
                    # Sort fields with EXPORT_FIELDS first, then others
                    fieldnames = []
                    for field in self.EXPORT_FIELDS:
                        if field in all_fields:
                            fieldnames.append(field)
                    for field in sorted(all_fields):
                        if field not in fieldnames:
                            fieldnames.append(field)
                    
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(devices)
                
                self.logger.info(f"Exported {len(devices)} devices to {filepath}")
                created_files.append(filepath)
                
            except Exception as e:
                self.logger.error(f"Failed to export CSV for CID {cid}: {e}")
        
        return created_files
    
    def export_to_json(self, devices_by_cid: Dict[str, List[Dict]], 
                       os_type: str, output_dir: str = '.') -> List[str]:
        """
        Export devices to JSON files.
        
        Args:
            devices_by_cid: Dictionary mapping CID to list of devices
            os_type: Operating system type for filename
            output_dir: Directory to save files
            
        Returns:
            List of created file paths
        """
        created_files = []
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        for cid, devices in devices_by_cid.items():
            if not devices:
                continue
            
            # Create filename
            cid_label = cid if cid != 'default' else 'current'
            filename = f"{os_type}_devices_{cid_label}_{timestamp}.json"
            filepath = os.path.join(output_dir, filename)
            
            try:
                output_data = {
                    'cid': cid,
                    'os_type': os_type,
                    'query_time': datetime.utcnow().isoformat(),
                    'device_count': len(devices),
                    'devices': devices
                }
                
                with open(filepath, 'w', encoding='utf-8') as jsonfile:
                    json.dump(output_data, jsonfile, indent=2, default=str)
                
                self.logger.info(f"Exported {len(devices)} devices to {filepath}")
                created_files.append(filepath)
                
            except Exception as e:
                self.logger.error(f"Failed to export JSON for CID {cid}: {e}")
        
        return created_files
    
    def discover_and_export(self, os_type: str, cid: Optional[str] = None,
                           output_format: str = 'csv', output_dir: str = '.',
                           online_only: bool = True) -> Tuple[Dict[str, List[Dict]], List[str]]:
        """
        Discover devices and export to files.
        
        Args:
            os_type: Operating system type (windows, mac, linux)
            cid: Optional specific CID to query
            output_format: Export format (csv or json)
            output_dir: Directory to save files
            online_only: If True, only query online devices
            
        Returns:
            Tuple of (devices_by_cid dictionary, list of created file paths)
        """
        # Ensure output directory exists
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        
        # Query devices
        self.logger.info(f"Starting device discovery for {os_type} systems...")
        devices_by_cid = self.query_devices_by_os(os_type, cid, online_only)
        
        # Summary
        total_devices = sum(len(devices) for devices in devices_by_cid.values())
        self.logger.info(f"Found {total_devices} total devices across {len(devices_by_cid)} CID(s)")
        
        # Export based on format
        if output_format.lower() == 'json':
            created_files = self.export_to_json(devices_by_cid, os_type, output_dir)
        else:
            created_files = self.export_to_csv(devices_by_cid, os_type, output_dir)
        
        return devices_by_cid, created_files