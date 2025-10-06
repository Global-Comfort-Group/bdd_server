from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.core.database import get_db
from app.models.user import User
from app.models.property import Property
from app.models.draft_nego_table import DraftNegoTable
from app.api.v1.auth import get_current_user
from app.schemas.draft_nego_table import (
    DraftNegoTable as DraftNegoTableSchema,
    DraftNegoTableCreate,
    DraftNegoTableUpdate,
    DraftNegoTableWithProperty
)

router = APIRouter()

@router.post("/", response_model=DraftNegoTableSchema)
def create_draft_nego_table(
    draft_in: DraftNegoTableCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new draft negotiation table for a property."""
    
    # Verify property exists
    property_obj = db.query(Property).filter(Property.id == draft_in.property_id).first()
    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )
    
    # Check if draft already exists for this property and user
    existing_draft = db.query(DraftNegoTable).filter(
        and_(
            DraftNegoTable.property_id == draft_in.property_id,
            DraftNegoTable.user_id == current_user.id
        )
    ).first()
    
    if existing_draft:
        # Update existing draft
        for field, value in draft_in.dict(exclude_unset=True).items():
            if field != "property_id":  # Don't update property_id
                setattr(existing_draft, field, value)
        
        db.commit()
        db.refresh(existing_draft)
        return existing_draft
    
    # Create new draft
    draft_data = draft_in.dict()
    draft_data["user_id"] = current_user.id
    
    db_draft = DraftNegoTable(**draft_data)
    db.add(db_draft)
    db.commit()
    db.refresh(db_draft)
    
    return db_draft

@router.get("/property/{property_id}", response_model=Optional[DraftNegoTableSchema])
def get_draft_by_property(
    property_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get draft negotiation table for a specific property by current user."""
    
    draft = db.query(DraftNegoTable).filter(
        and_(
            DraftNegoTable.property_id == property_id,
            DraftNegoTable.user_id == current_user.id
        )
    ).first()
    
    return draft

@router.get("/", response_model=List[DraftNegoTableWithProperty])
def get_user_drafts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get all draft negotiation tables for current user."""
    
    drafts = db.query(DraftNegoTable).filter(
        DraftNegoTable.user_id == current_user.id
    ).offset(skip).limit(limit).all()
    
    return drafts

@router.put("/{draft_id}", response_model=DraftNegoTableSchema)
def update_draft_nego_table(
    draft_id: int,
    draft_update: DraftNegoTableUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a draft negotiation table."""
    
    # Get existing draft
    draft = db.query(DraftNegoTable).filter(
        and_(
            DraftNegoTable.id == draft_id,
            DraftNegoTable.user_id == current_user.id
        )
    ).first()
    
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not found"
        )
    
    # Update draft
    update_data = draft_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(draft, field, value)
    
    db.commit()
    db.refresh(draft)
    
    return draft

@router.patch("/{draft_id}/auto-save", response_model=DraftNegoTableSchema)
def auto_save_draft(
    draft_id: int,
    draft_update: DraftNegoTableUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Auto-save a draft negotiation table (lighter endpoint for frequent calls)."""
    
    # Get existing draft
    draft = db.query(DraftNegoTable).filter(
        and_(
            DraftNegoTable.id == draft_id,
            DraftNegoTable.user_id == current_user.id
        )
    ).first()
    
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not found"
        )
    
    # Update only provided fields
    update_data = draft_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(draft, field, value)
    
    # Update last_auto_save timestamp is handled by SQLAlchemy onupdate
    db.commit()
    db.refresh(draft)
    
    return draft

@router.delete("/{draft_id}")
def delete_draft_nego_table(
    draft_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a draft negotiation table."""
    
    # Get existing draft
    draft = db.query(DraftNegoTable).filter(
        and_(
            DraftNegoTable.id == draft_id,
            DraftNegoTable.user_id == current_user.id
        )
    ).first()
    
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not found"
        )
    
    db.delete(draft)
    db.commit()
    
    return {"message": "Draft deleted successfully"}

@router.post("/{draft_id}/finalize", response_model=dict)
def finalize_draft_to_nego_table(
    draft_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Convert a draft to a final negotiation table and delete the draft."""
    
    # This endpoint will be called by the client when ready to submit
    # It should validate the draft data and create the actual NegoTable
    
    draft = db.query(DraftNegoTable).filter(
        and_(
            DraftNegoTable.id == draft_id,
            DraftNegoTable.user_id == current_user.id
        )
    ).first()
    
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Draft not found"
        )
    
    # Here you would create the actual NegoTable from the draft data
    # For now, return the draft data for the client to handle
    return {
        "draft_data": {
            "form_data": draft.form_data,
            "negotiations_data": draft.negotiations_data,
            "financial_data": draft.financial_data,
            "property_id": draft.property_id
        },
        "message": "Draft ready for finalization"
    }