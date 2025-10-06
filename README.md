# BDD Property Tracker - Backend Server

FastAPI backend server for the BDD Property Tracker system with PostgreSQL database, comprehensive property workflow management, and duplicate detection capabilities.

## Features

- **🏗️ FastAPI Backend** with automatic OpenAPI documentation
- **🔐 JWT Authentication** using FastAPI-Users
- **📊 Property Management** with 8-stage workflow system
- **🔍 Duplicate Detection** using fuzzy matching algorithms
- **🗄️ PostgreSQL Database** with SQLAlchemy ORM
- **📝 Database Migrations** with Alembic
- **🧪 Comprehensive Testing** with pytest and Playwright
- **🚀 Production Ready** with Docker and Railway deployment
- **📁 File Upload System** for property attachments
- **🎯 Role-based Access Control** (Admin, Manager, Agent, Reviewer)

## Tech Stack

- **Backend**: FastAPI with Python 3.11+
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT tokens with FastAPI-Users
- **File Storage**: Local storage (Railway compatible)
- **Validation**: Pydantic v2
- **Migration**: Alembic
- **Testing**: pytest with async support and Playwright
- **Deployment**: Railway with Docker support

## Quick Start

### 1. Environment Setup

```bash
# Clone and navigate to project
cd bdd_server

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Database Setup

Create your `.env` file:

```bash
cp .env.example .env
# Edit .env with your database credentials
```

```bash
# Create database
createdb bdd_property_tracker

# Run migrations
alembic upgrade head
```

### 3. Development Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Property Workflow System

The system implements an 8-stage property workflow:

1. **PROPERTY_SOURCING** → 2. **PROPERTY_STUDY** → 3. **PBY_PREPARATION** → 4. **COUNCIL_APPROVAL** → 5. **NEGOTIATION** → 6. **DUE_DILIGENCE** → 7. **CONTRACT_SIGNING** → 8. **TAKEOVER**

Each transition is validated and tracked with full audit history.

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/jwt/login` - Login
- `GET /api/v1/users/me` - Get current user

### Properties
- `GET /api/v1/properties/` - List properties
- `POST /api/v1/properties/` - Create property
- `GET /api/v1/properties/{id}` - Get property details
- `PATCH /api/v1/properties/{id}` - Update property
- `PATCH /api/v1/properties/{id}/status` - Update workflow status
- `POST /api/v1/properties/{id}/attachments` - Upload files

### Duplicate Detection
- `POST /api/v1/duplicates/check` - Check for duplicates
- `POST /api/v1/duplicates/{id}/mark-duplicate` - Mark as duplicate
- `GET /api/v1/duplicates/{id}/similarity/{id2}` - Calculate similarity

### Admin
- `GET /api/v1/admin/users` - List users (admin only)
- `GET /api/v1/admin/properties/stats` - Property statistics
- `PATCH /api/v1/admin/properties/{id}/assign-reviewer` - Assign reviewer

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run specific test file
pytest tests/test_properties.py -v

# Run Playwright tests
playwright test
```

## Development Commands

```bash
# Format code
black app/ tests/

# Sort imports
isort app/ tests/

# Lint code
flake8 app/ tests/

# Type checking
mypy app/
```

## Database Migrations

```bash
# Create new migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

## Docker Deployment

### Local Development
```bash
# Start with Docker Compose
docker-compose up --build

# Stop services
docker-compose down
```

### Production Build
```bash
# Build image
docker build -t bdd-property-tracker .

# Run container
docker run -p 8000:8000 \
  -e DATABASE_URL="your-db-url" \
  -e SECRET_KEY="your-secret" \
  bdd-property-tracker
```

## Railway Deployment

1. Connect your GitHub repository to Railway
2. Set environment variables in Railway dashboard:
   - `DATABASE_URL` (automatically provided)
   - `SECRET_KEY`
   - `ALLOWED_ORIGINS`
   - `GOOGLE_MAPS_API_KEY` (optional)
3. Deploy automatically on git push

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `DATABASE_URL` | PostgreSQL connection string | ✅ | - |
| `SECRET_KEY` | JWT secret key | ✅ | - |
| `ALLOWED_ORIGINS` | CORS allowed origins | ✅ | - |
| `UPLOAD_DIRECTORY` | File upload directory | ❌ | ./uploads |
| `MAX_FILE_SIZE` | Max file size in bytes | ❌ | 10MB |
| `GOOGLE_MAPS_API_KEY` | Google Maps API key | ❌ | - |
| `SMTP_HOST` | Email SMTP host | ❌ | - |

## Architecture

The application follows a clean architecture pattern:

- **`app/main.py`** - FastAPI application setup
- **`app/core/`** - Core configuration and database
- **`app/models/`** - SQLAlchemy database models
- **`app/schemas/`** - Pydantic request/response schemas
- **`app/services/`** - Business logic layer
- **`app/api/`** - API route handlers
- **`app/utils/`** - Utility functions and helpers

## Security Features

- JWT token authentication with FastAPI-Users
- Password hashing with bcrypt
- Input validation with Pydantic
- SQL injection prevention with SQLAlchemy
- File upload validation and sanitization
- CORS configuration
- Role-based access control

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License.

