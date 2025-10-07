#!/usr/bin/env python3
"""
Example usage of UAC (Unix-like Artifacts Collector) with fnerd-falconpy.

This example demonstrates how to use the UAC collector for forensic collection
on Unix/Linux/macOS systems.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from forensics_nerdstriker import FalconForensicOrchestrator, OptimizedFalconForensicOrchestrator
from forensics_nerdstriker.utils import load_environment


def run_single_host_uac_collection():
    """Example: Run UAC collection on a single host"""
    print("=== Single Host UAC Collection Example ===\n")
    
    # Load environment variables
    load_environment()
    
    # Get credentials
    client_id = os.getenv('FALCON_CLIENT_ID') or os.getenv('CLIENT_ID')
    client_secret = os.getenv('FALCON_CLIENT_SECRET') or os.getenv('CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("Error: Please set FALCON_CLIENT_ID and FALCON_CLIENT_SECRET environment variables")
        return
    
    # Initialize orchestrator
    orchestrator = FalconForensicOrchestrator(client_id, client_secret)
    
    # Target host and UAC profile
    hostname = "linux-server-01"  # Replace with actual hostname
    uac_profile = "ir_triage"  # Options: ir_triage, full, logs, memory_dump, network, files
    
    print(f"Running UAC collection on {hostname} with profile '{uac_profile}'...")
    
    # Run UAC collection
    success = orchestrator.run_uac_collection(
        hostname=hostname,
        profile=uac_profile,
        upload=True  # Upload to S3
    )
    
    if success:
        print(f"✓ UAC collection completed successfully for {hostname}")
    else:
        print(f"✗ UAC collection failed for {hostname}")


def run_batch_uac_collection():
    """Example: Run UAC collection on multiple hosts using batch operations"""
    print("\n=== Batch UAC Collection Example ===\n")
    
    # Load environment variables
    load_environment()
    
    # Get credentials
    client_id = os.getenv('FALCON_CLIENT_ID') or os.getenv('CLIENT_ID')
    client_secret = os.getenv('FALCON_CLIENT_SECRET') or os.getenv('CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("Error: Please set FALCON_CLIENT_ID and FALCON_CLIENT_SECRET environment variables")
        return
    
    # Initialize optimized orchestrator for batch operations
    orchestrator = OptimizedFalconForensicOrchestrator(
        client_id=client_id,
        client_secret=client_secret,
        max_concurrent_hosts=10,  # Process up to 10 hosts concurrently
        enable_caching=True
    )
    
    # Define targets (hostname, uac_profile)
    targets = [
        ("linux-web-01", "ir_triage"),
        ("linux-db-01", "full"),
        ("macos-dev-01", "logs"),
        ("linux-app-01", "network"),
        ("ubuntu-srv-01", "ir_triage"),
    ]
    
    print(f"Running batch UAC collection on {len(targets)} hosts...")
    
    # Run batch collection
    results = orchestrator.run_uac_batch(targets, upload_to_s3=True)
    
    # Display results
    print("\nResults:")
    for hostname, success in results.items():
        status = "✓" if success else "✗"
        print(f"  {status} {hostname}: {'Success' if success else 'Failed'}")
    
    # Summary
    success_count = sum(1 for v in results.values() if v)
    print(f"\nTotal: {success_count}/{len(results)} successful")


def run_mixed_platform_collection():
    """Example: Run appropriate collector based on platform (KAPE for Windows, UAC for others)"""
    print("\n=== Mixed Platform Collection Example ===\n")
    
    # Load environment variables
    load_environment()
    
    # Get credentials
    client_id = os.getenv('FALCON_CLIENT_ID') or os.getenv('CLIENT_ID')
    client_secret = os.getenv('FALCON_CLIENT_SECRET') or os.getenv('CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("Error: Please set FALCON_CLIENT_ID and FALCON_CLIENT_SECRET environment variables")
        return
    
    # Initialize orchestrator
    orchestrator = FalconForensicOrchestrator(client_id, client_secret)
    
    # List of hosts to process
    hosts = [
        "windows-srv-01",
        "linux-web-01",
        "macos-dev-01",
        "windows-dc-01",
        "ubuntu-app-01",
    ]
    
    print(f"Processing {len(hosts)} hosts with platform-appropriate collectors...\n")
    
    for hostname in hosts:
        # Get host info to determine platform
        host_info = orchestrator.get_host_info(hostname)
        
        if not host_info:
            print(f"✗ {hostname}: Host not found")
            continue
        
        platform = host_info.platform.lower()
        print(f"Processing {hostname} ({platform})...")
        
        if platform == "windows":
            # Use KAPE for Windows
            success = orchestrator.run_kape_collection(
                hostname=hostname,
                target="WebBrowsers",
                upload=True
            )
            collector = "KAPE"
        else:
            # Use UAC for Unix/Linux/macOS
            success = orchestrator.run_uac_collection(
                hostname=hostname,
                profile="ir_triage",
                upload=True
            )
            collector = "UAC"
        
        if success:
            print(f"  ✓ {collector} collection completed successfully")
        else:
            print(f"  ✗ {collector} collection failed")


def list_available_uac_profiles():
    """Example: Show available UAC profiles"""
    print("\n=== Available UAC Profiles ===\n")
    
    profiles = {
        "ir_triage": "Incident response triage - Quick collection of key artifacts",
        "full": "Complete forensic collection - All available artifacts",
        "logs": "System and application logs collection",
        "memory_dump": "Memory acquisition (requires memory tools on target)",
        "network": "Network configuration and active connections",
        "files": "File system artifacts and metadata",
        "offline": "Offline system analysis (mounted drives)",
    }
    
    print("Available UAC profiles for collection:\n")
    for profile, description in profiles.items():
        print(f"  • {profile}: {description}")
    
    print("\nUsage example:")
    print('  orchestrator.run_uac_collection(hostname="linux-01", profile="ir_triage")')


if __name__ == "__main__":
    print("fnerd-falconpy - UAC Collection Examples\n")
    print("This demonstrates UAC (Unix-like Artifacts Collector) usage.\n")
    
    # Run examples
    run_single_host_uac_collection()
    run_batch_uac_collection()
    run_mixed_platform_collection()
    list_available_uac_profiles()
    
    print("\n✓ Examples completed!")
    print("\nNote: UAC requires the UAC package to be placed in:")
    print("  falcon_client/resources/uac/uac.tar.gz")
    print("\nDownload UAC from: https://github.com/tclahr/uac/releases")