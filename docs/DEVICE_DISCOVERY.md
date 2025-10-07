# Device Discovery Module

## Overview

The Device Discovery module allows you to query and export device information from CrowdStrike Falcon based on operating system type. It properly handles multi-CID environments where a parent CID has visibility of all devices across multiple member/child CIDs (operating companies), and automatically groups devices by their member CID for export.

## Features

- **OS-based Filtering**: Query devices by Windows, Mac, or Linux
- **Multi-CID Architecture**: Parent CID queries all devices, automatically groups by member CID
- **Member CID Organization**: Each operating company's devices are exported to separate files
- **Single CID Targeting**: Option to filter results to a specific member CID
- **Status Filtering**: Filter by online/offline status
- **Export Formats**: CSV and JSON with detailed device information
- **Batch Processing**: Efficiently handles large environments

## Installation

The discovery module is included with the 4n6nerdstriker package:

```bash
pip install -e .
```

## Usage

### Basic Discovery

```bash
# Discover all Mac devices (online only by default)
4n6nerdstriker discover -o mac

# Discover Windows devices including offline
4n6nerdstriker discover -o windows --include-offline

# Discover Linux devices in specific CID
4n6nerdstriker discover -o linux -c 1234567890abcdef
```

### Export Options

```bash
# Export to JSON format
4n6nerdstriker discover -o mac -f json

# Export to specific directory
4n6nerdstriker discover -o windows --output-dir ./reports

# Include offline devices (recommended for most environments)
4n6nerdstriker discover -o mac --include-offline
```

## Important Notes

### Online vs Offline Devices

**IMPORTANT**: Many CrowdStrike environments show devices as "offline" even when they're active. This can happen due to:
- Devices not actively communicating with the Falcon console
- Status field synchronization delays
- Network or firewall configurations

**Recommendation**: Always use `--include-offline` flag for comprehensive discovery:

```bash
4n6nerdstriker discover -o mac --include-offline
```

### Output Files

Files are created with the following naming convention:
- CSV: `[os]_devices_[member_cid]_[timestamp].csv`
- JSON: `[os]_devices_[member_cid]_[timestamp].json`

Each member CID (operating company) gets its own file for easy organization. For example, if you have devices across 10 different operating companies, you'll get 10 separate files, one for each member CID.

## Exported Fields

The discovery module exports comprehensive device information:

- **hostname**: Device hostname
- **device_id**: Unique device ID (AID)
- **cid**: Customer ID
- **platform_name**: Operating system platform
- **os_version**: Detailed OS version
- **agent_version**: Falcon agent version
- **local_ip**: Local IP address
- **external_ip**: External IP address
- **mac_address**: MAC address
- **last_seen**: Last communication timestamp
- **status**: Device status
- **product_type_desc**: Product description
- **system_manufacturer**: Hardware manufacturer
- **system_product_name**: Hardware model
- **tags**: Applied tags
- **groups**: Group memberships

## Use Cases

### Asset Inventory
```bash
# Export all devices for inventory
4n6nerdstriker discover -o windows --include-offline -f csv
4n6nerdstriker discover -o mac --include-offline -f csv
4n6nerdstriker discover -o linux --include-offline -f csv
```

### Compliance Reporting
```bash
# Export devices for specific CID
4n6nerdstriker discover -o windows -c YOUR_CID --include-offline -f json
```

### Migration Planning
```bash
# Identify all Mac devices for migration
4n6nerdstriker discover -o mac --include-offline --output-dir ./migration
```

## API Requirements

- CrowdStrike API credentials with device read permissions
- For multi-CID: Flight Control or appropriate cross-CID permissions

## Performance

- Queries are batched (5000 devices per request)
- Device details retrieved in batches of 100
- Large environments may take several minutes

## Troubleshooting

### No Devices Found

If the command returns no devices:

1. **Check credentials**: Ensure FALCON_CLIENT_ID and FALCON_CLIENT_SECRET are set
2. **Use --include-offline**: Many devices may show as offline
3. **Verify permissions**: Ensure API credentials have device read access
4. **Check CID**: For multi-CID environments, verify CID access

### Debug Mode

Use `--log-level DEBUG` for detailed output:

```bash
4n6nerdstriker discover -o mac --include-offline --log-level DEBUG
```

## Examples

### Complete Environment Discovery

```bash
#!/bin/bash
# Discover all devices across all OS types

OUTPUT_DIR="./discovery_$(date +%Y%m%d)"
mkdir -p "$OUTPUT_DIR"

echo "Discovering Windows devices..."
4n6nerdstriker discover -o windows --include-offline -f csv --output-dir "$OUTPUT_DIR"

echo "Discovering Mac devices..."
4n6nerdstriker discover -o mac --include-offline -f csv --output-dir "$OUTPUT_DIR"

echo "Discovering Linux devices..."
4n6nerdstriker discover -o linux --include-offline -f csv --output-dir "$OUTPUT_DIR"

echo "Discovery complete! Results in $OUTPUT_DIR"
```

### Python Integration

```python
from forensics_nerdstriker.discovery import DeviceDiscovery

# Initialize discovery
discovery = DeviceDiscovery(
    client_id=os.environ['FALCON_CLIENT_ID'],
    client_secret=os.environ['FALCON_CLIENT_SECRET']
)

# Query devices
devices_by_cid = discovery.query_devices_by_os(
    os_type='mac',
    online_only=False  # Include offline devices
)

# Export to CSV
csv_files = discovery.export_to_csv(devices_by_cid, 'mac')

# Process results
for cid, devices in devices_by_cid.items():
    print(f"CID {cid}: {len(devices)} devices")
    for device in devices:
        print(f"  - {device['hostname']}: {device['os_version']}")
```

## Support

For issues or questions, please refer to the main 4n6nerdstriker documentation or submit an issue on the project repository.