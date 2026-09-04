"""
Admin Portal Package - Separate from Property Management
For BDD employee management and system administration only
"""
from fastapi import APIRouter
from app.api.admin.users import router as users_router
from app.api.admin.dashboard import router as dashboard_router, stats_router
from app.api.admin.activity_logs import router as activity_logs_router
from app.api.admin.excel_import import router as excel_import_router

admin_router = APIRouter(prefix="/admin", tags=["admin-portal"])

# Include admin sub-routers
admin_router.include_router(users_router)
admin_router.include_router(dashboard_router)
admin_router.include_router(stats_router)
admin_router.include_router(activity_logs_router)
admin_router.include_router(excel_import_router)