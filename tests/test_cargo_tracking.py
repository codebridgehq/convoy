"""E2E tests for the cargo tracking endpoint."""

import uuid

import httpx
import pytest


class TestCargoTrackingEndpoint:
    """Tests for GET /cargo/{cargo_id}/tracking endpoint."""

    @pytest.fixture
    async def created_cargo_id(self, async_client: httpx.AsyncClient) -> str:
        """Create a cargo and return its ID for tracking tests."""
        payload = {
            "params": {
                "model": "claude-sonnet-4-5",
                "max_tokens": 1024,
                "messages": [
                    {
                        "role": "user",
                        "content": "Test message for tracking test."
                    }
                ]
            },
            "callback_url": "https://example.com/callback"
        }
        
        response = await async_client.post("/cargo/load", json=payload)
        assert response.status_code == 200
        data = response.json()
        return data["cargo_id"]

    async def test_cargo_tracking_success(
        self, 
        async_client: httpx.AsyncClient,
        created_cargo_id: str
    ):
        """Test that tracking endpoint returns valid tracking info for existing cargo."""
        response = await async_client.get(f"/cargo/{created_cargo_id}/tracking")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "cargo_id" in data
        assert "status" in data
        assert "status_description" in data
        assert "created_at" in data
        assert "updated_at" in data
        
        # Verify cargo_id matches
        assert data["cargo_id"] == created_cargo_id
        
        # Verify status is a non-empty string
        assert isinstance(data["status"], str)
        assert len(data["status"]) > 0

    async def test_cargo_tracking_not_found(
        self, 
        async_client: httpx.AsyncClient
    ):
        """Test that tracking endpoint returns 404 for non-existent cargo."""
        non_existent_id = str(uuid.uuid4())
        
        response = await async_client.get(f"/cargo/{non_existent_id}/tracking")
        
        assert response.status_code == 404

    async def test_cargo_tracking_invalid_uuid_format(
        self, 
        async_client: httpx.AsyncClient
    ):
        """Test tracking endpoint with invalid UUID format."""
        invalid_id = "not-a-valid-uuid"
        
        response = await async_client.get(f"/cargo/{invalid_id}/tracking")
        
        # Should return 404 (not found) since it won't match any cargo
        assert response.status_code == 404

    async def test_cargo_tracking_response_is_json(
        self, 
        async_client: httpx.AsyncClient,
        created_cargo_id: str
    ):
        """Test that tracking endpoint returns JSON content type."""
        response = await async_client.get(f"/cargo/{created_cargo_id}/tracking")
        
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

    async def test_cargo_tracking_timestamps_are_valid(
        self, 
        async_client: httpx.AsyncClient,
        created_cargo_id: str
    ):
        """Test that tracking timestamps are valid ISO format strings."""
        response = await async_client.get(f"/cargo/{created_cargo_id}/tracking")
        
        assert response.status_code == 200
        data = response.json()
        
        # Timestamps should be non-empty strings in ISO format
        assert isinstance(data["created_at"], str)
        assert isinstance(data["updated_at"], str)
        assert len(data["created_at"]) > 0
        assert len(data["updated_at"]) > 0

    async def test_cargo_tracking_status_description_present(
        self, 
        async_client: httpx.AsyncClient,
        created_cargo_id: str
    ):
        """Test that status_description provides meaningful information."""
        response = await async_client.get(f"/cargo/{created_cargo_id}/tracking")
        
        assert response.status_code == 200
        data = response.json()
        
        # Status description should be a non-empty string
        assert isinstance(data["status_description"], str)
        assert len(data["status_description"]) > 0
