# API Module

The API module provides client classes for interacting with CrowdStrike Falcon APIs.

## Components

### clients.py
Basic API client implementations:

- **DiscoverAPIClient**: Handles host discovery operations
  - `query_hosts()`: Find hosts by filter
  - `get_host_details()`: Get detailed host information
  - Uses the Discover API for host lookups

- **RTRAPIClient**: Handles Real Time Response operations
  - `init_session()`: Initialize RTR session
  - `delete_session()`: Close RTR session
  - `execute_command()`: Run read-only commands
  - `execute_admin_command()`: Run administrative commands
  - `execute_active_responder_command()`: Run file operation commands
  - Various status check methods

### clients_optimized.py
Performance-optimized API clients with batch operations:

- **OptimizedDiscoverAPIClient**: Enhanced host discovery
  - `query_hosts_scroll()`: Pagination support for large queries (500 hosts/page)
  - `get_host_details_batch()`: Batch retrieval of host details (100 hosts/call)
  - Built-in caching with 5-minute expiry
  - Uses Hosts API instead of Discover for better performance

- **OptimizedRTRAPIClient**: Enhanced RTR operations
  - `batch_init_sessions()`: Initialize sessions on multiple hosts
  - `batch_command()`: Execute commands on multiple hosts
  - `batch_get_command()`: Retrieve files from multiple hosts
  - `batch_refresh_sessions()`: Keep multiple sessions alive
  - Automatic session tracking and cleanup

## Usage

### Basic Usage
```python
from falcon_client.api import DiscoverAPIClient, RTRAPIClient

# Host discovery
discover = DiscoverAPIClient(client_id, client_secret)
discover.initialize()
host_ids = discover.query_hosts("hostname:'DESKTOP-*'")
details = discover.get_host_details(host_ids)

# RTR operations
rtr = RTRAPIClient(client_id, client_secret, member_cid)
rtr.initialize()
session = rtr.init_session(device_id)
result = rtr.execute_command(session_id, "ls", "ls C:\\")
```

### Optimized Usage
```python
from falcon_client.api import OptimizedDiscoverAPIClient, OptimizedRTRAPIClient

# Batch host discovery with caching
discover = OptimizedDiscoverAPIClient(client_id, client_secret)
discover.initialize()
all_hosts = discover.query_hosts_scroll("platform_name:'Windows'", limit=500)
details = discover.get_host_details_batch(all_hosts, batch_size=100)

# Batch RTR operations
rtr = OptimizedRTRAPIClient(client_id, client_secret, member_cid)
rtr.initialize()
sessions = rtr.batch_init_sessions(device_ids)
results = rtr.batch_command(batch_id, "ps", "ps")
```

## Architecture Notes

1. **Separation of Concerns**: API clients handle only API communication
2. **Error Handling**: All methods return None on error with logging
3. **Resource Management**: Proper session lifecycle management
4. **Performance**: Optimized clients use native SDK batch operations
5. **Caching**: Host details cached to reduce API calls

## Performance Considerations

- Use optimized clients for operations on 5+ hosts
- Batch operations can reduce execution time by 85%+
- Host cache reduces redundant API calls
- Session tracking prevents resource leaks

## Extension Points

To add new API operations:

1. Add methods to the appropriate client class
2. Follow the existing error handling pattern
3. Return None on error, log all exceptions
4. For batch operations, add to the optimized client