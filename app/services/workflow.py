from typing import Dict, List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.property import Property
from app.models.workflow import PropertyStatus, WorkflowHistory
from app.schemas.workflow import StatusUpdateRequest


class WorkflowService:
    """Service for managing property workflow state transitions."""
    
    VALID_TRANSITIONS: Dict[PropertyStatus, List[PropertyStatus]] = {
        PropertyStatus.PROPERTY_SOURCING: [PropertyStatus.PROPERTY_SCREENING_FUNG_SHUI],
        PropertyStatus.PROPERTY_SCREENING_FUNG_SHUI: [
            PropertyStatus.PBY_STUDY,
            PropertyStatus.PROPERTY_SOURCING  # Allow going back
        ],
        PropertyStatus.PBY_STUDY: [
            PropertyStatus.EXECOM,
            PropertyStatus.PROPERTY_SCREENING_FUNG_SHUI  # Allow going back
        ],
        PropertyStatus.EXECOM: [
            PropertyStatus.BOARD_APPROVAL,
            PropertyStatus.PBY_STUDY  # Allow going back
        ],
        PropertyStatus.BOARD_APPROVAL: [
            PropertyStatus.DUE_DILIGENCE,
            PropertyStatus.EXECOM  # Allow going back
        ],
        PropertyStatus.DUE_DILIGENCE: [
            PropertyStatus.NEGOTIATION,
            PropertyStatus.BOARD_APPROVAL  # Allow going back
        ],
        PropertyStatus.NEGOTIATION: [
            PropertyStatus.COL_DOAS_SIGNING,
            PropertyStatus.DUE_DILIGENCE  # Allow going back
        ],
        PropertyStatus.COL_DOAS_SIGNING: [
            PropertyStatus.NEGOTIATION  # Allow going back for corrections
        ],
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    async def transition_status(
        self,
        property_id: int,
        request: StatusUpdateRequest,
        user_id: int,
    ) -> Optional[Property]:
        """
        Transition a property to a new status with validation.
        
        Args:
            property_id: ID of the property to update
            request: Status update request with new status and notes
            user_id: ID of the user making the change
            
        Returns:
            Updated property or None if validation fails
        """
        # Get the property
        stmt = select(Property).where(Property.id == property_id)
        result = await self.db.execute(stmt)
        property_obj = result.scalar_one_or_none()
        
        if not property_obj:
            return None

        # Validate transition
        if not self.is_valid_transition(property_obj.status, request.new_status):
            raise ValueError(
                f"Invalid transition from {property_obj.status} to {request.new_status}"
            )

        # Store the old status
        old_status = property_obj.status

        # Update property status
        property_obj.status = request.new_status

        # Create workflow history entry
        history_entry = WorkflowHistory(
            property_id=property_id,
            from_status=old_status,
            to_status=request.new_status,
            changed_by_id=user_id,
            notes=request.notes,
        )

        self.db.add(history_entry)
        await self.db.commit()
        await self.db.refresh(property_obj)

        return property_obj

    def is_valid_transition(
        self, current_status: PropertyStatus, new_status: PropertyStatus
    ) -> bool:
        """Check if a status transition is valid."""
        valid_next_statuses = self.VALID_TRANSITIONS.get(current_status, [])
        return new_status in valid_next_statuses

    def get_next_valid_statuses(self, current_status: PropertyStatus) -> List[PropertyStatus]:
        """Get all valid next statuses for the current status."""
        return self.VALID_TRANSITIONS.get(current_status, [])

    async def get_property_history(self, property_id: int) -> List[WorkflowHistory]:
        """Get the complete workflow history for a property."""
        stmt = (
            select(WorkflowHistory)
            .options(selectinload(WorkflowHistory.changed_by))
            .where(WorkflowHistory.property_id == property_id)
            .order_by(WorkflowHistory.created_at)
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_properties_by_status(
        self, status: PropertyStatus, skip: int = 0, limit: int = 100
    ) -> List[Property]:
        """Get all properties with a specific status."""
        stmt = (
            select(Property)
            .options(selectinload(Property.submitted_by))
            .where(Property.status == status)
            .offset(skip)
            .limit(limit)
            .order_by(Property.created_at.desc())
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_workflow_statistics(self) -> Dict[PropertyStatus, int]:
        """Get count of properties in each workflow status."""
        from sqlalchemy import func
        
        stmt = (
            select(Property.status, func.count(Property.id))
            .group_by(Property.status)
        )
        result = await self.db.execute(stmt)
        
        stats = {}
        for status, count in result.all():
            stats[status] = count
            
        # Ensure all statuses are represented
        for status in PropertyStatus:
            if status not in stats:
                stats[status] = 0
                
        return stats