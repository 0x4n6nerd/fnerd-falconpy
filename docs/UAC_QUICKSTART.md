# UAC Quick Start Guide

This guide helps you get started with UAC (Unix-like Artifacts Collector) in 4n6NerdStriker v1.1.0.

## Prerequisites

1. **4n6NerdStriker v1.1.0** installed
2. **UAC package** downloaded from https://github.com/tclahr/uac/releases
3. **CrowdStrike API credentials** with RTR permissions
4. **Target systems** running Linux, macOS, or Unix

## Setup

### 1. Download UAC

```bash
# Download latest UAC release (example: v3.7.0)
wget https://github.com/tclahr/uac/releases/download/v3.7.0/uac-3.7.0.tar.gz

# Copy to resources directory
cp uac-3.7.0.tar.gz forensics_nerdstriker/resources/uac/uac.tar.gz
```

### 2. Verify Installation

```bash
# Check UAC is in place
ls -la forensics_nerdstriker/resources/uac/uac.tar.gz
```

## Basic Usage

### Single Host Collection

```bash
# Quick incident response triage
4n6nerdstriker uac -n 1 -d linux-server-01 -p ir_triage

# Full forensic collection
4n6nerdstriker uac -n 1 -d linux-server-01 -p full

# Just collect logs
4n6nerdstriker uac -n 1 -d linux-server-01 -p logs
```

### Multiple Host Collection

```bash
# Collect from 3 hosts with same profile
4n6nerdstriker uac -n 3 -d host1 -d host2 -d host3 -p ir_triage -p ir_triage -p ir_triage

# Different profiles per host
4n6nerdstriker uac -n 3 -d linux-01 -d macos-01 -d linux-02 -p full -p logs -p network

# Batch mode for better performance
4n6nerdstriker uac -n 5 -d host1 -d host2 -d host3 -d host4 -d host5 \
  -p ir_triage -p ir_triage -p full -p logs -p network --batch
```

## Available Profiles

| Profile | Use Case | Collection Time |
|---------|----------|-----------------|
| `ir_triage` | Quick incident response | 5-15 minutes |
| `full` | Complete forensic collection | 30-120 minutes |
| `logs` | System and application logs | 5-20 minutes |
| `memory_dump` | Memory acquisition | 15-60 minutes |
| `network` | Network configuration | 5-10 minutes |
| `files` | File system artifacts | 20-90 minutes |
| `offline` | Mounted drives | Variable |

## Python API Usage

### Basic Collection

```python
from forensics_nerdstriker import FalconForensicOrchestrator

# Initialize
orchestrator = FalconForensicOrchestrator(client_id, client_secret)

# Run UAC collection
success = orchestrator.run_uac_collection(
    hostname="ubuntu-web-01",
    profile="ir_triage",
    upload=True  # Auto-upload to S3
)
```

### Batch Collection

```python
from forensics_nerdstriker import OptimizedFalconForensicOrchestrator

# Initialize optimized orchestrator
orchestrator = OptimizedFalconForensicOrchestrator(
    client_id, client_secret,
    max_concurrent_hosts=10
)

# Batch collection
results = orchestrator.run_uac_batch([
    ("linux-01", "ir_triage"),
    ("linux-02", "full"),
    ("macos-01", "logs"),
    ("freebsd-01", "network")
])

# Check results
for host, success in results.items():
    print(f"{host}: {'Success' if success else 'Failed'}")
```

## Platform Detection

The system automatically detects the platform and uses the appropriate collector:

```python
# Automatic platform detection
host_info = orchestrator.get_host_info("server-01")

if host_info.platform == "windows":
    # Use KAPE
    orchestrator.run_kape_collection(hostname, "WebBrowsers")
else:
    # Use UAC
    orchestrator.run_uac_collection(hostname, "ir_triage")
```

## Output Location

UAC collections are uploaded to S3 with this structure:
```
s3://your-bucket/uac/hostname/uac-hostname-os-timestamp.tar.gz
```

## Monitoring Progress

UAC collections can take time. Monitor progress in the console:

```
[*] Starting UAC collection on linux-01 with profile: ir_triage
[*] Preparing UAC package
[*] Uploading UAC to cloud
[*] Deploying UAC on target host
[*] Extracting UAC package
[*] Executing UAC collection with profile: ir_triage
[*] UAC still running... 2.5 minutes elapsed
[*] UAC still running... 5.0 minutes elapsed
[*] UAC collection file found: uac-linux-01-linux-20250127T143022
[*] UAC collection completed: uac-linux-01-linux-20250127T143022
[*] Starting upload to S3...
[*] Successfully uploaded uac-linux-01-linux-20250127T143022.tar.gz to S3
[*] Cleanup completed
[+] UAC collection uploaded successfully
```

## Troubleshooting

### Common Issues

1. **UAC not found**
   - Ensure uac.tar.gz is in `forensics_nerdstriker/resources/uac/`
   - Download from https://github.com/tclahr/uac/releases

2. **Platform error**
   - UAC only works on Unix/Linux/macOS
   - Use KAPE for Windows systems

3. **Permission denied**
   - Ensure RTR has admin permissions
   - Check API client scopes

4. **Collection timeout**
   - Large collections may exceed default timeout
   - Use smaller profiles for quick results

### Debug Mode

```bash
# Enable debug logging
export FALCON_LOG_LEVEL=DEBUG
4n6nerdstriker uac -n 1 -d host -p ir_triage
```

## Best Practices

1. **Start with ir_triage** - Quick results for incident response
2. **Use batch mode** - Better performance for multiple hosts
3. **Monitor S3 uploads** - Ensure collections are stored
4. **Clean up regularly** - UAC removes itself after collection
5. **Validate profiles** - Test profiles in non-production first

## Next Steps

- Review collected artifacts in S3
- Process with analysis tools
- Create custom profiles for your environment
- Integrate with SIEM/SOAR platforms

For more details, see the full documentation in the project README.