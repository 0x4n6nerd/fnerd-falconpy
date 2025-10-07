# UAC (Unix-like Artifacts Collector) Comprehensive Guide

## Overview

UAC is a **zero-dependency forensic artifact collection tool** for Unix-like systems, requiring only a POSIX shell to operate. It follows forensic best practices for order of volatility and provides enterprise-grade collection capabilities without installation requirements.

## Key Features

- **Zero Dependencies**: Runs with just shell - no Python, Perl, or compiled binaries required
- **Cross-Platform**: Supports AIX, ESXi, FreeBSD, Linux, macOS, NetBSD, NetScaler, OpenBSD, and Solaris
- **YAML-Based Configuration**: Extensible artifact and profile definitions
- **Cloud Integration**: Native S3, Azure Blob, and SFTP support
- **Forensically Sound**: Maintains order of volatility and chain of custody

## Quick Start

```bash
# Download and extract UAC
wget https://github.com/tclahr/uac/releases/latest/uac.tar.gz
tar -xzf uac.tar.gz
cd uac-*

# Run basic incident response triage
./uac -p ir_triage /output

# Full forensic collection
./uac -p full /evidence

# Upload to S3
./uac -p ir_triage -S s3://bucket/case123 /tmp
```

## Built-in Profiles

### ir_triage (Incident Response Triage)
- **Purpose**: Rapid incident response (60-90 minutes typical)
- **Data Volume**: 100MB-2GB compressed
- **Key Artifacts**: Volatile data, processes, network, system config
- **Excludes**: Browser data, user applications

### full (Comprehensive Collection)
- **Purpose**: Complete forensic acquisition
- **Collection Time**: 2-4+ hours
- **Data Volume**: 1-10GB+ compressed
- **Includes**: All artifacts including browser data, user files

### offline (Mounted Image Analysis)
- **Purpose**: Post-mortem analysis
- **Use Case**: Analyzing forensic images
- **Excludes**: Live commands

### offline_ir_triage (Offline Triage)
- **Purpose**: Quick triage of mounted images
- **Collection Time**: 15-30 minutes
- **Scope**: Essential artifacts from offline systems

## Performance Optimization

Based on real-world testing showing 4,721 seconds (~79 minutes) for `ir_triage`:

### Quick Optimizations

1. **Use SSD for temp directory** (30-40% improvement):
   ```bash
   export UAC_TEMP_DIR=/fast/ssd/uac_temp
   ./uac -p ir_triage /output
   ```

2. **Exclude time-consuming artifacts**:
   ```bash
   # Skip hash_executables (saves ~35 minutes)
   ./uac -p ir_triage -a !hash_executables/* /output
   
   # Skip bodyfile generation (saves ~5 minutes)
   ./uac -p ir_triage -a !bodyfile/* /output
   ```

3. **Date-based filtering** (40-60% improvement):
   ```bash
   ./uac -p full --start-date 2024-01-01 --end-date 2024-12-31 /output
   ```

4. **Custom lightweight profile**:
   ```yaml
   # quick_triage.yaml
   name: quick_triage
   description: Minimal triage collection
   artifacts:
     - live_response/process/ps.yaml
     - live_response/network/netstat.yaml
     - files/logs/auth_logs.yaml
     - files/system/passwd.yaml
   ```

### Performance Breakdown (ir_triage on macOS)

| Artifact | Time | Impact |
|----------|------|--------|
| hash_executables | ~35 min | Hashes all executables |
| bodyfile | ~5 min | Timeline generation |
| hidden_files | ~3 min | File system search |
| world_writable_files | ~3 min | Permission search |
| SUID/SGID files | ~3 min each | Security search |

## Custom Profiles

### Creating Custom Profiles

1. **Web Server Investigation**:
   ```yaml
   name: web_compromise
   description: Web server intrusion investigation
   artifacts:
     - live_response/process/*
     - live_response/network/*
     - files/logs/apache.yaml
     - files/logs/nginx.yaml
     - files/applications/web_shells.yaml
     - custom/persistence_check.yaml
   ```

2. **Malware Hunt**:
   ```yaml
   name: malware_hunt
   description: Active malware investigation
   artifacts:
     - memory_dump/avml.yaml
     - live_response/process/*
     - hash_executables/*
     - files/system/cron.yaml
     - files/system/systemd.yaml
   ```

3. **Insider Threat**:
   ```yaml
   name: insider_threat
   description: User activity investigation
   artifacts:
     - files/user/bash_history.yaml
     - files/user/ssh.yaml
     - files/logs/auth_logs.yaml
     - live_response/process/lsof.yaml
   ```

### Dynamic Profile Usage

```bash
# Combine profiles with additional artifacts
./uac -p ir_triage -a memory_dump/* -a custom/* /output

# Exclude specific artifacts
./uac -p full -a !files/browsers/* -a !hash_executables/* /output

# Target specific user
./uac -a "files/user/*:path=/home/suspicious_user" /output
```

## Enterprise Deployment

### Remote Collection via SSH

```bash
# Single host
ssh root@target "curl -L https://github.com/tclahr/uac/releases/latest/uac.tar.gz | 
  tar -xz && cd uac-* && ./uac -p ir_triage /tmp"

# Multiple hosts with GNU Parallel
parallel -j 10 ssh {} "wget -qO- https://github.com/tclahr/uac/releases/latest/uac.tar.gz | 
  tar -xz && cd uac-* && ./uac -p ir_triage -S sftp://evidence@storage:/cases/\$(date +%F) /tmp" \
  ::: $(cat hosts.txt)
```

### Ansible Deployment

```yaml
---
- name: UAC Forensic Collection
  hosts: incident_response
  become: yes
  tasks:
    - name: Deploy and run UAC
      shell: |
        cd /tmp
        wget -q https://github.com/tclahr/uac/releases/latest/uac.tar.gz
        tar -xzf uac.tar.gz
        cd uac-*
        ./uac -p {{ profile | default('ir_triage') }} \
          -S s3://{{ evidence_bucket }}/{{ ansible_hostname }}/{{ ansible_date_time.date }} \
          /tmp
      async: 7200
      poll: 60
```

## Incident Response Playbooks

### Ransomware Response

```bash
#!/bin/bash
# Emergency ransomware collection
CASE="RANSOM-$(date +%Y%m%d-%H%M%S)"

# Priority 1: Volatile data (run immediately)
./uac -a live_response/process/* -a live_response/network/* /evidence/$CASE/volatile &

# Priority 2: Recent changes (last 48 hours)
./uac -a bodyfile/* --start-date $(date -d '2 days ago' +%Y-%m-%d) /evidence/$CASE/timeline &

# Priority 3: Persistence and logs
./uac -a files/system/cron.yaml -a files/system/systemd.yaml -a files/logs/* /evidence/$CASE/persistence &

wait
```

### APT Investigation

```yaml
# apt_hunt.yaml
name: apt_hunt
description: Advanced Persistent Threat investigation
artifacts:
  # Memory acquisition
  - memory_dump/avml.yaml
  
  # Process analysis
  - live_response/process/*
  - hash_executables/hash_executables.yaml
  
  # Network backdoors
  - live_response/network/*
  - files/logs/firewall_logs.yaml
  
  # Persistence
  - files/system/*
  - files/user/autostart.yaml
  - files/applications/ssh.yaml
  
  # Data staging
  - custom/hidden_directories.yaml
  - custom/large_archives.yaml
```

## Integration with 4n6NerdStriker

The 4n6NerdStriker integrates UAC for Unix-like systems forensic collection:

```python
# Deployment via RTR
uac_collector.run_uac_collection(host_info, profile="ir_triage")

# Profile mapping
FALCON_TO_UAC_PROFILES = {
    "quick": "ir_triage",
    "comprehensive": "full",
    "offline": "offline",
    "custom": "/path/to/custom.yaml"
}

# Evidence path
EVIDENCE_PATH = "/opt/0x4n6nerd/evidence"  # Default evidence path
```

## Artifact Categories

### Live Response
- **Process**: ps, lsof, pstree, process hashes
- **Network**: netstat, ss, arp, routing tables
- **System**: hardware info, kernel modules, system stats
- **Hardware**: dmesg, ioreg, system profiler
- **Packages**: installed software, package managers
- **Storage**: disk usage, mounts, RAID status

### File Collection
- **Logs**: System logs, application logs, audit logs
- **Configuration**: /etc files, systemd units, cron jobs
- **User Data**: Shell history, SSH keys, browser artifacts
- **Applications**: Database files, web server configs
- **Security**: Firewall rules, SELinux policies

### Special Collections
- **Memory**: AVML memory acquisition
- **Timeline**: Bodyfile for timeline analysis
- **Hashes**: Executable file hashing
- **Container**: Docker, LXC/LXD artifacts
- **Cloud**: AWS, Azure, GCP metadata

## Best Practices

1. **Always run as root** for complete collection
2. **Use profiles** appropriate to investigation timeframe
3. **Test custom artifacts** before production use
4. **Monitor disk space** during collection
5. **Verify evidence integrity** with hashes
6. **Document collection parameters** for court proceedings
7. **Use date filtering** for targeted collections
8. **Implement secure transfer** for evidence movement

## Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Long runtime | Use custom profile with specific artifacts |
| Permission denied | Run with sudo or as root |
| No space left | Set UAC_TEMP_DIR to larger partition |
| Binary not found | Add required binary to uac/bin/[os]/ |
| Upload timeout | Use local collection then transfer |

### Debug Mode

```bash
# Enable debugging
./uac -p ir_triage --debug /output 2>&1 | tee debug.log

# Analyze issues
grep ERROR debug.log
grep "command not found" debug.log
```

## Resources

- **GitHub**: https://github.com/tclahr/uac
- **Documentation**: https://tclahr.github.io/uac-docs/
- **Releases**: https://github.com/tclahr/uac/releases
- **Issues**: https://github.com/tclahr/uac/issues

## Conclusion

UAC provides enterprise-grade forensic collection capabilities with minimal requirements. Its extensible architecture, comprehensive artifact coverage, and zero-dependency design make it ideal for incident response in heterogeneous Unix-like environments.