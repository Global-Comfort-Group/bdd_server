"""
File upload endpoints using Alibaba Cloud OSS
"""
from typing import Dict, Any, List
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_async_session
from app.models.property import PropertyAttachment, Property
from app.schemas.property import PropertyAttachmentRead
from app.services.file_storage import file_storage_service
from app.api.v1.auth import get_current_user
from app.models.user import User, UserRole

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("/property/{property_id}/attachment", response_model=PropertyAttachmentRead)
async def upload_property_attachment(
    property_id: int,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """
    Upload a file attachment for a property using Alibaba Cloud OSS.
    Only the property submitter, BDD users, and admins can upload attachments.

    Args:
        property_id: ID of the property to attach file to
        file: File to upload
        current_user: Currently authenticated user
        db: Database session

    Returns:
        PropertyAttachmentRead with OSS URLs
    """
    try:
        # Verify property exists and check permissions
        stmt = select(Property).where(Property.id == property_id)
        result = await db.execute(stmt)
        property_obj = result.scalar_one_or_none()

        if not property_obj:
            raise HTTPException(status_code=404, detail="Property not found")

        # Permission check: Only submitter, BDD users, and admins can upload
        if (current_user.role not in [UserRole.BDD_USER, UserRole.ADMIN] and
            property_obj.submitted_by_id != current_user.id):
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to upload attachments to this property"
            )

        print(f"🔒 Permission granted: {current_user.email} uploading to property {property_id}")

        # Upload file to OSS
        upload_result = await file_storage_service.save_file(
            file=file,
            subfolder=f"property_{property_id}"
        )

        # Create database record
        # Note: Using cloudinary_* field names for backward compatibility
        attachment = PropertyAttachment(
            property_id=property_id,
            filename=file.filename,
            original_filename=upload_result["original_filename"],
            cloudinary_public_id=upload_result["object_key"],  # OSS object key
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

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        # If database fails, try to clean up OSS upload
        try:
            if 'upload_result' in locals():
                await file_storage_service.delete_file(upload_result["object_key"])
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
    Delete a property attachment from both database and OSS.
    Only the property submitter, BDD users, and admins can delete attachments.

    Args:
        attachment_id: ID of the attachment to delete
        current_user: Currently authenticated user
        db: Database session

    Returns:
        Success message
    """
    # Get attachment from database with property relationship
    stmt = (
        select(PropertyAttachment)
        .join(Property, PropertyAttachment.property_id == Property.id)
        .where(PropertyAttachment.id == attachment_id)
    )
    result = await db.execute(stmt)
    attachment = result.scalar_one_or_none()

    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    # Get the property to check permissions
    property_stmt = select(Property).where(Property.id == attachment.property_id)
    property_result = await db.execute(property_stmt)
    property_obj = property_result.scalar_one_or_none()

    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")

    # Permission check: Only submitter, BDD users, and admins can delete
    if (current_user.role not in [UserRole.BDD_USER, UserRole.ADMIN] and
        property_obj.submitted_by_id != current_user.id):
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to delete this attachment"
        )

    print(f"🔒 Permission granted: {current_user.email} deleting attachment {attachment_id}")

    try:
        # Delete from OSS (cloudinary_public_id stores the OSS object key)
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
    Get URL for an attachment.
    Note: OSS doesn't support on-the-fly image transformation.
    Returns the original URL.

    Args:
        attachment_id: ID of the attachment
        width: Requested width (ignored for OSS)
        height: Requested height (ignored for OSS)
        db: Database session

    Returns:
        Attachment URL
    """
    attachment = await db.get(PropertyAttachment, attachment_id)
    if not attachment:
        raise HTTPException(status_code=404, detail="Attachment not found")

    # Return the secure URL (OSS doesn't have built-in image transformation)
    return {"thumbnail_url": attachment.cloudinary_secure_url}


@router.post("/test-upload")
async def test_oss_upload(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """
    Test endpoint for OSS uploads (for development/testing).

    Args:
        file: File to upload
        current_user: Currently authenticated user

    Returns:
        Upload result with URLs and metadata
    """
    try:
        result = await file_storage_service.save_file(file=file, subfolder="test")

        return {
            "message": "File uploaded successfully to OSS!",
            "file_info": {
                "original_filename": result["original_filename"],
                "object_key": result["object_key"],
                "url": result["url"],
                "secure_url": result["secure_url"],
                "file_size": result["file_size"],
                "mime_type": result["mime_type"]
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Test upload failed: {str(e)}"
        )
