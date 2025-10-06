from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.core.database import get_async_session
from app.models.user import User
from app.api.v1.auth import get_current_user
from app.api.v1.properties_simple import MOCK_PROPERTIES

router = APIRouter()

# In-memory storage for created nego tables (in production, this would be a database)
CREATED_NEGO_TABLES = {}

# In-memory storage for attachments linked to in-memory nego tables
NEGO_TABLE_ATTACHMENTS = {}

@router.get("/")
async def get_nego_tables(
    property_id: Optional[int] = Query(None, description="Filter by property ID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000)
):
    """Get negotiation tables, optionally filtered by property."""
    
    # Get all created nego tables
    all_tables = list(CREATED_NEGO_TABLES.values())
    
    # Filter by property ID if provided
    if property_id:
        all_tables = [t for t in all_tables if t.get("property_id") == property_id]
    
    return all_tables[skip:skip + limit]

@router.post("/")
async def create_nego_table(
    nego_table_data: dict,
    db: AsyncSession = Depends(get_async_session)
):
    """Create a new negotiation table for a property with auto-populated data."""
    
    print(f"📥 RECEIVED NEGO TABLE CREATE REQUEST")
    print(f"📥 Request data: {nego_table_data}")
    
    from app.services.property import PropertyService
    from sqlalchemy import select
    from app.models.property import Property
    
    property_id = nego_table_data.get("propertyId")
    if not property_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Property ID is required"
        )
    
    # Ensure property_id is an integer for database queries
    property_id = int(property_id)
    
    print(f"🔍 Creating negotiation chronicle for property ID: {property_id}")
    
    # First try to get property from database
    try:
        from sqlalchemy.orm import selectinload
        
        # Eagerly load the submitted_by relationship to avoid lazy loading issues
        result = await db.execute(
            select(Property)
            .filter(Property.id == property_id)
            .options(selectinload(Property.submitted_by))
        )
        property_obj = result.scalar_one_or_none()
        
        if property_obj:
            print(f"✅ Found property in database: {property_obj.name}")
            # Convert database property to dictionary format
            property_data = {
                "id": property_obj.id,
                "name": property_obj.name,
                "address": property_obj.address,
                "lotArea": float(property_obj.lot_area) if property_obj.lot_area else 0,
                "propertyType": property_obj.property_type.value if property_obj.property_type else "LAND_ONLY",
                "price": float(property_obj.price) if property_obj.price else 0,
                "currency": property_obj.currency or "PHP",
                "zoningClassification": property_obj.zoning_classification or "",
                "titleNumber": property_obj.title_number or "",
                "transactionStatus": property_obj.transaction_status.value if property_obj.transaction_status else "S",
                "status": property_obj.status.value if property_obj.status else "PENDING",  # Added status field
                "submittedBy": {
                    "id": property_obj.submitted_by.id if property_obj.submitted_by else 0,
                    "firstName": property_obj.submitted_by.first_name if property_obj.submitted_by else "Unknown",
                    "lastName": property_obj.submitted_by.last_name if property_obj.submitted_by else "User",
                    "email": property_obj.submitted_by.email if property_obj.submitted_by else "unknown@email.com",
                    "role": property_obj.submitted_by.role.value if property_obj.submitted_by and property_obj.submitted_by.role else "AGENT"
                } if property_obj.submitted_by else {
                    "id": 0,
                    "firstName": "Unknown",
                    "lastName": "User",
                    "email": "unknown@email.com",
                    "role": "AGENT"
                }
            }
        else:
            # Fallback to MOCK_PROPERTIES if not in database
            print(f"⚠️  Property not found in database, checking mock storage...")
            if property_id not in MOCK_PROPERTIES:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Property not found (ID: {property_id})"
                )
            property_data = MOCK_PROPERTIES[property_id]
            print(f"✅ Found property in mock storage: {property_data['name']}")
    except Exception as e:
        print(f"❌ Error fetching property: {e}")
        import traceback
        traceback.print_exc()
        # For database errors, don't fallback - raise the error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error while fetching property: {str(e)}"
        )
    
    # Auto-generate nego table ID
    new_id = len(CREATED_NEGO_TABLES) + 1
    
    # Auto-populate nego table from property details
    new_nego_table = {
        "id": new_id,
        "property_id": property_id,
        "source_origin": nego_table_data.get("sourceOrigin", "Direct Inquiry"),
        "current_property_name": property_data["name"],
        "current_location": property_data["address"],
        "current_property_type": property_data["propertyType"],
        "current_lot_area": property_data["lotArea"],
        "status": "ACTIVE",
        "monthly_lease": nego_table_data.get("monthlyLease"),
        "sale_total": property_data["price"],  # Auto-fill from property price
        "investment": nego_table_data.get("investment"),
        "negotiations": nego_table_data.get("negotiations", []),
        
        # Include missing property fields that should be preserved
        "title_number": property_data.get("titleNumber", ""),
        "zoning_classification": property_data.get("zoningClassification", ""),
        "transaction_status": property_data.get("transactionStatus", ""),
        "submitted_by": property_data.get("submittedBy", {}),
        
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
        "created_by": {
            "id": property_data["submittedBy"]["id"],
            "firstName": property_data["submittedBy"]["firstName"],
            "lastName": property_data["submittedBy"]["lastName"]
        },
        "property": {
            "id": property_data["id"],
            "name": property_data["name"],
            "address": property_data["address"],
            "lotArea": property_data["lotArea"],
            "propertyType": property_data["propertyType"],
            "price": property_data["price"],
            "currency": property_data["currency"],
            "status": property_data["status"],
            # Include the missing fields in the property object as well
            "titleNumber": property_data.get("titleNumber", ""),
            "zoningClassification": property_data.get("zoningClassification", ""),
            "transactionStatus": property_data.get("transactionStatus", ""),
            "submittedBy": property_data.get("submittedBy", {})
        }
    }
    
    # Store the nego table
    CREATED_NEGO_TABLES[new_id] = new_nego_table
    
    return new_nego_table

@router.get("/{nego_table_id}")
async def get_nego_table(
    nego_table_id: int
):
    """Get a specific negotiation table by ID."""
    
    if nego_table_id not in CREATED_NEGO_TABLES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Negotiation table not found"
        )
    
    return CREATED_NEGO_TABLES[nego_table_id]

@router.post("/{nego_table_id}/timeline")
async def add_timeline_entry(
    nego_table_id: int,
    timeline_data: dict
):
    """Add a timeline entry (negotiation) to a nego table."""
    
    if nego_table_id not in CREATED_NEGO_TABLES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Negotiation table not found"
        )
    
    nego_table = CREATED_NEGO_TABLES[nego_table_id]
    
    # Create new timeline entry
    new_entry = {
        "date": timeline_data.get("date", datetime.now().strftime("%Y-%m-%d")),
        "meeting_type": timeline_data.get("meetingType", "General Meeting"),
        "attendees": timeline_data.get("attendees", []),
        "notes": timeline_data.get("notes", ""),
        "outcome": timeline_data.get("outcome", ""),
        "created_at": datetime.now().isoformat()
    }
    
    # Add to negotiations list
    nego_table["negotiations"].append(new_entry)
    nego_table["updated_at"] = datetime.now().isoformat()
    
    return {
        "message": "Timeline entry added successfully",
        "entry": new_entry,
        "nego_table_id": nego_table_id
    }

@router.get("/{nego_table_id}/export/csv")
async def export_nego_table_csv(
    nego_table_id: int
):
    """Export negotiation table data to CSV format."""
    
    if nego_table_id not in CREATED_NEGO_TABLES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Negotiation table not found"
        )
    
    nego_table = CREATED_NEGO_TABLES[nego_table_id]
    
    # Create CSV data structure
    csv_data = {
        "property_info": {
            "Property Name": nego_table["current_property_name"],
            "Location": nego_table["current_location"],
            "Property Type": nego_table["current_property_type"],
            "Lot Area": f"{nego_table['current_lot_area']} sqm",
            "Sale Price": f"₱{nego_table['sale_total']:,}" if nego_table.get('sale_total') else "N/A",
            "Monthly Lease": f"₱{nego_table['monthly_lease']:,}" if nego_table.get('monthly_lease') else "N/A",
            "Investment": f"₱{nego_table['investment']:,}" if nego_table.get('investment') else "N/A",
            "Status": nego_table["status"],
            "Source Origin": nego_table["source_origin"],
            # Include the missing fields in CSV export
            "Title Number": nego_table.get("title_number", "N/A"),
            "Zoning Classification": nego_table.get("zoning_classification", "N/A"),
            "Transaction Status": nego_table.get("transaction_status", "N/A"),
            "Submitted By": f"{nego_table.get('submitted_by', {}).get('firstName', '')} {nego_table.get('submitted_by', {}).get('lastName', '')}".strip() or "N/A"
        },
        "timeline": nego_table["negotiations"],
        "metadata": {
            "Exported Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "Total Timeline Entries": len(nego_table["negotiations"]),
            "Created Date": nego_table["created_at"],
            "Last Updated": nego_table["updated_at"]
        }
    }
    
    return csv_data

@router.put("/{nego_table_id}")
async def update_nego_table(
    nego_table_id: int,
    nego_table_data: dict
):
    """Update a negotiation table."""
    
    for i, table in enumerate(MOCK_NEGO_TABLES):
        if table.get("id") == nego_table_id:
            MOCK_NEGO_TABLES[i].update(nego_table_data)
            MOCK_NEGO_TABLES[i]["updated_at"] = datetime.now().isoformat()
            return MOCK_NEGO_TABLES[i]
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Negotiation table not found"
    )

@router.delete("/{nego_table_id}")
async def delete_nego_table(
    nego_table_id: int
):
    """Delete a negotiation table."""
    
    for i, table in enumerate(MOCK_NEGO_TABLES):
        if table.get("id") == nego_table_id:
            MOCK_NEGO_TABLES.pop(i)
            return {"message": "Negotiation table deleted successfully"}
    
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Negotiation table not found"
    )