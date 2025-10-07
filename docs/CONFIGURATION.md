# 4n6NerdStriker Configuration Guide

## Overview

4n6NerdStriker supports external configuration files for managing workspace paths, S3 endpoints, proxy settings, and other configurable parameters. This allows you to customize the client's behavior without modifying code or environment variables.

**Key Features (v1.3.1+):**
- Configurable workspace directories for forensic tool deployment
- Custom S3 bucket and endpoint configuration
- Proxy server settings for restricted networks
- Dynamic host entries for endpoint /etc/hosts configuration
- Adjustable timeouts for large file operations

## Configuration File Locations

The client searches for configuration files in the following order:

1. **Environment Variable**: `FALCON_CONFIG_PATH` 
2. **Current Directory**: `config.yaml`, `config.yml`, or `config.json`
3. **Home Directory**: `~/.forensics_nerdstriker/config.yaml`, `~/.forensics_nerdstriker/config.yml`, or `~/.forensics_nerdstriker/config.json`

The first configuration file found will be used. If no configuration file is found, default values will be used.

## Configuration File Format

Configuration files can be in YAML or JSON format. YAML is recommended for readability.

### Full Configuration Example (config.yaml)

```yaml
# Workspace Configuration (NEW in v1.3.1+)
# Configure where forensic tools are deployed on target endpoints
workspace:
  # Windows workspace path (for KAPE collections)
  # Default: C:\0x4n6nerd
  windows: "C:\\0x4n6nerd"
  
  # Unix/Linux/macOS workspace path (for UAC collections)
  # Default: /opt/0x4n6nerd
  # Note: Avoid /tmp on macOS as it symlinks to /private/tmp
  unix: "/opt/0x4n6nerd"
  
  # Custom workspace examples:
  # windows: "D:\\ForensicTools\\Collections"
  # unix: "/forensics/workspace"

# S3 Configuration
s3:
  # Default S3 bucket for artifact uploads
  bucket_name: "your-s3-bucket-name"
  
  # S3 endpoint URL (optional - defaults to AWS standard endpoint)
  # Uncomment for custom S3-compatible endpoints (MinIO, DigitalOcean Spaces, etc.)
  # endpoint_url: "https://s3.us-west-2.amazonaws.com"
  
  # AWS region (optional - defaults to us-east-1)
  # region: "us-west-2"

# Proxy Configuration
proxy:
  # Proxy host for S3 uploads (when direct S3 access is not available)
  host: ""  # Leave empty if no proxy
  
  # Proxy IP address (optional - used as fallback if hostname resolution fails)
  ip: ""
  
  # Whether to use proxy by default (true/false)
  enabled: false

# Dynamic Host Entries
# These entries will be automatically added to /etc/hosts on target endpoints
# You can add as many entries as needed - all will be applied
host_entries:
  # Example entries - uncomment and modify as needed
  # - ip: "10.0.0.100"
  #   hostname: "forensic-server.example.com"
  #   comment: "forensic-server"  # Optional comment
  
  # Add more entries as needed - they will all be added to /etc/hosts
  # - ip: "10.0.0.100"
  #   hostname: "internal-service.example.com"
  #   comment: "internal-api"
  
  # - ip: "192.168.1.50"
  #   hostname: "database.local"
  #   comment: "database-server"

# Alternative endpoints (optional)
alternative_endpoints:
  # Velociraptor host for alternative upload method
  velociraptor:
    host: ""  # Your Velociraptor server
    ip: ""
    enabled: false

# Timeout Configuration (seconds)
timeouts:
  # File download timeout for large files
  file_download: 18000  # 5 hours
  
  # File upload timeout
  file_upload: 1500  # 25 minutes
  
  # SHA retrieval timeout
  sha_retrieval: 2000  # ~33 minutes
  
  # Command execution timeout
  command_execution: 600  # 10 minutes

# Advanced S3 Settings
advanced:
  # Presigned URL expiration time (seconds)
  presigned_url_expiration: 3600  # 1 hour
  
  # Multi-part upload threshold (bytes)
  multipart_threshold: 104857600  # 100MB
  
  # Multi-part upload chunk size (bytes)
  multipart_chunksize: 10485760  # 10MB
  
  # Maximum number of concurrent S3 transfers
  max_concurrent_transfers: 10
  
  # S3 transfer max bandwidth (bytes/second, 0 = unlimited)
  max_bandwidth: 0
```

### Minimal Configuration Example

```yaml
s3:
  bucket_name: "my-custom-bucket"

proxy:
  enabled: false  # Disable proxy, use direct S3 access
```

## Dynamic Host Entries

The `host_entries` configuration allows you to dynamically add any number of entries to the `/etc/hosts` file on target endpoints during collection operations. This is useful for:

- Resolving internal hostnames that aren't in DNS
- Overriding DNS resolution for specific services
- Adding proxy servers and internal endpoints
- Supporting air-gapped or isolated networks

### How It Works

1. Define entries in the `host_entries` list in your configuration file
2. Each entry requires an `ip` and `hostname`, with an optional `comment`
3. During collection, all entries are automatically added to `/etc/hosts` on the target
4. Works cross-platform (Windows and Unix/Linux/macOS)

### Example: Multiple Internal Services

```yaml
host_entries:
  # Proxy servers
  - ip: "10.0.0.1"
    hostname: "s3-proxy.internal"
    comment: "primary-s3-proxy"
    
  - ip: "10.0.0.2"
    hostname: "s3-proxy-backup.internal"
    comment: "backup-s3-proxy"
  
  # Internal services
  - ip: "172.16.0.10"
    hostname: "api.internal"
    comment: "internal-api"
    
  - ip: "172.16.0.20"
    hostname: "metrics.internal"
    comment: "metrics-collector"
    
  - ip: "172.16.0.30"
    hostname: "logs.internal"
    comment: "log-aggregator"
  
  # Database servers
  - ip: "192.168.100.10"
    hostname: "db-primary.local"
    comment: "primary-database"
    
  - ip: "192.168.100.11"
    hostname: "db-replica.local"
    comment: "replica-database"
```

### Platform-Specific Behavior

**Windows**: Entries are added to `C:\Windows\System32\drivers\etc\hosts` using PowerShell:
```
IP<tab>hostname<tab>#comment
```

**Unix/Linux/macOS**: Entries are added to `/etc/hosts` using echo:
```
IP hostname #comment
```

### Backwards Compatibility

If no `host_entries` are defined, the system will use default entries:
- Velociraptor endpoint
- S3 proxy endpoint

This ensures existing configurations continue to work without modification.

## Common Use Cases

### 1. Using a Custom S3 Endpoint (MinIO, etc.)

```yaml
s3:
  bucket_name: "my-minio-bucket"
  endpoint_url: "https://minio.example.com:9000"
  region: "us-east-1"

proxy:
  enabled: false  # Direct access to MinIO
```

### 2. Using a Different Proxy Server

```yaml
proxy:
  host: "proxy.mycompany.com"
  ip: "10.0.0.100"
  enabled: true
```

### 3. Adjusting Timeouts for Large Files

```yaml
timeouts:
  file_download: 36000  # 10 hours for very large files
  file_upload: 3600    # 1 hour
```

### 4. Disabling Proxy for Direct S3 Access

```yaml
proxy:
  enabled: false

s3:
  bucket_name: "my-direct-bucket"
  region: "eu-west-1"
```

## Environment Variables

Configuration files take precedence over environment variables. However, AWS credentials still need to be set via environment variables or AWS credential files:

```bash
# AWS Credentials (still required)
export AWS_ACCESS_KEY_ID=your-key
export AWS_SECRET_ACCESS_KEY=your-secret

# Optional: Override config file location
export FALCON_CONFIG_PATH=/path/to/custom/config.yaml
```

## Verifying Configuration

You can verify your configuration using the test script:

```bash
# Activate virtual environment
source .venv/bin/activate

# Run configuration test
python test/test_config_loader.py
```

This will display:
- Which configuration file was loaded
- Current S3 settings
- Current proxy settings
- Timeout values
- Alternative endpoints

## Programmatic Configuration Updates

The configuration can also be updated programmatically:

```python
from forensics_nerdstriker.core.configuration import Configuration

config = Configuration()

# Get current values
bucket = config.get_s3_bucket()
proxy_host = config.get_proxy_host()
is_proxy_enabled = config.is_proxy_enabled()

# Reload configuration from file
config.reload_config()
```

## Default Values

If no configuration file is present, the following defaults are used:

- **S3 Bucket**: `your-s3-bucket-name`
- **Proxy Host**: Not configured (empty string)
- **Proxy IP**: Not configured (empty string)
- **Proxy Enabled**: `false`
- **S3 Endpoint**: AWS default (not specified)
- **Region**: `us-east-1`
- **File Download Timeout**: 18000 seconds (5 hours)
- **File Upload Timeout**: 1500 seconds (25 minutes)

## Troubleshooting

### Configuration Not Loading

1. Check file exists in expected location:
   ```bash
   ls -la config.yaml
   ls -la ~/.forensics_nerdstriker/
   ```

2. Verify YAML syntax:
   ```bash
   python -c "import yaml; yaml.safe_load(open('config.yaml'))"
   ```

3. Check environment variable:
   ```bash
   echo $FALCON_CONFIG_PATH
   ```

### S3 Upload Failures

1. Verify bucket name and permissions
2. Check if proxy is required for your network
3. Ensure AWS credentials are properly set
4. Check endpoint URL if using custom S3

### Proxy Issues

1. Verify proxy host is reachable:
   ```bash
   ping proxy-host.example.com
   nslookup proxy-host.example.com
   ```

2. Check proxy IP is correct
3. Try disabling proxy if on a network with direct S3 access

## Migration from Hardcoded Values

Previous versions had hardcoded S3 buckets and proxy settings. To maintain backward compatibility:

1. Default values match the previously hardcoded values
2. No configuration file is required (defaults will be used)
3. Existing environments will continue to work without changes

To customize settings:
1. Create a `config.yaml` file in the project directory
2. Add only the settings you want to override
3. The client will automatically use the new values

## Security Considerations

1. **Do not commit** configuration files with sensitive information to version control
2. Add `config.yaml` and `config.json` to `.gitignore`
3. Use environment variables for AWS credentials (never put them in config files)
4. Consider using different configuration files for different environments (dev, staging, prod)
5. Restrict file permissions on configuration files containing sensitive data:
   ```bash
   chmod 600 config.yaml
   ```

## Support

For issues or questions about configuration:
1. Run the test script to verify configuration is loading correctly
2. Check the logs for configuration-related messages
3. Ensure YAML/JSON syntax is valid
4. Verify network connectivity to S3/proxy endpoints