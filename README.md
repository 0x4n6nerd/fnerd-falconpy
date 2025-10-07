# fnerd-falconpy 🚀

**Production-ready cross-platform forensic collection toolkit for CrowdStrike Falcon RTR**

fnerd-falconpy is a comprehensive Python package that leverages CrowdStrike Falcon's Real Time Response (RTR) capabilities to perform enterprise-scale forensic collections across Windows, macOS, and Linux endpoints.

## Key Features

- **🎯 Cross-Platform Collections**: Automated forensic collection from Windows (KAPE), Unix/Linux/macOS (UAC)
- **⚡ High Performance**: Collect forensic artifacts in minutes instead of hours
- **☁️ Cloud Integration**: Direct upload to AWS S3 or local download
- **🔧 Configurable**: External YAML configuration for flexible deployments
- **📊 Enterprise Scale**: Batch collection support for multiple endpoints
- **🔍 Browser History**: Extract browsing history from all major browsers
- **🛡️ RTR Integration**: Seamless integration with CrowdStrike's RTR capabilities
- **Browser History**: Cross-platform concurrent collection - extensively tested
- **Device Discovery**: Query and export device inventory by OS type across all CIDs
- **Batch operations** for multiple hosts with concurrent execution
- **Cloud storage** integration (S3) with verified uploads
- **Cross-platform** support (Windows, macOS, Linux)

## Features

### 🎯 **Production Ready (v1.3.0) - Extensively Tested June 2025**
- **KAPE**: 100% success rate (11/11 targets) - Fast (7-8m), Medium (9-13m), Large (19-35m) collections
- **UAC**: All 8 profiles stable - validated with full profile (85m, 3.8GB, 150 artifacts)
- **Browser History**: Concurrent collection from all major browsers
- **Triage**: Simplified concurrent execution using proven methods
- **S3 Uploads**: Reliable verification with streaming uploads for large files

### 🏗️ **Architecture**
- **Modular Design**: Clean separation with dedicated collectors, managers, and core components
- **Performance Optimized**: Concurrent execution and session reuse for efficiency
- **Cross-Platform**: Native support for Windows, macOS, and Linux endpoints
- **Cloud Integration**: Built-in S3 upload with comprehensive verification

### 🛡️ **Operational Security**
- **Workspace Cleanup**: Automatic removal of forensic artifacts from target systems
- **Session Management**: Proper RTR session handling with timeout protection
- **Error Recovery**: Emergency cleanup capabilities for operational security
- **Interactive RTR**: Full terminal experience for real-time response operations

### 🔧 **Management**
- **Host Isolation**: Network containment capabilities for incident response
- **Environment-Aware**: Configuration via environment variables and .env files
- **Extensible**: Easy to add new collectors and capabilities
- **Audit Logging**: Comprehensive logging for compliance and troubleshooting

## Requirements

### Software Requirements
- **Python**: 3.10 or higher (tested up to 3.13)
- **CrowdStrike Falcon**: API credentials with RTR permissions
- **Git**: For cloning the repository

### Third-Party Forensic Tools (Required)

fnerd-falconpy requires two external forensic collection tools that are **NOT included** in this repository:

#### **KAPE** (Windows Collections)
- **Author**: Eric Zimmerman (@EricZimmerman)
- **Purpose**: Windows forensic artifact collection
- **Repository**: https://github.com/EricZimmerman/KapeFiles
- **Download**: https://www.kroll.com/kape
- **License**: Free for personal and commercial use

#### **UAC** (Unix/Linux/macOS Collections)
- **Author**: Thiago Canozzo Lahr (@tclahr)
- **Purpose**: Unix-like system forensic artifact collection
- **Repository**: https://github.com/tclahr/uac
- **License**: Apache License 2.0

**📖 See [DEPENDENCIES.md](DEPENDENCIES.md) for detailed setup instructions.**

**🙏 See [CREDITS.md](CREDITS.md) for full attribution and acknowledgments.**

> **Why not included?** These tools are maintained by their respective authors and should be obtained from official sources to ensure you have the latest versions, proper licensing, and security updates.

## Installation

### From PyPI
```bash
pip install fnerd-falconpy
```

### From Source
```bash
git clone https://github.com/fnerd/fnerd-falconpy
cd fnerd-falconpy
pip install -e .
```

### Development Installation
```bash
git clone https://github.com/fnerd/fnerd-falconpy
cd fnerd-falconpy
pip install -e ".[dev]"
```

### Post-Installation Setup
After cloning the repository:

1. **Set Up Dependencies**: Obtain KAPE and UAC from their official sources
   ```bash
   # Run the dependency setup helper
   ./scripts/setup_dependencies.sh

   # OR follow the detailed guide
   # See DEPENDENCIES.md for complete instructions
   ```

2. **Create Environment File**: Copy the `.env.example` template
   ```bash
   cp .env.example .env
   ```

3. **Configure Credentials**: Add your CrowdStrike API credentials and AWS keys to `.env`
   ```bash
   # Edit .env with your credentials
   FALCON_CLIENT_ID=your-client-id
   FALCON_CLIENT_SECRET=your-client-secret
   AWS_ACCESS_KEY_ID=your-aws-key
   AWS_SECRET_ACCESS_KEY=your-aws-secret
   ```

4. **Test Installation**: Verify setup
   ```bash
   python test/test_installation.py
   ```

## Configuration

### Configuration File (NEW)

fnerd-falconpy now supports external configuration files for S3 endpoints, proxy settings, and timeouts. Create a `config.yaml` file in your project directory:

```yaml
# Workspace Configuration (NEW)
workspace:
  windows: "C:\\0x4n6nerd"  # Default Windows workspace for KAPE collections
  unix: "/opt/0x4n6nerd"     # Default Unix/Linux/macOS workspace for UAC collections

# S3 Configuration
s3:
  bucket_name: "your-s3-bucket"  # Default: your-s3-bucket-name
  # endpoint_url: "https://custom-s3.example.com"  # Optional: for S3-compatible services

# Proxy Configuration  
proxy:
  host: "your-proxy.example.com"  # Optional proxy server
  enabled: false  # Set to true to enable proxy

# Timeouts (seconds)
timeouts:
  file_download: 18000  # 5 hours for large files
```

### Workspace Configuration

The workspace directories are where forensic collection tools are deployed and temporary files are stored on target endpoints. These paths are fully configurable:

**Default Workspace Paths:**
- Windows: `C:\0x4n6nerd` (for KAPE collections)
- Unix/Linux/macOS: `/opt/0x4n6nerd` (for UAC collections)

**Custom Workspace Configuration:**
You can customize these paths in your `config.yaml`:

```yaml
workspace:
  windows: "D:\\ForensicTools"    # Custom Windows workspace
  unix: "/forensics/collections"   # Custom Unix workspace
```

**Important Workspace Notes:**
- Workspaces are automatically created and cleaned up after collections
- Ensure the configured paths are accessible and have sufficient permissions
- Avoid using system directories or paths with special restrictions
- On macOS, avoid `/tmp` as it symlinks to `/private/tmp` which can cause issues

See [Configuration Guide](docs/CONFIGURATION.md) for full documentation.

### Environment Variables

The package automatically searches for `.env` files in multiple locations:

1. **Current working directory** (`./.env`) - where you run commands
2. **User's home directory** (`~/.env`) - convenient for global config  
3. **Package installation directory** - relative to package location

```env
# CrowdStrike Falcon API Credentials (Required)
# Using FALCON_ prefix to avoid conflicts with other applications
FALCON_CLIENT_ID=your-client-id
FALCON_CLIENT_SECRET=your-client-secret

# AWS S3 Configuration (Required for upload functionality)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_DEFAULT_REGION=us-east-1

# Optional: Override config file location
FALCON_CONFIG_PATH=/path/to/custom/config.yaml
S3_BUCKET_NAME=your-s3-bucket-name
```

**Important Setup Notes:**
- **Variable Names**: Use `FALCON_CLIENT_ID` and `FALCON_CLIENT_SECRET` (legacy `CLIENT_ID` and `CLIENT_SECRET` are supported for backwards compatibility)
- **Credentials**: Store your CrowdStrike API credentials securely (e.g., 1Password) and create the `.env` file after installation
- **AWS Configuration**: Configure AWS CLI (`aws configure`) or EC2 instance roles for boto3 authentication as an alternative to environment variables
- **File Placement**: Place `.env` file in any of the search locations above - the package will find it automatically
- **S3 Permissions**: Ensure your AWS credentials have `s3:PutObject`, `s3:GetObject`, and `s3:ListBucket` permissions for the specified bucket
- **Validation**: The package validates that required Falcon credentials are present and logs which `.env` file was loaded

### API Permissions Required

Your CrowdStrike API client needs the following scopes:
- `hosts:read` - For host discovery
- `hosts:write` - For host isolation actions
- `real-time-response:read` - For RTR session management
- `real-time-response:write` - For RTR command execution
- `real-time-response-admin:write` - For admin commands (KAPE execution)

## Usage

### Command Line Interface

The package provides a `fnerd-falconpy` command:

```bash
# Quick KAPE triage (Windows, 2-5 minutes)
fnerd-falconpy kape -n 1 -d HOSTNAME -t !BasicCollection

# Comprehensive KAPE collection (15-30 minutes)
fnerd-falconpy kape -n 1 -d HOSTNAME -t KapeTriage --upload

# Multiple host KAPE collection with batch mode
fnerd-falconpy kape -n 3 -d HOST1 -d HOST2 -d HOST3 -t !BasicCollection -t RegistryHives -t EventLogs --batch

# Single host UAC collection (Linux/macOS/Unix)
fnerd-falconpy uac -n 1 -d HOSTNAME -p ir_triage

# Multiple host UAC collection with batch mode
fnerd-falconpy uac -n 3 -d HOST1 -d HOST2 -d HOST3 -p ir_triage -p full -p logs --batch

# Browser history collection
fnerd-falconpy browser_history -n 1 -d HOSTNAME -u USERNAME

# Batch browser history collection
fnerd-falconpy browser_history -n 2 -d HOST1 -d HOST2 -u USER1 -u USER2 --batch

# Batch triage from file (mixed environments)
fnerd-falconpy triage -f hosts.txt

# Device discovery - export all Mac devices
fnerd-falconpy discover -o mac

# Device discovery - Windows devices in specific CID
fnerd-falconpy discover -o windows -c 1234567890abcdef

# Device discovery - Linux devices including offline, export to JSON
fnerd-falconpy discover -o linux --include-offline -f json

# Interactive RTR session
fnerd-falconpy rtr -d HOSTNAME

# Host isolation (network containment)
fnerd-falconpy isolate -d HOSTNAME -r "Security incident"

# Release from isolation
fnerd-falconpy release -d HOSTNAME -r "Threat remediated"

# Check isolation status
fnerd-falconpy isolation-status -d HOSTNAME
```

### Python API

```python
from fnerd_falconpy import FalconForensicOrchestrator

# Initialize orchestrator
orchestrator = FalconForensicOrchestrator(
    client_id="your-client-id",
    client_secret="your-client-secret"
)

# Run KAPE collection (Windows)
success = orchestrator.run_kape_collection(
    hostname="DESKTOP-ABC123",
    target="WebBrowsers",
    upload=True
)

# Run UAC collection (Linux/macOS/Unix)
success = orchestrator.run_uac_collection(
    hostname="linux-srv-01",
    profile="ir_triage",
    upload=True
)

# Collect browser history
success = orchestrator.collect_browser_history(
    hostname="DESKTOP-ABC123",
    username="jdoe"
)

# Host isolation
result = orchestrator.isolate_host("DESKTOP-ABC123", "Malware detected")
if result.success:
    print(f"Host isolated: {result.message}")

# Check isolation status
from fnerd_falconpy.response import IsolationStatus
status = orchestrator.get_isolation_status("DESKTOP-ABC123")
if status == IsolationStatus.CONTAINED:
    print("Host is isolated")

# Release from isolation
result = orchestrator.release_host("DESKTOP-ABC123", "Threat remediated")
```

### Batch Operations (Optimized)

```python
from fnerd_falconpy import OptimizedFalconForensicOrchestrator

# Initialize optimized orchestrator
orchestrator = OptimizedFalconForensicOrchestrator(
    client_id="your-client-id",
    client_secret="your-client-secret",
    max_concurrent_hosts=20,
    enable_caching=True
)

# Batch KAPE collection (Windows)
results = orchestrator.run_kape_batch([
    ("host1", "WebBrowsers"),
    ("host2", "BasicCollection"),
    ("host3", "RegistryHives")
])

# Batch UAC collection (Linux/macOS/Unix)
results = orchestrator.run_uac_batch([
    ("linux-01", "ir_triage"),
    ("macos-01", "logs"),
    ("linux-02", "full")
])

# Batch browser history
results = orchestrator.browser_history_batch([
    ("user1", "host1"),
    ("user2", "host2")
])
```

## Architecture

### Package Structure

```
fnerd_falconpy/
├── core/           # Core data models and interfaces
├── api/            # API client implementations
├── managers/       # Session, host, and file management
├── collectors/     # KAPE and browser history collectors
├── rtr/            # Interactive RTR session module
├── utils/          # Utility functions and helpers
├── cli/            # Command-line interface
└── resources/      # Static resources (KAPE configurations)
```

### Key Components

1. **Orchestrator**: Main entry point that coordinates all operations
2. **API Clients**: Handle CrowdStrike API interactions
3. **Managers**: Handle host discovery, session management, and file operations
4. **Collectors**: Implement specific collection logic (KAPE, browser history)
5. **RTR Interactive**: Terminal interface for real-time response sessions
6. **Platform Handlers**: OS-specific command generation

See individual module README files for detailed documentation.

## KAPE Integration

The package includes KAPE module and target files in the `resources/kape` directory. These are automatically deployed to target systems when running KAPE collections.

### Supported KAPE Targets

- BasicCollection
- WebBrowsers
- RegistryHives
- EventLogs
- And many more...

See `resources/kape/Targets/` for the full list.

## Documentation

### UAC (Unix-like Artifacts Collector)
- [Comprehensive Guide](docs/UAC_COMPREHENSIVE_GUIDE.md) - Complete UAC overview and usage
- [Performance Guide](docs/UAC_PERFORMANCE.md) - Optimization strategies and benchmarks
- [Custom Profiles](docs/UAC_CUSTOM_PROFILES.md) - Ready-to-use incident response profiles
- [Enterprise Deployment](docs/UAC_ENTERPRISE_DEPLOYMENT.md) - Large-scale deployment patterns

### General Documentation
- [Architecture](docs/ARCHITECTURE.md) - System design and components
- [API Reference](docs/FalconPy_API_Reference.md) - Detailed API documentation
- [RTR Development Guide](docs/RTR_DEVELOPMENT_GUIDE.md) - RTR best practices

## Performance Considerations

- Use `--batch` flag when processing 5+ hosts for significant performance improvements
- The optimized orchestrator uses native FalconPy batch operations
- Host details are cached for 5 minutes to reduce API calls
- Sessions are automatically managed and refreshed
- UAC collections can be optimized by excluding time-consuming artifacts (see [Performance Guide](docs/UAC_PERFORMANCE.md))

## Troubleshooting

### Common Issues

1. **Authentication Errors**: Verify your CLIENT_ID and CLIENT_SECRET
2. **Permission Errors**: Ensure your API client has required scopes
3. **Host Not Found**: Verify the hostname matches exactly (case-sensitive)
4. **KAPE Not Found**: Ensure KAPE is installed on target Windows systems

### Debug Mode

Enable debug logging:
```bash
fnerd-falconpy --log-level DEBUG kape -n 1 -d HOSTNAME -t WebBrowsers
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For issues and feature requests, please use the GitHub issue tracker.