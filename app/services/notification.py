from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime

from app.models.notification import Notification, NotificationType
from app.schemas.notification import NotificationCreate, NotificationUpdate
from app.utils.email import EmailService


class NotificationService:
    """Service for managing user notifications"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.email_service = EmailService()
    
    async def create_notification(
        self, 
        notification_data: NotificationCreate,
        send_email: bool = True,
        send_realtime: bool = True
    ) -> Notification:
        """Create a new notification and optionally send email/realtime"""
        notification = Notification(
            user_id=notification_data.user_id,
            notification_type=notification_data.notification_type,
            title=notification_data.title,
            message=notification_data.message,
            property_id=notification_data.property_id,
            duplicate_property_id=notification_data.duplicate_property_id,
        )
        
        self.db.add(notification)
        await self.db.commit()
        await self.db.refresh(notification)
        
        # Send email notification if requested
        if send_email:
            await self._send_email_notification(notification)
        
        # Send real-time notification via WebSocket
        if send_realtime:
            await self._send_realtime_notification(notification)
        
        return notification
    
    async def get_user_notifications(
        self, 
        user_id: int, 
        unread_only: bool = False,
        limit: int = 50
    ) -> List[Notification]:
        """Get notifications for a user"""
        stmt = select(Notification).where(Notification.user_id == user_id)
        
        if unread_only:
            stmt = stmt.where(Notification.is_read == False)
        
        stmt = stmt.order_by(Notification.created_at.desc()).limit(limit)
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def mark_as_read(self, notification_id: int) -> Optional[Notification]:
        """Mark a notification as read"""
        stmt = select(Notification).where(Notification.id == notification_id)
        result = await self.db.execute(stmt)
        notification = result.scalar_one_or_none()
        
        if notification:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            await self.db.commit()
            await self.db.refresh(notification)
        
        return notification
    
    async def mark_all_as_read(self, user_id: int) -> int:
        """Mark all notifications as read for a user"""
        stmt = select(Notification).where(
            Notification.user_id == user_id,
            Notification.is_read == False
        )
        result = await self.db.execute(stmt)
        notifications = result.scalars().all()
        
        count = 0
        for notification in notifications:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            count += 1
        
        await self.db.commit()
        return count
    
    async def delete_notification(self, notification_id: int) -> bool:
        """Delete a notification"""
        stmt = select(Notification).where(Notification.id == notification_id)
        result = await self.db.execute(stmt)
        notification = result.scalar_one_or_none()
        
        if notification:
            await self.db.delete(notification)
            await self.db.commit()
            return True
        
        return False
    
    async def get_unread_count(self, user_id: int) -> int:
        """Get count of unread notifications for a user"""
        from sqlalchemy import func
        stmt = select(func.count()).where(
            Notification.user_id == user_id,
            Notification.is_read == False
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()
    
    async def _send_email_notification(self, notification: Notification):
        """Send email notification to user"""
        try:
            # Get user email
            from app.models.user import User
            stmt = select(User).where(User.id == notification.user_id)
            result = await self.db.execute(stmt)
            user = result.scalar_one_or_none()
            
            if not user:
                return
            
            # Send email based on notification type
            await self.email_service.send_email(
                to_emails=[user.email],
                subject=notification.title,
                body=notification.message,
                html_body=self._format_html_email(notification)
            )
        except Exception as e:
            print(f"Failed to send email notification: {e}")
    
    def _format_html_email(self, notification: Notification) -> str:
        """Format notification as HTML email"""
        return f"""
        <html>
        <body>
            <h2>{notification.title}</h2>
            <p>{notification.message}</p>
            <br>
            <p><small>This is an automated notification from BDD Property Tracker</small></p>
        </body>
        </html>
        """
    
    async def _send_realtime_notification(self, notification: Notification):
        """Send real-time notification via WebSocket"""
        try:
            # Import here to avoid circular imports
            from app.api.v1.websocket_notifications import send_notification_to_user
            
            notification_data = {
                "id": notification.id,
                "type": notification.notification_type.value,
                "title": notification.title,
                "message": notification.message,
                "property_id": notification.property_id,
                "is_read": notification.is_read,
                "created_at": notification.created_at.isoformat()
            }
            
            await send_notification_to_user(notification.user_id, notification_data)
        except Exception as e:
            print(f"Failed to send real-time notification: {e}")
    
    async def create_duplicate_notification(
        self,
        user_id: int,
        property_id: int,
        duplicate_property_id: int,
        similarity_score: float,
        match_reasons: List[str]
    ) -> Notification:
        """Create a notification for duplicate property detection"""
        reasons_text = ", ".join(match_reasons)
        
        notification_data = NotificationCreate(
            user_id=user_id,
            notification_type=NotificationType.DUPLICATE_DETECTED,
            title="Duplicate Property Detected",
            message=(
                f"Your property submission (ID: {property_id}) appears to be a duplicate. "
                f"It matches an existing property (ID: {duplicate_property_id}) with "
                f"{similarity_score * 100:.1f}% similarity. "
                f"Match reasons: {reasons_text}. "
                f"Please review and contact an administrator if you believe this is an error."
            ),
            property_id=property_id,
            duplicate_property_id=duplicate_property_id
        )
        
        return await self.create_notification(notification_data, send_email=True)

