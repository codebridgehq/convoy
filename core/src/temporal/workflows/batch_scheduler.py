"""Batch scheduler workflow for monitoring and creating batches."""

from dataclasses import dataclass
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from src.temporal.activities.batch_activities import (
        check_pending_requests,
        create_batch_job,
        poll_batch_status,
        process_batch_results,
        submit_batch_to_provider,
    )
    from src.temporal.config import BatchConfig


@dataclass
class BatchSchedulerInput:
    """Input for the batch scheduler workflow."""

    provider: str
    check_interval_seconds: int = 30


@workflow.defn
class BatchSchedulerWorkflow:
    """Workflow that continuously monitors pending requests and creates batches.

    This workflow runs indefinitely for each provider, checking for pending
    requests and creating batches when thresholds are met.
    """

    @workflow.run
    async def run(self, input: BatchSchedulerInput) -> None:
        """Run the batch scheduler for a provider.

        Args:
            input: BatchSchedulerInput containing provider and config.
        """
        # Retry policy for activities
        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(minutes=5),
            maximum_attempts=5,
        )

        workflow.logger.info(f"Starting batch scheduler for provider: {input.provider}")

        while True:
            try:
                # Check if we should create a batch
                pending_result = await workflow.execute_activity(
                    check_pending_requests,
                    input.provider,
                    start_to_close_timeout=timedelta(seconds=30),
                    retry_policy=retry_policy,
                )

                if pending_result["should_batch"]:
                    workflow.logger.info(
                        f"Creating batch for {input.provider}: "
                        f"{pending_result['pending_count']} pending requests"
                    )

                    # Create the batch job
                    batch_job_id = await workflow.execute_activity(
                        create_batch_job,
                        input.provider,
                        start_to_close_timeout=timedelta(seconds=60),
                        retry_policy=retry_policy,
                    )

                    workflow.logger.info(f"Created batch job: {batch_job_id}")

                    # Submit to provider
                    provider_job_id = await workflow.execute_activity(
                        submit_batch_to_provider,
                        batch_job_id,
                        start_to_close_timeout=timedelta(minutes=5),
                        retry_policy=retry_policy,
                    )

                    workflow.logger.info(
                        f"Submitted batch to provider, job ID: {provider_job_id}"
                    )

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
                            f"Started {len(cargo_request_ids)} callback delivery workflows"
                        )

            except Exception as e:
                workflow.logger.error(f"Error in batch scheduler for {input.provider}: {e}")
                # Continue running despite errors

            # Wait before next check
            await workflow.sleep(timedelta(seconds=input.check_interval_seconds))
