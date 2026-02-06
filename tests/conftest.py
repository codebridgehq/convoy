"""Pytest configuration and fixtures for Convoy E2E tests."""

import os
from typing import AsyncGenerator

import httpx
import pytest


@pytest.fixture(scope="session")
def api_base_url() -> str:
    """Get API base URL from environment variable.
    
    The API_BASE_URL environment variable allows targeting different environments:
    - Local Docker: http://convoy-api:8000
    - Local development: http://localhost:8000
    - Staging: https://staging-api.convoy.example.com
    - Production: https://api.convoy.example.com
    """
    url = os.environ.get("API_BASE_URL", "http://localhost:8000")
    return url.rstrip("/")


@pytest.fixture
async def async_client(api_base_url: str) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Provide an async HTTP client configured with the API base URL.
    
    The client is configured with:
    - Base URL from environment variable
    - 30 second timeout for all requests
    - Automatic connection cleanup
    """
    async with httpx.AsyncClient(
        base_url=api_base_url,
        timeout=30.0,
    ) as client:
        yield client
