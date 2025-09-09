"""
File storage service using Cloudinary for BDD Property Tracker
"""
import uuid
from typing import Dict, Any, Optional
from pathlib import Path
from fastapi import UploadFile, HTTPException

from app.core.config import settings
from app.services.cloudinary_service import cloudinary_service


class FileStorageService:
    """Service for handling file uploads using Cloudinary."""
    
    def __init__(self):
        self.max_file_size = settings.MAX_FILE_SIZE
        self.allowed_types = {
            'image/jpeg', 'image/png', 'image/gif', 'image/webp',
            'application/pdf', 'application/msword',
            'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'application/vnd.ms-excel',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'text/plain', 'text/csv'
        }

    async def save_file(self, file: UploadFile, subfolder: str = "properties") -> Dict[str, Any]:
        """
        Save uploaded file to Cloudinary.
        
        Args:
            file: The uploaded file
            subfolder: Subfolder to organize files in Cloudinary
            
        Returns:
            Dict with file information including Cloudinary URLs and metadata
        """
        # Validate file size
        if file.size and file.size > self.max_file_size:
            raise HTTPException(
                status_code=413,
                detail=f"File size exceeds maximum allowed size of {self.max_file_size} bytes"
            )

        # Validate file type
        if not self.validate_file_type(file):
            raise HTTPException(
                status_code=422,
                detail=f"File type {file.content_type} is not allowed"
            )

        # Generate unique public ID for Cloudinary
        file_extension = self._get_file_extension(file.filename)
        unique_id = f"{uuid.uuid4()}"
        
        # Optional: Add image transformations for different file types
        transformation = None
        if file.content_type and file.content_type.startswith('image/'):
            transformation = {
                "quality": "auto",
                "fetch_format": "auto"
            }
        
        try:
            # Upload to Cloudinary
            result = await cloudinary_service.upload_file(
                file=file,
                subfolder=subfolder,
                public_id=unique_id,
                transformation=transformation
            )
            
            return result
            
        except HTTPException:
            # Re-raise HTTPException from cloudinary_service
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload file: {str(e)}"
            )

    async def delete_file(self, public_id: str) -> bool:
        """
        Delete a file from Cloudinary.
        
        Args:
            public_id: Cloudinary public ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = cloudinary_service.delete_file(public_id)
            return result.get("result") == "ok"
        except HTTPException:
            return False
        except Exception:
            return False

    def get_file_url(self, public_id: str, transformation: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate URL for accessing a file from Cloudinary.
        
        Args:
            public_id: Cloudinary public ID
            transformation: Optional transformation parameters
            
        Returns:
            Generated URL
        """
        try:
            return cloudinary_service.generate_url(
                public_id=public_id,
                transformation=transformation,
                secure=True
            )
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to generate URL: {str(e)}"
            )

    def get_thumbnail_url(self, public_id: str, width: int = 300, height: int = 200) -> str:
        """
        Generate thumbnail URL for images.
        
        Args:
            public_id: Cloudinary public ID
            width: Thumbnail width
            height: Thumbnail height
            
        Returns:
            Thumbnail URL
        """
        transformation = {
            "width": width,
            "height": height,
            "crop": "fill",
            "quality": "auto",
            "fetch_format": "auto"
        }
        
        return self.get_file_url(public_id, transformation)

    def _get_file_extension(self, filename: str) -> str:
        """Extract file extension from filename."""
        if not filename:
            return ""
        return Path(filename).suffix.lower()

    def validate_file_type(self, file: UploadFile) -> bool:
        """Validate if file type is allowed."""
        return file.content_type in self.allowed_types

    def get_file_info(self, public_id: str) -> Dict[str, Any]:
        """
        Get file information from Cloudinary.
        
        Args:
            public_id: Cloudinary public ID
            
        Returns:
            File information
        """
        try:
            return cloudinary_service.get_file_info(public_id)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to get file info: {str(e)}"
            )


# Global instance
file_storage_service = FileStorageService()