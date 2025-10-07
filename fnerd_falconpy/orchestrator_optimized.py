"""
Optimized orchestrator with batch operations support.

⚠️ WARNING: CONCURRENCY NOT WORKING PROPERLY

Despite the ThreadPoolExecutor implementation in this file, batch collections
are still running SEQUENTIALLY in testing. The concurrent execution is not
functioning as intended.

Known Issues:
- Batch collections process one host at a time (no parallelism)
- ThreadPoolExecutor code is present but not achieving concurrent execution
- Single host collections work perfectly
- No performance improvement over sequential execution

Workaround:
Run multiple instances of the tool manually in parallel:
  fnerd-falconpy kape -n 1 -d HOST1 -t "!SANS_Triage" &
  fnerd-falconpy kape -n 1 -d HOST2 -t "!SANS_Triage" &
  fnerd-falconpy kape -n 1 -d HOST3 -t "!SANS_Triage" &

TO FIX: Investigate why ThreadPoolExecutor isn't achieving parallelism.
Possible causes: RTR session locks, API rate limits, GIL, or cloud upload locks.
"""

from typing import Optional, List, Tuple, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import threading
from pathlib import Path
from fnerd_falconpy.core.base import HostInfo, ILogger, DefaultLogger, Platform
from fnerd_falconpy.api.clients_optimized import OptimizedDiscoverAPIClient, OptimizedRTRAPIClient
from fnerd_falconpy.managers.managers import HostManager, SessionManager, FileManager
from fnerd_falconpy.collectors.collectors import BrowserHistoryCollector, ForensicCollector
from fnerd_falconpy.collectors.uac_collector import UACCollector
from fnerd_falconpy.utils.cloud_storage import CloudStorageManager
from fnerd_falconpy.core.configuration import Configuration


class OptimizedFalconForensicOrchestrator:
    """Optimized orchestrator with batch operations and performance enhancements"""
    
    def __init__(self, client_id: str, client_secret: str, 
                 logger: Optional[ILogger] = None,
                 max_concurrent_hosts: int = 20,
                 enable_caching: bool = True,
                 batch_size: int = 100):
        """
        Initialize the optimized orchestrator
        
        ⚠️ NOTE: max_concurrent_hosts parameter currently has no effect.
        Concurrency is not working - collections run sequentially.
        
        Args:
            client_id: CrowdStrike API client ID
            client_secret: CrowdStrike API client secret
            logger: Optional logger instance
            max_concurrent_hosts: ⚠️ NOT WORKING - collections run sequentially
            enable_caching: Enable host details caching
            batch_size: Size for batch operations
        """
        self.logger = logger or DefaultLogger("OptimizedFalconForensicOrchestrator")
        self.max_concurrent_hosts = max_concurrent_hosts
        self.enable_caching = enable_caching
        self.batch_size = batch_size
        
        # Initialize configuration
        self.config = Configuration()
        
        # Initialize optimized API clients
        self.discover_client = OptimizedDiscoverAPIClient(
            client_id, client_secret, self.logger
        )
        self.discover_client.initialize()
        
        # RTR clients will be initialized per CID
        self.rtr_clients = {}  # CID -> OptimizedRTRAPIClient
        
        # Initialize managers (will be updated with RTR client later)
        self.host_manager = HostManager(self.discover_client, self.logger)
        self.session_managers = {}  # CID -> SessionManager
        self.file_managers = {}  # CID -> FileManager
        
        # Initialize collectors (will be created per CID)
        self.browser_collectors = {}  # CID -> BrowserHistoryCollector
        self.forensic_collectors = {}  # CID -> ForensicCollector
        self.uac_collectors = {}  # CID -> UACCollector
        
        # Initialize cloud storage
        self.cloud_storage = CloudStorageManager(self.logger)
        
        # Batch session tracking
        self._active_batches = {}  # batch_id -> {cid, device_ids, timestamp}
        
        # Track cloud files uploaded per CID to prevent duplicates
        self._cloud_files_uploaded = {}  # cid -> set of filenames
        self._cloud_upload_lock = threading.Lock()  # Thread-safe cloud uploads
    
    def _get_or_create_rtr_client(self, cid: str) -> OptimizedRTRAPIClient:
        """Get or create RTR client for a CID"""
        if cid not in self.rtr_clients:
            self.logger.info(f"Creating RTR client for CID: {cid}")
            
            rtr_client = OptimizedRTRAPIClient(
                self.discover_client.client_id,
                self.discover_client.client_secret,
                cid,
                self.logger
            )
            rtr_client.initialize()
            
            self.rtr_clients[cid] = rtr_client
            
            # Create managers for this CID
            self.session_managers[cid] = SessionManager(rtr_client, self.logger)
            self.file_managers[cid] = FileManager(
                rtr_client,
                self.session_managers[cid],
                self.logger
            )
            
            # Create collectors for this CID
            self.browser_collectors[cid] = BrowserHistoryCollector(
                self.file_managers[cid],
                self.session_managers[cid],
                self.config,
                self.logger
            )
            
            self.forensic_collectors[cid] = ForensicCollector(
                self.file_managers[cid],
                self.session_managers[cid],
                self.cloud_storage,
                self.config,
                self.logger
            )
            
            self.uac_collectors[cid] = UACCollector(
                self.file_managers[cid],
                self.session_managers[cid],
                self.cloud_storage,
                self.config,
                self.logger
            )
        
        return self.rtr_clients[cid]
    
    def run_kape_batch(self, targets: List[Tuple[str, str]], upload_to_s3: bool = True) -> Dict[str, bool]:
        """
        Run KAPE collection on multiple hosts in batch
        
        Args:
            targets: List of (hostname, kape_target) tuples
            upload_to_s3: Whether to upload results to S3
            
        Returns:
            Dictionary mapping hostname to success status
        """
        start_time = time.time()
        self.logger.info(f"Starting batch KAPE collection for {len(targets)} hosts")
        
        # Group hosts by CID
        hosts_by_cid = {}
        host_info_map = {}
        
        # Get host information for all hosts
        if self.enable_caching:
            # Get all host info at once with caching
            all_hostnames = [hostname for hostname, _ in targets]
            host_details = self._get_host_details_batch(all_hostnames)
            
            for hostname, kape_target in targets:
                host_info = host_details.get(hostname)
                if host_info:
                    cid = host_info.cid
                    if cid not in hosts_by_cid:
                        hosts_by_cid[cid] = []
                    hosts_by_cid[cid].append((hostname, kape_target, host_info))
                    host_info_map[hostname] = host_info
                else:
                    self.logger.error(f"Failed to get host info for {hostname}")
        else:
            # Fall back to individual lookups
            for hostname, kape_target in targets:
                host_info = self.host_manager.get_host_by_hostname(hostname)
                if host_info:
                    cid = host_info.cid
                    if cid not in hosts_by_cid:
                        hosts_by_cid[cid] = []
                    hosts_by_cid[cid].append((hostname, kape_target, host_info))
                    host_info_map[hostname] = host_info
                else:
                    self.logger.error(f"Failed to get host info for {hostname}")
        
        # Process each CID group
        results = {}
        
        with ThreadPoolExecutor(max_workers=min(len(hosts_by_cid), 5)) as executor:
            futures = {}
            
            for cid, cid_hosts in hosts_by_cid.items():
                future = executor.submit(
                    self._process_kape_batch_for_cid,
                    cid, cid_hosts, upload_to_s3
                )
                futures[future] = cid
            
            for future in as_completed(futures):
                cid = futures[future]
                try:
                    cid_results = future.result()
                    results.update(cid_results)
                except Exception as e:
                    self.logger.error(f"Failed to process CID {cid}: {e}")
                    # Mark all hosts in this CID as failed
                    for hostname, _, _ in hosts_by_cid[cid]:
                        results[hostname] = False
        
        elapsed = time.time() - start_time
        success_count = sum(1 for v in results.values() if v)
        
        self.logger.info(
            f"Batch KAPE collection completed in {elapsed:.1f}s. "
            f"Success: {success_count}/{len(targets)}"
        )
        
        return results
    
    def _upload_kape_cloud_files_once(self, cid: str, target: str) -> bool:
        """
        Upload KAPE cloud files once per CID (thread-safe)
        
        Args:
            cid: Customer ID
            target: KAPE target specification
            
        Returns:
            True if files already uploaded or upload successful, False otherwise
        """
        with self._cloud_upload_lock:
            # Check if files already uploaded for this CID
            if cid not in self._cloud_files_uploaded:
                self._cloud_files_uploaded[cid] = set()
            
            if 'kape.zip' in self._cloud_files_uploaded[cid]:
                self.logger.debug(f"Cloud files already uploaded for CID {cid}")
                return True
            
            # Need to upload files
            self.logger.info(f"Uploading KAPE cloud files for CID {cid}")
            
            # Get a forensic collector to prepare the package
            if cid not in self.forensic_collectors:
                self._get_or_create_rtr_client(cid)
            
            forensic_collector = self.forensic_collectors[cid]
            file_manager = self.file_managers[cid]
            
            # Prepare KAPE package
            from pathlib import Path
            kape_zip = forensic_collector.prepare_kape_package(target)
            
            # Get current cloud files
            cloud_files = file_manager.list_cloud_files(cid)
            
            # Delete existing kape.zip if present
            if 'kape.zip' in cloud_files:
                file_manager.delete_from_cloud(cid, 'kape.zip')
            
            # Upload kape.zip
            if not file_manager.upload_to_cloud(
                cid, 
                str(kape_zip), 
                'Kape Triage Tool Upload', 
                '4n6 Triage Tool'
            ):
                self.logger.error("Failed to upload kape.zip")
                return False
            
            # Delete existing deploy_kape.ps1 if present
            if 'deploy_kape.ps1' in cloud_files:
                file_manager.delete_from_cloud(cid, 'deploy_kape.ps1')
            
            # Upload deploy script
            try:
                # Try to use importlib.resources (Python 3.9+)
                try:
                    from importlib import resources
                    with resources.path('fnerd_falconpy.resources', 'deploy_kape.ps1') as p:
                        deploy_script = Path(p)
                except:
                    # Fallback to pkg_resources
                    import pkg_resources
                    deploy_script = Path(pkg_resources.resource_filename('fnerd_falconpy', 'resources/deploy_kape.ps1'))
            except:
                # Fallback for development
                package_root = Path(__file__).parent.parent
                deploy_script = package_root / "resources" / "deploy_kape.ps1"
            
            if not deploy_script.exists():
                self.logger.error("deploy_kape.ps1 not found")
                return False
            
            if not file_manager.upload_to_cloud(
                cid,
                str(deploy_script),
                'Kape Triage Execution Script',
                'Kape Launcher Script'
            ):
                self.logger.error("Failed to upload deploy_kape.ps1")
                return False
            
            # Mark files as uploaded
            self._cloud_files_uploaded[cid].add('kape.zip')
            self._cloud_files_uploaded[cid].add('deploy_kape.ps1')
            
            self.logger.info(f"Cloud files uploaded successfully for CID {cid}")
            return True
    
    def _process_kape_batch_for_cid(self, cid: str, 
                                   hosts: List[Tuple[str, str, HostInfo]], 
                                   upload_to_s3: bool) -> Dict[str, bool]:
        """Process KAPE collection for all hosts in a CID"""
        results = {}
        
        # Get RTR client for this CID
        rtr_client = self._get_or_create_rtr_client(cid)
        
        # Upload cloud files once for all hosts in this CID
        # Use the first host's target for preparation
        first_target = hosts[0][1] if hosts else "!BasicCollection"
        if not self._upload_kape_cloud_files_once(cid, first_target):
            self.logger.error(f"Failed to upload cloud files for CID {cid}")
            # Mark all hosts as failed
            for hostname, _, _ in hosts:
                results[hostname] = False
            return results
        
        # Extract device IDs
        device_ids = [host_info.aid for _, _, host_info in hosts]
        
        # Initialize batch sessions
        self.logger.info(f"Initializing batch sessions for {len(device_ids)} devices in CID {cid}")
        
        sessions = rtr_client.batch_init_sessions(device_ids)
        if not sessions:
            self.logger.error(f"Failed to initialize batch sessions for CID {cid}")
            for hostname, _, _ in hosts:
                results[hostname] = False
            return results
        
        # Get batch ID from first session
        batch_id = None
        for device_id, session_info in rtr_client._active_sessions.items():
            if device_id in device_ids:
                batch_id = session_info.get('batch_id')
                break
        
        if not batch_id:
            self.logger.error(f"No batch ID found for CID {cid}")
            for hostname, _, _ in hosts:
                results[hostname] = False
            return results
        
        # Store batch info
        self._active_batches[batch_id] = {
            'cid': cid,
            'device_ids': device_ids,
            'timestamp': time.time()
        }
        
        # Process KAPE collections in smaller groups
        batch_size = min(10, self.max_concurrent_hosts)
        
        for i in range(0, len(hosts), batch_size):
            batch_hosts = hosts[i:i + batch_size]
            
            # Run KAPE on this batch
            batch_results = self._run_kape_on_batch(
                cid, batch_id, batch_hosts, upload_to_s3
            )
            results.update(batch_results)
            
            # Refresh sessions if needed
            if i + batch_size < len(hosts):
                rtr_client.batch_refresh_sessions(batch_id)
        
        return results
    
    def _run_kape_on_batch(self, cid: str, batch_id: str,
                          hosts: List[Tuple[str, str, HostInfo]], 
                          upload_to_s3: bool) -> Dict[str, bool]:
        """Run KAPE on a batch of hosts"""
        results = {}
        forensic_collector = self.forensic_collectors[cid]
        
        # Use ThreadPoolExecutor for actual concurrency
        with ThreadPoolExecutor(max_workers=min(len(hosts), 10)) as executor:
            futures = {}
            
            for hostname, kape_target, host_info in hosts:
                future = executor.submit(
                    self._process_single_kape,
                    forensic_collector, hostname, kape_target, host_info, upload_to_s3
                )
                futures[future] = hostname
            
            for future in as_completed(futures):
                hostname = futures[future]
                try:
                    results[hostname] = future.result()
                except Exception as e:
                    self.logger.error(f"Failed to run KAPE on {hostname}: {e}")
                    results[hostname] = False
        
        return results
    
    def _process_single_kape(self, forensic_collector, hostname, kape_target, 
                             host_info, upload_to_s3):
        """Process a single KAPE collection (thread-safe)"""
        try:
            # Run KAPE collection WITHOUT cloud file upload (already done per CID)
            collection_file = self._run_kape_collection_no_upload(
                forensic_collector, host_info, kape_target
            )
            
            if collection_file and upload_to_s3:
                # Upload to S3
                return forensic_collector.upload_kape_results(host_info, collection_file)
            elif collection_file:
                # Download locally
                return forensic_collector.download_kape_results(host_info, collection_file)
            else:
                return False
        except Exception as e:
            self.logger.error(f"Error processing KAPE for {hostname}: {e}")
            raise
    
    def _run_kape_collection_no_upload(self, forensic_collector, host_info: HostInfo, target: str) -> Optional[str]:
        """
        Run KAPE collection WITHOUT uploading cloud files (for batch operations)
        Cloud files should be uploaded once per CID using _upload_kape_cloud_files_once
        
        This is a modified version of ForensicCollector.run_kape_collection that skips cloud upload
        """
        session = None
        try:
            # Start RTR session
            session = forensic_collector.session_manager.start_session(host_info.aid)
            if not session:
                self.logger.error("Failed to start RTR session")
                return None
            
            # Perform pre-execution cleanup
            self.logger.info("Performing pre-execution cleanup check...")
            if not forensic_collector.perform_pre_execution_cleanup(session, host_info):
                self.logger.error("Pre-execution cleanup failed")
                return None
            
            # Deploy KAPE on target (cloud files already uploaded)
            self.logger.info("Deploying KAPE on target host")
            if not forensic_collector.deploy_kape(session, host_info.platform):
                self.logger.error("Failed to deploy KAPE")
                return None
            
            # Execute KAPE (has its own monitoring with proper session management)
            self.logger.info(f"Starting KAPE collection with target: {target}")
            collection_file = forensic_collector.execute_kape(session, host_info)
            
            if not collection_file:
                self.logger.error("KAPE execution failed")
                return None
            
            self.logger.info(f"KAPE collection completed: {collection_file}")
            return collection_file
            
        except Exception as e:
            self.logger.error(f"Error during KAPE collection: {e}", exc_info=True)
            return None
        finally:
            # Clean up session
            if session:
                try:
                    forensic_collector.session_manager.end_session(session)
                except Exception as e:
                    self.logger.warning(f"Failed to close RTR session: {e}")
    
    def browser_history_batch(self, targets: List[Tuple[str, str]]) -> Dict[str, bool]:
        """
        Retrieve browser history from multiple hosts in batch
        
        Args:
            targets: List of (username, hostname) tuples
            
        Returns:
            Dictionary mapping "hostname:username" to success status
        """
        start_time = time.time()
        self.logger.info(f"Starting batch browser history collection for {len(targets)} targets")
        
        # Group by hostname to get host info efficiently
        hostname_map = {}
        for username, hostname in targets:
            if hostname not in hostname_map:
                hostname_map[hostname] = []
            hostname_map[hostname].append(username)
        
        # Get all host info
        host_details = self._get_host_details_batch(list(hostname_map.keys()))
        
        # Group by CID
        targets_by_cid = {}
        
        for hostname, usernames in hostname_map.items():
            host_info = host_details.get(hostname)
            if host_info:
                cid = host_info.cid
                if cid not in targets_by_cid:
                    targets_by_cid[cid] = []
                    
                for username in usernames:
                    targets_by_cid[cid].append((username, hostname, host_info))
            else:
                self.logger.error(f"Failed to get host info for {hostname}")
        
        # Process each CID
        results = {}
        
        with ThreadPoolExecutor(max_workers=min(len(targets_by_cid), 5)) as executor:
            futures = {}
            
            for cid, cid_targets in targets_by_cid.items():
                future = executor.submit(
                    self._process_browser_history_batch_for_cid,
                    cid, cid_targets
                )
                futures[future] = cid
            
            for future in as_completed(futures):
                cid = futures[future]
                try:
                    cid_results = future.result()
                    results.update(cid_results)
                except Exception as e:
                    self.logger.error(f"Failed to process CID {cid}: {e}")
                    for username, hostname, _ in targets_by_cid[cid]:
                        results[f"{hostname}:{username}"] = False
        
        elapsed = time.time() - start_time
        success_count = sum(1 for v in results.values() if v)
        
        self.logger.info(
            f"Batch browser history collection completed in {elapsed:.1f}s. "
            f"Success: {success_count}/{len(targets)}"
        )
        
        return results
    
    def _process_browser_history_batch_for_cid(self, cid: str,
                                             targets: List[Tuple[str, str, HostInfo]]) -> Dict[str, bool]:
        """Process browser history collection for all targets in a CID"""
        results = {}
        
        # Ensure RTR client and collectors exist for this CID
        self._get_or_create_rtr_client(cid)
        browser_collector = self.browser_collectors[cid]
        
        # Use ThreadPoolExecutor for actual concurrency
        with ThreadPoolExecutor(max_workers=min(len(targets), 10)) as executor:
            futures = {}
            
            for username, hostname, host_info in targets:
                future = executor.submit(
                    self._process_single_browser_history,
                    browser_collector, username, hostname, host_info
                )
                futures[future] = f"{hostname}:{username}"
            
            for future in as_completed(futures):
                key = futures[future]
                try:
                    results[key] = future.result()
                except Exception as e:
                    hostname = key.split(':')[0]
                    username = key.split(':')[1]
                    self.logger.error(f"Failed to collect browser history for {username}@{hostname}: {e}")
                    results[key] = False
        
        return results
    
    def _process_single_browser_history(self, browser_collector, username, hostname, host_info):
        """Process a single browser history collection (thread-safe)"""
        try:
            return browser_collector.collect_browser_history(host_info, username)
        except Exception as e:
            self.logger.error(f"Error collecting browser history for {username}@{hostname}: {e}")
            raise
    
    def _get_host_details_batch(self, hostnames: List[str]) -> Dict[str, HostInfo]:
        """Get host details for multiple hostnames efficiently"""
        # Fall back to individual lookups for reliability
        # Batch lookup can be complex with filter expressions
        result = {}
        
        for hostname in hostnames:
            host_info = self.host_manager.get_host_by_hostname(hostname)
            if host_info:
                result[hostname] = host_info
        
        return result
    
    def run_uac_batch(self, targets: List[Tuple[str, str]], upload_to_s3: bool = True) -> Dict[str, bool]:
        """
        Run UAC collection on multiple Unix/Linux/macOS hosts in batch
        
        Args:
            targets: List of (hostname, uac_profile) tuples
            upload_to_s3: Whether to upload results to S3
            
        Returns:
            Dictionary mapping hostname to success status
        """
        start_time = time.time()
        self.logger.info(f"Starting batch UAC collection for {len(targets)} hosts")
        
        # Group hosts by CID
        hosts_by_cid = {}
        host_info_map = {}
        
        # Get host information for all hosts
        if self.enable_caching:
            # Get all host info at once with caching
            all_hostnames = [hostname for hostname, _ in targets]
            host_details = self._get_host_details_batch(all_hostnames)
            
            for hostname, uac_profile in targets:
                host_info = host_details.get(hostname)
                if host_info:
                    # Check platform - UAC only works on non-Windows
                    platform = Platform(host_info.platform.lower())
                    if platform == Platform.WINDOWS:
                        self.logger.error(f"UAC not supported on Windows host {hostname}. Use KAPE instead.")
                        continue
                        
                    cid = host_info.cid
                    if cid not in hosts_by_cid:
                        hosts_by_cid[cid] = []
                    hosts_by_cid[cid].append((hostname, uac_profile, host_info))
                    host_info_map[hostname] = host_info
                else:
                    self.logger.error(f"Failed to get host info for {hostname}")
        else:
            # Fall back to individual lookups
            for hostname, uac_profile in targets:
                host_info = self.host_manager.get_host_by_hostname(hostname)
                if host_info:
                    # Check platform
                    platform = Platform(host_info.platform.lower())
                    if platform == Platform.WINDOWS:
                        self.logger.error(f"UAC not supported on Windows host {hostname}. Use KAPE instead.")
                        continue
                        
                    cid = host_info.cid
                    if cid not in hosts_by_cid:
                        hosts_by_cid[cid] = []
                    hosts_by_cid[cid].append((hostname, uac_profile, host_info))
                    host_info_map[hostname] = host_info
                else:
                    self.logger.error(f"Host {hostname} not found")
        
        # Process each CID group concurrently
        results = {}
        with ThreadPoolExecutor(max_workers=self.max_concurrent_hosts) as executor:
            futures = []
            
            for cid, hosts in hosts_by_cid.items():
                future = executor.submit(
                    self._process_uac_batch_for_cid,
                    cid, hosts, upload_to_s3
                )
                futures.append(future)
            
            # Collect results
            for future in as_completed(futures):
                try:
                    cid_results = future.result()
                    results.update(cid_results)
                except Exception as e:
                    self.logger.error(f"Failed to process UAC batch: {e}")
        
        # Add failed hosts that weren't processed
        for hostname, _ in targets:
            if hostname not in results:
                results[hostname] = False
        
        elapsed = time.time() - start_time
        success_count = sum(1 for v in results.values() if v)
        
        self.logger.info(
            f"Batch UAC collection completed in {elapsed:.1f}s. "
            f"Success: {success_count}/{len(targets)}"
        )
        
        return results
    
    def _process_uac_batch_for_cid(self, cid: str, hosts: List[Tuple[str, str, HostInfo]], 
                                   upload_to_s3: bool) -> Dict[str, bool]:
        """Process UAC collection for all hosts in a CID"""
        results = {}
        
        # Get or create UAC collector for this CID
        self._get_or_create_rtr_client(cid)
        uac_collector = self.uac_collectors[cid]
        
        # Use ThreadPoolExecutor for actual concurrency
        with ThreadPoolExecutor(max_workers=min(len(hosts), 10)) as executor:
            futures = {}
            
            for hostname, uac_profile, host_info in hosts:
                future = executor.submit(
                    self._process_single_uac,
                    uac_collector, hostname, uac_profile, host_info, upload_to_s3
                )
                futures[future] = hostname
            
            for future in as_completed(futures):
                hostname = futures[future]
                try:
                    results[hostname] = future.result()
                except Exception as e:
                    self.logger.error(f"Failed to run UAC on {hostname}: {e}")
                    results[hostname] = False
        
        return results
    
    def _process_single_uac(self, uac_collector, hostname, uac_profile, 
                           host_info, upload_to_s3):
        """Process a single UAC collection (thread-safe)"""
        try:
            self.logger.info(f"Running UAC collection on {hostname} with profile {uac_profile}")
            
            # Run UAC collection
            collection_file = uac_collector.run_uac_collection(host_info, uac_profile)
            
            if collection_file and upload_to_s3:
                # Upload results
                return uac_collector.upload_uac_results(host_info, collection_file)
            elif collection_file:
                # Download locally
                return uac_collector.download_uac_results(host_info, collection_file)
            else:
                return False
        except Exception as e:
            self.logger.error(f"Error processing UAC for {hostname}: {e}")
            raise
    
    def cleanup(self):
        """Clean up resources and expired sessions"""
        self.logger.info("Cleaning up orchestrator resources")
        
        # Clean up expired sessions in all RTR clients
        for cid, rtr_client in self.rtr_clients.items():
            rtr_client.cleanup_expired_sessions()
        
        # Clean up old batch info
        current_time = time.time()
        expired_batches = []
        
        for batch_id, batch_info in self._active_batches.items():
            if current_time - batch_info['timestamp'] > 600:  # 10 minutes
                expired_batches.append(batch_id)
        
        for batch_id in expired_batches:
            self._active_batches.pop(batch_id)
            self.logger.debug(f"Removed expired batch {batch_id}")
        
        self.logger.info("Cleanup completed")
    
    def get_cache_stats(self) -> Dict:
        """Get cache statistics"""
        stats = {
            'host_cache': {
                'size': len(self.discover_client._host_cache),
                'hits': 0,  # Would need to track this
                'misses': 0,  # Would need to track this
                'hit_rate': 0.0
            },
            'active_sessions': sum(len(client._active_sessions) for client in self.rtr_clients.values()),
            'active_batches': len(self._active_batches),
            'rtr_clients': len(self.rtr_clients)
        }
        
        return stats
    
    # Single-host methods for compatibility
    def run_kape(self, hostname: str, collection_type: str, upload_to_s3: bool = True) -> bool:
        """Run KAPE on a single host (compatibility method)"""
        results = self.run_kape_batch([(hostname, collection_type)], upload_to_s3)
        return results.get(hostname, False)
    
    def browser_history(self, username: str, hostname: str) -> bool:
        """Collect browser history from a single host (compatibility method)"""
        results = self.browser_history_batch([(username, hostname)])
        return results.get(f"{hostname}:{username}", False)
    
    def get_host_info(self, hostname: str) -> Optional[HostInfo]:
        """
        Get host information for a single hostname (compatibility method)
        
        Args:
            hostname: Target hostname
            
        Returns:
            HostInfo object or None if not found
        """
        try:
            return self.host_manager.get_host_by_hostname(hostname)
        except Exception as e:
            self.logger.error(f"Failed to get host info for {hostname}: {e}", exc_info=True)
            return None
    
    def run_kape_collection(self, hostname: str, target: str, upload: bool = True) -> bool:
        """
        Run KAPE collection on a single Windows host (compatibility method)
        
        Args:
            hostname: Target hostname
            target: KAPE target specification
            upload: Whether to upload results to S3
            
        Returns:
            True if successful, False otherwise
        """
        try:
            results = self.run_kape_batch([(hostname, target)], upload_to_s3=upload)
            return results.get(hostname, False)
        except Exception as e:
            self.logger.error(f"Failed to run KAPE collection on {hostname}: {e}", exc_info=True)
            return False
    
    def run_uac_collection(self, hostname: str, profile: str = "ir_triage", upload: bool = True) -> bool:
        """
        Run UAC collection on a single Unix/Linux/macOS host (compatibility method)
        
        Args:
            hostname: Target hostname
            profile: UAC profile to use
            upload: Whether to upload results to S3
            
        Returns:
            True if successful, False otherwise
        """
        try:
            results = self.run_uac_batch([(hostname, profile)], upload_to_s3=upload)
            return results.get(hostname, False)
        except Exception as e:
            self.logger.error(f"Failed to run UAC collection on {hostname}: {e}", exc_info=True)
            return False