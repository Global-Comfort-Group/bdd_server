"""
Staging table for properties parsed out of the BDD monthly Excel file.

An Excel row is a REFERRAL LEAD, not a property. The sheet carries a name, an
address, who referred it, and — on some months — a lot area, floor area and a
lease/sale rate. It carries nothing about price, zoning, property type,
coordinates, title or photos, all of which `properties` requires.

Rather than invent values to satisfy those NOT NULL columns, imported rows land
here first. Every field is nullable except the two the sheet always has, so a
missing value stays missing. An admin fills in what `properties` needs and
promotes the row; only then does a real Property exist.

`review_status` is a plain string rather than a SQLEnum on purpose — this
schema has already migrated zoning_classification to an enum and back again
(5928678ca707, then 48f4018b5e86), and a three-value status is not worth
repeating that.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

# review_status values
IMPORT_PENDING = "PENDING"
IMPORT_PROMOTED = "PROMOTED"
IMPORT_DISCARDED = "DISCARDED"


class PropertyImport(Base):
    __tablename__ = "property_imports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    # --- What the sheet actually provides -------------------------------
    # Only `name` is guaranteed. Everything else is NULL when the sheet had
    # nothing, and NULL means "unknown" — never 0 and never a default.
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    address: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    referred_by: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    referral_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    lot_area: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    building_area: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Kept as text: the column mixes per-sqm rates ("35,000/sqm.") with
    # absolute totals ("94Million"), so it cannot become a number safely.
    lease_raw: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    sale_raw: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    status_hint: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # --- Provenance ------------------------------------------------------
    sheet_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    row_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    source_file: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # --- Review state ----------------------------------------------------
    review_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default=IMPORT_PENDING, server_default=IMPORT_PENDING
    )
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    promoted_property_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("properties.id"), nullable=True
    )

    imported_by_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    promoted_property = relationship("Property", foreign_keys=[promoted_property_id])
    imported_by = relationship("User", foreign_keys=[imported_by_id])

    def __repr__(self) -> str:
        return f"<PropertyImport {self.id} {self.name!r} {self.review_status}>"
