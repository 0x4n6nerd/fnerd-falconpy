# RTR Interactive Session Development Guide

## Introduction

This guide documents the development process of adding an interactive RTR (Real Time Response) session feature to the 4n6NerdStriker package. It serves as both a reference for the implementation and a learning resource for understanding how to add major features to a modular Python package.

## Feature Requirements

The goal was to add a command-line interface that allows users to:
1. Start an interactive RTR session with a remote host
2. Execute RTR commands as if using the CrowdStrike console
3. Handle file operations (get/download)
4. Provide a user-friendly terminal experience

Command: `4n6nerdstriker rtr -d HOSTNAME`

## Design Process

### 1. Understanding the Existing Architecture

Before adding the feature, I analyzed the existing codebase structure:

```
forensics_nerdstriker/
├── core/           # Base classes and interfaces
├── api/            # API client wrappers
├── managers/       # Business logic managers
├── collectors/     # Specialized collectors
├── cli/            # Command-line interface
└── utils/          # Utility functions
```

Key insights:
- The package follows a modular design with clear separation of concerns
- API operations are wrapped in client classes
- Managers handle business logic and coordination
- The orchestrator ties everything together

### 2. Researching RTR Capabilities

I researched the FalconPy SDK documentation to understand:
- Available RTR API endpoints
- Command execution flow
- Session management requirements
- Command types and permissions

Key findings:
- RTR has three command types: read-only, active responder, and admin
- Commands are executed asynchronously and require status polling
- Sessions need to be kept alive with pulse commands
- File operations have special handling

### 3. Designing the Module Structure

I decided to create a new `rtr` module with three main components:

```
forensics_nerdstriker/rtr/
├── __init__.py         # Module exports
├── commands.py         # Command definitions and parser
└── interactive.py      # Interactive session handler
```

This follows the existing pattern of creating focused modules for specific functionality.

## Implementation Details

### Step 1: Command Definitions (`commands.py`)

First, I created a system for defining and managing RTR commands:

```python
class CommandType(Enum):
    """Types of RTR commands"""
    READ_ONLY = "read_only"
    ACTIVE_RESPONDER = "active_responder"
    ADMIN = "admin"
    LOCAL = "local"  # Local helper commands

@dataclass
class RTRCommand:
    """RTR command definition"""
    name: str
    command_type: CommandType
    base_command: str
    description: str
    syntax: str
    platforms: List[str]
    requires_admin: bool = False
```

**Design Decision**: Using dataclasses for command definitions makes them self-documenting and easy to extend.

The `RTRCommandParser` class handles:
- Command validation
- Platform compatibility checking
- Command string formatting
- Help text generation

**Key Learning**: Separating command definitions from execution logic makes the code more maintainable and testable.

### Step 2: Interactive Session (`interactive.py`)

The `RTRInteractiveSession` class manages the interactive terminal experience:

```python
class RTRInteractiveSession:
    def __init__(self, orchestrator: FalconForensicOrchestrator, 
                 logger: Optional[ILogger] = None):
        self.orchestrator = orchestrator
        self.logger = logger or DefaultLogger("RTRInteractiveSession")
        # ... initialization
```

**Design Decision**: Accepting the orchestrator as a dependency allows us to reuse all existing functionality without duplicating code.

Key features implemented:

1. **Command Line Interface**:
   - Uses Python's `readline` module for history and tab completion
   - Custom prompt showing hostname and directory
   - Command history saved to `~/.falcon_rtr_history`

2. **Command Execution Flow**:
   ```python
   def _execute_rtr_command(self, command: RTRCommand, command_string: str):
       # 1. Determine API method based on command type
       # 2. Execute command via appropriate API
       # 3. Poll for completion if needed
       # 4. Display results
   ```

3. **File Management**:
   - Tracks files retrieved with 'get' command
   - Provides local 'download' command to save files
   - Creates `rtr_downloads/` directory for saved files

4. **Error Handling**:
   - Graceful handling of network errors
   - User-friendly error messages
   - Proper cleanup on exit

### Step 3: CLI Integration

Modified `cli/main.py` to add the new subcommand:

```python
# Add subparser
rtr_parser = subparsers.add_parser('rtr', help='Start interactive RTR session')
rtr_parser.add_argument('-d', '--device', required=True, help='Target device name')

# Handle command
elif args.command == 'rtr':
    from forensics_nerdstriker.rtr import RTRInteractiveSession
    rtr_session = RTRInteractiveSession(orchestrator)
    success = rtr_session.start(args.device)
    results = {args.device: success}
```

**Key Learning**: The existing CLI structure made it easy to add new commands without disrupting existing functionality.

### Step 4: Package Integration

Updated `__init__.py` to export the new module:

```python
from forensics_nerdstriker.rtr import (
    RTRInteractiveSession,
    RTRCommandParser,
    RTRCommand
)
```

This maintains the package's clean API surface.

## Technical Challenges and Solutions

### Challenge 1: Asynchronous Command Execution

RTR commands execute asynchronously, requiring status polling.

**Solution**: Implemented a polling mechanism with visual feedback:
```python
def _wait_for_command_completion(self, cloud_request_id: str, ...):
    print("Waiting for command to complete", end="", flush=True)
    for attempt in range(max_attempts):
        # Check status
        if complete:
            return status
        print(".", end="", flush=True)
        time.sleep(interval)
```

### Challenge 2: Platform-Specific Commands

Different operating systems support different commands.

**Solution**: Platform validation in the command parser:
```python
if self.platform not in command.platforms:
    return None, f"Command '{command_name}' is not available on {self.platform}"
```

### Challenge 3: File Download Workflow

The 'get' command retrieves files to the cloud, not locally.

**Solution**: Two-step process:
1. `get <file>` - Retrieves file to RTR session
2. `download <sha256>` - Downloads file locally

This maintains security while providing usability.

## Code Organization Principles

### 1. Single Responsibility

Each class has one clear purpose:
- `RTRCommand`: Defines a command
- `RTRCommandParser`: Parses and validates commands
- `RTRInteractiveSession`: Manages the interactive session

### 2. Dependency Injection

The session accepts dependencies rather than creating them:
```python
def __init__(self, orchestrator: FalconForensicOrchestrator, 
             logger: Optional[ILogger] = None):
```

This makes the code testable and flexible.

### 3. Interface Segregation

Local commands vs. RTR commands are handled differently:
```python
if command.command_type == CommandType.LOCAL:
    self._handle_local_command(command, command_string)
else:
    self._execute_rtr_command(command, command_string)
```

### 4. Error Handling Strategy

Consistent error handling throughout:
```python
try:
    # Operation
except SpecificException as e:
    self.logger.error(f"Specific error: {e}")
    # User-friendly message
except Exception as e:
    self.logger.error(f"Unexpected error: {e}", exc_info=True)
    # Generic user message
```

## Testing Considerations

While not implemented in this example, here's how you would test this feature:

### Unit Tests

1. **Command Parser Tests**:
   ```python
   def test_parse_valid_command():
       parser = RTRCommandParser("windows")
       cmd, cmd_str = parser.parse_command("ls C:\\")
       assert cmd.name == "ls"
       assert cmd_str == "ls C:\\"
   ```

2. **Command Validation Tests**:
   ```python
   def test_platform_validation():
       parser = RTRCommandParser("linux")
       cmd, error = parser.parse_command("ipconfig")
       assert cmd is None
       assert "not available on linux" in error
   ```

### Integration Tests

1. **Mock RTR API responses**
2. **Test command execution flow**
3. **Verify file tracking**

### Manual Testing Checklist

- [ ] Can connect to Windows/Mac/Linux hosts
- [ ] All read-only commands work
- [ ] File retrieval and download works
- [ ] Error messages are helpful
- [ ] Session cleanup on exit
- [ ] Command history persists

## Best Practices Applied

### 1. User Experience

- Clear feedback for long operations
- Helpful error messages
- Tab completion for commands
- Persistent command history

### 2. Code Documentation

- Comprehensive docstrings
- Type hints throughout
- Clear variable names
- Inline comments for complex logic

### 3. Defensive Programming

- Input validation
- Null checks
- Graceful degradation
- Proper resource cleanup

### 4. Modularity

- Reusable components
- Clear interfaces
- Minimal coupling
- Easy to extend

## Lessons Learned

### 1. Leverage Existing Code

Instead of reimplementing API calls, I used the existing orchestrator and managers. This ensured consistency and reduced code duplication.

### 2. Start with the User Experience

I designed the command-line interface first, then worked backward to the implementation. This ensured the feature was user-friendly.

### 3. Plan for Extensibility

The command definition system makes it trivial to add new commands without modifying core logic.

### 4. Handle Errors Gracefully

Users should never see stack traces. Every error is caught and presented with helpful context.

## Future Enhancements

This design makes it easy to add:

1. **Command Aliases**: Map common commands (e.g., `dir` → `ls`)
2. **Scripting Support**: Execute multiple commands from a file
3. **Output Redirection**: Save command output to files
4. **Session Recording**: Record and replay sessions
5. **Advanced Tab Completion**: Complete file paths and command arguments

## Conclusion

Adding the RTR interactive session feature demonstrated several key principles:

1. **Understand Before Building**: Research the APIs and existing code structure
2. **Design for Integration**: New features should fit naturally into the existing architecture
3. **Focus on User Experience**: Make the tool intuitive and helpful
4. **Write Maintainable Code**: Clear structure, good documentation, and error handling
5. **Plan for Growth**: Design systems that are easy to extend

This feature adds significant value to the 4n6NerdStriker package while maintaining its architectural integrity. The modular design ensures that future developers can understand, maintain, and extend the functionality.

## Code Metrics

- **New Lines of Code**: ~1000
- **New Classes**: 3
- **New Module**: 1
- **Integration Points**: 3 (CLI, orchestrator, package exports)
- **External Dependencies**: 0 (uses only stdlib and existing deps)

The implementation follows all established patterns in the codebase and serves as a good example of how to add major features to a modular Python package.