# fnerd-falconpy Package Structure

This document explains the overall architecture and how the components work together.

## Package Organization

```
falcon_client/
├── __init__.py           # Package exports
├── orchestrator.py       # Main orchestrator
├── orchestrator_optimized.py  # Optimized orchestrator with batch support
├── core/                 # Core data models and interfaces
│   ├── base.py          # Data classes and interfaces
│   └── configuration.py # Configuration management
├── api/                  # API client implementations
│   ├── clients.py       # Basic API clients
│   ├── clients_optimized.py # Optimized API clients
│   ├── hosts_client.py  # Hosts API wrapper
│   └── response_policies_client.py # Response policies wrapper
├── managers/            # High-level managers
│   └── managers.py      # Host, Session, and File managers
├── collectors/          # Data collectors
│   └── collectors.py    # Browser and forensic collectors
├── rtr/                 # Real Time Response interactive session
│   ├── __init__.py      # RTR exports
│   ├── commands.py      # Command definitions and parser
│   └── interactive.py   # Interactive session handler
├── response/            # Incident response actions
│   ├── __init__.py      # Response exports
│   ├── isolation.py     # Host isolation management
│   └── policies.py      # Response policy framework
├── utils/               # Utility classes
│   ├── platform_handlers.py # OS-specific handlers
│   └── cloud_storage.py     # S3 integration
├── cli/                 # Command-line interface
│   └── main.py          # CLI entry point
└── resources/           # Static resources
    ├── kape/            # KAPE modules and targets
    └── deploy_kape.ps1  # KAPE deployment script
```

## Component Interaction Flow

### Standard Flow (FalconForensicOrchestrator)

```
CLI/API Request
    ↓
FalconForensicOrchestrator
    ↓
    ├── DiscoverAPIClient (host discovery)
    ├── RTRAPIClient (session management)
    ├── HostsAPIClient (host actions)
    ├── HostManager (host operations)
    ├── SessionManager (session lifecycle)
    ├── FileManager (file operations)
    ├── BrowserHistoryCollector (browser data)
    ├── ForensicCollector (KAPE operations)
    ├── HostIsolationManager (network containment)
    ├── RTRInteractiveSession (interactive RTR)
    └── CloudStorageManager (S3 uploads)
```

### Optimized Flow (OptimizedFalconForensicOrchestrator)

```
CLI/API Request (with --batch)
    ↓
OptimizedFalconForensicOrchestrator
    ↓
    ├── OptimizedDiscoverAPIClient (cached, batch discovery)
    ├── OptimizedRTRAPIClient (batch operations)
    └── [Same managers and collectors, but used in batch mode]
```

## Key Design Patterns

### 1. Dependency Injection
All components receive their dependencies through constructors:
```python
orchestrator = FalconForensicOrchestrator(client_id, client_secret)
# Internally creates and wires all dependencies
```

### 2. Interface Segregation
Clear interfaces for extensibility:
- `ILogger` - Logging interface
- `IConfigProvider` - Configuration interface
- `PlatformHandler` - Platform-specific operations

### 3. Factory Pattern
Platform-specific handlers created via factory:
```python
handler = PlatformFactory.create_handler(platform)
```

### 4. Repository Pattern
Managers act as repositories for their domains:
- `HostManager` - Repository for host operations
- `SessionManager` - Repository for session operations
- `FileManager` - Repository for file operations

## Adding New Features

### Adding a New Collector

1. Create new collector class in `collectors/`:
```python
class RegistryCollector:
    def __init__(self, file_manager, session_manager, logger):
        self.file_manager = file_manager
        self.session_manager = session_manager
        self.logger = logger
    
    def collect_registry(self, host_info: HostInfo) -> bool:
        # Implementation
        pass
```

2. Add to orchestrator:
```python
self.registry_collector = RegistryCollector(
    self.file_manager,
    self.session_manager,
    self.logger
)
```

3. Add public method to orchestrator:
```python
def collect_registry(self, hostname: str) -> bool:
    host_info = self.initialize_for_host(hostname)
    return self.registry_collector.collect_registry(host_info)
```

### Adding Platform Support

1. Create new platform handler:
```python
class AIXPlatformHandler(PlatformHandler):
    def get_browser_history_paths(self, username: str) -> Dict[str, List[str]]:
        # AIX-specific paths
        pass
```

2. Add to PlatformFactory:
```python
@staticmethod
def create_handler(platform: Platform) -> PlatformHandler:
    if platform == Platform.AIX:
        return AIXPlatformHandler()
```

### Adding New Storage Backend

1. Create new storage manager:
```python
class AzureStorageManager:
    def upload_file(self, local_path: str, **kwargs) -> str:
        # Azure blob storage implementation
        pass
```

2. Update orchestrator to use it:
```python
self.cloud_storage = AzureStorageManager(self.logger)
```

## Performance Considerations

### Caching
- Host details cached for 5 minutes in optimized client
- Reduces API calls for repeated operations

### Batch Operations
- Native FalconPy batch methods used when available
- Sessions initialized in batches
- Commands executed across multiple hosts simultaneously

### Resource Management
- Sessions tracked and cleaned up automatically
- Expired sessions removed periodically
- File handles properly closed

## Error Handling Strategy

1. **API Errors**: Logged and return None/False
2. **Network Errors**: Retry with exponential backoff
3. **Resource Errors**: Cleanup attempted, then re-raise
4. **User Errors**: Clear error messages to CLI

## Testing Approach

### Unit Tests
Test individual components in isolation:
```python
def test_host_manager_get_host():
    mock_client = Mock()
    manager = HostManager(mock_client, logger)
    # Test implementation
```

### Integration Tests
Test component interactions:
```python
def test_browser_collection_flow():
    orchestrator = FalconForensicOrchestrator(test_id, test_secret)
    # Test full collection flow
```

### End-to-End Tests
Test complete workflows:
```python
def test_cli_kape_collection():
    result = subprocess.run(['falcon-client', 'kape', ...])
    # Verify results
```

## Configuration

### Required Environment Variables
- `CLIENT_ID` - CrowdStrike API client ID
- `CLIENT_SECRET` - CrowdStrike API client secret

### Optional Environment Variables
- `AWS_ACCESS_KEY_ID` - For S3 uploads
- `AWS_SECRET_ACCESS_KEY` - For S3 uploads
- `AWS_DEFAULT_REGION` - AWS region
- `S3_BUCKET_NAME` - Target S3 bucket

### Configuration Precedence
1. Command-line arguments
2. Environment variables
3. .env file
4. Default values

## Security Considerations

1. **Credentials**: Never hardcoded, always from environment
2. **File Paths**: All paths validated before use
3. **Command Injection**: Commands built safely with proper escaping
4. **Data Encryption**: S3 uploads use HTTPS
5. **Access Control**: S3 presigned URLs expire after 1 hour

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure package is installed: `pip install -e .`
2. **API Errors**: Check credentials and permissions
3. **Resource Not Found**: Verify KAPE resources are included
4. **S3 Errors**: Check AWS credentials and bucket permissions

### Debug Mode
Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Or via CLI:
```bash
falcon-client --log-level DEBUG ...
```