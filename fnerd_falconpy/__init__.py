"""
4n6NerdStriker - A forensics collection toolkit for CrowdStrike Falcon RTR

A comprehensive Python package for CrowdStrike Falcon RTR forensic collection
and analysis operations.
"""

__version__ = "1.3.0"
__author__ = "0x4n6nerd"

# Core imports
from fnerd_falconpy.core.base import (
    HostInfo,
    Platform,
    RTRSession,
    CommandResult,
    ILogger,
    DefaultLogger,
    IConfigProvider
)

# Main orchestrators
from fnerd_falconpy.orchestrator import FalconForensicOrchestrator
from fnerd_falconpy.orchestrator_optimized import OptimizedFalconForensicOrchestrator

# Managers
from fnerd_falconpy.managers.managers import (
    HostManager,
    SessionManager,
    FileManager
)

# Collectors
from fnerd_falconpy.collectors.collectors import (
    BrowserHistoryCollector,
    ForensicCollector
)
from fnerd_falconpy.collectors.uac_collector import UACCollector

# Configuration
from fnerd_falconpy.core.configuration import Configuration

# Platform handlers
from fnerd_falconpy.utils.platform_handlers import (
    PlatformHandler,
    WindowsPlatformHandler,
    MacPlatformHandler,
    LinuxPlatformHandler,
    PlatformFactory
)

# Cloud storage
from fnerd_falconpy.utils.cloud_storage import CloudStorageManager

# API clients (for advanced usage)
from fnerd_falconpy.api.clients import (
    DiscoverAPIClient,
    RTRAPIClient
)
from fnerd_falconpy.api.clients_optimized import (
    OptimizedDiscoverAPIClient,
    OptimizedRTRAPIClient
)

# RTR Interactive Session
from fnerd_falconpy.rtr import (
    RTRInteractiveSession,
    RTRCommandParser,
    RTRCommand
)

# Response actions
from fnerd_falconpy.response import (
    HostIsolationManager,
    IsolationResult,
    ResponsePolicyManager
)

# Discovery
from fnerd_falconpy.discovery import DeviceDiscovery

# Convenience exports
__all__ = [
    # Version info
    "__version__",
    
    # Main classes
    "FalconForensicOrchestrator",
    "OptimizedFalconForensicOrchestrator",
    
    # Data classes
    "HostInfo",
    "Platform", 
    "RTRSession",
    "CommandResult",
    
    # Interfaces
    "ILogger",
    "DefaultLogger",
    "IConfigProvider",
    
    # Managers
    "HostManager",
    "SessionManager", 
    "FileManager",
    
    # Collectors
    "BrowserHistoryCollector",
    "ForensicCollector",
    "UACCollector",
    
    # Configuration
    "Configuration",
    
    # Platform support
    "PlatformHandler",
    "WindowsPlatformHandler",
    "MacPlatformHandler", 
    "LinuxPlatformHandler",
    "PlatformFactory",
    
    # Cloud
    "CloudStorageManager",
    
    # API clients
    "DiscoverAPIClient",
    "RTRAPIClient",
    "OptimizedDiscoverAPIClient",
    "OptimizedRTRAPIClient",
    
    # RTR Interactive
    "RTRInteractiveSession",
    "RTRCommandParser",
    "RTRCommand",
    
    # Response actions
    "HostIsolationManager",
    "IsolationResult",
    "ResponsePolicyManager",
    
    # Discovery
    "DeviceDiscovery",
]