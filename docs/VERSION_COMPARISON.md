# Version Comparison: v1.0.0 vs v1.1.0 vs v1.2.0

## Overview

This document provides a detailed comparison between 4n6NerdStriker versions, highlighting major features and improvements:
- v1.1.0: Added UAC (Unix-like Artifacts Collector) support
- v1.2.0: Critical performance improvements, race condition fixes, and upload verification for KAPE

## Feature Comparison

### Forensic Collection

| Feature | v1.0.0 | v1.1.0 | v1.2.0 |
|---------|--------|--------|--------|
| KAPE (Windows) | ✅ | ✅ | ✅ Enhanced |
| UAC (Unix/Linux/macOS) | ❌ | ✅ | ✅ |
| Cross-platform forensics | Partial | Complete | Complete |
| Dynamic upload monitoring | ❌ | ❌ | ✅ |
| File stability verification | ❌ | ❌ | ✅ |
| Auto-cleanup deployment | ❌ | ❌ | ✅ |

### Platform Coverage

| Platform | v1.0.0 | v1.1.0 | v1.2.0 |
|----------|--------|--------|--------|
| Windows forensics | KAPE | KAPE | KAPE (Enhanced) |
| Linux forensics | ❌ | UAC | UAC |
| macOS forensics | ❌ | UAC | UAC |
| Unix/BSD forensics | ❌ | UAC | UAC |

### Performance Improvements

| Metric | v1.0.0 | v1.1.0 | v1.2.0 |
|--------|--------|--------|--------|
| KAPE upload wait time | Fixed 25 min | Fixed 25 min | Dynamic (2-20 min) |
| KAPE race condition fix | ❌ | ❌ | ✅ Two-phase monitoring |
| Deployment reliability | Basic | Basic | Enhanced |
| Time savings per collection | Baseline | Baseline | 5-25 minutes |

### CLI Commands

#### v1.0.0
```bash
4n6nerdstriker kape        # Windows only
4n6nerdstriker browser_history
4n6nerdstriker rtr
4n6nerdstriker isolate
4n6nerdstriker release
4n6nerdstriker isolation-status
```

#### v1.1.0 (New)
```bash
4n6nerdstriker kape        # Windows only
4n6nerdstriker uac         # Unix/Linux/macOS (NEW)
4n6nerdstriker browser_history
4n6nerdstriker rtr
4n6nerdstriker isolate
4n6nerdstriker release
4n6nerdstriker isolation-status
```

### API Methods

#### v1.0.0
```python
# Orchestrator methods
orchestrator.run_kape_collection()
orchestrator.collect_browser_history()
orchestrator.isolate_host()
orchestrator.release_host()

# Batch operations (Optimized)
orchestrator.run_kape_batch()
orchestrator.browser_history_batch()
```

#### v1.1.0 (New)
```python
# Orchestrator methods
orchestrator.run_kape_collection()
orchestrator.run_uac_collection()        # NEW
orchestrator.collect_browser_history()
orchestrator.isolate_host()
orchestrator.release_host()

# Batch operations (Optimized)
orchestrator.run_kape_batch()
orchestrator.run_uac_batch()             # NEW
orchestrator.browser_history_batch()
```

## Code Changes

### New Files (v1.1.0)
- `forensics_nerdstriker/collectors/uac_collector.py` - UAC collector implementation
- `forensics_nerdstriker/resources/uac/README.md` - UAC setup instructions
- `examples/uac_usage.py` - UAC usage examples
- `RELEASE_NOTES_v1.1.0.md` - Release documentation
- `CHANGELOG.md` - Version history tracking
- `docs/FEATURE_MATRIX.md` - Comprehensive feature overview
- `docs/VERSION_COMPARISON.md` - This document

### Modified Files (v1.1.0)
1. `forensics_nerdstriker/__init__.py` - Added UACCollector export
2. `forensics_nerdstriker/collectors/__init__.py` - Added UACCollector import
3. `forensics_nerdstriker/orchestrator.py` - Added run_uac_collection method
4. `forensics_nerdstriker/orchestrator_optimized.py` - Added run_uac_batch method
5. `forensics_nerdstriker/cli/main.py` - Added uac subcommand
6. `forensics_nerdstriker/core/configuration.py` - Added UAC_SETTINGS
7. `README.md` - Added UAC examples
8. `CLAUDE.md` - Added UAC implementation details
9. `pyproject.toml` - Version bump to 1.1.0

## Configuration Changes

### v1.0.0
```python
# Configuration focused on KAPE
KAPE_SETTINGS = {
    "base_path": "C:\\workspace",
    "temp_path": "C:\\workspace\\temp",
    # ...
}
```

### v1.1.0 (New)
```python
# Added UAC configuration
UAC_SETTINGS = {
    "base_path": "/tmp/uac_collection",
    "evidence_path": "/tmp/uac_collection/evidence",
    "monitoring_interval": 30,
    "default_profile": "ir_triage",
    "timeout": 3600,
    "available_profiles": [
        "ir_triage", "full", "offline",
        "logs", "memory_dump", "files", "network"
    ]
}
```

## Performance Impact

- No performance degradation for existing features
- UAC operations use same optimized patterns as KAPE
- Batch operations supported for UAC collections
- Session pooling and caching work across both collectors

## Migration Notes

### For Users
- No breaking changes - v1.0.0 code continues to work
- New UAC functionality is additive
- Download UAC package separately for Unix forensics

### For Developers
- UACCollector follows same patterns as ForensicCollector
- Platform validation prevents cross-platform misuse
- Same error handling and logging patterns

## Testing Coverage

### v1.0.0
- KAPE collection tests (Windows)
- Browser history tests (all platforms)
- RTR session tests
- Host isolation tests

### v1.1.0 (Additional)
- UAC collection tests (Unix/Linux/macOS)
- Platform validation tests
- Batch UAC operation tests
- Cross-platform forensics tests

## Documentation Updates

### New Documentation (v1.1.0)
- UAC setup guide in resources directory
- UAC usage examples
- Feature matrix showing all capabilities
- Version comparison (this document)
- Release notes for v1.1.0

### Updated Documentation
- README with UAC examples
- Architecture docs with UAC details
- Collectors module documentation
- CLI help text

## Future Compatibility

The v1.1.0 architecture ensures:
- Easy addition of new forensic tools
- Platform-specific collectors can be added
- Existing patterns support new collectors
- No breaking changes needed for future tools

## Version Highlights

### v1.1.0 - Cross-Platform Forensics
- Added UAC support for Unix/Linux/macOS forensics
- Complete cross-platform coverage
- Batch operations for UAC collections
- Full backward compatibility

### v1.2.0 - Performance & Reliability
- **KAPE Race Condition Fix**: Two-phase monitoring resolves VHDX to .7z conversion timing
- **Universal S3 Upload Verification**: Eliminates false upload failures across platforms
- Dynamic KAPE upload monitoring (5-25 minute time savings)
- ZIP file stability verification system
- Complete deployment cleanup procedures
- Enhanced RTR command compatibility

## Summary

- **v1.1.0** brought complete cross-platform forensic collection capabilities
- **v1.2.0** delivers critical performance improvements and reliability enhancements
- All versions maintain full backward compatibility
- Each release builds upon previous functionality without breaking changes