from typing import List, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.property import Property, PropertyAttachment
from app.models.user import User
from app.models.workflow import PropertyStatus
from app.schemas.property import PropertyCreate, PropertyUpdate


class PropertyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_property(self, property_id: int) -> Optional[Property]:
        """Get a single property by ID with all relationships loaded."""
        stmt = (
            select(Property)
            .options(
                selectinload(Property.submitted_by),
                selectinload(Property.reviewer),
                selectinload(Property.attachments),
                selectinload(Property.workflow_history).selectinload(property.changed_by)
            )
            .where(Property.id == property_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_properties(
        self,
        skip: int = 0,
        limit: int = 100,
        status: Optional[PropertyStatus] = None,
        submitted_by_id: Optional[int] = None,
        reviewer_id: Optional[int] = None,
        property_type: Optional[str] = None,
    ) -> List[Property]:
        """Get properties with optional filtering."""
        stmt = (
            select(Property)
            .options(selectinload(Property.submitted_by))
            .offset(skip)
            .limit(limit)
        )
        
        if status:
            stmt = stmt.where(Property.status == status)
        if submitted_by_id:
            stmt = stmt.where(Property.submitted_by_id == submitted_by_id)
        if reviewer_id:
            stmt = stmt.where(Property.reviewer_id == reviewer_id)
        if property_type:
            stmt = stmt.where(Property.property_type == property_type)
            
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def create_property(
        self, property_data: PropertyCreate, user_id: int
    ) -> Property:
        """Create a new property."""
        property_dict = property_data.model_dump()
        property_dict["submitted_by_id"] = user_id
        property_dict["status"] = PropertyStatus.PROPERTY_SOURCING
        
        db_property = Property(**property_dict)
        self.db.add(db_property)
        await self.db.commit()
        await self.db.refresh(db_property)
        return db_property

    async def update_property(
        self, property_id: int, property_data: PropertyUpdate
    ) -> Optional[Property]:
        """Update an existing property."""
        property_obj = await self.get_property(property_id)
        if not property_obj:
            return None
            
        update_data = property_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(property_obj, field, value)
            
        await self.db.commit()
        await self.db.refresh(property_obj)
        return property_obj

    async def delete_property(self, property_id: int) -> bool:
        """Delete a property."""
        property_obj = await self.get_property(property_id)
        if not property_obj:
            return False
            
        await self.db.delete(property_obj)
        await self.db.commit()
        return True

    async def assign_reviewer(
        self, property_id: int, reviewer_id: int
    ) -> Optional[Property]:
        """Assign a reviewer to a property."""
        property_obj = await self.get_property(property_id)
        if not property_obj:
            return None
            
        # Verify reviewer exists
        reviewer_stmt = select(User).where(User.id == reviewer_id)
        reviewer_result = await self.db.execute(reviewer_stmt)
        reviewer = reviewer_result.scalar_one_or_none()
        if not reviewer:
            return None
            
        property_obj.reviewer_id = reviewer_id
        await self.db.commit()
        await self.db.refresh(property_obj)
        return property_obj

    async def get_properties_count(
        self,
        status: Optional[PropertyStatus] = None,
        submitted_by_id: Optional[int] = None,
    ) -> int:
        """Get total count of properties with optional filtering."""
        stmt = select(func.count(Property.id))
        
        if status:
            stmt = stmt.where(Property.status == status)
        if submitted_by_id:
            stmt = stmt.where(Property.submitted_by_id == submitted_by_id)
            
        result = await self.db.execute(stmt)
        return result.scalar()

    async def get_property_by_title_number(self, title_number: str) -> Optional[Property]:
        """Get property by title number."""
        stmt = select(Property).where(Property.title_number == title_number)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    # File attachment methods
    async def add_attachment(
        self,
        property_id: int,
        filename: str,
        original_filename: str,
        file_path: str,
        file_size: int,
        mime_type: str,
        uploaded_by_id: int,
    ) -> PropertyAttachment:
        """Add a file attachment to a property."""
        attachment = PropertyAttachment(
            property_id=property_id,
            filename=filename,
            original_filename=original_filename,
            file_path=file_path,
            file_size=file_size,
            mime_type=mime_type,
            uploaded_by_id=uploaded_by_id,
        )
        self.db.add(attachment)
        await self.db.commit()
        await self.db.refresh(attachment)
        return attachment

    async def get_property_attachments(
        self, property_id: int
    ) -> List[PropertyAttachment]:
        """Get all attachments for a property."""
        stmt = (
            select(PropertyAttachment)
            .where(PropertyAttachment.property_id == property_id)
            .order_by(PropertyAttachment.uploaded_at)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()