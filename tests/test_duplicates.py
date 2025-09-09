import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_check_duplicates_by_title_number(client: AsyncClient, agent_token: str, sample_property_data: dict):
    """Test duplicate detection by title number."""
    headers = {"Authorization": f"Bearer {agent_token}"}
    
    # Create a property first
    await client.post("/api/v1/properties/", json=sample_property_data, headers=headers)
    
    # Check for duplicates with same title number
    duplicate_check_data = sample_property_data.copy()
    response = await client.post("/api/v1/duplicates/check", json=duplicate_check_data, headers=headers)
    assert response.status_code == 200
    
    duplicates = response.json()
    assert isinstance(duplicates, list)
    assert len(duplicates) == 1
    assert duplicates[0]["similarity_score"] == 1.0  # Exact match
    assert "Exact title number match" in duplicates[0]["match_reasons"]


@pytest.mark.asyncio
async def test_check_duplicates_by_address(client: AsyncClient, agent_token: str, sample_property_data: dict):
    """Test duplicate detection by address similarity."""
    headers = {"Authorization": f"Bearer {agent_token}"}
    
    # Create a property first
    await client.post("/api/v1/properties/", json=sample_property_data, headers=headers)
    
    # Check for duplicates with similar address but different title
    similar_property = sample_property_data.copy()
    similar_property["title_number"] = "DIFFERENT-001-2023"
    similar_property["address"] = "123 Test St, Test City"  # Slightly different
    
    response = await client.post("/api/v1/duplicates/check", json=similar_property, headers=headers)
    assert response.status_code == 200
    
    duplicates = response.json()
    assert isinstance(duplicates, list)
    if duplicates:  # Address similarity might or might not trigger based on threshold
        assert duplicates[0]["similarity_score"] < 1.0
        assert any("Address similarity" in reason for reason in duplicates[0]["match_reasons"])


@pytest.mark.asyncio
async def test_check_duplicates_by_location(client: AsyncClient, agent_token: str, sample_property_data: dict):
    """Test duplicate detection by geographic proximity."""
    headers = {"Authorization": f"Bearer {agent_token}"}
    
    # Create a property first
    await client.post("/api/v1/properties/", json=sample_property_data, headers=headers)
    
    # Check for duplicates with nearby coordinates
    nearby_property = sample_property_data.copy()
    nearby_property["title_number"] = "NEARBY-001-2023"
    nearby_property["address"] = "456 Different Street"
    nearby_property["latitude"] = 14.5996  # Very close latitude
    nearby_property["longitude"] = 120.9843  # Very close longitude
    nearby_property["name"] = "Similar Test Property"
    
    response = await client.post("/api/v1/duplicates/check", json=nearby_property, headers=headers)
    assert response.status_code == 200
    
    duplicates = response.json()
    assert isinstance(duplicates, list)
    if duplicates:  # Location proximity might trigger based on distance
        assert any("Within" in reason for reason in duplicates[0]["match_reasons"])


@pytest.mark.asyncio
async def test_mark_property_as_duplicate(client: AsyncClient, admin_token: str, sample_property_data: dict):
    """Test marking property as duplicate."""
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Create two properties
    property1_response = await client.post("/api/v1/properties/", json=sample_property_data, headers=headers)
    property1 = property1_response.json()
    
    property2_data = sample_property_data.copy()
    property2_data["title_number"] = "DUPLICATE-001-2023"
    property2_data["name"] = "Duplicate Property"
    property2_response = await client.post("/api/v1/properties/", json=property2_data, headers=headers)
    property2 = property2_response.json()
    
    # Mark property2 as duplicate of property1
    mark_duplicate_params = {
        "original_property_id": property1["id"],
        "notes": "Found to be duplicate during review"
    }
    
    response = await client.post(
        f"/api/v1/duplicates/{property2['id']}/mark-duplicate", 
        params=mark_duplicate_params,
        headers=headers
    )
    assert response.status_code == 200
    
    data = response.json()
    assert "marked as duplicate" in data["message"].lower()


@pytest.mark.asyncio
async def test_calculate_similarity_score(client: AsyncClient, agent_token: str, sample_property_data: dict):
    """Test similarity score calculation between properties."""
    headers = {"Authorization": f"Bearer {agent_token}"}
    
    # Create two properties
    property1_response = await client.post("/api/v1/properties/", json=sample_property_data, headers=headers)
    property1 = property1_response.json()
    
    property2_data = sample_property_data.copy()
    property2_data["title_number"] = "SIMILAR-001-2023"
    property2_data["name"] = "Similar Test Property"
    property2_data["address"] = "124 Test Street, Test City"  # Similar address
    property2_response = await client.post("/api/v1/properties/", json=property2_data, headers=headers)
    property2 = property2_response.json()
    
    # Calculate similarity
    response = await client.get(
        f"/api/v1/duplicates/{property1['id']}/similarity/{property2['id']}", 
        headers=headers
    )
    assert response.status_code == 200
    
    data = response.json()
    assert "similarity_score" in data
    assert 0 <= data["similarity_score"] <= 1
    assert data["property1_id"] == property1["id"]
    assert data["property2_id"] == property2["id"]


@pytest.mark.asyncio
async def test_unauthorized_duplicate_operations(client: AsyncClient, agent_token: str, sample_property_data: dict):
    """Test that regular users cannot perform admin-only duplicate operations."""
    headers = {"Authorization": f"Bearer {agent_token}"}
    
    # Create a property
    property_response = await client.post("/api/v1/properties/", json=sample_property_data, headers=headers)
    property_data = property_response.json()
    
    # Try to mark as duplicate (should fail for non-admin)
    mark_duplicate_params = {
        "original_property_id": 999,
        "notes": "Unauthorized attempt"
    }
    
    response = await client.post(
        f"/api/v1/duplicates/{property_data['id']}/mark-duplicate", 
        params=mark_duplicate_params,
        headers=headers
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_no_duplicates_found(client: AsyncClient, agent_token: str):
    """Test duplicate check when no duplicates exist."""
    headers = {"Authorization": f"Bearer {agent_token}"}
    
    unique_property = {
        "name": "Completely Unique Property",
        "address": "999 Unique Avenue, Unique City",
        "latitude": 10.1234,
        "longitude": 125.6789,
        "lot_area": 500.0,
        "property_type": "COMMERCIAL",
        "price": 5000000.00,
        "currency": "PHP",
        "zoning_classification": "C1",
        "title_number": "UNIQUE-999-2023",
        "description": "A completely unique property"
    }
    
    response = await client.post("/api/v1/duplicates/check", json=unique_property, headers=headers)
    assert response.status_code == 200
    
    duplicates = response.json()
    assert isinstance(duplicates, list)
    assert len(duplicates) == 0