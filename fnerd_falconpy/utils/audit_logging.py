"""
Audit logging utilities for fnerd_falconpy operations.
Provides centralized logging with rotation and archival for compliance and security.
"""

import os
import logging
import gzip
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional


class AuditLogger:
    """Centralized audit logger with rotation and archival."""
    
    def __init__(self, log_dir: Optional[str] = None):
        """
        Initialize audit logger.
        
        Args:
            log_dir: Custom log directory (defaults to ~/.fnerd_falconpy/logs)
        """
        self.log_dir = Path(log_dir or os.path.expanduser("~/.fnerd_falconpy/logs"))
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Archive old logs on startup
        self._archive_old_logs()
        
    def _archive_old_logs(self, days_to_keep: int = 30, days_to_compress: int = 7):
        """
        Archive and compress old log files.
        
        Args:
            days_to_keep: Total days to keep logs (compressed + uncompressed)
            days_to_compress: Days after which to compress logs
        """
        try:
            now = datetime.now()
            compress_date = now - timedelta(days=days_to_compress)
            delete_date = now - timedelta(days=days_to_keep)
            
            for log_file in self.log_dir.glob("fnerd_falconpy_audit_*.log"):
                try:
                    # Extract date from filename: fnerd_falconpy_audit_YYYYMMDD.log
                    date_str = log_file.stem.split('_')[-1]
                    file_date = datetime.strptime(date_str, "%Y%m%d")
                    
                    if file_date < delete_date:
                        # Delete old logs and their compressed versions
                        log_file.unlink(missing_ok=True)
                        compressed_file = log_file.with_suffix('.log.gz')
                        compressed_file.unlink(missing_ok=True)
                        
                    elif file_date < compress_date and file_date != now.date():
                        # Compress logs older than compress_date but newer than delete_date
                        compressed_file = log_file.with_suffix('.log.gz')
                        if not compressed_file.exists():
                            with open(log_file, 'rb') as f_in:
                                with gzip.open(compressed_file, 'wb') as f_out:
                                    shutil.copyfileobj(f_in, f_out)
                            log_file.unlink()  # Remove original after compression
                            
                except (ValueError, OSError) as e:
                    # Skip files that don't match expected format or can't be processed
                    continue
                    
        except Exception as e:
            # Don't fail startup due to archival issues
            pass
    
    def get_current_audit_log(self) -> Path:
        """Get the current audit log file path."""
        timestamp = datetime.now().strftime("%Y%m%d")
        return self.log_dir / f"fnerd_falconpy_audit_{timestamp}.log"
    
    def log_operation_start(self, operation: str, target: str, user: str = None):
        """Log the start of a security operation."""
        logger = logging.getLogger("fnerd_falconpy.audit")
        user_info = f" (User: {user})" if user else ""
        logger.info(f"OPERATION_START: {operation} on {target}{user_info}")
    
    def log_operation_end(self, operation: str, target: str, success: bool, details: str = None):
        """Log the completion of a security operation."""
        logger = logging.getLogger("fnerd_falconpy.audit")
        status = "SUCCESS" if success else "FAILURE"
        detail_info = f" - {details}" if details else ""
        logger.info(f"OPERATION_END: {operation} on {target} - {status}{detail_info}")
    
    def log_file_access(self, file_path: str, action: str, target: str):
        """Log file access operations."""
        logger = logging.getLogger("fnerd_falconpy.audit")
        logger.info(f"FILE_ACCESS: {action} {file_path} on {target}")
    
    def log_rtr_session(self, target: str, session_id: str, action: str):
        """Log RTR session activities."""
        logger = logging.getLogger("fnerd_falconpy.audit")
        logger.info(f"RTR_SESSION: {action} session {session_id} on {target}")
    
    def log_error(self, operation: str, target: str, error: str):
        """Log operational errors."""
        logger = logging.getLogger("fnerd_falconpy.audit")
        logger.error(f"OPERATION_ERROR: {operation} on {target} - {error}")


# Global audit logger instance
_audit_logger = None

def get_audit_logger() -> AuditLogger:
    """Get the global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def log_session_info(command_args: list, environment_info: dict = None):
    """Log session startup information for audit purposes."""
    logger = logging.getLogger("fnerd_falconpy.audit")
    
    # Log command execution
    command_str = ' '.join(command_args)
    logger.info(f"COMMAND_EXECUTED: {command_str}")
    
    # Log environment info if provided
    if environment_info:
        for key, value in environment_info.items():
            # Don't log sensitive information like API keys
            if 'secret' not in key.lower() and 'key' not in key.lower():
                logger.info(f"ENVIRONMENT: {key}={value}")
    
    # Log user context
    try:
        import getpass
        import socket
        user = getpass.getuser()
        hostname = socket.gethostname()
        logger.info(f"USER_CONTEXT: {user}@{hostname}")
    except Exception:
        pass


def cleanup_on_exit():
    """Cleanup function to call on program exit."""
    logger = logging.getLogger("fnerd_falconpy.audit")
    logger.info("=== Falcon Client Session Ended ===")