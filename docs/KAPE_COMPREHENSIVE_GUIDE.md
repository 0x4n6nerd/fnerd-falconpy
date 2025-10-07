# KAPE (Kroll Artifact Parser and Extractor) Comprehensive Guide

## Overview

KAPE is the de facto standard for Windows digital forensics, capable of collecting and processing critical artifacts in **under 10 minutes** compared to hours with traditional imaging. Developed by Eric Zimmerman at Kroll, this modular framework supports **over 500 community-contributed targets** and seamlessly integrates with major forensic toolchains.

## Key Features

- **Speed-Focused Design**: Collects Windows artifacts in 2-10 minutes vs hours for full disk imaging
- **Dual-Phase Architecture**: Collection (Targets) and Processing (Modules) phases
- **Zero-Dependency Deployment**: Portable executable requiring only .NET Framework
- **Extensive Artifact Coverage**: Over 100 built-in targets covering all Windows forensic categories
- **Community-Driven**: 500+ community-contributed targets with Git synchronization
- **Enterprise-Ready**: Scales from single workstations to thousands of endpoints

## Quick Start

```bash
# Basic triage collection (2-5 minutes)
kape.exe --tsource C: --tdest C:\temp\case --target !BasicCollection

# Comprehensive collection with processing (15-30 minutes)
kape.exe --tsource C: --tdest C:\temp\case --target KapeTriage --mdest C:\temp\case\parsed --module !EZParser

# VSS collection for historical data
kape.exe --tsource C: --tdest C:\temp\case --target RegistryHives --vss

# Remote collection
kape.exe --tsource \\COMPUTERNAME\C$ --tdest C:\collections\%m-%d --target !SANS_Triage
```

## Performance Benchmarks

### Collection Times

| Target | Typical Duration | Data Volume | Use Case |
|--------|-----------------|-------------|----------|
| !BasicCollection | 2-5 minutes | 100-500 MB | Initial triage |
| KapeTriage | 15-30 minutes | 1-5 GB | Comprehensive triage |
| RegistryHives | 30-60 seconds | 50-200 MB | Registry analysis |
| EventLogs | 1-3 minutes | 100 MB-2 GB | Log analysis |
| FileSystem | 5-10 minutes | 500 MB-2 GB | Timeline creation |
| !SANS_Triage | 10-20 minutes | 1-3 GB | SANS methodology |

### Performance Optimizations

1. **Sparse File Handling** (v0.83+): Reduces FileSystem collection from 300+ to ~30 seconds
2. **SHA-1 Deduplication**: Eliminates redundant file collection
3. **Queue-Based Processing**: Handles locked files through raw disk reads
4. **Parallel Execution**: 3-5 concurrent instances optimal per endpoint

## Built-in Targets

### Registry Targets
- **System Hives**: SAM, SECURITY, SOFTWARE, SYSTEM
- **User Hives**: NTUSER.DAT, UsrClass.dat
- **Transaction Logs**: Registry .LOG files
- **Backups**: RegBack directory contents

### Event Log Targets
- **Core Logs**: Security, System, Application
- **PowerShell**: Operational and analytic logs
- **RDP**: TerminalServices logs
- **WMI**: WMI-Activity traces
- **50+ Specialized Logs**: Office, Exchange, IIS, etc.

### File System Targets
- **$MFT**: Master File Table for complete file listing
- **$J**: USN Journal for recent file changes (1-7 days)
- **Prefetch**: Application execution evidence
- **Recycle Bin**: Deleted file metadata
- **Jump Lists**: Recent document access

### Browser Artifacts
- **Chromium-Based**: History, Cookies, Cache, Downloads
- **Firefox**: places.sqlite, form history, sessions
- **Internet Explorer**: WebCacheV*.dat parsing
- **Edge**: Both legacy and Chromium versions

### Application Artifacts
- **Microsoft Office**: Recent documents, trusted locations
- **Cloud Storage**: OneDrive, Dropbox, Google Drive logs
- **Communication**: Teams, Slack, Discord databases
- **Development**: Git repositories, IDE configurations

## Compound Targets

### !BasicCollection
Minimal triage collection including:
- Critical registry hives
- Recent user activity
- Basic system information
- 2-5 minute collection time

### KapeTriage
Comprehensive triage including:
- All registry hives with backups
- Event logs (Security, System, Application)
- Browser artifacts
- File system metadata
- 15-30 minute collection time

### !SANS_Triage
SANS methodology-based collection:
- Execution artifacts
- Account usage
- File/folder access
- Network activity
- 10-20 minute collection time

## Custom Target Creation

### Basic YAML Structure
```yaml
Description: Custom malware investigation target
Author: Your Name
Version: 1.0
Id: unique-guid-here
RecreateDirectories: true
Targets:
  - Name: Suspicious Executables
    Category: Malware
    Path: C:\
    Recursive: true
    FileMask: "*.exe"
    MinSize: 1024
    MaxSize: 10485760  # 10MB
    Comment: "Collect executables under 10MB"
```

### Advanced Features
```yaml
# Using variables
Path: C:\Users\%user%\AppData\

# Regular expressions
FileMask: regex:.*\.(exe|dll|scr|bat|ps1)$

# Volume Shadow Copies
ProcessVSS: true
Dedupe: true

# Conditional collection
OnlyIfPresent: C:\malware\indicator.txt
```

## Module System

### Core Processing Modules

#### EvtxECmd
Parses Windows event logs to CSV:
```bash
--module EvtxECmd
```
- Processes all EVTX files
- Normalizes fields
- Outputs timeline-ready CSV

#### MFTECmd
Processes Master File Table:
```bash
--module MFTECmd
```
- Full file system timeline
- Deleted file recovery
- Timestamp analysis

#### RECmd (Registry)
Registry analysis via RegRipper:
```bash
--module RECmd_AllBatchFiles
```
- Automated artifact extraction
- USB device history
- User activity analysis

### Compound Modules

#### !EZParser
Runs all Eric Zimmerman tools:
- Automatic tool selection
- Consistent CSV output
- Timeline integration

## Enterprise Deployment

### Infrastructure Requirements

#### Collection Servers
- **CPU**: 16+ cores per 100 concurrent collections
- **RAM**: 64GB minimum
- **Storage**: NVMe SSD for active collections
- **Network**: 10GbE recommended

#### Storage Architecture
```
Tier 1 (Active): NVMe SSD - 30 days
Tier 2 (Recent): SATA SSD - 90 days  
Tier 3 (Archive): HDD Array - Long-term
```

### Deployment Methods

#### Group Policy
```powershell
# Deploy KAPE via GPO
Copy-Item \\share\KAPE C:\Tools\KAPE -Recurse
New-ItemProperty -Path "HKLM:\Software\KAPE" -Name "Version" -Value "3.0.0.0"
```

#### PowerShell Remoting
```powershell
# Remote collection
Invoke-Command -ComputerName $targets -ScriptBlock {
    & C:\Tools\KAPE\kape.exe --tsource C: --tdest D:\Collections\$env:COMPUTERNAME --target !BasicCollection
}
```

#### SCCM/ConfigMgr
- Package KAPE as application
- Deploy to collection
- Monitor compliance

### Authentication & Security

#### Required Permissions
- Local logon rights
- Administrative share access (C$, ADMIN$)
- Registry read permissions
- Event log access

#### Service Account Setup
```powershell
# Create dedicated service account
New-ADUser -Name "svc_kape" -AccountPassword $pwd -Enabled $true
Add-ADGroupMember -Identity "Event Log Readers" -Members "svc_kape"
Grant-LogonAsService -Identity "DOMAIN\svc_kape"
```

## Investigation Workflows

### Malware Investigation
```bash
# Quick assessment (5 minutes)
kape.exe --target Prefetch,RecentFileCache --mdest C:\analysis --module PECmd

# Deep analysis (30 minutes)
kape.exe --target KapeTriage,MemoryFiles --mdest C:\analysis --module !EZParser,Volatility
```

### Ransomware Response
```bash
# Emergency collection (2-5 minutes)
kape.exe --target EventLogs,VSS --vss --mdest C:\incident

# Full analysis (30+ minutes)
kape.exe --target !BasicCollection,FileSystem --mdest C:\incident --module Timeline
```

### Insider Threat
```bash
# User activity focus
kape.exe --target BrowsingHistory,CloudStorage,USBDevices --mdest C:\investigation
```

## Performance Tuning

### Optimization Strategies

1. **Use Local NVMe Storage**: 100x faster than HDDs
2. **Enable Deduplication**: `--dedupe` flag
3. **Limit VSS Depth**: `--vss 3` for last 3 snapshots
4. **Parallel Processing**: Run 3-5 instances concurrently
5. **Network Optimization**: SMB 3.0 multichannel

### Resource Management
```bash
# CPU throttling
start /low kape.exe [parameters]

# Memory limiting
kape.exe --ul  # Use linear processing

# Batch mode for multiple targets
Create _kape.cli with sequential commands
```

### Common Bottlenecks

| Issue | Solution |
|-------|----------|
| Sparse files ($J) | Update to v0.83+ |
| Large registry hives | Use streaming mode |
| Network latency | Local staging first |
| Memory exhaustion | --ul flag |

## Integration Examples

### Plaso/Timeline
```bash
# Generate super timeline
log2timeline.py timeline.plaso C:\collections\
psort.py -o dynamic timeline.plaso timeline.csv
```

### X-Ways Forensics
- Import VHD/VHDX containers directly
- Maintains hash verification
- Preserves metadata

### SIEM Integration
```python
# Splunk ingestion
[monitor://C:\KAPE_Output\*.csv]
disabled = false
sourcetype = kape_timeline
index = forensics
```

## Troubleshooting

### Common Issues

| Error | Cause | Solution |
|-------|-------|----------|
| Access Denied | Insufficient privileges | Run as administrator |
| Module not found | Missing binary | Run --sync to update |
| Network timeout | Firewall blocking | Check SMB ports |
| VSS errors | Shadow copies disabled | Enable VSS service |
| File monitoring timeout | VHDX to .7z conversion timing | Fixed with two-phase monitoring (v1.2.0) |

### KAPE File Processing (v1.2.0+)

**VHDX to .7z Workflow**: KAPE creates VHDX files during collection, then post-processes to .7z format:

1. **Phase 1**: VHDX creation and completion (main collection)
2. **Phase 2**: VHDX to .7z conversion (background process)

**Monitoring**: Falcon client uses two-phase monitoring to handle this workflow properly:
- Monitors VHDX file stability first (5-minute timeout)
- Then monitors .7z conversion completion (10-minute timeout)
- Provides detailed logging for each phase

### Debug Mode
```bash
# Enable comprehensive logging
kape.exe --debug --trace [parameters]

# Check console log
type C:\temp\KAPE_console.log
```

## Best Practices

1. **Start with !BasicCollection** for quick triage
2. **Use compound targets** for consistency
3. **Enable deduplication** for efficiency
4. **Document custom targets** with clear descriptions
5. **Test targets** on representative systems
6. **Monitor resource usage** during collections
7. **Maintain chain of custody** with hash verification
8. **Regular updates** via --sync command

## Advanced Techniques

### Dynamic Target Creation
```yaml
# Runtime variable substitution
Path: C:\Users\%user%\AppData\Local\%app%\
SaveAsVariable: UserAppData

# Conditional processing
OnlyIfPresent: C:\Program Files\TargetApp\
AlwaysAddToQueue: true
```

### Module Chaining
```yaml
# Process then analyze
Executable: parser.exe
CommandLine: -f %sourceFile% -o %destinationDirectory%
ExportFormat: csv
Append: true
```

### Performance Monitoring
```powershell
# Track collection metrics
Measure-Command {
    & kape.exe --target KapeTriage --mdest C:\output
} | Select-Object TotalMinutes, TotalSeconds
```

## Resources

- **GitHub**: https://github.com/EricZimmerman/KapeFiles
- **Documentation**: https://ericzimmerman.github.io/KapeDocs/
- **Training**: SANS FOR508, FOR500
- **Community**: DFIR Discord, Twitter #DFIR

## Conclusion

KAPE revolutionizes Windows forensics by reducing collection times from hours to minutes while maintaining forensic integrity. Its modular architecture, extensive target library, and active community support make it indispensable for modern incident response. Whether conducting quick triage or comprehensive investigations, KAPE provides the speed, flexibility, and reliability required for effective Windows forensics.