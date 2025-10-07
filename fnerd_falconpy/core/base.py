"""
Base classes and interfaces for the modular Falcon client.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

# ============================================================================
# DATA CLASSES AND ENUMS
# ============================================================================

@dataclass
class HostInfo:
    """Data class for host information"""
    hostname: str
    aid: str
    cid: str
    os_name: str
    os_version: str
    cpu_name: str
    platform: str
    
class Platform(Enum):
    """Supported platforms"""
    WINDOWS = "windows"
    MAC = "mac"
    LINUX = "linux"
    
@dataclass
class RTRSession:
    """Data class for RTR session information"""
    session_id: str
    device_id: str
    status_code: int
    created_at: float
    raw_response: Dict[str, Any]  # Store full response for compatibility
    
@dataclass
class CommandResult:
    """Data class for command execution results"""
    stdout: str
    stderr: str
    return_code: int
    cloud_request_id: str
    complete: bool

# ============================================================================
# BASE INTERFACES
# ============================================================================

class ILogger(ABC):
    """Interface for logging operations"""
    @abstractmethod
    def info(self, message: str) -> None:
        pass
    
    @abstractmethod
    def error(self, message: str, exc_info: bool = False) -> None:
        pass
    
    @abstractmethod
    def warning(self, message: str) -> None:
        pass
    
    @abstractmethod
    def debug(self, message: str) -> None:
        pass

class IConfigProvider(ABC):
    """Interface for configuration management"""
    @abstractmethod
    def get_browser_path(self, browser: str, platform: Platform, user: str) -> str:
        pass
    
    @abstractmethod
    def get_browser_root_paths(self, platform: Platform) -> Dict[str, str]:
        pass
    
    @abstractmethod
    def get_timeout(self, operation: str) -> int:
        pass

# ============================================================================
# DEFAULT IMPLEMENTATIONS
# ============================================================================

class DefaultLogger(ILogger):
    """Default logger implementation using Python's logging module"""
    
    def __init__(self, name: str = __name__, level: int = logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # Only add handlers if neither this logger nor root logger has handlers
        # This prevents duplicate logging when basicConfig has been called
        if not self.logger.handlers and not logging.root.handlers:
            handler = logging.StreamHandler()
            # Set handler to ERROR level to suppress WARNING messages from console
            # WARNINGs will still be logged to files when file handlers are added
            handler.setLevel(logging.ERROR)
            formatter = logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            # Prevent propagation to avoid duplicate logs
            self.logger.propagate = False
    
    def info(self, message: str) -> None:
        self.logger.info(message)
    
    def error(self, message: str, exc_info: bool = False) -> None:
        self.logger.error(message, exc_info=exc_info)
    
    def warning(self, message: str) -> None:
        self.logger.warning(message)
    
    def debug(self, message: str) -> None:
        self.logger.debug(message)