# RTR Interactive Session Module

## Overview

The RTR (Real Time Response) Interactive Session module provides a command-line interface for interacting with CrowdStrike Falcon RTR sessions. This allows security analysts and incident responders to execute commands on remote endpoints in real-time, similar to using RTR through the Falcon console.

## Features

- **Interactive Terminal**: Full terminal-like experience with command history and tab completion
- **Cross-Platform Support**: Works with Windows, macOS, and Linux endpoints
- **Command Categories**:
  - Read-only commands (ls, cat, pwd, ps, etc.)
  - Active responder commands (get, zip)
  - Admin commands (put, run, runscript, cp, mv, rm, mkdir)
  - Local helper commands (help, files, download, clear)
- **File Management**: Download files retrieved with 'get' command
- **Session Management**: Automatic session keepalive and cleanup
- **Command History**: Persistent command history across sessions

## Usage

### Starting an RTR Session

```bash
falcon-client rtr -d HOSTNAME
```

Or with explicit credentials:
```bash
falcon-client --client-id YOUR_ID --client-secret YOUR_SECRET rtr -d HOSTNAME
```

### Available Commands

Once in an RTR session, you can use the following commands:

#### Read-Only Commands
- `ls [path]` - List directory contents
- `cat <file>` - View file contents
- `cd <directory>` - Change directory
- `pwd` - Print working directory
- `ps` - List running processes
- `env` - Display environment variables
- `filehash <file> [md5|sha256]` - Calculate file hash
- `history` - View command history
- `netstat [-a]` - Display network connections
- `ipconfig` (Windows) / `ifconfig` (Mac/Linux) - Network configuration

#### Active Responder Commands
- `get <file>` - Retrieve a file from the host
- `zip <archive> <file/directory>` - Create a zip archive

#### Admin Commands (require elevated privileges)
- `put <filename>` - Upload a file to the host
- `run <executable> [args]` - Run an executable
- `runscript -CloudFile=<script> [args]` - Run a script from the cloud
- `cp <source> <dest>` - Copy a file
- `mv <source> <dest>` - Move a file
- `rm <file>` - Remove a file
- `mkdir <directory>` - Create a directory

#### Local Helper Commands
- `help [command]` - Show available commands or help for specific command
- `files` - List files in current RTR session
- `download <sha256>` - Download a file retrieved with 'get'
- `clear` - Clear the screen
- `exit` / `quit` - Exit the RTR session

### Example Session

```
$ falcon-client rtr -d DESKTOP-ABC123

======================================================================
CrowdStrike Falcon RTR Interactive Session
======================================================================
Started at: 2024-01-15 10:30:00
======================================================================

Connecting to DESKTOP-ABC123...
✓ Connected to DESKTOP-ABC123
  Platform: windows
  OS: Windows 10.0.19044
  AID: 1234567890abcdef...

Initializing RTR session...
✓ RTR session established (ID: 12345678...)

Type 'help' for available commands or 'exit' to quit

RTR [DESKTOP-ABC123:~]> pwd
Executing: pwd
C:\

RTR [DESKTOP-ABC123:~]> ls
Executing: ls
Name                          Size  Type        Last Modified
----                          ----  ----        -------------
PerfLogs                      0     <Directory> 12/07/2019 09:14:01
Program Files                 0     <Directory> 01/10/2024 15:22:33
Program Files (x86)           0     <Directory> 01/10/2024 15:22:33
Users                         0     <Directory> 12/15/2023 08:45:12
Windows                       0     <Directory> 01/10/2024 18:30:45

RTR [DESKTOP-ABC123:~]> get C:\Users\john\Documents\report.pdf
Executing: get C:\Users\john\Documents\report.pdf
Waiting for command to complete...

✓ File retrieved successfully
  Filename: report.pdf
  SHA256: a1b2c3d4e5f6...

Use 'download a1b2c3d4e5f6...' to save the file locally

RTR [DESKTOP-ABC123:~]> download a1b2c3d4e5f6
Downloading report.pdf...
✓ File saved to: /home/analyst/rtr_downloads/report.pdf

RTR [DESKTOP-ABC123:~]> exit

Exiting RTR session...

Closing RTR session...
✓ Session closed

Goodbye!
```

## Architecture

### Module Structure

```
falcon_client/rtr/
├── __init__.py              # Module exports
├── commands.py              # Command definitions and parser
├── interactive.py           # Interactive session handler
└── README.md               # This file
```

### Key Components

1. **RTRInteractiveSession**: Main class that manages the interactive session
   - Handles user input and command execution
   - Manages session state and lifecycle
   - Provides file download capabilities

2. **RTRCommandParser**: Parses and validates commands
   - Platform-specific command validation
   - Command syntax formatting for RTR API
   - Help text generation

3. **RTRCommand**: Data class for command definitions
   - Command metadata (name, type, syntax, platforms)
   - Permission requirements

### Design Decisions

1. **Platform Detection**: Commands are validated against the target platform to prevent execution errors

2. **Command Types**: Commands are categorized by permission level:
   - Read-only: Safe commands that don't modify the system
   - Active Responder: Commands that can retrieve data
   - Admin: Commands that can modify the system

3. **Local Commands**: Helper commands that run locally, not on the remote host

4. **File Tracking**: Retrieved files are tracked by SHA256 for easy download

5. **Session Management**: Automatic session initialization and cleanup

## Error Handling

The module handles various error conditions:
- Invalid commands or syntax
- Platform-incompatible commands
- Network/API failures
- Session timeouts
- File operation errors

Errors are logged and displayed to the user with helpful messages.

## Security Considerations

1. **Authentication**: Uses the same authentication as other falcon-client commands
2. **Authorization**: Respects RTR permissions set in Falcon console
3. **Logging**: All commands are logged for audit purposes
4. **File Validation**: Downloaded files maintain SHA256 integrity

## Extending the Module

### Adding New Commands

1. Add command definition to `RTR_COMMANDS` in `commands.py`:
```python
"newcmd": RTRCommand(
    name="newcmd",
    command_type=CommandType.READ_ONLY,
    base_command="newcmd",
    description="Description of command",
    syntax="newcmd [args]",
    platforms=["windows", "mac", "linux"]
)
```

2. Add any special handling in `interactive.py` if needed

### Adding Platform-Specific Commands

Commands can be restricted to specific platforms:
```python
platforms=["windows"]  # Windows only
platforms=["mac", "linux"]  # Unix-like systems
```

## Troubleshooting

### Common Issues

1. **"Command not available on platform"**: The command isn't supported on the target OS
2. **"Failed to initialize RTR session"**: Check host connectivity and RTR permissions
3. **"Command timed out"**: The command took too long to execute (>60s)
4. **"File not found in session"**: The file wasn't retrieved with 'get' first

### Debug Mode

Enable debug logging for troubleshooting:
```bash
falcon-client --log-level DEBUG rtr -d HOSTNAME
```

## Future Enhancements

Potential improvements for future versions:
1. Script execution from local files
2. Batch command execution
3. Session recording and playback
4. Enhanced tab completion for file paths
5. Progress bars for long-running commands
6. Multiple concurrent sessions
7. Session sharing/handoff

## Learning Resources

For developers new to RTR:
1. Review the CrowdStrike RTR documentation
2. Start with read-only commands to understand the flow
3. Practice in a test environment before production use
4. Study the command execution flow in `interactive.py`