from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy import desc, func
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.activity_log import ActivityLog, ActivityAction, ResourceType
from app.models.user import User
from app.schemas.activity_log import ActivityLogCreate, ActivityLogResponse, ActivityLogFilters, ActivityStats


class ActivityLogService:
    """Service for managing activity logs"""

    @staticmethod
    async def create_log(
        db: AsyncSession,
        user_id: Optional[int],
        action: ActivityAction,
        resource_type: ResourceType,
        details: str,
        resource_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> ActivityLog:
        """Create a new activity log entry"""
        log = ActivityLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent
        )
        db.add(log)
        await db.commit()
        await db.refresh(log)
        return log

    @staticmethod
    async def get_logs(
        db: AsyncSession,
        filters: ActivityLogFilters
    ) -> tuple[List[ActivityLogResponse], int]:
        """Get activity logs with filters"""
        # Build query
        query = select(ActivityLog).options()
        
        # Apply filters
        if filters.user_id:
            query = query.where(ActivityLog.user_id == filters.user_id)
        if filters.action:
            query = query.where(ActivityLog.action == filters.action)
        if filters.resource_type:
            query = query.where(ActivityLog.resource_type == filters.resource_type)
        if filters.resource_id:
            query = query.where(ActivityLog.resource_id == filters.resource_id)
        if filters.date_from:
            query = query.where(ActivityLog.created_at >= filters.date_from)
        if filters.date_to:
            query = query.where(ActivityLog.created_at <= filters.date_to)
        
        # Get total count
        count_query = select(func.count()).select_from(ActivityLog)
        if filters.user_id:
            count_query = count_query.where(ActivityLog.user_id == filters.user_id)
        if filters.action:
            count_query = count_query.where(ActivityLog.action == filters.action)
        if filters.resource_type:
            count_query = count_query.where(ActivityLog.resource_type == filters.resource_type)
        if filters.resource_id:
            count_query = count_query.where(ActivityLog.resource_id == filters.resource_id)
        if filters.date_from:
            count_query = count_query.where(ActivityLog.created_at >= filters.date_from)
        if filters.date_to:
            count_query = count_query.where(ActivityLog.created_at <= filters.date_to)
            
        total_result = await db.execute(count_query)
        total = total_result.scalar_one()
        
        # Apply pagination and ordering
        query = query.order_by(desc(ActivityLog.created_at))
        query = query.limit(filters.limit).offset(filters.skip)
        
        # Execute query
        result = await db.execute(query)
        logs = result.scalars().all()
        
        # Join with user data
        log_responses = []
        for log in logs:
            user_name = None
            user_email = None
            if log.user_id:
                user_result = await db.execute(
                    select(User).where(User.id == log.user_id)
                )
                user = user_result.scalar_one_or_none()
                if user:
                    user_name = user.full_name
                    user_email = user.email
            
            log_responses.append(ActivityLogResponse(
                id=log.id,
                user_id=log.user_id,
                action=log.action,
                resource_type=log.resource_type,
                resource_id=log.resource_id,
                details=log.details,
                ip_address=log.ip_address,
                user_agent=log.user_agent,
                created_at=log.created_at,
                user_name=user_name,
                user_email=user_email
            ))
        
        return log_responses, total

    @staticmethod
    async def get_activity_stats(db: AsyncSession) -> ActivityStats:
        """Get activity statistics"""
        # Total activities
        total_result = await db.execute(select(func.count()).select_from(ActivityLog))
        total_activities = total_result.scalar_one()
        
        # Recent logins (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_logins_result = await db.execute(
            select(func.count()).select_from(ActivityLog).where(
                ActivityLog.action == ActivityAction.LOGIN,
                ActivityLog.created_at >= yesterday
            )
        )
        recent_logins = recent_logins_result.scalar_one()
        
        # Actions by type
        actions_result = await db.execute(
            select(ActivityLog.action, func.count(ActivityLog.id))
            .group_by(ActivityLog.action)
        )
        actions_by_type = {action.value: count for action, count in actions_result.all()}
        
        # Users active today
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        active_users_result = await db.execute(
            select(func.count(func.distinct(ActivityLog.user_id)))
            .where(ActivityLog.created_at >= today, ActivityLog.user_id.isnot(None))
        )
        users_active_today = active_users_result.scalar_one()
        
        # Most active users (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        most_active_result = await db.execute(
            select(
                ActivityLog.user_id,
                func.count(ActivityLog.id).label('activity_count')
            )
            .where(
                ActivityLog.created_at >= week_ago,
                ActivityLog.user_id.isnot(None)
            )
            .group_by(ActivityLog.user_id)
            .order_by(desc('activity_count'))
            .limit(5)
        )
        
        most_active_users = []
        for user_id, activity_count in most_active_result.all():
            user_result = await db.execute(select(User).where(User.id == user_id))
            user = user_result.scalar_one_or_none()
            if user:
                most_active_users.append({
                    "user_id": user_id,
                    "user_name": user.full_name,
                    "user_email": user.email,
                    "activity_count": activity_count
                })
        
        return ActivityStats(
            total_activities=total_activities,
            recent_logins=recent_logins,
            actions_by_type=actions_by_type,
            users_active_today=users_active_today,
            most_active_users=most_active_users
        )

    @staticmethod
    async def delete_old_logs(db: AsyncSession, days: int = 90) -> int:
        """Delete activity logs older than specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        result = await db.execute(
            select(ActivityLog).where(ActivityLog.created_at < cutoff_date)
        )
        old_logs = result.scalars().all()
        count = len(old_logs)
        
        for log in old_logs:
            await db.delete(log)
        
        await db.commit()
        return count





