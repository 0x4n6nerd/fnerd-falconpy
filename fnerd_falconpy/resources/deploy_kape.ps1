# Define the path to the zip file and the destination folder for extraction
# Note: These paths match the workspace.windows configuration in config.yaml
# Default is C:\0x4n6nerd but can be changed via configuration
$zipPath = "C:\0x4n6nerd\kape.zip"
$destination = "C:\0x4n6nerd"
$file = "C:\0x4n6nerd\"

# Create the destination directory if it does not exist
if (!(Test-Path -Path $destination)) {
    New-Item -ItemType Directory -Path $destination | Out-Null
}

# Unzip the file into the destination folder
try {
    Expand-Archive -Path $zipPath -DestinationPath $destination -Force
    Write-Output "Successfully unzipped '$zipPath' to '$destination'."
}
catch {
    Write-Error "Failed to unzip '$zipPath'. Error details: $_"
    exit 1
}

# Define the path to the binary to execute (assumed to be kape.exe)
$binaryPath = Join-Path $file "kape.exe"
$cliPath = Join-Path $file "_kape.cli"

# Check if the binary and CLI file exist
if (Test-Path -Path $binaryPath) {
    if (Test-Path -Path $cliPath) {
        Write-Output "Executing KAPE with CLI file: $cliPath"
        try {
            # Change to KAPE directory and execute with CLI file (background execution)
            Set-Location $file
            Start-Process -FilePath $binaryPath -ArgumentList "--cli", $cliPath -NoNewWindow
            Write-Output "KAPE execution started in background"
        }
        catch {
            Write-Error "Failed to execute KAPE with CLI file. Error details: $_"
        }
    }
    else {
        Write-Error "CLI file '$cliPath' not found."
    }
}
else {
    Write-Error "Binary '$binaryPath' not found in '$destination'."
}

