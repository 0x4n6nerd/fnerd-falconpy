# KAPE Enterprise Deployment Guide

## Overview

KAPE's enterprise deployment transforms incident response from hours to minutes across thousands of endpoints. This guide covers infrastructure requirements, deployment strategies, and operational procedures for large-scale KAPE implementations.

## Infrastructure Architecture

### Recommended Deployment Model

```
┌─────────────────┐
│ Falcon Console  │
└────────┬────────┘
         │
┌────────▼────────┐     ┌──────────────┐
│   RTR Session   │────▶│ Target Host  │
│    Manager      │     │  (Windows)   │
└─────────────────┘     └──────┬───────┘
                               │
                        ┌──────▼───────┐
                        │    KAPE      │
                        │  Execution   │
                        └──────┬───────┘
                               │
                 ┌─────────────┴──────────────┐
                 │                            │
         ┌───────▼────────┐          ┌───────▼────────┐
         │ Local Storage  │          │ Network Share  │
         │  (Fast SSD)    │          │   (SMB 3.0)    │
         └───────┬────────┘          └───────┬────────┘
                 │                            │
                 └─────────────┬──────────────┘
                               │
                       ┌───────▼────────┐
                       │   S3 Upload    │
                       │  (Long-term)   │
                       └────────────────┘
```

## Performance Requirements

### Collection Server Specifications

| Scale | Endpoints | CPU Cores | RAM | Storage | Network |
|-------|-----------|-----------|-----|---------|---------|
| Small | <100 | 8 | 16 GB | 1 TB NVMe | 1 GbE |
| Medium | 100-1000 | 16 | 64 GB | 5 TB NVMe | 10 GbE |
| Large | 1000-5000 | 32 | 128 GB | 20 TB NVMe | 2x10 GbE |
| Enterprise | 5000+ | 64+ | 256 GB | 50+ TB NVMe | 4x10 GbE |

### Storage Calculations

```python
# Storage requirement formula
daily_storage = endpoints * avg_collection_size * collections_per_day * compression_ratio

# Example: 5000 endpoints
endpoints = 5000
avg_collection_size = 1  # GB
collections_per_day = 0.1  # 10% daily
compression_ratio = 0.3  # 70% compression

daily_storage = 5000 * 1 * 0.1 * 0.3  # = 150 GB/day
monthly_storage = daily_storage * 30   # = 4.5 TB/month
annual_storage = monthly_storage * 12  # = 54 TB/year
```

### Network Bandwidth Planning

| Collection Size | Time Window | Endpoints | Required Bandwidth |
|----------------|-------------|-----------|-------------------|
| 500 MB | 1 hour | 100 | 111 Mbps |
| 1 GB | 4 hours | 500 | 277 Mbps |
| 2 GB | 8 hours | 1000 | 555 Mbps |
| 500 MB | 24 hours | 5000 | 231 Mbps |

## Deployment Methods

### 1. Pre-staged KAPE via Falcon RTR

```python
def deploy_kape_prestaged(host_info):
    """Deploy KAPE to standard location for future use"""
    
    session = session_manager.start_session(host_info.aid)
    
    # Check if KAPE already exists
    check_cmd = "test -d C:\\Tools\\KAPE && echo EXISTS"
    result = session_manager.execute_command(session, "runscript", 
                                           f"runscript -Raw=```{check_cmd}```")
    
    if "EXISTS" in result.stdout:
        logger.info(f"KAPE already deployed on {host_info.hostname}")
        return True
    
    # Deploy KAPE
    commands = [
        "mkdir C:\\Tools\\KAPE",
        "cd C:\\Tools\\KAPE",
        "put kape.zip",
        "Expand-Archive -Path kape.zip -DestinationPath . -Force",
        "del kape.zip"
    ]
    
    for cmd in commands:
        session_manager.execute_command(session, "runscript", 
                                      f"runscript -Raw=```{cmd}```")
    
    return True
```

### 2. Dynamic Deployment Pattern

```python
def run_kape_collection(host_info, target="!BasicCollection"):
    """Execute KAPE with dynamic deployment"""
    
    # Upload KAPE to cloud files if needed
    ensure_kape_in_cloud(host_info.cid)
    
    session = session_manager.start_session(host_info.aid)
    
    # Create working directory
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    work_dir = f"C:\\0x4n6nerd\\{timestamp}"
    
    commands = [
        f"mkdir {work_dir}",
        f"cd {work_dir}",
        "put kape.zip",
        "Expand-Archive -Path kape.zip -DestinationPath .",
        f".\\kape.exe --tsource C: --tdest {work_dir}\\output --target {target} --zip"
    ]
    
    for cmd in commands:
        result = session_manager.execute_command(session, "runscript", 
                                               f"runscript -Raw=```{cmd}```")
        if not result or result.return_code != 0:
            logger.error(f"Command failed: {cmd}")
            return None
    
    return f"{work_dir}\\output"
```

### 3. Batch Collection Orchestration

```python
class KAPEOrchestrator:
    """Manage large-scale KAPE collections"""
    
    def __init__(self, max_concurrent=5):
        self.max_concurrent = max_concurrent
        self.active_collections = {}
        self.queue = Queue()
        
    def collect_batch(self, hosts, target="!BasicCollection", priority_map=None):
        """Collect from multiple hosts with priority handling"""
        
        # Sort by priority
        if priority_map:
            hosts.sort(key=lambda h: priority_map.get(h.hostname, 99))
        
        with ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
            futures = []
            
            for host in hosts:
                # Select target based on host type
                host_target = self.select_target(host, target)
                
                future = executor.submit(self.collect_single, host, host_target)
                futures.append((host, future))
            
            # Process results
            results = []
            for host, future in futures:
                try:
                    result = future.result(timeout=3600)  # 1 hour timeout
                    results.append({
                        "host": host.hostname,
                        "status": "success",
                        "output": result
                    })
                except Exception as e:
                    results.append({
                        "host": host.hostname,
                        "status": "failed",
                        "error": str(e)
                    })
            
            return results
    
    def select_target(self, host, default_target):
        """Select optimal target based on host characteristics"""
        
        # Quick collection for critical servers
        if "DC" in host.hostname or "SQL" in host.hostname:
            return "!BasicCollection"
        
        # Full collection for suspected compromised hosts
        if host.tags and "compromised" in host.tags:
            return "!SANS_Triage"
        
        # Browser focus for workstations
        if "WKS" in host.hostname:
            return "BrowsingHistory"
        
        return default_target
```

## Authentication and Security

### Service Account Configuration

```powershell
# Create KAPE service account
$password = ConvertTo-SecureString "ComplexPassword123!" -AsPlainText -Force
New-ADUser -Name "svc_kape" -AccountPassword $password -Enabled $true `
    -PasswordNeverExpires $true -CannotChangePassword $true

# Add to necessary groups
Add-ADGroupMember -Identity "Event Log Readers" -Members "svc_kape"
Add-ADGroupMember -Identity "Backup Operators" -Members "svc_kape"

# Grant specific permissions
$acl = Get-Acl "C:\Windows\System32\config"
$permission = "DOMAIN\svc_kape","ReadAndExecute","Allow"
$accessRule = New-Object System.Security.AccessControl.FileSystemAccessRule $permission
$acl.SetAccessRule($accessRule)
Set-Acl "C:\Windows\System32\config" $acl

# Configure for RTR usage
Grant-CsRTRRole -Identity "DOMAIN\svc_kape" -Role "RTR-Administrator"
```

### Least Privilege Implementation

```yaml
# KAPE execution permissions
RequiredPermissions:
  - SeBackupPrivilege       # File access
  - SeDebugPrivilege        # Process memory
  - SeSecurityPrivilege     # Audit logs
  - SeSystemProfilePrivilege # Performance data
  
RestrictedPaths:
  - C:\Windows\System32\config\SAM  # If not needed
  - C:\Users\*\NTUSER.DAT          # If user data excluded
```

## Monitoring and Management

### Real-time Collection Monitoring

```python
class KAPEMonitor:
    """Monitor KAPE collection progress"""
    
    def __init__(self):
        self.collections = {}
        self.metrics = defaultdict(list)
        
    def start_monitoring(self, host, target, session):
        """Begin monitoring a collection"""
        
        collection_id = f"{host}_{int(time.time())}"
        self.collections[collection_id] = {
            "host": host,
            "target": target,
            "start_time": time.time(),
            "status": "running",
            "progress": 0,
            "files_collected": 0,
            "size_collected": 0
        }
        
        # Start background monitoring
        Thread(target=self.monitor_progress, 
               args=(collection_id, session)).start()
        
        return collection_id
    
    def monitor_progress(self, collection_id, session):
        """Monitor KAPE console output for progress"""
        
        console_log = "C:\\0x4n6nerd\\temp\\console.log"
        
        while self.collections[collection_id]["status"] == "running":
            try:
                # Read console log
                result = session_manager.execute_command(
                    session, "runscript", 
                    f"runscript -Raw=```Get-Content {console_log} -Tail 50```"
                )
                
                if result and result.stdout:
                    # Parse progress
                    self.parse_progress(collection_id, result.stdout)
                
                time.sleep(10)  # Check every 10 seconds
                
            except Exception as e:
                logger.error(f"Monitoring error: {e}")
                break
    
    def parse_progress(self, collection_id, output):
        """Extract metrics from KAPE output"""
        
        # Example: "Processed 1,234 files in 00:05:23"
        files_match = re.search(r"Processed ([\d,]+) files", output)
        if files_match:
            files = int(files_match.group(1).replace(",", ""))
            self.collections[collection_id]["files_collected"] = files
        
        # Example: "Total: 1.23 GB"
        size_match = re.search(r"Total: ([\d.]+) ([GM]B)", output)
        if size_match:
            size = float(size_match.group(1))
            unit = size_match.group(2)
            if unit == "GB":
                size *= 1024
            self.collections[collection_id]["size_collected"] = size
```

### Performance Dashboard Integration

```python
def generate_kape_metrics():
    """Generate metrics for monitoring dashboards"""
    
    metrics = {
        "collections_active": len([c for c in monitor.collections.values() 
                                  if c["status"] == "running"]),
        "collections_completed_1h": len([c for c in monitor.collections.values() 
                                        if c["status"] == "completed" and 
                                        time.time() - c["start_time"] < 3600]),
        "avg_collection_time": statistics.mean([c["duration"] 
                                               for c in monitor.collections.values() 
                                               if "duration" in c]),
        "total_data_collected_gb": sum([c["size_collected"] 
                                       for c in monitor.collections.values()]) / 1024
    }
    
    # Push to monitoring system
    push_to_prometheus(metrics)
    push_to_splunk(metrics)
    
    return metrics
```

## High Availability Configuration

### Active-Passive Clustering

```powershell
# Configure Windows Failover Cluster for KAPE servers
Install-WindowsFeature -Name Failover-Clustering -IncludeManagementTools

# Create cluster
New-Cluster -Name "KAPE-Cluster" -Node "KAPE-01", "KAPE-02" `
    -StaticAddress "10.10.10.100"

# Add shared storage
Add-ClusterSharedVolume -Name "KAPE-Storage"

# Configure cluster role
Add-ClusterGenericServiceRole -Name "KAPE-Service" `
    -ServiceName "KAPECollectionService"
```

### Geographic Distribution

```yaml
# Multi-site deployment configuration
Sites:
  US-East:
    Servers: ["kape-use1", "kape-use2"]
    Storage: "\\nas-use\kape$"
    Endpoints: 2000
    
  US-West:
    Servers: ["kape-usw1", "kape-usw2"]
    Storage: "\\nas-usw\kape$"
    Endpoints: 1500
    
  Europe:
    Servers: ["kape-eu1", "kape-eu2"]
    Storage: "\\nas-eu\kape$"
    Endpoints: 1000
    
LoadBalancing:
  Method: "GeoIP"
  HealthCheck: "TCP:445"
  Failover: "Automatic"
```

## Compliance and Governance

### Data Retention Policies

```python
class KAPERetentionManager:
    """Manage collection retention and deletion"""
    
    def __init__(self, retention_days=90):
        self.retention_days = retention_days
        self.deletion_log = []
        
    def enforce_retention(self, storage_path):
        """Delete collections older than retention period"""
        
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        
        for collection in Path(storage_path).rglob("*.zip"):
            # Parse timestamp from filename
            # Format: hostname_20240315_123456.zip
            match = re.search(r"_(\d{8})_(\d{6})", collection.name)
            if match:
                date_str = match.group(1)
                collection_date = datetime.strptime(date_str, "%Y%m%d")
                
                if collection_date < cutoff_date:
                    # Log deletion
                    self.deletion_log.append({
                        "file": str(collection),
                        "date": collection_date,
                        "deleted_at": datetime.now(),
                        "size_mb": collection.stat().st_size / 1024 / 1024
                    })
                    
                    # Secure deletion
                    self.secure_delete(collection)
    
    def secure_delete(self, file_path):
        """Securely delete file with overwrite"""
        
        # Overwrite with random data
        size = file_path.stat().st_size
        with open(file_path, "wb") as f:
            f.write(os.urandom(size))
        
        # Delete file
        file_path.unlink()
```

### Chain of Custody

```python
def maintain_chain_of_custody(collection_id, actions):
    """Track all actions on evidence"""
    
    custody_record = {
        "collection_id": collection_id,
        "created": datetime.now().isoformat(),
        "actions": []
    }
    
    for action in actions:
        custody_record["actions"].append({
            "timestamp": datetime.now().isoformat(),
            "action": action["type"],
            "user": action["user"],
            "details": action["details"],
            "hash": calculate_hash(action["file"]) if "file" in action else None
        })
    
    # Save custody record
    with open(f"{collection_id}_custody.json", "w") as f:
        json.dump(custody_record, f, indent=2)
    
    # Sign with PKI
    sign_custody_record(f"{collection_id}_custody.json")
```

## Best Practices

1. **Pre-stage KAPE** on critical systems during maintenance windows
2. **Use tiered targets** - !BasicCollection first, then expand if needed
3. **Implement collection queuing** to prevent resource exhaustion
4. **Monitor performance metrics** and adjust concurrent collections
5. **Test failover procedures** regularly
6. **Document custom targets** with version control
7. **Train IR team** on KAPE capabilities and limitations
8. **Maintain evidence integrity** with hash verification
9. **Plan for growth** - 20-30% annual data increase
10. **Regular updates** via automated sync procedures

## Troubleshooting Enterprise Issues

### Common Problems and Solutions

| Issue | Cause | Solution |
|-------|-------|----------|
| Mass failures | Authentication | Verify service account permissions |
| Slow collections | Network congestion | Implement QoS for forensic traffic |
| Storage full | Retention not enforced | Automate cleanup procedures |
| Inconsistent results | Version mismatch | Centralize KAPE deployment |
| High CPU on endpoints | Too many concurrent | Reduce parallel collections |

### Debug Collection Issues

```powershell
# Enable detailed logging
$debugPath = "C:\0x4n6nerd\debug"
New-Item -ItemType Directory -Path $debugPath -Force

# Run with debug
& kape.exe --tsource C: --tdest $debugPath --target !BasicCollection `
    --debug --trace --vhdx %m-%d-debug

# Analyze results
Get-Content "$debugPath\console.log" | Select-String "ERROR|WARNING"
```

## Conclusion

Enterprise KAPE deployment requires careful planning but delivers transformative incident response capabilities. By following these guidelines, organizations can achieve consistent sub-10-minute collection times across thousands of endpoints while maintaining forensic integrity and operational efficiency.