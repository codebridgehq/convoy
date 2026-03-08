"""FastAPI dependencies for API key authentication."""

from datetime import datetime, timezone
from uuid import UUID

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database import get_async_session, APIKey, Project
from src.auth.key_generator import hash_api_key, validate_key_format

# Define the API key header
api_key_header = APIKeyHeader(
    name="X-API-Key",
    auto_error=False,
    description="API key for authentication. Format: convoy_sk_xxxxx",
)


class AuthenticatedProject:
    """Container for authenticated project context."""

    def __init__(self, project: Project, api_key: APIKey):
        """
        Initialize authenticated project context.
        
        Args:
            project: The authenticated project
            api_key: The API key used for authentication
        """
        self.project = project
        self.api_key = api_key
        self.project_id: UUID = project.id
        self.project_slug: str = project.slug


async def get_current_project(
    api_key: str | None = Security(api_key_header),
    session: AsyncSession = Depends(get_async_session),
) -> AuthenticatedProject:
    """
    Validate API key and return the authenticated project.
    
    This is the main authentication dependency for protected routes.
    
    Args:
        api_key: The API key from the X-API-Key header
        session: Database session
        
    Returns:
        AuthenticatedProject containing the project and API key
        
    Raises:
        HTTPException: 401 if key is missing, invalid format, or not found
        HTTPException: 403 if project is inactive
    """
    if api_key is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required. Include X-API-Key header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Validate format
    if not validate_key_format(api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key format.",
        )

    # Hash and lookup
    key_hash = hash_api_key(api_key)

    result = await session.execute(
        select(APIKey, Project)
        .join(Project, APIKey.project_id == Project.id)
        .where(APIKey.key_hash == key_hash)
        .where(APIKey.is_active == True)  # noqa: E712
    )
    row = result.first()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key.",
        )

    api_key_obj, project = row

    # Check if key is expired
    if api_key_obj.expires_at and api_key_obj.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key has expired.",
        )

    # Check if project is active
    if not project.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Project is inactive.",
        )

    # Update last_used_at
    api_key_obj.last_used_at = datetime.now(timezone.utc)

    return AuthenticatedProject(project=project, api_key=api_key_obj)


async def get_optional_project(
    api_key: str | None = Security(api_key_header),
    session: AsyncSession = Depends(get_async_session),
) -> AuthenticatedProject | None:
    """
    Return authenticated project if key provided, None otherwise.
    
    Use this for routes that should work with or without authentication.
    
    Args:
        api_key: The API key from the X-API-Key header (optional)
        session: Database session
        
    Returns:
        AuthenticatedProject if valid key provided, None otherwise
    """
    if api_key is None:
        return None
    return await get_current_project(api_key, session)
