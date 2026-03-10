"""Batch scheduler workflow for monitoring and creating batches."""

from dataclasses import dataclass
from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from src.worker.activities.batch_activities import (
        check_pending_requests,
        create_batch_job,
    )
    from src.worker.config import BatchConfig
    from src.worker.workflows.batch_processing import BatchProcessingInput


@dataclass
class BatchSchedulerInput:
    """Input for the batch scheduler workflow."""

    provider: str
    check_interval_seconds: int = 30
    # Track iterations across continue-as-new to maintain total count for logging
    total_iterations: int = 0


# Maximum iterations before triggering continue-as-new to reset workflow history.
# Each iteration can generate multiple events (activities, timers, child workflows).
# With ~10-20 events per iteration, 500 iterations keeps us well under the 50K limit.
MAX_ITERATIONS_BEFORE_CONTINUE_AS_NEW = 500


@workflow.defn
class BatchSchedulerWorkflow:
    """Workflow that continuously monitors pending requests and creates batches.

    This workflow runs indefinitely for each provider, checking for pending
    requests and creating batches when thresholds are met. Each batch is
    processed by a separate BatchProcessingWorkflow, allowing multiple
    batches to be processed simultaneously.

    For Bedrock, batches are created per-model since Bedrock requires a single
    model per batch job. For Anthropic, all requests can be batched together.
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

        workflow.logger.info(
            f"Starting batch scheduler for provider: {input.provider} "
            f"(total iterations so far: {input.total_iterations})"
        )

        iteration_count = 0

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
                    models_ready = pending_result.get("models_ready")

                    if models_ready:
                        # Bedrock: Create separate batch for each model that meets threshold
                        # This ensures all requests in a batch use the same model
                        workflow.logger.info(
                            f"Creating Bedrock batches for {len(models_ready)} models: {models_ready}"
                        )

                        for model in models_ready:
                            batch_job_id = await workflow.execute_activity(
                                create_batch_job,
                                args=[input.provider, model],
                                start_to_close_timeout=timedelta(seconds=60),
                                retry_policy=retry_policy,
                            )

                            workflow.logger.info(
                                f"Created Bedrock batch job {batch_job_id} for model: {model}"
                            )

                            # Start child workflow for batch processing (non-blocking)
                            await workflow.start_child_workflow(
                                "BatchProcessingWorkflow",
                                BatchProcessingInput(
                                    batch_job_id=batch_job_id,
                                    provider=input.provider,
                                ),
                                id=f"batch-processing-{batch_job_id}",
                            )

                            workflow.logger.info(
                                f"Started batch processing workflow for batch {batch_job_id}"
                            )
                    else:
                        # Anthropic: Single batch for all models (each request has its own model)
                        workflow.logger.info(
                            f"Creating batch for {input.provider}: "
                            f"{pending_result['pending_count']} pending requests"
                        )

                        batch_job_id = await workflow.execute_activity(
                            create_batch_job,
                            args=[input.provider, None],
                            start_to_close_timeout=timedelta(seconds=60),
                            retry_policy=retry_policy,
                        )

                        workflow.logger.info(f"Created batch job: {batch_job_id}")

                        # Start child workflow for batch processing (non-blocking)
                        await workflow.start_child_workflow(
                            "BatchProcessingWorkflow",
                            BatchProcessingInput(
                                batch_job_id=batch_job_id,
                                provider=input.provider,
                            ),
                            id=f"batch-processing-{batch_job_id}",
                        )

                        workflow.logger.info(
                            f"Started batch processing workflow for batch {batch_job_id}"
                        )

            except Exception as e:
                workflow.logger.error(f"Error in batch scheduler for {input.provider}: {e}")
                # Continue running despite errors

            iteration_count += 1

            # Check if we need to continue-as-new to reset workflow history
            # This prevents hitting Temporal's history size limit (~50K events)
            if iteration_count >= MAX_ITERATIONS_BEFORE_CONTINUE_AS_NEW:
                workflow.logger.info(
                    f"Reached {iteration_count} iterations for {input.provider}, "
                    f"continuing as new workflow to reset history"
                )
                workflow.continue_as_new(
                    BatchSchedulerInput(
                        provider=input.provider,
                        check_interval_seconds=input.check_interval_seconds,
                        total_iterations=input.total_iterations + iteration_count,
                    )
                )

            # Wait before next check
            await workflow.sleep(timedelta(seconds=input.check_interval_seconds))
