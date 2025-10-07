# Host Isolation & Response Module

The Host Isolation module provides network containment capabilities for incident response scenarios. This allows you to quickly isolate compromised or suspicious hosts from the network while maintaining CrowdStrike Falcon sensor connectivity.

## Overview

Host isolation (network containment) is a critical incident response capability that:
- Prevents lateral movement by cutting off network access
- Maintains Falcon sensor connectivity for continued monitoring
- Allows for controlled release when threats are remediated
- Provides audit trail of isolation actions

## Features

### 1. Host Isolation
Isolate one or more hosts from the network:

```bash
# Isolate a single host
4n6nerdstriker isolate -d HOSTNAME

# Isolate with reason
4n6nerdstriker isolate -d HOSTNAME -r "Suspicious activity detected"

# Isolate multiple hosts
4n6nerdstriker isolate -d HOST1 -d HOST2 -d HOST3 -r "Ransomware outbreak"
```

### 2. Release from Isolation
Release hosts from network containment:

```bash
# Release a single host
4n6nerdstriker release -d HOSTNAME

# Release with reason
4n6nerdstriker release -d HOSTNAME -r "Threat remediated"

# Release multiple hosts
4n6nerdstriker release -d HOST1 -d HOST2 -d HOST3
```

### 3. Check Isolation Status
Monitor isolation status of hosts:

```bash
# Check specific host
4n6nerdstriker isolation-status -d HOSTNAME

# List all isolated hosts
4n6nerdstriker isolation-status
```

## API Usage

For programmatic access:

```python
from forensics_nerdstriker import FalconForensicOrchestrator

# Initialize orchestrator
orchestrator = FalconForensicOrchestrator(
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET"
)

# Isolate a host
result = orchestrator.isolate_host("hostname", reason="Malware detected")
if result.success:
    print(f"Host isolated: {result.message}")

# Release a host
result = orchestrator.release_host("hostname", reason="Remediation complete")

# Check status
status = orchestrator.get_isolation_status("hostname")
if status and status.get('is_isolated'):
    print(f"Host is isolated since: {status.get('modified_timestamp')}")

# List all isolated hosts
isolated = orchestrator.list_isolated_hosts()
for host in isolated:
    print(f"{host['hostname']} - Isolated")
```

## Direct Manager Usage

For more control:

```python
from forensics_nerdstriker.response import HostIsolationManager
from forensics_nerdstriker.api import HostsAPIClient

# Create manager
hosts_client = HostsAPIClient(client_id, client_secret)
isolation_manager = HostIsolationManager(hosts_client)

# Batch isolation
hostnames = ["host1", "host2", "host3"]
batch_result = isolation_manager.isolate_hosts_batch(
    hostnames, 
    reason="Security incident"
)

for hostname, result in batch_result.results.items():
    if result.success:
        print(f"{hostname}: Isolated")
    else:
        print(f"{hostname}: Failed - {result.error}")
```

## Best Practices

1. **Always Document Reasons**: Include clear reasons for isolation/release actions for audit trails

2. **Verify Before Isolation**: Check host details before isolation:
   ```bash
   4n6nerdstriker isolation-status -d HOSTNAME
   ```

3. **Monitor Isolated Hosts**: Regularly check isolated hosts and release when appropriate

4. **Batch Operations**: Use batch operations for multiple hosts during incidents

5. **Integration with IR Playbooks**: Incorporate isolation into automated incident response workflows

## Architecture

The isolation module follows the established patterns:

```
response/
├── __init__.py
├── isolation.py      # Core isolation logic
└── policies.py       # Response policy management (future)

api/
├── hosts_client.py   # Hosts API wrapper
└── response_policies_client.py  # Policies API wrapper
```

### Key Components

1. **IsolationResult**: Standard result object with success/error tracking
2. **HostIsolationManager**: Main manager for isolation operations
3. **HostsAPIClient**: API wrapper for device actions
4. **Orchestrator Integration**: Convenience methods in main orchestrator

## Error Handling

Common scenarios:
- Host not found: Returns error with details
- Already isolated: Success with informational message
- Permission denied: Error with authorization details
- API errors: Wrapped with context

## Future Enhancements

1. **Scheduled Release**: Auto-release after specified duration
2. **Policy-Based Isolation**: Automatic isolation based on detection rules
3. **Isolation Groups**: Manage groups of isolated hosts
4. **Reporting**: Generate isolation reports and metrics
5. **Webhook Integration**: Notifications on isolation events