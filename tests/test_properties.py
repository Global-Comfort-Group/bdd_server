import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_property(client: AsyncClient, agent_token: str, sample_property_data: dict):
    """Test property creation."""
    headers = {"Authorization": f"Bearer {agent_token}"}
    
    response = await client.post("/api/v1/properties/", json=sample_property_data, headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["name"] == sample_property_data["name"]
    assert data["address"] == sample_property_data["address"]
    assert data["title_number"] == sample_property_data["title_number"]
    assert data["status"] == "PROPERTY_SOURCING"
    assert "id" in data


@pytest.mark.asyncio
async def test_create_property_duplicate_title(client: AsyncClient, agent_token: str, sample_property_data: dict):
    """Test property creation with duplicate title number."""
    headers = {"Authorization": f"Bearer {agent_token}"}
    
    # Create first property
    response = await client.post("/api/v1/properties/", json=sample_property_data, headers=headers)
    assert response.status_code == 200
    
    # Try to create second property with same title number
    response = await client.post("/api/v1/properties/", json=sample_property_data, headers=headers)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_get_properties(client: AsyncClient, agent_token: str, sample_property_data: dict):
    """Test getting list of properties."""
    headers = {"Authorization": f"Bearer {agent_token}"}
    
    # Create a property first
    await client.post("/api/v1/properties/", json=sample_property_data, headers=headers)
    
    # Get properties list
    response = await client.get("/api/v1/properties/", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["name"] == sample_property_data["name"]


@pytest.mark.asyncio
async def test_get_property_by_id(client: AsyncClient, agent_token: str, sample_property_data: dict):
    """Test getting a specific property by ID."""
    headers = {"Authorization": f"Bearer {agent_token}"}
    
    # Create a property first
    create_response = await client.post("/api/v1/properties/", json=sample_property_data, headers=headers)
    property_data = create_response.json()
    property_id = property_data["id"]
    
    # Get property by ID
    response = await client.get(f"/api/v1/properties/{property_id}", headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == property_id
    assert data["name"] == sample_property_data["name"]


@pytest.mark.asyncio
async def test_update_property(client: AsyncClient, agent_token: str, sample_property_data: dict):
    """Test property update."""
    headers = {"Authorization": f"Bearer {agent_token}"}
    
    # Create a property first
    create_response = await client.post("/api/v1/properties/", json=sample_property_data, headers=headers)
    property_data = create_response.json()
    property_id = property_data["id"]
    
    # Update property
    update_data = {"name": "Updated Property Name", "price": 2000000.00}
    response = await client.patch(f"/api/v1/properties/{property_id}", json=update_data, headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["name"] == update_data["name"]
    assert float(data["price"]) == update_data["price"]


@pytest.mark.asyncio
async def test_update_property_status(client: AsyncClient, agent_token: str, sample_property_data: dict):
    """Test property status update."""
    headers = {"Authorization": f"Bearer {agent_token}"}
    
    # Create a property first
    create_response = await client.post("/api/v1/properties/", json=sample_property_data, headers=headers)
    property_data = create_response.json()
    property_id = property_data["id"]
    
    # Update status
    status_data = {"new_status": "PROPERTY_SCREENING_FUNG_SHUI", "notes": "Moving to screening phase"}
    response = await client.patch(f"/api/v1/properties/{property_id}/status", json=status_data, headers=headers)
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "PROPERTY_SCREENING_FUNG_SHUI"


@pytest.mark.asyncio
async def test_invalid_status_transition(client: AsyncClient, agent_token: str, sample_property_data: dict):
    """Test invalid status transition."""
    headers = {"Authorization": f"Bearer {agent_token}"}
    
    # Create a property first
    create_response = await client.post("/api/v1/properties/", json=sample_property_data, headers=headers)
    property_data = create_response.json()
    property_id = property_data["id"]
    
    # Try invalid status transition (skip steps)
    status_data = {"new_status": "COL_DOAS_SIGNING", "notes": "Invalid transition"}
    response = await client.patch(f"/api/v1/properties/{property_id}/status", json=status_data, headers=headers)
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_delete_property(client: AsyncClient, agent_token: str, sample_property_data: dict):
    """Test property deletion."""
    headers = {"Authorization": f"Bearer {agent_token}"}
    
    # Create a property first
    create_response = await client.post("/api/v1/properties/", json=sample_property_data, headers=headers)
    property_data = create_response.json()
    property_id = property_data["id"]
    
    # Delete property
    response = await client.delete(f"/api/v1/properties/{property_id}", headers=headers)
    assert response.status_code == 200
    
    # Verify property is deleted
    response = await client.get(f"/api/v1/properties/{property_id}", headers=headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_property_workflow_history(client: AsyncClient, agent_token: str, sample_property_data: dict):
    """Test property workflow history tracking."""
    headers = {"Authorization": f"Bearer {agent_token}"}
    
    # Create a property
    create_response = await client.post("/api/v1/properties/", json=sample_property_data, headers=headers)
    property_data = create_response.json()
    property_id = property_data["id"]
    
    # Update status to create history entry
    status_data = {"new_status": "PROPERTY_SCREENING_FUNG_SHUI", "notes": "Moving to screening phase"}
    await client.patch(f"/api/v1/properties/{property_id}/status", json=status_data, headers=headers)
    
    # Get workflow history
    response = await client.get(f"/api/v1/properties/{property_id}/history", headers=headers)
    assert response.status_code == 200
    
    history = response.json()
    assert isinstance(history, list)
    assert len(history) == 1
    assert history[0]["to_status"] == "PROPERTY_SCREENING_FUNG_SHUI"
    assert history[0]["notes"] == "Moving to screening phase"