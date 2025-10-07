#!/bin/bash
#
# setup_dependencies.sh
# Helper script to set up KAPE and UAC dependencies for 4n6NerdStriker
#
# This script provides guidance and verification for obtaining and configuring
# third-party forensic tools required by 4n6NerdStriker.
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Determine package directory name
if [ -d "fnerd_falconpy" ]; then
    PACKAGE_DIR="fnerd_falconpy"
else
    echo -e "${RED}Error: Cannot find package directory (fnerd_falconpy)${NC}"
    exit 1
fi

RESOURCES_DIR="${PACKAGE_DIR}/resources"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}fnerd-falconpy Dependency Setup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "This script will help you set up the required third-party tools:"
echo "  1. KAPE (Windows forensic artifact collector)"
echo "  2. UAC (Unix/Linux/macOS forensic artifact collector)"
echo ""
echo -e "${YELLOW}Note: These tools are NOT included in the repository.${NC}"
echo "You must obtain them from their official sources."
echo ""

# Create resources directory if it doesn't exist
mkdir -p "$RESOURCES_DIR"

#
# KAPE Setup
#
echo -e "${BLUE}----------------------------------------${NC}"
echo -e "${BLUE}1. KAPE (Kroll Artifact Parser and Extractor)${NC}"
echo -e "${BLUE}----------------------------------------${NC}"
echo ""
echo "KAPE is created by Eric Zimmerman"
echo "Repository: https://github.com/EricZimmerman/KapeFiles"
echo "Download: https://www.kroll.com/kape"
echo ""

if [ -f "$RESOURCES_DIR/kape.zip" ]; then
    echo -e "${GREEN}✓ kape.zip found${NC}"
    KAPE_SIZE=$(du -sh "$RESOURCES_DIR/kape.zip" | cut -f1)
    echo "  Size: $KAPE_SIZE"
else
    echo -e "${RED}✗ kape.zip not found${NC}"
    echo ""
    echo "To set up KAPE:"
    echo "  1. Download KAPE from: https://www.kroll.com/kape"
    echo "  2. Clone KapeFiles: git clone https://github.com/EricZimmerman/KapeFiles.git"
    echo "  3. Create directory: mkdir -p $RESOURCES_DIR/kape"
    echo "  4. Copy KAPE binary: cp /path/to/kape.exe $RESOURCES_DIR/kape/"
    echo "  5. Copy KapeFiles: cp -r /path/to/KapeFiles/Targets $RESOURCES_DIR/kape/"
    echo "                      cp -r /path/to/KapeFiles/Modules $RESOURCES_DIR/kape/"
    echo "  6. Create archive: cd $RESOURCES_DIR && zip -r kape.zip kape/"
    echo ""
    echo "See DEPENDENCIES.md for detailed instructions."
    echo ""
fi

if [ -d "$RESOURCES_DIR/kape" ]; then
    echo -e "${GREEN}✓ kape/ directory found${NC}"

    if [ -f "$RESOURCES_DIR/kape/kape.exe" ]; then
        echo -e "${GREEN}  ✓ kape.exe found${NC}"
    else
        echo -e "${YELLOW}  ⚠ kape.exe not found${NC}"
    fi

    if [ -d "$RESOURCES_DIR/kape/Targets" ]; then
        TARGET_COUNT=$(find "$RESOURCES_DIR/kape/Targets" -name "*.tkape" | wc -l)
        echo -e "${GREEN}  ✓ Targets directory found ($TARGET_COUNT targets)${NC}"
    else
        echo -e "${YELLOW}  ⚠ Targets directory not found${NC}"
    fi

    if [ -d "$RESOURCES_DIR/kape/Modules" ]; then
        MODULE_COUNT=$(find "$RESOURCES_DIR/kape/Modules" -name "*.mkape" | wc -l)
        echo -e "${GREEN}  ✓ Modules directory found ($MODULE_COUNT modules)${NC}"
    else
        echo -e "${YELLOW}  ⚠ Modules directory not found${NC}"
    fi
else
    echo -e "${YELLOW}⚠ kape/ directory not found${NC}"
fi

# Check custom KAPE targets
echo ""
if [ -d "$RESOURCES_DIR/kape/Targets/Custom" ]; then
    CUSTOM_COUNT=$(find "$RESOURCES_DIR/kape/Targets/Custom" -name "*.tkape" | wc -l)
    echo -e "${GREEN}✓ Custom KAPE targets: $CUSTOM_COUNT files${NC}"
    find "$RESOURCES_DIR/kape/Targets/Custom" -name "*.tkape" -exec basename {} \; | while read -r file; do
        echo "  - $file"
    done
fi

echo ""

#
# UAC Setup
#
echo -e "${BLUE}----------------------------------------${NC}"
echo -e "${BLUE}2. UAC (Unix-like Artifacts Collector)${NC}"
echo -e "${BLUE}----------------------------------------${NC}"
echo ""
echo "UAC is created by Tclahr (Thiago Canozzo Lahr)"
echo "Repository: https://github.com/tclahr/uac"
echo "License: Apache 2.0"
echo ""

if [ -f "$RESOURCES_DIR/uac.zip" ]; then
    echo -e "${GREEN}✓ uac.zip found${NC}"
    UAC_SIZE=$(du -sh "$RESOURCES_DIR/uac.zip" | cut -f1)
    echo "  Size: $UAC_SIZE"
else
    echo -e "${RED}✗ uac.zip not found${NC}"
    echo ""
    echo "To set up UAC:"
    echo "  1. Clone repository: git clone https://github.com/tclahr/uac.git"
    echo "     OR download release: https://github.com/tclahr/uac/releases"
    echo "  2. Create directory: mkdir -p $RESOURCES_DIR/uac"
    echo "  3. Copy UAC files: cp -r /path/to/uac/* $RESOURCES_DIR/uac/"
    echo "  4. Create archive: cd $RESOURCES_DIR/uac && zip -r ../uac.zip ."
    echo ""
    echo "See DEPENDENCIES.md for detailed instructions."
    echo ""
fi

if [ -d "$RESOURCES_DIR/uac" ]; then
    echo -e "${GREEN}✓ uac/ directory found${NC}"

    if [ -f "$RESOURCES_DIR/uac/uac" ]; then
        echo -e "${GREEN}  ✓ uac binary found${NC}"
    elif [ -f "$RESOURCES_DIR/uac/uac.sh" ]; then
        echo -e "${GREEN}  ✓ uac.sh script found${NC}"
    else
        echo -e "${YELLOW}  ⚠ uac binary/script not found${NC}"
    fi

    if [ -d "$RESOURCES_DIR/uac/profiles" ]; then
        PROFILE_COUNT=$(find "$RESOURCES_DIR/uac/profiles" -name "*.yaml" -o -name "*.yml" | wc -l)
        echo -e "${GREEN}  ✓ Profiles directory found ($PROFILE_COUNT profiles)${NC}"
    else
        echo -e "${YELLOW}  ⚠ Profiles directory not found${NC}"
    fi
else
    echo -e "${YELLOW}⚠ uac/ directory not found${NC}"
fi

echo ""

#
# Deployment Scripts
#
echo -e "${BLUE}----------------------------------------${NC}"
echo -e "${BLUE}3. Deployment Scripts${NC}"
echo -e "${BLUE}----------------------------------------${NC}"
echo ""

if [ -f "$RESOURCES_DIR/deploy_kape.ps1" ]; then
    echo -e "${GREEN}✓ deploy_kape.ps1 found${NC}"
else
    echo -e "${YELLOW}⚠ deploy_kape.ps1 not found${NC}"
fi

if [ -f "$RESOURCES_DIR/deploy_uac.sh" ]; then
    echo -e "${GREEN}✓ deploy_uac.sh found${NC}"
else
    echo -e "${YELLOW}⚠ deploy_uac.sh not found${NC}"
fi

echo ""

#
# Summary
#
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

KAPE_READY=false
UAC_READY=false

if [ -f "$RESOURCES_DIR/kape.zip" ] && [ -d "$RESOURCES_DIR/kape" ]; then
    KAPE_READY=true
fi

if [ -f "$RESOURCES_DIR/uac.zip" ] && [ -d "$RESOURCES_DIR/uac" ]; then
    UAC_READY=true
fi

if $KAPE_READY && $UAC_READY; then
    echo -e "${GREEN}✓ All dependencies are configured!${NC}"
    echo ""
    echo "You can now use fnerd-falconpy:"
    echo "  - KAPE collections (Windows): fnerd-falconpy kape -n 1 -d HOSTNAME -t TARGET"
    echo "  - UAC collections (Unix/Linux/macOS): fnerd-falconpy uac -n 1 -d HOSTNAME -p PROFILE"
    echo ""
    echo "Run test: python test/test_installation.py"
elif $KAPE_READY; then
    echo -e "${GREEN}✓ KAPE is configured${NC}"
    echo -e "${YELLOW}⚠ UAC is not configured${NC}"
    echo ""
    echo "You can use KAPE collections, but UAC is not available."
    echo "See DEPENDENCIES.md for UAC setup instructions."
elif $UAC_READY; then
    echo -e "${YELLOW}⚠ KAPE is not configured${NC}"
    echo -e "${GREEN}✓ UAC is configured${NC}"
    echo ""
    echo "You can use UAC collections, but KAPE is not available."
    echo "See DEPENDENCIES.md for KAPE setup instructions."
else
    echo -e "${YELLOW}⚠ Dependencies are not fully configured${NC}"
    echo ""
    echo "Please follow the instructions in DEPENDENCIES.md to set up:"
    if ! $KAPE_READY; then
        echo "  - KAPE (Windows forensic collections)"
    fi
    if ! $UAC_READY; then
        echo "  - UAC (Unix/Linux/macOS forensic collections)"
    fi
fi

echo ""
echo "For detailed setup instructions, see: DEPENDENCIES.md"
echo "For credits and attribution, see: CREDITS.md"
echo ""

exit 0
