"""
Configuration loader for external config files (YAML/JSON).

NEW in v1.3.1: External configuration system replaces hardcoded values.
This module loads configuration from config.yaml for:
- S3 bucket and endpoint settings
- Proxy configuration
- Dynamic host entries for /etc/hosts
- Timeout values
- Alternative endpoints

The configuration system is designed to be flexible and backwards compatible.
If no config file exists, sensible defaults are used.
"""

import os
import yaml
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ConfigLoader:
    """Loads and manages external configuration files.
    
    The ConfigLoader searches for configuration files in this priority order:
    1. Explicitly provided path
    2. FALCON_CONFIG_PATH environment variable
    3. config.yaml/config.json in current directory
    4. ~/.fnerd_falconpy/config.yaml
    
    If no config file is found, default values are used for backwards compatibility.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration loader.
        
        IMPORTANT: This is called once at startup and cached globally.
        Changes to config file require restart or manual reload.
        
        Args:
            config_path: Optional explicit path to configuration file.
                        If None, searches in standard locations:
                        1. $FALCON_CONFIG_PATH environment variable
                        2. ./config.yaml or ./config.json (current directory)
                        3. ~/.fnerd_falconpy/config.yaml (user home)
        
        Example config.yaml structure:
            s3:
              bucket_name: "my-forensics-bucket"
            proxy:
              host: "proxy.example.com"
              ip: "10.0.0.1"
            host_entries:
              - ip: "10.0.0.2"
                hostname: "service.internal"
        """
        self.config_path = self._find_config_file(config_path)
        self.config: Dict[str, Any] = {}
        self._load_config()
        
    def _find_config_file(self, config_path: Optional[str] = None) -> Optional[Path]:
        """
        Find configuration file using multiple search strategies.
        
        Search order ensures flexibility while maintaining backwards compatibility.
        Most users place config.yaml in the project root directory.
        
        Args:
            config_path: Explicitly provided config path (highest priority)
            
        Returns:
            Path to config file if found, None otherwise (will use defaults)
        """
        # Priority 1: Explicitly provided path (for testing or custom setups)
        if config_path:
            path = Path(config_path)
            if path.exists():
                logger.info(f"Using config file from provided path: {path}")
                return path
            else:
                # Log warning but continue - will use defaults
                logger.warning(f"Provided config path does not exist: {path}")
        
        # Priority 2: Environment variable
        env_path = os.environ.get('FALCON_CONFIG_PATH')
        if env_path:
            path = Path(env_path)
            if path.exists():
                logger.info(f"Using config file from environment variable: {path}")
                return path
            else:
                logger.warning(f"Config path from env variable does not exist: {path}")
        
        # Priority 3: Current directory
        for filename in ['config.yaml', 'config.yml', 'config.json']:
            path = Path.cwd() / filename
            if path.exists():
                logger.info(f"Using config file from current directory: {path}")
                return path
        
        # Priority 4: User home directory
        home_config_dir = Path.home() / '.fnerd_falconpy'
        for filename in ['config.yaml', 'config.yml', 'config.json']:
            path = home_config_dir / filename
            if path.exists():
                logger.info(f"Using config file from home directory: {path}")
                return path
        
        logger.info("No configuration file found, will use default settings")
        return None
    
    def _load_config(self) -> None:
        """Load configuration from file."""
        if not self.config_path:
            return
            
        try:
            with open(self.config_path, 'r') as file:
                if self.config_path.suffix in ['.yaml', '.yml']:
                    self.config = yaml.safe_load(file) or {}
                elif self.config_path.suffix == '.json':
                    self.config = json.load(file)
                else:
                    logger.warning(f"Unknown config file extension: {self.config_path.suffix}")
                    return
                    
            logger.info(f"Successfully loaded configuration from {self.config_path}")
            
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse YAML config file: {e}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON config file: {e}")
        except Exception as e:
            logger.error(f"Failed to load config file: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation for nested access.
        
        This method allows accessing nested config values with a simple string.
        For example, 's3.bucket_name' accesses config['s3']['bucket_name'].
        
        Args:
            key: Configuration key using dot notation
                 Examples: 's3.bucket_name', 'proxy.host', 'timeouts.file_download'
            default: Default value returned if key not found (ensures backwards compatibility)
            
        Returns:
            Configuration value or default if not found
            
        Example:
            bucket = config.get('s3.bucket_name', 'default-bucket')
            timeout = config.get('timeouts.file_download', 3600)
        """
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
                
        return value if value is not None else default
    
    def get_s3_config(self) -> Dict[str, Any]:
        """Get S3 configuration with defaults.
        
        Returns complete S3 configuration needed for uploads.
        Supports custom S3-compatible services (MinIO, DigitalOcean Spaces, etc.)
        
        Returns:
            Dictionary with S3 settings:
            - bucket_name: Target S3 bucket
            - endpoint_url: Optional custom endpoint (for S3-compatible services)
            - region: AWS region (defaults to us-east-1)
            - Advanced settings for multipart uploads
        """
        return {
            'bucket_name': self.get('s3.bucket_name', 'your-s3-bucket-name'),
            'endpoint_url': self.get('s3.endpoint_url'),  # None for standard AWS S3
            'region': self.get('s3.region', 'us-east-1'),
            'presigned_url_expiration': self.get('advanced.presigned_url_expiration', 3600),
            'multipart_threshold': self.get('advanced.multipart_threshold', 104857600),
            'multipart_chunksize': self.get('advanced.multipart_chunksize', 10485760),
            'max_concurrent_transfers': self.get('advanced.max_concurrent_transfers', 10),
            'max_bandwidth': self.get('advanced.max_bandwidth', 0)
        }
    
    def get_proxy_config(self) -> Dict[str, Any]:
        """Get proxy configuration with defaults.
        
        Proxy is used for S3 uploads when direct internet access is not available.
        The proxy host/IP are added to /etc/hosts on target endpoints.
        
        Returns:
            Dictionary with:
            - host: Proxy hostname
            - ip: Proxy IP address (fallback if DNS fails)
            - enabled: Whether to use proxy (set False for direct S3 access)
        """
        return {
            'host': self.get('proxy.host', ''),
            'ip': self.get('proxy.ip', ''),
            'enabled': self.get('proxy.enabled', False)
        }
    
    def get_timeout_config(self) -> Dict[str, int]:
        """Get timeout configuration with defaults.
        
        CRITICAL: These timeouts were tuned for production based on real-world testing:
        - file_download: 5 hours for 3.4GB+ files over VPN
        - file_upload: 25 minutes for S3 uploads
        - sha_retrieval: 33 minutes for CrowdStrike to process large files
        - command_execution: 10 minutes for complex RTR commands
        
        Returns:
            Dictionary with timeout values in seconds
        """
        return {
            'file_download': self.get('timeouts.file_download', 18000),  # 5 hours
            'file_upload': self.get('timeouts.file_upload', 1500),       # 25 minutes
            'sha_retrieval': self.get('timeouts.sha_retrieval', 2000),   # ~33 minutes
            'command_execution': self.get('timeouts.command_execution', 600)  # 10 minutes
        }
    
    def get_alternative_endpoints(self) -> Dict[str, Any]:
        """Get alternative endpoint configurations."""
        return self.get('alternative_endpoints', {})
    
    def get_host_entries(self) -> list:
        """
        Get host entries that should be added to /etc/hosts on target endpoints.
        
        NEW in v1.3.1: Supports unlimited entries from config file.
        These entries are dynamically added during forensic collections to ensure
        endpoints can reach required services (S3 proxy, Velociraptor, etc.).
        
        Returns:
            List of host entry dictionaries, each containing:
            - ip: IP address
            - hostname: Fully qualified domain name
            - comment: Optional comment for the entry
            
        Example config.yaml:
            host_entries:
              - ip: "10.0.0.1"
                hostname: "proxy.internal"
                comment: "S3 proxy"
              - ip: "10.0.0.2"
                hostname: "velociraptor.internal"
        """
        host_entries = self.get('host_entries', [])
        
        # Ensure backwards compatibility - if no host_entries defined, use defaults
        if not host_entries:
            # Default entries for backward compatibility - empty by default
            host_entries = []
            
            # Also check proxy config and add if not already present
            proxy_config = self.get_proxy_config()
            if proxy_config.get('host') and proxy_config.get('ip'):
                # Check if proxy entry already exists
                proxy_exists = any(
                    entry['hostname'] == proxy_config['host'] 
                    for entry in host_entries
                )
                if not proxy_exists:
                    host_entries.append({
                        'ip': proxy_config['ip'],
                        'hostname': proxy_config['host'],
                        'comment': 'proxy-server'
                    })
        
        return host_entries
    
    def reload(self) -> None:
        """Reload configuration from file."""
        self.config = {}
        self._load_config()
        logger.info("Configuration reloaded")
    
    def update_config_value(self, key: str, value: Any) -> None:
        """
        Update a configuration value in memory (does not save to file).
        
        Args:
            key: Configuration key (supports dot notation)
            value: New value
        """
        keys = key.split('.')
        config = self.config
        
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
            
        config[keys[-1]] = value
        logger.debug(f"Updated config {key} = {value}")


# Global configuration instance
_config_loader: Optional[ConfigLoader] = None

def get_config_loader() -> ConfigLoader:
    """
    Get or create the global configuration loader instance.
    
    This implements a singleton pattern - the config is loaded once
    and reused throughout the application lifecycle.
    
    Returns:
        ConfigLoader instance (cached globally)
        
    Note:
        Call reload_config() if you need to refresh from disk
    """
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader

def reload_config() -> None:
    """Reload the global configuration."""
    global _config_loader
    if _config_loader:
        _config_loader.reload()
    else:
        _config_loader = ConfigLoader()