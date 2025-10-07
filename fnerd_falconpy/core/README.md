# Core Module

The core module contains the fundamental data models, interfaces, and configuration classes used throughout the fnerd-falconpy package.

## Components

### base.py
Contains all the core data models and interfaces:

- **HostInfo**: Data class representing a host/endpoint
  - `aid`: Agent ID (unique identifier)
  - `hostname`: Host name
  - `platform`: Operating system platform (Windows/Mac/Linux)
  - `cid`: Customer ID

- **Platform**: Enum for supported platforms
  - `WINDOWS`
  - `MACOS`
  - `LINUX`

- **RTRSession**: Data class for RTR session information
  - `session_id`: Unique session identifier
  - `host_info`: Associated host information
  - `established_at`: Session creation timestamp

- **CommandResult**: Data class for command execution results
  - `stdout`: Command output
  - `stderr`: Error output
  - `errors`: List of errors
  - `command_request_id`: Request identifier

- **ILogger**: Logger interface (abstract base class)
  - Methods: `debug()`, `info()`, `warning()`, `error()`

- **DefaultLogger**: Default implementation of ILogger using Python's logging module

- **IConfigProvider**: Configuration provider interface

### configuration.py
Configuration management for the package:

- **Configuration**: Main configuration class
  - Loads settings from environment variables
  - Provides defaults for various operations
  - Handles platform-specific configurations

## Usage

```python
from falcon_client.core import HostInfo, Platform, Configuration

# Create a host info object
host = HostInfo(
    aid="12345",
    hostname="DESKTOP-ABC123",
    platform=Platform.WINDOWS,
    cid="customer123"
)

# Load configuration
config = Configuration()
```

## Architecture Notes

The core module follows these design principles:

1. **Data Classes**: All data models use Python dataclasses for immutability and type safety
2. **Interfaces**: Abstract base classes define contracts for logging and configuration
3. **Platform Independence**: The Platform enum allows for OS-specific behavior
4. **Configuration**: Centralized configuration management with environment variable support

## Extension Points

To add new functionality:

1. **New Data Models**: Add new dataclasses to base.py following the existing pattern
2. **Custom Loggers**: Implement the ILogger interface for custom logging backends
3. **Configuration Providers**: Implement IConfigProvider for alternative config sources