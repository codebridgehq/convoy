"""E2E tests for the cargo load endpoint."""

import httpx
import pytest


class TestCargoLoadEndpoint:
    """Tests for POST /cargo/load endpoint."""

    @pytest.fixture
    def valid_cargo_payload(self) -> dict:
        """Provide a valid cargo load request payload."""
        return {
            "params": {
                "model": "claude-sonnet-4-5",
                "max_tokens": 1024,
                "messages": [
                    {
                        "role": "user",
                        "content": "Hello, this is a test message for E2E testing."
                    }
                ]
            },
            "callback_url": "https://example.com/callback"
        }

    async def test_cargo_load_success(
        self, 
        async_client: httpx.AsyncClient,
        valid_cargo_payload: dict
    ):
        """Test that cargo load endpoint accepts valid payload and returns success."""
        response = await async_client.post("/cargo/load", json=valid_cargo_payload)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "cargo_id" in data
        assert "status" in data
        assert "message" in data
        
        # Verify cargo_id is a non-empty string
        assert isinstance(data["cargo_id"], str)
        assert len(data["cargo_id"]) > 0
        
        # Verify status indicates success
        assert data["status"] == "success"

    async def test_cargo_load_with_system_prompt(
        self, 
        async_client: httpx.AsyncClient
    ):
        """Test cargo load with system prompt included."""
        payload = {
            "params": {
                "model": "claude-sonnet-4-5",
                "max_tokens": 512,
                "system": "You are a helpful assistant for testing purposes.",
                "messages": [
                    {
                        "role": "user",
                        "content": "What is 2 + 2?"
                    }
                ]
            },
            "callback_url": "https://example.com/webhook"
        }
        
        response = await async_client.post("/cargo/load", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "cargo_id" in data

    async def test_cargo_load_with_optional_params(
        self, 
        async_client: httpx.AsyncClient
    ):
        """Test cargo load with optional parameters like temperature and top_p."""
        payload = {
            "params": {
                "model": "claude-3-haiku-20240307",
                "max_tokens": 256,
                "temperature": 0.7,
                "top_p": 0.9,
                "messages": [
                    {
                        "role": "user",
                        "content": "Generate a creative response."
                    }
                ]
            },
            "callback_url": "https://example.com/callback"
        }
        
        response = await async_client.post("/cargo/load", json=payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

    async def test_cargo_load_missing_model_returns_error(
        self, 
        async_client: httpx.AsyncClient
    ):
        """Test that missing model field returns validation error."""
        payload = {
            "params": {
                "max_tokens": 1024,
                "messages": [
                    {
                        "role": "user",
                        "content": "Test message"
                    }
                ]
            },
            "callback_url": "https://example.com/callback"
        }
        
        response = await async_client.post("/cargo/load", json=payload)
        
        assert response.status_code == 422  # Unprocessable Entity

    async def test_cargo_load_missing_messages_returns_error(
        self, 
        async_client: httpx.AsyncClient
    ):
        """Test that missing messages field returns validation error."""
        payload = {
            "params": {
                "model": "claude-sonnet-4-5",
                "max_tokens": 1024
            },
            "callback_url": "https://example.com/callback"
        }
        
        response = await async_client.post("/cargo/load", json=payload)
        
        assert response.status_code == 422  # Unprocessable Entity

    async def test_cargo_load_missing_callback_url_returns_error(
        self, 
        async_client: httpx.AsyncClient
    ):
        """Test that missing callback_url field returns validation error."""
        payload = {
            "params": {
                "model": "claude-sonnet-4-5",
                "max_tokens": 1024,
                "messages": [
                    {
                        "role": "user",
                        "content": "Test message"
                    }
                ]
            }
        }
        
        response = await async_client.post("/cargo/load", json=payload)
        
        assert response.status_code == 422  # Unprocessable Entity

    async def test_cargo_load_empty_body_returns_error(
        self, 
        async_client: httpx.AsyncClient
    ):
        """Test that empty request body returns validation error."""
        response = await async_client.post("/cargo/load", json={})
        
        assert response.status_code == 422  # Unprocessable Entity

    async def test_cargo_load_response_is_json(
        self, 
        async_client: httpx.AsyncClient,
        valid_cargo_payload: dict
    ):
        """Test that cargo load endpoint returns JSON content type."""
        response = await async_client.post("/cargo/load", json=valid_cargo_payload)
        
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")
