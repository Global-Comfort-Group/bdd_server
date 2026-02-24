"""
Authentication endpoints for BDD Property Tracker
Provides JWT-based authentication with account approval workflow
"""
from datetime import datetime, timedelta
from typing import Annotated, Optional

from jose import jwt
from fastapi import APIRouter, Depends, HTTPException, status, Request, File, UploadFile
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, field_validator
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_async_session
from app.models.user import User
from app.models.enums import UserRole, AccountStatus
from app.utils.activity_logger import log_login

router = APIRouter(prefix="/auth", tags=["auth"])

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

# Registration schema
class UserRegister(BaseModel):
    email: EmailStr
    password: str
    firstName: str
    middleName: Optional[str] = None
    lastName: str
    role: UserRole = UserRole.AGENT
    company: Optional[str] = None
    phone: str
    
    @field_validator('phone')
    @classmethod
    def validate_philippines_phone(cls, v: str) -> str:
        import re
        # Philippines phone number patterns:
        # Mobile: 09XXXXXXXXX, +639XXXXXXXXX, 639XXXXXXXXX (starts with 8 or 9)
        # Landline: 0XXXXXXXX, +63XXXXXXXX, 63XXXXXXXX (area codes 2-8, 7-8 digits after area code)
        mobile_pattern = r'^(\+63|63|0)?[89]\d{9}$'
        landline_pattern = r'^(\+63|63|0)?[2-8]\d{7,8}$'
        
        if not (re.match(mobile_pattern, v) or re.match(landline_pattern, v)):
            raise ValueError('Please enter a valid Philippines phone number (e.g., 09171234567, +639171234567, or 021234567)')
        return v

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: timedelta = None):
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm="HS256")
    return encoded_jwt

async def get_user_by_email(db: AsyncSession, email: str):
    """Get user by email."""
    from sqlalchemy import select
    from app.models.user import User
    
    stmt = select(User).where(User.email == email)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()

async def authenticate_user(db: AsyncSession, email: str, password: str):
    """Authenticate user with email and password."""
    try:
        print(f"🔍 Looking up user: {email}")
        user = await get_user_by_email(db, email)
        
        if not user:
            print(f"❌ User not found: {email}")
            return False
        
        print(f"✅ User found: {email}, checking password...")
        if not verify_password(password, user.hashed_password):
            print(f"❌ Password verification failed for: {email}")
            return False
        
        print(f"✅ Password verified, checking account status: {user.account_status}")
        
        # Check if account is approved
        if user.account_status != AccountStatus.APPROVED:
            status_msg = "pending_approval" if user.account_status == AccountStatus.PENDING else "rejected"
            print(f"⚠️ Account not approved: {email} - Status: {status_msg}")
            return status_msg
        
        print(f"✅ Authentication successful for: {email}")
        return user
    except Exception as e:
        print(f"💥 Error in authenticate_user: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

@router.post("/register")
async def register_user(
    user_data: UserRegister,
    db: AsyncSession = Depends(get_async_session)
):
    """Register a new user."""
    # Check if user already exists
    existing_user = await get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = hash_password(user_data.password)
    
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        first_name=user_data.firstName,
        middle_name=user_data.middleName if user_data.middleName else None,
        last_name=user_data.lastName,
        role=user_data.role,
        company=user_data.company if user_data.company else None,
        phone=user_data.phone,
        is_active=True,
        is_superuser=False,
        is_verified=False,
        account_status=AccountStatus.PENDING
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    return {
        "message": "Registration submitted successfully. Your account is pending admin approval.",
        "user": {
            "id": new_user.id,
            "email": new_user.email,
            "first_name": new_user.first_name,
            "last_name": new_user.last_name,
            "role": new_user.role,
            "company": new_user.company,
            "account_status": new_user.account_status,
            "is_active": new_user.is_active
        }
    }

@router.post("/login")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    request: Request,
    db: AsyncSession = Depends(get_async_session)
):
    """Login endpoint that returns a JWT token."""
    try:
        print(f"🔐 Login attempt for: {form_data.username}")
        user = await authenticate_user(db, form_data.username, form_data.password)
        print(f"🔐 Authentication result: {user}")
        
        if not user:
            print(f"❌ Authentication failed for: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Handle account approval status
        if user == "pending_approval":
            print(f"⏳ Account pending approval: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account is pending admin approval. Please wait for approval before logging in.",
            )
        elif user == "rejected":
            print(f"🚫 Account rejected: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Your account has been rejected by an administrator.",
            )
        
        # Create access token
        print(f"✅ Creating access token for: {form_data.username}")
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.id, "role": user.role}, 
            expires_delta=access_token_expires
        )
        
        # Log successful login (don't fail login if logging fails)
        try:
            await log_login(
                db=db,
                user_id=user.id,
                user_email=user.email,
                request=request
            )
            print(f"✅ Login successful for: {form_data.username}")
        except Exception as e:
            # Log the error but don't fail the login
            print(f"⚠️ Activity logging failed: {e}")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "middle_name": user.middle_name,
                "last_name": user.last_name,
                "role": user.role,
                "company": user.company,
                "phone": user.phone,
                "avatar_url": user.avatar_url,
                "is_active": user.is_active
            }
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        # Catch any unexpected errors and log them
        print(f"💥 Login error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: AsyncSession = Depends(get_async_session)
):
    """Get current user from JWT token."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        print(f"🔑 Decoding JWT token...")
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        print(f"🔑 JWT payload: {payload}")
        email: str = payload.get("sub")
        if email is None:
            print(f"❌ No email in JWT payload")
            raise credentials_exception
        print(f"🔑 Looking up user by email: {email}")
    except jwt.JWTError as e:
        print(f"❌ JWT decode error: {e}")
        raise credentials_exception
        
    user = await get_user_by_email(db, email=email)
    if user is None:
        print(f"❌ User not found in database: {email}")
        raise credentials_exception
    
    print(f"✅ User found: {user.email} (ID: {user.id})")
    return user

async def get_optional_token(request) -> Optional[str]:
    """Extract token from Authorization header if present."""
    from fastapi import Request
    authorization = request.headers.get("Authorization")
    if authorization and authorization.startswith("Bearer "):
        return authorization.split(" ")[1]
    return None

async def get_current_user_optional(
    request: Request,
    db: AsyncSession = Depends(get_async_session)
) -> Optional[User]:
    """Get current user from JWT token, return None if not authenticated."""
    from fastapi import Request
    
    token = await get_optional_token(request)
    if not token:
        return None
        
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        email: str = payload.get("sub")
        if email is None:
            return None
            
        user = await get_user_by_email(db, email=email)
        return user
    except jwt.JWTError:
        return None

@router.get("/me")
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    """Get current user information."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "first_name": current_user.first_name,
        "middle_name": current_user.middle_name,
        "last_name": current_user.last_name,
        "role": current_user.role,
        "company": current_user.company,
        "phone": current_user.phone,
        "avatar_url": current_user.avatar_url,
        "is_active": current_user.is_active
    }


class ProfileUpdate(BaseModel):
    """Schema for user profile updates (non-admin)"""
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None  # Changed from EmailStr to allow empty string handling
    phone: Optional[str] = None
    company: Optional[str] = None

    @field_validator('first_name', 'middle_name', 'last_name', 'company', mode='before')
    @classmethod
    def empty_string_to_none(cls, v: Optional[str]) -> Optional[str]:
        """Convert empty strings to None for optional fields"""
        if v == '':
            return None
        return v

    @field_validator('email', mode='before')
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        """Validate email, treating empty string as None"""
        if v is None or v == '':
            return None
        # Basic email validation
        import re
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Please enter a valid email address')
        return v

    @field_validator('phone', mode='before')
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone, treating empty string as None"""
        if v is None or v == '':
            return None
        import re
        # Strip spaces and dashes for validation
        cleaned = re.sub(r'[\s\-()]', '', v)
        # Accept any reasonable phone number format (7-15 digits, optional + prefix)
        if not re.match(r'^\+?\d{7,15}$', cleaned):
            raise ValueError('Please enter a valid phone number')
        return v


@router.patch("/me")
async def update_profile(
    profile_data: ProfileUpdate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_async_session)
):
    """Update current user's profile information."""
    try:
        # Check if email is being changed and if it's already taken
        if profile_data.email and profile_data.email != current_user.email:
            existing_user = await get_user_by_email(db, profile_data.email)
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already in use"
                )
        
        # Update user fields
        update_data = profile_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                setattr(current_user, field, value)
        
        current_user.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(current_user)
        
        return {
            "message": "Profile updated successfully",
            "user": {
                "id": current_user.id,
                "email": current_user.email,
                "first_name": current_user.first_name,
                "middle_name": current_user.middle_name,
                "last_name": current_user.last_name,
                "role": current_user.role,
                "company": current_user.company,
                "phone": current_user.phone,
                "avatar_url": current_user.avatar_url,
                "is_active": current_user.is_active
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        print(f"💥 Profile update error: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )


class PasswordChange(BaseModel):
    """Schema for password change"""
    current_password: str
    new_password: str


@router.patch("/password")
async def change_password(
    password_data: PasswordChange,
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(get_async_session)
):
    """Change current user's password."""
    try:
        # Verify current password
        if not verify_password(password_data.current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Validate new password length
        if len(password_data.new_password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be at least 8 characters long"
            )
        
        # Update password
        current_user.hashed_password = hash_password(password_data.new_password)
        current_user.updated_at = datetime.utcnow()
        await db.commit()
        
        return {"message": "Password changed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        print(f"💥 Password change error: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to change password: {str(e)}"
        )


@router.post("/avatar")
async def upload_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session)
):
    """Upload or update user avatar image."""
    from app.services.file_storage import FileStorageService
    
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File must be an image"
            )
        
        # Validate file size (5MB limit)
        if file.size and file.size > 5 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Avatar file size must be less than 5MB"
            )
        
        # Upload to OSS
        from app.services.oss_service import get_oss_service
        file_storage = FileStorageService()
        upload_result = await file_storage.save_file(
            file=file,
            subfolder=f"avatars/user_{current_user.id}"
        )

        # OSS bucket has private ACL — generate a 1-year signed URL so the
        # browser can load the image directly without credentials
        oss_service = get_oss_service()
        signed_url = oss_service.generate_signed_url(
            upload_result["object_key"],
            expires=365 * 24 * 3600  # 1 year
        )

        # Update user's avatar URL
        current_user.avatar_url = signed_url
        current_user.updated_at = datetime.utcnow()
        await db.commit()
        await db.refresh(current_user)
        
        return {
            "message": "Avatar uploaded successfully",
            "avatar_url": current_user.avatar_url
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        print(f"💥 Avatar upload error: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload avatar: {str(e)}"
        )