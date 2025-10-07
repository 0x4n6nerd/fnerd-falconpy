# Git LFS Setup for 4n6NerdStriker

## Overview

This project contains large binary files (forensic tools, executables, and archives) that are tracked using Git Large File Storage (LFS). This keeps the repository size manageable while still versioning these important files.

## Files Tracked by Git LFS

- **Compressed Archives**: `*.zip`, `*.tar.gz`, `*.7z`
- **Windows Executables**: `*.exe`, `*.dll`, `*.msi`
- **KAPE Tools**: ~74MB of forensic collection tools
- **UAC Tools**: ~8.5MB of Unix artifact collectors
- **Binary Forensic Tools**: Various executables in the modules directory
- **Large JSON Files**: Discovery output files

Total LFS storage: ~200MB

## Setup Instructions

### 1. Install Git LFS

**macOS:**
```bash
brew install git-lfs
```

**Ubuntu/Debian:**
```bash
sudo apt-get install git-lfs
```

**Windows:**
Download and install from [https://git-lfs.github.com/](https://git-lfs.github.com/)

### 2. Run Setup Script

We've provided a setup script to configure Git LFS:

```bash
./setup_git_lfs.sh
```

This script will:
- Verify Git LFS is installed
- Initialize Git LFS in the repository
- Migrate existing large files if needed
- Verify tracking configuration

### 3. Manual Setup (Alternative)

If you prefer manual setup:

```bash
# Initialize Git LFS
git lfs install

# The .gitattributes file already tracks the necessary files
# Just ensure it's committed
git add .gitattributes
git commit -m "Add Git LFS tracking configuration"

# If you have existing commits with large files
git lfs migrate import --include="*.zip" --everything
git lfs migrate import --include="*.exe" --everything
```

## For Contributors

When cloning this repository:

```bash
# Clone with LFS files
git clone https://github.com/0x4n6nerd/4n6NerdStriker.git

# If you already cloned without LFS
git lfs pull
```

## Verification

To verify Git LFS is working correctly:

```bash
# Check tracked patterns
git lfs track

# List LFS files
git lfs ls-files

# Check LFS status
git lfs status
```

## GitHub LFS Quotas

- **Free tier**: 1 GB storage, 1 GB bandwidth per month
- **This project**: ~200MB storage requirement
- **Recommendation**: Should fit comfortably in free tier for small teams

If you need more storage/bandwidth, you can purchase additional LFS data packs from GitHub.

## Troubleshooting

### "This exceeds GitHub's file size limit of 100.00 MB"

This means Git LFS is not properly configured. Run:
```bash
git lfs track "*.zip"
git add .gitattributes
git commit -m "Track large files with Git LFS"
```

### "Smudge error" when cloning

This usually means Git LFS is not installed. Install it and run:
```bash
git lfs install
git lfs pull
```

### Files downloading as text pointers

This happens when LFS is not initialized. Run:
```bash
git lfs fetch
git lfs checkout
```

## Important Notes

1. **First Push**: The initial push to GitHub will take longer as it uploads all LFS objects
2. **Build Directory**: The `build/` directory is gitignored, so those duplicates won't be pushed
3. **Binary Files**: All forensic tool executables are tracked via LFS to keep the repo lightweight
4. **Credentials**: Never commit AWS credentials or API keys - use environment variables

## Files Not Tracked

The following are explicitly excluded from the repository:
- `build/` directory (build artifacts)
- `.env` files (credentials)
- `venv/` and `.venv/` (Python virtual environments)
- `*.log` files
- Temporary files and caches