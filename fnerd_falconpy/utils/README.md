# Utils Module

The utils module provides utility classes for platform-specific operations and cloud storage.

## Components

### platform_handlers.py

Platform-specific command generators for different operating systems:

#### PlatformHandler (Abstract Base)
- `get_browser_history_paths()`: Get browser profile locations
- `get_list_command()`: Generate directory listing command
- `get_ps_command()`: Generate process listing command
- `get_cd_command()`: Generate change directory command
- `get_mkdir_command()`: Generate make directory command
- `get_rm_command()`: Generate remove/delete command
- `get_extract_command()`: Generate file extraction command

#### WindowsPlatformHandler
- Chrome paths: `%LOCALAPPDATA%\Google\Chrome\User Data`
- Firefox paths: `%APPDATA%\Mozilla\Firefox\Profiles`
- Edge paths: `%LOCALAPPDATA%\Microsoft\Edge\User Data`
- Uses Windows-specific commands (dir, del, etc.)

#### MacPlatformHandler
- Chrome paths: `~/Library/Application Support/Google/Chrome`
- Firefox paths: `~/Library/Application Support/Firefox/Profiles`
- Edge paths: `~/Library/Application Support/Microsoft Edge`
- Uses Unix commands (ls, rm, etc.)

#### LinuxPlatformHandler
- Chrome paths: `~/.config/google-chrome`
- Firefox paths: `~/.mozilla/firefox`
- Uses Unix commands with Linux-specific paths

#### PlatformFactory
Factory class for creating appropriate platform handlers:
```python
handler = PlatformFactory.create_handler(Platform.WINDOWS)
```

### cloud_storage.py

Cloud storage integration for artifact storage:

#### CloudStorageManager
Manages S3 uploads for collected artifacts:

- **Methods**:
  - `upload_file()`: Upload file to S3
  - `upload_file_with_metadata()`: Upload with custom metadata
  - `generate_s3_key()`: Generate consistent S3 keys
  - `get_presigned_url()`: Generate temporary download URLs
  
- **Features**:
  - Automatic S3 client configuration
  - Metadata tagging for artifacts
  - Organized folder structure
  - Presigned URL generation
  - Comprehensive error handling

## Usage

### Platform Handlers
```python
from falcon_client.utils import PlatformFactory, Platform

# Get platform-specific handler
handler = PlatformFactory.create_handler(Platform.WINDOWS)

# Get browser paths for a user
paths = handler.get_browser_history_paths("john.doe")

# Generate platform-specific commands
ls_cmd = handler.get_list_command("C:\\Users")
ps_cmd = handler.get_ps_command()
```

### Cloud Storage
```python
from falcon_client.utils import CloudStorageManager

# Initialize manager
storage = CloudStorageManager(logger)

# Upload a file
s3_key = storage.upload_file(
    "/local/path/file.zip",
    hostname="DESKTOP-ABC123",
    file_type="kape_collection"
)

# Upload with metadata
s3_key = storage.upload_file_with_metadata(
    "/local/path/history.db",
    hostname="DESKTOP-ABC123",
    metadata={
        "browser": "chrome",
        "username": "john.doe",
        "profile": "Default"
    }
)

# Get download URL
url = storage.get_presigned_url(s3_key, expiration=3600)
```

## S3 Storage Structure

Files are organized in S3 as:
```
forensic-collections/
├── YYYY-MM-DD/
│   ├── DESKTOP-ABC123/
│   │   ├── kape_collection_TIMESTAMP.zip
│   │   ├── browser_history/
│   │   │   ├── chrome_Default_history_TIMESTAMP.db
│   │   │   └── firefox_profile_places_TIMESTAMP.sqlite
```

## Configuration

Environment variables:
- `AWS_ACCESS_KEY_ID`: AWS access key
- `AWS_SECRET_ACCESS_KEY`: AWS secret key
- `AWS_DEFAULT_REGION`: AWS region (default: us-east-1)
- `S3_BUCKET_NAME`: Target S3 bucket

## Architecture Notes

1. **Platform Abstraction**: Single interface for multi-OS support
2. **Command Safety**: All commands properly escaped/quoted
3. **Path Handling**: Platform-specific path separators
4. **Error Handling**: Graceful fallbacks for missing resources

## Extension Points

To add new platform support:
1. Create a new handler class inheriting from PlatformHandler
2. Implement all abstract methods
3. Add to PlatformFactory
4. Test commands on target platform

To add new cloud storage backends:
1. Create new storage manager class
2. Implement upload/download methods
3. Maintain consistent key generation
4. Add appropriate error handling