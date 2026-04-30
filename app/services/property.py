from datetime import datetime
from typing import List, Optional, Tuple
from sqlalchemy import select, func, or_, and_, asc, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.property import Property, PropertyAttachment
from app.models.user import User
from app.models.workflow import PropertyStatus, WorkflowHistory
from app.schemas.property import PropertyCreate, PropertyUpdate


_SORTABLE_COLUMNS = {
    "created_at": Property.created_at,
    "name": Property.name,
    "price": Property.price,
    "status": Property.status,
}


def _apply_property_filters(
    stmt,
    *,
    search: Optional[str] = None,
    statuses: Optional[List[str]] = None,
    property_types: Optional[List[str]] = None,
    transaction_statuses: Optional[List[str]] = None,
    submitted_by_id: Optional[int] = None,
    reviewer_id: Optional[int] = None,
    referred_by: Optional[str] = None,
    price_min: Optional[float] = None,
    price_max: Optional[float] = None,
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    bookmarked_only: bool = False,
):
    """Apply WHERE clauses shared by list and count queries."""
    if search:
        like = f"%{search.lower()}%"
        stmt = stmt.where(
            or_(
                func.lower(Property.name).like(like),
                func.lower(Property.address).like(like),
            )
        )
    if statuses:
        stmt = stmt.where(Property.status.in_(statuses))
    if property_types:
        stmt = stmt.where(Property.property_type.in_(property_types))
    if transaction_statuses:
        stmt = stmt.where(Property.transaction_status.in_(transaction_statuses))
    if submitted_by_id is not None:
        stmt = stmt.where(Property.submitted_by_id == submitted_by_id)
    if reviewer_id is not None:
        stmt = stmt.where(Property.reviewer_id == reviewer_id)
    if referred_by:
        stmt = stmt.where(func.lower(Property.referred_by).like(f"%{referred_by.lower()}%"))
    if price_min is not None:
        stmt = stmt.where(Property.price >= price_min)
    if price_max is not None:
        stmt = stmt.where(Property.price <= price_max)
    if date_from is not None:
        stmt = stmt.where(Property.created_at >= date_from)
    if date_to is not None:
        stmt = stmt.where(Property.created_at <= date_to)
    if bookmarked_only:
        stmt = stmt.where(Property.is_marked.is_(True))
    return stmt


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
                selectinload(Property.workflow_history).selectinload(WorkflowHistory.changed_by)
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
        transaction_status: Optional[str] = None,
    ) -> List[Property]:
        """Get properties with optional filtering (legacy single-value filters)."""
        statuses = [status.value if hasattr(status, "value") else status] if status else None
        property_types = [property_type] if property_type else None
        transaction_statuses = [transaction_status] if transaction_status else None
        properties, _ = await self.search_properties(
            skip=skip,
            limit=limit,
            statuses=statuses,
            property_types=property_types,
            transaction_statuses=transaction_statuses,
            submitted_by_id=submitted_by_id,
            reviewer_id=reviewer_id,
        )
        return properties

    async def search_properties(
        self,
        *,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        statuses: Optional[List[str]] = None,
        property_types: Optional[List[str]] = None,
        transaction_statuses: Optional[List[str]] = None,
        submitted_by_id: Optional[int] = None,
        reviewer_id: Optional[int] = None,
        referred_by: Optional[str] = None,
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        bookmarked_only: bool = False,
        sort_by: str = "created_at",
        sort_order: str = "desc",
    ) -> Tuple[List[Property], int]:
        """Filter + sort + paginate properties; returns (rows, total_count)."""
        sort_column = _SORTABLE_COLUMNS.get(sort_by, Property.created_at)
        order_fn = asc if sort_order == "asc" else desc

        list_stmt = (
            select(Property)
            .options(
                selectinload(Property.submitted_by),
                selectinload(Property.reviewer),
                selectinload(Property.attachments),
            )
        )
        list_stmt = _apply_property_filters(
            list_stmt,
            search=search,
            statuses=statuses,
            property_types=property_types,
            transaction_statuses=transaction_statuses,
            submitted_by_id=submitted_by_id,
            reviewer_id=reviewer_id,
            referred_by=referred_by,
            price_min=price_min,
            price_max=price_max,
            date_from=date_from,
            date_to=date_to,
            bookmarked_only=bookmarked_only,
        )
        list_stmt = list_stmt.order_by(order_fn(sort_column), desc(Property.id)).offset(skip).limit(limit)

        count_stmt = _apply_property_filters(
            select(func.count(Property.id)),
            search=search,
            statuses=statuses,
            property_types=property_types,
            transaction_statuses=transaction_statuses,
            submitted_by_id=submitted_by_id,
            reviewer_id=reviewer_id,
            referred_by=referred_by,
            price_min=price_min,
            price_max=price_max,
            date_from=date_from,
            date_to=date_to,
            bookmarked_only=bookmarked_only,
        )

        rows_result = await self.db.execute(list_stmt)
        count_result = await self.db.execute(count_stmt)
        return list(rows_result.scalars().all()), int(count_result.scalar() or 0)

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