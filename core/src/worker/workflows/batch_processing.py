"""Batch processing workflow for handling individual batch lifecycle."""

from dataclasses import dataclass
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ActivityError

with workflow.unsafe.imports_passed_through():
    from src.worker.activities.batch_activities import (
        mark_batch_failed,
        poll_batch_status,
        process_batch_results,
        submit_batch_to_provider,
    )


@dataclass
class BatchProcessingInput:
    """Input for the batch processing workflow."""

    batch_job_id: str
    provider: str


@workflow.defn
class BatchProcessingWorkflow:
    """Workflow that handles the lifecycle of a single batch.

    This workflow is spawned by BatchSchedulerWorkflow for each batch,
    allowing multiple batches to be processed simultaneously.

    If submission fails after all retries, the batch is marked as failed
    and its cargo_requests are reset to pending for reprocessing.
    """

    @workflow.run
    async def run(self, input: BatchProcessingInput) -> None:
        """Process a single batch through its complete lifecycle.

        Args:
            input: BatchProcessingInput containing batch_job_id and provider.
        """
        # Retry policy for submission - will retry on transient errors
        submit_retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=5),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(minutes=5),
            maximum_attempts=5,
        )

        # Retry policy for other activities
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(minutes=5),
            maximum_attempts=5,
        )

        # No retry for marking batch as failed - should succeed on first try
        no_retry_policy = RetryPolicy(maximum_attempts=1)

        batch_job_id = input.batch_job_id

        workflow.logger.info(
            f"Starting batch processing workflow for batch {batch_job_id} "
            f"(provider: {input.provider})"
        )

        try:
            # Submit to provider
            provider_job_id = await workflow.execute_activity(
                submit_batch_to_provider,
                batch_job_id,
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=submit_retry_policy,
            )

            workflow.logger.info(
                f"Submitted batch {batch_job_id} to provider, job ID: {provider_job_id}"
            )

        except ActivityError as e:
            # Submission failed after all retries - mark batch as failed and reset cargo_requests
            error_message = self._extract_error_message(e)
            workflow.logger.error(
                f"Failed to submit batch {batch_job_id} after retries: {error_message}"
            )

            # Mark batch as failed and reset cargo_requests to pending
            reset_count = await workflow.execute_activity(
                mark_batch_failed,
                args=[batch_job_id, error_message],
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=no_retry_policy,
            )

            workflow.logger.info(
                f"Batch {batch_job_id} marked as failed. "
                f"Reset {reset_count} cargo_requests to pending for reprocessing."
            )
            return  # Exit workflow - cargo_requests will be picked up by next batch

        try:
            # Poll until complete
            completed = False
            status_result = {}
            while not completed:
                # Wait before polling
                await workflow.sleep(timedelta(minutes=1))

                status_result = await workflow.execute_activity(
                    poll_batch_status,
                    args=[batch_job_id, provider_job_id],
                    start_to_close_timeout=timedelta(seconds=30),
                    retry_policy=retry_policy,
                )

                completed = status_result["completed"]
                workflow.logger.info(
                    f"Batch {batch_job_id} status: {status_result['status']}"
                )

                if status_result.get("error_message"):
                    workflow.logger.error(
                        f"Batch {batch_job_id} error: {status_result['error_message']}"
                    )

            # Process results and trigger callbacks
            if status_result.get("status") not in ("failed", "cancelled"):
                cargo_request_ids = await workflow.execute_activity(
                    process_batch_results,
                    batch_job_id,
                    start_to_close_timeout=timedelta(minutes=10),
                    retry_policy=retry_policy,
                )

                workflow.logger.info(
                    f"Processed {len(cargo_request_ids)} results for batch {batch_job_id}"
                )

                # Start child workflows for callback delivery
                for cargo_request_id in cargo_request_ids:
                    await workflow.start_child_workflow(
                        "CallbackDeliveryWorkflow",
                        cargo_request_id,
                        id=f"callback-delivery-{cargo_request_id}",
                    )

                workflow.logger.info(
                    f"Started {len(cargo_request_ids)} callback delivery workflows "
                    f"for batch {batch_job_id}"
                )
            else:
                workflow.logger.warning(
                    f"Batch {batch_job_id} ended with status {status_result.get('status')}, "
                    f"skipping result processing"
                )

        except Exception as e:
            workflow.logger.error(
                f"Error processing batch {batch_job_id}: {e}"
            )
            raise  # Re-raise to let Temporal handle retries/failure

    def _extract_error_message(self, error: ActivityError) -> str:
        """Extract a meaningful error message from an ActivityError.

        Args:
            error: The ActivityError from a failed activity.

        Returns:
            A human-readable error message.
        """
        # Try to get the cause chain to find the actual error
        cause = error.__cause__
        messages = []

        while cause:
            if hasattr(cause, "message"):
                messages.append(str(cause.message))
            elif str(cause):
                messages.append(str(cause))
            cause = getattr(cause, "__cause__", None)

        if messages:
            # Return the most specific error (last in chain)
            return messages[-1]

        # Fallback to the error string
        return str(error)
