# CLI Module

The CLI module provides the command-line interface for Falcon Client operations.

## Components

### main.py

The main entry point for the `falcon-client` command-line tool.

#### Features
- Argument parsing for multiple subcommands
- Credential resolution from environment or CLI
- Logging configuration
- Batch and sequential operation modes
- Performance reporting

#### Subcommands

##### kape
Run KAPE collection on one or more hosts:
```bash
falcon-client kape -n 1 -d HOSTNAME -t WebBrowsers

# Multiple hosts with batch mode
falcon-client kape -n 3 -d HOST1 -d HOST2 -d HOST3 -t Target1 -t Target2 -t Target3 --batch
```

##### browser_history
Collect browser history from one or more hosts:
```bash
falcon-client browser_history -n 1 -d HOSTNAME -u USERNAME

# Multiple hosts with batch mode
falcon-client browser_history -n 2 -d HOST1 -d HOST2 -u USER1 -u USER2 --batch
```

## Command Options

### Common Options
- `-n, --num-hosts`: Number of hosts to process (required)
- `--client-id`: Falcon API Client ID (or use CLIENT_ID env var)
- `--client-secret`: Falcon API Client Secret (or use CLIENT_SECRET env var)
- `--log-level`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `--log-file`: Log to file instead of console
- `--batch`: Enable concurrent operations for better performance
- `--max-concurrent`: Maximum concurrent operations (default: 20)

### KAPE-specific Options
- `-d, --device`: Device/hostname (repeat for each host)
- `-t, --target`: KAPE target name (repeat for each host)

### Browser History Options
- `-d, --device`: Device/hostname (repeat for each host)
- `-u, --user`: Username (repeat for each host)

## Environment Variables

The CLI respects these environment variables:
- `CLIENT_ID`: Falcon API client ID
- `CLIENT_SECRET`: Falcon API client secret
- AWS credentials (for S3 uploads)
- `.env` file is automatically loaded if present

## Execution Modes

### Sequential Mode (default)
- Processes hosts one at a time
- Simpler debugging
- Lower resource usage

### Batch Mode (--batch)
- Uses optimized orchestrator with native batch operations
- Significantly faster for multiple hosts
- Shows performance statistics

## Output Format

The CLI provides structured output:
```
[*] Starting concurrent KAPE collection for 3 devices
[*] Using native batch operations
[*] Processing HOST1 with target WebBrowsers...
[+] HOST1: KAPE run and upload complete
[*] Processing HOST2 with target BasicCollection...
[+] HOST2: KAPE run and upload complete
[*] Processing HOST3 with target EventLogs...
[!] HOST3: KAPE collection failed

============================================================
Total execution time: 125.3 seconds
Overall success rate: 2/3 (66.7%)

Concurrent execution: ENABLED
Average time per host: 41.8 seconds

Performance Stats:
  Host cache size: 3
  Active sessions: 0
  Active batches: 1
============================================================
```

## Error Handling

The CLI provides clear error messages:
- Missing credentials
- Invalid input counts
- Host not found
- Collection failures

Exit codes:
- 0: All operations successful
- 1: One or more operations failed

## Logging

### Console Logging (default)
```
2024-01-15 10:30:15 [INFO] FalconForensicOrchestrator: Starting browser history collection
2024-01-15 10:30:16 [INFO] HostManager: Found host: DESKTOP-ABC123
```

### File Logging
```bash
falcon-client --log-file falcon.log --log-level DEBUG kape -n 1 -d HOST -t Target
```

## Performance Tips

1. Use `--batch` for 5+ hosts
2. Adjust `--max-concurrent` based on your API limits
3. Enable DEBUG logging for troubleshooting
4. Monitor S3 uploads for large collections

## Integration Examples

### Shell Script
```bash
#!/bin/bash
# Collect from multiple hosts
HOSTS=("HOST1" "HOST2" "HOST3")
TARGETS=("WebBrowsers" "WebBrowsers" "WebBrowsers")

falcon-client kape -n ${#HOSTS[@]} \
  $(printf -- '-d %s ' "${HOSTS[@]}") \
  $(printf -- '-t %s ' "${TARGETS[@]}") \
  --batch --log-file collection.log
```

### Python Script
```python
import subprocess
import os

os.environ['CLIENT_ID'] = 'your-client-id'
os.environ['CLIENT_SECRET'] = 'your-client-secret'

result = subprocess.run([
    'falcon-client', 'browser_history',
    '-n', '1', '-d', 'HOSTNAME', '-u', 'USERNAME'
], capture_output=True, text=True)

print(result.stdout)
```