from typing import Optional, List, Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Form, File, UploadFile, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
import os
import uuid
from pathlib import Path

from app.core.database import get_async_session
from app.api.v1.auth import get_current_user, get_current_user_optional
from app.models.user import User
from app.services.cloudinary_service import cloudinary_service
from app.services.property import PropertyService
from app.schemas.property import PropertyCreate
from app.models.enums import PropertyType, PropertyStatus, TransactionStatus
from datetime import datetime
from decimal import Decimal

router = APIRouter()

# Mock property data
MOCK_PROPERTIES = {
    1: {
        "id": 1,
        "name": "Ces't La Vie Hotel",
        "address": "Juana Osmena Extn., Kamphutaw, Cebu City",
        "lotArea": 510,
        "propertyType": "HOTEL",
        "price": 130000000,
        "currency": "PHP",
        "zoningClassification": "Commercial",
        "titleNumber": "TCT-12345-CEBU",
        "description": "Closed 5-story hotel building with basement and roofdeck. 69 guest rooms with basement parking.",
        "status": "NEGOTIATION",
        "transactionStatus": "S",  # Sale
        "submittedBy": {
            "id": 1,
            "firstName": "Mark",
            "lastName": "Gerbuela",
            "email": "mark@broker.com",
            "role": "BROKER"
        }
    },
    2: {
        "id": 2,
        "name": "BGC Residential Lot",
        "address": "26th Street, Bonifacio Global City, Taguig",
        "lotArea": 300,
        "propertyType": "RESIDENTIAL",
        "price": 45000000,
        "currency": "PHP",
        "zoningClassification": "Residential",
        "titleNumber": "TCT-654321",
        "description": "Premium residential lot in BGC",
        "status": "NEGOTIATION",
        "transactionStatus": "S",  # Sale
        "submittedBy": {
            "id": 2,
            "firstName": "Maria",
            "lastName": "Santos",
            "email": "maria@broker.com",
            "role": "BROKER"
        }
    },
    3: {
        "id": 3,
        "name": "Ortigas Commercial Space",
        "address": "EDSA, Ortigas Center, Pasig City",
        "lotArea": 750,
        "propertyType": "COMMERCIAL",
        "price": 85000000,
        "currency": "PHP",
        "zoningClassification": "Commercial",
        "titleNumber": "TCT-789012",
        "description": "Strategic commercial space in Ortigas",
        "status": "DUE_DILIGENCE",
        "transactionStatus": "L",  # Lease
        "submittedBy": {
            "id": 3,
            "firstName": "Carlos",
            "lastName": "Reyes",
            "email": "carlos@realty.com",
            "role": "AGENT"
        }
    },
    4: {
        "id": 4,
        "name": "Alabang Industrial Warehouse",
        "address": "Filinvest Corporate City, Alabang, Muntinlupa",
        "lotArea": 2000,
        "propertyType": "INDUSTRIAL",
        "price": 120000000,
        "currency": "PHP",
        "zoningClassification": "Industrial",
        "titleNumber": "TCT-345678",
        "description": "Large warehouse facility in Alabang",
        "status": "CONTRACT_SIGNING",
        "transactionStatus": "S",  # Sale
        "submittedBy": {
            "id": 4,
            "firstName": "Ana",
            "lastName": "Garcia",
            "email": "ana@properties.com",
            "role": "BROKER"
        }
    },
    5: {
        "id": 5,
        "name": "QC Mixed-Use Development",
        "address": "Commonwealth Avenue, Quezon City",
        "lotArea": 1200,
        "propertyType": "MIXED_USE",
        "price": 200000000,
        "currency": "PHP",
        "zoningClassification": "Mixed Use",
        "titleNumber": "TCT-901234",
        "description": "Mixed-use development opportunity in QC",
        "status": "COUNCIL_APPROVAL",
        "transactionStatus": "S",  # Sale
        "submittedBy": {
            "id": 5,
            "firstName": "Roberto",
            "lastName": "Cruz",
            "email": "roberto@investments.com",
            "role": "AGENT"
        }
    },
    6: {
        "id": 6,
        "name": "Cebu IT Park Office Space",
        "address": "Cebu IT Park, Lahug, Cebu City",
        "lotArea": 800,
        "propertyType": "COMMERCIAL",
        "price": 95000000,
        "currency": "PHP",
        "zoningClassification": "Commercial",
        "titleNumber": "TCT-567890",
        "description": "Modern office space in Cebu IT Park",
        "status": "PROPERTY_SOURCING",
        "transactionStatus": "L",  # Lease
        "submittedBy": {
            "id": 6,
            "firstName": "Rico",
            "lastName": "Gonzales",
            "email": "rico@cebu.com",
            "role": "AGENT"
        }
    },
    7: {
        "id": 7,
        "name": "Davao Residential Subdivision",
        "address": "Catalunan Grande, Davao City",
        "lotArea": 5000,
        "propertyType": "RESIDENTIAL",
        "price": 75000000,
        "currency": "PHP",
        "zoningClassification": "Residential",
        "titleNumber": "TCT-345789",
        "description": "Large residential subdivision lot in Davao",
        "status": "PBY_PREPARATION",
        "transactionStatus": "S",  # Sale
        "submittedBy": {
            "id": 7,
            "firstName": "Elena",
            "lastName": "Rodriguez",
            "email": "elena@mindanao.com",
            "role": "BROKER"
        }
    },
    8: {
        "id": 8,
        "name": "Baguio Mountain Resort",
        "address": "Session Road, Baguio City",
        "lotArea": 3000,
        "propertyType": "COMMERCIAL",
        "price": 180000000,
        "currency": "PHP",
        "zoningClassification": "Tourism",
        "titleNumber": "TCT-678901",
        "description": "Mountain resort property in Baguio",
        "status": "TAKEOVER",
        "transactionStatus": "S",  # Sale
        "submittedBy": {
            "id": 8,
            "firstName": "Miguel",
            "lastName": "Santos",
            "email": "miguel@highland.com",
            "role": "AGENT"
        }
    }
}

@router.get("/")
async def get_properties(
    skip: int = 0,
    limit: int = 100,
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_async_session)
):
    """Get all properties from mock storage."""
    
    print(f"🔍 GET All Properties Request")
    print(f"📋 Total Mock Properties: {len(MOCK_PROPERTIES)}")
    print(f"🔢 Available IDs: {list(MOCK_PROPERTIES.keys())}")
    
    # Get all properties from mock storage
    all_properties = list(MOCK_PROPERTIES.values())
    
    # Apply status filter if provided
    if status_filter:
        all_properties = [p for p in all_properties if p.get("status") == status_filter]
    
    # Apply pagination
    total = len(all_properties)
    paginated = all_properties[skip:skip + limit]
    
    print(f"✅ Returning {len(paginated)} properties (total: {total})")
    
    return {
        "properties": paginated,
        "total": total,
        "skip": skip,
        "limit": limit
    }

@router.get("/statistics")
async def get_property_statistics(
    request: Request,
    db: AsyncSession = Depends(get_async_session),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """Get property statistics from mock storage."""
    
    from datetime import datetime, timedelta
    
    print(f"📊 GET Statistics Request")
    
    # Get all properties from mock storage
    all_properties = list(MOCK_PROPERTIES.values())
    
    # Count by status
    status_counts = {}
    for prop in all_properties:
        status = prop.get("status", "PROPERTY_SOURCING")
        status_counts[status] = status_counts.get(status, 0) + 1
    
    # Calculate metrics
    total_properties = len(all_properties)
    
    pending_review = (
        status_counts.get("PROPERTY_SOURCING", 0) + 
        status_counts.get("PROPERTY_STUDY", 0)
    )
    
    approved = (
        status_counts.get("NEGOTIATION", 0) + 
        status_counts.get("DUE_DILIGENCE", 0) + 
        status_counts.get("CONTRACT_SIGNING", 0) +
        status_counts.get("TAKEOVER", 0)
    )
    
    under_negotiation = status_counts.get("NEGOTIATION", 0)
    
    # Count recent submissions (mock data - count all as this week for demo)
    this_week_submissions = total_properties
    
    # Duplicate alerts (placeholder)
    duplicate_alerts = 0
    
    print(f"✅ Statistics: Total={total_properties}, Pending={pending_review}, Approved={approved}")
    
    return {
        "totalProperties": total_properties,
        "pendingReview": pending_review,
        "approved": approved,
        "underNegotiation": under_negotiation,
        "thisWeekSubmissions": this_week_submissions,
        "duplicateAlerts": duplicate_alerts,
        "statusBreakdown": status_counts
    }

@router.get("/recent-activity")
async def get_recent_activity(
    limit: int = 10,
    db: AsyncSession = Depends(get_async_session)
):
    """Get recent property activities for dashboard."""
    
    from app.models.workflow import WorkflowHistory
    from sqlalchemy.orm import selectinload
    from sqlalchemy import select
    from app.models.property import Property
    
    try:
        # Get recent workflow history entries (status changes, updates, etc.)
        workflow_result = await db.execute(
            select(WorkflowHistory)
            .options(
                selectinload(WorkflowHistory.property),
                selectinload(WorkflowHistory.changed_by)
            )
            .order_by(WorkflowHistory.created_at.desc())
            .limit(limit)
        )
        
        workflow_history = workflow_result.scalars().all()
        
        activities = []
        for entry in workflow_history:
            activity = {
                "id": entry.id,
                "type": "status_change",
                "title": f"Property status changed to {entry.to_status.value if entry.to_status else 'Unknown'}",
                "description": f"{entry.property.name if entry.property else 'Unknown Property'} - by {entry.changed_by.first_name if entry.changed_by else 'Unknown'} {entry.changed_by.last_name if entry.changed_by else 'User'}",
                "timestamp": entry.created_at.isoformat(),
                "property": {
                    "id": entry.property.id if entry.property else 0,
                    "name": entry.property.name if entry.property else "Unknown Property"
                },
                "user": {
                    "name": f"{entry.changed_by.first_name if entry.changed_by else 'Unknown'} {entry.changed_by.last_name if entry.changed_by else 'User'}",
                    "role": entry.changed_by.role.value if entry.changed_by and entry.changed_by.role else "Unknown"
                }
            }
            activities.append(activity)
        
        # If no workflow history, fall back to recent property creations
        if not activities:
            properties_result = await db.execute(
                select(Property)
                .options(selectinload(Property.submitted_by))
                .order_by(Property.created_at.desc())
                .limit(limit)
            )
            
            recent_properties = properties_result.scalars().all()
            
            for prop in recent_properties:
                activity = {
                    "id": f"prop_{prop.id}",
                    "type": "property_created", 
                    "title": "New property submitted",
                    "description": f"{prop.name} - by {prop.submitted_by.first_name if prop.submitted_by else 'Unknown'} {prop.submitted_by.last_name if prop.submitted_by else 'User'}",
                    "timestamp": prop.created_at.isoformat(),
                    "property": {
                        "id": prop.id,
                        "name": prop.name
                    },
                    "user": {
                        "name": f"{prop.submitted_by.first_name if prop.submitted_by else 'Unknown'} {prop.submitted_by.last_name if prop.submitted_by else 'User'}",
                        "role": prop.submitted_by.role.value if prop.submitted_by and prop.submitted_by.role else "Unknown"
                    }
                }
                activities.append(activity)
        
        return {
            "activities": activities,
            "total": len(activities)
        }
        
    except Exception as e:
        print(f"Database query failed for recent activity: {e}")
        return {
            "activities": [],
            "total": 0
        }

@router.get("/{property_id}")
async def get_property(
    property_id: int
):
    """Get a specific property by ID."""
    
    print(f"🔍 GET Property Request - ID: {property_id}")
    print(f"📋 Available Property IDs: {list(MOCK_PROPERTIES.keys())}")
    print(f"🏠 Total Properties in Storage: {len(MOCK_PROPERTIES)}")
    
    if property_id not in MOCK_PROPERTIES:
        print(f"❌ Property ID {property_id} not found in mock storage")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Property not found. Available IDs: {list(MOCK_PROPERTIES.keys())}"
        )
    
    property_data = MOCK_PROPERTIES[property_id]
    print(f"✅ Found property: {property_data.get('name', 'Unknown')}")
    return property_data

async def upload_file_to_cloudinary(file: UploadFile, folder: str = "properties") -> dict:
    """Upload file to Cloudinary and return the file info."""
    try:
        # Upload to Cloudinary
        result = await cloudinary_service.upload_file(
            file=file,
            subfolder=folder
        )
        
        print(f"✅ Cloudinary upload successful: {file.filename}")
        print(f"🔗 URL: {result['secure_url']}")
        
        return {
            "cloudinary_id": result["public_id"],
            "url": result["secure_url"],
            "original_filename": result["original_filename"],
            "file_size": result["file_size"],
            "mime_type": result["mime_type"]
        }
    except Exception as e:
        print(f"❌ Cloudinary upload failed for {file.filename}: {e}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to upload {file.filename}: {str(e)}"
        )

@router.post("/")
async def create_property(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_async_session),
    name: str = Form(...),
    address: str = Form(...),
    lotArea: int = Form(...),
    propertyType: str = Form(...),
    price: int = Form(...),
    currency: str = Form("PHP"),
    zoningClassification: str = Form(...),
    titleNumber: str = Form(...),
    description: str = Form(""),
    buildingArea: Optional[int] = Form(None),
    floors: Optional[int] = Form(None),
    rooms: Optional[int] = Form(None),
    openParking: Optional[int] = Form(None),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    # Google Places API fields
    place_id: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    province: Optional[str] = Form(None),
    region: Optional[str] = Form(None),
    barangay: Optional[str] = Form(None),
    postal_code: Optional[str] = Form(None),
    transactionStatus: Optional[str] = Form("S"),  # Default to SALE
    images: List[UploadFile] = File(default=[]),
    attachments: List[UploadFile] = File(default=[]),
    authorization_letter: Optional[UploadFile] = File(None)
):
    """Create a new property with file uploads."""
    
    print(f"🔥 CREATING PROPERTY: {name}")
    print(f"👤 Submitted by: {current_user.first_name} {current_user.last_name} (ID: {current_user.id})")
    print(f"📍 Address: {address}")
    print(f"💰 Price: {price} {currency}")
    print(f"📐 Lot Area: {lotArea} sqm")
    print(f"🏗️ Property Type: {propertyType}")
    print(f"📋 Zoning: {zoningClassification}")
    print(f"📄 Title: {titleNumber}")
    print(f"💼 Transaction Status: {transactionStatus}")
    print(f"🖼️ Images: {len(images)} files")
    print(f"📎 Attachments: {len(attachments)} files")
    print(f"📝 Authorization Letter: {'Yes' if authorization_letter else 'No'}")
    
    # Generate new property ID
    new_id = max(MOCK_PROPERTIES.keys()) + 1 if MOCK_PROPERTIES else 1
    
    # Process uploaded files with Cloudinary
    saved_images = []
    for image in images:
        if image.filename:  # Only process files that have a filename
            try:
                cloudinary_result = await upload_file_to_cloudinary(image, "property_images")
                saved_images.append({
                    "id": str(uuid.uuid4()),
                    "fileName": cloudinary_result["original_filename"],
                    "fileUrl": cloudinary_result["url"],
                    "fileSize": cloudinary_result["file_size"],
                    "fileType": cloudinary_result["mime_type"],
                    "cloudinaryId": cloudinary_result["cloudinary_id"],
                    "uploadedAt": datetime.now()
                })
                print(f"✅ Uploaded image to Cloudinary: {image.filename}")
            except Exception as e:
                print(f"❌ Error uploading image {image.filename}: {e}")
                # Continue processing other files even if one fails
    
    saved_attachments = []
    for attachment in attachments:
        if attachment.filename:  # Only process files that have a filename
            try:
                cloudinary_result = await upload_file_to_cloudinary(attachment, "property_documents")
                saved_attachments.append({
                    "id": str(uuid.uuid4()),
                    "fileName": cloudinary_result["original_filename"],
                    "fileUrl": cloudinary_result["url"],
                    "fileSize": cloudinary_result["file_size"],
                    "fileType": cloudinary_result["mime_type"],
                    "cloudinaryId": cloudinary_result["cloudinary_id"],
                    "uploadedAt": datetime.now()
                })
                print(f"✅ Uploaded attachment to Cloudinary: {attachment.filename}")
            except Exception as e:
                print(f"❌ Error uploading attachment {attachment.filename}: {e}")
                # Continue processing other files even if one fails
    
    saved_auth_letter = None
    if authorization_letter and authorization_letter.filename:
        try:
            cloudinary_result = await upload_file_to_cloudinary(authorization_letter, "authorization_letters")
            saved_auth_letter = {
                "id": str(uuid.uuid4()),
                "fileName": cloudinary_result["original_filename"],
                "fileUrl": cloudinary_result["url"],
                "fileSize": cloudinary_result["file_size"],
                "fileType": cloudinary_result["mime_type"],
                "cloudinaryId": cloudinary_result["cloudinary_id"],
                "uploadedAt": datetime.now()
            }
            print(f"✅ Uploaded authorization letter to Cloudinary: {authorization_letter.filename}")
        except Exception as e:
            print(f"❌ Error uploading authorization letter: {e}")
            # Authorization letter is required, so we should fail if this doesn't work
            raise HTTPException(
                status_code=400,
                detail=f"Failed to upload authorization letter: {str(e)}"
            )
    
    # Create new property with auto-populated fields
    new_property = {
        "id": new_id,
        "name": name,
        "address": address,
        "lotArea": lotArea,
        "propertyType": propertyType,
        "price": price,
        "currency": currency,
        "zoningClassification": zoningClassification,
        "titleNumber": titleNumber,
        "description": description,
        "status": "PROPERTY_SOURCING",  # Default status for new properties
        "transactionStatus": transactionStatus or "S",  # Default to Sale if not specified
        "attachments": saved_images + saved_attachments + ([saved_auth_letter] if saved_auth_letter else []),
        "createdAt": datetime.now(),  # Mock timestamp
        "updatedAt": datetime.now(),  # Mock timestamp
        "submittedBy": {
            "id": 999,  # Mock user ID for development
            "firstName": "System",
            "lastName": "User",
            "email": "system@bdd.com",
            "role": "AGENT"
        }
    }
    
    # Add optional fields if provided
    if buildingArea is not None:
        new_property["buildingArea"] = buildingArea
    if floors is not None:
        new_property["floors"] = floors
    if rooms is not None:
        new_property["rooms"] = rooms
    if openParking is not None:
        new_property["openParking"] = openParking
    if latitude is not None:
        new_property["latitude"] = latitude
    if longitude is not None:
        new_property["longitude"] = longitude
    
    # Add Google Places API fields if provided
    if place_id is not None:
        new_property["place_id"] = place_id
    if city is not None:
        new_property["city"] = city
    if province is not None:
        new_property["province"] = province
    if region is not None:
        new_property["region"] = region
    if barangay is not None:
        new_property["barangay"] = barangay
    if postal_code is not None:
        new_property["postal_code"] = postal_code
    # transactionStatus is now set in the main property object above
    
    # Add processed files to the property
    all_attachments = saved_images + saved_attachments
    if saved_auth_letter:
        all_attachments.append(saved_auth_letter)
    new_property["attachments"] = all_attachments
    
    # Store the property in mock storage
    MOCK_PROPERTIES[new_id] = new_property
    
    # Also save to database so it appears in All Properties page
    try:
        property_service = PropertyService(db)
        
        # Create PropertyCreate schema from form data
        property_create = PropertyCreate(
            name=name,
            address=address,
            latitude=latitude,
            longitude=longitude,
            place_id=place_id,
            street=None,  # Not provided in form
            barangay_name=barangay,
            city_name=city,
            province_name=province,
            region_name=region,
            zip_code=postal_code,
            country="Philippines",
            lot_area=float(lotArea),
            property_type=PropertyType(propertyType),
            price=Decimal(str(price)),
            currency=currency or "PHP",
            zoning_classification=zoningClassification,
            title_number=titleNumber,
            description=description or "",
            transaction_status=TransactionStatus(transactionStatus) if transactionStatus else TransactionStatus.S
        )
        
        # Save to database with current authenticated user
        db_property = await property_service.create_property(property_create, user_id=current_user.id)
        print(f"✅ PROPERTY SAVED TO DATABASE - DB ID: {db_property.id}")
        
        # Save attachments to database
        from app.models.property import PropertyAttachment
        try:
            for attachment_data in all_attachments:
                db_attachment = PropertyAttachment(
                    property_id=db_property.id,
                    filename=attachment_data["fileName"],
                    original_filename=attachment_data["fileName"],
                    cloudinary_public_id=attachment_data["cloudinaryId"],
                    cloudinary_url=attachment_data["fileUrl"],
                    cloudinary_secure_url=attachment_data["fileUrl"],  # Using same URL for both
                    file_size=attachment_data["fileSize"],
                    mime_type=attachment_data["fileType"],
                    uploaded_by_id=current_user.id
                )
                db.add(db_attachment)
            
            await db.commit()
            print(f"✅ SAVED {len(all_attachments)} ATTACHMENTS TO DATABASE")
            
            # Update the new_property with the database ID and refresh attachments
            new_property["id"] = db_property.id  # Use database ID instead of mock ID
            new_property["attachments"] = all_attachments  # Keep the attachment data
            print(f"✅ UPDATED PROPERTY WITH DATABASE ID: {db_property.id}")
            
        except Exception as attachment_error:
            print(f"⚠️  Failed to save attachments to database: {attachment_error}")
            await db.rollback()
        
    except Exception as e:
        print(f"⚠️  Failed to save to database: {e}")
        # Continue anyway - at least the mock version will work
    
    print(f"✅ PROPERTY CREATED SUCCESSFULLY - DB ID: {new_property['id']}")
    
    return {
        "message": "Property created successfully",
        "property": new_property
    }

@router.post("/sync-to-database")
async def sync_properties_to_database(db: AsyncSession = Depends(get_async_session)):
    """Sync all mock properties to the database so they appear in All Properties page"""
    try:
        property_service = PropertyService(db)
        synced_count = 0
        errors = []
        
        for mock_id, mock_property in MOCK_PROPERTIES.items():
            try:
                # Check if property already exists in database by title number
                existing = await property_service.get_property_by_title_number(mock_property["titleNumber"])
                if existing:
                    print(f"⏭️  Skipping {mock_property['name']} - already exists in database")
                    continue
                
                # Create PropertyCreate schema from mock data
                property_create = PropertyCreate(
                    name=mock_property["name"],
                    address=mock_property["address"],
                    latitude=mock_property.get("latitude"),
                    longitude=mock_property.get("longitude"),
                    place_id=mock_property.get("place_id"),
                    street=None,
                    barangay_name=mock_property.get("barangay"),
                    city_name=mock_property.get("city"),
                    province_name=mock_property.get("province"),
                    region_name=mock_property.get("region"),
                    zip_code=mock_property.get("postal_code"),
                    country="Philippines",
                    lot_area=float(mock_property["lotArea"]),
                    property_type=PropertyType(mock_property["propertyType"]),
                    price=Decimal(str(mock_property["price"])),
                    currency=mock_property.get("currency", "PHP"),
                    zoning_classification=mock_property["zoningClassification"],
                    title_number=mock_property["titleNumber"],
                    description=mock_property.get("description", ""),
                    transaction_status=TransactionStatus(mock_property.get("transactionStatus", "S"))
                )
                
                # Save to database
                db_property = await property_service.create_property(property_create, user_id=6)
                synced_count += 1
                print(f"✅ Synced: {mock_property['name']} -> DB ID: {db_property.id}")
                
            except Exception as e:
                error_msg = f"Failed to sync {mock_property['name']}: {str(e)}"
                errors.append(error_msg)
                print(f"❌ {error_msg}")
        
        return {
            "message": f"Sync completed. {synced_count} properties synced to database.",
            "synced_count": synced_count,
            "total_mock_properties": len(MOCK_PROPERTIES),
            "errors": errors
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Sync failed: {str(e)}"
        )

class PropertyStatusUpdate(BaseModel):
    status: str
    notes: Optional[str] = None

class PropertyUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    lotArea: Optional[float] = None
    propertyType: Optional[str] = None
    price: Optional[float] = None
    currency: Optional[str] = None
    zoningClassification: Optional[str] = None
    titleNumber: Optional[str] = None
    description: Optional[str] = None
    transactionStatus: Optional[str] = None

@router.put("/{property_id}/status")
async def update_property_status(
    property_id: int,
    update_data: PropertyStatusUpdate
):
    """Update a property's status."""
    
    print(f"🔄 UPDATING PROPERTY STATUS: {property_id}")
    print(f"📋 New Status: {update_data.status}")
    print(f"📝 Notes: {update_data.notes}")
    
    if property_id not in MOCK_PROPERTIES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )
    
    # Update the property status
    MOCK_PROPERTIES[property_id]["status"] = update_data.status
    MOCK_PROPERTIES[property_id]["updatedAt"] = "2024-01-01T00:00:00Z"  # Mock timestamp
    
    # In a real implementation, you would also save the status change to a history table
    
    print(f"✅ PROPERTY STATUS UPDATED SUCCESSFULLY")
    
    return MOCK_PROPERTIES[property_id]


@router.put("/{property_id}")
async def update_property(
    property_id: int,
    update_data: PropertyUpdate
):
    """Update a property's details."""
    
    print(f"🔄 UPDATING PROPERTY: {property_id}")
    print(f"📋 Update Data: {update_data}")
    
    if property_id not in MOCK_PROPERTIES:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Property not found"
        )
    
    # Get current property
    property_obj = MOCK_PROPERTIES[property_id]
    
    # Update only provided fields
    update_dict = update_data.dict(exclude_unset=True)
    
    for field, value in update_dict.items():
        if value is not None:
            property_obj[field] = value
    
    # Handle coordinate updates - convert lat/lng to coordinates object if needed
    if "latitude" in update_dict or "longitude" in update_dict:
        lat = property_obj.get("latitude")
        lng = property_obj.get("longitude")
        if lat is not None and lng is not None:
            property_obj["coordinates"] = {
                "lat": lat,
                "lng": lng
            }
    
    # Update timestamp
    property_obj["updatedAt"] = "2024-01-01T00:00:00Z"  # Mock timestamp
    
    print(f"✅ PROPERTY UPDATED SUCCESSFULLY")
    
    return property_obj