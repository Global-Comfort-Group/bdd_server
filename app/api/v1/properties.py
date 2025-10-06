from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.encoders import jsonable_encoder
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.models.user import User
from app.models.workflow import PropertyStatus
from app.schemas.property import (
    PropertyCreate, PropertyRead, PropertyUpdate, PropertyListRead,
    PropertyAttachmentRead, PropertyType
)
from app.schemas.user import UserPublic
from app.models.enums import TransactionStatus
from app.schemas.workflow import StatusUpdateRequest
from app.services.property import PropertyService
from app.services.workflow import WorkflowService
from app.services.file_storage import FileStorageService
from app.api.v1.auth import get_current_user

router = APIRouter(prefix="/properties", tags=["properties"])

# Optional authentication dependency - returns None if not authenticated
async def get_current_user_optional() -> Optional[User]:
    """Get current user if authenticated, otherwise return None"""
    try:
        return await get_current_user()
    except:
        return None


@router.get("/")
async def list_properties(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status: Optional[PropertyStatus] = None,
    property_type: Optional[PropertyType] = None,
    transaction_status: Optional[TransactionStatus] = None,
    submitted_by_id: Optional[int] = None,
    reviewer_id: Optional[int] = None,
    db: AsyncSession = Depends(get_async_session),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Get list of properties with optional filtering."""
    service = PropertyService(db)
    
    # Non-BDD users can only see their own properties unless they're brokers or admins
    # If no authentication, allow viewing all properties (for development)
    if current_user and current_user.role.value not in ["BDD_USER", "ADMIN"]:
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
        transaction_status=transaction_status.value if transaction_status else None,
    )
    
    # Serialize properties to match client expectations
    serialized_properties = []
    for prop in properties:
        property_dict = {
            "id": prop.id,
            "name": prop.name,
            "address": prop.address,
            "latitude": prop.latitude,
            "longitude": prop.longitude,
            "place_id": prop.place_id,
            "street": prop.street,
            "barangay_name": prop.barangay_name,
            "city_name": prop.city_name,
            "province_name": prop.province_name,
            "region_name": prop.region_name,
            "zip_code": prop.zip_code,
            "country": prop.country,
            "lot_area": float(prop.lot_area) if prop.lot_area else 0,
            "property_type": prop.property_type.value if prop.property_type else "RESIDENTIAL",
            "price": float(prop.price) if prop.price else 0,
            "currency": prop.currency or "PHP",
            "zoning_classification": prop.zoning_classification,
            "title_number": prop.title_number,
            "description": prop.description or "",
            "transaction_status": prop.transaction_status.value if prop.transaction_status else "S",
            "status": prop.status.value if prop.status else "PROPERTY_SOURCING",
            "submitted_by_id": prop.submitted_by_id,
            "submittedById": str(prop.submitted_by_id),  # Client expects string format
            "reviewer_id": prop.reviewer_id,
            "created_at": prop.created_at.isoformat() if prop.created_at else None,
            "updated_at": prop.updated_at.isoformat() if prop.updated_at else None,
            "createdAt": prop.created_at.isoformat() if prop.created_at else None,  # Client format
            "updatedAt": prop.updated_at.isoformat() if prop.updated_at else None,  # Client format
        }
        
        # Add submitted_by information
        if prop.submitted_by:
            property_dict["submitted_by"] = {
                "id": prop.submitted_by.id,
                "first_name": prop.submitted_by.first_name,
                "last_name": prop.submitted_by.last_name,
                "email": prop.submitted_by.email,
                "role": prop.submitted_by.role.value if prop.submitted_by.role else "AGENT",
                "created_at": prop.submitted_by.created_at.isoformat() if prop.submitted_by.created_at else None,
                "updated_at": prop.submitted_by.updated_at.isoformat() if prop.submitted_by.updated_at else None,
            }
            property_dict["submittedBy"] = {  # Client format
                "id": prop.submitted_by.id,
                "firstName": prop.submitted_by.first_name,
                "lastName": prop.submitted_by.last_name,
                "email": prop.submitted_by.email,
                "role": prop.submitted_by.role.value if prop.submitted_by.role else "AGENT",
                "createdAt": prop.submitted_by.created_at.isoformat() if prop.submitted_by.created_at else None,
                "updatedAt": prop.submitted_by.updated_at.isoformat() if prop.submitted_by.updated_at else None,
            }
        else:
            property_dict["submitted_by"] = None
            property_dict["submittedBy"] = None
            
        # Add reviewer information
        if prop.reviewer:
            property_dict["reviewer"] = {
                "id": prop.reviewer.id,
                "first_name": prop.reviewer.first_name,
                "last_name": prop.reviewer.last_name,
                "email": prop.reviewer.email,
                "role": prop.reviewer.role.value if prop.reviewer.role else "BDD_USER",
                "created_at": prop.reviewer.created_at.isoformat() if prop.reviewer.created_at else None,
                "updated_at": prop.reviewer.updated_at.isoformat() if prop.reviewer.updated_at else None,
            }
        else:
            property_dict["reviewer"] = None
            
        # Add attachments and workflow history (empty for now)
        property_dict["attachments"] = []
        property_dict["workflowHistory"] = []
        
        serialized_properties.append(property_dict)
    
    return {
        "properties": serialized_properties,
        "total": len(serialized_properties),
        "skip": skip,
        "limit": limit
    }


@router.post("/", response_model=PropertyRead)
async def create_property(
    property_data: PropertyCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
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


@router.get("/{property_id}")
async def get_property(
    property_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Get a specific property by ID with camelCase fields for client compatibility."""
    service = PropertyService(db)
    property_obj = await service.get_property(property_id)
    
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Check permissions (skip if no authentication for development)
    if (current_user and 
        current_user.role.value not in ["BDD_USER", "ADMIN"] and 
        property_obj.submitted_by_id != current_user.id and
        property_obj.reviewer_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to view this property")
    
    # Debug logging
    print(f"🏠 Fetching property ID: {property_id}")
    print(f"📋 Property Type: {property_obj.property_type}")
    print(f"💼 Transaction Status: {property_obj.transaction_status}")
    print(f"🏗️ Zoning Classification: {property_obj.zoning_classification}")
    print(f"📄 Title Number: {property_obj.title_number}")
    print(f"📐 Lot Area: {property_obj.lot_area}")
    print(f"📅 Created At: {property_obj.created_at}")
    print(f"📅 Updated At: {property_obj.updated_at}")
    print(f"👤 Submitted By: {property_obj.submitted_by.email if property_obj.submitted_by else 'None'}")
    print(f"📎 Attachments Count: {len(property_obj.attachments)}")
    for att in property_obj.attachments:
        print(f"  - {att.original_filename}: {att.file_size} bytes, {att.mime_type}")
    
    # Create a response with both snake_case (for Pydantic) and camelCase (for client) fields
    # This ensures compatibility with both the schema and the client expectations
    property_dict = {
        "id": property_obj.id,
        "name": property_obj.name,
        "address": property_obj.address,
        "latitude": property_obj.latitude,
        "longitude": property_obj.longitude,
        "place_id": property_obj.place_id,
        "street": property_obj.street,
        "barangay_name": property_obj.barangay_name,
        "city_name": property_obj.city_name,
        "province_name": property_obj.province_name,
        "region_name": property_obj.region_name,
        "zip_code": property_obj.zip_code,
        "country": property_obj.country,
        "lot_area": property_obj.lot_area,
        "property_type": property_obj.property_type,
        "price": property_obj.price,
        "currency": property_obj.currency,
        "zoning_classification": property_obj.zoning_classification,
        "title_number": property_obj.title_number,
        "description": property_obj.description,
        "transaction_status": property_obj.transaction_status,
        "status": property_obj.status,
        "submitted_by_id": property_obj.submitted_by_id,
        "reviewer_id": property_obj.reviewer_id,
        "created_at": property_obj.created_at,
        "updated_at": property_obj.updated_at,
        "attachments": property_obj.attachments,
        "workflow_history": property_obj.workflow_history,
    }
    
    # Safely serialize user data without exposing passwords
    if property_obj.submitted_by:
        user_data = UserPublic.model_validate(property_obj.submitted_by)
        property_dict["submitted_by"] = user_data
    else:
        property_dict["submitted_by"] = None
        
    if property_obj.reviewer:
        reviewer_data = UserPublic.model_validate(property_obj.reviewer)
        property_dict["reviewer"] = reviewer_data
    else:
        property_dict["reviewer"] = None
    
    # Create the Pydantic response
    response = PropertyRead(**property_dict)
    
    # Convert to dict and add camelCase aliases for client compatibility
    response_dict = response.model_dump()
    
    # Convert submittedBy user object to camelCase
    submitted_by_camel = None
    if property_obj.submitted_by:
        submitted_by_camel = {
            "id": property_obj.submitted_by.id,
            "email": property_obj.submitted_by.email,
            "firstName": property_obj.submitted_by.first_name,
            "middleName": property_obj.submitted_by.middle_name,
            "lastName": property_obj.submitted_by.last_name,
            "role": property_obj.submitted_by.role.value if property_obj.submitted_by.role else None,
            "company": property_obj.submitted_by.company,
            "phone": property_obj.submitted_by.phone,
            "isActive": property_obj.submitted_by.is_active,
            "accountStatus": property_obj.submitted_by.account_status.value if property_obj.submitted_by.account_status else None,
        }
    
    response_dict.update({
        "propertyType": str(property_obj.property_type.value) if property_obj.property_type else None,
        "lotArea": float(property_obj.lot_area) if property_obj.lot_area else 0,
        "zoningClassification": property_obj.zoning_classification,
        "titleNumber": property_obj.title_number,
        "transactionStatus": str(property_obj.transaction_status.value) if property_obj.transaction_status else None,
        "submittedBy": submitted_by_camel,
        "submittedById": str(property_obj.submitted_by_id) if property_obj.submitted_by_id else None,
        "createdAt": property_obj.created_at.isoformat() if property_obj.created_at else None,
        "updatedAt": property_obj.updated_at.isoformat() if property_obj.updated_at else None,
    })
    
    print(f"🔥 RESPONSE DICT KEYS: {list(response_dict.keys())}")
    print(f"🔥 Has propertyType: {'propertyType' in response_dict}")
    print(f"🔥 Has lotArea: {'lotArea' in response_dict}")
    print(f"🔥 propertyType value: {response_dict.get('propertyType')}")
    print(f"🔥 lotArea value: {response_dict.get('lotArea')}")
    
    # Use jsonable_encoder to ensure all fields are JSON serializable
    # This preserves our custom camelCase fields while handling CORS
    return jsonable_encoder(response_dict)


@router.patch("/{property_id}", response_model=PropertyRead)
async def update_property(
    property_id: int,
    property_data: PropertyUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Update a property."""
    service = PropertyService(db)
    property_obj = await service.get_property(property_id)
    
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Check permissions - only owner, reviewer, BDD user, or admin can update
    if (current_user.role.value not in ["BDD_USER", "ADMIN"] and
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
    current_user: User = Depends(get_current_user),
):
    """Delete a property."""
    service = PropertyService(db)
    property_obj = await service.get_property(property_id)
    
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Only BDD users, admins, or property owner can delete
    if (current_user.role.value not in ["BDD_USER", "ADMIN"] and
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
    current_user: User = Depends(get_current_user),
):
    """Update property workflow status."""
    # Check if property exists and user has permission
    property_service = PropertyService(db)
    property_obj = await property_service.get_property(property_id)
    
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Status updates can be done by BDD users, admins, brokers, or property owner
    if (current_user.role.value not in ["BDD_USER", "ADMIN", "BROKER"] and
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
    current_user: User = Depends(get_current_user),
):
    """Get property workflow history."""
    # Check if property exists and user has permission
    property_service = PropertyService(db)
    property_obj = await property_service.get_property(property_id)
    
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Check permissions
    if (current_user.role.value not in ["BDD_USER", "ADMIN"] and
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
    current_user: User = Depends(get_current_user),
):
    """Upload an attachment for a property."""
    # Check if property exists and user has permission
    property_service = PropertyService(db)
    property_obj = await property_service.get_property(property_id)
    
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Check permissions
    if (current_user.role.value not in ["BDD_USER", "ADMIN"] and
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
    current_user: User = Depends(get_current_user),
):
    """Get list of property attachments."""
    # Check if property exists and user has permission
    property_service = PropertyService(db)
    property_obj = await property_service.get_property(property_id)
    
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property not found")
    
    # Check permissions
    if (current_user.role.value not in ["BDD_USER", "ADMIN"] and
        property_obj.submitted_by_id != current_user.id and
        property_obj.reviewer_id != current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to view attachments")
    
    attachments = await property_service.get_property_attachments(property_id)
    return attachments


@router.get("/dashboard/statistics")
async def get_user_dashboard_statistics(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Get dashboard statistics for the current user based on their role."""
    from datetime import datetime, timedelta
    from sqlalchemy import func
    from app.models.property import Property
    from app.models.notification import Notification
    
    # Determine the appropriate filter based on user role
    is_admin_or_bdd = current_user.role.value in ["ADMIN", "BDD_USER"]
    
    # Build base query
    if is_admin_or_bdd:
        # Admin/BDD users see all properties
        base_query = select(Property)
    else:
        # Other users only see their own properties
        base_query = select(Property).where(Property.submitted_by_id == current_user.id)
    
    # Total properties count
    total_properties_query = select(func.count(Property.id))
    if not is_admin_or_bdd:
        total_properties_query = total_properties_query.where(Property.submitted_by_id == current_user.id)
    total_properties_result = await db.execute(total_properties_query)
    total_properties = total_properties_result.scalar() or 0
    
    # Status counts
    from app.models.workflow import PropertyStatus
    pending_review_query = select(func.count(Property.id)).where(
        Property.status.in_([PropertyStatus.PROPERTY_SOURCING, PropertyStatus.PROPERTY_STUDY])
    )
    approved_query = select(func.count(Property.id)).where(
        Property.status.in_([
            PropertyStatus.NEGOTIATION,
            PropertyStatus.DUE_DILIGENCE,
            PropertyStatus.CONTRACT_SIGNING,
            PropertyStatus.TAKEOVER
        ])
    )
    under_negotiation_query = select(func.count(Property.id)).where(
        Property.status == PropertyStatus.NEGOTIATION
    )
    
    if not is_admin_or_bdd:
        pending_review_query = pending_review_query.where(Property.submitted_by_id == current_user.id)
        approved_query = approved_query.where(Property.submitted_by_id == current_user.id)
        under_negotiation_query = under_negotiation_query.where(Property.submitted_by_id == current_user.id)
    
    pending_review_result = await db.execute(pending_review_query)
    pending_review = pending_review_result.scalar() or 0
    
    approved_result = await db.execute(approved_query)
    approved = approved_result.scalar() or 0
    
    under_negotiation_result = await db.execute(under_negotiation_query)
    under_negotiation = under_negotiation_result.scalar() or 0
    
    # This week submissions
    week_ago = datetime.utcnow() - timedelta(days=7)
    this_week_query = select(func.count(Property.id)).where(Property.created_at >= week_ago)
    if not is_admin_or_bdd:
        this_week_query = this_week_query.where(Property.submitted_by_id == current_user.id)
    this_week_result = await db.execute(this_week_query)
    this_week_submissions = this_week_result.scalar() or 0
    
    # Duplicate alerts (only for admin/BDD users)
    duplicate_alerts = 0
    if is_admin_or_bdd:
        # Count properties with potential duplicates
        # This is a placeholder - you can implement actual duplicate detection logic
        from app.models.property import DuplicateGroup
        try:
            duplicate_count_query = select(func.count(func.distinct(DuplicateGroup.id)))
            duplicate_count_result = await db.execute(duplicate_count_query)
            duplicate_alerts = duplicate_count_result.scalar() or 0
        except:
            duplicate_alerts = 0
    
    # Get unread notifications count
    unread_notifications_query = select(func.count(Notification.id)).where(
        Notification.user_id == current_user.id,
        Notification.is_read == False
    )
    unread_notifications_result = await db.execute(unread_notifications_query)
    unread_notifications = unread_notifications_result.scalar() or 0
    
    # Get status breakdown
    status_breakdown = {}
    for status in PropertyStatus:
        status_query = select(func.count(Property.id)).where(Property.status == status)
        if not is_admin_or_bdd:
            status_query = status_query.where(Property.submitted_by_id == current_user.id)
        status_result = await db.execute(status_query)
        status_count = status_result.scalar() or 0
        if status_count > 0:
            status_breakdown[status.value] = status_count
    
    return {
        "totalProperties": total_properties,
        "pendingReview": pending_review,
        "approved": approved,
        "underNegotiation": under_negotiation,
        "thisWeekSubmissions": this_week_submissions,
        "duplicateAlerts": duplicate_alerts,
        "unreadNotifications": unread_notifications,
        "statusBreakdown": status_breakdown,
        "userRole": current_user.role.value,
        "generatedAt": datetime.utcnow().isoformat()
    }


@router.patch("/{property_id}/assign-reviewer", response_model=PropertyRead)
async def assign_reviewer(
    property_id: int,
    reviewer_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Assign a reviewer to a property (admins only)."""
    if current_user.role.value != "ADMIN":
        raise HTTPException(status_code=403, detail="Not authorized to assign reviewers")
    
    service = PropertyService(db)
    property_obj = await service.assign_reviewer(property_id, reviewer_id)
    
    if not property_obj:
        raise HTTPException(status_code=404, detail="Property or reviewer not found")
    
    return property_obj