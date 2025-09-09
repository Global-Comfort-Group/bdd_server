import asyncio
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import get_async_session, Base
from app.core.config import settings


# Test database URL
TEST_DATABASE_URL = settings.TEST_DATABASE_URL or "postgresql+asyncpg://test:test@localhost/test_bdd"

# Create test engine
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_db():
    """Create test database tables and clean up after tests."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield
    
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session(test_db):
    """Create a test database session."""
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture
async def client(db_session):
    """Create test HTTP client with database session override."""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_async_session] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


@pytest.fixture
async def admin_token(client: AsyncClient):
    """Create admin user and return auth token."""
    # Register admin user
    admin_data = {
        "email": "admin@test.com",
        "password": "testpassword123",
        "first_name": "Admin",
        "last_name": "User",
        "role": "ADMIN"
    }
    
    response = await client.post("/api/v1/auth/register", json=admin_data)
    assert response.status_code == 201
    
    # Login to get token
    login_data = {
        "username": "admin@test.com",
        "password": "testpassword123"
    }
    
    response = await client.post("/api/v1/auth/jwt/login", data=login_data)
    assert response.status_code == 204
    
    # Extract token from cookie or header
    # For testing purposes, we'll create a token manually
    from app.services.auth import get_user_manager
    from app.api.deps import get_user_db
    from app.api.v1.auth import auth_backend
    
    # Get user
    from sqlalchemy import select
    from app.models.user import User
    
    async with TestSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == "admin@test.com"))
        user = result.scalar_one()
        
        # Generate token
        from app.api.v1.auth import get_jwt_strategy
        jwt_strategy = get_jwt_strategy()
        token = await jwt_strategy.write_token(user)
        
        return token


@pytest.fixture
async def agent_token(client: AsyncClient):
    """Create agent user and return auth token."""
    # Register agent user
    agent_data = {
        "email": "agent@test.com",
        "password": "testpassword123",
        "first_name": "Agent",
        "last_name": "User",
        "role": "AGENT"
    }
    
    response = await client.post("/api/v1/auth/register", json=agent_data)
    assert response.status_code == 201
    
    # Get user and generate token
    from sqlalchemy import select
    from app.models.user import User
    
    async with TestSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == "agent@test.com"))
        user = result.scalar_one()
        
        from app.api.v1.auth import get_jwt_strategy
        jwt_strategy = get_jwt_strategy()
        token = await jwt_strategy.write_token(user)
        
        return token


@pytest.fixture
async def sample_property_data():
    """Sample property data for testing."""
    return {
        "name": "Test Property",
        "address": "123 Test Street, Test City",
        "latitude": 14.5995,
        "longitude": 120.9842,
        "lot_area": 100.5,
        "property_type": "RESIDENTIAL",
        "price": 1000000.00,
        "currency": "PHP",
        "zoning_classification": "R1",
        "title_number": "TEST-001-2023",
        "description": "A test property for unit testing"
    }