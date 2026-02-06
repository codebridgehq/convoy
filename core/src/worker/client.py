"""Temporal client configuration and connection management."""

import logging

from temporalio.client import Client

from .config import TemporalConfig

logger = logging.getLogger(__name__)

_client: Client | None = None


async def get_temporal_client(config: TemporalConfig | None = None) -> Client:
    """Get or create a connected Temporal client.

    Args:
        config: Optional Temporal configuration. Uses defaults if not provided.

    Returns:
        Connected Temporal client instance.
    """
    global _client

    if _client is not None:
        return _client

    if config is None:
        config = TemporalConfig()

    logger.info(f"Connecting to Temporal server at {config.address}")

    _client = await Client.connect(
        config.address,
        namespace=config.namespace,
    )

    logger.info(f"Connected to Temporal server (namespace: {config.namespace})")
    return _client


async def close_temporal_client() -> None:
    """Close the Temporal client connection."""
    global _client

    if _client is not None:
        logger.info("Closing Temporal client connection")
        await _client.close()
        _client = None
