#!/usr/bin/env python3
"""
Example usage of the RTR Interactive Session feature.

This script demonstrates how to use the RTR interactive session
both from the command line and programmatically.
"""

import os
from forensics_nerdstriker import FalconForensicOrchestrator, RTRInteractiveSession
from forensics_nerdstriker.utils import load_environment

# Load environment variables with smart path resolution
load_environment()


def example_command_line_usage():
    """Example: Using RTR from the command line."""
    print("RTR Command Line Usage Examples")
    print("=" * 50)
    
    print("\n1. Basic RTR session:")
    print("   falcon-client rtr -d HOSTNAME")
    
    print("\n2. With explicit credentials:")
    print("   falcon-client --client-id YOUR_ID --client-secret YOUR_SECRET rtr -d HOSTNAME")
    
    print("\n3. With debug logging:")
    print("   falcon-client --log-level DEBUG rtr -d HOSTNAME")
    
    print("\n4. With custom log file:")
    print("   falcon-client --log-file rtr_session.log rtr -d HOSTNAME")
    
    print("\nOnce in the RTR session, try these commands:")
    print("   help              - Show all available commands")
    print("   pwd               - Show current directory")
    print("   ls                - List files in current directory")
    print("   ps                - List running processes")
    print("   get <file>        - Retrieve a file")
    print("   files             - List retrieved files")
    print("   download <sha256> - Download retrieved file locally")
    print("   exit              - Exit the session")


def example_programmatic_usage():
    """Example: Using RTR programmatically in Python."""
    print("\n\nRTR Programmatic Usage Example")
    print("=" * 50)
    
    # Get credentials from environment (new variable names with fallback)
    client_id = os.getenv('FALCON_CLIENT_ID') or os.getenv('CLIENT_ID')
    client_secret = os.getenv('FALCON_CLIENT_SECRET') or os.getenv('CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("Error: Set FALCON_CLIENT_ID and FALCON_CLIENT_SECRET environment variables")
        print("(Legacy CLIENT_ID and CLIENT_SECRET are also supported)")
        return
    
    # Example code
    print("""
from forensics_nerdstriker import FalconForensicOrchestrator, RTRInteractiveSession

# Create orchestrator
orchestrator = FalconForensicOrchestrator(
    client_id=client_id,
    client_secret=client_secret
)

# Create RTR session
rtr_session = RTRInteractiveSession(orchestrator)

# Start interactive session
success = rtr_session.start("HOSTNAME")

if success:
    print("RTR session completed successfully")
else:
    print("RTR session failed")
""")


def example_custom_integration():
    """Example: Integrating RTR into a larger script."""
    print("\n\nCustom Integration Example")
    print("=" * 50)
    
    print("""
# Example: Incident response script with RTR

import sys
from forensics_nerdstriker import FalconForensicOrchestrator, RTRInteractiveSession

def investigate_host(hostname: str, orchestrator: FalconForensicOrchestrator):
    '''Perform initial investigation on a host'''
    
    print(f"Starting investigation of {hostname}")
    
    # 1. Collect browser history
    print("Collecting browser history...")
    orchestrator.collect_browser_history(hostname, "username")
    
    # 2. Run KAPE collection
    print("Running KAPE collection...")
    orchestrator.run_kape_collection(hostname, "BasicCollection")
    
    # 3. Start RTR session for manual investigation
    print("Starting RTR session for manual investigation...")
    rtr = RTRInteractiveSession(orchestrator)
    rtr.start(hostname)
    
    print("Investigation complete")

# Usage
if __name__ == "__main__":
    orchestrator = FalconForensicOrchestrator(
        client_id=os.getenv('FALCON_CLIENT_ID') or os.getenv('CLIENT_ID'),
        client_secret=os.getenv('FALCON_CLIENT_SECRET') or os.getenv('CLIENT_SECRET')
    )
    
    investigate_host(sys.argv[1], orchestrator)
""")


def example_automation():
    """Example: Automating RTR commands (future enhancement)."""
    print("\n\nFuture Enhancement: RTR Automation")
    print("=" * 50)
    
    print("""
# This is a conceptual example of how RTR could be extended
# for automation (not currently implemented)

class RTRAutomation:
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
    
    def collect_logs(self, hostname: str, log_paths: List[str]):
        '''Automatically collect specific log files'''
        
        # Start session
        session = self.orchestrator.session_manager.start_session(aid)
        
        # Retrieve each log file
        for log_path in log_paths:
            # Execute get command
            self.orchestrator.rtr_client.execute_active_responder_command(
                base_command="get",
                command_string=f"get {log_path}",
                device_id=aid,
                session_id=session.session_id
            )
        
        # Download all files
        files = self.orchestrator.rtr_client.list_files_v2(session.session_id)
        for file_info in files:
            # Download logic here
            pass
        
        # Clean up
        self.orchestrator.session_manager.end_session(session)

# Usage
automation = RTRAutomation(orchestrator)
automation.collect_logs(
    "HOSTNAME",
    [
        "C:\\\\Windows\\\\System32\\\\winevt\\\\Logs\\\\Security.evtx",
        "C:\\\\Windows\\\\System32\\\\winevt\\\\Logs\\\\System.evtx"
    ]
)
""")


def example_error_handling():
    """Example: Proper error handling in RTR sessions."""
    print("\n\nError Handling Best Practices")
    print("=" * 50)
    
    print("""
from forensics_nerdstriker import FalconForensicOrchestrator, RTRInteractiveSession
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # Create orchestrator
    orchestrator = FalconForensicOrchestrator(
        client_id=client_id,
        client_secret=client_secret
    )
    
    # Create RTR session with custom logger
    rtr_session = RTRInteractiveSession(orchestrator, logger=logger)
    
    # Start session with error handling
    try:
        success = rtr_session.start(hostname)
        if not success:
            logger.error(f"Failed to start RTR session for {hostname}")
            # Fallback to other collection methods
            
    except KeyboardInterrupt:
        logger.info("RTR session interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error in RTR session: {e}", exc_info=True)
        
except Exception as e:
    logger.error(f"Failed to initialize orchestrator: {e}")
    sys.exit(1)
""")


if __name__ == "__main__":
    print("fnerd-falconpy RTR Usage Examples")
    print("=" * 70)
    
    example_command_line_usage()
    example_programmatic_usage()
    example_custom_integration()
    example_automation()
    example_error_handling()
    
    print("\n" + "=" * 70)
    print("For more information, see:")
    print("- falcon_client/rtr/README.md")
    print("- docs/RTR_DEVELOPMENT_GUIDE.md")