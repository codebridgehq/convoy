# Convoy E2E Tests

End-to-end tests for the Convoy API application using pytest and httpx.

## Overview

These tests verify the Convoy API endpoints work correctly by making real HTTP requests to a running API instance. The tests can be run against any environment (local, staging, production) by configuring the `API_BASE_URL` environment variable.

## Test Coverage

| Test File | Endpoint | Description |
|-----------|----------|-------------|
| `test_auth.py` | Auth endpoints | Authentication and API key tests |
| `test_batch_flow.py` | Full flow | **Batch processing E2E test** - sends 100 requests to verify complete flow |
| `test_cargo_load.py` | `POST /cargo/load` | Cargo load endpoint tests (valid/invalid payloads) |

## Running Tests

### Using Docker Compose (Recommended)

The E2E tests are configured as a Docker Compose profile that only runs when explicitly requested.

```bash
# Start the application stack first (if not already running)
docker compose up -d

# Run E2E tests against local Docker environment
docker compose --profile tests run --rm convoy-tests

# Run tests and see output in real-time
docker compose --profile tests run --rm convoy-tests pytest -v
```

### Running Against Different Environments

```bash
# Against staging environment
API_BASE_URL=https://staging-api.convoy.example.com \
  docker compose --profile tests run --rm convoy-tests

# Against production environment
API_BASE_URL=https://api.convoy.example.com \
  docker compose --profile tests run --rm convoy-tests
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
| `CALLBACK_SERVER_URL` | `http://mock-callback:8001` | URL of the mock callback server (for batch flow tests) |

### Pytest Options

The tests use the following pytest configuration (defined in `pyproject.toml`):

- `asyncio_mode = "auto"` - Automatically handle async tests
- `testpaths = ["."]` - Look for tests in the current directory
- `python_files = ["test_*.py"]` - Test file pattern

## Test Structure

```
tests/
├── __init__.py              # Package marker
├── conftest.py              # Shared fixtures (api_base_url, async_client)
├── pyproject.toml           # Dependencies and pytest config
├── Dockerfile               # Docker image for running tests
├── Dockerfile.callback      # Docker image for mock callback server
├── mock_callback_server.py  # FastAPI server for receiving callbacks
├── README.md                # This file
├── test_auth.py             # Authentication tests
├── test_batch_flow.py       # Batch processing E2E tests
├── test_cargo_load.py       # Cargo load endpoint tests
└── test_cargo_tracking.py   # Cargo tracking endpoint tests
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
docker compose --profile tests build --no-cache convoy-tests
```

## Batch Flow Test

The `test_batch_flow.py` file contains a comprehensive E2E test that verifies the complete batch processing pipeline.

### What It Tests

1. **Request Submission**: Sends 100 cargo requests to the API
2. **Batch Creation**: Verifies the batch scheduler creates a batch when threshold is met
3. **Batch Processing**: Waits for Bedrock to process the batch
4. **Callback Delivery**: Verifies all callbacks are delivered to the mock server
5. **Status Tracking**: Confirms cargo tracking shows correct status progression

### Prerequisites

- AWS credentials configured for Bedrock access
- `BATCH_SIZE_THRESHOLD` set to 100 (default)
- All services running (API, Worker, Temporal, PostgreSQL)

### Running the Batch Flow Test

```bash
# Start all services including mock callback server
docker compose --profile tests up -d

# Run only the batch flow test
docker compose --profile tests run --rm convoy-tests \
  pytest test_batch_flow.py::TestBatchFlow::test_batch_flow_100_requests -v -s

# Run smoke tests first (quick verification)
docker compose --profile tests run --rm convoy-tests \
  pytest test_batch_flow.py::TestBatchFlowSmoke -v
```

### Test Configuration

The test uses these defaults (configurable in `test_batch_flow.py`):

| Setting | Default | Description |
|---------|---------|-------------|
| `BATCH_SIZE` | 100 | Number of requests to send |
| `MODEL` | `anthropic.claude-3-haiku-20240307-v1:0` | Bedrock model (cheapest Claude) |
| `MAX_TOKENS` | 50 | Max response tokens (keeps costs low) |
| `BATCH_TIMEOUT_SECONDS` | 1800 | Max wait for batch processing (30 min) |
| `CALLBACK_TIMEOUT_SECONDS` | 600 | Max wait for callbacks (10 min) |

### Expected Duration

- **Request Submission**: ~10-30 seconds
- **Batch Processing**: 5-20 minutes (depends on Bedrock queue)
- **Callback Delivery**: 1-5 minutes
- **Total**: ~10-30 minutes

### Cost Estimate

Using Claude 3 Haiku on Bedrock with 100 requests:
- Input: ~100 tokens × 100 requests = 10,000 tokens (~$0.0025)
- Output: ~50 tokens × 100 requests = 5,000 tokens (~$0.00125)
- **Total: ~$0.004 per test run**

### Mock Callback Server

The mock callback server (`mock_callback_server.py`) provides:

- `POST /callback` - Receives callbacks from Convoy
- `GET /callbacks` - Lists all received callbacks
- `GET /callbacks/{cargo_id}` - Gets specific callback
- `DELETE /callbacks` - Clears stored callbacks
- `GET /health` - Health check

You can inspect callbacks during testing:

```bash
# Check callback count
curl http://localhost:8001/callbacks

# Get specific callback
curl http://localhost:8001/callbacks/cargo_abc123
```
