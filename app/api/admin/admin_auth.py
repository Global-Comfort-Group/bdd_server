"""
Admin Portal Authentication
Separate authentication for admin portal with different permissions
"""
from typing import Annotated
from fastapi import Depends, HTTPException, status
from app.api.v1.auth import current_active_user
from app.models.user import User
from app.models.enums import UserRole


async def current_admin_user(
    current_user: Annotated[User, Depends(current_active_user)]
) -> User:
    """
    Dependency to ensure only ADMIN users can access admin portal endpoints
    """
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required. This portal is for BDD employee management only."
        )
    return current_user


async def current_superuser_admin(
    current_user: Annotated[User, Depends(current_admin_user)]
) -> User:
    """
    Dependency for super admin operations (system-level changes)
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin privileges required"
        )
    return current_user