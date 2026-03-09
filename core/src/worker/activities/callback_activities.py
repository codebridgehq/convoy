"""Callback delivery activities for Temporal workflows."""

import logging
import ssl
from datetime import datetime, timezone

import httpx
from sqlalchemy import select, update
from temporalio import activity
from temporalio.exceptions import ApplicationError

from src.database import (
    CallbackDelivery,
    CallbackStatus,
    CargoRequest,
    CargoResult,
    CargoStatus,
    get_async_session,
)
from src.worker.config import CallbackConfig

logger = logging.getLogger(__name__)


@activity.defn
async def deliver_callback(
    cargo_request_id: str,
    callback_url: str,
    payload: dict,
) -> bool:
    """Deliver a result to the callback URL via HTTP POST.

    Args:
        cargo_request_id: The cargo request ID.
        callback_url: The URL to deliver the callback to.
        payload: The payload to send.

    Returns:
        True if delivery was successful.

    Raises:
        ApplicationError: On HTTP error (triggers Temporal retry).
    """
    config = CallbackConfig()

    logger.info(f"Delivering callback for cargo request {cargo_request_id} to {callback_url}")

    try:
        # Use system SSL certificates instead of certifi to ensure broader CA coverage
        ssl_context = ssl.create_default_context()
        async with httpx.AsyncClient(
            timeout=config.http_timeout_seconds,
            verify=ssl_context,
        ) as client:
            response = await client.post(
                callback_url,
                json=payload,
                headers={
                    "Content-Type": "application/json",
                    "X-Convoy-Cargo-Id": cargo_request_id,
                },
            )

            # Update callback delivery record with attempt info
            await _update_attempt(
                cargo_request_id,
                http_status_code=response.status_code,
                error_message=None if response.is_success else response.text[:500],
            )

            if response.is_success:
                logger.info(
                    f"Callback delivered successfully for {cargo_request_id} "
                    f"(status: {response.status_code})"
                )
                return True

            # Non-success status code - raise error to trigger retry
            error_msg = f"Callback failed with status {response.status_code}: {response.text[:200]}"
            logger.warning(error_msg)
            raise ApplicationError(
                error_msg,
                non_retryable=response.status_code in (400, 401, 403, 404, 405),
            )

    except httpx.TimeoutException as e:
        await _update_attempt(cargo_request_id, error_message=f"Timeout: {str(e)}")
        logger.warning(f"Callback timeout for {cargo_request_id}: {e}")
        raise ApplicationError(f"Callback timeout: {e}", non_retryable=False) from e

    except httpx.RequestError as e:
        await _update_attempt(cargo_request_id, error_message=f"Request error: {str(e)}")
        logger.warning(f"Callback request error for {cargo_request_id}: {e}")
        raise ApplicationError(f"Callback request error: {e}", non_retryable=False) from e


async def _update_attempt(
    cargo_request_id: str,
    http_status_code: int | None = None,
    error_message: str | None = None,
) -> None:
    """Update the callback delivery record with attempt information."""
    from uuid import UUID

    request_uuid = UUID(cargo_request_id)

    async for session in get_async_session():
        stmt = select(CallbackDelivery).where(
            CallbackDelivery.cargo_request_id == request_uuid
        )
        result = await session.execute(stmt)
        delivery = result.scalar_one_or_none()

        if delivery:
            delivery.attempt_count += 1
            delivery.last_attempt_at = datetime.now(timezone.utc)
            delivery.http_status_code = http_status_code
            delivery.error_message = error_message
            delivery.status = CallbackStatus.RETRYING
            await session.commit()


@activity.defn
async def update_callback_status(
    cargo_request_id: str,
    status: str,
    http_status_code: int | None = None,
    error_message: str | None = None,
) -> None:
    """Update the callback delivery status.

    Args:
        cargo_request_id: The cargo request ID.
        status: The new status (delivered, failed, etc.).
        http_status_code: Optional HTTP status code from last attempt.
        error_message: Optional error message.
    """
    from uuid import UUID

    request_uuid = UUID(cargo_request_id)
    callback_status = CallbackStatus(status)

    async for session in get_async_session():
        # Update callback delivery
        delivery_stmt = select(CallbackDelivery).where(
            CallbackDelivery.cargo_request_id == request_uuid
        )
        result = await session.execute(delivery_stmt)
        delivery = result.scalar_one_or_none()

        if delivery:
            delivery.status = callback_status
            if http_status_code:
                delivery.http_status_code = http_status_code
            if error_message:
                delivery.error_message = error_message
            if callback_status == CallbackStatus.DELIVERED:
                delivery.completed_at = datetime.now(timezone.utc)

        # Update cargo request status
        if callback_status == CallbackStatus.DELIVERED:
            cargo_status = CargoStatus.CALLBACK_DELIVERED
        elif callback_status == CallbackStatus.FAILED:
            cargo_status = CargoStatus.CALLBACK_FAILED
        else:
            cargo_status = None

        if cargo_status:
            cargo_stmt = (
                update(CargoRequest)
                .where(CargoRequest.id == request_uuid)
                .values(status=cargo_status)
            )
            await session.execute(cargo_stmt)

        await session.commit()

        logger.info(f"Updated callback status for {cargo_request_id} to {status}")


@activity.defn
async def mark_callback_failed(cargo_request_id: str) -> None:
    """Mark a callback as permanently failed after all retries exhausted.

    Args:
        cargo_request_id: The cargo request ID.
    """
    await update_callback_status(
        cargo_request_id,
        status=CallbackStatus.FAILED.value,
        error_message="All retry attempts exhausted",
    )
    logger.warning(f"Callback marked as failed for {cargo_request_id} after all retries")


@activity.defn
async def get_callback_payload(cargo_request_id: str) -> dict:
    """Get the callback payload for a cargo request.

    Args:
        cargo_request_id: The cargo request ID.

    Returns:
        Dictionary containing the callback payload.
    """
    from uuid import UUID

    request_uuid = UUID(cargo_request_id)

    async for session in get_async_session():
        # Get cargo request with result
        stmt = select(CargoRequest).where(CargoRequest.id == request_uuid)
        result = await session.execute(stmt)
        cargo_request = result.scalar_one_or_none()

        if not cargo_request:
            raise ApplicationError(
                f"Cargo request not found: {cargo_request_id}",
                non_retryable=True,
            )

        # Get the result
        result_stmt = select(CargoResult).where(
            CargoResult.cargo_request_id == request_uuid
        )
        result = await session.execute(result_stmt)
        cargo_result = result.scalar_one_or_none()

        if not cargo_result:
            raise ApplicationError(
                f"Cargo result not found for request: {cargo_request_id}",
                non_retryable=True,
            )

        return {
            "cargo_id": cargo_request.cargo_id,
            "success": cargo_result.success,
            "response": cargo_result.response,
            "error_message": cargo_result.error_message,
            "created_at": cargo_result.created_at.isoformat(),
        }


@activity.defn
async def get_cargo_callback_url(cargo_request_id: str) -> str:
    """Get the callback URL for a cargo request.

    Args:
        cargo_request_id: The cargo request ID.

    Returns:
        The callback URL.
    """
    from uuid import UUID

    request_uuid = UUID(cargo_request_id)

    async for session in get_async_session():
        stmt = select(CargoRequest.callback_url).where(CargoRequest.id == request_uuid)
        result = await session.execute(stmt)
        callback_url = result.scalar_one_or_none()

        if not callback_url:
            raise ApplicationError(
                f"Cargo request not found: {cargo_request_id}",
                non_retryable=True,
            )

        return callback_url
