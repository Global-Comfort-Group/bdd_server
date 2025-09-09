"""
Advanced Playwright API Testing for BDD Server
Provides comprehensive API testing with Playwright
"""

import pytest
from playwright.async_api import async_playwright, APIRequestContext, Playwright
from typing import Dict, Any
import json

from tests.context7_config import TestContext


class PlaywrightAPITester:
    """Advanced Playwright-based API testing utility"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.playwright: Playwright = None
        self.api_context: APIRequestContext = None
        self.auth_token: str = None
    
    async def setup(self):
        """Setup Playwright API context"""
        self.playwright = await async_playwright().start()
        self.api_context = await self.playwright.request.new_context(
            base_url=self.base_url,
            extra_http_headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
        return self
    
    async def cleanup(self):
        """Cleanup Playwright resources"""
        if self.api_context:
            await self.api_context.dispose()
        if self.playwright:
            await self.playwright.stop()
    
    async def register_user(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Register a new user via API"""
        response = await self.api_context.post(
            "/api/v1/auth/register",
            data=json.dumps(user_data)
        )
        
        assert response.ok, f"Registration failed: {await response.text()}"
        return await response.json()
    
    async def login_user(self, email: str, password: str) -> str:
        """Login user and return auth token"""
        # Create form data for login
        form_data = f"username={email}&password={password}"
        
        response = await self.api_context.post(
            "/api/v1/auth/jwt/login",
            data=form_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        assert response.status == 204, f"Login failed: {await response.text()}"
        
        # Extract token from cookies
        cookies = await self.api_context.storage_state()
        for cookie in cookies.get("cookies", []):
            if cookie["name"] == "fastapiusersauth":
                return cookie["value"]
        
        # If no cookie, create a mock token for testing
        return "mock_jwt_token_for_testing"
    
    async def set_auth_token(self, token: str):
        """Set authentication token for subsequent requests"""
        self.auth_token = token
    
    def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers"""
        if self.auth_token:
            return {"Authorization": f"Bearer {self.auth_token}"}
        return {}
    
    async def create_property(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a property via API"""
        response = await self.api_context.post(
            "/api/v1/properties/",
            data=json.dumps(property_data),
            headers=self.get_auth_headers()
        )
        
        assert response.ok, f"Property creation failed: {await response.text()}"
        return await response.json()
    
    async def get_properties(self, **params) -> list:
        """Get properties list via API"""
        query_params = "&".join([f"{k}={v}" for k, v in params.items() if v is not None])
        url = "/api/v1/properties/"
        if query_params:
            url += f"?{query_params}"
        
        response = await self.api_context.get(url, headers=self.get_auth_headers())
        assert response.ok, f"Get properties failed: {await response.text()}"
        return await response.json()
    
    async def update_property_status(self, property_id: int, new_status: str, notes: str = None):
        """Update property status via API"""
        status_data = {"new_status": new_status}
        if notes:
            status_data["notes"] = notes
        
        response = await self.api_context.patch(
            f"/api/v1/properties/{property_id}/status",
            data=json.dumps(status_data),
            headers=self.get_auth_headers()
        )
        
        assert response.ok, f"Status update failed: {await response.text()}"
        return await response.json()
    
    async def check_duplicates(self, property_data: Dict[str, Any]) -> list:
        """Check for duplicate properties via API"""
        response = await self.api_context.post(
            "/api/v1/duplicates/check",
            data=json.dumps(property_data),
            headers=self.get_auth_headers()
        )
        
        assert response.ok, f"Duplicate check failed: {await response.text()}"
        return await response.json()
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform health check"""
        response = await self.api_context.get("/health")
        assert response.ok, f"Health check failed: {await response.text()}"
        return await response.json()
    
    async def test_api_performance(self, endpoint: str, method: str = "GET", data: Dict = None) -> Dict[str, Any]:
        """Test API endpoint performance"""
        import time
        
        start_time = time.time()
        
        if method.upper() == "GET":
            response = await self.api_context.get(endpoint, headers=self.get_auth_headers())
        elif method.upper() == "POST":
            response = await self.api_context.post(
                endpoint, 
                data=json.dumps(data) if data else None,
                headers=self.get_auth_headers()
            )
        elif method.upper() == "PATCH":
            response = await self.api_context.patch(
                endpoint,
                data=json.dumps(data) if data else None,
                headers=self.get_auth_headers()
            )
        else:
            raise ValueError(f"Unsupported method: {method}")
        
        end_time = time.time()
        response_time = end_time - start_time
        
        return {
            "status_code": response.status,
            "response_time_ms": response_time * 1000,
            "ok": response.ok,
            "headers": dict(response.headers),
            "response_size": len(await response.text())
        }


@pytest.fixture
async def playwright_api():
    """Playwright API testing fixture"""
    tester = PlaywrightAPITester()
    await tester.setup()
    
    yield tester
    
    await tester.cleanup()


@pytest.fixture
async def authenticated_playwright_api():
    """Authenticated Playwright API testing fixture"""
    tester = PlaywrightAPITester()
    await tester.setup()
    
    # Create and login test user
    user_data = {
        "email": "playwright@test.com",
        "password": "testpassword123",
        "first_name": "Playwright",
        "last_name": "User",
        "role": "AGENT"
    }
    
    await tester.register_user(user_data)
    token = await tester.login_user(user_data["email"], user_data["password"])
    await tester.set_auth_token(token)
    
    yield tester
    
    await tester.cleanup()


# Advanced API Tests using Playwright
@pytest.mark.asyncio
async def test_api_health_performance(playwright_api: PlaywrightAPITester):
    """Test API health endpoint performance"""
    performance = await playwright_api.test_api_performance("/health")
    
    assert performance["ok"], "Health check should succeed"
    assert performance["response_time_ms"] < 1000, "Health check should respond within 1 second"
    assert performance["status_code"] == 200, "Health check should return 200"


@pytest.mark.asyncio
async def test_complete_property_workflow(authenticated_playwright_api: PlaywrightAPITester):
    """Test complete property workflow using Playwright"""
    api = authenticated_playwright_api
    
    # 1. Create property
    property_data = {
        "name": "Playwright Test Property",
        "address": "123 Playwright Street",
        "latitude": 14.5995,
        "longitude": 120.9842,
        "lot_area": 200.0,
        "property_type": "RESIDENTIAL",
        "price": 2000000.00,
        "currency": "PHP",
        "zoning_classification": "R1",
        "title_number": "PW-001-2024",
        "description": "Property created via Playwright testing"
    }
    
    property_obj = await api.create_property(property_data)
    assert property_obj["name"] == property_data["name"]
    assert property_obj["status"] == "PROPERTY_SOURCING"
    
    property_id = property_obj["id"]
    
    # 2. Update status through workflow
    updated_property = await api.update_property_status(
        property_id, 
        "PROPERTY_STUDY", 
        "Moving to study phase via Playwright"
    )
    assert updated_property["status"] == "PROPERTY_STUDY"
    
    # 3. Check duplicates
    duplicates = await api.check_duplicates(property_data)
    assert len(duplicates) >= 1, "Should find the property itself as a duplicate"
    assert duplicates[0]["similarity_score"] == 1.0, "Exact match should have score 1.0"
    
    # 4. Get properties list
    properties = await api.get_properties()
    assert len(properties) >= 1, "Should return at least the created property"
    
    found_property = next((p for p in properties if p["id"] == property_id), None)
    assert found_property is not None, "Created property should be in the list"


@pytest.mark.asyncio
async def test_api_error_handling(playwright_api: PlaywrightAPITester):
    """Test API error handling with Playwright"""
    api = playwright_api
    
    # Test unauthorized access
    response = await api.api_context.get("/api/v1/properties/")
    assert response.status == 401, "Should return 401 for unauthorized access"
    
    # Test invalid endpoint
    response = await api.api_context.get("/api/v1/nonexistent")
    assert response.status == 404, "Should return 404 for nonexistent endpoint"
    
    # Test invalid data
    response = await api.api_context.post(
        "/api/v1/auth/register",
        data=json.dumps({"invalid": "data"})
    )
    assert response.status in [400, 422], "Should return 400/422 for invalid registration data"


@pytest.mark.asyncio
async def test_concurrent_api_requests(authenticated_playwright_api: PlaywrightAPITester):
    """Test concurrent API requests performance"""
    import asyncio
    
    api = authenticated_playwright_api
    
    # Create multiple properties concurrently
    tasks = []
    for i in range(5):
        property_data = {
            "name": f"Concurrent Property {i}",
            "address": f"{i} Concurrent Street",
            "latitude": 14.5995 + i * 0.001,
            "longitude": 120.9842 + i * 0.001,
            "lot_area": 100.0 + i * 10,
            "property_type": "RESIDENTIAL",
            "price": 1000000.00 + i * 100000,
            "currency": "PHP",
            "zoning_classification": "R1",
            "title_number": f"CONC-{i:03d}-2024",
            "description": f"Concurrent test property {i}"
        }
        tasks.append(api.create_property(property_data))
    
    # Execute all tasks concurrently
    results = await asyncio.gather(*tasks)
    
    assert len(results) == 5, "All concurrent requests should succeed"
    for i, result in enumerate(results):
        assert result["name"] == f"Concurrent Property {i}"
        assert "id" in result
    
    # Verify all properties were created
    properties = await api.get_properties()
    concurrent_properties = [p for p in properties if p["name"].startswith("Concurrent Property")]
    assert len(concurrent_properties) == 5, "All concurrent properties should be retrievable"


@pytest.mark.asyncio 
async def test_api_load_performance(authenticated_playwright_api: PlaywrightAPITester):
    """Test API load performance"""
    api = authenticated_playwright_api
    
    # Test multiple requests to properties endpoint
    response_times = []
    
    for _ in range(10):
        performance = await api.test_api_performance("/api/v1/properties/")
        response_times.append(performance["response_time_ms"])
        assert performance["ok"], "All requests should succeed"
    
    # Calculate statistics
    avg_response_time = sum(response_times) / len(response_times)
    max_response_time = max(response_times)
    
    assert avg_response_time < 500, f"Average response time should be under 500ms, got {avg_response_time:.2f}ms"
    assert max_response_time < 1000, f"Max response time should be under 1000ms, got {max_response_time:.2f}ms"
    
    print(f"API Load Test Results:")
    print(f"  Average response time: {avg_response_time:.2f}ms")
    print(f"  Max response time: {max_response_time:.2f}ms")
    print(f"  Min response time: {min(response_times):.2f}ms")