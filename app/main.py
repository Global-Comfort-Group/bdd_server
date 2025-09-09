from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

from app.core.config import settings
from app.api.v1.auth import auth_router, users_router
from app.api.v1.simple_auth import router as simple_auth_router
from app.api.v1.properties import router as properties_router
from app.api.v1.duplicates import router as duplicates_router
from app.api.admin import admin_router
from app.api.v1.uploads import router as uploads_router


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

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=["*"],
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
# Temporary simple auth router (working)
app.include_router(
    simple_auth_router,
    prefix=settings.API_V1_PREFIX,
    tags=["simple-auth"]
)

# FastAPI-Users auth router (currently broken)
# app.include_router(
#     auth_router,
#     prefix=f"{settings.API_V1_PREFIX}/auth",
#     tags=["authentication"]
# )

# FastAPI-Users users router (currently broken)
# app.include_router(
#     users_router,
#     prefix=settings.API_V1_PREFIX,
#     tags=["users"]
# )

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

# Admin Portal - Separate from property management API
app.include_router(
    admin_router,
    tags=["admin-portal"]
)

app.include_router(
    uploads_router,
    prefix=settings.API_V1_PREFIX,
    tags=["uploads"]
)

# Add exception handlers
from fastapi import Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)


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


# Add middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests."""
    start_time = time.time()
    
    # Log request
    logger.info(f"Request: {request.method} {request.url}")
    
    response = await call_next(request)
    
    # Log response
    process_time = time.time() - start_time
    logger.info(f"Response: {response.status_code} - {process_time:.4f}s")
    
    return response


import time