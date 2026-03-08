from datetime import datetime
from typing import Optional, Union

from pydantic import BaseModel, Field

class CacheControl(BaseModel):
    """Cache control settings for content blocks."""
    type: str = Field(default="ephemeral", description="Cache control type (e.g., 'ephemeral')")


class TextContentBlock(BaseModel):
    """Text content block for system or user messages."""
    type: str = Field(default="text", description="Content block type")
    text: str = Field(..., description="The text content")
    cache_control: Optional[CacheControl] = Field(default=None, description="Optional cache control settings")


class Message(BaseModel):
    """A message in the conversation."""
    role: str = Field(..., description="The role of the message sender (e.g., 'user', 'assistant')")
    content: Union[str, list[TextContentBlock]] = Field(..., description="The message content - can be a string or list of content blocks")


class BatchParams(BaseModel):
    """Parameters for batch processing, compatible with AWS Bedrock and Anthropic batch APIs."""
    model: str = Field(..., description="The model to use (e.g., 'claude-sonnet-4-5', 'claude-3-haiku-20240307')")
    max_tokens: int = Field(default=1024, description="Maximum number of tokens to generate")
    system: Optional[Union[str, list[TextContentBlock]]] = Field(
        default=None,
        description="System prompt - can be a string or list of content blocks with optional cache control"
    )
    messages: list[Message] = Field(..., description="List of messages in the conversation")
    temperature: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Sampling temperature (0.0 to 1.0)")
    top_p: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Top-p sampling parameter")
    top_k: Optional[int] = Field(default=None, ge=0, description="Top-k sampling parameter")
    stop_sequences: Optional[list[str]] = Field(default=None, description="List of sequences that will stop generation")


class CargoLoadRequest(BaseModel):
    """Request model for loading a prompt into the batch processing queue.
    
    Compatible with AWS Bedrock batch processing and Anthropic batch API format.
    The custom_id is handled internally by the convoy app.
    """
    params: BatchParams = Field(..., description="Batch processing parameters including model, messages, and optional settings")
    callback_url: str = Field(..., description="URL to receive notification when processing is complete")
    
class CargoLoadResponse(BaseModel):
    """Response model for the cargo load operation."""
    cargo_id: str = Field(..., description="Unique identifier for the loaded cargo")
    status: str = Field(..., description="Status of the operation (e.g., 'success', 'error')")
    message: str = Field(..., description="Detailed message about the operation result")


class CargoTrackingResponse(BaseModel):
    """Response model for cargo tracking information."""
    cargo_id: str = Field(..., description="Unique identifier for the cargo")
    status: str = Field(..., description="Current status of the cargo (e.g., 'pending', 'processing', 'completed')")
    status_description: str = Field(..., description="Human-readable description of the current status")
    created_at: datetime = Field(..., description="Timestamp when cargo was created")
    updated_at: datetime = Field(..., description="Timestamp when cargo was last updated")


# ============ Project Management Models ============

class ProjectCreate(BaseModel):
    """Request model for creating a new project."""
    name: str = Field(..., min_length=1, max_length=255, description="Project name")
    slug: str = Field(
        ...,
        min_length=1,
        max_length=63,
        pattern=r"^[a-z0-9][a-z0-9-]*[a-z0-9]$|^[a-z0-9]$",
        description="URL-friendly identifier (lowercase, alphanumeric, hyphens, must start/end with alphanumeric)",
    )
    description: Optional[str] = Field(None, max_length=1000, description="Project description")


class ProjectUpdate(BaseModel):
    """Request model for updating a project."""
    name: Optional[str] = Field(None, min_length=1, max_length=255, description="Project name")
    description: Optional[str] = Field(None, max_length=1000, description="Project description")
    is_active: Optional[bool] = Field(None, description="Whether the project is active")


class ProjectResponse(BaseModel):
    """Response model for project details."""
    id: str = Field(..., description="Project UUID")
    name: str = Field(..., description="Project name")
    slug: str = Field(..., description="URL-friendly identifier")
    description: Optional[str] = Field(None, description="Project description")
    is_active: bool = Field(..., description="Whether the project is active")
    created_at: datetime = Field(..., description="Timestamp when project was created")
    updated_at: datetime = Field(..., description="Timestamp when project was last updated")


class ProjectListResponse(BaseModel):
    """Response model for listing projects."""
    projects: list[ProjectResponse] = Field(..., description="List of projects")
    total: int = Field(..., description="Total number of projects")


# ============ API Key Management Models ============

class APIKeyCreate(BaseModel):
    """Request model for creating a new API key."""
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Human-readable name for the key (e.g., 'Production', 'Development')",
    )
    expires_at: Optional[datetime] = Field(
        None,
        description="Optional expiration date for the key",
    )


class APIKeyResponse(BaseModel):
    """Response model for API key details (without the actual key)."""
    id: str = Field(..., description="API key UUID")
    name: str = Field(..., description="Human-readable name for the key")
    key_prefix: str = Field(..., description="First 12 characters for identification")
    is_active: bool = Field(..., description="Whether the key is active")
    last_used_at: Optional[datetime] = Field(None, description="Timestamp when key was last used")
    expires_at: Optional[datetime] = Field(None, description="Expiration date for the key")
    created_at: datetime = Field(..., description="Timestamp when key was created")


class APIKeyCreatedResponse(BaseModel):
    """Response model when a new API key is created (includes full key).
    
    ⚠️ IMPORTANT: The full API key is only returned once at creation time.
    Save it securely - it cannot be retrieved again!
    """
    id: str = Field(..., description="API key UUID")
    name: str = Field(..., description="Human-readable name for the key")
    key: str = Field(..., description="Full API key - SAVE THIS, it won't be shown again!")
    key_prefix: str = Field(..., description="First 12 characters for identification")
    expires_at: Optional[datetime] = Field(None, description="Expiration date for the key")
    created_at: datetime = Field(..., description="Timestamp when key was created")


class APIKeyListResponse(BaseModel):
    """Response model for listing API keys."""
    api_keys: list[APIKeyResponse] = Field(..., description="List of API keys")
    total: int = Field(..., description="Total number of API keys")
