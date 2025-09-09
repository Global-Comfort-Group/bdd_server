import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    """Test user registration."""
    user_data = {
        "email": "test@example.com",
        "password": "testpassword123",
        "first_name": "Test",
        "last_name": "User",
        "role": "AGENT"
    }
    
    response = await client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201
    
    data = response.json()
    assert data["email"] == user_data["email"]
    assert data["first_name"] == user_data["first_name"]
    assert data["last_name"] == user_data["last_name"]
    assert data["role"] == user_data["role"]
    assert "id" in data


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """Test registration with duplicate email."""
    user_data = {
        "email": "duplicate@example.com",
        "password": "testpassword123",
        "first_name": "Test",
        "last_name": "User",
        "role": "AGENT"
    }
    
    # First registration should succeed
    response = await client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 201
    
    # Second registration with same email should fail
    response = await client.post("/api/v1/auth/register", json=user_data)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    """Test user login."""
    # First register a user
    user_data = {
        "email": "login@example.com",
        "password": "testpassword123",
        "first_name": "Login",
        "last_name": "User",
        "role": "AGENT"
    }
    
    await client.post("/api/v1/auth/register", json=user_data)
    
    # Now login
    login_data = {
        "username": "login@example.com",
        "password": "testpassword123"
    }
    
    response = await client.post("/api/v1/auth/jwt/login", data=login_data)
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    """Test login with wrong password."""
    # First register a user
    user_data = {
        "email": "wrongpass@example.com",
        "password": "testpassword123",
        "first_name": "Wrong",
        "last_name": "Password",
        "role": "AGENT"
    }
    
    await client.post("/api/v1/auth/register", json=user_data)
    
    # Login with wrong password
    login_data = {
        "username": "wrongpass@example.com",
        "password": "wrongpassword"
    }
    
    response = await client.post("/api/v1/auth/jwt/login", data=login_data)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_current_user(client: AsyncClient, agent_token: str):
    """Test getting current user information."""
    headers = {"Authorization": f"Bearer {agent_token}"}
    
    response = await client.get("/api/v1/users/me", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["email"] == "agent@test.com"
    assert data["role"] == "AGENT"


@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient):
    """Test accessing protected endpoint without token."""
    response = await client.get("/api/v1/users/me")
    assert response.status_code == 401