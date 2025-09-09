"""
Admin Portal - User Management Endpoints
For BDD employee management only - separate from property management portal
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.models.user import User
from app.models.property import Property
from app.models.enums import UserRole
from app.schemas.user import UserRead, UserCreate, UserUpdate
from app.api.admin.admin_auth import current_admin_user, current_superuser_admin

router = APIRouter(prefix="/users", tags=["admin-users"])


@router.get("/", response_model=List[UserRead])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_admin_user),
):
    """List all users (admin portal only)."""
    stmt = select(User).offset(skip).limit(limit)
    
    if role:
        stmt = stmt.where(User.role == role)
    if is_active is not None:
        stmt = stmt.where(User.is_active == is_active)
    
    result = await db.execute(stmt)
    users = result.scalars().all()
    
    return users


@router.post("/", response_model=UserRead)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_superuser_admin),
):
    """Create a new user (super admin only)."""
    # Check if user already exists
    stmt = select(User).where(User.email == user_data.email)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    # Create user using FastAPI Users
    from app.services.auth import get_user_manager
    from app.api.deps import get_user_db
    
    user_db = get_user_db.__next__()
    user_manager = get_user_manager.__next__(user_db)
    
    try:
        user = await user_manager.create(user_data)
        return user
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_superuser_admin),
):
    """Update a user (super admin only)."""
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update user fields
    update_data = user_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "password" and value:
            from app.core.security import get_password_hash
            setattr(user, "hashed_password", get_password_hash(value))
        elif field != "password":
            setattr(user, field, value)
    
    await db.commit()
    await db.refresh(user)
    return user


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_superuser_admin),
):
    """Delete a user (super admin only)."""
    if user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if user has any properties
    property_count_stmt = select(func.count(Property.id)).where(Property.submitted_by_id == user_id)
    property_count_result = await db.execute(property_count_stmt)
    property_count = property_count_result.scalar()
    
    if property_count > 0:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot delete user with {property_count} associated properties"
        )
    
    await db.delete(user)
    await db.commit()
    
    return {"message": "User deleted successfully"}


@router.get("/stats")
async def get_user_statistics(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_admin_user),
):
    """Get user statistics (admin portal only)."""
    # Get total users count
    total_stmt = select(func.count(User.id))
    total_result = await db.execute(total_stmt)
    total_users = total_result.scalar()
    
    # Get active users count
    active_stmt = select(func.count(User.id)).where(User.is_active == True)
    active_result = await db.execute(active_stmt)
    active_users = active_result.scalar()
    
    # Get users by role
    role_stmt = (
        select(User.role, func.count(User.id))
        .group_by(User.role)
    )
    role_result = await db.execute(role_stmt)
    users_by_role = dict(role_result.all())
    
    # Get recent registrations (last 30 days)
    from datetime import datetime, timedelta
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_stmt = select(func.count(User.id)).where(User.created_at >= thirty_days_ago)
    recent_result = await db.execute(recent_stmt)
    recent_users = recent_result.scalar()
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "recent_registrations_30_days": recent_users,
        "users_by_role": users_by_role,
        "generated_at": datetime.utcnow()
    }