"""
Activity Logger Utility
Provides helper functions and decorators for logging user activities
"""
from functools import wraps
from typing import Optional
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.activity_log import ActivityAction, ResourceType
from app.services.activity_log_service import ActivityLogService


def get_client_ip(request: Request) -> Optional[str]:
    """Extract client IP from request"""
    if hasattr(request, 'client') and request.client:
        return request.client.host
    # Check for proxied requests
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return None


def get_user_agent(request: Request) -> Optional[str]:
    """Extract user agent from request"""
    return request.headers.get("User-Agent")


async def log_activity(
    db: AsyncSession,
    user_id: Optional[int],
    action: ActivityAction,
    resource_type: ResourceType,
    details: str,
    resource_id: Optional[int] = None,
    request: Optional[Request] = None
):
    """
    Log an activity
    
    Usage:
        await log_activity(
            db=db,
            user_id=current_user.id,
            action=ActivityAction.CREATE,
            resource_type=ResourceType.PROPERTY,
            details="Created property 'Sample Property'",
            resource_id=property.id,
            request=request
        )
    """
    ip_address = get_client_ip(request) if request else None
    user_agent = get_user_agent(request) if request else None
    
    await ActivityLogService.create_log(
        db=db,
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        details=details,
        resource_id=resource_id,
        ip_address=ip_address,
        user_agent=user_agent
    )


# Quick helper functions for common activities
async def log_login(
    db: AsyncSession,
    user_id: int,
    user_email: str,
    request: Optional[Request] = None
):
    """Log user login"""
    await log_activity(
        db=db,
        user_id=user_id,
        action=ActivityAction.LOGIN,
        resource_type=ResourceType.SYSTEM,
        details=f"User {user_email} logged in",
        request=request
    )


async def log_logout(
    db: AsyncSession,
    user_id: int,
    user_email: str,
    request: Optional[Request] = None
):
    """Log user logout"""
    await log_activity(
        db=db,
        user_id=user_id,
        action=ActivityAction.LOGOUT,
        resource_type=ResourceType.SYSTEM,
        details=f"User {user_email} logged out",
        request=request
    )


async def log_user_created(
    db: AsyncSession,
    admin_id: int,
    created_user_id: int,
    created_user_email: str,
    request: Optional[Request] = None
):
    """Log user creation"""
    await log_activity(
        db=db,
        user_id=admin_id,
        action=ActivityAction.CREATE,
        resource_type=ResourceType.USER,
        resource_id=created_user_id,
        details=f"Created new user: {created_user_email}",
        request=request
    )


async def log_user_updated(
    db: AsyncSession,
    admin_id: int,
    updated_user_id: int,
    updated_user_email: str,
    changes: str,
    request: Optional[Request] = None
):
    """Log user update"""
    await log_activity(
        db=db,
        user_id=admin_id,
        action=ActivityAction.UPDATE,
        resource_type=ResourceType.USER,
        resource_id=updated_user_id,
        details=f"Updated user {updated_user_email}: {changes}",
        request=request
    )


async def log_user_deleted(
    db: AsyncSession,
    admin_id: int,
    deleted_user_id: int,
    deleted_user_email: str,
    request: Optional[Request] = None
):
    """Log user deletion"""
    await log_activity(
        db=db,
        user_id=admin_id,
        action=ActivityAction.DELETE,
        resource_type=ResourceType.USER,
        resource_id=deleted_user_id,
        details=f"Deleted user: {deleted_user_email}",
        request=request
    )


async def log_property_created(
    db: AsyncSession,
    user_id: int,
    property_id: int,
    property_name: str,
    request: Optional[Request] = None
):
    """Log property creation"""
    await log_activity(
        db=db,
        user_id=user_id,
        action=ActivityAction.CREATE,
        resource_type=ResourceType.PROPERTY,
        resource_id=property_id,
        details=f"Created property: {property_name}",
        request=request
    )


async def log_property_updated(
    db: AsyncSession,
    user_id: int,
    property_id: int,
    property_name: str,
    changes: str,
    request: Optional[Request] = None
):
    """Log property update"""
    await log_activity(
        db=db,
        user_id=user_id,
        action=ActivityAction.UPDATE,
        resource_type=ResourceType.PROPERTY,
        resource_id=property_id,
        details=f"Updated property {property_name}: {changes}",
        request=request
    )


async def log_property_status_changed(
    db: AsyncSession,
    user_id: int,
    property_id: int,
    property_name: str,
    old_status: str,
    new_status: str,
    request: Optional[Request] = None
):
    """Log property status change"""
    await log_activity(
        db=db,
        user_id=user_id,
        action=ActivityAction.STATUS_CHANGE,
        resource_type=ResourceType.PROPERTY,
        resource_id=property_id,
        details=f"Changed property {property_name} status from {old_status} to {new_status}",
        request=request
    )


async def log_role_change(
    db: AsyncSession,
    admin_id: int,
    user_id: int,
    user_email: str,
    old_role: str,
    new_role: str,
    request: Optional[Request] = None
):
    """Log user role change"""
    await log_activity(
        db=db,
        user_id=admin_id,
        action=ActivityAction.ROLE_CHANGE,
        resource_type=ResourceType.USER,
        resource_id=user_id,
        details=f"Changed role for {user_email} from {old_role} to {new_role}",
        request=request
    )


async def log_data_export(
    db: AsyncSession,
    user_id: int,
    export_type: str,
    details: str,
    request: Optional[Request] = None
):
    """Log data export"""
    await log_activity(
        db=db,
        user_id=user_id,
        action=ActivityAction.EXPORT,
        resource_type=ResourceType.SYSTEM,
        details=f"Exported {export_type}: {details}",
        request=request
    )





