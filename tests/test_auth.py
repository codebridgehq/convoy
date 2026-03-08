"""E2E tests for authentication and management endpoints."""

import uuid

import httpx
import pytest


class TestAdminAuthentication:
    """Tests for admin authentication on management endpoints."""

    async def test_management_endpoints_require_admin_key(
        self,
        async_client: httpx.AsyncClient
    ):
        """Test that management endpoints require admin API key."""
        # Try to list projects without admin key
        response = await async_client.get("/admin/projects")
        
        assert response.status_code == 401
        assert "detail" in response.json()

    async def test_management_endpoints_reject_invalid_admin_key(
        self,
        api_base_url: str
    ):
        """Test that management endpoints reject invalid admin API key."""
        async with httpx.AsyncClient(
            base_url=api_base_url,
            timeout=30.0,
            headers={"X-Admin-Key": "invalid-admin-key"},
        ) as client:
            response = await client.get("/admin/projects")
        
        assert response.status_code == 401
        assert "detail" in response.json()

    async def test_management_endpoints_accept_valid_admin_key(
        self,
        admin_client: httpx.AsyncClient
    ):
        """Test that management endpoints accept valid admin API key."""
        response = await admin_client.get("/admin/projects")
        
        assert response.status_code == 200

    async def test_project_api_key_cannot_access_management(
        self,
        api_base_url: str,
        test_api_key: str
    ):
        """Test that project API keys cannot access management endpoints."""
        async with httpx.AsyncClient(
            base_url=api_base_url,
            timeout=30.0,
            headers={"X-Admin-Key": test_api_key},  # Using project key as admin key
        ) as client:
            response = await client.get("/admin/projects")
        
        # Should fail because project API key is not the admin key
        assert response.status_code == 401


class TestProjectManagement:
    """Tests for project management endpoints."""

    async def test_create_project_success(
        self,
        admin_client: httpx.AsyncClient
    ):
        """Test creating a new project."""
        project_slug = f"test-project-{uuid.uuid4().hex[:8]}"
        
        response = await admin_client.post(
            "/admin/projects",
            json={
                "name": "Test Project",
                "slug": project_slug,
                "description": "A test project",
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert "id" in data
        assert data["name"] == "Test Project"
        assert data["slug"] == project_slug
        assert data["description"] == "A test project"
        assert data["is_active"] is True
        assert "created_at" in data

    async def test_create_project_duplicate_slug_fails(
        self,
        admin_client: httpx.AsyncClient
    ):
        """Test that creating a project with duplicate slug fails."""
        project_slug = f"duplicate-slug-{uuid.uuid4().hex[:8]}"
        
        # Create first project
        response1 = await admin_client.post(
            "/admin/projects",
            json={
                "name": "First Project",
                "slug": project_slug,
            },
        )
        assert response1.status_code == 201
        
        # Try to create second project with same slug
        response2 = await admin_client.post(
            "/admin/projects",
            json={
                "name": "Second Project",
                "slug": project_slug,
            },
        )
        assert response2.status_code == 409
        assert "already exists" in response2.json()["detail"].lower()

    async def test_list_projects(
        self,
        admin_client: httpx.AsyncClient
    ):
        """Test listing all projects."""
        response = await admin_client.get("/admin/projects")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "projects" in data
        assert isinstance(data["projects"], list)
        # Should have at least the test project created by fixtures
        assert len(data["projects"]) >= 1

    async def test_get_project_by_slug(
        self,
        admin_client: httpx.AsyncClient,
        test_project: dict
    ):
        """Test getting a project by slug."""
        response = await admin_client.get(
            f"/admin/projects/{test_project['slug']}"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == test_project["id"]
        assert data["name"] == test_project["name"]

    async def test_get_nonexistent_project_returns_404(
        self,
        admin_client: httpx.AsyncClient
    ):
        """Test that getting a nonexistent project returns 404."""
        fake_id = str(uuid.uuid4())
        
        response = await admin_client.get(f"/admin/projects/{fake_id}")
        
        assert response.status_code == 404

    async def test_update_project(
        self,
        admin_client: httpx.AsyncClient
    ):
        """Test updating a project."""
        # Create a project to update
        project_slug = f"update-test-{uuid.uuid4().hex[:8]}"
        create_response = await admin_client.post(
            "/admin/projects",
            json={
                "name": "Original Name",
                "slug": project_slug,
            },
        )
        assert create_response.status_code == 201
        project = create_response.json()
        
        # Update the project (use slug, not id)
        update_response = await admin_client.patch(
            f"/admin/projects/{project['slug']}",
            json={
                "name": "Updated Name",
                "description": "Updated description",
            },
        )
        
        assert update_response.status_code == 200
        data = update_response.json()
        assert data["name"] == "Updated Name"
        assert data["description"] == "Updated description"

    async def test_deactivate_project(
        self,
        admin_client: httpx.AsyncClient
    ):
        """Test deactivating a project."""
        # Create a project to deactivate
        project_slug = f"deactivate-test-{uuid.uuid4().hex[:8]}"
        create_response = await admin_client.post(
            "/admin/projects",
            json={
                "name": "Project to Deactivate",
                "slug": project_slug,
            },
        )
        assert create_response.status_code == 201
        project = create_response.json()
        
        # Deactivate the project (use slug, not id)
        update_response = await admin_client.patch(
            f"/admin/projects/{project['slug']}",
            json={"is_active": False},
        )
        
        assert update_response.status_code == 200
        assert update_response.json()["is_active"] is False


class TestAPIKeyManagement:
    """Tests for API key management endpoints."""

    async def test_create_api_key_success(
        self,
        admin_client: httpx.AsyncClient,
        test_project: dict
    ):
        """Test creating a new API key."""
        response = await admin_client.post(
            f"/admin/projects/{test_project['slug']}/api-keys",
            json={"name": "Test API Key"},
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert "id" in data
        assert "key" in data  # Raw key only available at creation
        assert data["name"] == "Test API Key"
        assert data["key_prefix"].startswith("convoy_sk_")
        assert "created_at" in data
        
        # Verify the key format
        assert data["key"].startswith("convoy_sk_")
        assert len(data["key"]) == 42  # convoy_sk_ (10) + 32 chars = 42

    async def test_create_api_key_with_expiration(
        self,
        admin_client: httpx.AsyncClient,
        test_project: dict
    ):
        """Test creating an API key with expiration date."""
        from datetime import datetime, timedelta, timezone
        
        expires_at = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        
        response = await admin_client.post(
            f"/admin/projects/{test_project['slug']}/api-keys",
            json={
                "name": "Expiring API Key",
                "expires_at": expires_at,
            },
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["expires_at"] is not None

    async def test_list_api_keys(
        self,
        admin_client: httpx.AsyncClient,
        test_project: dict
    ):
        """Test listing API keys for a project."""
        response = await admin_client.get(
            f"/admin/projects/{test_project['slug']}/api-keys"
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "api_keys" in data
        assert isinstance(data["api_keys"], list)
        # Should have at least the test API key created by fixtures
        assert len(data["api_keys"]) >= 1
        
        # Verify key structure (should NOT include raw key)
        for key in data["api_keys"]:
            assert "id" in key
            assert "name" in key
            assert "key_prefix" in key
            assert "key" not in key  # Raw key should not be exposed

    async def test_revoke_api_key(
        self,
        admin_client: httpx.AsyncClient,
        test_project: dict
    ):
        """Test revoking an API key."""
        # Create an API key to revoke
        create_response = await admin_client.post(
            f"/admin/projects/{test_project['slug']}/api-keys",
            json={"name": "Key to Revoke"},
        )
        assert create_response.status_code == 201
        key_id = create_response.json()["id"]
        
        # Revoke the key
        revoke_response = await admin_client.delete(
            f"/admin/projects/{test_project['slug']}/api-keys/{key_id}"
        )
        
        assert revoke_response.status_code == 204
