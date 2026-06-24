"""
Pydantic schemas for per-property KMZ uploads.
"""
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class PropertyKMZRead(BaseModel):
    """KMZ file metadata (used for list/detail responses; excludes the full
    GeoJSON payload which can be large)."""
    id: int
    property_id: int
    filename: str
    file_size: Optional[int] = None
    feature_count: int
    uploaded_by: Optional[int] = None
    upload_date: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PropertyKMZFeatures(BaseModel):
    """The parsed GeoJSON FeatureCollection for a KMZ, ready for the map view."""
    id: int
    property_id: int
    filename: str
    feature_count: int
    geojson: dict[str, Any]
