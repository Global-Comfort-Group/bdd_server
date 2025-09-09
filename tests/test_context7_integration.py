"""
Context7-style Integration Tests for BDD Server
Demonstrates advanced testing patterns with context management
"""

import pytest
from tests.context7_config import (
    TestContext, 
    test_context, 
    authenticated_context, 
    admin_context,
    context_test,
    api_test
)


@api_test
async def test_user_registration_flow(test_context: TestContext):
    """Test complete user registration and authentication flow"""
    # Test user registration
    user_data = {
        "email": "context7@test.com",
        "password": "securepassword123",
        "first_name": "Context",
        "last_name": "Seven",
        "role": "AGENT",
        "company": "Test Company",
        "phone": "+63917123456"
    }
    
    # Register user
    response = await test_context.client.post("/api/v1/auth/register", json=user_data)
    await test_context.assert_api_response(
        response, 
        expected_status=201,
        expected_keys=["id", "email", "first_name", "last_name", "role"]
    )
    
    user = response.json()
    assert user["email"] == user_data["email"]
    assert user["role"] == user_data["role"]
    assert user["company"] == user_data["company"]
    
    # Test login
    token = await test_context.login_user(user_data["email"], user_data["password"])
    assert token is not None
    
    # Test authenticated request
    headers = test_context.get_auth_headers(token)
    me_response = await test_context.client.get("/api/v1/users/me", headers=headers)
    await test_context.assert_api_response(me_response, expected_keys=["id", "email"])
    
    me_data = me_response.json()
    assert me_data["email"] == user_data["email"]


@api_test
async def test_property_lifecycle_management(authenticated_context: TestContext):
    """Test complete property lifecycle with context management"""
    token = authenticated_context.test_data["auth_token"]
    headers = authenticated_context.get_auth_headers(token)
    
    # 1. Create property
    property_data = {
        "name": "Context7 Lifecycle Property",
        "address": "456 Lifecycle Avenue, Context City",
        "latitude": 14.6042,
        "longitude": 120.9822,
        "lot_area": 250.0,
        "property_type": "COMMERCIAL",
        "price": 5000000.00,
        "currency": "PHP",
        "zoning_classification": "C1",
        "title_number": "LIFE-001-2024",
        "description": "Property for lifecycle testing"
    }
    
    create_response = await authenticated_context.client.post(
        "/api/v1/properties/", 
        json=property_data, 
        headers=headers
    )
    await authenticated_context.assert_api_response(
        create_response,
        expected_keys=["id", "name", "status", "created_at"]
    )
    
    property_obj = create_response.json()
    property_id = property_obj["id"]
    assert property_obj["status"] == "PROPERTY_SOURCING"
    
    # Store in context for cleanup
    authenticated_context.test_data[f"property_{property_id}"] = property_obj
    
    # 2. Progress through workflow stages
    workflow_stages = [
        ("PROPERTY_STUDY", "Initial property analysis completed"),
        ("PBY_PREPARATION", "Preparing for council submission"),
        ("COUNCIL_APPROVAL", "Submitted to council for approval"),
        ("NEGOTIATION", "Entering negotiation phase"),
        ("DUE_DILIGENCE", "Conducting due diligence"),
        ("CONTRACT_SIGNING", "Ready for contract signing"),
        ("TAKEOVER", "Property takeover completed")
    ]
    
    for new_status, notes in workflow_stages:
        status_update = {
            "new_status": new_status,
            "notes": notes
        }
        
        status_response = await authenticated_context.client.patch(
            f"/api/v1/properties/{property_id}/status",
            json=status_update,
            headers=headers
        )
        await authenticated_context.assert_api_response(
            status_response,
            expected_keys=["id", "status"]
        )
        
        updated_property = status_response.json()
        assert updated_property["status"] == new_status
        
        # Verify workflow history
        history_response = await authenticated_context.client.get(
            f"/api/v1/properties/{property_id}/history",
            headers=headers
        )
        await authenticated_context.assert_api_response(history_response)
        
        history = history_response.json()
        assert len(history) > 0, "History should contain workflow entries"
        latest_entry = history[-1]
        assert latest_entry["to_status"] == new_status
        assert latest_entry["notes"] == notes
    
    # 3. Verify final state
    final_response = await authenticated_context.client.get(
        f"/api/v1/properties/{property_id}",
        headers=headers
    )
    await authenticated_context.assert_api_response(final_response)
    
    final_property = final_response.json()
    assert final_property["status"] == "TAKEOVER"
    assert len(final_property["workflow_history"]) == len(workflow_stages)


@api_test
async def test_duplicate_detection_context(authenticated_context: TestContext):
    """Test duplicate detection with multiple properties in context"""
    token = authenticated_context.test_data["auth_token"]
    headers = authenticated_context.get_auth_headers(token)
    
    # Create original property
    original_property = await authenticated_context.create_test_property(
        token,
        name="Original Property",
        address="789 Original Street, Duplicate City",
        title_number="ORIG-001-2024"
    )
    
    # Create similar property (potential duplicate)
    similar_property_data = {
        "name": "Similar Property",  # Different name
        "address": "789 Original St, Duplicate City",  # Similar address
        "latitude": 14.5995,
        "longitude": 120.9842,
        "lot_area": 150.0,
        "property_type": "RESIDENTIAL",
        "price": 1500000.00,
        "currency": "PHP",
        "zoning_classification": "R1",
        "title_number": "SIM-001-2024",  # Different title
        "description": "Similar property for duplicate testing"
    }
    
    # Check for duplicates
    duplicate_response = await authenticated_context.client.post(
        "/api/v1/duplicates/check",
        json=similar_property_data,
        headers=headers
    )
    await authenticated_context.assert_api_response(duplicate_response)
    
    duplicates = duplicate_response.json()
    assert len(duplicates) >= 1, "Should find the original property as a potential duplicate"
    
    # Find the original property in duplicates
    original_duplicate = next(
        (d for d in duplicates if d["property_id"] == original_property["id"]), 
        None
    )
    assert original_duplicate is not None, "Original property should be detected as duplicate"
    assert original_duplicate["similarity_score"] > 0.5, "Similarity score should be significant"
    assert "Address similarity" in str(original_duplicate["match_reasons"]), "Should match on address"
    
    # Test exact duplicate (same title number)
    exact_duplicate_data = similar_property_data.copy()
    exact_duplicate_data["title_number"] = original_property["title_number"]
    
    exact_duplicate_response = await authenticated_context.client.post(
        "/api/v1/duplicates/check",
        json=exact_duplicate_data,
        headers=headers
    )
    await authenticated_context.assert_api_response(exact_duplicate_response)
    
    exact_duplicates = exact_duplicate_response.json()
    assert len(exact_duplicates) >= 1, "Should find exact duplicate"
    
    exact_match = exact_duplicates[0]
    assert exact_match["similarity_score"] == 1.0, "Exact title match should have score 1.0"
    assert "Exact title number match" in exact_match["match_reasons"]


@api_test
async def test_admin_operations_context(admin_context: TestContext):
    """Test admin operations with proper context"""
    admin_token = admin_context.test_data["auth_token"]
    admin_headers = admin_context.get_auth_headers(admin_token)
    
    # Create regular user first
    regular_user = await admin_context.create_test_user(
        email="regular@context7.com",
        role="AGENT"
    )
    regular_token = await admin_context.login_user("regular@context7.com", "testpassword123")
    
    # Create property as regular user
    property_obj = await admin_context.create_test_property(
        regular_token,
        name="Admin Test Property"
    )
    property_id = property_obj["id"]
    
    # Test admin statistics
    stats_response = await admin_context.client.get(
        "/api/v1/admin/properties/stats",
        headers=admin_headers
    )
    await admin_context.assert_api_response(
        stats_response,
        expected_keys=["total_properties", "properties_by_status", "properties_by_type"]
    )
    
    stats = stats_response.json()
    assert stats["total_properties"] >= 1
    assert "PROPERTY_SOURCING" in stats["properties_by_status"]
    
    # Test user management
    users_response = await admin_context.client.get(
        "/api/v1/admin/users",
        headers=admin_headers
    )
    await admin_context.assert_api_response(users_response)
    
    users = users_response.json()
    assert len(users) >= 2, "Should have at least admin and regular user"
    
    # Test reviewer assignment
    assign_response = await admin_context.client.patch(
        f"/api/v1/admin/properties/{property_id}/assign-reviewer",
        params={"reviewer_id": admin_context.test_data["current_user"]["id"]},
        headers=admin_headers
    )
    await admin_context.assert_api_response(assign_response)
    
    assignment_result = assign_response.json()
    assert "assigned" in assignment_result["message"].lower()


@context_test
async def test_error_handling_with_context():
    """Test error handling scenarios with context management"""
    context = TestContext()
    await context.setup()
    
    try:
        # Test invalid authentication
        invalid_headers = {"Authorization": "Bearer invalid_token"}
        response = await context.client.get("/api/v1/users/me", headers=invalid_headers)
        assert response.status_code == 401
        
        # Test invalid property data
        invalid_property = {
            "name": "",  # Empty name
            "price": -1000,  # Negative price
            "lot_area": 0  # Zero area
        }
        
        # Should fail without authentication
        response = await context.client.post("/api/v1/properties/", json=invalid_property)
        assert response.status_code == 401
        
        # Create user and test with authentication
        user = await context.create_test_user()
        token = await context.login_user(user["email"], "testpassword123")
        
        response = await context.client.post(
            "/api/v1/properties/", 
            json=invalid_property,
            headers=context.get_auth_headers(token)
        )
        assert response.status_code in [400, 422], "Should reject invalid property data"
        
    finally:
        await context.cleanup()


@api_test
async def test_concurrent_operations_context(authenticated_context: TestContext):
    """Test concurrent operations within context"""
    import asyncio
    
    token = authenticated_context.test_data["auth_token"]
    headers = authenticated_context.get_auth_headers(token)
    
    # Create multiple properties concurrently
    async def create_property(index: int):
        property_data = {
            "name": f"Concurrent Property {index}",
            "address": f"{index} Concurrent Street",
            "latitude": 14.5995 + index * 0.001,
            "longitude": 120.9842 + index * 0.001,
            "lot_area": 100.0 + index,
            "property_type": "RESIDENTIAL",
            "price": 1000000.00 + index * 50000,
            "currency": "PHP",
            "zoning_classification": "R1",
            "title_number": f"CONC-{index:03d}-2024",
            "description": f"Concurrent property {index}"
        }
        
        response = await authenticated_context.client.post(
            "/api/v1/properties/",
            json=property_data,
            headers=headers
        )
        await authenticated_context.assert_api_response(response)
        return response.json()
    
    # Execute concurrent operations
    tasks = [create_property(i) for i in range(5)]
    results = await asyncio.gather(*tasks)
    
    assert len(results) == 5, "All concurrent operations should succeed"
    
    # Verify all properties exist
    list_response = await authenticated_context.client.get("/api/v1/properties/", headers=headers)
    await authenticated_context.assert_api_response(list_response)
    
    properties = list_response.json()
    concurrent_properties = [p for p in properties if "Concurrent Property" in p["name"]]
    assert len(concurrent_properties) == 5, "All concurrent properties should be retrievable"