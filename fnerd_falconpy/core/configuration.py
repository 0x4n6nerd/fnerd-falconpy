"""
Configuration management for the Falcon client.
"""

import os
import logging
from typing import Dict, Any, Optional
from .base import Platform, IConfigProvider
from ..utils.env_loader import load_environment
from ..utils.config_loader import get_config_loader

logger = logging.getLogger(__name__)

class Configuration(IConfigProvider):
    """Centralized configuration management with configurable workspace paths.
    
    Manages all configuration settings including:
    - Workspace paths for forensic tool deployment (configurable via config.yaml)
    - S3 bucket and proxy settings
    - Timeout values for various operations
    - Browser paths for artifact collection
    """
    
    def __init__(self):
        """Initialize configuration, load environment variables, and apply workspace settings.
        
        Loads configuration from:
        1. Environment variables (.env file or system)
        2. External config.yaml file (for workspace paths, S3 settings, etc.)
        """
        self._env_loaded = load_environment()
        if self._env_loaded:
            logger.info("Environment variables loaded successfully")
        else:
            logger.warning("No .env file found, using system environment variables only")
        
        # Load external configuration file
        self.config_loader = get_config_loader()
        
        # Override AWS_SETTINGS with values from config file
        self._update_aws_settings()
        
        # Override workspace paths with values from config file
        self._update_workspace_settings()
    
    # Browser paths configuration
    BROWSER_PATHS = {
        "chrome": {
            Platform.WINDOWS: "C:\\Users\\{user}\\AppData\\Local\\Google\\Chrome\\'User Data'\\",
            Platform.MAC: "/Users/{user}/Library/'Application Support'/Google/Chrome/",
            Platform.LINUX: "/home/{user}/.config/google-chrome/"
        },
        "firefox": {
            Platform.WINDOWS: "C:\\Users\\{user}\\AppData\\Roaming\\Mozilla\\Firefox\\Profiles\\",
            Platform.MAC: "/Users/{user}/Library/'Application Support'/Firefox/Profiles/",
            Platform.LINUX: "/home/{user}/.mozilla/firefox/"
        },
        "brave": {
            Platform.WINDOWS: "C:\\Users\\{user}\\AppData\\Local\\BraveSoftware\\Brave-Browser\\'User Data'\\",
            Platform.MAC: "/Users/{user}/Library/'Application Support'/BraveSoftware/Brave-Browser/'User Data'/",
            Platform.LINUX: "/home/{user}/.config/BraveSoftware/Brave-Browser/"
        },
        "edge": {
            Platform.WINDOWS: "C:\\Users\\{user}\\AppData\\Local\\Microsoft\\Edge\\'User Data'\\",
            Platform.MAC: "/Users/{user}/Library/'Application Support'/'Microsoft Edge'/'User Data'/",
            Platform.LINUX: "/home/{user}/.config/microsoft-edge/"
        },
        "opera": {
            Platform.WINDOWS: "C:\\Users\\{user}\\AppData\\Roaming\\'Opera Software'\\'Opera Stable'\\",
            Platform.MAC: "/Users/{user}/Library/'Application Support'/com.operasoftware.Opera/",
            Platform.LINUX: "/home/{user}/.config/opera/"
        },
        "safari": {
            Platform.MAC: "/Users/{user}/Library/Safari/"
        },
        "vivaldi": {
            Platform.WINDOWS: "C:\\Users\\{user}\\AppData\\Local\\Vivaldi\\'User Data'\\",
            Platform.MAC: "/Users/{user}/Library/'Application Support'/Vivaldi/'User Data'/",
            Platform.LINUX: "/home/{user}/.config/vivaldi/"
        },
        "arc": {
            Platform.WINDOWS: "C:\\Users\\{user}\\AppData\\Local\\Arc\\'User Data'\\",
            Platform.MAC: "/Users/{user}/Library/'Application Support'/Arc/'User Data'/"
        },
        "opera_gx": {
            Platform.WINDOWS: "C:\\Users\\{user}\\AppData\\Local\\'Opera Software'\\'Opera GX Stable'\\",
            Platform.MAC: "/Users/{user}/Library/'Application Support'/'Opera Software'/'Opera GX Stable'/",
            Platform.LINUX: "/home/{user}/.config/opera-gx/"
        },
        "tor": {
            Platform.WINDOWS: "C:\\Users\\{user}\\Desktop\\Tor Browser\\Browser\\TorBrowser\\Data\\Browser\\profile.default\\",
            Platform.MAC: "/Applications/'Tor Browser.app'/Contents/MacOS/Tor/'Tor Browser'/Data/Browser/profile.default/",
            Platform.LINUX: "/home/{user}/tor-browser_en-US/Browser/TorBrowser/Data/Browser/profile.default/"
        }
    }
    
    # Browser root paths for discovery
    BROWSER_ROOT = {
        Platform.WINDOWS: {
            "all": "C:\\Users\\{user}\\AppData\\Local\\",
            "other": "C:\\Users\\{user}\\AppData\\Roaming\\"
        },
        Platform.MAC: {
            "all": "/Users/{user}/Library/'Application Support'/"
        },
        Platform.LINUX: {
            "all": "/home/{user}/.config/",
            "other": "/home/{user}/.mozilla/"
        }
    }
    
    # Operation timeouts (in seconds)
    TIMEOUTS = {
        "command_execution": 600,  # 10 minutes (increased from 120s for bodyfile generation)
        "command_status_check": 2,  # Interval between status checks
        "file_download": 600,  # 10 minutes (increased from 300s for large collection files)
        "file_upload": 1500,  # 25 minutes
        "kape_execution": 7200,  # 2 hours (legacy, use target_timeouts)
        "kape_monitoring": 30,  # 30 seconds for monitoring commands (ps, ls during KAPE)
        "kape_basic": 300,      # 5 minutes for !BasicCollection
        "kape_triage": 1800,    # 30 minutes for KapeTriage
        "kape_comprehensive": 7200,  # 2 hours for full collections
        "session_pulse": 60,
        "sha_retrieval": 100,
        "max_retries": 60  # For command status polling
    }
    
    # File operation settings
    FILE_SETTINGS = {
        "upload_rate": 5000000,  # bytes per second (for timeout estimation)
        "max_file_size": 5 * 1024 * 1024 * 1024,  # 5GB
        "chunk_size": 1024 * 1024  # 1MB chunks for reading
    }
    
    # AWS/S3 settings (default values, will be overridden by config file if present)
    AWS_SETTINGS = {
        "default_bucket": "your-s3-bucket-name",
        "proxy_host": "",
        "proxy_ip": "",
        "proxy_enabled": False,
        "endpoint_url": None,
        "region": "us-east-1",
        "velocirapter_host": "",
        "velocirapter_ip": ""
    }
    
    # KAPE settings (default values - will be updated from config file)
    KAPE_SETTINGS = {
        "base_path": "C:\\0x4n6nerd",  # Default Windows workspace, configurable via workspace.windows in config.yaml
        "temp_path": "C:\\0x4n6nerd\\temp",  # Temp directory within workspace, updated dynamically
        "monitoring_interval": 60,  # seconds between status checks
        "vhdx_name_pattern": "%m-triage",
        "target_timeouts": {  # Target-specific timeouts in seconds
            # Based on real-world performance data
            "!BasicCollection": 300,      # 5 minutes (2-5 min typical)
            "KapeTriage": 1800,          # 30 minutes (15-30 min typical)
            "RegistryHives": 60,         # 1 minute (30-60 sec typical)
            "EventLogs": 180,            # 3 minutes (1-3 min typical)
            "FileSystem": 600,           # 10 minutes (5-10 min typical)
            "BrowsingHistory": 300,      # 5 minutes (2-5 min typical)
            "!SANS_Triage": 1200,        # 20 minutes (10-20 min typical)
            "MemoryFiles": 120,          # 2 minutes (1-2 min typical)
            "WebBrowsers": 300,          # 5 minutes
            "WindowsDefender": 180,      # 3 minutes
            "!Compound": 2400,           # 40 minutes (compound targets)
            "default": 7200              # 2 hours fallback
        },
        "performance_metrics": {
            "sparse_file_optimization": True,  # v0.83+ feature
            "deduplication_enabled": True,
            "vss_default_depth": 3,  # Last 3 shadow copies
            "max_concurrent_instances": 5,
            "optimal_concurrent": 3  # 3-5 is optimal per endpoint
        },
        "optimized_targets": {
            # Investigation-specific optimized targets
            "EmergencyTriage": {
                "time": "2-5 minutes",
                "description": "Critical artifacts for immediate incident assessment",
                "artifacts": ["Registry core", "Recent events", "Prefetch"]
            },
            "MalwareAnalysis": {
                "time": "5-15 minutes",
                "description": "Focused collection for malware investigations",
                "artifacts": ["Execution evidence", "Persistence", "Network traces"]
            },
            "RansomwareResponse": {
                "time": "3-8 minutes",
                "description": "Rapid collection for ransomware incidents",
                "artifacts": ["USN Journal", "Ransom notes", "Shadow copies"]
            },
            "InsiderThreat": {
                "time": "15-30 minutes",
                "description": "User behavior and data exfiltration artifacts",
                "artifacts": ["Browser history", "Email", "USB activity", "Cloud logs"]
            },
            "APTComprehensive": {
                "time": "30+ minutes",
                "description": "Deep forensic analysis for sophisticated threats",
                "artifacts": ["Complete registry", "All logs", "Memory", "Network"]
            }
        },
        "target_optimization": {
            "min_size_default": 1024,  # 1KB - exclude empty/corrupt files
            "max_size_registry": 536870912,  # 512MB for registry hives
            "max_size_logs": 104857600,  # 100MB for event logs
            "max_size_prefetch": 2097152,  # 2MB for prefetch files
            "use_regex_patterns": True,
            "enable_path_variables": True  # %user%, %s%, %d% expansion
        }
    }
    
    # UAC settings (default values - will be updated from config file)
    UAC_SETTINGS = {
        "base_path": "/opt/0x4n6nerd",  # Default Unix workspace, configurable via workspace.unix in config.yaml
        "evidence_path": "/opt/0x4n6nerd/evidence",  # Evidence directory within workspace, updated dynamically
        "monitoring_interval": 30,  # seconds between status checks
        "default_profile": "ir_triage",
        "timeout": 18000,  # 5 hours default timeout (for 3.4GB+ files)
        "binary_path": os.getenv("UAC_BINARY_PATH", ""),  # Path to UAC binary (optional)
        "profile_timeouts": {  # Profile-specific timeouts in seconds
            # Real-world test data for ir_triage on macOS:
            # - Total: 4721 seconds (~79 minutes)
            # - hash_executables: ~35 minutes
            # - bodyfile: ~5 minutes
            # - File system searches: 15-20 minutes total
            "ir_triage": 7200,    # 2 hours (tested at ~79 minutes)
            "full": 21600,        # 6 hours (includes all artifacts)
            "offline": 3600,      # 1 hour (minimal live response)
            "offline_ir_triage": 1800,  # 30 minutes (offline triage)
            "logs": 3600,         # 1 hour (log collection only)
            "memory_dump": 18000, # 5 hours (memory intensive)
            "files": 14400,       # 4 hours (extensive file collection)
            "network": 1800,      # 30 minutes (network artifacts only)
            # Custom profiles (based on research)
            "quick_triage": 1200, # 20 minutes (minimal collection)
            "ransomware_response": 5400,  # 90 minutes
            "web_compromise": 3600,  # 60 minutes
            "malware_hunt": 9000,  # 150 minutes (includes hash_executables)
            "insider_threat": 3600,  # 60 minutes
            "apt_investigation": 14400,  # 4 hours (comprehensive)
            # New optimized profiles based on timing analysis
            "quick_triage_optimized": 3600,  # 60 minutes (allow time for archiving)
            "ir_triage_no_hash": 5400,       # 90 minutes (should be much faster than full ir_triage)
            "network_compromise": 2700,       # 45 minutes (conservative)
            "malware_hunt_fast": 4500         # 75 minutes (conservative)
        },
        "available_profiles": [
            "ir_triage",
            "full",
            "offline",
            "logs",
            "memory_dump",
            "files",
            "network",
            # Optimized profiles
            "quick_triage_optimized",
            "ir_triage_no_hash",
            "network_compromise",
            "malware_hunt_fast"
        ]
    }
    
    # Browser Collection Settings
    BROWSER_SETTINGS = {
        "max_concurrent_downloads": 5,  # Number of concurrent downloads
        "download_timeout": 300,        # 5 minutes per file
        "max_file_size": 1073741824,    # 1GB max file size
        "retry_attempts": 3             # Number of retry attempts per file
    }
    
    def get_browser_path(self, browser: str, platform: Platform, user: str) -> str:
        """
        Get browser path for specific platform and user
        
        Args:
            browser: Browser name (e.g., 'chrome', 'firefox')
            platform: Target platform
            user: Username to insert into path
            
        Returns:
            Formatted browser path
            
        Raises:
            ValueError: If browser or platform is not supported
        """
        browser_lower = browser.lower()
        
        if browser_lower not in self.BROWSER_PATHS:
            raise ValueError(f"Unknown browser: '{browser}'")
            
        if platform not in self.BROWSER_PATHS[browser_lower]:
            raise ValueError(f"Browser '{browser}' is not supported on platform '{platform.value}'")
            
        path_template = self.BROWSER_PATHS[browser_lower][platform]
        return path_template.format(user=user)
    
    def get_browser_root_paths(self, platform: Platform) -> Dict[str, str]:
        """
        Get browser root paths for platform
        
        Args:
            platform: Target platform
            
        Returns:
            Dictionary of root paths
        """
        return self.BROWSER_ROOT.get(platform, {})
    
    def get_timeout(self, operation: str) -> int:
        """
        Get timeout for specific operation
        
        Args:
            operation: Operation name
            
        Returns:
            Timeout in seconds (defaults to 60 if operation not found)
        """
        return self.TIMEOUTS.get(operation, 60)
    
    def get_file_setting(self, setting: str) -> int:
        """
        Get file operation setting
        
        Args:
            setting: Setting name
            
        Returns:
            Setting value
        """
        return self.FILE_SETTINGS.get(setting, 0)
    
    def get_aws_setting(self, setting: str) -> str:
        """
        Get AWS/S3 setting
        
        Args:
            setting: Setting name
            
        Returns:
            Setting value
        """
        return self.AWS_SETTINGS.get(setting, "")
    
    def get_kape_setting(self, setting: str) -> str:
        """
        Get KAPE setting
        
        Args:
            setting: Setting name
            
        Returns:
            Setting value
        """
        return self.KAPE_SETTINGS.get(setting, "")
    
    def get_uac_setting(self, setting: str):
        """
        Get UAC setting
        
        Args:
            setting: Setting name
            
        Returns:
            Setting value (can be string, int, dict, or list)
        """
        return self.UAC_SETTINGS.get(setting)
    
    def get_browser_setting(self, setting: str):
        """
        Get browser setting
        
        Args:
            setting: Setting name
            
        Returns:
            Setting value (can be string, int, dict, or list)
        """
        return self.BROWSER_SETTINGS.get(setting)
    
    def get_workspace_path(self, platform: Platform) -> str:
        """
        Get the configured workspace path for a specific platform.
        
        Workspace paths are configurable via config.yaml and determine where
        forensic collection tools are deployed on target endpoints.
        
        Args:
            platform: The platform to get the workspace path for
            
        Returns:
            The configured workspace path for the platform
            - Windows: Returns KAPE workspace (default: C:\0x4n6nerd)
            - Unix/Linux/macOS: Returns UAC workspace (default: /opt/0x4n6nerd)
        """
        if platform == Platform.WINDOWS:
            return self.KAPE_SETTINGS.get("base_path", "C:\\0x4n6nerd")
        else:
            return self.UAC_SETTINGS.get("base_path", "/opt/0x4n6nerd")
    
    def get_env_var(self, var_name: str, default: str = "") -> str:
        """
        Get environment variable value
        
        Args:
            var_name: Environment variable name
            default: Default value if variable not found
            
        Returns:
            Environment variable value or default
        """
        return os.getenv(var_name, default)
    
    def is_env_loaded(self) -> bool:
        """
        Check if .env file was successfully loaded
        
        Returns:
            True if .env file was loaded, False otherwise
        """
        return self._env_loaded
    
    def _update_workspace_settings(self) -> None:
        """Update workspace paths from configuration file.
        
        Reads workspace configuration from config.yaml and updates:
        - Windows workspace path (for KAPE deployments) - default: C:\0x4n6nerd
        - Unix workspace path (for UAC deployments) - default: /opt/0x4n6nerd
        
        These paths determine where forensic tools are deployed on target endpoints.
        """
        if not self.config_loader:
            return
            
        # Get workspace configuration from config file
        workspace_config = self.config_loader.get("workspace", {})
        
        if workspace_config:
            # Update Windows workspace path (KAPE)
            if "windows" in workspace_config:
                windows_path = workspace_config["windows"]
                self.KAPE_SETTINGS["base_path"] = windows_path
                self.KAPE_SETTINGS["temp_path"] = f"{windows_path}\\temp"
                logger.info(f"Windows workspace path set to: {windows_path}")
            
            # Update Unix/Linux/macOS workspace path (UAC)
            if "unix" in workspace_config:
                unix_path = workspace_config["unix"]
                self.UAC_SETTINGS["base_path"] = unix_path
                self.UAC_SETTINGS["evidence_path"] = f"{unix_path}/evidence"
                logger.info(f"Unix workspace path set to: {unix_path}")
    
    def _update_aws_settings(self) -> None:
        """Update AWS settings from configuration file."""
        if not self.config_loader:
            return
            
        # Get S3 configuration
        s3_config = self.config_loader.get_s3_config()
        self.AWS_SETTINGS["default_bucket"] = s3_config.get("bucket_name", self.AWS_SETTINGS["default_bucket"])
        self.AWS_SETTINGS["endpoint_url"] = s3_config.get("endpoint_url")
        self.AWS_SETTINGS["region"] = s3_config.get("region", self.AWS_SETTINGS["region"])
        
        # Get proxy configuration
        proxy_config = self.config_loader.get_proxy_config()
        self.AWS_SETTINGS["proxy_host"] = proxy_config.get("host", self.AWS_SETTINGS["proxy_host"])
        self.AWS_SETTINGS["proxy_ip"] = proxy_config.get("ip", self.AWS_SETTINGS["proxy_ip"])
        self.AWS_SETTINGS["proxy_enabled"] = proxy_config.get("enabled", self.AWS_SETTINGS["proxy_enabled"])
        
        # Get alternative endpoints
        alt_endpoints = self.config_loader.get_alternative_endpoints()
        if "velociraptor" in alt_endpoints:
            velociraptor = alt_endpoints["velociraptor"]
            self.AWS_SETTINGS["velocirapter_host"] = velociraptor.get("host", self.AWS_SETTINGS["velocirapter_host"])
            self.AWS_SETTINGS["velocirapter_ip"] = velociraptor.get("ip", self.AWS_SETTINGS["velocirapter_ip"])
        
        logger.info(f"AWS settings updated from config file: bucket={self.AWS_SETTINGS['default_bucket']}, proxy={self.AWS_SETTINGS['proxy_host']}")
    
    def get_s3_bucket(self) -> str:
        """Get configured S3 bucket name."""
        return self.AWS_SETTINGS.get("default_bucket", "your-s3-bucket-name")
    
    def get_s3_endpoint(self) -> Optional[str]:
        """Get configured S3 endpoint URL."""
        return self.AWS_SETTINGS.get("endpoint_url")
    
    def get_proxy_host(self) -> str:
        """Get configured proxy host."""
        return self.AWS_SETTINGS.get("proxy_host", "")
    
    def get_proxy_ip(self) -> str:
        """Get configured proxy IP."""
        return self.AWS_SETTINGS.get("proxy_ip", "54.148.116.132")
    
    def is_proxy_enabled(self) -> bool:
        """Check if proxy is enabled."""
        return self.AWS_SETTINGS.get("proxy_enabled", True)
    
    def reload_config(self) -> None:
        """Reload configuration from file."""
        if self.config_loader:
            self.config_loader.reload()
            self._update_aws_settings()
            logger.info("Configuration reloaded")
    
    def get_host_entries(self) -> list:
        """
        Get host entries that should be added to /etc/hosts on endpoints.
        
        Returns:
            List of host entry dictionaries with 'ip', 'hostname', and optional 'comment'
        """
        if self.config_loader:
            return self.config_loader.get_host_entries()
        
        # Fallback to default entries if no config loader
        return [
            {
                'ip': self.AWS_SETTINGS.get('velocirapter_ip', '44.231.123.212'),
                'hostname': self.AWS_SETTINGS.get('velocirapter_host', ''),
                'comment': 'velociraptor'
            },
            {
                'ip': self.AWS_SETTINGS.get('proxy_ip', '54.148.116.132'),
                'hostname': self.AWS_SETTINGS.get('proxy_host', ''),
                'comment': 's3-proxy'
            }
        ]
    
    def generate_hosts_command(self, platform: str = "windows") -> str:
        """
        Generate the command to add host entries based on the platform.
        
        Args:
            platform: Target platform ('windows' or 'unix')
            
        Returns:
            Command string to add all host entries
        """
        host_entries = self.get_host_entries()
        
        if not host_entries:
            return ""
        
        if platform.lower() == "windows":
            # Windows PowerShell command
            commands = []
            for entry in host_entries:
                ip = entry.get('ip')
                hostname = entry.get('hostname')
                comment = entry.get('comment', '')
                
                if ip and hostname:
                    # Format: IP<tab>hostname<tab>#comment
                    line = f"{ip}`t{hostname}"
                    if comment:
                        line += f"`t#{comment}"
                    
                    commands.append(
                        f"Add-Content -Path 'C:\\Windows\\System32\\drivers\\etc\\hosts' -Value '{line}'"
                    )
            
            if commands:
                # Join all commands with semicolon
                hosts_cmd = "runscript -Raw=```" + "; ".join(commands) + "```"
                return hosts_cmd
                
        else:  # Unix/Linux/macOS
            # Unix shell command
            commands = []
            for entry in host_entries:
                ip = entry.get('ip')
                hostname = entry.get('hostname')
                comment = entry.get('comment', '')
                
                if ip and hostname:
                    # Format: IP hostname #comment
                    line = f"{ip} {hostname}"
                    if comment:
                        line += f" #{comment}"
                    
                    commands.append(f"echo '{line}' >> /etc/hosts")
            
            if commands:
                # Join all commands with semicolon
                hosts_cmd = "runscript -Raw=```" + "; ".join(commands) + "```"
                return hosts_cmd
        
        return ""