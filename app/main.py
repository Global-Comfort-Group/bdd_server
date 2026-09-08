from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from typing import Optional
import time
import logging

from app.core.config import settings
from app.api.v1.auth import router as auth_router
from app.api.v1.properties_simple import router as properties_simple_router
from app.api.v1.properties import router as properties_router
from app.api.v1.duplicates import router as duplicates_router
from app.api.v1.notifications import router as notifications_router
# Using simple nego_tables for now - it fetches properties from database
# TODO: Migrate to production nego_tables.py once async/sync issues are resolved
from app.api.v1.nego_tables_simple import router as nego_tables_router
# from app.api.v1.draft_nego_tables import router as draft_nego_tables_router
from app.api.v1.negotiation_chronicles import router as negotiation_chronicles_router
from app.api.v1.nego_ai_analysis import router as nego_ai_analysis_router
from app.api.admin import admin_router
from app.api.v1.uploads import router as uploads_router
from app.api.v1.address import router as address_router
from app.api.v1.property_kmz import router as property_kmz_router
from app.api.v1.files import router as files_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 BDD Property Tracker API starting up...")
    
    # Create upload directory if it doesn't exist
    os.makedirs(settings.UPLOAD_DIRECTORY, exist_ok=True)
    print(f"📁 Upload directory ready: {settings.UPLOAD_DIRECTORY}")
    
    yield
    
    # Shutdown
    print("🛑 BDD Property Tracker API shutting down...")


# Create FastAPI application
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="FastAPI backend for BDD Property Tracker system with PostgreSQL database",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Set up CORS - More permissive for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],  # Explicitly include OPTIONS
    allow_headers=["*"],  # Allow all headers
)

# Mount static files for uploads
if os.path.exists(settings.UPLOAD_DIRECTORY):
    app.mount("/files", StaticFiles(directory=settings.UPLOAD_DIRECTORY), name="files")

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for deployment monitoring."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION
    }

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": f"Welcome to {settings.PROJECT_NAME} API",
        "version": settings.VERSION,
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health"
    }

# Include routers
# Authentication
app.include_router(
    auth_router,
    prefix=settings.API_V1_PREFIX,
    tags=["auth"]
)

app.include_router(
    properties_simple_router,
    prefix=f"{settings.API_V1_PREFIX}/properties-submit",
    tags=["properties-submit"]
)

app.include_router(
    properties_router,
    prefix=settings.API_V1_PREFIX,
    tags=["properties"]
)

app.include_router(
    duplicates_router,
    prefix=settings.API_V1_PREFIX,
    tags=["duplicates"]
)

app.include_router(
    notifications_router,
    prefix=settings.API_V1_PREFIX,
    tags=["notifications"]
)

app.include_router(
    nego_tables_router,
    prefix=f"{settings.API_V1_PREFIX}/nego-tables",
    tags=["nego-tables"]
)

app.include_router(
    negotiation_chronicles_router,
    prefix=f"{settings.API_V1_PREFIX}/negotiation-chronicles",
    tags=["negotiation-chronicles"]
)

app.include_router(
    nego_ai_analysis_router,
    prefix=f"{settings.API_V1_PREFIX}/nego-ai-analysis",
    tags=["nego-ai-analysis"]
)

# app.include_router(
#     draft_nego_tables_router,
#     prefix=f"{settings.API_V1_PREFIX}/draft-nego-tables",
#     tags=["draft-nego-tables"]
# )

# Admin Portal - Separate from property management API
app.include_router(
    admin_router,
    tags=["admin-portal"]
)

# Also expose the admin portal under the versioned prefix.
#
# The deployed topology proxies ONLY `/api/v1/*` to this service
# (see `rewrites()` in the client's next.config.ts), and `/admin/*` on the
# public host is served by Next.js as its own page routes. Mounted solely at
# the root, every admin endpoint is therefore unreachable from a browser in
# staging/production — `/api/v1/admin/users` 404s here while `/admin/users`
# never leaves the frontend.
#
# The client already builds admin URLs as `${BASE_URL}/admin/...`, i.e.
# `/api/v1/admin/...`, so this makes those resolve. The root mount is kept so
# local setups that call the backend directly on :8000 keep working.
app.include_router(
    admin_router,
    prefix=settings.API_V1_PREFIX,
    tags=["admin-portal"]
)

app.include_router(
    uploads_router,
    prefix=settings.API_V1_PREFIX,
    tags=["uploads"]
)

app.include_router(
    address_router,
    prefix=f"{settings.API_V1_PREFIX}/address",
    tags=["address"]
)

app.include_router(
    property_kmz_router,
    prefix=settings.API_V1_PREFIX,
    tags=["property-kmz"]
)

app.include_router(
    files_router,
    prefix=settings.API_V1_PREFIX,
    tags=["files"]
)

# Add exception handlers
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

logger = logging.getLogger(__name__)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Log full 422 validation errors so we can diagnose them."""
    errors = exc.errors()
    print(f"❌ 422 VALIDATION ERROR on {request.method} {request.url.path}")
    for err in errors:
        print(f"   field={err.get('loc')} msg={err.get('msg')} type={err.get('type')}")
    return JSONResponse(
        status_code=422,
        content={"detail": errors}
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler for unhandled exceptions."""
    logger.error(f"Global exception handler caught: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "message": "An unexpected error occurred. Please try again later."
        }
    )


# Nine routes are served with a trailing slash ("/properties/", "/admin/users/"
# and so on). Starlette answers the slashless form with a 307 whose Location is
# absolute, built from the request's Host header — which behind a reverse proxy
# is this service's own hostname, not the one the browser is talking to.
#
# That makes the redirect cross-origin, and `fetch` drops the Authorization
# header when it follows one. The retry arrives unauthenticated, the backend
# answers 401, and the frontend treats that as an expired session and signs the
# user out. Next.js normalises the slash away before proxying, so the browser
# cannot avoid this by asking for the slashed path — it never survives the hop.
#
# Matching the slashed route directly removes the redirect entirely, which works
# whatever sits in front of us. Only paths that are genuinely routes are
# rewritten, so a real 404 is still a 404.
_slashed_routes: Optional[set] = None


def _routes_served_with_a_slash() -> set:
    """Route paths ending in "/", computed once, after all routers are in."""
    global _slashed_routes
    if _slashed_routes is None:
        _slashed_routes = {
            route.path
            for route in app.routes
            if getattr(route, "path", "").endswith("/")
        }
    return _slashed_routes


@app.middleware("http")
async def match_routes_whose_trailing_slash_was_stripped(request: Request, call_next):
    """Route "/admin/users" to "/admin/users/" instead of redirecting to it."""
    path = request.scope.get("path", "")
    if not path.endswith("/") and f"{path}/" in _routes_served_with_a_slash():
        request.scope["path"] = f"{path}/"
    return await call_next(request)


# Add middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests."""
    start_time = time.time()
    
    # Log request
    print(f"📥 Request: {request.method} {request.url}")
    logger.info(f"Request: {request.method} {request.url}")
    
    try:
        response = await call_next(request)
        
        # Log response
        process_time = time.time() - start_time
        print(f"📤 Response: {response.status_code} - {process_time:.4f}s")
        logger.info(f"Response: {response.status_code} - {process_time:.4f}s")
        
        return response
    except Exception as e:
        print(f"💥 Middleware error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        raise