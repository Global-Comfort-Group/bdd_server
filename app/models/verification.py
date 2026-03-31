"""
Verification code model for email and SMS verification
"""
from datetime import datetime, timedelta
from enum import Enum
from sqlalchemy import String, DateTime, Boolean, Integer, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class VerificationType(str, Enum):
    """Types of verification"""
    EMAIL = "EMAIL"
    SMS = "SMS"
    PASSWORD_RESET = "PASSWORD_RESET"
    TWO_FACTOR = "TWO_FACTOR"


class VerificationCode(Base):
    """Model for storing verification codes"""
    __tablename__ = "verification_codes"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # User identification
    email: Mapped[str] = mapped_column(String(255), nullable=True, index=True)
    phone_number: Mapped[str] = mapped_column(String(20), nullable=True, index=True)
    
    # Verification details
    code: Mapped[str] = mapped_column(String(10), nullable=False)
    verification_type: Mapped[VerificationType] = mapped_column(
        SQLEnum(VerificationType), 
        nullable=False
    )
    
    # Status
    is_used: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_expired: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        default=datetime.utcnow, 
        nullable=False
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime, 
        nullable=False
    )
    used_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)
    
    # Attempts tracking (prevent brute force)
    attempts: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    @property
    def is_valid(self) -> bool:
        """Check if code is still valid"""
        return (
            not self.is_used 
            and not self.is_expired 
            and self.expires_at > datetime.utcnow()
            and self.attempts < 5  # Max 5 attempts
        )
    
    @staticmethod
    def create_expiry_time(minutes: int = 15) -> datetime:
        """Create expiry time (default 15 minutes)"""
        return datetime.utcnow() + timedelta(minutes=minutes)

