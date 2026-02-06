"""E2E tests for the health check endpoint."""

import httpx
import pytest


class TestHealthEndpoint:
    """Tests for GET /health endpoint."""

    async def test_health_check_returns_ok(self, async_client: httpx.AsyncClient):
        """Test that health check endpoint returns 200 OK with status ok."""
        response = await async_client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data == {"status": "ok"}

    async def test_health_check_response_is_json(self, async_client: httpx.AsyncClient):
        """Test that health check endpoint returns JSON content type."""
        response = await async_client.get("/health")
        
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")
