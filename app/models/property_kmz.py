"""
PropertyKMZ model.

Stores a KMZ (Google Earth) file uploaded against a property, along with the
GeoJSON FeatureCollection parsed from it. A property may have several KMZ files
(e.g. successive surveys), so this is a one-to-many relationship.

The raw KMZ lives in OSS (re-downloadable via a signed URL); the parsed GeoJSON
is cached here so the Property View can render buildings, infra, and pins
without re-downloading and unzipping the archive each time.
"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class PropertyKMZ(Base):
    __tablename__ = "property_kmz_files"

    id = Column(Integer, primary_key=True, index=True)
    property_id = Column(Integer, ForeignKey("properties.id"), nullable=False, index=True)

    # File metadata
    filename = Column(String(255), nullable=False)          # original filename
    oss_object_key = Column(String(500), nullable=False)    # OSS key for signed URL / deletion
    file_url = Column(String(500), nullable=False)          # stored (secure) URL
    file_size = Column(Integer)                             # in bytes
    file_sha256 = Column(String(64), nullable=True, index=True)  # for duplicate detection

    # Parsed GeoJSON FeatureCollection (see app/services/kmz_parser.py)
    parsed_data = Column(JSON, nullable=False)
    # Convenience count so the list endpoint need not load the full GeoJSON
    feature_count = Column(Integer, nullable=False, server_default="0")

    # Metadata
    uploaded_by = Column(Integer, ForeignKey("user.id"), nullable=True)
    upload_date = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    property = relationship("Property", back_populates="kmz_files")
    uploader = relationship("User")
