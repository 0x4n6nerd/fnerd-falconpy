# Collectors Module

The collectors module contains specialized classes for collecting forensic data from endpoints.

## Components

### collectors.py

#### BrowserHistoryCollector
Collects browser history from Chrome, Firefox, and Edge:

- **Methods**:
  - `collect_browser_history()`: Main collection method
  - `get_browser_paths()`: Get platform-specific browser paths
  - `download_browser_files()`: Download history databases
  
- **Features**:
  - Cross-platform support (Windows, macOS, Linux)
  - Multiple browser support (Chrome, Firefox, Edge)
  - Automatic user profile detection
  - SQLite database handling

#### ForensicCollector
Handles KAPE forensic collection operations (Windows only):

- **Methods**:
  - `run_kape_collection()`: Execute KAPE on target host
  - `prepare_kape_package()`: Prepare KAPE deployment package
  - `monitor_kape_execution()`: Monitor KAPE progress
  - `upload_kape_results()`: Upload results to S3
  - `cleanup_kape_artifacts()`: Clean up after collection
  
- **Features**:
  - Dynamic KAPE target configuration
  - Progress monitoring
  - Automatic S3 upload
  - Comprehensive cleanup
  - Error recovery

### uac_collector.py (v1.1.0)

#### UACCollector
Handles UAC (Unix-like Artifacts Collector) forensic collection operations for Unix/Linux/macOS:

- **Methods**:
  - `run_uac_collection()`: Execute UAC on target host
  - `prepare_uac_package()`: Prepare UAC deployment package
  - `monitor_uac_execution()`: Monitor UAC progress
  - `upload_uac_results()`: Upload results to S3
  
- **Features**:
  - Zero-dependency deployment
  - Profile-based collection
  - Platform validation (prevents Windows usage)
  - Automatic S3 upload
  - Comprehensive error handling

## Usage

### Browser History Collection
```python
from falcon_client.collectors import BrowserHistoryCollector

collector = BrowserHistoryCollector(file_manager, session_manager, config, logger)
success = collector.collect_browser_history(host_info, "username")
```

### KAPE Collection (Windows)
```python
from falcon_client.collectors import ForensicCollector

collector = ForensicCollector(file_manager, session_manager, cloud_storage, logger)
collection_file = collector.run_kape_collection(host_info, "WebBrowsers")
if collection_file:
    success = collector.upload_kape_results(host_info, collection_file)
```

### UAC Collection (Unix/Linux/macOS)
```python
from falcon_client.collectors import UACCollector

collector = UACCollector(file_manager, session_manager, cloud_storage, config, logger)
collection_file = collector.run_uac_collection(host_info, "ir_triage")
if collection_file:
    success = collector.upload_uac_results(host_info, collection_file)
```

## Supported KAPE Targets (Windows)

Common targets include:
- `BasicCollection` - Essential forensic artifacts
- `WebBrowsers` - Browser artifacts
- `RegistryHives` - Windows registry
- `EventLogs` - Windows event logs
- `FileSystem` - MFT and filesystem metadata
- Many more in `resources/kape/Targets/`

## Supported UAC Profiles (Unix/Linux/macOS)

Available profiles include:
- `ir_triage` - Incident response triage (default)
- `full` - Complete forensic collection
- `logs` - System and application logs
- `memory_dump` - Memory acquisition
- `network` - Network configuration and connections
- `files` - File system artifacts
- `offline` - Offline system analysis

## Browser Support

| Browser | Windows | macOS | Linux |
|---------|---------|--------|--------|
| Chrome | ✓ | ✓ | ✓ |
| Firefox | ✓ | ✓ | ✓ |
| Edge | ✓ | ✓ | ✗ |

## Collection Workflow

### Browser History
1. Create RTR session
2. Identify browser profile paths
3. Download history databases
4. Store in S3 with metadata
5. Clean up session

### KAPE Collection (Windows)
1. Prepare KAPE package with target
2. Upload package and deploy script
3. Deploy KAPE via PowerShell
4. Execute KAPE with specified target
5. Monitor execution progress
6. Download results
7. Upload to S3
8. Clean up all artifacts

### UAC Collection (Unix/Linux/macOS)
1. Prepare UAC tarball
2. Upload to target via RTR
3. Extract UAC package
4. Execute UAC with profile
5. Monitor execution progress
6. Upload results to S3
7. Clean up UAC binaries

## Architecture Notes

1. **Platform Abstraction**: Platform handlers provide OS-specific commands
2. **Resource Management**: Automatic cleanup of remote artifacts
3. **Progress Monitoring**: Real-time status updates during collection
4. **Error Recovery**: Comprehensive error handling and cleanup

## Configuration

Deployment paths are configurable via `config.yaml`. Default paths:

KAPE deployments (Windows):
- Deploy location: `C:\0x4n6nerd\` (configurable via workspace.windows)
- Temp directory: `C:\0x4n6nerd\temp\`
- Results: `C:\0x4n6nerd\<timestamp>_collection.zip`

UAC deployments (Unix/Linux/macOS):
- Deploy location: `/opt/0x4n6nerd/` (configurable via workspace.unix)
- Evidence directory: `/opt/0x4n6nerd/evidence/`
- Results: `uac-<hostname>-<os>-<timestamp>.tar.gz`

## Extension Points

To add new collectors:

1. Create a new collector class
2. Inherit common patterns from existing collectors
3. Implement collection, monitoring, and cleanup methods
4. Add platform-specific logic as needed
5. Ensure proper resource cleanup

To add new browser support:

1. Add browser paths to platform handlers
2. Update `get_browser_paths()` method
3. Handle browser-specific database formats
4. Test on target platforms