# Convoy E2E Tests

End-to-end tests for the Convoy API application using pytest and httpx.

## Overview

These tests verify the Convoy API endpoints work correctly by making real HTTP requests to a running API instance. The tests can be run against any environment (local, staging, production) by configuring the `API_BASE_URL` environment variable.

## Test Coverage

| Test File | Endpoint | Description |
|-----------|----------|-------------|
| `test_health.py` | `GET /health` | Health check endpoint tests |
| `test_cargo_load.py` | `POST /cargo/load` | Cargo load endpoint tests (valid/invalid payloads) |
| `test_cargo_tracking.py` | `GET /cargo/{cargo_id}/tracking` | Cargo tracking endpoint tests |

## Running Tests

### Using Docker Compose (Recommended)

The E2E tests are configured as a Docker Compose profile that only runs when explicitly requested.

```bash
# Start the application stack first (if not already running)
docker compose up -d

# Run E2E tests against local Docker environment
docker compose --profile tests up --build convoy-e2e-tests

# Run tests and see output in real-time
docker compose --profile tests up --build --attach convoy-e2e-tests convoy-e2e-tests
```

### Running Against Different Environments

```bash
# Against staging environment
API_BASE_URL=https://staging-api.convoy.example.com \
  docker compose --profile tests up --build convoy-e2e-tests

# Against production environment
API_BASE_URL=https://api.convoy.example.com \
  docker compose --profile tests up --build convoy-e2e-tests
```

### Running Locally (Without Docker)

```bash
# Navigate to tests directory
cd tests

# Install dependencies
uv sync

# Run tests against local development server
API_BASE_URL=http://localhost:8000 uv run pytest -v

# Run specific test file
API_BASE_URL=http://localhost:8000 uv run pytest test_health.py -v

# Run with more verbose output
API_BASE_URL=http://localhost:8000 uv run pytest -v --tb=long
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `API_BASE_URL` | `http://localhost:8000` | Base URL of the Convoy API to test |

### Pytest Options

The tests use the following pytest configuration (defined in `pyproject.toml`):

- `asyncio_mode = "auto"` - Automatically handle async tests
- `testpaths = ["."]` - Look for tests in the current directory
- `python_files = ["test_*.py"]` - Test file pattern

## Test Structure

```
tests/
├── __init__.py           # Package marker
├── conftest.py           # Shared fixtures (api_base_url, async_client)
├── pyproject.toml        # Dependencies and pytest config
├── Dockerfile            # Docker image for running tests
├── README.md             # This file
├── test_health.py        # Health endpoint tests
├── test_cargo_load.py    # Cargo load endpoint tests
└── test_cargo_tracking.py # Cargo tracking endpoint tests
```

## Writing New Tests

### Adding a New Test File

1. Create a new file named `test_<feature>.py`
2. Import the `async_client` fixture from conftest
3. Write async test functions or classes

Example:

```python
"""E2E tests for new feature."""

import httpx
import pytest


class TestNewFeature:
    """Tests for new feature endpoint."""

    async def test_new_endpoint(self, async_client: httpx.AsyncClient):
        """Test the new endpoint."""
        response = await async_client.get("/new-endpoint")
        assert response.status_code == 200
```

### Available Fixtures

| Fixture | Scope | Description |
|---------|-------|-------------|
| `api_base_url` | session | The API base URL from environment |
| `async_client` | function | Pre-configured httpx AsyncClient |

## Troubleshooting

### Tests fail with connection errors

Ensure the API is running and accessible at the configured `API_BASE_URL`:

```bash
# Check if API is running
curl http://localhost:8000/health

# For Docker, ensure the network is correct
docker network ls
```

### Tests timeout

Increase the timeout in `conftest.py` or check network connectivity:

```python
async with httpx.AsyncClient(
    base_url=api_base_url,
    timeout=60.0,  # Increase timeout
) as client:
    yield client
```

### Docker build fails

Ensure you have the latest dependencies:

```bash
# Rebuild without cache
docker compose --profile tests build --no-cache convoy-e2e-tests
```
