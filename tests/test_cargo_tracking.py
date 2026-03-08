"""E2E tests for the cargo tracking endpoint."""

import uuid

import httpx
import pytest


class TestCargoTrackingEndpoint:
    """Tests for GET /cargo/{cargo_id}/tracking endpoint."""

    @pytest.fixture
    async def created_cargo_id(self, authenticated_client: httpx.AsyncClient) -> str:
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
        
        response = await authenticated_client.post("/cargo/load", json=payload)
        assert response.status_code == 200
        data = response.json()
        return data["cargo_id"]

    async def test_cargo_tracking_success(
        self, 
        authenticated_client: httpx.AsyncClient,
        created_cargo_id: str
    ):
        """Test that tracking endpoint returns valid tracking info for existing cargo."""
        response = await authenticated_client.get(f"/cargo/{created_cargo_id}/tracking")
        
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
        authenticated_client: httpx.AsyncClient
    ):
        """Test that tracking endpoint returns 404 for non-existent cargo."""
        non_existent_id = f"cargo_{uuid.uuid4().hex}"
        
        response = await authenticated_client.get(f"/cargo/{non_existent_id}/tracking")
        
        assert response.status_code == 404

    async def test_cargo_tracking_invalid_uuid_format(
        self, 
        authenticated_client: httpx.AsyncClient
    ):
        """Test tracking endpoint with invalid UUID format."""
        invalid_id = "not-a-valid-uuid"
        
        response = await authenticated_client.get(f"/cargo/{invalid_id}/tracking")
        
        # Should return 404 (not found) since it won't match any cargo
        assert response.status_code == 404

    async def test_cargo_tracking_response_is_json(
        self, 
        authenticated_client: httpx.AsyncClient,
        created_cargo_id: str
    ):
        """Test that tracking endpoint returns JSON content type."""
        response = await authenticated_client.get(f"/cargo/{created_cargo_id}/tracking")
        
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

    async def test_cargo_tracking_timestamps_are_valid(
        self, 
        authenticated_client: httpx.AsyncClient,
        created_cargo_id: str
    ):
        """Test that tracking timestamps are valid ISO format strings."""
        response = await authenticated_client.get(f"/cargo/{created_cargo_id}/tracking")
        
        assert response.status_code == 200
        data = response.json()
        
        # Timestamps should be non-empty strings in ISO format
        assert isinstance(data["created_at"], str)
        assert isinstance(data["updated_at"], str)
        assert len(data["created_at"]) > 0
        assert len(data["updated_at"]) > 0

    async def test_cargo_tracking_status_description_present(
        self, 
        authenticated_client: httpx.AsyncClient,
        created_cargo_id: str
    ):
        """Test that status_description provides meaningful information."""
        response = await authenticated_client.get(f"/cargo/{created_cargo_id}/tracking")
        
        assert response.status_code == 200
        data = response.json()
        
        # Status description should be a non-empty string
        assert isinstance(data["status_description"], str)
        assert len(data["status_description"]) > 0


class TestCargoTrackingAuthentication:
    """Tests for cargo tracking endpoint authentication."""

    async def test_cargo_tracking_without_api_key_returns_401(
        self,
        async_client: httpx.AsyncClient
    ):
        """Test that tracking without API key returns 401 Unauthorized."""
        cargo_id = f"cargo_{uuid.uuid4().hex}"
        response = await async_client.get(f"/cargo/{cargo_id}/tracking")
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data

    async def test_cargo_tracking_with_invalid_api_key_returns_401(
        self,
        api_base_url: str
    ):
        """Test that tracking with invalid API key returns 401 Unauthorized."""
        cargo_id = f"cargo_{uuid.uuid4().hex}"
        
        async with httpx.AsyncClient(
            base_url=api_base_url,
            timeout=30.0,
            headers={"X-API-Key": "invalid-api-key"},
        ) as client:
            response = await client.get(f"/cargo/{cargo_id}/tracking")
        
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data


class TestCargoTrackingProjectIsolation:
    """Tests for cargo tracking project isolation."""

    @pytest.fixture
    async def cargo_from_test_project(
        self,
        authenticated_client: httpx.AsyncClient
    ) -> str:
        """Create a cargo in the test project."""
        payload = {
            "params": {
                "model": "claude-sonnet-4-5",
                "max_tokens": 1024,
                "messages": [
                    {
                        "role": "user",
                        "content": "Test message for isolation test."
                    }
                ]
            },
            "callback_url": "https://example.com/callback"
        }
        
        response = await authenticated_client.post("/cargo/load", json=payload)
        assert response.status_code == 200
        return response.json()["cargo_id"]

    @pytest.fixture
    async def other_project_api_key(
        self,
        api_base_url: str,
        admin_api_key: str
    ) -> str:
        """Create another project and return its API key."""
        import uuid
        
        async with httpx.AsyncClient(
            base_url=api_base_url,
            timeout=30.0,
            headers={"X-Admin-Key": admin_api_key},
        ) as client:
            # Create another project
            project_slug = f"other-project-{uuid.uuid4().hex[:8]}"
            project_response = await client.post(
                "/admin/projects",
                json={
                    "name": "Other Test Project",
                    "slug": project_slug,
                    "description": "Another project for isolation testing",
                },
            )
            assert project_response.status_code == 201
            project = project_response.json()
            
            # Create API key for the other project (use slug, not id)
            key_response = await client.post(
                f"/admin/projects/{project['slug']}/api-keys",
                json={"name": "Other Project API Key"},
            )
            assert key_response.status_code == 201
            return key_response.json()["key"]

    async def test_cannot_track_cargo_from_other_project(
        self,
        api_base_url: str,
        cargo_from_test_project: str,
        other_project_api_key: str
    ):
        """Test that a project cannot track cargo from another project."""
        async with httpx.AsyncClient(
            base_url=api_base_url,
            timeout=30.0,
            headers={"X-API-Key": other_project_api_key},
        ) as client:
            response = await client.get(f"/cargo/{cargo_from_test_project}/tracking")
        
        # Should return 404 because the cargo belongs to a different project
        assert response.status_code == 404
