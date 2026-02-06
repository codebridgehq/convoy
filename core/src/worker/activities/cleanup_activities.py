"""Result cleanup activities for Temporal workflows."""

import logging
from datetime import datetime, timezone

from sqlalchemy import delete, select
from temporalio import activity

from src.database import (
    CallbackDelivery,
    CargoResult,
    get_async_session,
)
from src.worker.config import CleanupConfig

logger = logging.getLogger(__name__)


@activity.defn
async def find_expired_results() -> list[str]:
    """Find cargo request IDs with expired results.

    Returns:
        List of cargo_request_id strings for expired results.
    """
    config = CleanupConfig()
    expired_ids = []

    async for session in get_async_session():
        now = datetime.now(timezone.utc)

        # Find expired results
        stmt = (
            select(CargoResult.cargo_request_id)
            .where(CargoResult.expires_at < now)
            .limit(config.deletion_batch_size)
        )
        result = await session.execute(stmt)
        expired_ids = [str(row[0]) for row in result.fetchall()]

        logger.info(f"Found {len(expired_ids)} expired results to clean up")

        return expired_ids


@activity.defn
async def delete_expired_results(cargo_request_ids: list[str]) -> int:
    """Delete expired results and their associated callback deliveries.

    Args:
        cargo_request_ids: List of cargo request IDs to delete results for.

    Returns:
        Number of results deleted.
    """
    from uuid import UUID

    if not cargo_request_ids:
        return 0

    request_uuids = [UUID(id_str) for id_str in cargo_request_ids]

    async for session in get_async_session():
        # Delete callback deliveries first (foreign key constraint)
        delete_callbacks_stmt = delete(CallbackDelivery).where(
            CallbackDelivery.cargo_request_id.in_(request_uuids)
        )
        await session.execute(delete_callbacks_stmt)

        # Delete cargo results
        delete_results_stmt = delete(CargoResult).where(
            CargoResult.cargo_request_id.in_(request_uuids)
        )
        result = await session.execute(delete_results_stmt)
        deleted_count = result.rowcount

        await session.commit()

        logger.info(f"Deleted {deleted_count} expired results and their callback deliveries")

        return deleted_count
