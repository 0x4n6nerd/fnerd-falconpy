#!/usr/bin/env python3
"""
Example usage of the Device Discovery module.

This script demonstrates how to use the DeviceDiscovery class to:
1. Query devices by operating system
2. Filter by CID
3. Export results to CSV and JSON formats
"""

import os
import sys

# Add parent directory to path for development
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from forensics_nerdstriker.discovery import DeviceDiscovery


def discover_all_macs():
    """Discover all Mac devices across all CIDs"""
    
    # Initialize discovery with credentials
    discovery = DeviceDiscovery(
        client_id=os.environ['FALCON_CLIENT_ID'],
        client_secret=os.environ['FALCON_CLIENT_SECRET']
    )
    
    # Query all online Mac devices
    print("Discovering all online Mac devices...")
    devices_by_cid = discovery.query_devices_by_os('mac', online_only=True)
    
    # Export to CSV
    csv_files = discovery.export_to_csv(devices_by_cid, 'mac')
    
    # Print summary
    total = sum(len(devices) for devices in devices_by_cid.values())
    print(f"Found {total} Mac devices across {len(devices_by_cid)} CID(s)")
    print(f"Exported to: {csv_files}")


def discover_windows_in_cid(cid):
    """Discover Windows devices in a specific CID"""
    
    discovery = DeviceDiscovery(
        client_id=os.environ['FALCON_CLIENT_ID'],
        client_secret=os.environ['FALCON_CLIENT_SECRET']
    )
    
    # Query Windows devices in specific CID (including offline)
    print(f"Discovering Windows devices in CID {cid}...")
    devices_by_cid = discovery.query_devices_by_os(
        'windows', 
        cid=cid,
        online_only=False
    )
    
    # Export to JSON
    json_files = discovery.export_to_json(devices_by_cid, 'windows')
    
    # Print details
    for cid, devices in devices_by_cid.items():
        online = sum(1 for d in devices if d.get('status') == 'online')
        offline = len(devices) - online
        print(f"CID {cid}: {len(devices)} devices ({online} online, {offline} offline)")
        print(f"Exported to: {json_files}")


def discover_and_export_all():
    """Comprehensive discovery and export using the main method"""
    
    discovery = DeviceDiscovery(
        client_id=os.environ['FALCON_CLIENT_ID'],
        client_secret=os.environ['FALCON_CLIENT_SECRET']
    )
    
    # Discover all Linux devices and export to CSV
    print("Running comprehensive Linux discovery...")
    devices_by_cid, created_files = discovery.discover_and_export(
        os_type='linux',
        output_format='csv',
        output_dir='./discovery_results',
        online_only=True
    )
    
    print(f"Discovery complete. Files created: {created_files}")
    
    # Show sample data
    for cid, devices in devices_by_cid.items():
        if devices:
            print(f"\nSample from CID {cid}:")
            sample = devices[0]
            print(f"  Hostname: {sample.get('hostname')}")
            print(f"  OS: {sample.get('platform_name')} {sample.get('os_version')}")
            print(f"  Agent: {sample.get('agent_version')}")
            print(f"  IP: {sample.get('local_ip')}")


if __name__ == "__main__":
    # Example 1: Discover all Macs
    print("=" * 60)
    print("Example 1: Discover all Mac devices")
    print("=" * 60)
    discover_all_macs()
    
    print("\n" + "=" * 60)
    print("Example 2: Comprehensive Linux discovery")
    print("=" * 60)
    discover_and_export_all()
    
    # Example 3: Discover Windows in specific CID (if you know a CID)
    # Uncomment and replace with actual CID to test
    # print("\n" + "=" * 60)
    # print("Example 3: Discover Windows in specific CID")
    # print("=" * 60)
    # discover_windows_in_cid('your-cid-here')