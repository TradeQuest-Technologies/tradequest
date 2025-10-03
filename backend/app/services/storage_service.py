"""
Storage service for handling file uploads and storage
Supports both local filesystem and AWS S3
"""

import os
import boto3
from pathlib import Path
from typing import Optional, BinaryIO, Union
from botocore.exceptions import ClientError, NoCredentialsError
import structlog
from app.core.config import settings

logger = structlog.get_logger()


class StorageService:
    """Unified storage service for local and S3 storage"""
    
    def __init__(self):
        self.use_s3 = settings.USE_S3_STORAGE
        self.s3_bucket = settings.S3_BUCKET_NAME
        
        if self.use_s3:
            self._init_s3_client()
        else:
            self._init_local_storage()
    
    def _init_s3_client(self):
        """Initialize S3 client"""
        try:
            if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
                # Use explicit credentials
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.AWS_REGION
                )
            else:
                # Use IAM role or environment credentials
                self.s3_client = boto3.client('s3', region_name=settings.AWS_REGION)
            
            # Test connection
            self.s3_client.head_bucket(Bucket=self.s3_bucket)
            logger.info(f"S3 storage initialized with bucket: {self.s3_bucket}")
            
        except NoCredentialsError:
            logger.error("AWS credentials not found")
            raise
        except ClientError as e:
            logger.error(f"Failed to connect to S3 bucket {self.s3_bucket}: {e}")
            raise
        except Exception as e:
            logger.error(f"S3 initialization failed: {e}")
            raise
    
    def _init_local_storage(self):
        """Initialize local storage directories"""
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.coach_dir = Path("data/coach_workspaces")
        
        # Create directories if they don't exist
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.coach_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Local storage initialized with directories: {self.upload_dir}, {self.coach_dir}")
    
    def upload_file(
        self, 
        file_obj: BinaryIO, 
        file_path: str, 
        content_type: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> str:
        """
        Upload a file to storage
        
        Args:
            file_obj: File object to upload
            file_path: Path where file should be stored
            content_type: MIME type of the file
            metadata: Additional metadata for S3
            
        Returns:
            URL or path to the uploaded file
        """
        if self.use_s3:
            return self._upload_to_s3(file_obj, file_path, content_type, metadata)
        else:
            return self._upload_to_local(file_obj, file_path)
    
    def _upload_to_s3(
        self, 
        file_obj: BinaryIO, 
        file_path: str, 
        content_type: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> str:
        """Upload file to S3"""
        try:
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type
            if metadata:
                extra_args['Metadata'] = metadata
            
            self.s3_client.upload_fileobj(
                file_obj,
                self.s3_bucket,
                file_path,
                ExtraArgs=extra_args
            )
            
            # Return S3 URL
            url = f"https://{self.s3_bucket}.s3.{settings.AWS_REGION}.amazonaws.com/{file_path}"
            logger.info(f"File uploaded to S3: {file_path}")
            return url
            
        except ClientError as e:
            logger.error(f"Failed to upload file to S3: {e}")
            raise
    
    def _upload_to_local(self, file_obj: BinaryIO, file_path: str) -> str:
        """Upload file to local storage"""
        try:
            full_path = self.upload_dir / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(full_path, 'wb') as f:
                f.write(file_obj.read())
            
            logger.info(f"File uploaded locally: {full_path}")
            return str(full_path.relative_to(Path.cwd()))
            
        except Exception as e:
            logger.error(f"Failed to upload file locally: {e}")
            raise
    
    def download_file(self, file_path: str) -> bytes:
        """
        Download a file from storage
        
        Args:
            file_path: Path to the file
            
        Returns:
            File contents as bytes
        """
        if self.use_s3:
            return self._download_from_s3(file_path)
        else:
            return self._download_from_local(file_path)
    
    def _download_from_s3(self, file_path: str) -> bytes:
        """Download file from S3"""
        try:
            response = self.s3_client.get_object(Bucket=self.s3_bucket, Key=file_path)
            return response['Body'].read()
            
        except ClientError as e:
            logger.error(f"Failed to download file from S3: {e}")
            raise
    
    def _download_from_local(self, file_path: str) -> bytes:
        """Download file from local storage"""
        try:
            full_path = self.upload_dir / file_path
            with open(full_path, 'rb') as f:
                return f.read()
                
        except Exception as e:
            logger.error(f"Failed to download file locally: {e}")
            raise
    
    def delete_file(self, file_path: str) -> bool:
        """
        Delete a file from storage
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if successful, False otherwise
        """
        if self.use_s3:
            return self._delete_from_s3(file_path)
        else:
            return self._delete_from_local(file_path)
    
    def _delete_from_s3(self, file_path: str) -> bool:
        """Delete file from S3"""
        try:
            self.s3_client.delete_object(Bucket=self.s3_bucket, Key=file_path)
            logger.info(f"File deleted from S3: {file_path}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to delete file from S3: {e}")
            return False
    
    def _delete_from_local(self, file_path: str) -> bool:
        """Delete file from local storage"""
        try:
            full_path = self.upload_dir / file_path
            if full_path.exists():
                full_path.unlink()
                logger.info(f"File deleted locally: {full_path}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Failed to delete file locally: {e}")
            return False
    
    def file_exists(self, file_path: str) -> bool:
        """
        Check if a file exists in storage
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file exists, False otherwise
        """
        if self.use_s3:
            return self._exists_in_s3(file_path)
        else:
            return self._exists_locally(file_path)
    
    def _exists_in_s3(self, file_path: str) -> bool:
        """Check if file exists in S3"""
        try:
            self.s3_client.head_object(Bucket=self.s3_bucket, Key=file_path)
            return True
        except ClientError:
            return False
    
    def _exists_locally(self, file_path: str) -> bool:
        """Check if file exists locally"""
        full_path = self.upload_dir / file_path
        return full_path.exists()
    
    def get_file_url(self, file_path: str, expires_in: int = 3600) -> str:
        """
        Get a URL to access a file
        
        Args:
            file_path: Path to the file
            expires_in: Expiration time in seconds (for S3 presigned URLs)
            
        Returns:
            URL to access the file
        """
        if self.use_s3:
            return self._get_s3_presigned_url(file_path, expires_in)
        else:
            return f"/uploads/{file_path}"
    
    def _get_s3_presigned_url(self, file_path: str, expires_in: int = 3600) -> str:
        """Generate presigned URL for S3 object"""
        try:
            url = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.s3_bucket, 'Key': file_path},
                ExpiresIn=expires_in
            )
            return url
            
        except ClientError as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise
    
    def create_coach_workspace(self, user_id: str, session_id: str) -> str:
        """
        Create a workspace directory for AI coach sessions
        
        Args:
            user_id: User ID
            session_id: Session ID
            
        Returns:
            Path to the workspace
        """
        workspace_path = f"coach_workspaces/{user_id}/{session_id}"
        
        if self.use_s3:
            # For S3, just return the path (no need to create directory)
            return workspace_path
        else:
            # For local storage, create the directory
            full_path = self.coach_dir / user_id / session_id
            full_path.mkdir(parents=True, exist_ok=True)
            return str(full_path.relative_to(Path.cwd()))


# Global storage service instance
storage_service = StorageService()
