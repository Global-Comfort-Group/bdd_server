from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class DraftNegoTable(Base):
    __tablename__ = "draft_nego_tables"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    
    # Store form data as JSON for flexibility
    form_data = Column(JSON, nullable=False)
    negotiations_data = Column(JSON, default=[])
    financial_data = Column(JSON, default={})
    
    # Metadata
    step_completed = Column(String(50), default="basic-info")  # basic-info, timeline, financial, review
    last_auto_save = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    property = relationship("Property")
    user = relationship("User")