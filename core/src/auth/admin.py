"""Admin authentication for management endpoints."""

import os
import secrets

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

# Define the admin API key header
admin_key_header = APIKeyHeader(
    name="X-Admin-Key",
    auto_error=False,
    description="Admin API key for management endpoints",
)


async def require_admin(
    admin_key: str | None = Security(admin_key_header),
) -> None:
    """
    Verify admin API key for management endpoints.
    
    This dependency should be used on all management routes
    (project creation, API key management, etc.).
    
    Args:
        admin_key: The admin API key from the X-Admin-Key header
        
    Raises:
        HTTPException: 500 if admin auth not configured
        HTTPException: 401 if key is missing or invalid
    """
    expected_key = os.getenv("ADMIN_API_KEY")

    if not expected_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Admin authentication not configured. Set ADMIN_API_KEY environment variable.",
        )

    if admin_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin API key required. Include X-Admin-Key header.",
            headers={"WWW-Authenticate": "AdminApiKey"},
        )

    # Use constant-time comparison to prevent timing attacks
    if not secrets.compare_digest(admin_key, expected_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin API key.",
        )
