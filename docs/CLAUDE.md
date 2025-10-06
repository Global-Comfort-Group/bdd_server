# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Server Development
```bash
# Start development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Install dependencies
pip install -r requirements.txt

# Set up virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Database Management
```bash
# Create new migration
alembic revision --autogenerate -m "Migration description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Create database
createdb bdd_property_tracker
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_properties.py -v
```

### Code Quality
```bash
# Format code
black app/ tests/

# Sort imports
isort app/ tests/

# Lint code
flake8 app/ tests/
```

## Architecture Overview

### Core System Design
This is a **BDD Property Tracker** built as a FastAPI backend with PostgreSQL. The system manages real estate properties through an 8-stage workflow process from sourcing to takeover.

### Key Architectural Components

**Authentication & Authorization**
- JWT token-based authentication with account approval workflow
- Role-based access control (different user roles with varying permissions)
- User management with company associations

**Property Workflow State Machine**
The system implements a strict workflow with 8 sequential stages:
1. PROPERTY_SOURCING → 2. PROPERTY_STUDY → 3. PBY_PREPARATION → 4. COUNCIL_APPROVAL → 5. NEGOTIATION → 6. DUE_DILIGENCE → 7. CONTRACT_SIGNING → 8. TAKEOVER

Each transition is tracked in `WorkflowHistory` with audit trail of who made changes and when.

**Duplicate Detection System**
Multi-layered duplicate detection using:
- Exact title number matching
- Fuzzy address matching with Levenshtein distance
- Geographic proximity detection using coordinates
- Similarity scoring algorithm combining multiple factors

**Data Models Relationships**
- `User` model with custom authentication
- `Property` model with workflow status tracking and geographic data
- `WorkflowHistory` for audit trails
- `PropertyAttachment` for file management
- Foreign key relationships linking users to properties they submit/review

**Service Layer Architecture**
- `AuthService`: User authentication and token management
- `PropertyService`: CRUD operations and business logic
- `DuplicateDetectionService`: Fuzzy matching and similarity algorithms
- `WorkflowService`: State transition validation and history tracking
- `FileStorageService`: Upload handling with validation

### API Design Patterns

**Versioned API Structure**
All endpoints under `/api/v1/` with clear resource-based routing:
- `/auth/*` - Authentication operations
- `/properties/*` - Property CRUD and status management
- `/duplicates/*` - Duplicate detection and merging
- `/admin/*` - Administrative functions

**Status Management**
Properties can only transition between adjacent workflow stages. The `WorkflowService` validates all transitions and maintains history.

**File Upload System**
Supports property attachments with validation for file types, sizes, and storage management compatible with Railway deployment.

## Environment Configuration

### Required Environment Variables
```env
DATABASE_URL=postgresql://username:password@localhost:5432/bdd_property_tracker
SECRET_KEY=your-super-secret-key-here
ALLOWED_ORIGINS=http://localhost:3000
MAX_FILE_SIZE=10485760  # 10MB
GOOGLE_MAPS_API_KEY=optional-for-geocoding
```

### Railway Deployment
The system is configured for Railway deployment with:
- `railway.toml` configuration
- Health check endpoint at `/health`
- PostgreSQL service integration
- Environment-based configuration management

### Database Schema Notes
- Uses SQLAlchemy 2.0 with mapped_column syntax
- Enum types for status and role management  
- Proper indexing on frequently queried fields (email, title_number)
- Audit timestamps on all major entities
- Foreign key constraints maintaining referential integrity