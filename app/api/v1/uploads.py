"""
File upload endpoints using Cloudinary
"""
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.models.property import PropertyAttachment
from app.schemas.property import PropertyAttachmentRead
from app.services.file_storage import file_storage_service
from app.api.v1.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("/property/{property_id}/attachment", response_model=PropertyAttachmentRead)
async def upload_property_attachment(
    property_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Upload a file attachment for a property using Cloudinary.
    
    Args:
        property_id: ID of the property to attach file to
        file: File to upload
        current_user: Currently authenticated user
        db: Database session
        
    Returns:
        PropertyAttachmentRead with Cloudinary URLs
    """
    try:
        # Upload file to Cloudinary
        upload_result = await file_storage_service.save_file(
            file=file, 
            subfolder=f"property_{property_id}"
        )
        
        # Create database record
        attachment = PropertyAttachment(
            property_id=property_id,
            filename=file.filename,
            original_filename=upload_result["original_filename"],
            cloudinary_public_id=upload_result["public_id"],
            cloudinary_url=upload_result["url"],
            cloudinary_secure_url=upload_result["secure_url"],
            file_size=upload_result["file_size"],
            mime_type=upload_result["mime_type"],
            width=upload_result.get("width"),
            height=upload_result.get("height"),
            uploaded_by_id=current_user.id
        )
        
        db.add(attachment)
        await db.commit()
        await db.refresh(attachment)
        
        return attachment
        
    except Exception as e:
        await db.rollback()
        # If database fails, try to clean up Cloudinary upload
        try:
            if 'upload_result' in locals():
                await file_storage_service.delete_file(upload_result["public_id"])
        except:
            pass  # Best effort cleanup
        
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create attachment: {str(e)}"
        )


@router.delete("/attachment/{attachment_id}")
async def delete_property_attachment(
    attachment_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Delete a property attachment from both database and Cloudinary.
    
    Args:
        attachment_id: ID of the attachment to delete
        current_user: Currently authenticated user
        db: Database session
        
    Returns:
        Success message
    """
    # Get attachment from database
    attachment = await db.get(PropertyAttachment, attachment_id)
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")
    
    try:
        # Delete from Cloudinary
        await file_storage_service.delete_file(attachment.cloudinary_public_id)
        
        # Delete from database
        await db.delete(attachment)
        await db.commit()
        
        return {"message": "Attachment deleted successfully"}
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete attachment: {str(e)}"
        )


@router.get("/attachment/{attachment_id}/thumbnail")
async def get_attachment_thumbnail(
    attachment_id: int,
    width: int = 300,
    height: int = 200,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Get thumbnail URL for an attachment.
    
    Args:
        attachment_id: ID of the attachment
        width: Thumbnail width
        height: Thumbnail height
        db: Database session
        
    Returns:
        Thumbnail URL
    """
    attachment = await db.get(PropertyAttachment, attachment_id)
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")
    
    # Generate thumbnail URL
    thumbnail_url = file_storage_service.get_thumbnail_url(
        public_id=attachment.cloudinary_public_id,
        width=width,
        height=height
    )
    
    return {"thumbnail_url": thumbnail_url}


@router.post("/test-upload")
async def test_cloudinary_upload(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Test endpoint for Cloudinary uploads (for development/testing).
    
    Args:
        file: File to upload
        current_user: Currently authenticated user
        
    Returns:
        Upload result with URLs and metadata
    """
    try:
        result = await file_storage_service.save_file(file=file, subfolder="test")
        
        return {
            "message": "File uploaded successfully to Cloudinary!",
            "file_info": {
                "original_filename": result["original_filename"],
                "public_id": result["public_id"],
                "url": result["url"],
                "secure_url": result["secure_url"],
                "file_size": result["file_size"],
                "mime_type": result["mime_type"],
                "width": result.get("width"),
                "height": result.get("height")
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Test upload failed: {str(e)}"
        )