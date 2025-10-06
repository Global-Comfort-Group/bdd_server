from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.models.user import User
from app.schemas.notification import NotificationRead, NotificationUpdate
from app.services.notification import NotificationService
from app.api.v1.auth import get_current_user

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/", response_model=List[NotificationRead])
async def get_my_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Get current user's notifications"""
    service = NotificationService(db)
    notifications = await service.get_user_notifications(
        current_user.id, 
        unread_only=unread_only,
        limit=limit
    )
    return notifications


@router.get("/unread-count")
async def get_unread_count(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Get count of unread notifications"""
    service = NotificationService(db)
    count = await service.get_unread_count(current_user.id)
    return {"unread_count": count}


@router.patch("/{notification_id}/read", response_model=NotificationRead)
async def mark_notification_as_read(
    notification_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Mark a notification as read"""
    service = NotificationService(db)
    notification = await service.mark_as_read(notification_id)
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    # Check if notification belongs to current user
    if notification.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this notification")
    
    return notification


@router.post("/mark-all-read")
async def mark_all_notifications_as_read(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Mark all notifications as read for current user"""
    service = NotificationService(db)
    count = await service.mark_all_as_read(current_user.id)
    return {"message": f"Marked {count} notifications as read"}


@router.delete("/{notification_id}")
async def delete_notification(
    notification_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(get_current_user),
):
    """Delete a notification"""
    service = NotificationService(db)
    
    # First check if notification exists and belongs to user
    from sqlalchemy import select
    from app.models.notification import Notification
    stmt = select(Notification).where(Notification.id == notification_id)
    result = await db.execute(stmt)
    notification = result.scalar_one_or_none()
    
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    if notification.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this notification")
    
    success = await service.delete_notification(notification_id)
    
    if success:
        return {"message": "Notification deleted successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to delete notification")

