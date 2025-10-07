# Response Actions Module

This module provides incident response capabilities for the Falcon Client package, including host isolation (network containment) and response policy management.

## Overview

The response module enables security teams to take immediate action on compromised or suspicious endpoints:

- **Network Isolation**: Instantly isolate hosts while maintaining CrowdStrike Falcon connectivity
- **Batch Operations**: Efficiently handle multiple hosts during incident response
- **Audit Trail**: Track all actions with mandatory reason documentation
- **Status Monitoring**: Real-time visibility into isolation states

## Components

### Host Isolation (`isolation.py`)

Manages network containment operations:

```python
class HostIsolationManager:
    """Manages host isolation and release operations"""
    
    def isolate_host(hostname: str, reason: Optional[str]) -> IsolationResult
    def release_host(hostname: str, reason: Optional[str]) -> IsolationResult
    def get_isolation_status(hostname: str) -> IsolationStatus
    def get_isolated_hosts() -> List[Dict]
```

### Response Policies (`policies.py`)

Framework for automated response policies (future enhancement):

```python
class ResponsePolicyManager:
    """Manages response policies and automated actions"""
    
    def list_policies() -> List[ResponsePolicy]
    def get_policy(policy_id: str) -> Optional[ResponsePolicy]
    def create_policy(policy: ResponsePolicy) -> bool
```

## Usage Examples

### Command Line

```bash
# Isolate a compromised host
falcon-client isolate -d WORKSTATION-01 -r "Ransomware detected"

# Isolate multiple hosts
falcon-client isolate -d HOST1 -d HOST2 -d HOST3 -r "Lateral movement prevention"

# Check isolation status
falcon-client isolation-status -d WORKSTATION-01

# List all isolated hosts
falcon-client isolation-status

# Release from isolation
falcon-client release -d WORKSTATION-01 -r "Threat remediated"
```

### Python API

```python
from falcon_client import FalconForensicOrchestrator

# Initialize orchestrator
orchestrator = FalconForensicOrchestrator(client_id, client_secret)

# Isolate a host
result = orchestrator.isolate_host("WORKSTATION-01", "Malware detected")
if result.success:
    print(f"Host isolated: {result.message}")

# Check status
from falcon_client.response import IsolationStatus
status = orchestrator.get_isolation_status("WORKSTATION-01")
if status == IsolationStatus.CONTAINED:
    print("Host is currently isolated")

# Get all isolated hosts
isolated = orchestrator.get_isolated_hosts()
for host in isolated:
    print(f"{host['hostname']} - Isolated since {host['modified_timestamp']}")
```

## Isolation States

The module tracks the following isolation states:

- `NORMAL` - Host is not isolated
- `CONTAINED` - Host is isolated (network containment active)
- `CONTAINING` - Isolation in progress
- `LIFTING` - Release from isolation in progress
- `UNKNOWN` - Unable to determine status

## Best Practices

1. **Always Document Actions**: Include clear, concise reasons for all isolation/release actions
2. **Verify Before Isolation**: Check host details before taking action
3. **Monitor Isolated Hosts**: Regularly review isolated systems
4. **Plan Release Strategy**: Document criteria for releasing hosts
5. **Use Batch Operations**: For incidents affecting multiple hosts

## Error Handling

The module provides detailed error information:

```python
result = orchestrator.isolate_host("hostname", "reason")
if not result.success:
    print(f"Isolation failed: {result.error}")
    # Common errors:
    # - Host not found
    # - Already isolated
    # - Permission denied
    # - API communication error
```

## Future Enhancements

- **Scheduled Release**: Auto-release after specified duration
- **Policy-Based Isolation**: Automatic isolation based on detection rules
- **Group Operations**: Manage isolation by host groups
- **Webhook Integration**: Notifications for isolation events
- **Compliance Reporting**: Detailed audit reports

## API Permissions Required

The following CrowdStrike API permissions are required:
- `hosts:read` - To query host information
- `hosts:write` - To perform isolation actions

## Architecture

The response module follows the established patterns:
- Dependency injection for flexibility
- Clean separation of concerns
- Comprehensive error handling
- Integration with existing managers

For more details, see the [Architecture Guide](../../ARCHITECTURE.md).