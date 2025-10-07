"""
Platform-specific handlers for OS-dependent operations.
"""

import re
from abc import ABC, abstractmethod
from typing import Optional, Tuple
from fnerd_falconpy.core.base import Platform

class PlatformHandler(ABC):
    """Abstract base class for platform-specific operations"""
    
    @abstractmethod
    def get_file_size_command(self, file_path: str) -> Tuple[str, str]:
        """
        Get platform-specific file size command
        
        Args:
            file_path: Path to the file
            
        Returns:
            Tuple of (base_command, command_string)
        """
        pass
        
    @abstractmethod
    def parse_file_size_output(self, output: str, file_path: str) -> Optional[int]:
        """
        Parse platform-specific file size output
        
        Args:
            output: Command output
            file_path: Original file path (for error messages)
            
        Returns:
            File size in bytes or None if not found
        """
        pass
        
    @abstractmethod
    def get_browser_history_path(self, browser: str, username: str, profile: str) -> str:
        """
        Get platform-specific browser history path
        
        Args:
            browser: Browser name
            username: Username
            profile: Profile name
            
        Returns:
            Full path to history file
        """
        pass
        
    @abstractmethod
    def get_path_separator(self) -> str:
        """Get platform-specific path separator"""
        pass

class WindowsPlatformHandler(PlatformHandler):
    """Windows-specific operations"""
    
    def get_file_size_command(self, file_path: str) -> Tuple[str, str]:
        return "runscript", f"ls {file_path}"
        
    def parse_file_size_output(self, output: str, file_path: str) -> Optional[int]:
        """Parse Windows ls output for file size"""
        # TODO: Move Windows-specific parsing from FalconClient.get_file_size()
        # Check for "File Not Found" or "The system cannot find the file specified"
        # Use regex pattern to extract size
        if "File Not Found" in output or "The system cannot find the file specified" in output:
            return None
            
        # Pattern from original code
        pattern = re.compile(
            r'^(?!Name|----)(?!.*<Directory>).*?(\d+)\s+\d+(?:\.\d+)?\s+\d{1,2}/\d{1,2}/\d{4}',
            flags=re.MULTILINE
        )
        
        match = pattern.search(output)
        if match:
            try:
                return int(match.group(1))
            except (ValueError, TypeError):
                return None
        return None
        
    def get_browser_history_path(self, browser: str, username: str, profile: str) -> str:
        """Get Windows browser history path"""
        # TODO: Extract Windows-specific logic from FalconClient.get_browser_history()
        browser_lower = browser.lower()
        
        if browser_lower in ["chrome", "edge", "brave"]:
            # Chromium-based browsers
            return f"'{profile}'\\History"
        elif browser_lower == "firefox":
            # Firefox
            return f"'{profile}'\\places.sqlite"
        else:
            raise ValueError(f"Unsupported browser: {browser}")
            
    def get_path_separator(self) -> str:
        return "\\"

class MacPlatformHandler(PlatformHandler):
    """macOS-specific operations"""
    
    def get_file_size_command(self, file_path: str) -> Tuple[str, str]:
        return "runscript", f"ls -l {file_path}"
        
    def parse_file_size_output(self, output: str, file_path: str) -> Optional[int]:
        """Parse macOS ls -l output for file size"""
        # TODO: Move Mac-specific parsing from FalconClient.get_file_size()
        if "No such file or directory" in output:
            return None
            
        # Pattern from original code
        file_size_match = re.search(
            r"(?<=\s)(\d+)(?=\s(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec))",
            output
        )
        
        if file_size_match:
            try:
                return int(file_size_match.group(1))
            except (ValueError, TypeError):
                return None
        return None
        
    def get_browser_history_path(self, browser: str, username: str, profile: str) -> str:
        """Get macOS browser history path"""
        # TODO: Extract Mac-specific logic from FalconClient.get_browser_history()
        browser_lower = browser.lower()
        
        if browser_lower in ["chrome", "edge", "brave"]:
            # Chromium-based browsers
            return f"'{profile}'/History"
        elif browser_lower == "firefox":
            # Firefox
            return f"'{profile}'/places.sqlite"
        else:
            raise ValueError(f"Unsupported browser: {browser}")
            
    def get_path_separator(self) -> str:
        return "/"

class LinuxPlatformHandler(PlatformHandler):
    """Linux-specific operations"""
    
    def get_file_size_command(self, file_path: str) -> Tuple[str, str]:
        # Similar to macOS
        return "runscript", f"ls -l {file_path}"
        
    def parse_file_size_output(self, output: str, file_path: str) -> Optional[int]:
        """Parse Linux ls -l output for file size"""
        # Similar to macOS implementation
        if "No such file or directory" in output:
            return None
            
        file_size_match = re.search(
            r"(?<=\s)(\d+)(?=\s(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec))",
            output
        )
        
        if file_size_match:
            try:
                return int(file_size_match.group(1))
            except (ValueError, TypeError):
                return None
        return None
        
    def get_browser_history_path(self, browser: str, username: str, profile: str) -> str:
        """Get Linux browser history path"""
        browser_lower = browser.lower()
        
        if browser_lower in ["chrome", "edge", "brave"]:
            # Chromium-based browsers
            return f"'{profile}'/History"
        elif browser_lower == "firefox":
            # Firefox
            return f"'{profile}'/places.sqlite"
        else:
            raise ValueError(f"Unsupported browser: {browser}")
            
    def get_path_separator(self) -> str:
        return "/"

class PlatformFactory:
    """Factory for creating platform-specific handlers"""
    
    @staticmethod
    def create_handler(platform: Platform) -> PlatformHandler:
        """
        Create appropriate platform handler
        
        Args:
            platform: Target platform
            
        Returns:
            Platform-specific handler instance
            
        Raises:
            NotImplementedError: If platform is not supported
        """
        handlers = {
            Platform.WINDOWS: WindowsPlatformHandler,
            Platform.MAC: MacPlatformHandler,
            Platform.LINUX: LinuxPlatformHandler,
        }
        
        handler_class = handlers.get(platform)
        if not handler_class:
            raise NotImplementedError(f"Platform {platform.value} not supported")
            
        return handler_class()