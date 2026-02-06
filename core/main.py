"""Convoy API - Simplified batch processing."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.routes import router
from src.temporal.client import get_temporal_client
from src.temporal.config import BatchConfig, TemporalConfig
from src.temporal.workflows import BatchSchedulerInput, BatchSchedulerWorkflow

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown events."""
    # Startup: Start batch scheduler workflows
    temporal_config = TemporalConfig()

    try:
        client = await get_temporal_client()

        # Start batch scheduler workflows for each provider
        for provider in ["bedrock", "anthropic"]:
            workflow_id = f"batch-scheduler-{provider}"
            try:
                # Create input with config values read at startup
                workflow_input = BatchSchedulerInput(
                    provider=provider,
                    check_interval_seconds=BatchConfig.check_interval_seconds,
                )

                await client.start_workflow(
                    BatchSchedulerWorkflow.run,
                    workflow_input,
                    id=workflow_id,
                    task_queue=temporal_config.task_queue,
                )
                logger.info(f"Started batch scheduler workflow: {workflow_id}")
            except Exception as e:
                # Workflow may already be running (which is fine)
                if "already started" in str(e).lower() or "already exists" in str(e).lower():
                    logger.info(f"Batch scheduler workflow already running: {workflow_id}")
                else:
                    logger.warning(f"Could not start batch scheduler workflow {workflow_id}: {e}")

        logger.info("Temporal workflows initialized")

    except Exception as e:
        logger.error(f"Failed to initialize Temporal workflows: {e}")
        # Don't fail startup - the worker may not be running yet
        # Workflows will be started when the worker comes up

    yield

    # Shutdown: Nothing to clean up (workflows continue running)
    logger.info("Application shutting down")


app = FastAPI(
    title="🚂 Convoy API",
    description="Simplified batch processing",
    lifespan=lifespan,
)

app.include_router(router)
