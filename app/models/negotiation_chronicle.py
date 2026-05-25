from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

class NegotiationChronicleAttachment(Base):
    __tablename__ = "negotiation_chronicle_attachments"
    
    id = Column(Integer, primary_key=True, index=True)
    nego_table_id = Column(Integer, ForeignKey("nego_tables.id"), nullable=False)
    
    # File metadata
    filename = Column(String(255), nullable=False)
    file_url = Column(String(500), nullable=False)  # Cloudinary or local storage URL
    file_type = Column(String(50), nullable=False)  # csv, excel, google_sheets
    file_size = Column(Integer)  # in bytes
    
    # Parsed data stored as JSON
    # Structure: [{"header": "Property Name", "value": "...", "agreed_amount": 0, "for_nego": 0}, ...]
    parsed_data = Column(JSON, nullable=False)

    # Full Gemini AI analysis result (timeline mode)
    ai_result = Column(JSON, nullable=True)

    # Analysis lifecycle: PENDING (uploaded, not analyzed), ANALYZING, COMPLETED, FAILED
    analysis_status = Column(String(20), nullable=False, server_default="PENDING", index=True)
    analyzed_at = Column(DateTime(timezone=True), nullable=True)
    analysis_error = Column(Text, nullable=True)
    file_sha256 = Column(String(64), nullable=True, index=True)

    # Metadata
    uploaded_by = Column(Integer, ForeignKey("user.id"), nullable=True)  # Optional - supports anonymous uploads
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    nego_table = relationship("NegoTable", back_populates="chronicle_attachments")
    uploader = relationship("User")

