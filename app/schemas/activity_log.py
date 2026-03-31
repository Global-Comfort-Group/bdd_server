from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from app.models.activity_log import ActivityAction, ResourceType


# Base schema
class ActivityLogBase(BaseModel):
    action: ActivityAction
    resource_type: ResourceType
    resource_id: Optional[int] = None
    details: str
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


# For creating activity logs (internal use)
class ActivityLogCreate(ActivityLogBase):
    user_id: Optional[int] = None


# Response schema
class ActivityLogResponse(ActivityLogBase):
    id: int
    user_id: Optional[int]
    created_at: datetime
    
    # Include user information
    user_name: Optional[str] = None
    user_email: Optional[str] = None

    class Config:
        from_attributes = True


# Filters for querying
class ActivityLogFilters(BaseModel):
    user_id: Optional[int] = None
    action: Optional[ActivityAction] = None
    resource_type: Optional[ResourceType] = None
    resource_id: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    limit: int = Field(default=50, le=1000)
    skip: int = Field(default=0, ge=0)

    @field_validator('date_from', mode='before')
    @classmethod
    def parse_date_from(cls, v):
        if v is None or isinstance(v, datetime):
            return v
        try:
            # Accept "YYYY-MM-DD" or full ISO strings
            return datetime.fromisoformat(str(v)[:10]).replace(hour=0, minute=0, second=0, microsecond=0)
        except Exception:
            return None

    @field_validator('date_to', mode='before')
    @classmethod
    def parse_date_to(cls, v):
        if v is None or isinstance(v, datetime):
            return v
        try:
            return datetime.fromisoformat(str(v)[:10]).replace(hour=23, minute=59, second=59, microsecond=999999)
        except Exception:
            return None


# Statistics response
class ActivityStats(BaseModel):
    total_activities: int
    recent_logins: int
    actions_by_type: dict[str, int]
    users_active_today: int
    most_active_users: list[dict]





