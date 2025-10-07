#!/usr/bin/env python3
"""
Build UAC package with custom profiles for deployment.
This script should be run manually to create the UAC package.
The resulting package should be committed to the repository.
"""

import os
import sys
import shutil
import zipfile
import subprocess
from pathlib import Path

def main():
    """Build UAC package with custom profiles."""
    
    # Get paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    resources_dir = project_root / "falcon_client" / "resources" / "uac"
    profiles_source = resources_dir / "profiles"
    
    # Ensure we're in the right directory
    if not profiles_source.exists():
        print(f"Error: Custom profiles directory not found at {profiles_source}")
        return 1
    
    # Create a build directory within the project (not in system temp!)
    build_dir = project_root / "build_uac"
    if build_dir.exists():
        shutil.rmtree(build_dir)
    build_dir.mkdir()
    
    try:
        print("Downloading UAC from GitHub...")
        # Download UAC
        uac_url = "https://github.com/tclahr/uac/archive/refs/heads/main.zip"
        download_path = build_dir / "uac-download.zip"
        
        # Use curl to download
        result = subprocess.run(
            ["curl", "-L", "-o", str(download_path), uac_url],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            print(f"Error downloading UAC: {result.stderr}")
            return 1
        
        print("Extracting UAC...")
        # Extract UAC
        with zipfile.ZipFile(download_path, 'r') as zip_ref:
            zip_ref.extractall(build_dir)
        
        # Find extracted directory
        uac_dir = build_dir / "uac-main"
        if not uac_dir.exists():
            print("Error: UAC directory not found after extraction")
            return 1
        
        print("Adding custom profiles...")
        # Copy custom profiles
        target_profiles = uac_dir / "profiles"
        for profile in profiles_source.glob("*.yaml"):
            print(f"  Adding: {profile.name}")
            shutil.copy2(profile, target_profiles)
        
        # Create final package
        output_path = resources_dir / "uac.zip"
        print(f"Creating package at {output_path}...")
        
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in uac_dir.rglob('*'):
                if file_path.is_file() and file_path.name != '.DS_Store':
                    arcname = file_path.relative_to(build_dir)
                    zipf.write(file_path, arcname)
        
        print(f"✓ UAC package created successfully at: {output_path}")
        print(f"  Size: {output_path.stat().st_size / 1024 / 1024:.1f} MB")
        
        # List profiles in package
        with zipfile.ZipFile(output_path, 'r') as zipf:
            profiles = [n for n in zipf.namelist() if 'profiles/' in n and n.endswith('.yaml')]
            print(f"  Profiles included: {len(profiles)}")
            for p in sorted(profiles):
                print(f"    - {Path(p).name}")
        
    finally:
        # Cleanup build directory
        if build_dir.exists():
            shutil.rmtree(build_dir)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())