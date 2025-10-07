"""
Utility classes and helper functions.
"""

from fnerd_falconpy.utils.platform_handlers import (
    PlatformHandler,
    WindowsPlatformHandler,
    MacPlatformHandler,
    LinuxPlatformHandler,
    PlatformFactory
)

from fnerd_falconpy.utils.env_loader import (
    load_environment,
    find_dotenv_file,
    get_env_search_paths,
    create_example_env_file,
    validate_falcon_credentials
)

try:
    from fnerd_falconpy.utils.cloud_storage import CloudStorageManager
    _cloud_storage_available = True
except ImportError:
    CloudStorageManager = None
    _cloud_storage_available = False

__all__ = [
    "PlatformHandler",
    "WindowsPlatformHandler",
    "MacPlatformHandler", 
    "LinuxPlatformHandler",
    "PlatformFactory",
    "load_environment",
    "find_dotenv_file", 
    "get_env_search_paths",
    "create_example_env_file",
    "validate_falcon_credentials",
]

if _cloud_storage_available:
    __all__.append("CloudStorageManager")