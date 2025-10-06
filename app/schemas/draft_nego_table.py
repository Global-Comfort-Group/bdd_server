from typing import Any, Dict, List, Optional
from pydantic import BaseModel
from datetime import datetime

class DraftNegoTableBase(BaseModel):
    property_id: int
    form_data: Dict[str, Any]
    negotiations_data: List[Dict[str, Any]] = []
    financial_data: Dict[str, Any] = {}
    step_completed: str = "basic-info"

class DraftNegoTableCreate(DraftNegoTableBase):
    pass

class DraftNegoTableUpdate(BaseModel):
    form_data: Optional[Dict[str, Any]] = None
    negotiations_data: Optional[List[Dict[str, Any]]] = None
    financial_data: Optional[Dict[str, Any]] = None
    step_completed: Optional[str] = None

class DraftNegoTable(DraftNegoTableBase):
    id: int
    user_id: int
    last_auto_save: datetime
    created_at: datetime
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class DraftNegoTableWithProperty(DraftNegoTable):
    from app.schemas.property import Property
    property: Property
    
    class Config:
        from_attributes = True