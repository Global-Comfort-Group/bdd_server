from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.models.user import User
from app.models.workflow import PropertyStatus
from app.schemas.property import (
    PropertyCreate, PropertyRead, PropertyUpdate, PropertyListRead,
    PropertyAttachmentRead, PropertyType
)
from app.schemas.workflow import StatusUpdateRequest
from app.services.property import PropertyService
from app.services.workflow import WorkflowService
from app.services.file_storage import FileStorageService
from app.api.v1.auth import current_active_user

router = APIRouter(prefix="/properties", tags=["properties"])


@router.get("/", response_model=List[PropertyListRead])
async def list_properties(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[PropertyStatus] = None,
    property_type: Optional[PropertyType] = None,
    submitted_by_id: Optional[int] = None,
    reviewer_id: Optional[int] = None,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
):
    """Get list of properties with optional filtering."""
    service = PropertyService(db)
    
    # Non-BDD users can only see their own properties unless they're brokers
    if current_user.role.value not in ["BDD_USER"]:
        if submitted_by_id is None:
            submitted_by_id = current_user.id
        elif submitted_by_id != current_user.id and current_user.role.value != "BROKER":
            raise HTTPException(status_code=403, detail="Not authorized to view other users' properties")
    
    properties = await service.get_properties(
        skip=skip,
        limit=limit,
        status=status,
        submitted_by_id=submitted_by_id,
        reviewer_id=reviewer_id,
        property_type=property_type.value if property_type else None,
    )
    
    return properties


@router.post("/", response_model=PropertyRead)
async def create_property(
    property_data: PropertyCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
):
    """Create a new property."""
    service = PropertyService(db)
    
    # Check if title number already exists
    existing = await service.get_property_by_title_number(property_data.title_number)
    if existing:
        raise HTTPException(
            status_code=400, 
            detail="Property with this title number already exists"
        )
    
    return await service.create_property(property_data, current_user.id)


@router.get("/{property_id}", response_model=PropertyRead)
async def get_property(
    property_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
):
    """Get a specific property by ID."""
    service = PropertyService(db)
    property_obj = await service.get_property(property_id)
    
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Check permissions
    if (current_user.role.value not in ["BDD_USER"] and 
        property_obj.submitted_by_id != current_user.id and
        property_obj.reviewer_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to view this property")
    
    return property_obj


@router.patch("/{property_id}", response_model=PropertyRead)
async def update_property(
    property_id: int,
    property_data: PropertyUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
):
    """Update a property."""
    service = PropertyService(db)
    property_obj = await service.get_property(property_id)
    
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Check permissions - only owner, reviewer, or BDD user can update
    if (current_user.role.value not in ["BDD_USER"] and
        property_obj.submitted_by_id != current_user.id and
        property_obj.reviewer_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to update this property")
    
    # Check if title number change conflicts with existing property
    if (property_data.title_number and 
        property_data.title_number != property_obj.title_number):
        existing = await service.get_property_by_title_number(property_data.title_number)
        if existing:
            raise HTTPException(
                status_code=400, 
                detail="Property with this title number already exists"
            )
    
    updated_property = await service.update_property(property_id, property_data)
    return updated_property


@router.delete("/{property_id}")
async def delete_property(
    property_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
):
    """Delete a property."""
    service = PropertyService(db)
    property_obj = await service.get_property(property_id)
    
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Only BDD users or property owner can delete
    if (current_user.role.value not in ["BDD_USER"] and
        property_obj.submitted_by_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to delete this property")
    
    success = await service.delete_property(property_id)
    if success:
        return {"message": "Property deleted successfully"}
    else:
        raise HTTPException(status_code=400, detail="Failed to delete property")


@router.patch("/{property_id}/status", response_model=PropertyRead)
async def update_property_status(
    property_id: int,
    request: StatusUpdateRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
):
    """Update property workflow status."""
    # Check if property exists and user has permission
    property_service = PropertyService(db)
    property_obj = await property_service.get_property(property_id)
    
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Status updates can be done by BDD users, brokers, or property owner
    if (current_user.role.value not in ["BDD_USER", "BROKER"] and
        property_obj.submitted_by_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to update property status")
    
    # Use workflow service to handle status transition
    workflow_service = WorkflowService(db)
    
    try:
        updated_property = await workflow_service.transition_status(
            property_id, request, current_user.id
        )
        return updated_property
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{property_id}/history")
async def get_property_history(
    property_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
):
    """Get property workflow history."""
    # Check if property exists and user has permission
    property_service = PropertyService(db)
    property_obj = await property_service.get_property(property_id)
    
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Check permissions
    if (current_user.role.value not in ["BDD_USER"] and
        property_obj.submitted_by_id != current_user.id and
        property_obj.reviewer_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to view property history")
    
    workflow_service = WorkflowService(db)
    history = await workflow_service.get_property_history(property_id)
    
    return history


@router.post("/{property_id}/attachments", response_model=PropertyAttachmentRead)
async def upload_property_attachment(
    property_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
):
    """Upload an attachment for a property."""
    # Check if property exists and user has permission
    property_service = PropertyService(db)
    property_obj = await property_service.get_property(property_id)
    
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Check permissions
    if (current_user.role.value not in ["BDD_USER"] and
        property_obj.submitted_by_id != current_user.id and
        property_obj.reviewer_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to upload attachments")
    
    # Upload file
    file_service = FileStorageService()
    
    if not file_service.validate_file_type(file):
        raise HTTPException(status_code=422, detail="File type not allowed")
    
    try:
        filename, file_path = await file_service.save_file(file, f"properties/{property_id}")
        
        # Save attachment record
        attachment = await property_service.add_attachment(
            property_id=property_id,
            filename=filename,
            original_filename=file.filename,
            file_path=file_path,
            file_size=file.size or 0,
            mime_type=file.content_type or "application/octet-stream",
            uploaded_by_id=current_user.id,
        )
        
        return attachment
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to upload file: {str(e)}")


@router.get("/{property_id}/attachments", response_model=List[PropertyAttachmentRead])
async def list_property_attachments(
    property_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
):
    """Get list of property attachments."""
    # Check if property exists and user has permission
    property_service = PropertyService(db)
    property_obj = await property_service.get_property(property_id)
    
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Check permissions
    if (current_user.role.value not in ["BDD_USER"] and
        property_obj.submitted_by_id != current_user.id and
        property_obj.reviewer_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to view attachments")
    
    attachments = await property_service.get_property_attachments(property_id)
    return attachments


@router.patch("/{property_id}/assign-reviewer", response_model=PropertyRead)
async def assign_reviewer(
    property_id: int,
    reviewer_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
):
    """Assign a reviewer to a property (BDD users only)."""
    if current_user.role.value not in ["BDD_USER"]:
        raise HTTPException(status_code=403, detail="Not authorized to assign reviewers")
    
    service = PropertyService(db)
    property_obj = await service.assign_reviewer(property_id, reviewer_id)
    
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property or reviewer not found")
    
    return property_obj