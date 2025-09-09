from __future__ import annotations

from datetime import datetime
from typing import Optional, TYPE_CHECKING
from pydantic import BaseModel

from app.models.enums import PropertyStatus
from app.schemas.user import UserRead

if TYPE_CHECKING:
    from app.schemas.property import PropertyRead


class StatusUpdateRequest(BaseModel):
    new_status: PropertyStatus
    notes: Optional[str] = None


class WorkflowHistoryRead(BaseModel):
    id: int
    property_id: int
    from_status: Optional[PropertyStatus]
    to_status: PropertyStatus
    changed_by_id: int
    notes: Optional[str]
    created_at: datetime
    
    changed_by: Optional[UserRead] = None

    class Config:
        from_attributes = True


class DuplicateCheckRequest(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    title_number: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class DuplicateResult(BaseModel):
    property_id: int
    similarity_score: float
    match_reasons: list[str]
    # TODO: Add property: PropertyRead after fixing circular imports


class DuplicateMergeRequest(BaseModel):
    primary_property_id: int
    duplicate_property_ids: list[int]
    merge_notes: Optional[str] = None


