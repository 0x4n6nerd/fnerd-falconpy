# UAC Enterprise Deployment Guide

This guide covers large-scale deployment strategies for UAC in enterprise environments using Falcon RTR.

## Deployment Architecture

### Overview

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Falcon    │────▶│     RTR      │────▶│   Target    │
│   Console   │     │   Session    │     │   Systems   │
└─────────────┘     └──────────────┘     └─────────────┘
                           │                      │
                           ▼                      ▼
                    ┌──────────────┐      ┌─────────────┐
                    │     UAC      │      │  Evidence   │
                    │  Deployment  │      │ Collection  │
                    └──────────────┘      └─────────────┘
                                                 │
                                                 ▼
                                          ┌─────────────┐
                                          │   S3/SFTP   │
                                          │   Storage   │
                                          └─────────────┘
```

## Deployment Methods

### 1. Direct RTR Deployment

**Advantages**: No pre-staging required, always latest version  
**Disadvantages**: Slower deployment, bandwidth usage

```python
def deploy_and_collect(host_info, profile="ir_triage"):
    """Deploy UAC and collect artifacts via RTR"""
    
    # Start RTR session
    session = session_manager.start_session(host_info.aid)
    
    # Deploy UAC
    commands = [
        "mkdir -p /opt/uac_temp",
        "cd /opt/uac_temp",
        "curl -L https://github.com/tclahr/uac/releases/latest/uac.tar.gz -o uac.tar.gz",
        "tar -xzf uac.tar.gz",
        "cd uac-*"
    ]
    
    for cmd in commands:
        session_manager.execute_command(session, "runscript", f"runscript -Raw=```{cmd}```")
    
    # Execute collection
    uac_cmd = f"./uac -p {profile} -S s3://evidence-bucket/{host_info.hostname} /tmp"
    session_manager.execute_command(session, "runscript", f"runscript -Raw=```{uac_cmd}```")
```

### 2. Pre-staged Deployment

**Advantages**: Faster execution, consistent version  
**Disadvantages**: Requires maintenance, storage space

```python
def prestaged_collection(host_info, profile="ir_triage"):
    """Use pre-deployed UAC installation"""
    
    session = session_manager.start_session(host_info.aid)
    
    # Check if UAC exists
    check_cmd = "test -d /opt/forensics/uac && echo 'EXISTS'"
    result = session_manager.execute_command(session, "runscript", f"runscript -Raw=```{check_cmd}```")
    
    if "EXISTS" not in result.stdout:
        # Fall back to deployment
        return deploy_and_collect(host_info, profile)
    
    # Run collection
    uac_cmd = f"/opt/forensics/uac/uac -p {profile} -S s3://evidence-bucket/{host_info.hostname} /tmp"
    session_manager.execute_command(session, "runscript", f"runscript -Raw=```{uac_cmd}```")
```

### 3. Cloud File Deployment

**Advantages**: Centralized management, version control  
**Disadvantages**: Requires cloud file upload

```python
def cloud_file_deployment(host_info, profile="ir_triage"):
    """Deploy UAC from Falcon cloud files"""
    
    # Check/upload UAC to cloud files
    cloud_files = file_manager.list_cloud_files(host_info.cid)
    if 'uac.tar.gz' not in cloud_files:
        file_manager.upload_to_cloud(host_info.cid, "/path/to/uac.tar.gz", 
                                   "UAC Deployment", "Forensic Collection Tool")
    
    session = session_manager.start_session(host_info.aid)
    
    # Deploy from cloud
    commands = [
        "mkdir -p /opt/uac_temp",
        "cd /opt/uac_temp",
        "put uac.tar.gz",
        "tar -xzf uac.tar.gz",
        "cd uac-*",
        f"./uac -p {profile} /tmp/evidence"
    ]
    
    for cmd in commands:
        session_manager.execute_command(session, "runscript", f"runscript -Raw=```{cmd}```")
```

## Batch Collection Strategies

### 1. Parallel Collection by CID

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

def batch_collect_by_cid(hosts, profile="ir_triage", max_workers=10):
    """Collect from multiple hosts grouped by CID"""
    
    # Group hosts by CID
    cid_groups = {}
    for host in hosts:
        cid = host['cid']
        if cid not in cid_groups:
            cid_groups[cid] = []
        cid_groups[cid].append(host)
    
    results = {}
    
    # Process each CID group
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit CID groups for processing
        future_to_cid = {
            executor.submit(process_cid_group, cid, hosts, profile): cid 
            for cid, hosts in cid_groups.items()
        }
        
        # Collect results
        for future in as_completed(future_to_cid):
            cid = future_to_cid[future]
            try:
                results[cid] = future.result()
            except Exception as e:
                print(f"CID {cid} failed: {e}")
                results[cid] = {"error": str(e)}
    
    return results

def process_cid_group(cid, hosts, profile):
    """Process all hosts in a CID"""
    cid_results = []
    
    # Upload UAC once per CID
    upload_uac_to_cloud(cid)
    
    # Collect from each host
    for host in hosts:
        try:
            result = collect_single_host(host, profile)
            cid_results.append(result)
        except Exception as e:
            cid_results.append({"host": host['hostname'], "error": str(e)})
    
    return cid_results
```

### 2. Priority-Based Collection

```python
class PriorityCollector:
    """Manage collections based on host priority"""
    
    def __init__(self, max_concurrent=5):
        self.max_concurrent = max_concurrent
        self.high_priority = []
        self.medium_priority = []
        self.low_priority = []
    
    def add_host(self, host, priority="medium"):
        """Add host to collection queue"""
        if priority == "high":
            self.high_priority.append(host)
        elif priority == "low":
            self.low_priority.append(host)
        else:
            self.medium_priority.append(host)
    
    def collect_all(self, profile="ir_triage"):
        """Process all hosts by priority"""
        results = {
            "high": self.process_queue(self.high_priority, profile),
            "medium": self.process_queue(self.medium_priority, profile),
            "low": self.process_queue(self.low_priority, profile)
        }
        return results
    
    def process_queue(self, queue, profile):
        """Process a priority queue"""
        with ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
            futures = [
                executor.submit(self.collect_with_profile, host, profile)
                for host in queue
            ]
            return [f.result() for f in as_completed(futures)]
    
    def collect_with_profile(self, host, profile):
        """Select appropriate profile based on host type"""
        # Customize profile based on host characteristics
        if "web" in host['hostname']:
            profile = "web_compromise"
        elif "db" in host['hostname']:
            profile = "database_focus"
        
        return collect_single_host(host, profile)
```

### 3. Time-Based Collection

```python
def staggered_collection(hosts, profile="ir_triage", window_hours=8):
    """Distribute collections over time window"""
    
    total_hosts = len(hosts)
    interval = (window_hours * 3600) / total_hosts
    
    results = []
    start_time = time.time()
    
    for i, host in enumerate(hosts):
        # Calculate when this host should be collected
        scheduled_time = start_time + (i * interval)
        current_time = time.time()
        
        # Wait if needed
        if current_time < scheduled_time:
            time.sleep(scheduled_time - current_time)
        
        # Collect
        print(f"Collecting from {host['hostname']} ({i+1}/{total_hosts})")
        result = collect_single_host(host, profile)
        results.append(result)
    
    return results
```

## Performance Optimization

### 1. Profile Selection Algorithm

```python
def select_optimal_profile(host_info, time_constraint=None, priority="balanced"):
    """Select best profile based on constraints"""
    
    profiles = {
        "quick_triage": {"time": 20, "coverage": 0.3},
        "ir_triage": {"time": 90, "coverage": 0.7},
        "full": {"time": 240, "coverage": 1.0}
    }
    
    if time_constraint:
        # Find best coverage within time limit
        valid_profiles = {
            name: info for name, info in profiles.items()
            if info["time"] <= time_constraint
        }
        if valid_profiles:
            return max(valid_profiles.items(), key=lambda x: x[1]["coverage"])[0]
    
    if priority == "speed":
        return "quick_triage"
    elif priority == "comprehensive":
        return "full"
    else:
        return "ir_triage"
```

### 2. Resource Management

```python
class ResourceManager:
    """Manage system resources during collection"""
    
    def __init__(self):
        self.active_collections = {}
        self.resource_limits = {
            "max_concurrent": 5,
            "max_bandwidth_mbps": 100,
            "max_cpu_percent": 50
        }
    
    def can_start_collection(self, host_info):
        """Check if resources available"""
        current_load = len(self.active_collections)
        return current_load < self.resource_limits["max_concurrent"]
    
    def start_collection(self, host_info, profile):
        """Register collection start"""
        self.active_collections[host_info.aid] = {
            "start_time": time.time(),
            "profile": profile,
            "hostname": host_info.hostname
        }
    
    def end_collection(self, aid):
        """Register collection end"""
        if aid in self.active_collections:
            duration = time.time() - self.active_collections[aid]["start_time"]
            del self.active_collections[aid]
            return duration
        return None
```

## Monitoring and Reporting

### 1. Collection Status Dashboard

```python
class CollectionMonitor:
    """Monitor ongoing collections"""
    
    def __init__(self):
        self.collections = {}
    
    def start_monitoring(self, host_info, profile):
        """Begin monitoring a collection"""
        self.collections[host_info.aid] = {
            "hostname": host_info.hostname,
            "profile": profile,
            "start_time": time.time(),
            "status": "running",
            "progress": 0
        }
    
    def update_progress(self, aid, progress, status="running"):
        """Update collection progress"""
        if aid in self.collections:
            self.collections[aid]["progress"] = progress
            self.collections[aid]["status"] = status
    
    def get_summary(self):
        """Get current status summary"""
        summary = {
            "total": len(self.collections),
            "running": sum(1 for c in self.collections.values() if c["status"] == "running"),
            "completed": sum(1 for c in self.collections.values() if c["status"] == "completed"),
            "failed": sum(1 for c in self.collections.values() if c["status"] == "failed")
        }
        return summary
```

### 2. Automated Reporting

```python
def generate_collection_report(results):
    """Generate collection summary report"""
    
    report = {
        "summary": {
            "total_hosts": len(results),
            "successful": sum(1 for r in results if r.get("status") == "success"),
            "failed": sum(1 for r in results if r.get("status") == "failed"),
            "total_data_gb": sum(r.get("size_mb", 0) for r in results) / 1024
        },
        "details": [],
        "recommendations": []
    }
    
    # Analyze results
    for result in results:
        detail = {
            "hostname": result["hostname"],
            "status": result["status"],
            "duration_minutes": result.get("duration", 0) / 60,
            "size_mb": result.get("size_mb", 0)
        }
        report["details"].append(detail)
    
    # Add recommendations
    avg_duration = sum(r.get("duration", 0) for r in results) / len(results)
    if avg_duration > 3600:  # 1 hour
        report["recommendations"].append(
            "Consider using quick_triage profile for faster collections"
        )
    
    return report
```

## Security Considerations

### 1. Evidence Integrity

```python
def secure_collection(host_info, profile):
    """Collect with integrity verification"""
    
    session = session_manager.start_session(host_info.aid)
    
    # Generate collection ID
    collection_id = f"{host_info.hostname}_{int(time.time())}"
    
    # Run collection with hash
    commands = [
        f"./uac -p {profile} --hash-collected /tmp/{collection_id}",
        f"sha256sum /tmp/{collection_id}/* > /tmp/{collection_id}.hashes"
    ]
    
    for cmd in commands:
        session_manager.execute_command(session, "runscript", f"runscript -Raw=```{cmd}```")
    
    # Upload with verification
    upload_with_verification(session, collection_id)
```

### 2. Access Control

```python
class AccessController:
    """Manage collection permissions"""
    
    def __init__(self):
        self.authorized_users = set()
        self.audit_log = []
    
    def authorize_collection(self, user, host, profile):
        """Check if user can collect from host"""
        # Check user authorization
        if user not in self.authorized_users:
            self.audit_log.append({
                "user": user,
                "action": "unauthorized_attempt",
                "host": host,
                "timestamp": time.time()
            })
            return False
        
        # Log authorized action
        self.audit_log.append({
            "user": user,
            "action": "collection_started",
            "host": host,
            "profile": profile,
            "timestamp": time.time()
        })
        
        return True
```

## Integration Examples

### 1. SOAR Integration

```python
def soar_collection_playbook(alert_data):
    """Automated collection based on SOAR alert"""
    
    # Extract host information from alert
    hostname = alert_data.get("hostname")
    severity = alert_data.get("severity")
    
    # Select profile based on severity
    profile_map = {
        "critical": "full",
        "high": "ir_triage",
        "medium": "quick_triage",
        "low": "network_focus"
    }
    
    profile = profile_map.get(severity, "ir_triage")
    
    # Get host info from Falcon
    host_info = get_host_info(hostname)
    
    # Execute collection
    result = collect_with_uac(host_info, profile)
    
    # Update SOAR case
    update_case(alert_data["case_id"], {
        "forensic_collection": result,
        "collection_time": time.time()
    })
    
    return result
```

### 2. Scheduled Collections

```python
def scheduled_baseline_collection():
    """Regular baseline collections for comparison"""
    
    critical_hosts = get_critical_hosts()
    
    for host in critical_hosts:
        try:
            # Use minimal profile for baselines
            result = collect_single_host(host, "quick_triage")
            
            # Store baseline
            store_baseline(host["hostname"], result)
            
        except Exception as e:
            log_error(f"Baseline collection failed for {host['hostname']}: {e}")
```

## Best Practices

1. **Profile Selection**
   - Use `quick_triage` for initial assessment
   - Use `ir_triage` for standard investigations
   - Reserve `full` for critical incidents

2. **Resource Management**
   - Limit concurrent collections to 5-10 per Console
   - Stagger large-scale collections
   - Monitor system impact

3. **Evidence Handling**
   - Use S3 versioning for integrity
   - Implement retention policies
   - Maintain chain of custody logs

4. **Performance**
   - Pre-stage UAC for critical systems
   - Use SSD storage paths when available
   - Exclude unnecessary artifacts

5. **Security**
   - Restrict RTR permissions appropriately
   - Audit all collection activities
   - Encrypt evidence in transit and at rest