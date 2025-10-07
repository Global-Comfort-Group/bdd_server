from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.models.user import User
from app.api.v1.auth import get_current_user
from app.schemas.nego_table import (
    NegoTable as NegoTableSchema,
    NegoTableCreate,
    NegoTableUpdate,
    NegoTableWithProperty,
    NegotiationEntry as NegotiationEntrySchema,
    NegotiationEntryCreate,
    NegotiationEntryUpdate
)

router = APIRouter()

@router.post("/", response_model=NegoTableSchema)
def create_nego_table(
    nego_table_in: NegoTableCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new negotiation table for a property. Only BDD_USER and ADMIN can create."""
    
    # Check permissions - only BDD users and admins can create negotiation chronicles
    if current_user.role.value not in ["BDD_USER", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only BDD employees and admins can create negotiation chronicles"
        )
    
    # Verify property exists
    property_obj = db.query(Property).filter(Property.id == nego_table_in.property_id).first()
    if not property_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )
    
    # Create the nego table
    nego_table_data = nego_table_in.dict(exclude={"negotiations"})
    nego_table_data["created_by_id"] = current_user.id
    
    db_nego_table = NegoTable(**nego_table_data)
    db.add(db_nego_table)
    db.flush()  # Get the ID
    
    # Create negotiation entries
    for negotiation_data in nego_table_in.negotiations:
        db_negotiation = NegotiationEntry(
            **negotiation_data.dict(),
            nego_table_id=db_nego_table.id
        )
        db.add(db_negotiation)
    
    db.commit()
    db.refresh(db_nego_table)
    
    return db_nego_table

@router.get("/", response_model=List[NegoTableWithProperty])
def get_nego_tables(
    property_id: Optional[int] = Query(None, description="Filter by property ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get negotiation tables, optionally filtered by property."""
    
    query = db.query(NegoTable)
    
    if property_id:
        query = query.filter(NegoTable.property_id == property_id)
    
    nego_tables = query.offset(skip).limit(limit).all()
    
    # Add property information to each nego table
    result = []
    for nego_table in nego_tables:
        nego_table_dict = NegoTableSchema.from_orm(nego_table).dict()
        
        # Add property info
        property_info = {
            "id": nego_table.property.id,
            "name": nego_table.property.name,
            "address": nego_table.property.address,
            "lot_area": float(nego_table.property.lot_area),
            "property_type": nego_table.property.property_type.value,
            "price": float(nego_table.property.price),
            "currency": nego_table.property.currency
        }
        nego_table_dict["property"] = property_info
        result.append(nego_table_dict)
    
    return result

@router.get("/{nego_table_id}", response_model=NegoTableWithProperty)
def get_nego_table(
    nego_table_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific negotiation table by ID."""
    
    nego_table = db.query(NegoTable).filter(NegoTable.id == nego_table_id).first()
    if not nego_table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Negotiation table not found"
        )
    
    nego_table_dict = NegoTableSchema.from_orm(nego_table).dict()
    
    # Add property info
    property_info = {
        "id": nego_table.property.id,
        "name": nego_table.property.name,
        "address": nego_table.property.address,
        "lot_area": float(nego_table.property.lot_area),
        "property_type": nego_table.property.property_type.value,
        "price": float(nego_table.property.price),
        "currency": nego_table.property.currency
    }
    nego_table_dict["property"] = property_info
    
    return nego_table_dict

@router.put("/{nego_table_id}", response_model=NegoTableSchema)
def update_nego_table(
    nego_table_id: int,
    nego_table_in: NegoTableUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a negotiation table. Only BDD_USER and ADMIN can update."""
    
    # Check permissions - only BDD users and admins can update negotiation chronicles
    if current_user.role.value not in ["BDD_USER", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only BDD employees and admins can update negotiation chronicles"
        )
    
    nego_table = db.query(NegoTable).filter(NegoTable.id == nego_table_id).first()
    if not nego_table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Negotiation table not found"
        )
    
    # Update fields
    update_data = nego_table_in.dict(exclude_unset=True)
    update_data["updated_by_id"] = current_user.id
    
    for field, value in update_data.items():
        setattr(nego_table, field, value)
    
    db.commit()
    db.refresh(nego_table)
    
    return nego_table

@router.delete("/{nego_table_id}")
def delete_nego_table(
    nego_table_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a negotiation table. Only BDD_USER and ADMIN can delete."""
    
    # Check permissions - only BDD users and admins can delete negotiation chronicles
    if current_user.role.value not in ["BDD_USER", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only BDD employees and admins can delete negotiation chronicles"
        )
    
    nego_table = db.query(NegoTable).filter(NegoTable.id == nego_table_id).first()
    if not nego_table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Negotiation table not found"
        )
    
    db.delete(nego_table)
    db.commit()
    
    return {"message": "Negotiation table deleted successfully"}

# Negotiation entries endpoints
@router.post("/{nego_table_id}/negotiations", response_model=NegotiationEntrySchema)
def add_negotiation_entry(
    nego_table_id: int,
    negotiation_in: NegotiationEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a new negotiation entry to a nego table. Only BDD_USER and ADMIN can add."""
    
    # Check permissions - only BDD users and admins can add negotiation entries
    if current_user.role.value not in ["BDD_USER", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only BDD employees and admins can add negotiation entries"
        )
    
    # Verify nego table exists
    nego_table = db.query(NegoTable).filter(NegoTable.id == nego_table_id).first()
    if not nego_table:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Negotiation table not found"
        )
    
    db_negotiation = NegotiationEntry(
        **negotiation_in.dict(),
        nego_table_id=nego_table_id
    )
    db.add(db_negotiation)
    db.commit()
    db.refresh(db_negotiation)
    
    # Update nego table timestamp
    nego_table.updated_by_id = current_user.id
    db.commit()
    
    return db_negotiation

@router.put("/{nego_table_id}/negotiations/{negotiation_id}", response_model=NegotiationEntrySchema)
def update_negotiation_entry(
    nego_table_id: int,
    negotiation_id: int,
    negotiation_in: NegotiationEntryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update a negotiation entry. Only BDD_USER and ADMIN can update."""
    
    # Check permissions - only BDD users and admins can update negotiation entries
    if current_user.role.value not in ["BDD_USER", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only BDD employees and admins can update negotiation entries"
        )
    
    negotiation = db.query(NegotiationEntry).filter(
        and_(
            NegotiationEntry.id == negotiation_id,
            NegotiationEntry.nego_table_id == nego_table_id
        )
    ).first()
    
    if not negotiation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Negotiation entry not found"
        )
    
    # Update fields
    update_data = negotiation_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(negotiation, field, value)
    
    db.commit()
    db.refresh(negotiation)
    
    # Update nego table timestamp
    nego_table = db.query(NegoTable).filter(NegoTable.id == nego_table_id).first()
    if nego_table:
        nego_table.updated_by_id = current_user.id
        db.commit()
    
    return negotiation

@router.delete("/{nego_table_id}/negotiations/{negotiation_id}")
def delete_negotiation_entry(
    nego_table_id: int,
    negotiation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a negotiation entry. Only BDD_USER and ADMIN can delete."""
    
    # Check permissions - only BDD users and admins can delete negotiation entries
    if current_user.role.value not in ["BDD_USER", "ADMIN"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only BDD employees and admins can delete negotiation entries"
        )
    
    negotiation = db.query(NegotiationEntry).filter(
        and_(
            NegotiationEntry.id == negotiation_id,
            NegotiationEntry.nego_table_id == nego_table_id
        )
    ).first()
    
    if not negotiation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Negotiation entry not found"
        )
    
    db.delete(negotiation)
    db.commit()
    
    # Update nego table timestamp
    nego_table = db.query(NegoTable).filter(NegoTable.id == nego_table_id).first()
    if nego_table:
        nego_table.updated_by_id = current_user.id
        db.commit()
    
    return {"message": "Negotiation entry deleted successfully"}