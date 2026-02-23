from datetime import datetime
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, Field

# Negotiation data row schema
class NegotiationDataRow(BaseModel):
    header: str
    value: Optional[str] = None
    agreed_amount: Optional[float] = None
    for_nego: Optional[float] = None
    difference_percentage: Optional[float] = None  # Calculated: (for_nego - agreed_amount) / agreed_amount * 100

# Base schemas for Negotiation Chronicle Attachment
class NegotiationChronicleAttachmentBase(BaseModel):
    nego_table_id: int
    filename: str
    file_type: str
    parsed_data: List[Dict[str, Any]]

class NegotiationChronicleAttachmentCreate(NegotiationChronicleAttachmentBase):
    file_url: str
    file_size: Optional[int] = None
    uploaded_by: int

class NegotiationChronicleAttachmentUpdate(BaseModel):
    parsed_data: Optional[List[Dict[str, Any]]] = None

class NegotiationChronicleAttachment(NegotiationChronicleAttachmentBase):
    id: int
    file_url: str
    file_size: Optional[int] = None
    uploaded_by: Union[int, None] = Field(default=None)  # Explicitly allow None for in-memory attachments
    upload_date: Union[datetime, str]  # Accept both datetime objects and ISO strings
    created_at: Union[datetime, str]  # Accept both datetime objects and ISO strings
    updated_at: Union[datetime, str, None] = None  # Accept both datetime objects and ISO strings
    ai_result: Optional[Dict[str, Any]] = None  # Full Gemini AI analysis result (timeline mode)

    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat() if isinstance(v, datetime) else v
        }

# Response schema for file upload
class FileUploadResponse(BaseModel):
    success: bool
    message: str
    attachment_id: Optional[int] = None
    parsed_data: Optional[List[Dict[str, Any]]] = None

