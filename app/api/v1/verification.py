"""
Email and SMS verification endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel, EmailStr
from datetime import datetime
import random

from app.core.database import get_async_session
from app.models.verification import VerificationCode, VerificationType
from app.services.email_service import email_service
from app.services.sms_service import sms_service

router = APIRouter()


# Request/Response Models
class SendEmailVerificationRequest(BaseModel):
    email: EmailStr


class SendSMSVerificationRequest(BaseModel):
    phone_number: str


class VerifyCodeRequest(BaseModel):
    email: EmailStr | None = None
    phone_number: str | None = None
    code: str
    verification_type: VerificationType


class VerificationResponse(BaseModel):
    success: bool
    message: str


# Endpoints
@router.post("/send-email-verification", response_model=VerificationResponse)
async def send_email_verification(
    request: SendEmailVerificationRequest,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Send email verification code
    
    Flow:
    1. Generate 6-digit code
    2. Store in database with expiry (15 minutes)
    3. Send email via email service
    4. Return success
    """
    try:
        # Generate verification code
        code = ''.join([str(random.randint(0, 9)) for _ in range(6)])
        
        # Create verification record
        verification = VerificationCode(
            email=request.email,
            code=code,
            verification_type=VerificationType.EMAIL,
            expires_at=VerificationCode.create_expiry_time(15)
        )
        
        db.add(verification)
        await db.commit()
        
        # Send email
        success = await email_service.send_verification_email(
            to_email=request.email,
            verification_code=code
        )
        
        if not success:
            raise HTTPException(
                status_code=500, 
                detail="Failed to send verification email"
            )
        
        return VerificationResponse(
            success=True,
            message=f"Verification code sent to {request.email}"
        )
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-sms-verification", response_model=VerificationResponse)
async def send_sms_verification(
    request: SendSMSVerificationRequest,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Send SMS verification code
    
    Flow:
    1. Generate 6-digit code
    2. Store in database with expiry (15 minutes)
    3. Send SMS via SMS service
    4. Return success
    """
    try:
        # Generate verification code
        code = sms_service.generate_verification_code(6)
        
        # Create verification record
        verification = VerificationCode(
            phone_number=request.phone_number,
            code=code,
            verification_type=VerificationType.SMS,
            expires_at=VerificationCode.create_expiry_time(15)
        )
        
        db.add(verification)
        await db.commit()
        
        # Send SMS
        success = await sms_service.send_verification_sms(
            phone_number=request.phone_number,
            verification_code=code
        )
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail="Failed to send verification SMS"
            )
        
        return VerificationResponse(
            success=True,
            message=f"Verification code sent to {request.phone_number}"
        )
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/verify-code", response_model=VerificationResponse)
async def verify_code(
    request: VerifyCodeRequest,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Verify email or SMS code
    
    Flow:
    1. Find verification code in database
    2. Check if valid (not expired, not used, attempts < 5)
    3. Mark as used if valid
    4. Return success or error
    """
    try:
        # Build query based on email or phone
        query = select(VerificationCode).where(
            VerificationCode.code == request.code,
            VerificationCode.verification_type == request.verification_type,
            VerificationCode.is_used == False
        )
        
        if request.email:
            query = query.where(VerificationCode.email == request.email)
        elif request.phone_number:
            query = query.where(VerificationCode.phone_number == request.phone_number)
        else:
            raise HTTPException(
                status_code=400,
                detail="Either email or phone_number is required"
            )
        
        result = await db.execute(query)
        verification = result.scalar_one_or_none()
        
        if not verification:
            raise HTTPException(
                status_code=404,
                detail="Verification code not found"
            )
        
        # Increment attempts
        verification.attempts += 1
        
        # Check if valid
        if not verification.is_valid:
            await db.commit()
            
            if verification.attempts >= 5:
                raise HTTPException(
                    status_code=429,
                    detail="Too many attempts. Please request a new code."
                )
            elif verification.expires_at < datetime.utcnow():
                raise HTTPException(
                    status_code=410,
                    detail="Verification code expired. Please request a new code."
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid verification code"
                )
        
        # Mark as used
        verification.is_used = True
        verification.used_at = datetime.utcnow()
        await db.commit()
        
        return VerificationResponse(
            success=True,
            message="Verification successful"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/resend-verification", response_model=VerificationResponse)
async def resend_verification(
    request: SendEmailVerificationRequest | SendSMSVerificationRequest,
    db: AsyncSession = Depends(get_async_session)
):
    """
    Resend verification code
    Rate limit: 1 request per minute
    """
    # This is a simplified version - you'd want to add rate limiting
    # using Redis or similar
    
    if isinstance(request, SendEmailVerificationRequest):
        return await send_email_verification(request, db)
    else:
        return await send_sms_verification(request, db)

