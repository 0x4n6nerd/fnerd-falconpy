# KAPE Performance Optimization Guide

## Overview

KAPE (Kroll Artifact Parser and Extractor) revolutionizes Windows forensics by collecting artifacts in **under 10 minutes** compared to hours with traditional disk imaging. This guide provides detailed performance metrics, optimization strategies, and enterprise scaling considerations.

## Performance Benchmarks

### Collection Time by Target

| Target | Duration | Data Size | Files Collected | Use Case |
|--------|----------|-----------|-----------------|----------|
| !BasicCollection | 2-5 min | 100-500 MB | 1,000-5,000 | Quick triage |
| KapeTriage | 15-30 min | 1-5 GB | 10,000-50,000 | Full triage |
| RegistryHives | 30-60 sec | 50-200 MB | 20-50 | Registry analysis |
| EventLogs | 1-3 min | 100 MB-2 GB | 50-200 | Log investigation |
| FileSystem | 5-10 min | 500 MB-2 GB | Metadata only | Timeline creation |
| BrowsingHistory | 2-5 min | 200 MB-1 GB | 100-1,000 | Web activity |
| !SANS_Triage | 10-20 min | 1-3 GB | 5,000-20,000 | SANS methodology |
| MemoryFiles | 1-2 min | 2-8 GB | 5-10 | Memory analysis |

### Optimized Target Performance

| Investigation Type | Traditional | Optimized | Time Saved | Data Reduction |
|-------------------|-------------|-----------|------------|----------------|
| Emergency Triage | 15-30 min | 2-5 min | 80-85% | 70-80% |
| Malware Analysis | 45-60 min | 5-15 min | 75-80% | 85-90% |
| Ransomware Response | 20-30 min | 3-8 min | 70-85% | 80-90% |
| Insider Threat | 30-45 min | 15-20 min | 50-55% | 60-70% |
| APT Investigation | 60+ min | 30+ min | 50% | 40-50% |

### Processing Time by Module

| Module | Duration per GB | CPU Usage | Memory Usage | Output Size |
|--------|-----------------|-----------|--------------|-------------|
| EvtxECmd | 2-5 min | High (80-100%) | 200-500 MB | 2-5x input |
| MFTECmd | 5-10 min | Medium (40-60%) | 500 MB-1 GB | 1-2x input |
| RECmd | 1-3 min | Low (20-40%) | 100-300 MB | 0.5x input |
| PECmd | 30 sec | Low (10-20%) | 50-100 MB | 0.1x input |
| !EZParser | 15-30 min | High (60-80%) | 1-2 GB | 3-5x input |

## Critical Performance Improvements

### Sparse File Handling (v0.83+)
**Before**: FileSystem target took 300+ seconds due to sparse $J file processing  
**After**: Optimized to ~30 seconds with intelligent sparse file detection  
**Impact**: 10x performance improvement for file system collections

### Key Optimizations
1. **SHA-1 Deduplication**: Reduces collection size by 20-40% for system files
2. **Queue-Based Processing**: Handles locked files without retry delays
3. **VSS Smart Processing**: Avoids duplicate collection across shadow copies
4. **Memory Streaming**: Prevents loading large files entirely into memory

## Hardware Impact on Performance

### Storage Type Comparison

| Storage Type | Random IOPS | Sequential MB/s | Collection Impact |
|--------------|-------------|-----------------|-------------------|
| HDD (7200rpm) | 100-200 | 100-150 | Baseline (1x) |
| SATA SSD | 50,000 | 500-600 | 5-10x faster |
| NVMe SSD | 200,000+ | 2,000-7,000 | 20-100x faster |
| Network (1GbE) | Variable | 100-125 | 0.5-1x speed |
| Network (10GbE) | Variable | 1,000-1,250 | 5-10x faster |

### CPU and Memory Requirements

| Concurrent Collections | CPU Cores | RAM Required | Optimal Config |
|-----------------------|-----------|--------------|----------------|
| 1-5 | 4-8 | 8-16 GB | Desktop/Laptop |
| 5-20 | 8-16 | 16-32 GB | Workstation |
| 20-50 | 16-32 | 32-64 GB | Server |
| 50-100 | 32-64 | 64-128 GB | Enterprise |
| 100+ | 64+ | 128+ GB | Data Center |

## Target Selection Impact on Performance

### Key Optimization Techniques

1. **Size Filtering**: MinSize/MaxSize properties eliminate 70-90% of irrelevant data
2. **Path Specificity**: Exact paths vs wildcards improve speed by 5-10x
3. **Selective Recursion**: Disable when not needed to avoid deep traversal
4. **FileMask Precision**: Regex patterns for targeted collection

### Investigation-Specific Optimization

```yaml
# Example: Emergency Triage (2-5 minutes instead of 30+)
Name: EmergencyTriage
Targets:
  - Path: C:\Windows\System32\config
    FileMask: "SAM|SECURITY|SOFTWARE|SYSTEM"
    MaxSize: 268435456  # 256MB limit
    AlwaysAddToQueue: true
```

## Optimization Strategies

### 1. Storage Optimization
```powershell
# Use RAM disk for ultra-fast processing
New-VHD -Path R:\temp.vhdx -SizeBytes 10GB -Dynamic
Mount-VHD -Path R:\temp.vhdx
Initialize-Disk -Number $diskNumber
New-Volume -DiskNumber $diskNumber -FileSystem NTFS -DriveLetter R

# Direct to fast storage
kape.exe --tdest R:\collections --target !BasicCollection
```

### 2. Parallel Processing
```powershell
# Optimal: 3-5 concurrent KAPE instances
$targets = @("WebBrowsers", "RegistryHives", "EventLogs", "FileSystem")
$jobs = @()

foreach ($target in $targets) {
    $jobs += Start-Job -ScriptBlock {
        param($t)
        & C:\KAPE\kape.exe --target $t --tdest "C:\Output\$t"
    } -ArgumentList $target
}

Wait-Job $jobs
```

### 3. Target Optimization
```yaml
# Custom lean target for quick collection
Description: Quick Malware Triage
Targets:
  - Name: Critical Artifacts Only
    Path: C:\Windows\Prefetch\
    FileMask: "*.pf"
    MaxSize: 10485760  # Skip files over 10MB
    Comment: "Recent execution only"
```

### 4. VSS Optimization
```bash
# Limit VSS to recent snapshots only
kape.exe --target RegistryHives --vss 3  # Last 3 snapshots only

# Skip VSS for speed
kape.exe --target FileSystem --no-vss
```

## Enterprise Scaling

### Network Bandwidth Calculations

| Endpoints | Data per Host | Total Data | Time Window | Required Bandwidth |
|-----------|---------------|------------|-------------|-------------------|
| 100 | 2 GB | 200 GB | 1 hour | 444 Mbps |
| 1,000 | 2 GB | 2 TB | 8 hours | 69 Mbps |
| 5,000 | 1 GB | 5 TB | 24 hours | 48 Mbps |
| 10,000 | 500 MB | 5 TB | 24 hours | 48 Mbps |

### Storage Requirements

```
Daily Collection = Endpoints × Average_Collection_Size × Collections_Per_Day
Monthly Storage = Daily_Collection × Retention_Days × Compression_Ratio

Example (5000 endpoints):
- Daily: 5000 × 1GB × 1 = 5TB
- Monthly (90-day retention, 0.3 compression): 5TB × 90 × 0.3 = 135TB
```

### Infrastructure Design

#### Collection Tier
- **Servers**: 1 per 100 concurrent collections
- **Specs**: 16 cores, 64GB RAM, 10GbE NIC
- **Storage**: 2TB NVMe for staging

#### Processing Tier
- **Servers**: 1 per 500 endpoints
- **Specs**: 32 cores, 128GB RAM
- **Storage**: 10TB SSD array

#### Storage Tier
```
Active (0-30 days): NVMe SSD - 15TB
Recent (31-90 days): SATA SSD - 45TB  
Archive (90+ days): HDD Array - 500TB+
```

## Common Bottlenecks and Solutions

### 1. Sparse File Issues
**Problem**: $USN Journal taking excessive time  
**Solution**: Update to KAPE 0.83+ with sparse file optimization

### 2. Memory Exhaustion
**Problem**: Large registry hives causing OutOfMemory  
**Solution**: Use `--ul` (use linear) flag for sequential processing

### 3. Network Timeouts
**Problem**: Remote collection failing on slow links  
**Solution**: Stage locally first, then transfer
```bash
# Stage locally
kape.exe --tsource C: --tdest C:\temp\stage --target !BasicCollection

# Compress and transfer
7z a -mx=9 collection.7z C:\temp\stage\*
robocopy C:\temp \\server\share collection.7z /Z /R:3
```

### 4. Locked Files
**Problem**: Critical files in use  
**Solution**: KAPE automatically uses raw disk access
```yaml
# Force raw mode in target
AlwaysAddToQueue: true
SaveAsVariable: false
```

## Performance Monitoring

### Real-time Metrics
```powershell
# Monitor KAPE performance
$kapeProcess = Get-Process kape -ErrorAction SilentlyContinue
while ($kapeProcess) {
    $cpu = $kapeProcess.CPU
    $mem = $kapeProcess.WorkingSet64 / 1MB
    $handles = $kapeProcess.HandleCount
    
    Write-Host "$([DateTime]::Now) - CPU: $cpu, Mem: $mem MB, Handles: $handles"
    Start-Sleep -Seconds 5
    $kapeProcess = Get-Process kape -ErrorAction SilentlyContinue
}
```

### Collection Statistics
```powershell
# Parse KAPE console log for metrics
$log = Get-Content "C:\temp\KAPE_console.log"
$metrics = @{
    FilesFound = ($log | Select-String "Found: (\d+)" -AllMatches).Matches.Value
    FilesCopied = ($log | Select-String "Copied: (\d+)" -AllMatches).Matches.Value
    TotalSize = ($log | Select-String "bytes \(([^)]+)\)" -AllMatches).Matches.Value
    Duration = ($log | Select-String "Total execution time" -AllMatches).Line
}
```

## Best Practices for Speed

1. **Pre-position KAPE** on endpoints to avoid deployment time
2. **Use compound targets** to minimize overhead
3. **Enable deduplication** with `--dedupe` flag
4. **Limit collection scope** with MinSize/MaxSize
5. **Use batch mode** for multiple operations
6. **Avoid unnecessary modules** during collection phase
7. **Process offline** when possible to reduce endpoint impact
8. **Use fast compression** (ZIP with store method) for network transfer
9. **Implement collection queuing** to avoid resource contention
10. **Monitor and alert** on performance degradation

## Quick Reference

### Speed Comparison
| Method | 10GB System | 100GB System | 1TB System |
|--------|-------------|--------------|------------|
| Full Disk Image | 30-60 min | 5-10 hours | 2-3 days |
| KAPE Triage | 5-10 min | 15-30 min | 30-60 min |
| KAPE Basic | 2-5 min | 5-10 min | 10-20 min |

### Command Optimization
```bash
# Emergency Response (2-5 minutes)
kape.exe --tsource C: --tdest C:\out --target EmergencyTriage

# Malware Investigation (5-15 minutes)
kape.exe --tsource C: --tdest C:\out --target MalwareAnalysis --dedupe

# Ransomware Response (3-8 minutes)
kape.exe --tsource C: --tdest C:\out --target RansomwareResponse --vss 2

# Traditional Collection (15-30 minutes)
kape.exe --tsource C: --tdest C:\out --target !BasicCollection --dedupe --vss

# Comprehensive (30+ minutes)
kape.exe --tsource C: --tdest C:\out --target !SANS_Triage --dedupe --vss --zip
```

### Target Optimization Benefits

| Optimization | Impact | Example |
|--------------|--------|------|
| MinSize Filter | Excludes empty/corrupt files | MinSize: 1024 (1KB) |
| MaxSize Filter | Prevents huge file collection | MaxSize: 104857600 (100MB) |
| Path Specificity | 5-10x faster traversal | C:\Windows\System32\config vs C:\* |
| FileMask Regex | Precise matching | regex:.*\.(exe\|dll\|scr)$ |
| No Recursion | Avoids deep searches | Recursive: false |

## Conclusion

KAPE's performance advantages stem from its targeted collection approach, intelligent file handling, and modular architecture. By following these optimization strategies and understanding the performance characteristics, organizations can achieve sub-10-minute incident response times while maintaining forensic integrity. The key is balancing speed with completeness based on investigation requirements.