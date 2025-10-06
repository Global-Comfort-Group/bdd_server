"""
Admin Portal - System Dashboard Endpoints
For system-wide statistics and BDD employee insights
"""
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session
from app.models.user import User
from app.models.property import Property
from app.models.enums import UserRole
from app.services.workflow import WorkflowService
from app.api.admin.admin_auth import current_admin_user

router = APIRouter(prefix="/dashboard", tags=["admin-dashboard"])

# Add a general stats router without prefix for /admin/stats endpoint
stats_router = APIRouter(tags=["admin-stats"])


@router.get("/system-stats")
async def get_system_statistics(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_admin_user),
):
    """Get comprehensive system statistics for admin dashboard."""
    workflow_service = WorkflowService(db)
    
    # Property Statistics
    workflow_stats = await workflow_service.get_workflow_statistics()
    
    total_properties_stmt = select(func.count(Property.id))
    total_properties_result = await db.execute(total_properties_stmt)
    total_properties = total_properties_result.scalar()
    
    # Properties by type
    type_stmt = (
        select(Property.property_type, func.count(Property.id))
        .group_by(Property.property_type)
    )
    type_result = await db.execute(type_stmt)
    properties_by_type = dict(type_result.all())
    
    # Recent property activity (last 30 days)
    from datetime import datetime, timedelta
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_properties_stmt = select(func.count(Property.id)).where(Property.created_at >= thirty_days_ago)
    recent_properties_result = await db.execute(recent_properties_stmt)
    recent_properties = recent_properties_result.scalar()
    
    # User Statistics
    total_users_stmt = select(func.count(User.id))
    total_users_result = await db.execute(total_users_stmt)
    total_users = total_users_result.scalar()
    
    active_users_stmt = select(func.count(User.id)).where(User.is_active == True)
    active_users_result = await db.execute(active_users_stmt)
    active_users = active_users_result.scalar()
    
    # Users by role
    role_stmt = (
        select(User.role, func.count(User.id))
        .group_by(User.role)
    )
    role_result = await db.execute(role_stmt)
    users_by_role = dict(role_result.all())
    
    # Recent user registrations (last 30 days)
    recent_users_stmt = select(func.count(User.id)).where(User.created_at >= thirty_days_ago)
    recent_users_result = await db.execute(recent_users_stmt)
    recent_users = recent_users_result.scalar()
    
    # System Health Metrics
    # Top active users (users with most property submissions)
    top_users_stmt = (
        select(
            User.first_name,
            User.last_name, 
            User.email,
            User.role,
            func.count(Property.id).label('property_count')
        )
        .join(Property, User.id == Property.submitted_by_id, isouter=True)
        .group_by(User.id, User.first_name, User.last_name, User.email, User.role)
        .order_by(func.count(Property.id).desc())
        .limit(5)
    )
    top_users_result = await db.execute(top_users_stmt)
    top_active_users = [
        {
            "name": f"{row.first_name} {row.last_name}",
            "email": row.email,
            "role": row.role.value,
            "property_count": row.property_count
        }
        for row in top_users_result.all()
    ]
    
    return {
        "system_overview": {
            "total_properties": total_properties,
            "total_users": total_users,
            "active_users": active_users,
            "recent_properties_30_days": recent_properties,
            "recent_user_registrations_30_days": recent_users
        },
        "property_insights": {
            "properties_by_status": workflow_stats,
            "properties_by_type": properties_by_type
        },
        "user_insights": {
            "users_by_role": users_by_role,
            "top_active_users": top_active_users
        },
        "generated_at": datetime.utcnow()
    }


@stats_router.get("/stats")
async def get_admin_stats(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_admin_user),
):
    """Get general admin statistics for the admin panel overview."""
    # Get basic counts
    total_users_stmt = select(func.count(User.id))
    total_users_result = await db.execute(total_users_stmt)
    total_users = total_users_result.scalar()
    
    active_users_stmt = select(func.count(User.id)).where(User.is_active == True)
    active_users_result = await db.execute(active_users_stmt)
    active_users = active_users_result.scalar()
    
    total_properties_stmt = select(func.count(Property.id))
    total_properties_result = await db.execute(total_properties_stmt)
    total_properties = total_properties_result.scalar()
    
    return {
        "total_users": total_users,
        "active_users": active_users,
        "total_properties": total_properties,
        "generated_at": datetime.utcnow()
    }


@stats_router.get("/properties/stats")
async def get_admin_property_stats(
    db: AsyncSession = Depends(get_async_session),
    current_user: User = Depends(current_admin_user),
):
    """Get property statistics for admin panel."""
    total_properties_stmt = select(func.count(Property.id))
    total_properties_result = await db.execute(total_properties_stmt)
    total_properties = total_properties_result.scalar()
    
    # Properties by type
    type_stmt = (
        select(Property.property_type, func.count(Property.id))
        .group_by(Property.property_type)
    )
    type_result = await db.execute(type_stmt)
    properties_by_type = dict(type_result.all())
    
    # Recent properties (last 30 days)
    from datetime import datetime, timedelta
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    recent_properties_stmt = select(func.count(Property.id)).where(Property.created_at >= thirty_days_ago)
    recent_properties_result = await db.execute(recent_properties_stmt)
    recent_properties = recent_properties_result.scalar()
    
    return {
        "total_properties": total_properties,
        "properties_by_type": properties_by_type,
        "recent_properties_30_days": recent_properties,
        "generated_at": datetime.utcnow()
    }