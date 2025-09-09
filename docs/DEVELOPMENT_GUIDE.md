# BDD Property Tracker - Development Guide

A comprehensive guide to the FastAPI backend architecture, APIs, and folder structure.

## 📁 Project Structure Overview

```
bdd_server/
├── app/                           # Main application directory
│   ├── api/                       # API layer
│   │   └── v1/                    # API version 1
│   │       ├── admin.py           # Admin management endpoints
│   │       ├── auth.py            # Authentication & user management
│   │       ├── duplicates.py      # Property duplicate detection
│   │       ├── properties.py      # Property CRUD operations
│   │       └── uploads.py         # File upload with Cloudinary
│   ├── core/                      # Core system components
│   │   ├── config.py              # Configuration & environment settings
│   │   ├── database.py            # Database connection & session management
│   │   └── security.py            # Security utilities & password hashing
│   ├── models/                    # SQLAlchemy database models
│   │   ├── __init__.py            # Model exports
│   │   ├── enums.py               # Shared enums (PropertyStatus, UserRole, etc.)
│   │   ├── property.py            # Property & PropertyAttachment models
│   │   ├── user.py                # User model with FastAPI-Users
│   │   └── workflow.py            # WorkflowHistory model
│   ├── schemas/                   # Pydantic models for API serialization
│   │   ├── __init__.py            # Schema exports
│   │   ├── property.py            # Property-related schemas
│   │   ├── user.py                # User-related schemas
│   │   └── workflow.py            # Workflow & duplicate schemas
│   ├── services/                  # Business logic & external integrations
│   │   ├── auth.py                # Authentication service
│   │   ├── cloudinary_service.py  # Cloudinary file management
│   │   ├── duplicate.py           # Duplicate detection algorithms
│   │   ├── file_storage.py        # File storage abstraction
│   │   ├── property.py            # Property business logic
│   │   └── workflow.py            # Workflow state management
│   └── main.py                    # FastAPI application entry point
├── tests/                         # Test suite
│   ├── conftest.py                # Pytest configuration & fixtures
│   ├── context7_config.py         # Context7-style testing framework
│   ├── playwright_api_tests.py    # Playwright API tests
│   └── test_context7_integration.py # Integration tests
├── alembic/                       # Database migrations (if using Alembic)
├── .env                          # Environment variables
├── requirements.txt              # Python dependencies
├── CLOUDINARY_SETUP.md           # Cloudinary integration guide
└── DEVELOPMENT_GUIDE.md          # This file
```

## 🗂️ Detailed Folder Explanations

### **`app/api/v1/`** - API Layer
Contains all REST API endpoints organized by feature:

#### **`auth.py`** - Authentication & User Management
- **Purpose**: User registration, login, JWT token management
- **Key Features**: FastAPI-Users integration, role-based access control
- **Endpoints**:
  - `POST /api/v1/auth/register` - User registration
  - `POST /api/v1/auth/jwt/login` - User login
  - `POST /api/v1/auth/jwt/logout` - User logout
  - `GET /api/v1/users/me` - Get current user profile
  - `PATCH /api/v1/users/me` - Update user profile

#### **`properties.py`** - Property Management
- **Purpose**: CRUD operations for property records
- **Key Features**: Property lifecycle management, status transitions, attachments
- **Endpoints**:
  - `GET /api/v1/properties/` - List properties with filters
  - `POST /api/v1/properties/` - Create new property
  - `GET /api/v1/properties/{id}` - Get property details
  - `PATCH /api/v1/properties/{id}` - Update property
  - `DELETE /api/v1/properties/{id}` - Delete property
  - `PATCH /api/v1/properties/{id}/status` - Update property status
  - `GET /api/v1/properties/{id}/history` - Get workflow history

#### **`duplicates.py`** - Duplicate Detection
- **Purpose**: Property duplicate detection and management
- **Key Features**: Fuzzy matching, similarity scoring, batch processing
- **Endpoints**:
  - `POST /api/v1/duplicates/check` - Check for duplicates
  - `POST /api/v1/duplicates/merge` - Merge duplicate properties
  - `GET /api/v1/duplicates/potential` - List potential duplicates

#### **`admin.py`** - Administrative Functions
- **Purpose**: Admin-only operations and system management
- **Key Features**: User management, system statistics, reviewer assignment
- **Endpoints**:
  - `GET /api/v1/admin/users` - List all users
  - `GET /api/v1/admin/properties/stats` - Property statistics
  - `PATCH /api/v1/admin/properties/{id}/assign-reviewer` - Assign reviewer
  - `GET /api/v1/admin/system/health` - System health check

#### **`uploads.py`** - File Management
- **Purpose**: File uploads using Cloudinary integration
- **Key Features**: Property attachments, image optimization, thumbnails
- **Endpoints**:
  - `POST /api/v1/uploads/property/{id}/attachment` - Upload property attachment
  - `DELETE /api/v1/uploads/attachment/{id}` - Delete attachment
  - `GET /api/v1/uploads/attachment/{id}/thumbnail` - Get thumbnail URL
  - `POST /api/v1/uploads/test-upload` - Test upload (development)

### **`app/core/`** - Core System Components

#### **`config.py`** - Configuration Management
- **Purpose**: Environment variables and application settings
- **Key Features**: Pydantic settings, validation, type safety
- **Configuration Groups**:
  - Database connection settings
  - Security (JWT secrets, algorithms)
  - CORS origins
  - File upload limits
  - Cloudinary credentials
  - Google Maps API
  - Email SMTP settings

#### **`database.py`** - Database Layer
- **Purpose**: SQLAlchemy configuration and session management
- **Key Features**: Async database connections, session dependency injection
- **Components**:
  - `async_engine` - SQLAlchemy async engine
  - `AsyncSessionLocal` - Session factory
  - `get_async_session()` - FastAPI dependency for database sessions
  - `Base` - SQLAlchemy declarative base

#### **`security.py`** - Security Utilities
- **Purpose**: Password hashing, security helpers
- **Key Features**: bcrypt password hashing, security utilities
- **Functions**:
  - Password verification and hashing
  - Security context management

### **`app/models/`** - Database Models

#### **`enums.py`** - Shared Enumerations
- **PropertyStatus**: 8-stage workflow enum
  ```python
  PROPERTY_SOURCING → PROPERTY_STUDY → PBY_PREPARATION → 
  COUNCIL_APPROVAL → NEGOTIATION → DUE_DILIGENCE → 
  CONTRACT_SIGNING → TAKEOVER
  ```
- **PropertyType**: RESIDENTIAL, COMMERCIAL, INDUSTRIAL, AGRICULTURAL, MIXED_USE
- **UserRole**: ADMIN, MANAGER, AGENT, REVIEWER

#### **`user.py`** - User Model
- **Purpose**: User accounts with FastAPI-Users integration
- **Key Features**: Role-based access, company association, audit fields
- **Relationships**: One-to-many with properties (submitted/reviewed)

#### **`property.py`** - Property Models
- **Property Model**: Core property information
  - Basic details (name, address, coordinates)
  - Financial data (price, currency)
  - Technical specs (lot area, property type, zoning)
  - Workflow management (status, reviewer assignment)
  - Audit trail (created/updated timestamps)

- **PropertyAttachment Model**: Cloudinary file references
  - File metadata (filename, size, MIME type)
  - Cloudinary references (public_id, URLs)
  - Image dimensions (width, height)

#### **`workflow.py`** - Workflow Management
- **WorkflowHistory Model**: Audit trail for status changes
  - Status transitions (from_status → to_status)
  - Change tracking (who, when, why)
  - Notes and comments

### **`app/schemas/`** - API Data Models

#### **`property.py`** - Property API Schemas
- **PropertyBase**: Common property fields
- **PropertyCreate**: Property creation payload
- **PropertyUpdate**: Property update payload
- **PropertyRead**: Property response with relationships
- **PropertyListRead**: Simplified list view
- **PropertyAttachment** schemas: File attachment models

#### **`user.py`** - User API Schemas
- **UserRead**: User profile response
- **UserCreate**: User registration payload
- **UserUpdate**: User update payload
- Based on FastAPI-Users schemas with custom fields

#### **`workflow.py`** - Workflow & Duplicate Schemas
- **StatusUpdateRequest**: Status change payload
- **WorkflowHistoryRead**: Workflow history response
- **DuplicateCheckRequest**: Duplicate detection payload
- **DuplicateResult**: Duplicate detection response
- **DuplicateMergeRequest**: Duplicate merge payload

### **`app/services/`** - Business Logic Layer

#### **`auth.py`** - Authentication Service
- **Purpose**: FastAPI-Users integration and user management
- **Key Features**: User database adapter, authentication backend
- **Functions**:
  - User creation and management
  - Authentication strategy implementation
  - Role-based access control helpers

#### **`property.py`** - Property Business Logic
- **Purpose**: Property CRUD operations and business rules
- **Key Features**: Data validation, relationship management, search/filtering
- **Functions**:
  - Property creation with validation
  - Status transition validation
  - Property search and filtering
  - Relationship management (user assignments)

#### **`workflow.py`** - Workflow State Management
- **Purpose**: Property status transitions and workflow enforcement
- **Key Features**: State machine validation, audit trail creation
- **Functions**:
  - Status transition validation
  - Workflow history creation
  - Business rule enforcement
  - Notification triggers

#### **`duplicate.py`** - Duplicate Detection Service
- **Purpose**: Intelligent property duplicate detection
- **Key Features**: Multi-factor similarity analysis, fuzzy matching
- **Algorithms**:
  - Exact title number matching
  - Levenshtein distance for address similarity
  - Geographic proximity calculation
  - Composite similarity scoring

#### **`cloudinary_service.py`** - Cloudinary Integration
- **Purpose**: File upload, storage, and management via Cloudinary
- **Key Features**: Image optimization, transformations, secure URLs
- **Functions**:
  - File upload with validation
  - Image transformation and optimization
  - URL generation with transformations
  - File deletion and management
  - Folder organization (BDD_CLOUDINARY collection)

#### **`file_storage.py`** - Storage Abstraction
- **Purpose**: High-level file storage interface
- **Key Features**: Cloudinary integration, validation, thumbnails
- **Functions**:
  - Unified file upload interface
  - File type validation
  - Thumbnail generation
  - Error handling and cleanup

### **`tests/`** - Testing Framework

#### **`context7_config.py`** - Context7 Testing Framework
- **Purpose**: Advanced testing patterns with context management
- **Key Features**: Test isolation, database cleanup, fixture management
- **Classes**:
  - `TestContext`: Core testing context manager
  - Fixtures for authenticated and admin contexts
  - Helper methods for test data creation

#### **`playwright_api_tests.py`** - Playwright API Testing
- **Purpose**: End-to-end API testing with Playwright
- **Key Features**: Real HTTP requests, performance testing, concurrent operations
- **Test Types**:
  - API endpoint validation
  - Performance and load testing
  - Error handling scenarios
  - Concurrent request handling

## 🌐 API Documentation

### **Base URL**: `http://localhost:8000/api/v1`

### **Authentication**
All protected endpoints require JWT token in Authorization header:
```bash
Authorization: Bearer <jwt_token>
```

### **Response Format**
All APIs follow consistent response patterns:
```json
{
  "id": 1,
  "field1": "value1",
  "field2": "value2",
  "created_at": "2024-01-01T00:00:00",
  "updated_at": "2024-01-01T00:00:00"
}
```

### **Error Handling**
Standardized error responses:
```json
{
  "detail": "Error message",
  "status_code": 400
}
```

## 🗃️ Database Architecture

### **Core Tables**
1. **`user`** - User accounts and authentication
2. **`properties`** - Property records with workflow status
3. **`property_attachments`** - File references (Cloudinary)
4. **`workflow_history`** - Audit trail for status changes

### **Relationships**
- User → Properties (One-to-Many: submitted_by, reviewer)
- Property → Attachments (One-to-Many)
- Property → WorkflowHistory (One-to-Many)
- User → WorkflowHistory (One-to-Many: changed_by)

### **Indexes**
- User: email (unique), role
- Property: title_number (unique), status, submitted_by_id
- PropertyAttachment: cloudinary_public_id (unique)

## 🚀 Development Workflow

### **Starting Development Server**
```bash
# Activate virtual environment
source venv/bin/activate

# Start development server
uvicorn app.main:app --reload

# Access API documentation
open http://localhost:8000/docs
```

### **Running Tests**
```bash
# All tests
pytest

# Specific test file
pytest tests/test_context7_integration.py -v

# With coverage
pytest --cov=app tests/
```

### **Database Operations**
```bash
# Create tables (already done)
python -c "
import asyncio
from app.core.database import async_engine, Base
from app.models import *

async def create_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

asyncio.run(create_tables())
"
```

## 🔧 Configuration

### **Environment Variables** (`.env`)
```bash
# Database
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/bdd_property_tracker
TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/bdd_property_tracker_test

# Security
SECRET_KEY=your-secret-key
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001

# Cloudinary
CLOUDINARY_CLOUD_NAME=your-cloud-name
CLOUDINARY_API_KEY=your-api-key
CLOUDINARY_API_SECRET=your-api-secret
CLOUDINARY_FOLDER=BDD_CLOUDINARY

# File Upload
MAX_FILE_SIZE=10485760  # 10MB
```

## 📊 Key Features

### **Property Workflow System**
8-stage sequential workflow with validation and audit trail:
1. Property Sourcing
2. Property Study  
3. PBY Preparation
4. Council Approval
5. Negotiation
6. Due Diligence
7. Contract Signing
8. Takeover

### **Duplicate Detection**
Multi-factor duplicate detection system:
- Exact title number matching (100% similarity)
- Fuzzy address matching (Levenshtein distance)
- Geographic proximity (coordinate-based)
- Composite similarity scoring

### **File Management**
Enterprise-grade file storage with Cloudinary:
- Automatic image optimization
- On-demand transformations
- Secure URL generation
- Global CDN delivery
- Organized collection structure

### **Security**
Production-ready security implementation:
- JWT token authentication
- Role-based access control (RBAC)
- Password hashing with bcrypt
- CORS protection
- Input validation and sanitization

---

This development guide provides a comprehensive overview of the BDD Property Tracker backend architecture. For specific implementation details, refer to the individual source files and their inline documentation.