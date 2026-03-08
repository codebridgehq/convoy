"""Production E2E test for the complete batch processing flow.

This test module verifies the full batch processing pipeline against production:
1. Submit 100 requests to trigger batch creation
2. Wait for batch processing to complete
3. Verify cargo tracking shows correct status progression

Note: This test does not verify callback delivery since the callback URL
is a production endpoint without introspection capabilities.

Prerequisites:
- API_BASE_URL environment variable set (or uses default)
- ADMIN_API_KEY environment variable set for creating test project/API key
- AWS credentials configured for Bedrock access
"""

import asyncio
import logging
import os
import time
import uuid
from dataclasses import dataclass

import httpx
import pytest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Production configuration
API_BASE_URL = os.environ.get(
    "API_BASE_URL",
    "http://convoy-alb-dev-601855782.us-east-1.elb.amazonaws.com"
)
CALLBACK_URL = os.environ.get(
    "CALLBACK_URL",
    "https://oxfykx7mm6.execute-api.us-east-1.amazonaws.com/callback"
)
ADMIN_API_KEY = os.environ.get("ADMIN_API_KEY", "test-admin-key")

# Test configuration
BATCH_SIZE = 100  # Number of requests to send (matches BATCH_SIZE_THRESHOLD)
# Use Bedrock's Claude 3 Haiku - cheapest Claude model on Bedrock
MODEL = "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-haiku-20240307-v1:0"
MAX_TOKENS = 50  # Keep responses short to minimize cost
BATCH_TIMEOUT_SECONDS = 1800  # 30 minutes max for batch processing
POLL_INTERVAL_SECONDS = 30  # How often to check status


@dataclass
class BatchTestResult:
    """Result of a batch flow test."""

    total_requests: int
    successful_submissions: int
    failed_submissions: int
    cargo_ids: list[str]
    total_duration_seconds: float
    batch_processing_seconds: float
    final_statuses: dict[str, int]


async def create_test_project_and_api_key(
    base_url: str,
    admin_api_key: str,
) -> str:
    """Create a test project and API key for production testing.
    
    Args:
        base_url: API base URL.
        admin_api_key: Admin API key for management endpoints.
        
    Returns:
        The raw API key for the test project.
    """
    async with httpx.AsyncClient(
        base_url=base_url,
        timeout=30.0,
        headers={"X-Admin-API-Key": admin_api_key},
    ) as client:
        # Create a unique test project
        project_slug = f"prod-test-{uuid.uuid4().hex[:8]}"
        
        project_response = await client.post(
            "/management/projects",
            json={
                "name": "Production E2E Test Project",
                "slug": project_slug,
                "description": "Project created for production E2E testing",
            },
        )
        
        if project_response.status_code != 201:
            raise RuntimeError(
                f"Failed to create test project: {project_response.status_code} - "
                f"{project_response.text}"
            )
        
        project = project_response.json()
        logger.info(f"Created test project: {project['slug']} (ID: {project['id']})")
        
        # Create API key for the project (use slug, not id)
        key_response = await client.post(
            f"/admin/projects/{project['slug']}/api-keys",
            json={"name": "Production E2E Test API Key"},
        )
        
        if key_response.status_code != 201:
            raise RuntimeError(
                f"Failed to create API key: {key_response.status_code} - "
                f"{key_response.text}"
            )
        
        api_key = key_response.json()["key"]
        logger.info(f"Created API key for project: {project['slug']}")
        
        return api_key


async def submit_cargo_requests(
    client: httpx.AsyncClient,
    num_requests: int,
    callback_url: str,
) -> tuple[list[str], int, int]:
    """Submit cargo requests concurrently.

    Args:
        client: HTTP client for API calls (must be authenticated).
        num_requests: Number of requests to submit.
        callback_url: URL for callbacks.

    Returns:
        Tuple of (cargo_ids, success_count, failure_count)
    """
    cargo_ids = []
    success_count = 0
    failure_count = 0

    # Generate prompts
    prompts = []
    for i in range(num_requests):
        prompts.append({
            "params": {
                "model": MODEL,
                "max_tokens": MAX_TOKENS,
                "messages": [
                    {
                        "role": "user",
                        "content": f"Reply with only the number {i}. Nothing else."
                    }
                ]
            },
            "callback_url": callback_url,
        })

    # Submit requests in batches of 10 for controlled concurrency
    batch_size = 10
    for batch_start in range(0, len(prompts), batch_size):
        batch_end = min(batch_start + batch_size, len(prompts))
        batch_prompts = prompts[batch_start:batch_end]

        tasks = []
        for prompt in batch_prompts:
            tasks.append(client.post("/cargo/load", json=prompt))

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        for response in responses:
            if isinstance(response, Exception):
                logger.error(f"Request failed with exception: {response}")
                failure_count += 1
            elif response.status_code == 200:
                data = response.json()
                cargo_ids.append(data["cargo_id"])
                success_count += 1
            else:
                logger.error(
                    f"Request failed with status {response.status_code}: "
                    f"{response.text}"
                )
                failure_count += 1

        logger.info(
            f"Submitted {batch_end}/{len(prompts)} requests "
            f"(success: {success_count}, failed: {failure_count})"
        )

    return cargo_ids, success_count, failure_count


async def wait_for_batch_processing(
    client: httpx.AsyncClient,
    cargo_ids: list[str],
    timeout_seconds: float = BATCH_TIMEOUT_SECONDS,
) -> bool:
    """Wait for batch processing to complete.

    Monitors cargo tracking status until all requests are processed
    or timeout is reached.

    Args:
        client: HTTP client for API calls (must be authenticated).
        cargo_ids: List of cargo IDs to monitor.
        timeout_seconds: Maximum time to wait.

    Returns:
        True if all requests completed, False if timeout.
    """
    start_time = time.time()
    completed_statuses = {
        "callback_pending",
        "callback_delivered",
        "callback_failed",
        "completed",
        "failed",
    }

    while True:
        elapsed = time.time() - start_time
        if elapsed >= timeout_seconds:
            logger.warning(f"Timeout waiting for batch processing after {elapsed:.1f}s")
            return False

        # Sample a few cargo IDs to check status
        sample_size = min(10, len(cargo_ids))
        sample_ids = cargo_ids[:sample_size]

        completed_count = 0
        status_counts: dict[str, int] = {}

        for cargo_id in sample_ids:
            try:
                response = await client.get(f"/cargo/{cargo_id}/tracking")
                if response.status_code == 200:
                    data = response.json()
                    status = data.get("status", "unknown")
                    status_counts[status] = status_counts.get(status, 0) + 1
                    if status in completed_statuses:
                        completed_count += 1
            except Exception as e:
                logger.warning(f"Error checking status for {cargo_id}: {e}")

        logger.info(
            f"Batch processing status (sample of {sample_size}): "
            f"{status_counts} - elapsed: {elapsed:.1f}s"
        )

        # If all sampled requests are completed, assume batch is done
        if completed_count == sample_size:
            logger.info("Batch processing appears complete")
            return True

        await asyncio.sleep(POLL_INTERVAL_SECONDS)


async def verify_cargo_statuses(
    client: httpx.AsyncClient,
    cargo_ids: list[str],
) -> dict[str, int]:
    """Verify final status of all cargo requests.

    Args:
        client: HTTP client for API calls (must be authenticated).
        cargo_ids: List of cargo IDs to check.

    Returns:
        Dictionary of status -> count.
    """
    status_counts: dict[str, int] = {}

    for cargo_id in cargo_ids:
        try:
            response = await client.get(f"/cargo/{cargo_id}/tracking")
            if response.status_code == 200:
                data = response.json()
                status = data.get("status", "unknown")
                status_counts[status] = status_counts.get(status, 0) + 1
            else:
                status_counts["error"] = status_counts.get("error", 0) + 1
        except Exception as e:
            logger.warning(f"Error checking status for {cargo_id}: {e}")
            status_counts["error"] = status_counts.get("error", 0) + 1

    return status_counts


async def run_production_batch_test() -> BatchTestResult:
    """Run the production batch test.
    
    Returns:
        BatchTestResult with test metrics.
    """
    start_time = time.time()
    
    # First, create a test project and API key
    logger.info("Creating test project and API key...")
    api_key = await create_test_project_and_api_key(API_BASE_URL, ADMIN_API_KEY)
    
    async with httpx.AsyncClient(
        base_url=API_BASE_URL,
        timeout=60.0,
        headers={"X-API-Key": api_key},
    ) as client:
        # Step 1: Verify API health (health endpoint is public)
        logger.info("Checking API health...")
        async with httpx.AsyncClient(
            base_url=API_BASE_URL,
            timeout=10.0,
        ) as health_client:
            health_response = await health_client.get("/health")
            if health_response.status_code != 200:
                raise RuntimeError(f"API health check failed: {health_response.text}")
        logger.info("API is healthy")

        # Step 2: Submit cargo requests
        logger.info(f"Submitting {BATCH_SIZE} cargo requests...")
        submission_start = time.time()

        cargo_ids, success_count, failure_count = await submit_cargo_requests(
            client,
            BATCH_SIZE,
            CALLBACK_URL,
        )

        submission_duration = time.time() - submission_start
        logger.info(
            f"Submitted {success_count} requests in {submission_duration:.1f}s "
            f"({failure_count} failures)"
        )

        if success_count < BATCH_SIZE:
            logger.warning(
                f"Only {success_count}/{BATCH_SIZE} requests submitted successfully"
            )

        # Step 3: Wait for batch processing
        logger.info("Waiting for batch processing to complete...")
        logger.info("This may take up to 30 minutes for Bedrock batch processing...")
        batch_start = time.time()

        batch_completed = await wait_for_batch_processing(
            client,
            cargo_ids,
        )

        batch_duration = time.time() - batch_start
        logger.info(f"Batch processing took {batch_duration:.1f}s")

        # Step 4: Verify final cargo statuses
        logger.info("Verifying final cargo statuses...")
        final_statuses = await verify_cargo_statuses(client, cargo_ids)
        logger.info(f"Final status distribution: {final_statuses}")

        # Calculate totals
        total_duration = time.time() - start_time

        # Log summary
        logger.info("=" * 60)
        logger.info("PRODUCTION BATCH FLOW TEST SUMMARY")
        logger.info("=" * 60)
        logger.info(f"API URL: {API_BASE_URL}")
        logger.info(f"Callback URL: {CALLBACK_URL}")
        logger.info(f"Total requests: {BATCH_SIZE}")
        logger.info(f"Successful submissions: {success_count}")
        logger.info(f"Failed submissions: {failure_count}")
        logger.info(f"Final statuses: {final_statuses}")
        logger.info(f"Submission time: {submission_duration:.1f}s")
        logger.info(f"Batch processing time: {batch_duration:.1f}s")
        logger.info(f"Total duration: {total_duration:.1f}s")
        logger.info(f"Batch completed: {batch_completed}")
        logger.info("=" * 60)

        return BatchTestResult(
            total_requests=BATCH_SIZE,
            successful_submissions=success_count,
            failed_submissions=failure_count,
            cargo_ids=cargo_ids,
            total_duration_seconds=total_duration,
            batch_processing_seconds=batch_duration,
            final_statuses=final_statuses,
        )


class TestProductionBatchFlow:
    """Production tests for the complete batch processing flow."""

    @pytest.mark.asyncio
    async def test_batch_flow_100_requests(self):
        """Test the complete batch flow with 100 requests against production.

        This test:
        1. Creates a test project and API key
        2. Submits 100 cargo requests to trigger batch creation
        3. Waits for batch processing to complete
        4. Verifies cargo tracking shows correct final status
        """
        result = await run_production_batch_test()

        # Assertions
        assert result.successful_submissions >= BATCH_SIZE * 0.95, (
            f"Expected at least {BATCH_SIZE * 0.95} successful submissions, "
            f"got {result.successful_submissions}"
        )

        # Most cargo should be in a completed state
        completed_count = (
            result.final_statuses.get("callback_delivered", 0) +
            result.final_statuses.get("callback_pending", 0) +
            result.final_statuses.get("completed", 0)
        )
        min_expected_completed = int(BATCH_SIZE * 0.90)
        assert completed_count >= min_expected_completed, (
            f"Expected at least {min_expected_completed} completed, "
            f"got {completed_count}. Statuses: {result.final_statuses}"
        )


if __name__ == "__main__":
    # Allow running directly with: python test_batch_flow_production.py
    asyncio.run(run_production_batch_test())
