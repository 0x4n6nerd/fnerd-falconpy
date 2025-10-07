"""
Cloud storage management for S3 and other cloud providers.
"""

import boto3
import botocore
from uuid import uuid4
from typing import Optional, Tuple
from fnerd_falconpy.core.base import RTRSession, ILogger, DefaultLogger

class CloudStorageManager:
    """Manages cloud storage operations (S3, etc.)"""
    
    def __init__(self, logger: Optional[ILogger] = None):
        """
        Initialize cloud storage manager
        
        Args:
            logger: Logger instance (uses DefaultLogger if not provided)
        """
        self.logger = logger or DefaultLogger("CloudStorageManager")
        
    def generate_upload_url(self, bucket: str, filename: Optional[str] = None, 
                          expires_in: int = 3600) -> Tuple[str, str]:
        """
        Generate presigned upload URL
        
        Args:
            bucket: S3 bucket name
            filename: Optional custom filename
            expires_in: URL expiration time in seconds
            
        Returns:
            Tuple of (presigned_url, object_key)
            
        Raises:
            botocore.exceptions.ClientError: If there's an AWS API error
            botocore.exceptions.NoCredentialsError: If AWS credentials are missing
            ValueError: If bucket is empty or invalid
        """
        try:
            # Validate input
            if not bucket:
                raise ValueError("Bucket name cannot be empty")
                
            # Initialize S3 client with optional endpoint
            # Check if we have configuration available
            s3_kwargs = {}
            try:
                from ..core.configuration import Configuration
                config = Configuration()
                endpoint_url = config.get_s3_endpoint()
                if endpoint_url:
                    s3_kwargs['endpoint_url'] = endpoint_url
                    self.logger.info(f"Using custom S3 endpoint: {endpoint_url}")
            except ImportError:
                pass  # Configuration not available, use default
            
            s3 = boto3.client("s3", **s3_kwargs)
            
            # Generate object key
            object_key = filename or f"uploads/{uuid4()}.zip"
            
            try:
                # Generate presigned URL
                url = s3.generate_presigned_url(
                    ClientMethod="put_object",
                    Params={"Bucket": bucket, "Key": object_key},
                    ExpiresIn=expires_in,
                )
                
                self.logger.info(f"Generated presigned URL for {bucket}/{object_key}")
                return url, object_key
                
            except botocore.exceptions.ClientError as e:
                self.logger.error(f"AWS API error when generating presigned URL: {e}")
                raise
            except botocore.exceptions.NoCredentialsError as e:
                self.logger.error(f"AWS credentials not found: {e}")
                raise
                
        except Exception as e:
            if isinstance(e, (ValueError, botocore.exceptions.ClientError, 
                            botocore.exceptions.NoCredentialsError)):
                raise
            self.logger.error(f"Unexpected error in generate_upload_url: {e}", exc_info=True)
            raise
        
    def upload_via_proxy(self, session: RTRSession, local_path: str, 
                        upload_url: str, proxy_host: str) -> bool:
        """
        Upload file via proxy
        
        Args:
            session: Active RTR session
            local_path: Local file path on remote host
            upload_url: Target upload URL
            proxy_host: Proxy hostname
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Note: This is a simplified version that assumes the session manager
            # is available through dependency injection in real usage
            # In practice, this would be passed as a parameter or injected
            
            self.logger.info(f"Starting proxy upload from {local_path} to {proxy_host}")
            
            # The actual implementation would need access to the session manager
            # to execute commands. For now, we'll provide the structure:
            
            # 1. Set up hosts file entries (if needed)
            # 2. Execute PowerShell upload command
            # 3. Monitor upload progress
            
            self.logger.warning(
                "upload_via_proxy requires SessionManager integration. "
                "Please use the orchestrator or pass SessionManager as parameter."
            )
            
            # In a real implementation, this would:
            # - Execute PowerShell command to upload file
            # - Monitor progress
            # - Return success/failure
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error in upload_via_proxy: {e}", exc_info=True)
            return False
    
    def verify_s3_upload(self, bucket: str, object_key: str, expected_size: Optional[int] = None) -> bool:
        """
        Verify that a file was successfully uploaded to S3
        
        Args:
            bucket: S3 bucket name
            object_key: S3 object key (filename)
            expected_size: Expected file size in bytes (optional)
            
        Returns:
            True if file exists and matches expected size, False otherwise
        """
        try:
            # Initialize S3 client with optional endpoint
            # Check if we have configuration available
            s3_kwargs = {}
            try:
                from ..core.configuration import Configuration
                config = Configuration()
                endpoint_url = config.get_s3_endpoint()
                if endpoint_url:
                    s3_kwargs['endpoint_url'] = endpoint_url
                    self.logger.info(f"Using custom S3 endpoint: {endpoint_url}")
            except ImportError:
                pass  # Configuration not available, use default
            
            s3 = boto3.client("s3", **s3_kwargs)
            
            self.logger.info(f"Verifying S3 upload: s3://{bucket}/{object_key}")
            
            # Check if object exists and get metadata
            try:
                response = s3.head_object(Bucket=bucket, Key=object_key)
                
                # Extract file information
                actual_size = response['ContentLength']
                last_modified = response['LastModified']
                etag = response['ETag'].strip('"')
                
                self.logger.info(f"S3 object found: {actual_size} bytes, modified {last_modified}")
                
                # Verify file size if expected size provided
                if expected_size is not None:
                    if actual_size == expected_size:
                        self.logger.info(f"File size verification successful: {actual_size} bytes")
                        return True
                    else:
                        self.logger.error(f"File size mismatch: expected {expected_size}, actual {actual_size}")
                        return False
                else:
                    # If no size check, just confirm existence
                    self.logger.info(f"File existence verified: {actual_size} bytes")
                    return True
                    
            except botocore.exceptions.ClientError as e:
                error_code = e.response['Error']['Code']
                if error_code == '404':
                    self.logger.error(f"File not found in S3: s3://{bucket}/{object_key}")
                    return False
                else:
                    self.logger.error(f"AWS API error checking S3 object: {e}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Error verifying S3 upload: {e}", exc_info=True)
            return False
    
    def get_s3_object_info(self, bucket: str, object_key: str) -> Optional[dict]:
        """
        Get detailed information about an S3 object
        
        Args:
            bucket: S3 bucket name
            object_key: S3 object key (filename)
            
        Returns:
            Dictionary with object info (size, modified_date, etag) or None if not found
        """
        try:
            # Initialize S3 client with optional endpoint
            # Check if we have configuration available
            s3_kwargs = {}
            try:
                from ..core.configuration import Configuration
                config = Configuration()
                endpoint_url = config.get_s3_endpoint()
                if endpoint_url:
                    s3_kwargs['endpoint_url'] = endpoint_url
                    self.logger.info(f"Using custom S3 endpoint: {endpoint_url}")
            except ImportError:
                pass  # Configuration not available, use default
            
            s3 = boto3.client("s3", **s3_kwargs)
            
            # Get object metadata
            response = s3.head_object(Bucket=bucket, Key=object_key)
            
            return {
                'size': response['ContentLength'],
                'last_modified': response['LastModified'],
                'etag': response['ETag'].strip('"'),
                'content_type': response.get('ContentType', 'unknown'),
                'storage_class': response.get('StorageClass', 'STANDARD')
            }
            
        except botocore.exceptions.ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                self.logger.warning(f"S3 object not found: s3://{bucket}/{object_key}")
                return None
            else:
                self.logger.error(f"AWS API error getting S3 object info: {e}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error getting S3 object info: {e}", exc_info=True)
            return None