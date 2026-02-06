"""Mock callback server for E2E batch flow testing.

This module provides a simple FastAPI server that receives callbacks
from the Convoy batch processing system and stores them for verification.
"""

import asyncio
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

import uvicorn
from fastapi import FastAPI, Request

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class CallbackRecord:
    """Record of a received callback."""

    cargo_id: str
    payload: dict[str, Any]
    received_at: datetime
    headers: dict[str, str]


@dataclass
class CallbackStore:
    """Thread-safe store for received callbacks."""

    callbacks: dict[str, CallbackRecord] = field(default_factory=dict)
    _lock: asyncio.Lock = field(default_factory=asyncio.Lock)

    async def add(self, cargo_id: str, payload: dict, headers: dict) -> None:
        """Add a callback record."""
        async with self._lock:
            self.callbacks[cargo_id] = CallbackRecord(
                cargo_id=cargo_id,
                payload=payload,
                received_at=datetime.now(timezone.utc),
                headers=headers,
            )
            logger.info(f"Stored callback for cargo_id: {cargo_id}")

    async def get(self, cargo_id: str) -> CallbackRecord | None:
        """Get a callback record by cargo_id."""
        async with self._lock:
            return self.callbacks.get(cargo_id)

    async def get_all(self) -> dict[str, CallbackRecord]:
        """Get all callback records."""
        async with self._lock:
            return dict(self.callbacks)

    async def count(self) -> int:
        """Get the number of received callbacks."""
        async with self._lock:
            return len(self.callbacks)

    async def clear(self) -> None:
        """Clear all stored callbacks."""
        async with self._lock:
            self.callbacks.clear()
            logger.info("Cleared all stored callbacks")

    async def wait_for_callbacks(
        self,
        expected_count: int,
        timeout_seconds: float = 600,
        poll_interval: float = 5.0,
    ) -> bool:
        """Wait until expected number of callbacks are received.

        Args:
            expected_count: Number of callbacks to wait for.
            timeout_seconds: Maximum time to wait (default 10 minutes).
            poll_interval: How often to check (default 5 seconds).

        Returns:
            True if all callbacks received, False if timeout.
        """
        start_time = asyncio.get_event_loop().time()
        while True:
            current_count = await self.count()
            if current_count >= expected_count:
                logger.info(f"Received all {expected_count} callbacks")
                return True

            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed >= timeout_seconds:
                logger.warning(
                    f"Timeout waiting for callbacks: {current_count}/{expected_count}"
                )
                return False

            logger.info(
                f"Waiting for callbacks: {current_count}/{expected_count} "
                f"(elapsed: {elapsed:.1f}s)"
            )
            await asyncio.sleep(poll_interval)


# Global callback store
callback_store = CallbackStore()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler."""
    logger.info("Mock callback server starting...")
    yield
    logger.info("Mock callback server shutting down...")


app = FastAPI(
    title="Mock Callback Server",
    description="Receives callbacks from Convoy batch processing",
    lifespan=lifespan,
)


@app.post("/callback")
async def receive_callback(request: Request) -> dict:
    """Receive a callback from Convoy.

    The callback payload should contain:
    - cargo_id: The unique identifier for the cargo request
    - success: Whether processing was successful
    - response: The LLM response (if successful)
    - error: Error message (if failed)
    """
    payload = await request.json()
    headers = dict(request.headers)

    # Extract cargo_id from payload
    cargo_id = payload.get("cargo_id", "unknown")

    await callback_store.add(cargo_id, payload, headers)

    logger.info(f"Received callback for {cargo_id}: success={payload.get('success')}")

    return {"status": "received", "cargo_id": cargo_id}


@app.get("/callbacks")
async def list_callbacks() -> dict:
    """List all received callbacks."""
    callbacks = await callback_store.get_all()
    return {
        "count": len(callbacks),
        "callbacks": {
            cargo_id: {
                "cargo_id": record.cargo_id,
                "success": record.payload.get("success"),
                "received_at": record.received_at.isoformat(),
            }
            for cargo_id, record in callbacks.items()
        },
    }


@app.get("/callbacks/{cargo_id}")
async def get_callback(cargo_id: str) -> dict:
    """Get a specific callback by cargo_id."""
    record = await callback_store.get(cargo_id)
    if record is None:
        return {"error": "Callback not found", "cargo_id": cargo_id}
    return {
        "cargo_id": record.cargo_id,
        "payload": record.payload,
        "received_at": record.received_at.isoformat(),
    }


@app.get("/callbacks/count")
async def get_callback_count() -> dict:
    """Get the count of received callbacks."""
    count = await callback_store.count()
    return {"count": count}


@app.delete("/callbacks")
async def clear_callbacks() -> dict:
    """Clear all stored callbacks."""
    await callback_store.clear()
    return {"status": "cleared"}


@app.get("/health")
async def health_check() -> dict:
    """Health check endpoint."""
    return {"status": "ok"}


def run_server(host: str = "0.0.0.0", port: int = 8001) -> None:
    """Run the mock callback server."""
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    run_server()
