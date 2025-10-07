# KAPE Target Selection and Optimization Guide

## Overview

Strategic KAPE target selection can reduce collection times from 30+ minutes to under 5 minutes while eliminating 70-90% of irrelevant data. This guide provides comprehensive strategies for creating and selecting optimal KAPE targets based on investigation type and performance requirements.

## Key Performance Metrics

| Collection Type | Traditional Time | Optimized Time | Data Reduction | Improvement |
|-----------------|------------------|----------------|----------------|-------------|
| Basic Triage | 15-30 minutes | 3-5 minutes | 70-80% | 80% faster |
| Malware Analysis | 45-60 minutes | 8-12 minutes | 85-90% | 75% faster |
| Registry Focus | 10-15 minutes | 2-3 minutes | 90-95% | 85% faster |
| Browser Artifacts | 20-25 minutes | 4-6 minutes | 75-85% | 78% faster |
| Insider Threat | 30-45 minutes | 15-20 minutes | 60-70% | 50% faster |

## Target Architecture Fundamentals

### Core Target Properties

```yaml
Name: TargetName              # Unique identifier
Category: CategoryName        # Organizational grouping
Path: C:\Windows\System32    # Directory path (always a directory)
FileMask: "*.exe"            # File filtering pattern
Recursive: true              # Subdirectory traversal (default: false)
MinSize: 1024               # Minimum file size in bytes
MaxSize: 10485760           # Maximum file size in bytes
AlwaysAddToQueue: true      # Force raw disk access for locked files
```

### Performance Optimization Principles

1. **Path Specificity**: Use exact paths instead of wildcards in Path property
2. **Size Filtering**: Apply MinSize/MaxSize to eliminate irrelevant files
3. **Selective Recursion**: Enable only when necessary to avoid deep traversal
4. **FileMask Precision**: Use specific patterns or regex for targeted collection

## Investigation-Specific Target Strategies

### 1. Rapid Emergency Response (2-5 Minutes)

**Goal**: Immediate triage for active incidents

```yaml
Name: EmergencyTriage
Category: Triage
Description: Critical artifacts for immediate incident assessment
Targets:
  - Name: CoreRegistry
    Path: C:\Windows\System32\config
    FileMask: "SAM|SECURITY|SOFTWARE|SYSTEM"
    MaxSize: 268435456  # 256MB
    AlwaysAddToQueue: true
    
  - Name: RecentEvents
    Path: C:\Windows\System32\winevt\Logs
    FileMask: "Security.evtx|System.evtx|Application.evtx"
    MinSize: 65536      # 64KB minimum
    MaxSize: 104857600  # 100MB maximum
    
  - Name: CurrentProcesses
    Path: C:\Windows\Prefetch
    FileMask: "*.pf"
    MinSize: 1024
    MaxSize: 2097152    # 2MB
```

### 2. Malware Investigation (5-15 Minutes)

**Goal**: Identify and analyze malicious activity

```yaml
Name: MalwareAnalysis
Category: Malware
Description: Focused collection for malware investigations
Targets:
  - Name: ExecutionEvidence
    Path: C:\Windows\Prefetch
    FileMask: "*.pf"
    MinSize: 1024
    MaxSize: 2097152
    
  - Name: PersistenceRegistry
    Path: C:\Windows\System32\config
    FileMask: "SOFTWARE|SYSTEM"
    AlwaysAddToQueue: true
    
  - Name: StartupFolders
    Path: C:\Users\%user%\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup
    FileMask: "*"
    Recursive: true
    MaxSize: 10485760
    
  - Name: ScheduledTasks
    Path: C:\Windows\System32\Tasks
    FileMask: "*"
    Recursive: true
    MaxSize: 1048576
    
  - Name: RecentDocuments
    Path: C:\Users\%user%\AppData\Roaming\Microsoft\Windows\Recent
    FileMask: "*.lnk"
    MaxSize: 1048576
```

### 3. Ransomware Response (3-8 Minutes)

**Goal**: Rapid collection for ransomware incidents

```yaml
Name: RansomwareResponse
Category: Ransomware
Description: Emergency ransomware investigation artifacts
Targets:
  - Name: FileSystemChanges
    Path: C:\$Extend
    FileMask: "$UsnJrnl*"
    AlwaysAddToQueue: true
    
  - Name: RansomNotes
    Path: C:\Users
    FileMask: "*.txt|*.hta|*.html|README*|DECRYPT*|RECOVER*"
    Recursive: true
    MinSize: 100
    MaxSize: 10240     # 10KB max for ransom notes
    
  - Name: CryptoWallets
    Path: C:\Users\%user%\AppData
    FileMask: "wallet.dat|*.wallet"
    Recursive: true
    MaxSize: 104857600
    
  - Name: ShadowCopyInfo
    Path: C:\Windows\System32\winevt\Logs
    FileMask: "System.evtx|Application.evtx"
    MaxSize: 209715200  # 200MB
```

### 4. Insider Threat Investigation (15-30 Minutes)

**Goal**: Comprehensive user activity analysis

```yaml
Name: InsiderThreat
Category: UserActivity
Description: User behavior and data exfiltration artifacts
Targets:
  - Name: BrowserHistory
    Path: C:\Users\%user%\AppData\Local\Google\Chrome\User Data\Default
    FileMask: "History|Cookies|Web Data|Login Data"
    MinSize: 1024
    
  - Name: EmailArtifacts
    Path: C:\Users\%user%\AppData\Local\Microsoft\Outlook
    FileMask: "*.pst|*.ost"
    MinSize: 1048576   # 1MB minimum
    
  - Name: FileAccess
    Path: C:\Users\%user%\AppData\Roaming\Microsoft\Windows\Recent
    FileMask: "*.lnk"
    
  - Name: USBHistory
    Path: C:\Windows\System32\config
    FileMask: "SYSTEM"
    AlwaysAddToQueue: true
    
  - Name: CloudStorage
    Path: C:\Users\%user%
    FileMask: "*.log"
    Recursive: true
    MaxSize: 10485760
```

### 5. APT Investigation (30+ Minutes)

**Goal**: Deep forensic analysis for sophisticated threats

```yaml
Name: APTComprehensive
Category: APT
Description: Comprehensive collection for advanced persistent threats
Targets:
  - Name: CompleteRegistry
    Path: C:\Windows\System32\config
    FileMask: "*"
    AlwaysAddToQueue: true
    
  - Name: AllEventLogs
    Path: C:\Windows\System32\winevt\Logs
    FileMask: "*.evtx"
    
  - Name: MemoryArtifacts
    Path: C:\Windows\Memory
    FileMask: "*"
    
  - Name: NetworkArtifacts
    Path: C:\Windows\System32\LogFiles
    FileMask: "*"
    Recursive: true
```

## Advanced Target Optimization Techniques

### 1. Size-Based Filtering

```yaml
# Optimize registry collection by size
Name: RegistryOptimized
Path: C:\Windows\System32\config
FileMask: "SOFTWARE|SYSTEM|SAM|SECURITY"
MinSize: 32768      # 32KB minimum (exclude corrupted)
MaxSize: 536870912  # 512MB maximum (exclude bloated)
```

### 2. Regex Pattern Matching

```yaml
# Time-based event log collection
Name: RecentEventLogs
Path: C:\Windows\System32\winevt\Logs
FileMask: "regex:(Security|System|Application).*\.evtx"

# Suspicious file patterns
Name: SuspiciousFiles
Path: C:\Users
FileMask: "regex:.*\.(exe|dll|scr|bat|cmd|ps1|vbs|js)$"
Recursive: true
MinSize: 1024
MaxSize: 5242880  # 5MB
```

### 3. Variable Expansion

```yaml
# User profile expansion
Path: C:\Users\%user%\AppData\Local

# System drive detection
Path: %s%\Windows\System32\config

# Timestamp insertion
Path: C:\Logs\%d%
```

### 4. Compound Target Creation

```yaml
# Efficient compound target structure
Name: OptimizedIRTriage
Description: Streamlined incident response collection
Targets:
  - Name: CriticalRegistry
    Path: CompoundTargets\CriticalRegistry.tkape
  - Name: RecentExecution
    Path: CompoundTargets\RecentExecution.tkape
  - Name: NetworkActivity
    Path: CompoundTargets\NetworkActivity.tkape
  - Name: UserActivity
    Path: CompoundTargets\UserActivity.tkape
```

## Performance Optimization Strategies

### Path Optimization

**Inefficient:**
```yaml
Path: C:\Users\*\AppData\*\*
FileMask: "*"
Recursive: true
```

**Optimized:**
```yaml
Path: C:\Users\%user%\AppData\Local\Microsoft\Windows\WebCache
FileMask: "WebCacheV*.dat"
Recursive: false
```

### Targeted Collection

**Before (Collect Everything):**
- Collection Time: 45+ minutes
- Data Volume: 10-20 GB
- Analysis Noise: High

**After (Targeted Collection):**
- Collection Time: 5-10 minutes
- Data Volume: 500MB-2GB
- Analysis Focus: High

### VSS Integration

```yaml
# Historical registry analysis
Name: RegistryHistorical
Path: C:\Windows\System32\config
FileMask: "SOFTWARE|SYSTEM"
AlwaysAddToQueue: true
# Use with: --vss 3 (last 3 shadow copies)
```

## Enterprise Deployment

### Tiered Collection Strategy

#### Tier 1: Emergency Response (2-5 minutes)
- Core registry hives
- Recent event logs
- Current execution evidence
- Active network connections

#### Tier 2: Standard Investigation (10-15 minutes)
- Full registry collection
- Extended event logs
- Browser artifacts
- User activity indicators

#### Tier 3: Comprehensive Analysis (30+ minutes)
- Complete system artifacts
- All VSS snapshots
- Memory dumps
- Full file system metadata

### Automated Target Selection

```powershell
# PowerShell target selection based on indicators
function Select-KapeTarget {
    param([string]$IncidentType)
    
    $targetMap = @{
        "Ransomware" = "RansomwareResponse"
        "Malware" = "MalwareAnalysis"
        "Insider" = "InsiderThreat"
        "BEC" = "EmailCompromise"
        "APT" = "APTComprehensive"
        "Unknown" = "OptimizedIRTriage"
    }
    
    return $targetMap[$IncidentType]
}

# Usage
$target = Select-KapeTarget -IncidentType "Ransomware"
& kape.exe --target $target --tdest C:\Evidence
```

## Custom Target Templates

### Web Server Compromise

```yaml
Name: WebServerCompromise
Category: WebServer
Targets:
  - Name: IISLogs
    Path: C:\inetpub\logs\LogFiles
    FileMask: "*.log"
    Recursive: true
    MaxSize: 104857600
    
  - Name: WebShells
    Path: C:\inetpub\wwwroot
    FileMask: "*.aspx|*.asp|*.php|*.jsp"
    Recursive: true
    MinSize: 100
    MaxSize: 1048576
```

### Database Server Investigation

```yaml
Name: DatabaseInvestigation
Category: Database
Targets:
  - Name: SQLServerLogs
    Path: C:\Program Files\Microsoft SQL Server
    FileMask: "ERRORLOG*"
    Recursive: true
    MaxSize: 52428800
    
  - Name: DatabaseFiles
    Path: C:\Program Files\Microsoft SQL Server
    FileMask: "*.mdf|*.ldf"
    MaxSize: 1073741824  # 1GB limit
```

## Validation and Testing

### Pre-Deployment Checklist

1. **Syntax Validation**
   ```bash
   kape.exe --tlist  # List all targets
   kape.exe --tdetail TargetName  # Validate specific target
   ```

2. **Performance Testing**
   ```powershell
   Measure-Command {
       & kape.exe --target CustomTarget --tdest C:\Test
   }
   ```

3. **Coverage Verification**
   - Verify all critical artifacts collected
   - Check file size distributions
   - Validate collection completeness

## Best Practices

1. **Always use MinSize** to exclude empty/corrupted files
2. **Set reasonable MaxSize** limits based on investigation needs
3. **Avoid excessive recursion** in large directory structures
4. **Use specific FileMask** patterns over wildcards
5. **Test targets on representative systems** before deployment
6. **Document custom targets** with clear descriptions
7. **Version control** target configurations
8. **Regular review** and optimization of target performance
9. **Monitor collection metrics** for continuous improvement
10. **Train investigators** on target selection strategies

## Conclusion

Optimized KAPE target selection transforms forensic collection from a time-consuming, data-heavy process to a rapid, focused investigation tool. By implementing these strategies:

- Reduce collection times by 75-95%
- Decrease data volumes by 70-90%
- Improve investigation focus and efficiency
- Enable rapid incident response at scale

The key is understanding that effective forensics isn't about collecting everything—it's about collecting the right artifacts for each specific investigation context.