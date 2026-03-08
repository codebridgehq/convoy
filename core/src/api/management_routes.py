"""Management routes for project and API key administration."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth import require_admin
from src.auth.key_generator import generate_api_key
from src.database import get_async_session, Project, APIKey
from src.api.models import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectListResponse,
    APIKeyCreate,
    APIKeyResponse,
    APIKeyCreatedResponse,
    APIKeyListResponse,
)


management_router = APIRouter(
    prefix="/admin",
    tags=["Project Management"],
    dependencies=[Depends(require_admin)],
)


# ============ Project Endpoints ============


@management_router.post(
    "/projects",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project",
    description="Create a new project. Requires admin authentication.",
)
async def create_project(
    request: ProjectCreate,
    session: AsyncSession = Depends(get_async_session),
):
    """Create a new project."""
    # Check if slug already exists
    existing = await session.execute(
        select(Project).where(Project.slug == request.slug)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Project with slug '{request.slug}' already exists",
        )

    project = Project(
        name=request.name,
        slug=request.slug,
        description=request.description,
    )
    session.add(project)
    await session.flush()

    return ProjectResponse(
        id=str(project.id),
        name=project.name,
        slug=project.slug,
        description=project.description,
        is_active=project.is_active,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@management_router.get(
    "/projects",
    response_model=ProjectListResponse,
    summary="List all projects",
    description="List all projects with pagination. Requires admin authentication.",
)
async def list_projects(
    skip: int = 0,
    limit: int = 100,
    session: AsyncSession = Depends(get_async_session),
):
    """List all projects with pagination."""
    # Get total count
    total_result = await session.execute(select(func.count(Project.id)))
    total = total_result.scalar()

    # Get projects
    result = await session.execute(
        select(Project)
        .order_by(Project.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    projects = result.scalars().all()

    return ProjectListResponse(
        projects=[
            ProjectResponse(
                id=str(p.id),
                name=p.name,
                slug=p.slug,
                description=p.description,
                is_active=p.is_active,
                created_at=p.created_at,
                updated_at=p.updated_at,
            )
            for p in projects
        ],
        total=total,
    )


@management_router.get(
    "/projects/{project_slug}",
    response_model=ProjectResponse,
    summary="Get project by slug",
    description="Get a project by its slug. Requires admin authentication.",
)
async def get_project(
    project_slug: str,
    session: AsyncSession = Depends(get_async_session),
):
    """Get a project by its slug."""
    result = await session.execute(
        select(Project).where(Project.slug == project_slug)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_slug}' not found",
        )

    return ProjectResponse(
        id=str(project.id),
        name=project.name,
        slug=project.slug,
        description=project.description,
        is_active=project.is_active,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


@management_router.patch(
    "/projects/{project_slug}",
    response_model=ProjectResponse,
    summary="Update a project",
    description="Update a project's details. Requires admin authentication.",
)
async def update_project(
    project_slug: str,
    request: ProjectUpdate,
    session: AsyncSession = Depends(get_async_session),
):
    """Update a project's details."""
    result = await session.execute(
        select(Project).where(Project.slug == project_slug)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_slug}' not found",
        )

    if request.name is not None:
        project.name = request.name
    if request.description is not None:
        project.description = request.description
    if request.is_active is not None:
        project.is_active = request.is_active

    await session.flush()
    await session.refresh(project)

    return ProjectResponse(
        id=str(project.id),
        name=project.name,
        slug=project.slug,
        description=project.description,
        is_active=project.is_active,
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


# ============ API Key Endpoints ============


@management_router.post(
    "/projects/{project_slug}/api-keys",
    response_model=APIKeyCreatedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new API key for a project",
    description="""
Create a new API key for a project. Requires admin authentication.

⚠️ **IMPORTANT**: The full API key is only returned once at creation time.
Save it securely - it cannot be retrieved again!
""",
)
async def create_api_key(
    project_slug: str,
    request: APIKeyCreate,
    session: AsyncSession = Depends(get_async_session),
):
    """Create a new API key for a project."""
    # Get project
    result = await session.execute(
        select(Project).where(Project.slug == project_slug)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_slug}' not found",
        )

    # Generate key
    full_key, key_prefix, key_hash = generate_api_key()

    api_key = APIKey(
        project_id=project.id,
        name=request.name,
        key_prefix=key_prefix,
        key_hash=key_hash,
        expires_at=request.expires_at,
    )
    session.add(api_key)
    await session.flush()

    return APIKeyCreatedResponse(
        id=str(api_key.id),
        name=api_key.name,
        key=full_key,  # Only time the full key is returned!
        key_prefix=api_key.key_prefix,
        expires_at=api_key.expires_at,
        created_at=api_key.created_at,
    )


@management_router.get(
    "/projects/{project_slug}/api-keys",
    response_model=APIKeyListResponse,
    summary="List API keys for a project",
    description="List all API keys for a project (without the actual keys). Requires admin authentication.",
)
async def list_api_keys(
    project_slug: str,
    session: AsyncSession = Depends(get_async_session),
):
    """List all API keys for a project (without the actual keys)."""
    # Get project
    result = await session.execute(
        select(Project).where(Project.slug == project_slug)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project '{project_slug}' not found",
        )

    # Get API keys
    result = await session.execute(
        select(APIKey)
        .where(APIKey.project_id == project.id)
        .order_by(APIKey.created_at.desc())
    )
    api_keys = result.scalars().all()

    return APIKeyListResponse(
        api_keys=[
            APIKeyResponse(
                id=str(k.id),
                name=k.name,
                key_prefix=k.key_prefix,
                is_active=k.is_active,
                last_used_at=k.last_used_at,
                expires_at=k.expires_at,
                created_at=k.created_at,
            )
            for k in api_keys
        ],
        total=len(api_keys),
    )


@management_router.delete(
    "/projects/{project_slug}/api-keys/{key_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke an API key",
    description="Revoke (deactivate) an API key. Requires admin authentication.",
)
async def revoke_api_key(
    project_slug: str,
    key_id: str,
    session: AsyncSession = Depends(get_async_session),
):
    """Revoke (deactivate) an API key."""
    result = await session.execute(
        select(APIKey)
        .join(Project)
        .where(Project.slug == project_slug)
        .where(APIKey.id == key_id)
    )
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API key not found",
        )

    api_key.is_active = False
    await session.flush()
