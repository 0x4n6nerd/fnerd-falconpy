# Managers Module

The managers module provides high-level management classes for hosts, sessions, and files.

## Components

### managers.py

#### HostManager
Manages host discovery and information retrieval:

- **Methods**:
  - `get_host_by_hostname()`: Find a host by its hostname
  - `get_host_by_aid()`: Find a host by its Agent ID
  - `get_hosts_by_platform()`: Find all hosts of a specific platform
  
- **Features**:
  - Automatic platform detection from API response
  - Case-insensitive hostname matching
  - Detailed logging of operations

#### SessionManager
Manages RTR session lifecycle:

- **Methods**:
  - `create_session()`: Create a new RTR session
  - `end_session()`: Close an RTR session
  - `keep_session_alive()`: Refresh session to prevent timeout
  - `execute_command()`: Execute commands within a session
  
- **Features**:
  - Automatic session validation
  - Command execution with admin flag support
  - Session lifecycle logging

#### FileManager
Handles file operations in RTR sessions:

- **Methods**:
  - `list_cloud_files()`: List files in cloud storage
  - `upload_to_cloud()`: Upload file to cloud storage
  - `delete_from_cloud()`: Delete file from cloud storage
  - `download_from_host()`: Download file from remote host
  - `list_session_files()`: List files in current session
  - `get_file_info()`: Get detailed file information
  
- **Features**:
  - Cloud file management (put files)
  - File extraction from hosts
  - SHA256 hash verification
  - Automatic retry logic

## Usage

```python
from falcon_client.managers import HostManager, SessionManager, FileManager

# Host management
host_manager = HostManager(discover_client, logger)
host_info = host_manager.get_host_by_hostname("DESKTOP-ABC123")

# Session management
session_manager = SessionManager(rtr_client, logger)
session = session_manager.create_session(host_info)
result = session_manager.execute_command(session, "ls", "ls C:\\")
session_manager.end_session(session)

# File management
file_manager = FileManager(rtr_client, session_manager, logger)
cloud_files = file_manager.list_cloud_files(cid)
success = file_manager.upload_to_cloud(cid, "/path/to/file", "filename")
file_data = file_manager.download_from_host(session, "/path/on/host")
```

## Architecture Notes

1. **Abstraction Layer**: Managers provide high-level operations over API clients
2. **Error Recovery**: Built-in retry logic and error handling
3. **Resource Management**: Proper cleanup of sessions and resources
4. **Logging**: Comprehensive logging at each operation level

## Manager Interactions

```
HostManager
    ↓ (provides host info)
SessionManager
    ↓ (provides session)
FileManager
    ↓ (operates on files)
Collectors (use all managers)
```

## Best Practices

1. **Always close sessions**: Use try/finally or context managers
2. **Check return values**: Managers return None on failure
3. **Monitor session lifetime**: Sessions expire after 10 minutes
4. **Use appropriate permissions**: Admin commands require admin flag

## Extension Points

To add new manager functionality:

1. Create new methods following existing patterns
2. Include comprehensive error handling
3. Add detailed logging
4. Return None on failure, objects on success
5. Document all parameters and return values