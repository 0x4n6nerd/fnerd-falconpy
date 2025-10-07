#!/usr/bin/env python3
"""
UAC Update Script

This script checks for updates to the Unix-like Artifacts Collector (UAC) and downloads
the latest version if available. It should be run separately from the main falcon-client
runtime to avoid network delays during forensic collection.

Usage:
    python scripts/update_uac.py [--force]
    
Options:
    --force    Force download even if current version is up to date
"""

import os
import sys
import argparse
import requests
import json
import shutil
from pathlib import Path
from typing import Optional, Tuple
import hashlib


def get_latest_release_info() -> Tuple[str, str]:
    """
    Get the latest UAC release information from GitHub
    
    Returns:
        Tuple of (version, download_url)
    """
    try:
        # Get latest release info from GitHub API
        response = requests.get(
            "https://api.github.com/repos/tclahr/uac/releases/latest",
            headers={"Accept": "application/vnd.github.v3+json"},
            timeout=10
        )
        response.raise_for_status()
        
        release_data = response.json()
        version = release_data["tag_name"]
        
        # Find the UAC tar.gz asset
        download_url = None
        for asset in release_data.get("assets", []):
            if asset["name"].endswith(".tar.gz") and "uac" in asset["name"]:
                download_url = asset["browser_download_url"]
                break
        
        if not download_url:
            # Construct URL based on version
            version_clean = version.lstrip('v')
            download_url = f"https://github.com/tclahr/uac/releases/download/{version}/uac-{version_clean}.tar.gz"
        
        return version, download_url
        
    except Exception as e:
        print(f"Error getting latest release info: {e}")
        sys.exit(1)


def get_current_version(uac_path: Path) -> Optional[str]:
    """
    Get the current UAC version from the binary
    
    Args:
        uac_path: Path to UAC binary
        
    Returns:
        Version string or None if not found
    """
    if not uac_path.exists():
        return None
    
    try:
        # Try to get version from UAC binary
        # UAC typically outputs version with --version flag
        import subprocess
        result = subprocess.run(
            [str(uac_path), "--version"],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0 and result.stdout:
            # Extract version from output (format: "uac version X.Y.Z")
            version_line = result.stdout.strip()
            if "version" in version_line:
                parts = version_line.split()
                for i, part in enumerate(parts):
                    if part == "version" and i + 1 < len(parts):
                        return parts[i + 1]
        
        # If version command doesn't work, check for version file
        version_file = uac_path.parent / "version.txt"
        if version_file.exists():
            return version_file.read_text().strip()
            
    except Exception as e:
        print(f"Warning: Could not determine current version: {e}")
    
    return None


def download_uac(url: str, dest_path: Path) -> bool:
    """
    Download UAC tar.gz and extract the binary
    
    Args:
        url: Download URL for tar.gz
        dest_path: Destination path for the binary
        
    Returns:
        True if successful, False otherwise
    """
    import tarfile
    import tempfile
    
    try:
        print(f"Downloading UAC from {url}...")
        
        response = requests.get(url, stream=True, timeout=60)
        response.raise_for_status()
        
        # Create temporary file for tar.gz
        with tempfile.NamedTemporaryFile(suffix='.tar.gz', delete=False) as temp_file:
            temp_tar_path = Path(temp_file.name)
            
            # Download with progress
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    temp_file.write(chunk)
                    downloaded += len(chunk)
                    
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\rProgress: {percent:.1f}% ({downloaded}/{total_size} bytes)", end='')
        
        print()  # New line after progress
        
        # Extract UAC binary from tar.gz
        print("Extracting UAC binary...")
        with tempfile.TemporaryDirectory() as extract_dir:
            with tarfile.open(temp_tar_path, 'r:gz') as tar:
                tar.extractall(extract_dir)
            
            # Find the UAC binary
            extract_path = Path(extract_dir)
            uac_binary = None
            
            # Look for uac binary in extracted files
            for root, dirs, files in os.walk(extract_path):
                if 'uac' in files:
                    uac_path = Path(root) / 'uac'
                    # Verify it's the main UAC script/binary
                    if uac_path.stat().st_size > 1000:  # Basic size check
                        uac_binary = uac_path
                        break
            
            if not uac_binary:
                raise FileNotFoundError("UAC binary not found in archive")
            
            # Copy to destination
            shutil.copy2(uac_binary, dest_path)
            dest_path.chmod(0o755)
        
        # Clean up temp file
        temp_tar_path.unlink()
        
        print(f"Successfully extracted UAC to {dest_path}")
        return True
        
    except Exception as e:
        print(f"Error downloading/extracting UAC: {e}")
        # Clean up temp files
        if 'temp_tar_path' in locals() and temp_tar_path.exists():
            temp_tar_path.unlink()
        return False


def calculate_checksum(file_path: Path) -> str:
    """Calculate SHA256 checksum of a file"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def main():
    parser = argparse.ArgumentParser(
        description="Update UAC (Unix-like Artifacts Collector) to the latest version"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force download even if current version is up to date"
    )
    parser.add_argument(
        "--dest",
        type=str,
        help="Destination path for UAC binary (default: falcon_client/resources/uac/uac)"
    )
    
    args = parser.parse_args()
    
    # Determine destination path
    if args.dest:
        dest_path = Path(args.dest)
    else:
        # Default to resources/uac directory
        script_dir = Path(__file__).parent
        project_root = script_dir.parent
        dest_path = project_root / "falcon_client" / "resources" / "uac" / "uac"
    
    # Ensure destination directory exists
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    
    print("UAC Update Tool")
    print("=" * 50)
    
    # Get latest release info
    print("Checking for latest UAC release...")
    latest_version, download_url = get_latest_release_info()
    print(f"Latest version: {latest_version}")
    
    # Check current version
    current_version = get_current_version(dest_path)
    if current_version:
        print(f"Current version: {current_version}")
    else:
        print("No UAC binary found locally")
    
    # Determine if update is needed
    if not args.force and current_version == latest_version:
        print("\n✓ UAC is already up to date!")
        
        # Calculate and display checksum
        if dest_path.exists():
            checksum = calculate_checksum(dest_path)
            print(f"Checksum (SHA256): {checksum}")
        
        return
    
    # Download new version
    print(f"\nDownloading UAC {latest_version}...")
    
    # Backup current version if it exists
    if dest_path.exists():
        backup_path = dest_path.with_suffix('.backup')
        shutil.copy2(dest_path, backup_path)
        print(f"Backed up current version to {backup_path}")
    
    # Download new version
    if download_uac(download_url, dest_path):
        # Save version info
        version_file = dest_path.parent / "version.txt"
        version_file.write_text(latest_version)
        
        # Calculate and display checksum
        checksum = calculate_checksum(dest_path)
        print(f"\n✓ UAC updated successfully to version {latest_version}")
        print(f"Checksum (SHA256): {checksum}")
        
        # Remove backup
        backup_path = dest_path.with_suffix('.backup')
        if backup_path.exists():
            backup_path.unlink()
    else:
        # Restore backup if download failed
        backup_path = dest_path.with_suffix('.backup')
        if backup_path.exists():
            shutil.move(str(backup_path), str(dest_path))
            print("Restored previous version from backup")
        
        print("\n✗ UAC update failed")
        sys.exit(1)


if __name__ == "__main__":
    main()