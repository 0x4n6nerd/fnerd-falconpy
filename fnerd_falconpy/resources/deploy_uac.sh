#!/bin/bash
# UAC Deployment Script for Unix/Linux/macOS
# Follows same pattern as KAPE deployment

# Define paths
# Note: These paths match the workspace.unix configuration in config.yaml
# Default is /opt/0x4n6nerd but can be changed via configuration
UAC_ZIP="/opt/0x4n6nerd/uac.zip"
UAC_DIR="/opt/0x4n6nerd"
EVIDENCE_DIR="/opt/0x4n6nerd/evidence"
LOG_FILE="/opt/0x4n6nerd/uac_deploy.log"

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Create directories if they don't exist
log "Creating UAC directories..."
mkdir -p "$UAC_DIR"
mkdir -p "$EVIDENCE_DIR"

# Check if UAC zip exists
if [ ! -f "$UAC_ZIP" ]; then
    log "ERROR: UAC zip not found at $UAC_ZIP"
    exit 1
fi

# Extract UAC
log "Extracting UAC package..."
cd "$UAC_DIR"
if command -v unzip >/dev/null 2>&1; then
    unzip -o "$UAC_ZIP" >> "$LOG_FILE" 2>&1
else
    # Fallback to tar if it's a tar.gz file
    tar -xzf "$UAC_ZIP" >> "$LOG_FILE" 2>&1
fi

if [ $? -ne 0 ]; then
    log "ERROR: Failed to extract UAC package"
    exit 1
fi

# Find UAC binary
UAC_BIN=""
if [ -f "uac" ]; then
    UAC_BIN="./uac"
elif [ -d "uac-"* ]; then
    UAC_DIR_NAME=$(ls -d uac-* | head -1)
    UAC_BIN="./$UAC_DIR_NAME/uac"
fi

if [ -z "$UAC_BIN" ]; then
    log "ERROR: Could not find UAC binary"
    exit 1
fi

# Make UAC executable
chmod +x "$UAC_BIN"
log "Found UAC binary at: $UAC_BIN"

# Get profile from argument or use default
PROFILE="${1:-ir_triage}"
log "Using UAC profile: $PROFILE"

# Execute UAC in background WITHOUT nohup (which fails in RTR due to TTY limitations)
# Use shell backgrounding with proper I/O redirection instead
# UAC must be executed from within its own directory to find required files
log "Starting UAC collection..."
UAC_DIR_NAME=$(dirname "$UAC_BIN")
(cd "$UAC_DIR_NAME" && ./uac -p "$PROFILE" --output-format tar "$EVIDENCE_DIR" < /dev/null > "$UAC_DIR/uac_output.log" 2>&1; echo $? > "$UAC_DIR/uac_exit_code") &
UAC_PID=$!

log "UAC started with PID: $UAC_PID"
log "UAC is running in background. Check $UAC_DIR/uac_output.log for progress."
log "Exit code will be written to $UAC_DIR/uac_exit_code when complete."

# Create a status file for monitoring
echo "$UAC_PID" > "$UAC_DIR/uac.pid"

# Exit immediately so RTR doesn't timeout
exit 0