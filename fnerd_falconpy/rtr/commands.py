"""
RTR command definitions and parser.
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

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
    platforms: List[str]  # ['windows', 'mac', 'linux']
    requires_admin: bool = False

# Command definitions
RTR_COMMANDS = {
    # Read-only commands
    "cat": RTRCommand(
        name="cat",
        command_type=CommandType.READ_ONLY,
        base_command="cat",
        description="View file contents",
        syntax="cat <file_path>",
        platforms=["windows", "mac", "linux"]
    ),
    "cd": RTRCommand(
        name="cd",
        command_type=CommandType.READ_ONLY,
        base_command="cd",
        description="Change directory",
        syntax="cd <directory_path>",
        platforms=["windows", "mac", "linux"]
    ),
    "ls": RTRCommand(
        name="ls",
        command_type=CommandType.READ_ONLY,
        base_command="ls",
        description="List directory contents",
        syntax="ls [directory_path]",
        platforms=["windows", "mac", "linux"]
    ),
    "pwd": RTRCommand(
        name="pwd",
        command_type=CommandType.READ_ONLY,
        base_command="pwd",
        description="Print working directory",
        syntax="pwd",
        platforms=["windows", "mac", "linux"]
    ),
    "ps": RTRCommand(
        name="ps",
        command_type=CommandType.READ_ONLY,
        base_command="ps",
        description="List running processes",
        syntax="ps",
        platforms=["windows", "mac", "linux"]
    ),
    "env": RTRCommand(
        name="env",
        command_type=CommandType.READ_ONLY,
        base_command="env",
        description="Display environment variables",
        syntax="env",
        platforms=["windows", "mac", "linux"]
    ),
    "filehash": RTRCommand(
        name="filehash",
        command_type=CommandType.READ_ONLY,
        base_command="filehash",
        description="Calculate file hash",
        syntax="filehash <file_path> [md5|sha256]",
        platforms=["windows", "mac", "linux"]
    ),
    "history": RTRCommand(
        name="history",
        command_type=CommandType.READ_ONLY,
        base_command="history",
        description="Review command history",
        syntax="history",
        platforms=["windows", "mac", "linux"]
    ),
    "netstat": RTRCommand(
        name="netstat",
        command_type=CommandType.READ_ONLY,
        base_command="netstat",
        description="Display network connections",
        syntax="netstat [-a]",
        platforms=["windows", "mac", "linux"]
    ),
    "mount": RTRCommand(
        name="mount",
        command_type=CommandType.READ_ONLY,
        base_command="mount",
        description="Display mounted filesystems",
        syntax="mount",
        platforms=["mac", "linux"]
    ),
    "reg": RTRCommand(
        name="reg",
        command_type=CommandType.READ_ONLY,
        base_command="reg",
        description="Registry operations",
        syntax="reg query <key_path>",
        platforms=["windows"]
    ),
    
    # Active responder commands
    "get": RTRCommand(
        name="get",
        command_type=CommandType.ACTIVE_RESPONDER,
        base_command="get",
        description="Get a file from the host",
        syntax="get <file_path>",
        platforms=["windows", "mac", "linux"]
    ),
    "put": RTRCommand(
        name="put",
        command_type=CommandType.ADMIN,
        base_command="put",
        description="Upload a file to the host",
        syntax="put <file_name>",
        platforms=["windows", "mac", "linux"],
        requires_admin=True
    ),
    "run": RTRCommand(
        name="run",
        command_type=CommandType.ADMIN,
        base_command="run",
        description="Run an executable",
        syntax="run <executable> [arguments]",
        platforms=["windows", "mac", "linux"],
        requires_admin=True
    ),
    "runscript": RTRCommand(
        name="runscript",
        command_type=CommandType.ADMIN,
        base_command="runscript",
        description="Run a script from the cloud",
        syntax="runscript -CloudFile=<script_name> [arguments]",
        platforms=["windows", "mac", "linux"],
        requires_admin=True
    ),
    "shutdown": RTRCommand(
        name="shutdown",
        command_type=CommandType.ADMIN,
        base_command="shutdown",
        description="Shutdown the system",
        syntax="shutdown -r (reboot) | -s (shutdown)",
        platforms=["windows", "mac", "linux"],
        requires_admin=True
    ),
    "restart": RTRCommand(
        name="restart",
        command_type=CommandType.ADMIN,
        base_command="restart",
        description="Restart the system",
        syntax="restart",
        platforms=["windows", "mac", "linux"],
        requires_admin=True
    ),
    "containhost": RTRCommand(
        name="containhost",
        command_type=CommandType.ADMIN,
        base_command="containhost",
        description="Network contain the host",
        syntax="containhost",
        platforms=["windows", "mac", "linux"],
        requires_admin=True
    ),
    "map": RTRCommand(
        name="map",
        command_type=CommandType.ADMIN,
        base_command="map",
        description="Map a network drive",
        syntax="map <drive_letter> <network_path>",
        platforms=["windows"],
        requires_admin=True
    ),
    "memdump": RTRCommand(
        name="memdump",
        command_type=CommandType.ADMIN,
        base_command="memdump",
        description="Dump memory to file",
        syntax="memdump",
        platforms=["windows", "mac", "linux"],
        requires_admin=True
    ),
    "mkdir": RTRCommand(
        name="mkdir",
        command_type=CommandType.ADMIN,
        base_command="mkdir",
        description="Create a directory",
        syntax="mkdir <directory_path>",
        platforms=["windows", "mac", "linux"],
        requires_admin=True
    ),
    "mv": RTRCommand(
        name="mv",
        command_type=CommandType.ADMIN,
        base_command="mv",
        description="Move a file",
        syntax="mv <source> <destination>",
        platforms=["windows", "mac", "linux"],
        requires_admin=True
    ),
    "rm": RTRCommand(
        name="rm",
        command_type=CommandType.ADMIN,
        base_command="rm",
        description="Remove a file",
        syntax="rm <file_path>",
        platforms=["windows", "mac", "linux"],
        requires_admin=True
    ),
    "kill": RTRCommand(
        name="kill",
        command_type=CommandType.ADMIN,
        base_command="kill",
        description="Kill a process",
        syntax="kill <pid>",
        platforms=["windows", "mac", "linux"],
        requires_admin=True
    ),
    "update": RTRCommand(
        name="update",
        command_type=CommandType.ADMIN,
        base_command="update",
        description="Update sensor",
        syntax="update install | history | install <version>",
        platforms=["windows", "mac", "linux"],
        requires_admin=True
    ),
    
    # Local helper commands
    "help": RTRCommand(
        name="help",
        command_type=CommandType.LOCAL,
        base_command="help",
        description="Show help information",
        syntax="help [command]",
        platforms=["windows", "mac", "linux"]
    ),
    "exit": RTRCommand(
        name="exit",
        command_type=CommandType.LOCAL,
        base_command="exit",
        description="Exit RTR session",
        syntax="exit",
        platforms=["windows", "mac", "linux"]
    ),
    "clear": RTRCommand(
        name="clear",
        command_type=CommandType.LOCAL,
        base_command="clear",
        description="Clear the screen",
        syntax="clear",
        platforms=["windows", "mac", "linux"]
    ),
    "download": RTRCommand(
        name="download",
        command_type=CommandType.LOCAL,
        base_command="download",
        description="Download a file that was retrieved with 'get'",
        syntax="download <sha256>",
        platforms=["windows", "mac", "linux"]
    ),
    "files": RTRCommand(
        name="files",
        command_type=CommandType.LOCAL,
        base_command="files",
        description="List files in current RTR session",
        syntax="files",
        platforms=["windows", "mac", "linux"]
    ),
    "upload": RTRCommand(
        name="upload",
        command_type=CommandType.LOCAL,
        base_command="upload",
        description="Upload a local file to CrowdStrike cloud storage for use with 'put'",
        syntax="upload <local_file_path>",
        platforms=["windows", "mac", "linux"]
    ),
}

class RTRCommandParser:
    """Parse and validate RTR commands"""
    
    def __init__(self, platform: str):
        """
        Initialize command parser
        
        Args:
            platform: Current host platform ('windows', 'mac', 'linux')
        """
        self.platform = platform.lower()
        self.current_directory = ""
        
    def parse_command(self, command_line: str) -> Tuple[Optional[RTRCommand], str]:
        """
        Parse a command line into command and arguments
        
        Args:
            command_line: Raw command line input
            
        Returns:
            Tuple of (RTRCommand or None, command_string)
        """
        if not command_line.strip():
            return None, ""
            
        parts = command_line.strip().split(maxsplit=1)
        command_name = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""
        
        # Handle special case for 'dir' on Windows
        if command_name == "dir" and self.platform == "windows":
            command_name = "ls"
            
        # Look up command
        command = RTR_COMMANDS.get(command_name)
        
        if not command:
            return None, command_line
            
        # Check platform compatibility
        if self.platform not in command.platforms:
            return None, command_line
            
        # For local commands, return as-is
        if command.command_type == CommandType.LOCAL:
            return command, command_line
            
        # For RTR commands, format the full command string
        if args:
            full_command = f"{command_name} {args}"
        else:
            full_command = command_name
            
        return command, full_command
        
    def get_available_commands(self, include_admin: bool = False) -> List[RTRCommand]:
        """
        Get list of available commands for current platform
        
        Args:
            include_admin: Include admin commands
            
        Returns:
            List of available RTRCommand objects
        """
        available = []
        
        for cmd in RTR_COMMANDS.values():
            # Check platform
            if self.platform not in cmd.platforms:
                continue
                
            # Check admin requirement
            if cmd.requires_admin and not include_admin:
                continue
                
            available.append(cmd)
            
        return sorted(available, key=lambda x: x.name)
        
    def format_help(self, command_name: Optional[str] = None) -> str:
        """
        Format help text
        
        Args:
            command_name: Specific command to get help for
            
        Returns:
            Formatted help text
        """
        if command_name:
            # Specific command help
            cmd = RTR_COMMANDS.get(command_name.lower())
            if not cmd:
                return f"Unknown command: {command_name}"
                
            help_text = f"\n{cmd.name} - {cmd.description}\n"
            help_text += f"Syntax: {cmd.syntax}\n"
            help_text += f"Type: {cmd.command_type.value}\n"
            help_text += f"Platforms: {', '.join(cmd.platforms)}\n"
            if cmd.requires_admin:
                help_text += "Requires: Admin privileges\n"
                
            return help_text
        else:
            # General help
            help_text = "\nAvailable RTR Commands:\n\n"
            
            # Group by type
            groups = {
                CommandType.READ_ONLY: "Read-Only Commands:",
                CommandType.ACTIVE_RESPONDER: "Active Responder Commands:",
                CommandType.ADMIN: "Admin Commands:",
                CommandType.LOCAL: "Local Commands:"
            }
            
            for cmd_type, header in groups.items():
                commands = [cmd for cmd in self.get_available_commands(include_admin=True) 
                           if cmd.command_type == cmd_type]
                
                if commands:
                    help_text += f"{header}\n"
                    for cmd in commands:
                        help_text += f"  {cmd.name:<15} - {cmd.description}\n"
                    help_text += "\n"
                    
            help_text += "Type 'help <command>' for detailed command help.\n"
            
            return help_text