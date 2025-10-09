# UAC Custom Profile Examples

This document provides ready-to-use custom UAC profiles for common incident response scenarios.

## Quick Start

Save any profile below as a `.yaml` file in the UAC `profiles/` directory, then run:
```bash
./uac -p profiles/custom_profile.yaml /output
```

## Incident Response Profiles

### 1. Ransomware Investigation

```yaml
# ransomware_response.yaml
version: 1.0
name: ransomware_response
description: Ransomware incident investigation
artifacts:
  # Critical volatile data
  - live_response/process/*
  - live_response/network/*
  
  # Recent file changes (ransomware activity)
  - bodyfile/bodyfile.yaml
  
  # Persistence mechanisms
  - files/system/cron.yaml
  - files/system/systemd.yaml
  - files/system/init.yaml
  
  # User activity
  - files/user/bash_history.yaml
  - files/user/ssh.yaml
  
  # System logs
  - files/logs/auth_logs.yaml
  - files/logs/syslog.yaml
  
  # Shadow copies and backups
  - custom/shadow_copies.yaml
  - custom/backup_status.yaml
```

### 2. Web Server Compromise

```yaml
# web_compromise.yaml
version: 1.0
name: web_compromise
description: Web server intrusion investigation
artifacts:
  # Running processes
  - live_response/process/*
  
  # Network connections
  - live_response/network/*
  
  # Web server logs
  - files/logs/apache.yaml
  - files/logs/nginx.yaml
  - files/logs/tomcat.yaml
  
  # Web application files
  - files/applications/www.yaml
  
  # Database logs
  - files/logs/mysql.yaml
  - files/logs/postgresql.yaml
  
  # Authentication
  - files/logs/auth_logs.yaml
  - files/system/passwd.yaml
  
  # Webshell detection
  - custom/webshell_hunt.yaml
```

### 3. Malware Investigation

```yaml
# malware_hunt.yaml
version: 1.0
name: malware_hunt
description: Active malware investigation
artifacts:
  # Memory acquisition
  - memory_dump/avml.yaml
  
  # Process analysis
  - live_response/process/*
  - hash_executables/hash_executables.yaml
  
  # Network indicators
  - live_response/network/*
  
  # Persistence locations
  - files/system/cron.yaml
  - files/system/systemd.yaml
  - files/system/init.yaml
  - files/user/autostart.yaml
  
  # Logs
  - files/logs/auth_logs.yaml
  - files/logs/syslog.yaml
  
  # Hidden files and directories
  - custom/hidden_files.yaml
  - custom/tmp_executables.yaml
```

### 4. Insider Threat

```yaml
# insider_threat.yaml
version: 1.0
name: insider_threat
description: Insider threat investigation
artifacts:
  # User activity monitoring
  - files/user/bash_history.yaml
  - files/user/mysql_history.yaml
  - files/user/python_history.yaml
  
  # SSH activity
  - files/user/ssh.yaml
  - files/logs/auth_logs.yaml
  
  # File access
  - live_response/process/lsof.yaml
  
  # Data exfiltration indicators
  - files/logs/mail.yaml
  - custom/large_archives.yaml
  - custom/usb_activity.yaml
  
  # Cloud storage clients
  - files/applications/dropbox.yaml
  - files/applications/gdrive.yaml
  
  # Database access
  - files/logs/mysql.yaml
  - files/logs/postgresql.yaml
```

### 5. APT Investigation

```yaml
# apt_investigation.yaml
version: 1.0
name: apt_investigation
description: Advanced Persistent Threat hunt
artifacts:
  # Memory forensics
  - memory_dump/avml.yaml
  
  # Complete process analysis
  - live_response/process/*
  - hash_executables/hash_executables.yaml
  
  # Network analysis
  - live_response/network/*
  - files/logs/firewall_logs.yaml
  
  # All persistence mechanisms
  - files/system/*
  - files/user/autostart.yaml
  
  # Command and control
  - files/logs/dns_logs.yaml
  - files/logs/proxy_logs.yaml
  
  # Lateral movement
  - files/user/ssh.yaml
  - files/logs/auth_logs.yaml
  
  # Data staging
  - custom/hidden_directories.yaml
  - custom/encrypted_archives.yaml
```

## Performance-Optimized Profiles

### 6. Quick Triage (15-20 minutes)

```yaml
# quick_triage.yaml
version: 1.0
name: quick_triage
description: Rapid initial assessment
artifacts:
  # Essential volatile data only
  - live_response/process/ps.yaml
  - live_response/network/netstat.yaml
  - live_response/network/ss.yaml
  
  # Critical logs
  - files/logs/auth_logs.yaml
  - files/logs/syslog.yaml
  
  # System basics
  - files/system/passwd.yaml
  - files/system/cron.yaml
  
  # Recent user activity
  - files/user/bash_history.yaml
```

### 7. Network Focus (20-30 minutes)

```yaml
# network_focus.yaml
version: 1.0
name: network_focus
description: Network-centric investigation
artifacts:
  # All network data
  - live_response/network/*
  
  # Process network usage
  - live_response/process/lsof.yaml
  
  # Firewall and network logs
  - files/logs/firewall_logs.yaml
  - files/logs/iptables.yaml
  
  # Network configuration
  - files/system/hosts.yaml
  - files/system/resolv.yaml
  - files/system/network.yaml
  
  # VPN and remote access
  - files/logs/openvpn.yaml
  - files/applications/vpn.yaml
```

### 8. Container Investigation

```yaml
# container_forensics.yaml
version: 1.0
name: container_forensics
description: Docker and container investigation
artifacts:
  # Container runtime
  - live_response/containers/*
  
  # Docker artifacts
  - files/applications/docker.yaml
  - files/logs/docker.yaml
  
  # Kubernetes
  - files/applications/kubernetes.yaml
  - files/logs/kubernetes.yaml
  
  # Container images and layers
  - custom/docker_images.yaml
  - custom/container_mounts.yaml
  
  # Process and network
  - live_response/process/*
  - live_response/network/*
```

## Compliance and Audit Profiles

### 9. PCI-DSS Compliance

```yaml
# pci_compliance.yaml
version: 1.0
name: pci_compliance
description: PCI-DSS compliance verification
artifacts:
  # Access control
  - files/system/passwd.yaml
  - files/system/group.yaml
  - files/system/sudoers.yaml
  - files/logs/auth_logs.yaml
  
  # Network security
  - live_response/network/iptables.yaml
  - files/system/ssh.yaml
  
  # Logging and monitoring
  - files/logs/*
  - files/system/rsyslog.yaml
  - files/system/auditd.yaml
  
  # System configuration
  - files/system/sysctl.yaml
  - live_response/packages/*
  
  # Encryption status
  - custom/encryption_check.yaml
```

### 10. HIPAA Audit

```yaml
# hipaa_audit.yaml
version: 1.0
name: hipaa_audit
description: HIPAA compliance audit
artifacts:
  # Access controls
  - files/system/passwd.yaml
  - files/logs/auth_logs.yaml
  - files/system/pam.yaml
  
  # Audit trails
  - files/logs/audit/*
  - files/system/auditd.yaml
  
  # Encryption
  - custom/disk_encryption.yaml
  - files/system/crypttab.yaml
  
  # System integrity
  - files/system/aide.yaml
  - files/system/tripwire.yaml
  
  # Backup verification
  - custom/backup_status.yaml
```

## Custom Artifact Examples

### Webshell Hunt

```yaml
# custom/webshell_hunt.yaml
version: 1.0
artifacts:
  - description: Hunt for potential webshells
    collector: find
    path: /var/www
    name_pattern: ["*.php", "*.jsp", "*.asp", "*.aspx"]
    content_pattern: ["eval", "base64_decode", "system", "exec", "passthru"]
    max_file_size: 1048576  # 1MB
    output_file: potential_webshells.txt
```

### Large Archive Search

```yaml
# custom/large_archives.yaml
version: 1.0
artifacts:
  - description: Find large archives (potential exfiltration)
    collector: find
    path: /home
    name_pattern: ["*.zip", "*.tar", "*.gz", "*.7z", "*.rar"]
    min_file_size: 104857600  # 100MB
    output_file: large_archives.txt
```

### Hidden Directories

```yaml
# custom/hidden_directories.yaml
version: 1.0
artifacts:
  - description: Find hidden directories
    collector: find
    path: /
    name_pattern: [".*"]
    file_type: [d]  # directories only
    exclude_path_pattern: ["/proc", "/sys", "/dev"]
    max_depth: 10
    output_file: hidden_directories.txt
```

## Usage Tips

1. **Test profiles before production use**:
   ```bash
   ./uac --validate-profile profiles/custom_profile.yaml
   ```

2. **Combine profiles for comprehensive collection**:
   ```bash
   ./uac -p ransomware_response.yaml -p network_focus.yaml /output
   ```

3. **Override artifacts on the fly**:
   ```bash
   ./uac -p quick_triage.yaml -a memory_dump/* /output
   ```

4. **Time-box collections**:
   ```bash
   timeout 3600 ./uac -p full /output  # 1-hour limit
   ```

5. **Profile performance testing**:
   ```bash
   time ./uac -p custom_profile.yaml /test_output
   ```

## Profile Development Guidelines

1. **Start minimal**: Begin with essential artifacts and expand as needed
2. **Consider volatility**: Collect volatile data first
3. **Test thoroughly**: Validate on representative systems
4. **Document purpose**: Clear descriptions help future users
5. **Version control**: Track profile changes
6. **Performance aware**: Monitor collection times
7. **Cross-platform**: Test on all target operating systems

## Performance-Optimized Profiles

Based on real-world timing analysis (macOS ARM64, ir_triage = 79 minutes), we've created optimized profiles:

### Quick Triage Optimized (15-20 minutes)
- **Profile name**: `quick_triage_optimized`
- **Purpose**: Rapid incident assessment
- **Key optimization**: Excludes hash_executables, bodyfile, and file searches
- **Includes**: Process, network, critical logs, SSH keys
- **Use case**: Time-critical incidents

### IR Triage No Hash (35-40 minutes)
- **Profile name**: `ir_triage_no_hash`
- **Purpose**: Full IR collection without hashing bottleneck
- **Key optimization**: Excludes only hash_executables (saves ~35 minutes)
- **Includes**: Everything from standard ir_triage except hashing
- **Use case**: Standard IR when file hashes aren't critical

### Network Compromise (25-30 minutes)
- **Profile name**: `network_compromise`
- **Purpose**: Focus on network intrusion artifacts
- **Key optimization**: Targeted collection for network attacks
- **Includes**: Network, web logs, SSH, access logs, timeline
- **Use case**: Web compromises, SSH intrusions

### Malware Hunt Fast (45-50 minutes)
- **Profile name**: `malware_hunt_fast`
- **Purpose**: Malware investigation with selective hashing
- **Key optimization**: Limited hashing to high-risk directories only
- **Includes**: Persistence, hidden files, startup, quarantine
- **Use case**: Targeted malware investigations

## Integration with fnerd-falconpy

These optimized profiles are built into 4n6NerdStriker v1.1.0+ with appropriate timeouts:

```bash
# Quick assessment (20 min timeout)
fnerd-falconpy uac -n 1 -d HOSTNAME -p quick_triage_optimized

# IR without hashing (45 min timeout)
fnerd-falconpy uac -n 1 -d HOSTNAME -p ir_triage_no_hash

# Network investigation (30 min timeout)
fnerd-falconpy uac -n 1 -d HOSTNAME -p network_compromise

# Fast malware hunt (50 min timeout)
fnerd-falconpy uac -n 1 -d HOSTNAME -p malware_hunt_fast
```

Custom profiles can also be referenced:
```python
# In forensics_nerdstriker configuration
UAC_PROFILES = {
    "ransomware": "/opt/uac/profiles/ransomware_response.yaml",
    "web_compromise": "/opt/uac/profiles/web_compromise.yaml",
    "quick": "/opt/uac/profiles/quick_triage.yaml",
    "malware": "/opt/uac/profiles/malware_hunt.yaml"
}
```
