from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from app.core.database import get_db
from app.api.v1.auth import get_current_user
from app.models.user import User
from app.models.enums import UserRole
from app.schemas.activity_log import (
    ActivityLogResponse, ActivityLogFilters, ActivityStats
)
from app.services.activity_log_service import ActivityLogService

router = APIRouter(prefix="/activity-logs", tags=["Admin - Activity Logs"])


def require_admin(current_user: User = Depends(get_current_user)):
    """Dependency to require admin role"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


@router.get("/", response_model=dict)
async def get_activity_logs(
    user_id: int = None,
    action: str = None,
    resource_type: str = None,
    resource_id: int = None,
    date_from: str = None,
    date_to: str = None,
    limit: int = 50,
    skip: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Get activity logs with optional filters (Admin only)
    
    Returns paginated list of activity logs
    """
    filters = ActivityLogFilters(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        skip=skip
    )
    
    logs, total = await ActivityLogService.get_logs(db, filters)
    
    return {
        "logs": logs,
        "total": total,
        "limit": limit,
        "skip": skip
    }


@router.get("/stats", response_model=ActivityStats)
async def get_activity_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Get activity statistics (Admin only)
    
    Returns aggregated statistics about system activity
    """
    return await ActivityLogService.get_activity_stats(db)


@router.get("/user/{user_id}", response_model=dict)
async def get_user_activity_logs(
    user_id: int,
    limit: int = 50,
    skip: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Get activity logs for a specific user (Admin only)
    """
    filters = ActivityLogFilters(
        user_id=user_id,
        limit=limit,
        skip=skip
    )
    
    logs, total = await ActivityLogService.get_logs(db, filters)
    
    return {
        "logs": logs,
        "total": total,
        "user_id": user_id
    }


@router.delete("/cleanup")
async def cleanup_old_logs(
    days: int = 90,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Delete activity logs older than specified days (Admin only)
    
    Default: 90 days
    """
    if days < 30:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete logs newer than 30 days"
        )
    
    deleted_count = await ActivityLogService.delete_old_logs(db, days)
    
    return {
        "message": f"Successfully deleted {deleted_count} old activity logs",
        "deleted_count": deleted_count,
        "older_than_days": days
    }


@router.get("/export")
async def export_activity_logs(
    request: Request,
    user_id: int = None,
    action: str = None,
    resource_type: str = None,
    date_from: str = None,
    date_to: str = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    """
    Export activity logs as CSV (Admin only)
    """
    from fastapi.responses import StreamingResponse
    import csv
    import io
    
    filters = ActivityLogFilters(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        date_from=date_from,
        date_to=date_to,
        limit=10000,  # Max export limit
        skip=0
    )
    
    logs, _ = await ActivityLogService.get_logs(db, filters)
    
    # Create CSV
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        'ID', 'User ID', 'User Name', 'User Email', 'Action', 
        'Resource Type', 'Resource ID', 'Details', 'IP Address', 
        'User Agent', 'Created At'
    ])
    
    # Data
    for log in logs:
        writer.writerow([
            log.id,
            log.user_id,
            log.user_name or '',
            log.user_email or '',
            log.action,
            log.resource_type,
            log.resource_id or '',
            log.details,
            log.ip_address or '',
            log.user_agent or '',
            log.created_at.isoformat()
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=activity_logs_{date_from or 'all'}_{date_to or 'all'}.csv"
        }
    )

