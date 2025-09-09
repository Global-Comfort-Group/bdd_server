"""
Cloudinary integration service for file uploads and management
"""
import os
import cloudinary
import cloudinary.uploader
import cloudinary.api
from typing import Dict, Any, Optional, List
from fastapi import HTTPException, UploadFile
# # import magic  # For MIME type detection - disabled to avoid libmagic dependency - removed to avoid libmagic dependency

from app.core.config import settings


class CloudinaryService:
    """Service for handling Cloudinary file uploads and management"""
    
    def __init__(self):
        """Initialize Cloudinary configuration"""
        cloudinary.config(
            cloud_name=settings.CLOUDINARY_CLOUD_NAME,
            api_key=settings.CLOUDINARY_API_KEY,
            api_secret=settings.CLOUDINARY_API_SECRET,
            secure=True
        )
    
    async def upload_file(
        self, 
        file: UploadFile, 
        subfolder: str = "properties",
        public_id: Optional[str] = None,
        transformation: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Upload file to Cloudinary
        
        Args:
            file: FastAPI UploadFile object
            subfolder: Cloudinary subfolder within main BDD_CLOUDINARY folder
            public_id: Custom public ID (optional)
            transformation: Image transformation parameters
            
        Returns:
            Dict with Cloudinary upload result
        """
        try:
            # Validate file size (10MB limit)
            if file.size and file.size > settings.MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=413,
                    detail=f"File too large. Maximum size is {settings.MAX_FILE_SIZE} bytes"
                )
            
            # Read file content
            file_content = await file.read()
            
            # Use content type from upload file (FastAPI handles MIME detection)
            mime_type = file.content_type or "application/octet-stream"
            
            # Build full folder path with main BDD folder
            full_folder = f"{settings.CLOUDINARY_FOLDER}/{subfolder}"
            
            # Prepare upload parameters
            upload_params = {
                "folder": full_folder,
                "resource_type": "auto",  # Auto-detect file type
                "use_filename": True,
                "unique_filename": True,
                "overwrite": False,
            }
            
            if public_id:
                upload_params["public_id"] = f"{full_folder}/{public_id}"
            
            if transformation:
                upload_params["transformation"] = transformation
            
            # Upload to Cloudinary
            result = cloudinary.uploader.upload(file_content, **upload_params)
            
            # Reset file position for potential reuse
            await file.seek(0)
            
            return {
                "public_id": result["public_id"],
                "url": result["url"],
                "secure_url": result["secure_url"],
                "width": result.get("width"),
                "height": result.get("height"),
                "file_size": result["bytes"],
                "mime_type": mime_type,
                "original_filename": file.filename,
                "cloudinary_result": result  # Full result for debugging
            }
            
        except cloudinary.exceptions.Error as e:
            raise HTTPException(
                status_code=400,
                detail=f"Cloudinary upload failed: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"File upload failed: {str(e)}"
            )
    
    def delete_file(self, public_id: str) -> Dict[str, Any]:
        """
        Delete file from Cloudinary
        
        Args:
            public_id: Cloudinary public ID
            
        Returns:
            Deletion result
        """
        try:
            result = cloudinary.uploader.destroy(public_id)
            return result
        except cloudinary.exceptions.Error as e:
            raise HTTPException(
                status_code=400,
                detail=f"Cloudinary deletion failed: {str(e)}"
            )
    
    def get_file_info(self, public_id: str) -> Dict[str, Any]:
        """
        Get file information from Cloudinary
        
        Args:
            public_id: Cloudinary public ID
            
        Returns:
            File information
        """
        try:
            result = cloudinary.api.resource(public_id)
            return result
        except cloudinary.exceptions.Error as e:
            raise HTTPException(
                status_code=404,
                detail=f"File not found: {str(e)}"
            )
    
    def generate_url(
        self, 
        public_id: str, 
        transformation: Optional[Dict[str, Any]] = None,
        secure: bool = True
    ) -> str:
        """
        Generate URL for a Cloudinary resource
        
        Args:
            public_id: Cloudinary public ID
            transformation: Image transformation parameters
            secure: Use HTTPS URL
            
        Returns:
            Generated URL
        """
        try:
            if transformation:
                url = cloudinary.CloudinaryImage(public_id).build_url(
                    transformation=transformation,
                    secure=secure
                )
            else:
                url = cloudinary.CloudinaryImage(public_id).build_url(secure=secure)
            
            return url
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"URL generation failed: {str(e)}"
            )
    
    def list_files(self, subfolder: str = "properties", max_results: int = 100) -> List[Dict[str, Any]]:
        """
        List files in a Cloudinary folder
        
        Args:
            subfolder: Cloudinary subfolder within main BDD_CLOUDINARY folder
            max_results: Maximum number of results
            
        Returns:
            List of file information
        """
        try:
            full_folder = f"{settings.CLOUDINARY_FOLDER}/{subfolder}"
            result = cloudinary.api.resources(
                type="upload",
                prefix=full_folder,
                max_results=max_results
            )
            return result.get("resources", [])
        except cloudinary.exceptions.Error as e:
            raise HTTPException(
                status_code=400,
                detail=f"Cloudinary listing failed: {str(e)}"
            )


# Global instance
cloudinary_service = CloudinaryService()