"""
Admin Portal - User Management Endpoints
For BDD employee management only - separate from property management portal
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.models.user import User
from app.models.property import Property
from app.models.enums import UserRole, AccountStatus
from app.schemas.user import UserRead, UserCreate, UserUpdate, UserListResponse
from app.api.admin.admin_auth import current_admin_user, current_superuser_admin
from app.utils.activity_logger import log_activity
from app.models.activity_log import ActivityAction, ResourceType

router = APIRouter(prefix="/users", tags=["admin-users"])


@router.get("/", response_model=UserListResponse)
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    account_status: Optional[AccountStatus] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_admin_user),
):
    """List all users (admin portal only)."""
    # Build query with filters
    query = select(User)

    if role:
        query = query.where(User.role == role)
    if is_active is not None:
        query = query.where(User.is_active == is_active)
    if account_status is not None:
        query = query.where(User.account_status == account_status)
    if search:
        term = f"%{search}%"
        query = query.where(
            or_(
                User.first_name.ilike(term),
                User.last_name.ilike(term),
                User.email.ilike(term),
                (User.first_name + " " + User.last_name).ilike(term),
            )
        )
    
    # Get total count before pagination
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0
    
    # Apply pagination
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    users = result.scalars().all()
    
    # Return paginated response
    return {
        "users": users,
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.post("/", response_model=UserRead)
async def create_user(
    user_data: UserCreate,
    http_request: Request,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_admin_user),
):
    """Create a new user (admin only)."""
    # Check if user already exists
    stmt = select(User).where(User.email == user_data.email)
    result = await db.execute(stmt)
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    # Create user directly in the database
    from app.core.security import get_password_hash
    
    # Create new user with hashed password
    # Admin-created users should ALWAYS be APPROVED and verified
    new_user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        first_name=user_data.first_name,
        middle_name=user_data.middle_name,
        last_name=user_data.last_name,
        role=user_data.role,
        company=user_data.company,
        phone=user_data.phone,
        is_active=user_data.is_active if user_data.is_active is not None else True,
        is_superuser=user_data.is_superuser if user_data.is_superuser is not None else False,
        is_verified=True,  # Admin-created users are ALWAYS verified
        account_status=AccountStatus.APPROVED  # Admin-created users are ALWAYS approved
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    try:
        await log_activity(
            db=db,
            user_id=current_user.id,
            action=ActivityAction.CREATE,
            resource_type=ResourceType.USER,
            resource_id=new_user.id,
            details=f"Created user: {new_user.email} with role {new_user.role.value if new_user.role else 'unknown'}",
            request=http_request,
        )
    except Exception:
        pass

    return new_user


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    http_request: Request,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_admin_user),
):
    """Update a user (admin only)."""
    import logging
    logger = logging.getLogger(__name__)
    
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Log the update attempt
    logger.info(f"Admin user {current_user.id} ({current_user.email}) updating user {user_id}")
    
    # Update user fields
    update_data = user_data.model_dump(exclude_unset=True)
    logger.info(f"Update data for user {user_id}: {update_data.keys()}")
    
    # Track if anything actually changed
    changes_made = False
    
    for field, value in update_data.items():
        if field == "password" and value:
            from app.core.security import get_password_hash
            setattr(user, "hashed_password", get_password_hash(value))
            logger.info(f"Updated password for user {user_id}")
            changes_made = True
        elif field != "password":
            # Only update if the value is different
            old_value = getattr(user, field, None)
            if old_value != value:
                setattr(user, field, value)
                logger.info(f"Updated {field} for user {user_id}: {old_value} -> {value}")
                changes_made = True
    
    if changes_made:
        # Explicitly update the updated_at timestamp
        from datetime import datetime
        user.updated_at = datetime.utcnow()

        await db.commit()
        await db.refresh(user)
        logger.info(f"Successfully updated user {user_id}")

        try:
            if 'role' in update_data:
                action = ActivityAction.ROLE_CHANGE
                details = f"Changed role for {user.email} to {user.role.value if user.role else 'unknown'}"
            elif 'is_active' in update_data:
                action = ActivityAction.ACTIVATE if update_data.get('is_active') else ActivityAction.DEACTIVATE
                details = f"{'Activated' if update_data.get('is_active') else 'Deactivated'} user: {user.email}"
            else:
                action = ActivityAction.UPDATE
                details = f"Updated user profile: {user.email}"
            await log_activity(
                db=db,
                user_id=current_user.id,
                action=action,
                resource_type=ResourceType.USER,
                resource_id=user_id,
                details=details,
                request=http_request,
            )
        except Exception:
            pass
    else:
        logger.info(f"No changes made to user {user_id}")

    return user


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    http_request: Request,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_admin_user),
):
    """Delete a user (admin only)."""
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
    
    user_email = user.email
    await db.delete(user)
    await db.commit()

    try:
        await log_activity(
            db=db,
            user_id=current_user.id,
            action=ActivityAction.DELETE,
            resource_type=ResourceType.USER,
            resource_id=user_id,
            details=f"Deleted user: {user_email}",
            request=http_request,
        )
    except Exception:
        pass

    return {"message": "User deleted successfully"}


@router.get("/pending", response_model=List[UserRead])
async def list_pending_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_admin_user),
):
    """List all pending approval users (admin portal only)."""
    stmt = (
        select(User)
        .where(User.account_status == AccountStatus.PENDING)
        .order_by(User.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    
    result = await db.execute(stmt)
    users = result.scalars().all()
    
    return users


@router.patch("/{user_id}/approve")
async def approve_user_account(
    user_id: int,
    http_request: Request,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_admin_user),
):
    """Approve a pending user account (admin only)."""
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.account_status != AccountStatus.PENDING:
        raise HTTPException(
            status_code=400, 
            detail=f"User account is not pending approval. Current status: {user.account_status}"
        )
    
    user.account_status = AccountStatus.APPROVED
    await db.commit()
    await db.refresh(user)

    try:
        await log_activity(
            db=db,
            user_id=current_user.id,
            action=ActivityAction.ACTIVATE,
            resource_type=ResourceType.USER,
            resource_id=user_id,
            details=f"Approved user account: {user.email}",
            request=http_request,
        )
    except Exception:
        pass

    return {
        "message": f"User account for {user.email} has been approved",
        "user": {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "account_status": user.account_status
        }
    }


@router.patch("/{user_id}/reject")
async def reject_user_account(
    user_id: int,
    http_request: Request,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_admin_user),
):
    """Reject a pending user account (admin only)."""
    stmt = select(User).where(User.id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.account_status != AccountStatus.PENDING:
        raise HTTPException(
            status_code=400, 
            detail=f"User account is not pending approval. Current status: {user.account_status}"
        )
    
    user.account_status = AccountStatus.REJECTED
    await db.commit()
    await db.refresh(user)

    try:
        await log_activity(
            db=db,
            user_id=current_user.id,
            action=ActivityAction.DEACTIVATE,
            resource_type=ResourceType.USER,
            resource_id=user_id,
            details=f"Rejected user account: {user.email}",
            request=http_request,
        )
    except Exception:
        pass

    return {
        "message": f"User account for {user.email} has been rejected",
        "user": {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "account_status": user.account_status
        }
    }


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
    
    # Get users by account status
    status_stmt = (
        select(User.account_status, func.count(User.id))
        .group_by(User.account_status)
    )
    status_result = await db.execute(status_stmt)
    users_by_status = dict(status_result.all())
    
    # Get pending users count
    pending_stmt = select(func.count(User.id)).where(User.account_status == AccountStatus.PENDING)
    pending_result = await db.execute(pending_stmt)
    pending_users = pending_result.scalar()
    
    # Get recent registrations (last 30 days)
    from datetime import datetime, timedelta
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_stmt = select(func.count(User.id)).where(User.created_at >= thirty_days_ago)
    recent_result = await db.execute(recent_stmt)
    recent_users = recent_result.scalar()
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "pending_approval": pending_users,
        "recent_registrations_30_days": recent_users,
        "users_by_role": users_by_role,
        "users_by_status": users_by_status,
        "generated_at": datetime.utcnow()
    }