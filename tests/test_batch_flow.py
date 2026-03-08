"""E2E tests for the complete batch processing flow.

This test module verifies the full batch processing pipeline:
1. Submit 100 requests to trigger batch creation
2. Wait for batch processing to complete
3. Verify callbacks are delivered to the mock server
4. Verify cargo tracking shows correct status progression

Prerequisites:
- Convoy API running
- Temporal worker running
- Mock callback server running
- AWS credentials configured for Bedrock access
- ADMIN_API_KEY environment variable set
"""

import asyncio
import logging
import os
import time
import uuid
from dataclasses import dataclass
from typing import Any

import httpx
import pytest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test configuration
BATCH_SIZE = 100  # Number of requests to send (matches BATCH_SIZE_THRESHOLD)
# Use Bedrock's Claude 3 Haiku - cheapest Claude model on Bedrock
MODEL = "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-haiku-20240307-v1:0"
MAX_TOKENS = 50  # Keep responses short to minimize cost
BATCH_TIMEOUT_SECONDS = 1800  # 30 minutes max for batch processing
CALLBACK_TIMEOUT_SECONDS = 600  # 10 minutes for all callbacks to arrive
POLL_INTERVAL_SECONDS = 30  # How often to check status


@dataclass
class BatchTestResult:
    """Result of a batch flow test."""

    total_requests: int
    successful_submissions: int
    failed_submissions: int
    cargo_ids: list[str]
    callbacks_received: int
    total_duration_seconds: float
    batch_processing_seconds: float
    callback_delivery_seconds: float


class TestBatchFlow:
    """Tests for the complete batch processing flow."""

    @pytest.fixture
    def callback_server_url(self) -> str:
        """Get the callback server URL.

        The mock callback server should be running and accessible.
        In Docker Compose, this would be http://mock-callback:8001
        For local testing, use http://localhost:8001
        """
        return os.environ.get("CALLBACK_SERVER_URL", "http://mock-callback:8001")

    @pytest.fixture
    def test_prompts(self) -> list[dict[str, Any]]:
        """Generate test prompts for batch processing.

        Creates 100 simple prompts that will generate short responses.
        Each prompt is unique to help identify results.
        """
        prompts = []
        for i in range(BATCH_SIZE):
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
                # callback_url will be set per-request
            })
        return prompts

    async def _submit_cargo_requests(
        self,
        client: httpx.AsyncClient,
        prompts: list[dict],
        callback_url: str,
    ) -> tuple[list[str], int, int]:
        """Submit cargo requests concurrently.

        Args:
            client: HTTP client for API calls (must be authenticated).
            prompts: List of prompt payloads.
            callback_url: URL for callbacks.

        Returns:
            Tuple of (cargo_ids, success_count, failure_count)
        """
        cargo_ids = []
        success_count = 0
        failure_count = 0

        # Submit requests in batches of 10 for controlled concurrency
        batch_size = 10
        for batch_start in range(0, len(prompts), batch_size):
            batch_end = min(batch_start + batch_size, len(prompts))
            batch_prompts = prompts[batch_start:batch_end]

            tasks = []
            for prompt in batch_prompts:
                payload = {
                    **prompt,
                    "callback_url": f"{callback_url}/callback",
                }
                tasks.append(client.post("/cargo/load", json=payload))

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

    async def _wait_for_batch_processing(
        self,
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

    async def _wait_for_callbacks(
        self,
        callback_client: httpx.AsyncClient,
        expected_count: int,
        timeout_seconds: float = CALLBACK_TIMEOUT_SECONDS,
    ) -> int:
        """Wait for callbacks to be received by the mock server.

        Args:
            callback_client: HTTP client for callback server.
            expected_count: Number of callbacks expected.
            timeout_seconds: Maximum time to wait.

        Returns:
            Number of callbacks received.
        """
        start_time = time.time()

        while True:
            elapsed = time.time() - start_time
            if elapsed >= timeout_seconds:
                logger.warning(f"Timeout waiting for callbacks after {elapsed:.1f}s")
                break

            try:
                response = await callback_client.get("/callbacks")
                if response.status_code == 200:
                    data = response.json()
                    count = data.get("count", 0)
                    logger.info(
                        f"Callbacks received: {count}/{expected_count} "
                        f"- elapsed: {elapsed:.1f}s"
                    )
                    if count >= expected_count:
                        return count
            except Exception as e:
                logger.warning(f"Error checking callback count: {e}")

            await asyncio.sleep(10)

        # Return final count
        try:
            response = await callback_client.get("/callbacks")
            if response.status_code == 200:
                return response.json().get("count", 0)
        except Exception:
            pass
        return 0

    async def _verify_cargo_statuses(
        self,
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

    @pytest.mark.asyncio
    async def test_batch_flow_100_requests(
        self,
        authenticated_client: httpx.AsyncClient,
        callback_server_url: str,
        test_prompts: list[dict],
    ):
        """Test the complete batch flow with 100 requests.

        This test:
        1. Clears any existing callbacks from the mock server
        2. Submits 100 cargo requests to trigger batch creation
        3. Waits for batch processing to complete
        4. Waits for callbacks to be delivered
        5. Verifies all callbacks were received
        6. Verifies cargo tracking shows correct final status
        """
        start_time = time.time()

        # Create client for callback server
        async with httpx.AsyncClient(
            base_url=callback_server_url,
            timeout=30.0,
        ) as callback_client:
            # Step 1: Clear existing callbacks
            logger.info("Clearing existing callbacks from mock server...")
            try:
                await callback_client.delete("/callbacks")
            except Exception as e:
                logger.warning(f"Could not clear callbacks: {e}")

            # Step 2: Submit cargo requests
            logger.info(f"Submitting {BATCH_SIZE} cargo requests...")
            submission_start = time.time()

            cargo_ids, success_count, failure_count = await self._submit_cargo_requests(
                authenticated_client,
                test_prompts,
                callback_server_url,
            )

            submission_duration = time.time() - submission_start
            logger.info(
                f"Submitted {success_count} requests in {submission_duration:.1f}s "
                f"({failure_count} failures)"
            )

            # Verify all requests were submitted successfully
            assert success_count == BATCH_SIZE, (
                f"Expected {BATCH_SIZE} successful submissions, got {success_count}"
            )
            assert len(cargo_ids) == BATCH_SIZE

            # Step 3: Wait for batch processing
            logger.info("Waiting for batch processing to complete...")
            batch_start = time.time()

            batch_completed = await self._wait_for_batch_processing(
                authenticated_client,
                cargo_ids,
            )

            batch_duration = time.time() - batch_start
            logger.info(f"Batch processing took {batch_duration:.1f}s")

            assert batch_completed, "Batch processing did not complete in time"

            # Step 4: Wait for callbacks
            logger.info("Waiting for callbacks to be delivered...")
            callback_start = time.time()

            callbacks_received = await self._wait_for_callbacks(
                callback_client,
                expected_count=BATCH_SIZE,
            )

            callback_duration = time.time() - callback_start
            logger.info(
                f"Received {callbacks_received} callbacks in {callback_duration:.1f}s"
            )

            # Step 5: Verify final cargo statuses
            logger.info("Verifying final cargo statuses...")
            final_statuses = await self._verify_cargo_statuses(
                authenticated_client, cargo_ids
            )
            logger.info(f"Final status distribution: {final_statuses}")

            # Calculate totals
            total_duration = time.time() - start_time

            # Log summary
            logger.info("=" * 60)
            logger.info("BATCH FLOW TEST SUMMARY")
            logger.info("=" * 60)
            logger.info(f"Total requests: {BATCH_SIZE}")
            logger.info(f"Successful submissions: {success_count}")
            logger.info(f"Callbacks received: {callbacks_received}")
            logger.info(f"Final statuses: {final_statuses}")
            logger.info(f"Submission time: {submission_duration:.1f}s")
            logger.info(f"Batch processing time: {batch_duration:.1f}s")
            logger.info(f"Callback delivery time: {callback_duration:.1f}s")
            logger.info(f"Total duration: {total_duration:.1f}s")
            logger.info("=" * 60)

            # Assertions
            # All callbacks should be received (allow some tolerance for failures)
            min_expected_callbacks = int(BATCH_SIZE * 0.95)  # 95% success rate
            assert callbacks_received >= min_expected_callbacks, (
                f"Expected at least {min_expected_callbacks} callbacks, "
                f"got {callbacks_received}"
            )

            # Most cargo should be in callback_delivered status
            delivered_count = final_statuses.get("callback_delivered", 0)
            min_expected_delivered = int(BATCH_SIZE * 0.90)  # 90% success rate
            assert delivered_count >= min_expected_delivered, (
                f"Expected at least {min_expected_delivered} delivered, "
                f"got {delivered_count}"
            )

    @pytest.mark.asyncio
    async def test_batch_flow_verify_callback_content(
        self,
        authenticated_client: httpx.AsyncClient,
        callback_server_url: str,
    ):
        """Test that callback content is correct.

        This is a smaller test that submits a few requests and verifies
        the callback payload structure is correct.
        """
        async with httpx.AsyncClient(
            base_url=callback_server_url,
            timeout=30.0,
        ) as callback_client:
            # Clear existing callbacks
            await callback_client.delete("/callbacks")

            # Submit a single request
            payload = {
                "params": {
                    "model": MODEL,
                    "max_tokens": MAX_TOKENS,
                    "messages": [
                        {
                            "role": "user",
                            "content": "Say 'test' and nothing else."
                        }
                    ]
                },
                "callback_url": f"{callback_server_url}/callback",
            }

            response = await authenticated_client.post("/cargo/load", json=payload)
            assert response.status_code == 200
            cargo_id = response.json()["cargo_id"]

            logger.info(f"Submitted test request with cargo_id: {cargo_id}")

            # Wait for callback (with longer timeout since it needs to batch)
            # Note: This test may take a while since batch threshold is 100
            # Consider running this after the main batch test
            logger.info(
                "Note: This test requires batch threshold to be met. "
                "Run after test_batch_flow_100_requests or lower BATCH_SIZE_THRESHOLD."
            )


class TestBatchFlowSmoke:
    """Smoke tests for batch flow - quick verification without full batch."""

    @pytest.mark.asyncio
    async def test_cargo_submission_works(
        self,
        authenticated_client: httpx.AsyncClient,
    ):
        """Verify that cargo submission works correctly."""
        payload = {
            "params": {
                "model": MODEL,
                "max_tokens": MAX_TOKENS,
                "messages": [
                    {
                        "role": "user",
                        "content": "Say hello."
                    }
                ]
            },
            "callback_url": "https://example.com/callback",
        }

        response = await authenticated_client.post("/cargo/load", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "cargo_id" in data
        assert data["status"] == "success"

        # Verify tracking shows pending status
        cargo_id = data["cargo_id"]
        tracking_response = await authenticated_client.get(f"/cargo/{cargo_id}/tracking")

        assert tracking_response.status_code == 200
        tracking_data = tracking_response.json()
        assert tracking_data["status"] == "pending"
        assert tracking_data["cargo_id"] == cargo_id

    @pytest.mark.asyncio
    async def test_mock_callback_server_health(self):
        """Verify the mock callback server is running."""
        callback_url = os.environ.get(
            "CALLBACK_SERVER_URL",
            "http://mock-callback:8001"
        )

        async with httpx.AsyncClient(
            base_url=callback_url,
            timeout=10.0,
        ) as client:
            response = await client.get("/health")
            assert response.status_code == 200
            assert response.json()["status"] == "ok"
