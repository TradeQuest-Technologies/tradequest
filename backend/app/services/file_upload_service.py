"""
File upload service for handling chart images and other attachments
"""

import os
import uuid
import aiofiles
from typing import Optional
from fastapi import UploadFile, HTTPException
from pathlib import Path
import structlog

logger = structlog.get_logger()

class FileUploadService:
    """Service for handling file uploads"""
    
    def __init__(self):
        self.upload_dir = Path("uploads")
        self.chart_dir = self.upload_dir / "charts"
        self.attachments_dir = self.upload_dir / "attachments"
        
        # Create directories if they don't exist
        self.chart_dir.mkdir(parents=True, exist_ok=True)
        self.attachments_dir.mkdir(parents=True, exist_ok=True)
    
    async def upload_chart_image(self, file: UploadFile, user_id: str) -> str:
        """Upload a chart image and return the file path"""
        
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=400,
                detail="Only image files are allowed for chart uploads"
            )
        
        # Validate file size (max 10MB)
        content = await file.read()
        if len(content) > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(
                status_code=400,
                detail="File size must be less than 10MB"
            )
        
        # Generate unique filename
        file_extension = Path(file.filename).suffix if file.filename else '.png'
        unique_filename = f"{user_id}_{uuid.uuid4()}{file_extension}"
        file_path = self.chart_dir / unique_filename
        
        # Save file
        try:
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)
            
            logger.info("Chart image uploaded", user_id=user_id, filename=unique_filename)
            
            # Return relative path for database storage
            return f"uploads/charts/{unique_filename}"
            
        except Exception as e:
            logger.error("Failed to upload chart image", error=str(e), user_id=user_id)
            raise HTTPException(
                status_code=500,
                detail="Failed to upload chart image"
            )
    
    async def upload_attachment(self, file: UploadFile, user_id: str) -> dict:
        """Upload an attachment and return file info"""
        
        # Validate file size (max 25MB)
        content = await file.read()
        if len(content) > 25 * 1024 * 1024:  # 25MB
            raise HTTPException(
                status_code=400,
                detail="File size must be less than 25MB"
            )
        
        # Generate unique filename
        original_filename = file.filename or "attachment"
        file_extension = Path(original_filename).suffix
        unique_filename = f"{user_id}_{uuid.uuid4()}{file_extension}"
        file_path = self.attachments_dir / unique_filename
        
        # Save file
        try:
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(content)
            
            logger.info("Attachment uploaded", user_id=user_id, filename=unique_filename)
            
            return {
                "name": original_filename,
                "url": f"uploads/attachments/{unique_filename}",
                "size": len(content),
                "type": file.content_type or "application/octet-stream"
            }
            
        except Exception as e:
            logger.error("Failed to upload attachment", error=str(e), user_id=user_id)
            raise HTTPException(
                status_code=500,
                detail="Failed to upload attachment"
            )
    
    def delete_file(self, file_path: str) -> bool:
        """Delete a file from the filesystem"""
        try:
            full_path = Path(file_path)
            if full_path.exists():
                full_path.unlink()
                logger.info("File deleted", file_path=file_path)
                return True
            return False
        except Exception as e:
            logger.error("Failed to delete file", error=str(e), file_path=file_path)
            return False
