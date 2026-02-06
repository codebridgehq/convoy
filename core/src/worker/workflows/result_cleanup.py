"""Result cleanup workflow for removing expired data."""

from datetime import timedelta

from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from src.worker.activities.cleanup_activities import (
        delete_expired_results,
        find_expired_results,
    )


@workflow.defn
class ResultCleanupWorkflow:
    """Workflow for cleaning up expired results.

    This workflow finds and deletes expired cargo results and their
    associated callback deliveries. It should be scheduled to run daily.
    """

    @workflow.run
    async def run(self) -> int:
        """Run the cleanup workflow.

        Returns:
            Total number of results deleted.
        """
        workflow.logger.info("Starting result cleanup workflow")

        retry_policy = RetryPolicy(
            initial_interval=timedelta(seconds=1),
            backoff_coefficient=2.0,
            maximum_interval=timedelta(minutes=5),
            maximum_attempts=3,
        )

        total_deleted = 0

        # Process in batches until no more expired results
        while True:
            # Find expired results
            expired_ids = await workflow.execute_activity(
                find_expired_results,
                start_to_close_timeout=timedelta(seconds=30),
                retry_policy=retry_policy,
            )

            if not expired_ids:
                workflow.logger.info("No more expired results to clean up")
                break

            workflow.logger.info(f"Found {len(expired_ids)} expired results to delete")

            # Delete the expired results
            deleted_count = await workflow.execute_activity(
                delete_expired_results,
                expired_ids,
                start_to_close_timeout=timedelta(minutes=5),
                retry_policy=retry_policy,
            )

            total_deleted += deleted_count
            workflow.logger.info(
                f"Deleted {deleted_count} results (total: {total_deleted})"
            )

        workflow.logger.info(f"Cleanup complete. Total deleted: {total_deleted}")
        return total_deleted
