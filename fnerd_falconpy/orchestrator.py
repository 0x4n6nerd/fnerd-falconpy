"""
Main orchestrator that coordinates all components.
"""

from typing import Optional
from fnerd_falconpy.core.base import HostInfo, ILogger, DefaultLogger, Platform
from fnerd_falconpy.api.clients import DiscoverAPIClient, RTRAPIClient
from fnerd_falconpy.managers.managers import HostManager, SessionManager, FileManager
from fnerd_falconpy.collectors.collectors import BrowserHistoryCollector, ForensicCollector
from fnerd_falconpy.collectors.uac_collector import UACCollector
from fnerd_falconpy.utils.cloud_storage import CloudStorageManager
from fnerd_falconpy.core.configuration import Configuration
from fnerd_falconpy.api.hosts_client import HostsAPIClient, ResponsePoliciesAPIClient
from fnerd_falconpy.response.isolation import HostIsolationManager
from fnerd_falconpy.response.policies import ResponsePolicyManager

class FalconForensicOrchestrator:
    """Main orchestrator that coordinates all components
    
    This is the central control point for the Falcon forensic collection system.
    It manages the lifecycle of all API clients, collectors, and managers.
    The orchestrator handles:
    - Host discovery and connection management
    - RTR (Real Time Response) session management
    - Forensic collection orchestration (KAPE, UAC, browser history)
    - Cloud storage uploads to S3
    - Host isolation for incident response
    
    Architecture flow:
    CLI -> Orchestrator -> Collectors -> Managers -> API Clients
    """
    
    def __init__(self, client_id: str, client_secret: str, logger: Optional[ILogger] = None):
        """
        Initialize the orchestrator with all necessary components
        
        IMPORTANT: The orchestrator uses lazy initialization for RTR-dependent components
        because the CID (Customer ID) is not known until a specific host is targeted.
        Each CID requires its own RTR client context.
        
        Args:
            client_id: CrowdStrike API client ID (from environment variable FALCON_CLIENT_ID)
            client_secret: CrowdStrike API client secret (from environment variable FALCON_CLIENT_SECRET)
            logger: Optional logger instance (defaults to console logger)
        """
        # Use provided logger or create default console logger
        self.logger = logger or DefaultLogger("FalconForensicOrchestrator")
        
        # Initialize configuration from external config.yaml file
        # This loads S3 settings, proxy configuration, and dynamic host entries
        # File location: ./config.yaml or $FALCON_CONFIG_PATH
        self.config = Configuration()
        
        # Initialize API clients that work at parent CID level
        # These clients can see across all member CIDs in the organization
        
        # Discover API: Used to find hosts across all member CIDs
        self.discover_client = DiscoverAPIClient(client_id, client_secret, self.logger)
        self.discover_client.initialize()
        
        # Hosts API: Used for host isolation/containment actions
        self.hosts_client = HostsAPIClient(client_id, client_secret, self.logger)
        self.hosts_client.initialize()
        
        # Response Policies API: Used for creating/managing response policies
        self.policies_client = ResponsePoliciesAPIClient(client_id, client_secret, self.logger)
        self.policies_client.initialize()
        
        # RTR (Real Time Response) client: Must be initialized per member CID
        # This is why it starts as None - we don't know the CID until a host is selected
        # Each member CID (operating company) requires its own RTR context
        self.rtr_client = None
        
        # Initialize managers that don't require RTR
        # Host manager: Discovers and queries host information
        self.host_manager = HostManager(self.discover_client, self.logger)
        
        # These managers require RTR client, so initialized later per CID
        self.session_manager = None  # Manages RTR sessions with hosts
        self.file_manager = None     # Handles file uploads/downloads via RTR
        
        # Initialize collectors - these orchestrate forensic collections
        # They require RTR managers, so initialized later per CID
        self.browser_collector = None   # Collects browser history from Chrome, Firefox, Edge, etc.
        self.forensic_collector = None  # Runs KAPE (Windows) forensic collections
        # Note: uac_collector is added dynamically in initialize_for_host()
        
        # Initialize cloud storage for S3 uploads
        # Uses AWS credentials from environment variables:
        # AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY
        self.cloud_storage = CloudStorageManager(self.logger)
        
        # Initialize incident response managers
        # Isolation manager: Network containment of compromised hosts
        self.isolation_manager = HostIsolationManager(self.host_manager, self.hosts_client, self.logger)
        # Policy manager: Creates and applies response policies
        self.policy_manager = ResponsePolicyManager(self.policies_client, self.logger)
        
        # Cache for initialized CIDs to avoid re-initialization
        # Key optimization: RTR clients are expensive to create, so we cache per CID
        self._initialized_cids = set()
        
    def initialize_for_host(self, hostname: str) -> HostInfo:
        """
        Initialize all RTR-dependent components for a specific host.
        
        This method is called before any forensic collection or RTR operation.
        It performs lazy initialization of RTR components only when needed.
        
        IMPORTANT: In CrowdStrike's multi-tenant architecture:
        - Parent CID can see all hosts but cannot perform RTR operations
        - Member CID context is required for RTR operations
        - Each member CID represents an operating company/business unit
        - We cache initialized CIDs to avoid expensive re-initialization
        
        Args:
            hostname: Target hostname (case-insensitive, partial match supported)
            
        Returns:
            HostInfo object containing:
            - device_id: Unique CrowdStrike device identifier
            - hostname: Full hostname
            - platform: Operating system (Windows/Mac/Linux)
            - cid: Customer ID this host belongs to
            - last_seen: Last connection timestamp
            
        Raises:
            ValueError: If host not found in any CID
            RuntimeError: If RTR initialization fails
        """
        # Query host information from Discover API (searches all CIDs)
        host_info = self.host_manager.get_host_by_hostname(hostname)
        if not host_info:
            raise ValueError(f"Host '{hostname}' not found in any CID")
        
        # Check if we've already initialized RTR for this CID
        # This is a key optimization - RTR init takes 2-3 seconds per CID
        if host_info.cid not in self._initialized_cids:
            self.logger.info(f"Initializing RTR client for CID: {host_info.cid}")
            
            # Create RTR client with member CID context
            # This allows us to execute commands on hosts within this CID
            self.rtr_client = RTRAPIClient(
                self.discover_client.client_id,
                self.discover_client.client_secret,
                host_info.cid,  # CRITICAL: Must use member CID, not parent CID
                self.logger
            )
            self.rtr_client.initialize()
            
            # Initialize RTR session manager
            # Handles: Creating sessions, keeping them alive, executing commands
            self.session_manager = SessionManager(self.rtr_client, self.logger)
            
            # Initialize file manager for RTR file operations
            # Handles: File uploads (put), downloads (get), and SHA256 retrieval
            # CRITICAL: Has 5-hour timeout for large files (3.4GB+)
            self.file_manager = FileManager(
                self.rtr_client, 
                self.session_manager,
                self.logger
            )
            
            # Initialize forensic collectors for this CID
            
            # Browser history collector: Extracts history from Chrome, Firefox, Edge, Safari
            # Uses concurrent collection for speed
            self.browser_collector = BrowserHistoryCollector(
                self.file_manager,
                self.session_manager,
                self.config,  # Provides dynamic host entries for /etc/hosts
                self.logger
            )
            
            # KAPE forensic collector (Windows only)
            # Runs Kroll Artifact Parser and Extractor for Windows forensics
            # Supports 11 targets: EventLogs, Registry, MalwareAnalysis, etc.
            self.forensic_collector = ForensicCollector(
                self.file_manager,
                self.session_manager,
                self.cloud_storage,
                self.config,
                self.logger
            )
            
            # UAC collector (Unix/Linux/macOS only)
            # Unix-like Artifact Collector for non-Windows forensics
            # Supports 8 profiles: ir_triage, full, quick_triage_optimized, etc.
            self.uac_collector = UACCollector(
                self.file_manager,
                self.session_manager,
                self.cloud_storage,
                self.config,  # CRITICAL: Must pass config for S3 settings
                self.logger
            )
            
            # Mark this CID as initialized to avoid re-initialization
            self._initialized_cids.add(host_info.cid)
            
        return host_info
    
    def collect_browser_history(self, hostname: str, username: str) -> bool:
        """
        High-level method to collect browser history from a user's browsers.
        
        Collects from: Chrome, Firefox, Edge, Safari, Brave
        Uses concurrent collection for speed (all browsers in parallel)
        
        Process:
        1. Initialize RTR connection to host
        2. Upload browser collection scripts
        3. Execute collection for specified user
        4. Download collected history files
        5. Clean up remote artifacts
        
        Args:
            hostname: Target hostname (partial match supported)
            username: Windows/Unix username whose browser history to collect
            
        Returns:
            True if successful, False otherwise
        
        Example:
            orchestrator.collect_browser_history("DESKTOP-ABC123", "john.doe")
        """
        try:
            self.logger.info(f"Starting browser history collection for {username}@{hostname}")
            
            # Initialize RTR connection and components for the host's CID
            host_info = self.initialize_for_host(hostname)
            
            # Execute browser history collection
            # This handles all browser types concurrently
            success = self.browser_collector.collect_browser_history(host_info, username)
            
            if success:
                self.logger.info("Browser history collection completed successfully")
            else:
                self.logger.error("Browser history collection failed")
                
            return success
            
        except Exception as e:
            self.logger.error(f"Failed to collect browser history: {e}", exc_info=True)
            return False
    
    def run_kape_collection(self, hostname: str, target: str, upload: bool = True) -> bool:
        """
        High-level method to run KAPE (Kroll Artifact Parser) collection on Windows.
        
        KAPE is a powerful forensic tool that collects Windows artifacts.
        Validated targets (100% success rate):
        - Fast (7-8m): EventLogs, RegistryHives, MalwareAnalysis, EmergencyTriage
        - Medium (9-13m): FileSystem, USBDetective, WebBrowsers, RansomwareResponse
        - Large (16-35m): KapeTriage, !BasicCollection, !SANS_Triage
        
        Process:
        1. Check host is Windows
        2. Deploy KAPE to configured workspace
        3. Execute KAPE with specified target
        4. Monitor collection progress
        5. Upload to S3 or download locally based on 'upload' flag
        6. Clean up remote workspace
        
        Args:
            hostname: Target Windows hostname
            target: KAPE target name (e.g., "!SANS_Triage", "EventLogs")
                   Use ! prefix for compound targets
            upload: True = upload to S3, False = download to current directory
            
        Returns:
            True if successful, False otherwise
            
        Example:
            # Upload to S3
            orchestrator.run_kape_collection("DESKTOP-ABC", "!SANS_Triage", upload=True)
            # Download locally
            orchestrator.run_kape_collection("DESKTOP-ABC", "EventLogs", upload=False)
        """
        try:
            self.logger.info(f"Starting KAPE collection on {hostname} with target: {target}")
            
            # Initialize RTR for the host's CID
            host_info = self.initialize_for_host(hostname)
            
            # Run KAPE collection
            collection_file = self.forensic_collector.run_kape_collection(host_info, target)
            if not collection_file:
                self.logger.error("KAPE collection failed")
                return False
            
            self.logger.info(f"KAPE collection completed: {collection_file}")
            
            # Handle upload to S3 or local download based on user choice
            # NEW in v1.3.1: Added local download option (upload=False)
            if upload:
                self.logger.info("Uploading KAPE collection to cloud storage")
                # Upload to S3 bucket configured in config.yaml
                upload_success = self.forensic_collector.upload_kape_results(
                    host_info, 
                    collection_file
                )
                
                if not upload_success:
                    self.logger.error("Failed to upload KAPE collection")
                    return False
                    
                self.logger.info("KAPE collection uploaded successfully")
            else:
                self.logger.info("Downloading KAPE collection locally")
                # Download to current working directory
                # File will be saved as: YYYY-MM-DD_hostname-triage.zip
                download_success = self.forensic_collector.download_kape_results(
                    host_info,
                    collection_file
                )
                
                if not download_success:
                    self.logger.error("Failed to download KAPE collection")
                    return False
                    
                self.logger.info("KAPE collection downloaded successfully")
                
                
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to run KAPE collection: {e}", exc_info=True)
            return False
    
    def run_uac_collection(self, hostname: str, profile: str = "ir_triage", upload: bool = True) -> bool:
        """
        High-level method to run UAC (Unix-like Artifact Collector) on Unix/Linux/macOS.
        
        UAC is the Unix equivalent of KAPE for forensic collection.
        Validated profiles (all stable):
        - Fast (15-30m): quick_triage_optimized, network_compromise
        - Medium (35-50m): ir_triage_no_hash, malware_hunt_fast
        - Large (60-90m): ir_triage (default), full
        - Special: offline, offline_ir_triage (for offline analysis)
        
        Process:
        1. Check host is Unix/Linux/macOS (not Windows)
        2. Deploy UAC to configured workspace
        3. Execute UAC with specified profile
        4. Monitor collection progress (simplified commands to prevent timeout)
        5. Upload to S3 or download locally based on 'upload' flag
        6. Clean up remote workspace
        
        Args:
            hostname: Target Unix/Linux/macOS hostname
            profile: UAC profile name (default: "ir_triage")
                    Options: ir_triage, full, quick_triage_optimized, etc.
            upload: True = upload to S3, False = download to current directory
            
        Returns:
            True if successful, False otherwise
            
        Example:
            # Upload to S3
            orchestrator.run_uac_collection("mac-host", "ir_triage", upload=True)
            # Download locally
            orchestrator.run_uac_collection("linux-srv", "quick_triage_optimized", upload=False)
        """
        try:
            self.logger.info(f"Starting UAC collection on {hostname} with profile: {profile}")
            
            # Initialize for host
            host_info = self.initialize_for_host(hostname)
            
            # Check platform
            platform = Platform(host_info.platform.lower())
            if platform == Platform.WINDOWS:
                self.logger.error("UAC is not supported on Windows. Use KAPE instead.")
                return False
                
            # Run UAC collection
            collection_file = self.uac_collector.run_uac_collection(host_info, profile)
            if not collection_file:
                self.logger.error("UAC collection failed")
                return False
            
            self.logger.info(f"UAC collection completed: {collection_file}")
            
            # Handle upload to S3 or local download based on user choice
            # NEW in v1.3.1: Added local download option (upload=False)
            if upload:
                self.logger.info("Uploading UAC collection to cloud storage")
                # Upload to S3 bucket configured in config.yaml
                # Uses curl for upload (handles 4GB+ files)
                upload_success = self.uac_collector.upload_uac_results(
                    host_info,
                    collection_file
                )
                
                if not upload_success:
                    self.logger.error("Failed to upload UAC collection")
                    return False
                    
                self.logger.info("UAC collection uploaded successfully")
            else:
                self.logger.info("Downloading UAC collection locally")
                # Download to current working directory
                # File will be saved as: hostname_profile_YYYYMMDD.tar.gz
                download_success = self.uac_collector.download_uac_results(
                    host_info,
                    collection_file
                )
                
                if not download_success:
                    self.logger.error("Failed to download UAC collection")
                    return False
                    
                self.logger.info("UAC collection downloaded successfully")
                
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to run UAC collection: {e}", exc_info=True)
            return False
    
    def get_host_info(self, hostname: str) -> Optional[HostInfo]:
        """
        Get host information from CrowdStrike.
        
        Queries the Discover API to find host details across all member CIDs.
        This is useful for checking if a host exists before attempting operations.
        
        Args:
            hostname: Target hostname (partial match supported)
            
        Returns:
            HostInfo object containing device details, or None if not found
        """
        try:
            return self.host_manager.get_host_by_hostname(hostname)
        except Exception as e:
            self.logger.error(f"Failed to get host info: {e}", exc_info=True)
            return None
    
    def isolate_host(self, hostname: str, reason: Optional[str] = None):
        """
        Isolate a host (network containment) for incident response.
        
        Network isolation blocks all network traffic except:
        - CrowdStrike cloud communication
        - Essential Windows services (if Windows)
        
        Use this when a host is compromised and needs immediate containment.
        
        Args:
            hostname: Target hostname to isolate
            reason: Optional reason for isolation (logged for audit)
            
        Returns:
            IsolationResult object with status and details
            
        Example:
            result = orchestrator.isolate_host("infected-pc", "Ransomware detected")
        """
        return self.isolation_manager.isolate_host(hostname, reason)
    
    def release_host(self, hostname: str, reason: Optional[str] = None):
        """
        Release a host from network isolation.
        
        Restores full network connectivity to a previously isolated host.
        Use after incident remediation is complete.
        
        Args:
            hostname: Target hostname to release
            reason: Optional reason for release (logged for audit)
            
        Returns:
            IsolationResult object with status and details
            
        Example:
            result = orchestrator.release_host("infected-pc", "Remediation complete")
        """
        return self.isolation_manager.release_host(hostname, reason)
    
    def get_isolation_status(self, hostname: str):
        """
        Check if a host is currently isolated.
        
        Args:
            hostname: Target hostname to check
            
        Returns:
            IsolationStatus enum: ISOLATED, NOT_ISOLATED, or UNKNOWN
            
        Example:
            status = orchestrator.get_isolation_status("desktop-123")
            if status == IsolationStatus.ISOLATED:
                print("Host is currently isolated")
        """
        return self.isolation_manager.get_isolation_status(hostname)
    
    def get_isolated_hosts(self):
        """
        Get a list of all currently isolated hosts across all CIDs.
        
        Useful for incident response reporting and tracking containment status.
        
        Returns:
            List of host information dictionaries containing:
            - hostname: Host identifier
            - device_id: CrowdStrike device ID
            - isolation_status: Current status
            - last_seen: Last communication time
            
        Example:
            isolated = orchestrator.get_isolated_hosts()
            print(f"Currently {len(isolated)} hosts are isolated")
        """
        return self.isolation_manager.get_isolated_hosts()