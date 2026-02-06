"""Callback delivery workflow for reliable result delivery."""

from dataclasses import dataclass
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from src.worker.activities.callback_activities import (
        deliver_callback,
        get_callback_payload,
        get_cargo_callback_url,
        mark_callback_failed,
        update_callback_status,
    )
    from src.worker.config import CallbackConfig


@workflow.defn
class CallbackDeliveryWorkflow:
    """Workflow for delivering callbacks with exponential backoff retry.

    This workflow handles reliable delivery of results to callback URLs,
    with configurable retry logic and exponential backoff.
    """

    @workflow.run
    async def run(self, cargo_request_id: str) -> bool:
        """Deliver a callback for a cargo request.

        Args:
            cargo_request_id: The cargo request ID to deliver callback for.

        Returns:
            True if delivery was successful, False otherwise.
        """
        workflow.logger.info(f"Starting callback delivery for {cargo_request_id}")

        # Get callback URL and payload
        try:
            callback_url = await workflow.execute_activity(
                get_cargo_callback_url,
                cargo_request_id,
                start_to_close_timeout=timedelta(seconds=30),
            )

            payload = await workflow.execute_activity(
                get_callback_payload,
                cargo_request_id,
                start_to_close_timeout=timedelta(seconds=30),
            )
        except Exception as e:
            workflow.logger.error(
                f"Failed to get callback info for {cargo_request_id}: {e}"
            )
            return False

        # Retry policy with exponential backoff
        # Delays: 1min, 5min, 15min, 1hr (as per config)
        # Note: Using hardcoded values to avoid sandbox restrictions
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=60),
            backoff_coefficient=3.0,
            maximum_interval=timedelta(hours=1),
            maximum_attempts=5,
        )

        try:
            # Attempt delivery with retries
            success = await workflow.execute_activity(
                deliver_callback,
                args=[cargo_request_id, callback_url, payload],
                start_to_close_timeout=timedelta(seconds=40),
                retry_policy=retry_policy,
            )

            if success:
                # Update status to delivered
                await workflow.execute_activity(
                    update_callback_status,
                    args=[cargo_request_id, "delivered"],
                    start_to_close_timeout=timedelta(seconds=30),
                )
                workflow.logger.info(
                    f"Callback delivered successfully for {cargo_request_id}"
                )
                return True

        except Exception as e:
            workflow.logger.warning(
                f"Callback delivery failed for {cargo_request_id} after all retries: {e}"
            )

        # Mark as failed after all retries exhausted
        await workflow.execute_activity(
            mark_callback_failed,
            cargo_request_id,
            start_to_close_timeout=timedelta(seconds=30),
        )

        workflow.logger.error(
            f"Callback marked as failed for {cargo_request_id}"
        )
        return False
