from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.models.user import User
from app.schemas.property import PropertyCreate
from app.schemas.workflow import DuplicateCheckRequest, DuplicateResult, DuplicateMergeRequest
from app.services.duplicate import DuplicateDetectionService
from app.services.property import PropertyService
from app.api.v1.auth import get_current_user

router = APIRouter(prefix="/duplicates", tags=["duplicates"])


@router.post("/check", response_model=List[DuplicateResult])
async def check_duplicates_by_property(
    property_data: PropertyCreate,
    threshold: float = 0.7,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Check for duplicate properties using full property data."""
    service = DuplicateDetectionService(db)
    
    try:
        duplicates = await service.check_duplicates(property_data, threshold)
        return duplicates
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Duplicate check failed: {str(e)}")


@router.get("/check", response_model=List[DuplicateResult])
async def check_duplicates_by_criteria(
    criteria: DuplicateCheckRequest = Depends(),
    threshold: float = 0.7,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Check for duplicates using flexible search criteria."""
    service = DuplicateDetectionService(db)
    
    try:
        duplicates = await service.check_duplicates_by_criteria(criteria, threshold)
        return duplicates
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Duplicate check failed: {str(e)}")


@router.post("/{property_id}/mark-duplicate")
async def mark_property_as_duplicate(
    property_id: int,
    original_property_id: int,
    notes: str = None,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Mark a property as a duplicate of another property."""
    # Only BDD users and admins can mark duplicates
    if current_user.role.value not in ["BDD_USER", "ADMIN"]:
        raise HTTPException(status_code=403, detail="Not authorized to mark duplicates")
    
    property_service = PropertyService(db)
    duplicate_service = DuplicateDetectionService(db)
    
    # Check both properties exist
    duplicate_property = await property_service.get_property(property_id)
    original_property = await property_service.get_property(original_property_id)
    
    if not duplicate_property:
        raise HTTPException(status_code=404, detail="Duplicate property not found")
    if not original_property:
        raise HTTPException(status_code=404, detail="Original property not found")
    
    try:
        # Use the new duplicate service method
        updated_property = await duplicate_service.mark_property_as_duplicate(
            property_id=property_id,
            duplicate_of_id=original_property_id,
            notes=notes
        )
        
        # Notify the property owner
        from app.services.notification import NotificationService
        from app.schemas.notification import NotificationCreate
        from app.models.notification import NotificationType
        
        notification_service = NotificationService(db)
        notification_data = NotificationCreate(
            user_id=duplicate_property.submitted_by_id,
            notification_type=NotificationType.DUPLICATE_DETECTED,
            title="Property Marked as Duplicate",
            message=(
                f"Your property '{duplicate_property.name}' (ID: {property_id}) has been marked "
                f"as a duplicate of property '{original_property.name}' (ID: {original_property_id}). "
                f"Notes: {notes or 'No additional notes provided'}. "
                f"Please contact an administrator if you have questions."
            ),
            property_id=property_id,
            duplicate_property_id=original_property_id
        )
        await notification_service.create_notification(notification_data, send_email=True)
        
        return {
            "message": f"Property {property_id} marked as duplicate of property {original_property_id}",
            "duplicate_property": updated_property,
            "original_property": original_property
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to mark duplicate: {str(e)}")


@router.post("/merge")
async def merge_duplicate_properties(
    merge_request: DuplicateMergeRequest,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Merge duplicate properties into a primary property."""
    # Only admin and BDD users can perform merges
    if current_user.role.value not in ["ADMIN", "BDD_USER"]:
        raise HTTPException(status_code=403, detail="Not authorized to merge properties")
    
    property_service = PropertyService(db)
    
    # Check primary property exists
    primary_property = await property_service.get_property(merge_request.primary_property_id)
    if not primary_property:
        raise HTTPException(status_code=404, detail="Primary property not found")
    
    # Check all duplicate properties exist
    duplicate_properties = []
    for dup_id in merge_request.duplicate_property_ids:
        dup_property = await property_service.get_property(dup_id)
        if not dup_property:
            raise HTTPException(status_code=404, detail=f"Duplicate property {dup_id} not found")
        duplicate_properties.append(dup_property)
    
    # Perform merge logic
    try:
        duplicate_service = DuplicateDetectionService(db)
        
        # Mark each duplicate property with the new duplicate tracking fields
        merged_info = []
        for dup_property in duplicate_properties:
            # Use the duplicate service to mark as duplicate
            updated_dup = await duplicate_service.mark_property_as_duplicate(
                property_id=dup_property.id,
                duplicate_of_id=merge_request.primary_property_id,
                notes=f"MERGED INTO PROPERTY #{merge_request.primary_property_id}. {merge_request.merge_notes or ''}"
            )
            
            merged_info.append({
                "id": dup_property.id,
                "name": dup_property.name,
                "status": "marked_as_merged",
                "is_duplicate": updated_dup.is_duplicate,
                "duplicate_of_id": updated_dup.duplicate_of_id
            })
            
            # Notify the property owner that their property was merged
            from app.services.notification import NotificationService
            from app.schemas.notification import NotificationCreate
            from app.models.notification import NotificationType
            
            notification_service = NotificationService(db)
            notification_data = NotificationCreate(
                user_id=dup_property.submitted_by_id,
                notification_type=NotificationType.PROPERTY_MERGED,
                title="Property Merged",
                message=(
                    f"Your property '{dup_property.name}' (ID: {dup_property.id}) has been merged "
                    f"into property '{primary_property.name}' (ID: {primary_property.id}). "
                    f"Merge notes: {merge_request.merge_notes or 'No additional notes'}. "
                    f"All information has been consolidated into the primary property."
                ),
                property_id=dup_property.id,
                duplicate_property_id=merge_request.primary_property_id
            )
            await notification_service.create_notification(notification_data, send_email=True)
        
        # Update primary property description to note the merge (optional, for reference)
        primary_description = primary_property.description or ""
        primary_description += f"\n\nMERGED WITH PROPERTIES: {', '.join([str(id) for id in merge_request.duplicate_property_ids])}"
        if merge_request.merge_notes:
            primary_description += f"\nMerge notes: {merge_request.merge_notes}"
        
        from app.schemas.property import PropertyUpdate
        primary_update = PropertyUpdate(description=primary_description)
        updated_primary = await property_service.update_property(
            merge_request.primary_property_id, 
            primary_update
        )
        
        return {
            "message": "Properties merged successfully",
            "primary_property": updated_primary,
            "merged_properties": merged_info
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Merge failed: {str(e)}")


@router.get("/{property_id}/similarity/{comparison_property_id}")
async def calculate_property_similarity(
    property_id: int,
    comparison_property_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Calculate similarity score between two properties."""
    property_service = PropertyService(db)
    
    # Check both properties exist
    property1 = await property_service.get_property(property_id)
    property2 = await property_service.get_property(comparison_property_id)
    
    if not property1:
        raise HTTPException(status_code=404, detail="First property not found")
    if not property2:
        raise HTTPException(status_code=404, detail="Second property not found")
    
    # Check permissions for both properties
    def can_access_property(prop):
        return (current_user.role.value in ["BDD_USER"] or
                prop.submitted_by_id == current_user.id or
                prop.reviewer_id == current_user.id)
    
    if not can_access_property(property1) or not can_access_property(property2):
        raise HTTPException(status_code=403, detail="Not authorized to compare these properties")
    
    try:
        service = DuplicateDetectionService(db)
        similarity_score = await service.calculate_similarity_score(property1, property2)
        
        return {
            "property1_id": property_id,
            "property2_id": comparison_property_id,
            "similarity_score": similarity_score,
            "properties": {
                "property1": {
                    "id": property1.id,
                    "name": property1.name,
                    "address": property1.address,
                    "title_number": property1.title_number
                },
                "property2": {
                    "id": property2.id,
                    "name": property2.name,
                    "address": property2.address,
                    "title_number": property2.title_number
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Similarity calculation failed: {str(e)}")