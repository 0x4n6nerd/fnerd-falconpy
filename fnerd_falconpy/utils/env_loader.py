"""
Smart environment file loading utility.

This module provides intelligent .env file resolution that searches multiple
locations to find environment configuration files.
"""

import os
import logging
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)


def find_dotenv_file() -> Optional[str]:
    """
    Find .env file in order of preference.
    
    Search order:
    1. Current working directory (./.env)
    2. User's home directory (~/.env)
    3. Package installation directory (relative to this file)
    
    Returns:
        str: Path to the found .env file, or None if not found
    """
    search_paths = [
        Path.cwd() / '.env',  # Current directory
        Path.home() / '.env',  # User home directory  
        Path(__file__).parent.parent.parent / '.env',  # Package root directory
    ]
    
    for path in search_paths:
        if path.exists() and path.is_file():
            logger.debug(f"Found .env file at: {path}")
            return str(path)
    
    logger.warning("No .env file found in any of the search locations")
    logger.debug(f"Searched paths: {[str(p) for p in search_paths]}")
    return None


def validate_falcon_credentials() -> tuple[bool, list[str]]:
    """
    Validate that required Falcon credentials are present.
    
    Returns:
        tuple: (is_valid, missing_vars) where is_valid is True if all 
               required credentials are present, and missing_vars is a 
               list of missing variable names
    """
    required_vars = ['FALCON_CLIENT_ID', 'FALCON_CLIENT_SECRET']
    missing_vars = []
    
    for var in required_vars:
        value = os.getenv(var)
        if not value or value.strip() == '':
            missing_vars.append(var)
    
    return len(missing_vars) == 0, missing_vars


def load_environment() -> bool:
    """
    Load environment variables with smart path resolution and validation.
    
    Attempts to find and load a .env file from multiple locations.
    Falls back to default dotenv behavior if no file is found.
    Validates that required Falcon credentials are present.
    
    Returns:
        bool: True if a .env file was found and loaded, False otherwise
    """
    env_file = find_dotenv_file()
    
    if env_file:
        logger.info(f"Loading environment from: {env_file}")
        load_dotenv(env_file)
        
        # Validate credentials after loading
        is_valid, missing_vars = validate_falcon_credentials()
        if not is_valid:
            logger.warning(f"Missing required Falcon credentials in {env_file}: {', '.join(missing_vars)}")
        else:
            logger.info("Required Falcon credentials found and loaded")
        
        return True
    else:
        logger.info("No .env file found, attempting default load_dotenv()")
        # Fallback to default behavior (looks in current directory)
        load_dotenv()
        
        # Check if credentials are available from system environment
        is_valid, missing_vars = validate_falcon_credentials()
        if not is_valid:
            logger.warning(f"Missing required Falcon credentials from environment: {', '.join(missing_vars)}")
        
        return False


def get_env_search_paths() -> list[str]:
    """
    Get the list of paths that will be searched for .env files.
    
    Useful for debugging or displaying to users where .env files
    should be placed.
    
    Returns:
        list[str]: List of paths that are searched for .env files
    """
    search_paths = [
        Path.cwd() / '.env',
        Path.home() / '.env', 
        Path(__file__).parent.parent.parent / '.env',
    ]
    
    return [str(path) for path in search_paths]


def create_example_env_file(target_path: Optional[str] = None) -> str:
    """
    Create an example .env file at the specified location.
    
    Args:
        target_path: Path where to create the .env file. 
                    If None, creates in current directory.
    
    Returns:
        str: Path to the created .env file
        
    Raises:
        IOError: If the file cannot be created
    """
    if target_path is None:
        target_path = Path.cwd() / '.env'
    else:
        target_path = Path(target_path)
    
    # Read the example file from the package
    example_file = Path(__file__).parent.parent.parent / '.env.example'
    
    if example_file.exists():
        # Copy the example file
        with open(example_file, 'r', encoding='utf-8') as source:
            content = source.read()
        
        with open(target_path, 'w', encoding='utf-8') as target:
            target.write(content)
        
        logger.info(f"Created .env file at: {target_path}")
        return str(target_path)
    else:
        # Create a basic template if no example exists
        template = """# CrowdStrike Falcon Configuration
# Copy this file to .env and update with your actual values

# CrowdStrike Falcon API Credentials (Required)
# Obtain these from your CrowdStrike console under API Clients & Keys
# Using FALCON_ prefix to avoid conflicts with other applications
FALCON_CLIENT_ID=your_client_id_here
FALCON_CLIENT_SECRET=your_client_secret_here

# Optional: CrowdStrike Base URL (defaults to US-1)
# FALCON_BASE_URL=https://api.crowdstrike.com

# Optional: Cloud Storage Configuration
# AWS_ACCESS_KEY_ID=your_aws_access_key
# AWS_SECRET_ACCESS_KEY=your_aws_secret_key
# AWS_DEFAULT_REGION=us-east-1
# S3_BUCKET_NAME=your_bucket_name

# Optional: Logging Configuration
# LOG_LEVEL=INFO
"""
        
        with open(target_path, 'w', encoding='utf-8') as target:
            target.write(template)
        
        logger.info(f"Created template .env file at: {target_path}")
        return str(target_path)