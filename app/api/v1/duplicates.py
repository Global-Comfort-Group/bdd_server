from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.models.user import User
from app.schemas.property import PropertyCreate
from app.schemas.workflow import DuplicateCheckRequest, DuplicateResult, DuplicateMergeRequest
from app.services.duplicate import DuplicateDetectionService
from app.services.property import PropertyService
from app.api.v1.auth import current_active_user

router = APIRouter(prefix="/duplicates", tags=["duplicates"])


@router.post("/check", response_model=List[DuplicateResult])
async def check_duplicates_by_property(
    property_data: PropertyCreate,
    threshold: float = 0.7,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_active_user),
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
    current_user: User = Depends(current_active_user),
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
    current_user: User = Depends(current_active_user),
):
    """Mark a property as a duplicate of another property."""
    # Only BDD users can mark duplicates
    if current_user.role.value not in ["BDD_USER"]:
        raise HTTPException(status_code=403, detail="Not authorized to mark duplicates")
    
    property_service = PropertyService(db)
    
    # Check both properties exist
    duplicate_property = await property_service.get_property(property_id)
    original_property = await property_service.get_property(original_property_id)
    
    if not duplicate_property:
        raise HTTPException(status_code=404, detail="Duplicate property not found")
    if not original_property:
        raise HTTPException(status_code=404, detail="Original property not found")
    
    # For now, we'll just add a note to the property
    # In a full implementation, you might want a separate table for duplicate relationships
    try:
        from app.schemas.property import PropertyUpdate
        update_data = PropertyUpdate(
            description=f"MARKED AS DUPLICATE OF PROPERTY #{original_property_id}. " + 
                       f"Notes: {notes or 'No additional notes'}\n\n" + 
                       (duplicate_property.description or "")
        )
        
        updated_property = await property_service.update_property(property_id, update_data)
        
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
    current_user: User = Depends(current_active_user),
):
    """Merge duplicate properties into a primary property."""
    # Only admin can perform merges
    if current_user.role.value != "ADMIN":
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
        # In a full implementation, you would:
        # 1. Move attachments from duplicate properties to primary
        # 2. Merge workflow history
        # 3. Update references in other tables
        # 4. Archive or delete duplicate properties
        
        # For now, we'll just mark the duplicates in their descriptions
        merge_notes = f"MERGED INTO PROPERTY #{merge_request.primary_property_id}"
        if merge_request.merge_notes:
            merge_notes += f". Notes: {merge_request.merge_notes}"
        
        merged_info = []
        for dup_property in duplicate_properties:
            from app.schemas.property import PropertyUpdate
            update_data = PropertyUpdate(
                description=f"{merge_notes}\n\n{dup_property.description or ''}"
            )
            
            updated_dup = await property_service.update_property(dup_property.id, update_data)
            merged_info.append({
                "id": dup_property.id,
                "name": dup_property.name,
                "status": "marked_as_merged"
            })
        
        # Update primary property description to note the merge
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
    current_user: User = Depends(current_active_user),
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