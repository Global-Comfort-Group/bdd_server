"""
Context7-style testing configuration for BDD Server
Provides context-aware testing utilities and fixtures
"""

import asyncio
import pytest
from typing import Dict, Any, AsyncGenerator
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.core.database import get_async_session, Base
from app.core.config import settings

# Test database URL
TEST_DATABASE_URL = settings.TEST_DATABASE_URL or "postgresql+asyncpg://postgres:postgres@localhost/test_bdd"

# Create test engine
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


class TestContext:
    """Context7-style test context manager for BDD Server testing"""
    
    def __init__(self):
        self.client: AsyncClient = None
        self.db_session: AsyncSession = None
        self.test_data: Dict[str, Any] = {}
        self.cleanup_tasks = []
    
    async def setup(self):
        """Setup test context"""
        # Setup database
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        # Create database session
        self.db_session = TestSessionLocal()
        
        # Override database dependency
        async def override_get_db():
            yield self.db_session
        
        app.dependency_overrides[get_async_session] = override_get_db
        
        # Create HTTP client
        self.client = AsyncClient(app=app, base_url="http://test")
        
        return self
    
    async def cleanup(self):
        """Cleanup test context"""
        # Close client
        if self.client:
            await self.client.aclose()
        
        # Close database session
        if self.db_session:
            await self.db_session.close()
        
        # Run cleanup tasks
        for task in self.cleanup_tasks:
            await task()
        
        # Clear dependency overrides
        app.dependency_overrides.clear()
        
        # Drop test tables
        async with test_engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    
    async def create_test_user(self, **kwargs) -> Dict[str, Any]:
        """Create a test user with default or custom data"""
        user_data = {
            "email": "test@example.com",
            "password": "testpassword123",
            "first_name": "Test",
            "last_name": "User",
            "role": "AGENT",
            **kwargs
        }
        
        response = await self.client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201
        
        user = response.json()
        self.test_data[f"user_{user['id']}"] = user
        return user
    
    async def login_user(self, email: str, password: str) -> str:
        """Login user and return authentication token"""
        login_data = {
            "username": email,
            "password": password
        }
        
        response = await self.client.post("/api/v1/auth/jwt/login", data=login_data)
        assert response.status_code == 204
        
        # Extract token from cookies or headers
        # For testing, we'll generate a token manually
        from app.api.v1.auth import create_access_token
        from datetime import timedelta
        from sqlalchemy import select
        from app.models.user import User
        
        result = await self.db_session.execute(select(User).where(User.email == email))
        user = result.scalar_one()
        
        jwt_strategy = get_jwt_strategy()
        token = await jwt_strategy.write_token(user)
        return token
    
    async def create_test_property(self, user_token: str, **kwargs) -> Dict[str, Any]:
        """Create a test property"""
        property_data = {
            "name": "Test Property",
            "address": "123 Test Street, Test City",
            "latitude": 14.5995,
            "longitude": 120.9842,
            "lot_area": 100.5,
            "property_type": "RESIDENTIAL",
            "price": 1000000.00,
            "currency": "PHP",
            "zoning_classification": "R1",
            "title_number": f"TEST-{len(self.test_data)}-2024",
            "description": "A test property",
            **kwargs
        }
        
        headers = {"Authorization": f"Bearer {user_token}"}
        response = await self.client.post("/api/v1/properties/", json=property_data, headers=headers)
        assert response.status_code == 200
        
        property_obj = response.json()
        self.test_data[f"property_{property_obj['id']}"] = property_obj
        return property_obj
    
    def get_auth_headers(self, token: str) -> Dict[str, str]:
        """Get authentication headers for requests"""
        return {"Authorization": f"Bearer {token}"}
    
    async def assert_api_response(self, response, expected_status: int = 200, expected_keys: list = None):
        """Assert API response with helpful error messages"""
        assert response.status_code == expected_status, f"Expected status {expected_status}, got {response.status_code}. Response: {response.text}"
        
        if expected_keys:
            data = response.json()
            for key in expected_keys:
                assert key in data, f"Expected key '{key}' not found in response: {data}"
    
    async def wait_for_condition(self, condition_func, timeout: int = 5, interval: float = 0.1):
        """Wait for a condition to be true (useful for async operations)"""
        start_time = asyncio.get_event_loop().time()
        while True:
            if await condition_func():
                return True
            
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise TimeoutError(f"Condition not met within {timeout} seconds")
            
            await asyncio.sleep(interval)


@pytest.fixture
async def test_context():
    """Context7-style test fixture"""
    context = TestContext()
    await context.setup()
    
    yield context
    
    await context.cleanup()


@pytest.fixture
async def authenticated_context():
    """Test context with authenticated user"""
    context = TestContext()
    await context.setup()
    
    # Create and login test user
    user = await context.create_test_user()
    token = await context.login_user(user["email"], "testpassword123")
    context.test_data["auth_token"] = token
    context.test_data["current_user"] = user
    
    yield context
    
    await context.cleanup()


@pytest.fixture
async def admin_context():
    """Test context with admin user"""
    context = TestContext()
    await context.setup()
    
    # Create and login admin user
    admin = await context.create_test_user(
        email="admin@example.com",
        role="ADMIN"
    )
    token = await context.login_user(admin["email"], "testpassword123")
    context.test_data["auth_token"] = token
    context.test_data["current_user"] = admin
    
    yield context
    
    await context.cleanup()


# Context7-style test decorators
def context_test(func):
    """Decorator for context-aware tests"""
    @pytest.mark.asyncio
    async def wrapper(*args, **kwargs):
        return await func(*args, **kwargs)
    return wrapper


def api_test(func):
    """Decorator for API tests with context"""
    @pytest.mark.asyncio
    async def wrapper(test_context: TestContext, *args, **kwargs):
        return await func(test_context, *args, **kwargs)
    return wrapper