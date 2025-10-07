# 4n6NerdStriker Feature Matrix

**Version**: 1.3.0 - Production Ready  
**Last Updated**: June 8, 2025

## Platform Support Matrix

| Feature | Windows | Linux | macOS | Unix/BSD | Status |
|---------|---------|-------|-------|----------|--------|
| KAPE Collection | ✅ | ❌ | ❌ | ❌ | 🟢 Production (100% success) |
| UAC Collection | ❌ | ✅ | ✅ | ✅ | 🟢 Production (All profiles stable) |
| Triage (Auto-detect) | ✅ | ✅ | ✅ | ✅ | 🟢 Production (New in v1.3.0) |
| Browser History | ✅ | ✅ | ✅ | ❌ | 🟢 Production |
| Interactive RTR | ✅ | ✅ | ✅ | ✅ | 🟢 Production |
| Host Isolation | ✅ | ✅ | ✅ | ✅ | 🟢 Production |
| Batch Operations | ✅ | ✅ | ✅ | ✅ | 🟢 Production |
| S3 Upload | ✅ | ✅ | ✅ | ✅ | 🟢 Production (Enhanced verification) |

## Forensic Collection Capabilities

### KAPE (Windows Only) - 🟢 100% Success Rate (11/11 targets tested)
| Target | Description | Collection Time | Status |
|--------|-------------|-----------------|--------|
| RegistryHives | Windows registry | 6 mins | ✅ Production |
| EventLogs | Windows event logs | 6 mins | ✅ Production |
| EmergencyTriage | Emergency response | 8 mins | ✅ Production |
| MalwareAnalysis | Malware investigation | 8 mins | ✅ Production |
| USBDetective | USB device forensics | 8 mins | ✅ Production |
| FileSystem | File metadata | 9 mins | ✅ Production |
| RansomwareResponse | Ransomware artifacts | 11 mins | ✅ Production |
| KapeTriage | Standard triage | 19 mins | ✅ Production |
| !BasicCollection | Essential forensics | 20 mins | ✅ Production |
| WebBrowsers | Browser artifacts | 2-5 mins | ✅ Production |
| !SANS_Triage | Comprehensive triage | 35 mins | ✅ Production |
| ServerTriage | Windows Server specific | N/A | ⚠️ Requires Windows Server |

### UAC (Unix/Linux/macOS) - 🟢 All 6 Profiles Stable
| Profile | Description | Collection Time | Status |
|---------|-------------|-----------------|--------|
| quick_triage_optimized | Essential artifacts only | 15-20 mins | ✅ Production |
| network_compromise | Network intrusion focus | 25-30 mins | ✅ Production |
| ir_triage_no_hash | Full IR without hashing | 35-40 mins | ✅ Production |
| malware_hunt_fast | Malware with selective hashing | 45-50 mins | ✅ Production |
| ir_triage | Complete IR triage | 79 mins | ✅ Production |
| full | Comprehensive collection | 6+ hours | ✅ Production |

### Triage (Mixed Environments) - 🟢 New in v1.3.0
| Feature | Description | Capability |
|---------|-------------|------------|
| Auto OS Detection | Automatic platform detection | ✅ Windows/Linux/macOS |
| Concurrent Execution | Parallel collections | ✅ ThreadPoolExecutor |
| Default Profiles | Smart defaults | Windows (!SANS_TRIAGE), Unix (ir_triage_no_hash) |
| Custom Override | Profile/target override | ✅ Full customization |

## Browser Support

| Browser | Windows | macOS | Linux |
|---------|---------|-------|-------|
| Chrome | ✅ | ✅ | ✅ |
| Firefox | ✅ | ✅ | ✅ |
| Edge | ✅ | ✅ | ❌ |
| Brave | ✅ | ✅ | ✅ |
| Opera | ✅ | ❌ | ❌ |
| Safari | ❌ | 🔄 | ❌ |

Legend: ✅ Supported | ❌ Not Supported | 🔄 Planned

## RTR Command Support

### Read-Only Commands
| Command | Windows | Linux/macOS | Description |
|---------|---------|-------------|-------------|
| cat | ✅ | ✅ | View file contents |
| cd | ✅ | ✅ | Change directory |
| ls | ✅ | ✅ | List directory |
| ps | ✅ | ✅ | List processes |
| pwd | ✅ | ✅ | Show current directory |

### Active Responder Commands
| Command | Windows | Linux/macOS | Description |
|---------|---------|-------------|-------------|
| get | ✅ | ✅ | Retrieve file |
| zip | ✅ | ✅ | Create archive |
| map | ✅ | ❌ | Map network drive |

### Admin Commands
| Command | Windows | Linux/macOS | Description |
|---------|---------|-------------|-------------|
| put | ✅ | ✅ | Upload file |
| run | ✅ | ✅ | Execute binary |
| runscript | ✅ | ✅ | Run script |
| mkdir | ✅ | ✅ | Create directory |
| rm | ✅ | ✅ | Remove file |
| mv | ✅ | ✅ | Move/rename file |

## API Methods

### Core Orchestrator Methods
| Method | Standard | Optimized | Description |
|--------|----------|-----------|-------------|
| run_kape_collection | ✅ | ✅ | Windows forensics |
| run_uac_collection | ✅ | ✅ | Unix forensics |
| collect_browser_history | ✅ | ✅ | Browser artifacts |
| isolate_host | ✅ | ✅ | Network containment |
| release_host | ✅ | ✅ | Remove isolation |
| get_isolation_status | ✅ | ✅ | Check status |

### Batch Operations (Optimized Only)
| Method | Description | Max Concurrent |
|--------|-------------|----------------|
| run_kape_batch | Multiple KAPE collections | 20 |
| run_uac_batch | Multiple UAC collections | 20 |
| browser_history_batch | Multiple browser collections | 20 |

### Triage Operations (New in v1.3.0)
| Method | Description | Capability |
|--------|-------------|------------|
| process_triage_single | Single host triage | Auto OS detection |
| process_triage_concurrent | Multi-host triage | Concurrent execution |

## Performance Characteristics

### Single Host Operations
| Operation | Typical Duration | Data Size |
|-----------|------------------|-----------|
| KAPE Triage | 15-30 mins | 100MB-2GB |
| UAC Triage | 10-20 mins | 50MB-1GB |
| Browser History | 2-5 mins | 10-100MB |
| RTR Session | Interactive | N/A |

### Batch Operations (10 hosts)
| Operation | Sequential | Concurrent | Speedup |
|-----------|------------|------------|---------|
| KAPE | 150-300 mins | 30-60 mins | 5x |
| UAC | 100-200 mins | 20-40 mins | 5x |
| Browser | 20-50 mins | 5-10 mins | 4x |

## S3 Upload Structure

```
bucket/
├── kape/
│   └── hostname/
│       └── YYYY-MM-DDTHHMM_hostname-triage.7z
├── uac/
│   └── hostname/
│       └── uac-hostname-os-YYYYMMDDTHHmmss.tar.gz
└── browser_history/
    └── hostname/
        └── username-Browser-Profile-History.7z
```

## Resource Requirements

### Client System (Running 4n6nerdstriker)
- Python 3.10+
- 2GB RAM minimum
- 10GB disk space for temporary files
- Network access to CrowdStrike APIs

### Target Systems
| Component | Windows | Linux/macOS |
|-----------|---------|-------------|
| KAPE | Pre-installed at C:\workspace | N/A |
| UAC | N/A | No pre-install required |
| RTR Agent | Falcon Sensor 6.0+ | Falcon Sensor 6.0+ |
| Disk Space | 5GB free | 5GB free |

## Security Considerations

### Authentication
- OAuth2 client credentials required
- API permissions needed:
  - `hosts:read/write`
  - `real-time-response:read/write`
  - `real-time-response-admin:write`

### Data Protection
- All transfers use TLS encryption
- S3 uploads support encryption at rest
- No credentials stored in collected data
- Sensitive paths excluded by default

## Version History

| Version | Release Date | Major Features | Status |
|---------|--------------|----------------|--------|
| 1.0.0 | 2025-01-20 | Initial release with KAPE, browser history, RTR | Stable |
| 1.1.0 | 2025-01-27 | Added UAC support for Unix/Linux/macOS | Stable |
| 1.2.0 | 2025-05-31 | Enhanced upload monitoring, performance fixes | Stable |
| 1.3.0 | 2025-06-08 | **🎉 Production release: KAPE 100% success, UAC all profiles stable, new Triage feature** | **🟢 Production Ready** |

## Limitations

1. **KAPE**: Windows only, requires pre-deployment
2. **UAC**: Not supported on Windows
3. **File Size**: 5GB maximum per file transfer
4. **API Rate Limits**: Subject to CrowdStrike API quotas
5. **Concurrent Sessions**: Limited by CrowdStrike license
6. **Browser Support**: Limited on some platforms

## Future Roadmap

- [ ] Memory dump collection for all platforms
- [ ] Custom artifact definitions
- [ ] Automated analysis pipelines
- [ ] Additional cloud storage providers
- [ ] Enhanced progress reporting
- [ ] Offline collection support