"""
Server-side store for in-flight Excel import previews.

The preview endpoint parses an uploaded workbook and hands back a token; the
confirm endpoint later exchanges that token for the parsed rows. That handover
has to survive:

  * **multiple workers** — the app runs `uvicorn --workers 2`, so preview and
    confirm are frequently served by different processes;
  * **restarts and redeploys** between the two calls.

An in-process dict satisfied neither and failed roughly half the time in
staging with "Import token not found or expired", so the rows live here
instead.
"""
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class PropertyImportToken(Base):
    __tablename__ = "property_import_tokens"

    token: Mapped[str] = mapped_column(String(36), primary_key=True)
    # The parsed rows exactly as the preview returned them, duplicate flags
    # included, so confirm acts on what the admin was actually shown.
    rows: Mapped[Any] = mapped_column(JSONB, nullable=False)
    source_file: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    created_by_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)

    def __repr__(self) -> str:
        return f"<PropertyImportToken {self.token} expires={self.expires_at}>"
