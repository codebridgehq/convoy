"""Pytest configuration and fixtures for Convoy E2E tests."""

import os
import uuid
from typing import AsyncGenerator

import httpx
import pytest


def pytest_collection_modifyitems(session, config, items):
    """Ensure test_batch_flow.py tests run last.
    
    This hook reorders collected test items so that all tests from
    test_batch_flow.py are executed after all other tests complete.
    """
    batch_flow_tests = []
    other_tests = []
    
    for item in items:
        if "test_batch_flow" in str(item.fspath):
            batch_flow_tests.append(item)
        else:
            other_tests.append(item)
    
    items[:] = other_tests + batch_flow_tests


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


@pytest.fixture(scope="session")
def admin_api_key() -> str:
    """Get admin API key from environment variable.
    
    The ADMIN_API_KEY is required for management endpoints (creating projects, API keys).
    """
    key = os.environ.get("ADMIN_API_KEY", "convoy_admin_dev_key_change_in_production")
    return key


@pytest.fixture(scope="session")
def test_project_and_key(api_base_url: str, admin_api_key: str) -> tuple[dict, str]:
    """Create a test project and API key for the test session.
    
    This fixture creates both a project and an API key once per test session.
    Returns a tuple of (project_dict, api_key_string).
    """
    with httpx.Client(
        base_url=api_base_url,
        timeout=30.0,
        headers={"X-Admin-Key": admin_api_key},
    ) as client:
        # Create a unique test project
        project_slug = f"test-project-{uuid.uuid4().hex[:8]}"
        
        project_response = client.post(
            "/admin/projects",
            json={
                "name": "E2E Test Project",
                "slug": project_slug,
                "description": "Project created for E2E testing",
            },
        )
        
        if project_response.status_code != 201:
            raise RuntimeError(
                f"Failed to create test project: {project_response.status_code} - {project_response.text}"
            )
        
        project = project_response.json()
        
        # Create API key for the project (use slug, not id)
        key_response = client.post(
            f"/admin/projects/{project['slug']}/api-keys",
            json={
                "name": "E2E Test API Key",
            },
        )
        
        if key_response.status_code != 201:
            raise RuntimeError(
                f"Failed to create test API key: {key_response.status_code} - {key_response.text}"
            )
        
        api_key = key_response.json()["key"]
        
        return project, api_key


@pytest.fixture(scope="session")
def test_project(test_project_and_key: tuple[dict, str]) -> dict:
    """Provide the test project."""
    return test_project_and_key[0]


@pytest.fixture(scope="session")
def test_api_key(test_project_and_key: tuple[dict, str]) -> str:
    """Provide the test API key."""
    return test_project_and_key[1]


@pytest.fixture
async def async_client(api_base_url: str) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Provide an async HTTP client configured with the API base URL.
    
    This client does NOT include authentication headers.
    Use for testing public endpoints (like /health) or testing auth rejection.
    
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


@pytest.fixture
async def authenticated_client(
    api_base_url: str,
    test_api_key: str,
) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Provide an async HTTP client with project API key authentication.
    
    This client includes the X-API-Key header for authenticating cargo requests.
    Use for testing cargo load and tracking endpoints.
    
    The client is configured with:
    - Base URL from environment variable
    - X-API-Key header with the test project's API key
    - 30 second timeout for all requests
    - Automatic connection cleanup
    """
    async with httpx.AsyncClient(
        base_url=api_base_url,
        timeout=30.0,
        headers={"X-API-Key": test_api_key},
    ) as client:
        yield client


@pytest.fixture
async def admin_client(
    api_base_url: str,
    admin_api_key: str,
) -> AsyncGenerator[httpx.AsyncClient, None]:
    """Provide an async HTTP client with admin API key authentication.
    
    This client includes the X-Admin-Key header for management endpoints.
    Use for testing project and API key management.
    
    The client is configured with:
    - Base URL from environment variable
    - X-Admin-Key header for admin authentication
    - 30 second timeout for all requests
    - Automatic connection cleanup
    """
    async with httpx.AsyncClient(
        base_url=api_base_url,
        timeout=30.0,
        headers={"X-Admin-Key": admin_api_key},
    ) as client:
        yield client
