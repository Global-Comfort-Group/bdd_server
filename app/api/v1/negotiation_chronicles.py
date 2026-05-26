from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from app.core.database import get_async_session
from app.api.v1.auth import get_current_user, get_current_user_optional
from app.models.user import User
from app.models.negotiation_chronicle import NegotiationChronicleAttachment
from app.models.nego_table import NegoTable
from app.schemas.negotiation_chronicle import (
    NegotiationChronicleAttachment as NegotiationChronicleAttachmentSchema,
    NegotiationChronicleAttachmentCreate,
    FileUploadResponse
)
from app.services.file_parser import parse_negotiation_file
from app.services.file_storage import file_storage_service
from app.services.oss_service import get_oss_service
import os


def _sign_attachment_url(attachment_data: dict) -> dict:
    """Replace file_url with a signed OSS URL so private-bucket downloads work."""
    file_url = attachment_data.get("file_url") or ""
    if not file_url or file_url.startswith("https://docs.google.com") or file_url.startswith("http://docs.google.com"):
        return attachment_data
    try:
        oss = get_oss_service()
        object_key = oss.object_key_from_url(file_url)
        if object_key:
            attachment_data = dict(attachment_data)
            attachment_data["file_url"] = oss.generate_signed_url(object_key, expires=3600)
    except Exception:
        pass
    return attachment_data

router = APIRouter()

@router.post("/upload/{nego_table_id}", response_model=FileUploadResponse)
async def upload_negotiation_chronicle(
    nego_table_id: int,
    file: Optional[UploadFile] = File(None),
    google_sheets_link: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_async_session),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Upload and parse a negotiation chronicle file (CSV, Excel) OR provide a Google Sheets link
    
    You can either:
    - Upload a file (CSV/Excel)
    - Provide a Google Sheets link
    """
    
    # Validate that at least one option is provided
    if not file and not google_sheets_link:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either a file or a Google Sheets link must be provided"
        )
    
    print(f"📤 Upload request for nego table {nego_table_id}")
    print(f"  - File: {file.filename if file else 'None'}")
    print(f"  - Google Sheets: {google_sheets_link if google_sheets_link else 'None'}")
    print(f"  - User: {current_user.email if current_user else 'Anonymous'}")
    
    # No need to verify nego table exists - we're just attaching reference data
    # The file contains the negotiation data to be displayed
    
    try:
        parsed_data = None
        file_url = None
        filename = None
        file_type = None
        file_size = 0
        
        # Option 1: File upload
        if file:
            # Parse the file
            parsed_data = await parse_negotiation_file(file)
            
            if not parsed_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="File is empty or has invalid format"
                )
            
            # Reset file pointer for upload
            await file.seek(0)
            
            # Upload file to storage (OSS)
            upload_result = await file_storage_service.save_file(file, subfolder="negotiation_chronicles")
            file_url = upload_result["secure_url"]
            filename = file.filename
            file_type = file.filename.split('.')[-1].lower()
            file_size = file.size
        
        # Option 2: Google Sheets link
        elif google_sheets_link:
            file_url = google_sheets_link
            filename = "Google Sheets Link"
            file_type = "google_sheets"
            file_size = 0
            parsed_data = []  # Empty for now, can be fetched via Google Sheets API later
            
            print(f"📊 Google Sheets link provided: {google_sheets_link}")
        
        # Check if we should save to database or just return parsed data
        # If nego table is in memory (simple API), don't save attachment to DB
        from app.api.v1.nego_tables_simple import CREATED_NEGO_TABLES, NEGO_TABLE_ATTACHMENTS
        from datetime import datetime
        
        if nego_table_id in CREATED_NEGO_TABLES:
            # In-memory nego table - store parsed data in memory
            print(f"📊 Storing parsed data in memory for nego table {nego_table_id}")
            
            # Store attachment in memory
            if nego_table_id not in NEGO_TABLE_ATTACHMENTS:
                NEGO_TABLE_ATTACHMENTS[nego_table_id] = []
            
            attachment_data = {
                "id": len(NEGO_TABLE_ATTACHMENTS[nego_table_id]) + 1,
                "nego_table_id": nego_table_id,
                "filename": filename,
                "file_url": file_url,
                "file_type": file_type,
                "file_size": file_size,
                "parsed_data": parsed_data,
                "uploaded_by": current_user.id if current_user else None,
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "upload_date": datetime.now().isoformat()
            }
            
            NEGO_TABLE_ATTACHMENTS[nego_table_id].append(attachment_data)
            print(f"✅ Stored attachment {attachment_data['id']} in memory")
            
            return FileUploadResponse(
                success=True,
                message="File uploaded and parsed successfully (in-memory)",
                attachment_id=attachment_data['id'],
                parsed_data=parsed_data
            )
        else:
            # Database nego table - save attachment record
            print(f"💾 Saving attachment to database for nego table {nego_table_id}")
            attachment = NegotiationChronicleAttachment(
                nego_table_id=nego_table_id,
                filename=filename,
                file_url=file_url,
                file_type=file_type,
                file_size=file_size,
                parsed_data=parsed_data,
                uploaded_by=current_user.id if current_user else None
            )
            
            db.add(attachment)
            await db.commit()
            await db.refresh(attachment)
            
            return FileUploadResponse(
                success=True,
                message="File uploaded and parsed successfully",
                attachment_id=attachment.id,
                parsed_data=parsed_data
            )
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing file: {str(e)}"
        )

@router.get("/{nego_table_id}/attachments", response_model=List[NegotiationChronicleAttachmentSchema])
async def get_negotiation_chronicle_attachments(
    nego_table_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)  # REQUIRED - sensitive data!
):
    """
    Get all negotiation chronicle attachments for a nego table (requires authentication)
    """
    print(f"📥 GET attachments request for nego table {nego_table_id}")
    print(f"  - User: {current_user.email}")
    
    # Check if nego table exists in memory storage (from nego_tables_simple.py)
    from app.api.v1.nego_tables_simple import CREATED_NEGO_TABLES, NEGO_TABLE_ATTACHMENTS
    
    if nego_table_id in CREATED_NEGO_TABLES:
        print(f"✅ Found nego table {nego_table_id} in memory storage")
        attachments = NEGO_TABLE_ATTACHMENTS.get(nego_table_id, [])
        print(f"📊 Found {len(attachments)} attachments in memory")
        return [_sign_attachment_url(a) for a in attachments]
    
    # Try database (for production-created nego tables)
    result = await db.execute(select(NegoTable).filter(NegoTable.id == nego_table_id))
    nego_table = result.scalar_one_or_none()
    
    if not nego_table:
        print(f"❌ Nego table {nego_table_id} not found in memory or database")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Negotiation table {nego_table_id} not found"
        )
    
    print(f"✅ Found nego table {nego_table_id} in database")
    result = await db.execute(
        select(NegotiationChronicleAttachment)
        .filter(NegotiationChronicleAttachment.nego_table_id == nego_table_id)
        .order_by(NegotiationChronicleAttachment.created_at.desc())
    )
    attachments = result.scalars().all()

    print(f"📊 Found {len(attachments)} attachments")
    serialized = [
        _sign_attachment_url(NegotiationChronicleAttachmentSchema.model_validate(a).model_dump())
        for a in attachments
    ]
    return serialized

@router.delete("/{attachment_id}")
async def delete_negotiation_chronicle_attachment(
    attachment_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a negotiation chronicle attachment
    """
    result = await db.execute(
        select(NegotiationChronicleAttachment)
        .filter(NegotiationChronicleAttachment.id == attachment_id)
    )
    attachment = result.scalar_one_or_none()
    
    if not attachment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attachment not found"
        )
    
    # Check if user has permission (BDD_USER, ADMIN, or original uploader)
    if current_user.role.value not in ["BDD_USER", "ADMIN"] and attachment.uploaded_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this attachment"
        )
    
    await db.delete(attachment)
    await db.commit()
    
    return {"success": True, "message": "Attachment deleted successfully"}

