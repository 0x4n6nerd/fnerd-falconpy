# Workspace Configuration Guide

## Overview

4n6NerdStriker uses configurable workspace directories for deploying forensic collection tools on target endpoints. This guide explains how to configure these paths for your environment.

## Default Workspace Paths

By default, 4n6NerdStriker uses these workspace directories:

- **Windows**: `C:\0x4n6nerd`
- **Unix/Linux/macOS**: `/opt/0x4n6nerd`

These paths are where:
- Forensic collection tools (KAPE, UAC) are deployed
- Temporary files are created during collection
- Collection results are stored before retrieval

## Configuring Custom Workspace Paths

You can customize workspace paths via the `config.yaml` file:

```yaml
workspace:
  windows: "C:\\0x4n6nerd"    # Windows workspace path
  unix: "/opt/0x4n6nerd"       # Unix/Linux/macOS workspace path
```

### Examples of Custom Configurations

#### Using a Different Drive on Windows
```yaml
workspace:
  windows: "D:\\ForensicTools"
  unix: "/opt/0x4n6nerd"
```

#### Using Enterprise-Specific Paths
```yaml
workspace:
  windows: "C:\\CompanyName\\Forensics"
  unix: "/opt/companyname/forensics"
```

#### Using Alternative Unix Locations
```yaml
workspace:
  windows: "C:\\0x4n6nerd"
  unix: "/forensics/workspace"
```

## Important Considerations

### Path Requirements

1. **Windows Paths**:
   - Use double backslashes (`\\`) in YAML configuration
   - Ensure the drive exists and has sufficient space
   - Avoid system-protected directories

2. **Unix/Linux/macOS Paths**:
   - Use forward slashes (`/`)
   - Ensure the path is accessible with appropriate permissions
   - **Avoid `/tmp`** on macOS as it symlinks to `/private/tmp`

### Permissions

The configured workspace paths must be:
- Writable by the RTR session user
- Have sufficient disk space for collection data
- Not restricted by system policies

### Automatic Management

4n6NerdStriker automatically:
- Creates workspace directories if they don't exist
- Deploys necessary tools to the workspace
- Cleans up the workspace after collection completes

## How Workspace Paths Are Used

### KAPE (Windows)
```
C:\0x4n6nerd\                    # Main workspace
├── kape.zip                     # KAPE package
├── kape.exe                     # KAPE executable
├── _kape.cli                    # KAPE configuration
├── Targets/                     # KAPE targets
├── Modules/                     # KAPE modules
└── temp/                        # Temporary collection directory
    └── <timestamp>_collection/  # Collection results
```

### UAC (Unix/Linux/macOS)
```
/opt/0x4n6nerd/                  # Main workspace
├── uac.zip                      # UAC package
├── uac-main/                    # UAC executable and libraries
│   ├── uac                      # Main UAC script
│   ├── lib/                     # UAC libraries
│   └── bin/                     # UAC binaries
└── evidence/                    # Collection results directory
    └── uac-<hostname>-<timestamp>.tar.gz
```

## Configuration File Locations

4n6NerdStriker searches for `config.yaml` in these locations (in order):
1. Environment variable: `$FALCON_CONFIG_PATH`
2. Current directory: `./config.yaml`
3. Home directory: `~/.forensics_nerdstriker/config.yaml`

## Verifying Your Configuration

To verify workspace configuration is loaded correctly:

```python
from forensics_nerdstriker.core.configuration import Configuration

config = Configuration()

# Get configured paths
windows_path = config.get_kape_setting("base_path")
unix_path = config.get_uac_setting("base_path")

print(f"Windows workspace: {windows_path}")
print(f"Unix workspace: {unix_path}")
```

Or use the test script:
```bash
python test/test_config_loader.py
```

## Troubleshooting

### Common Issues

1. **"Directory not found" errors**:
   - Verify the configured path exists or can be created
   - Check permissions on parent directory

2. **"Access denied" errors**:
   - Ensure RTR session has write permissions
   - Avoid system-protected directories

3. **Cleanup failures**:
   - RTR session may be in the workspace directory
   - 4n6NerdStriker automatically changes directory before cleanup

### Platform-Specific Notes

**Windows**:
- Deployment scripts use PowerShell
- Paths are case-insensitive
- Network paths (UNC) are not supported

**macOS**:
- Avoid `/tmp` due to symlink issues
- Use `/opt` or `/usr/local` for better compatibility
- May require admin privileges for `/opt`

**Linux**:
- Standard Unix paths work best
- Consider SELinux policies if applicable
- Ensure sufficient space in chosen partition

## Migration from Hardcoded Paths

If upgrading from an older version with hardcoded paths:

1. **Old hardcoded paths**:
   - Windows: `C:\0x4n6nerd`
   - Unix: `/opt/0x4n6nerd`

2. **New configurable defaults**:
   - Windows: `C:\0x4n6nerd`
   - Unix: `/opt/0x4n6nerd`

3. **To use custom paths**, create a `config.yaml` file with your desired workspace configuration

## Best Practices

1. **Choose paths with sufficient space**: Collections can be several GB
2. **Avoid temporary directories**: They may be cleaned by the OS
3. **Use consistent naming**: Makes troubleshooting easier across teams
4. **Document your configuration**: Include workspace paths in your deployment documentation
5. **Test before production**: Verify workspace creation and cleanup work correctly

## See Also

- [Configuration Guide](CONFIGURATION.md) - Complete configuration documentation
- [Architecture](ARCHITECTURE.md) - System design and components
- [README](../README.md) - General usage and setup