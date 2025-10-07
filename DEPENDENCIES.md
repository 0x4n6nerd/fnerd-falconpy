# Dependencies Guide

fnerd-falconpy relies on two external forensic collection tools. These tools are **not included** in this repository and must be obtained from their official sources.

## Required Third-Party Tools

### 1. KAPE (Kroll Artifact Parser and Extractor)

**Purpose**: Windows forensic artifact collection
**Author**: Eric Zimmerman
**License**: Free for personal/commercial use
**Official Repository**: https://github.com/EricZimmerman/KapeFiles

#### What You Need:
- **KAPE Executable**: `kape.exe` (from official KAPE distribution)
- **KAPE Files**: Target and module files from the KapeFiles repository

#### How to Obtain:

1. **Get KAPE Binary**:
   - Download KAPE from the official source: https://www.kroll.com/en/services/cyber-risk/incident-response-litigation-support/kroll-artifact-parser-extractor-kape
   - OR use the community version if available
   - Extract to a temporary location

2. **Get KAPE Files** (Targets and Modules):
   ```bash
   git clone https://github.com/EricZimmerman/KapeFiles.git
   ```

3. **Prepare for fnerd-falconpy**:
   ```bash
   # Create the resources directory structure
   mkdir -p fnerd_falconpy/resources/kape

   # Copy KAPE binary
   cp /path/to/kape.exe fnerd_falconpy/resources/kape/

   # Copy KAPE Targets and Modules
   cp -r /path/to/KapeFiles/Targets fnerd_falconpy/resources/kape/
   cp -r /path/to/KapeFiles/Modules fnerd_falconpy/resources/kape/
   ```

4. **Create kape.zip** (required by fnerd-falconpy):
   ```bash
   cd fnerd_falconpy/resources
   zip -r kape.zip kape/
   ```

#### KAPE Files Attribution:
The KAPE target and module files are created and maintained by **Eric Zimmerman** and the community.
- Repository: https://github.com/EricZimmerman/KapeFiles
- Updated regularly with new artifacts and modules

#### Custom KAPE Targets:
This repository **does include** custom `.tkape` target files created specifically for fnerd-falconpy:
- `RansomwareResponse.tkape` - Ransomware incident response artifacts
- `EmergencyTriage.tkape` - Quick emergency triage collection
- `MalwareAnalysis.tkape` - Malware analysis artifacts

These custom targets are located in `fnerd_falconpy/resources/kape/Targets/Custom/` and will work with the official KAPE Files.

---

### 2. UAC (Unix-like Artifacts Collector)

**Purpose**: Unix/Linux/macOS forensic artifact collection
**Author**: Tclahr (Thiago Canozzo Lahr)
**License**: Apache License 2.0
**Official Repository**: https://github.com/tclahr/uac

#### What You Need:
- UAC binary/script for target platforms (Linux, macOS, Unix)

#### How to Obtain:

1. **Download UAC**:
   ```bash
   # Clone the official repository
   git clone https://github.com/tclahr/uac.git

   # OR download the latest release
   curl -L https://github.com/tclahr/uac/releases/latest/download/uac-VERSION.tar.gz -o uac.tar.gz
   tar -xzf uac.tar.gz
   ```

2. **Prepare for fnerd-falconpy**:
   ```bash
   # Create the resources directory
   mkdir -p fnerd_falconpy/resources/uac

   # Copy UAC files
   cp -r /path/to/uac/* fnerd_falconpy/resources/uac/

   # Create uac.zip (required by fnerd-falconpy)
   cd fnerd_falconpy/resources/uac
   zip -r ../uac.zip .
   ```

#### UAC Profiles:
fnerd-falconpy includes custom UAC collection profiles optimized for incident response:
- `ir_triage` - Quick incident response triage
- `ir_triage_no_hash` - IR triage without file hashing (faster)
- `full` - Comprehensive collection
- `quick_triage_optimized` - Optimized quick collection
- And more (see `fnerd_falconpy/resources/uac/profiles/`)

---

## Automated Setup Script

For convenience, you can use the provided setup script:

```bash
# Run the dependency setup helper
./scripts/setup_dependencies.sh
```

This script will:
1. Check if KAPE and UAC are already configured
2. Provide download instructions and links
3. Verify directory structure
4. Create required .zip archives

---

## Verification

After setting up dependencies, verify your installation:

```bash
# Test the installation
python test/test_installation.py

# Check resources directory
ls -lh fnerd_falconpy/resources/
# Expected: kape.zip, uac.zip, deploy_kape.ps1, deploy_uac.sh
```

You should see:
```
fnerd_falconpy/resources/
├── kape/                  # KAPE files (not in git)
│   ├── kape.exe
│   ├── Targets/
│   └── Modules/
├── kape.zip              # Created from kape/ (not in git)
├── uac/                  # UAC files (not in git)
│   └── uac
├── uac.zip               # Created from uac/ (not in git)
├── deploy_kape.ps1       # Deployment script (in git)
└── deploy_uac.sh         # Deployment script (in git)
```

---

## File Size Reference

After setup, expect these approximate sizes:
- `kape.zip`: ~74 MB
- `kape/` directory: ~88 MB
- `uac.zip`: ~20-30 MB
- `uac/` directory: ~30-40 MB

**Total**: ~200-250 MB of third-party tools (excluded from git repository)

---

## Why Not Include These in the Repository?

1. **Licensing**: KAPE and UAC have their own licenses and should be obtained from official sources
2. **Size**: ~200MB+ of binaries would bloat the repository
3. **Updates**: Users should get the latest versions from official sources
4. **Attribution**: Proper credit to the original authors by directing users to their repositories
5. **Maintenance**: Tool authors maintain and update their own distributions

---

## Credits

### KAPE (Kroll Artifact Parser and Extractor)
- **Author**: Eric Zimmerman (@EricZimmerman)
- **Website**: https://www.kroll.com/kape
- **KapeFiles Repository**: https://github.com/EricZimmerman/KapeFiles
- **License**: Free for personal and commercial use

### UAC (Unix-like Artifacts Collector)
- **Author**: Thiago Canozzo Lahr (@tclahr)
- **Repository**: https://github.com/tclahr/uac
- **License**: Apache License 2.0

---

## Support

If you encounter issues with:
- **KAPE**: Refer to the official KAPE documentation and GitHub issues
- **UAC**: Check the UAC repository issues page
- **fnerd-falconpy integration**: Open an issue in this repository

---

## Additional Resources

### KAPE Resources:
- KAPE Documentation: https://ericzimmerman.github.io/KapeDocs/
- KAPE Training: https://www.kroll.com/kape
- Community Targets: https://github.com/EricZimmerman/KapeFiles

### UAC Resources:
- UAC Documentation: https://github.com/tclahr/uac/wiki
- UAC Releases: https://github.com/tclahr/uac/releases
- UAC Community: https://github.com/tclahr/uac/discussions
