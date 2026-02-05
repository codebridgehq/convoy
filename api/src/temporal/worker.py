"""Temporal worker entry point for Convoy.

This module runs the Temporal worker that executes workflows and activities.
Run with: python -m src.temporal.worker
"""

import asyncio
import logging
import signal
import sys

from temporalio.worker import Worker

from src.temporal.activities import (
    check_pending_requests,
    create_batch_job,
    delete_expired_results,
    deliver_callback,
    find_expired_results,
    mark_callback_failed,
    poll_batch_status,
    process_batch_results,
    submit_batch_to_provider,
    update_callback_status,
)
from src.temporal.activities.callback_activities import (
    get_callback_payload,
    get_cargo_callback_url,
)
from src.temporal.client import get_temporal_client
from src.temporal.config import TemporalConfig
from src.temporal.workflows import (
    BatchSchedulerWorkflow,
    CallbackDeliveryWorkflow,
    ResultCleanupWorkflow,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


async def run_worker() -> None:
    """Run the Temporal worker."""
    config = TemporalConfig()

    logger.info(f"Starting Temporal worker (task queue: {config.task_queue})")

    # Get Temporal client
    client = await get_temporal_client(config)

    # Create worker with all workflows and activities
    worker = Worker(
        client,
        task_queue=config.task_queue,
        workflows=[
            BatchSchedulerWorkflow,
            CallbackDeliveryWorkflow,
            ResultCleanupWorkflow,
        ],
        activities=[
            # Batch activities
            check_pending_requests,
            create_batch_job,
            submit_batch_to_provider,
            poll_batch_status,
            process_batch_results,
            # Callback activities
            deliver_callback,
            update_callback_status,
            mark_callback_failed,
            get_callback_payload,
            get_cargo_callback_url,
            # Cleanup activities
            find_expired_results,
            delete_expired_results,
        ],
    )

    logger.info("Worker started, waiting for tasks...")

    # Run the worker
    await worker.run()


def main() -> None:
    """Main entry point for the worker."""
    # Handle shutdown signals gracefully
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    shutdown_event = asyncio.Event()

    def signal_handler(sig: int, frame) -> None:
        logger.info(f"Received signal {sig}, shutting down...")
        shutdown_event.set()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        loop.run_until_complete(run_worker())
    except KeyboardInterrupt:
        logger.info("Worker interrupted")
    except Exception as e:
        logger.error(f"Worker error: {e}")
        sys.exit(1)
    finally:
        loop.close()
        logger.info("Worker stopped")


if __name__ == "__main__":
    main()
