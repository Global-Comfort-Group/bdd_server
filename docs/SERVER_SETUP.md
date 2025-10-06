# BDD Property Tracker - Server Setup Guide

## Project Overview
**FastAPI Backend** for BDD Property Tracker system with PostgreSQL database and Railway deployment.

## Tech Stack
- **Backend**: FastAPI with Python 3.11+
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT tokens with custom auth implementation
- **File Storage**: Local storage or cloud (Railway compatible)
- **Validation**: Pydantic v2
- **Migration**: Alembic
- **Testing**: pytest with async support
- **Deployment**: Railway

## Project Structure
```
bdd_server/
├── app/
│   ├── api/                    # API routes
│   │   ├── v1/                # API version 1
│   │   │   ├── auth.py       # Authentication endpoints
│   │   │   ├── properties.py # Property management
│   │   │   ├── users.py      # User management
│   │   │   ├── duplicates.py # Duplicate detection
│   │   │   └── admin.py      # Admin endpoints
│   │   └── deps.py           # Dependencies
│   ├── core/                  # Core configuration
│   │   ├── config.py         # Settings
│   │   ├── security.py       # Security utilities
│   │   └── database.py       # Database connection
│   ├── models/               # SQLAlchemy models
│   │   ├── user.py          # User model
│   │   ├── property.py      # Property model
│   │   └── workflow.py      # Workflow state model
│   ├── schemas/              # Pydantic schemas
│   │   ├── user.py          # User schemas
│   │   ├── property.py      # Property schemas
│   │   └── workflow.py      # Workflow schemas
│   ├── services/             # Business logic
│   │   ├── auth.py          # Authentication service
│   │   ├── property.py      # Property service
│   │   ├── duplicate.py     # Duplicate detection
│   │   ├── workflow.py      # Workflow management
│   │   └── file_storage.py  # File handling
│   ├── utils/                # Utility functions
│   │   ├── email.py         # Email utilities
│   │   ├── geocoding.py     # Location utilities
│   │   └── validators.py    # Custom validators
│   └── main.py               # FastAPI application
├── alembic/                  # Database migrations
├── tests/                    # Test files
├── requirements.txt          # Python dependencies
├── .env.example             # Environment template
├── Dockerfile               # Railway deployment
├── railway.toml             # Railway configuration
└── README.md
```

## Required Dependencies

### Core Dependencies (`requirements.txt`)
```txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
alembic==1.12.1
pydantic==2.5.0
pydantic-settings==2.1.0

# Authentication
# Authentication handled with custom JWT implementation
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6

# File handling
python-magic==0.4.27
pillow==10.1.0

# Utilities
python-decouple==3.8
httpx==0.25.2
geopy==2.4.0
fuzzywuzzy==0.18.0
python-levenshtein==0.23.0
```

### Development Dependencies
```txt
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.2
black==23.11.0
isort==5.12.0
flake8==6.1.0
```

## Environment Variables
Create `.env`:
```env
# Database
DATABASE_URL=postgresql://username:password@localhost:5432/bdd_property_tracker
TEST_DATABASE_URL=postgresql://username:password@localhost:5432/bdd_property_tracker_test

# Security
SECRET_KEY=your-super-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# CORS
ALLOWED_ORIGINS=http://localhost:3000,https://your-frontend-domain.com

# File Upload
MAX_FILE_SIZE=10485760  # 10MB
UPLOAD_DIRECTORY=./uploads

# Google Services (optional)
GOOGLE_MAPS_API_KEY=your-google-maps-server-key

# Email (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

## Database Models

### User Model
```python
# app/models/user.py
class User(SQLAlchemyBaseUserTable[int], Base):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    first_name: Mapped[str] = mapped_column(String(50))
    last_name: Mapped[str] = mapped_column(String(50))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole))
    company: Mapped[str] = mapped_column(String(100), nullable=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    properties: Mapped[List["Property"]] = relationship(back_populates="submitted_by")
```

### Property Model
```python
# app/models/property.py
class Property(Base):
    __tablename__ = "properties"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    address: Mapped[str] = mapped_column(String(500))
    latitude: Mapped[float] = mapped_column(Float, nullable=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=True)
    lot_area: Mapped[float] = mapped_column(Float)
    property_type: Mapped[PropertyType] = mapped_column(Enum(PropertyType))
    price: Mapped[Decimal] = mapped_column(Numeric(15, 2))
    currency: Mapped[str] = mapped_column(String(3), default="PHP")
    zoning_classification: Mapped[str] = mapped_column(String(100))
    title_number: Mapped[str] = mapped_column(String(100), unique=True)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    
    # Status and workflow
    status: Mapped[PropertyStatus] = mapped_column(Enum(PropertyStatus), default=PropertyStatus.PROPERTY_SOURCING)
    
    # Metadata
    submitted_by_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"))
    reviewer_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    submitted_by: Mapped["User"] = relationship(foreign_keys=[submitted_by_id])
    reviewer: Mapped["User"] = relationship(foreign_keys=[reviewer_id])
    attachments: Mapped[List["PropertyAttachment"]] = relationship(back_populates="property")
    workflow_history: Mapped[List["WorkflowHistory"]] = relationship(back_populates="property")
```

### Workflow State Machine
```python
# app/models/workflow.py
class PropertyStatus(str, Enum):
    PROPERTY_SOURCING = "PROPERTY_SOURCING"
    PROPERTY_STUDY = "PROPERTY_STUDY"
    PBY_PREPARATION = "PBY_PREPARATION"
    COUNCIL_APPROVAL = "COUNCIL_APPROVAL"
    NEGOTIATION = "NEGOTIATION"
    DUE_DILIGENCE = "DUE_DILIGENCE"
    CONTRACT_SIGNING = "CONTRACT_SIGNING"
    TAKEOVER = "TAKEOVER"

class WorkflowHistory(Base):
    __tablename__ = "workflow_history"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    property_id: Mapped[int] = mapped_column(Integer, ForeignKey("properties.id"))
    from_status: Mapped[PropertyStatus] = mapped_column(Enum(PropertyStatus), nullable=True)
    to_status: Mapped[PropertyStatus] = mapped_column(Enum(PropertyStatus))
    changed_by_id: Mapped[int] = mapped_column(Integer, ForeignKey("user.id"))
    notes: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationships
    property: Mapped["Property"] = relationship(back_populates="workflow_history")
    changed_by: Mapped["User"] = relationship()
```

## API Endpoints

### Authentication Routes
```python
# app/api/v1/auth.py
router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/register")
@router.post("/login")
@router.post("/logout")
@router.get("/me")
@router.patch("/me")
```

### Property Routes
```python
# app/api/v1/properties.py
router = APIRouter(prefix="/properties", tags=["properties"])

@router.get("/")  # List properties with filters
@router.post("/")  # Create property
@router.get("/{property_id}")  # Get property details
@router.patch("/{property_id}")  # Update property
@router.delete("/{property_id}")  # Delete property
@router.post("/{property_id}/attachments")  # Upload attachments
@router.patch("/{property_id}/status")  # Update status
@router.get("/{property_id}/history")  # Get workflow history
```

### Duplicate Detection Routes
```python
# app/api/v1/duplicates.py
router = APIRouter(prefix="/duplicates", tags=["duplicates"])

@router.get("/check")  # Check for duplicates
@router.post("/merge")  # Merge duplicate properties
@router.post("/{property_id}/mark-duplicate")  # Mark as duplicate
```

### Admin Routes
```python
# app/api/v1/admin.py
router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/users")  # List all users
@router.post("/users")  # Create user
@router.patch("/users/{user_id}")  # Update user
@router.delete("/users/{user_id}")  # Delete user
@router.get("/properties/stats")  # Property statistics
@router.patch("/properties/{property_id}/assign-reviewer")  # Assign reviewer
```

## Services Implementation

### Duplicate Detection Service
```python
# app/services/duplicate.py
class DuplicateDetectionService:
    @staticmethod
    async def check_duplicates(property_data: PropertyCreate) -> List[Property]:
        # Check by title number (exact match)
        # Check by address (fuzzy match)
        # Check by coordinates (proximity)
        pass
    
    @staticmethod
    async def calculate_similarity_score(prop1: Property, prop2: Property) -> float:
        # Calculate similarity based on multiple factors
        pass
```

### Workflow Service
```python
# app/services/workflow.py
class WorkflowService:
    VALID_TRANSITIONS = {
        PropertyStatus.PROPERTY_SOURCING: [PropertyStatus.PROPERTY_STUDY],
        PropertyStatus.PROPERTY_STUDY: [PropertyStatus.PBY_PREPARATION],
        # ... other transitions
    }
    
    @classmethod
    async def transition_status(
        cls, 
        property_id: int, 
        new_status: PropertyStatus,
        user_id: int,
        notes: str = None
    ) -> Property:
        # Validate transition
        # Update property status
        # Create workflow history entry
        pass
```

## Setup Instructions

### 1. Virtual Environment
```bash
cd bdd_server
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment Setup
```bash
cp .env.example .env
# Edit .env with your configurations
```

### 4. Database Setup
```bash
# Create database
createdb bdd_property_tracker

# Run migrations
alembic upgrade head
```

### 5. Development Server
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Database Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "Add new table"

# Apply migrations
alembic upgrade head

# Downgrade
alembic downgrade -1
```

## Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_properties.py -v
```

## Railway Deployment

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### railway.toml
```toml
[build]
builder = "dockerfile"

[deploy]
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "always"
```

## API Documentation
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
- OpenAPI JSON: `http://localhost:8000/openapi.json`

## Security Features
- JWT token authentication
- Password hashing with bcrypt
- Input validation with Pydantic
- SQL injection prevention with SQLAlchemy
- File upload validation
- Rate limiting (optional)
- CORS configuration

## Monitoring and Logging
- Structured logging with Python logging
- Request/response logging middleware
- Error tracking and alerting
- Performance monitoring
- Health check endpoints

This setup provides a robust, scalable backend for the BDD Property Tracker system with all required features and production-ready configurations.