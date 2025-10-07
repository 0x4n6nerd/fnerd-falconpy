# 4n6NerdStriker Architecture Guide

## Overview

4n6NerdStriker is a comprehensive Python package for CrowdStrike Falcon RTR (Real Time Response) forensic collection and analysis operations. This guide provides a detailed architectural overview for LLMs and developers to understand the codebase structure, design patterns, and integration points for future enhancements.

## Package Information

- **Name**: 4n6nerdstriker
- **Version**: 1.0.0
- **Python**: 3.10+ (tested up to 3.13)
- **Key Dependencies**: 
  - crowdstrike-falconpy>=1.3.0
  - boto3>=1.26.0
  - python-dotenv>=0.19.0

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI Layer                             │
│                    forensics_nerdstriker.cli.main                     │
└─────────────────┬───────────────────────────┬─────────────────┘
                  │                           │
┌─────────────────▼─────────────┐ ┌──────────▼──────────────────┐
│      Orchestrator Layer       │ │   Optimized Orchestrator    │
│ FalconForensicOrchestrator    │ │OptimizedFalconForensicOrch  │
└─────────────────┬─────────────┘ └──────────┬──────────────────┘
                  │                           │
┌─────────────────▼───────────────────────────▼─────────────────┐
│                      Managers Layer                            │
│  HostManager │ SessionManager │ FileManager                    │
└─────────────────┬───────────────────────────┬─────────────────┘
                  │                           │
┌─────────────────▼─────────────┐ ┌──────────▼──────────────────┐
│       API Clients Layer       │ │      Collectors Layer       │
│ DiscoverAPIClient│RTRAPIClient│ │BrowserHistoryC│ForensicC    │
└─────────────────┬─────────────┘ └──────────┬──────────────────┘
                  │                           │
┌─────────────────▼───────────────────────────▼─────────────────┐
│                        Core Layer                              │
│          Base Classes │ Configuration │ Interfaces             │
└────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Core Layer (`forensics_nerdstriker/core/`)

#### Base Module (`base.py`)
- **Data Classes**:
  - `HostInfo`: Host system information (hostname, aid, cid, os_name, platform)
  - `RTRSession`: RTR session state (session_id, device_id, status_code)
  - `CommandResult`: Command execution results (stdout, stderr, return_code)
  - `Platform`: Enum for supported platforms (WINDOWS, MAC, LINUX)

- **Interfaces**:
  - `ILogger`: Logging interface with info/error/warning/debug methods
  - `IConfigProvider`: Configuration interface for browser paths and timeouts
  - `DefaultLogger`: Default logging implementation

#### Configuration Module (`configuration.py`)
- **Browser Configuration**: Paths for Chrome, Firefox, Brave, Edge, Opera across platforms
- **Timeouts**: Command execution (120s), file operations (300s), KAPE (7200s)
- **AWS Settings**: S3 bucket defaults, proxy settings
- **KAPE Settings**: Base paths, monitoring intervals

### 2. API Clients Layer (`forensics_nerdstriker/api/`)

#### Standard Clients (`clients.py`)
- **DiscoverAPIClient**: Host discovery and information retrieval
  - `query_hosts()`: Find hosts by filter
  - `get_host_details()`: Get detailed host information

- **RTRAPIClient**: Real-time response operations
  - Session management: `init_session()`, `delete_session()`, `pulse_session()`
  - Command execution: `execute_command()`, `execute_admin_command()`
  - File operations: `list_files_v2()`, `get_extracted_file_contents()`

#### Optimized Clients (`clients_optimized.py`)
- **OptimizedDiscoverAPIClient**: Batch host operations with caching
  - 5-minute cache for host details
  - Concurrent API calls for multiple hosts

- **OptimizedRTRAPIClient**: Enhanced RTR operations
  - Session pooling and reuse
  - Automatic retry with exponential backoff
  - Batch command execution

### 3. Managers Layer (`forensics_nerdstriker/managers/`)

#### HostManager
- Host discovery by hostname with fuzzy matching
- Host information extraction and validation
- Platform detection and normalization

#### SessionManager
- RTR session lifecycle management
- Session state tracking and cleanup
- Automatic session pulse/keepalive
- Error handling and recovery

#### FileManager
- File size retrieval across platforms
- File download with progress tracking
- SHA256 hash retrieval and validation
- Compressed file handling (7z)

### 4. Collectors Layer (`forensics_nerdstriker/collectors/`)

#### BrowserHistoryCollector
- Multi-browser support: Chrome, Firefox, Edge, Brave, Opera
- Profile discovery and enumeration
- Platform-specific path handling
- Batch collection capabilities

#### ForensicCollector
- KAPE deployment and execution
- Collection monitoring and status tracking
- Result packaging and compression
- S3 upload integration

### 5. Utilities Layer (`forensics_nerdstriker/utils/`)

#### Platform Handlers (`platform_handlers.py`)
- Platform-specific command generation
- File path normalization
- Output parsing for each OS
- Factory pattern for handler selection

#### Cloud Storage (`cloud_storage.py`)
- S3 integration with boto3
- Multipart upload for large files
- Progress tracking and retry logic
- Bucket and key management

### 6. Orchestrator Layer

#### FalconForensicOrchestrator (`orchestrator.py`)
- Component initialization and coordination
- High-level collection methods
- CID-based component caching
- Error handling and logging

#### OptimizedFalconForensicOrchestrator (`orchestrator_optimized.py`)
- Batch operations with concurrency control
- Host detail caching (5-minute TTL)
- Session pooling and reuse
- Native FalconPy batch API usage

### 7. CLI Layer (`forensics_nerdstriker/cli/`)

#### Main CLI (`main.py`)
- Subcommands: `kape`, `browser_history`, `rtr`, `isolate`, `release`, `isolation-status`
- Argument parsing and validation
- Batch mode with ThreadPoolExecutor
- Progress reporting and error summary

### 8. Response Actions (`forensics_nerdstriker/response/`)

#### Host Isolation (`isolation.py`)
- Network containment capabilities
- IsolationManager for coordinating actions
- Support for batch operations
- Status tracking and audit trails

#### Response Policies (`policies.py`)
- Policy management (future enhancement)
- Automated response rules

## Key Design Patterns

### 1. Dependency Injection
- All components accept dependencies via constructor
- Interfaces for logger and configuration
- Facilitates testing and extensibility

### 2. Factory Pattern
- `PlatformFactory` creates appropriate platform handlers
- Dynamic handler selection based on OS

### 3. Strategy Pattern
- Platform handlers implement common interface
- Collectors use appropriate strategy per platform

### 4. Repository Pattern
- Managers abstract data access
- Clean separation between API and business logic

### 5. Command Pattern
- RTR commands encapsulated with validation
- Retry logic and status checking

## Integration Points

### 1. FalconPy SDK Integration
The package wraps FalconPy SDK classes:
- `Discover` for host operations
- `RealTimeResponse` for RTR commands
- `RealTimeResponseAdmin` for admin commands

### 2. KAPE Integration
- KAPE resources bundled in `resources/kape/`
- Deployment script: `deploy_kape.ps1`
- Module and target configurations included

### 3. AWS S3 Integration
- Boto3 for S3 operations
- Configurable via environment variables
- Multipart upload for large files

## Configuration Management

### Environment Variables
```env
CLIENT_ID=          # CrowdStrike API client ID
CLIENT_SECRET=      # CrowdStrike API client secret
AWS_ACCESS_KEY_ID=  # AWS credentials
AWS_SECRET_ACCESS_KEY=
AWS_DEFAULT_REGION=
S3_BUCKET_NAME=
```

### Hardcoded Defaults
- S3 bucket: `your-s3-bucket-name`
- KAPE path: `C:\0x4n6nerd`
- Timeouts defined in `Configuration` class

## Error Handling Strategy

1. **API Errors**: Wrapped with descriptive messages
2. **Network Errors**: Retry with exponential backoff
3. **Session Errors**: Automatic session recreation
4. **File Errors**: Graceful degradation with logging

## Performance Optimizations

1. **Batch Operations**: Native API batch calls when available
2. **Caching**: 5-minute cache for host details
3. **Concurrency**: ThreadPoolExecutor for parallel operations
4. **Session Pooling**: Reuse RTR sessions across operations

## Security Considerations

1. **Credentials**: Never hardcoded, environment/CLI only
2. **Logging**: Sensitive data sanitized
3. **File Validation**: SHA256 verification
4. **Path Sanitization**: Platform-specific path validation

## Extension Points

### Adding New Collectors
1. Create new class in `collectors/` module
2. Inherit from base collector pattern
3. Implement platform-specific logic
4. Register in orchestrator

### Adding New Browsers
1. Update `BROWSER_PATHS` in configuration
2. Add browser detection logic
3. Implement profile discovery
4. Update platform handlers

### Adding New KAPE Targets
1. Add `.tkape` files to `resources/kape/Targets/`
2. Update deployment script if needed
3. No code changes required

### Adding New UAC Profiles
1. UAC profiles are configured in the UAC package itself
2. Update `UAC_SETTINGS` in configuration if adding custom profiles
3. No code changes required for standard UAC profiles

### Adding New Platform Support
1. Create new `PlatformHandler` subclass
2. Implement required methods
3. Update `PlatformFactory`
4. Add to `Platform` enum

## Testing Considerations

### Unit Testing
- Mock API clients for isolated testing
- Use dependency injection for test doubles
- Test platform handlers independently

### Integration Testing
- Test against CrowdStrike sandbox environment
- Verify KAPE deployment and execution
- Test S3 upload with test bucket

### Performance Testing
- Benchmark batch operations
- Monitor API rate limits
- Profile memory usage for large operations

## Known Limitations

1. **Platform Support**: Browser history limited on some Unix variants
2. **KAPE**: Windows-only, requires pre-installation
3. **UAC**: Unix/Linux/macOS only, not supported on Windows
4. **API Rate Limits**: Subject to CrowdStrike API limits
5. **File Size**: 5GB limit for individual files

## Future Enhancement Opportunities

1. **Additional Collectors**:
   - Memory dump collection
   - Registry hive extraction
   - Event log collection
   - Network connection enumeration

2. **Platform Enhancements**:
   - Full Linux browser support
   - Mobile device support
   - Container/cloud workload support

3. **Performance Improvements**:
   - Streaming file downloads
   - Parallel file transfers
   - Compression optimization

4. **Integration Expansions**:
   - Additional cloud storage providers
   - SIEM integration
   - Automated analysis pipelines

5. **Monitoring & Observability**:
   - Metrics collection
   - Performance dashboards
   - Collection status tracking

## API Reference

### Key FalconPy API Operations Used

1. **Host Discovery**:
   - `Discover.query_hosts()`: Find hosts by filter
   - `Discover.get_hosts()`: Get host details

2. **RTR Session Management**:
   - `RealTimeResponse.init_session()`: Start RTR session
   - `RealTimeResponse.delete_session()`: End session
   - `RealTimeResponse.pulse_session()`: Keep alive

3. **Command Execution**:
   - `RealTimeResponse.execute_command()`: Run RTR commands
   - `RealTimeResponseAdmin.execute_admin_command()`: Run admin commands
   - `RealTimeResponse.check_command_status()`: Poll for completion

4. **File Operations**:
   - `RealTimeResponse.list_files_v2()`: List session files
   - `RealTimeResponse.get_extracted_file_contents()`: Download files

## Maintenance Notes

1. **Dependency Updates**: Monitor FalconPy SDK releases
2. **API Changes**: Watch for CrowdStrike API updates
3. **KAPE Updates**: Sync with latest KAPE releases
4. **Security Patches**: Regular dependency scanning

This architecture guide serves as a comprehensive reference for understanding and extending the 4n6NerdStriker package. It should be updated as the codebase evolves to maintain accuracy for future development efforts.