"""Pydantic models for the batch processor module."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class BatchProvider(str, Enum):
    """Supported batch processing providers."""

    BEDROCK = "bedrock"
    ANTHROPIC = "anthropic"


class BatchJobStatus(str, Enum):
    """Status of a batch job."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class BatchRequest(BaseModel):
    """A single request within a batch."""

    custom_id: str = Field(..., description="Unique identifier for this request")
    model: str = Field(..., description="Model identifier to use for this request")
    messages: list[dict[str, Any]] = Field(..., description="Message payload for the request")
    max_tokens: int = Field(default=1024, description="Maximum tokens for the response")
    metadata: dict[str, Any] | None = Field(default=None, description="Additional metadata")
    system: str | None = Field(default=None, description="System prompt for the request")
    temperature: float | None = Field(default=None, ge=0.0, le=1.0, description="Sampling temperature")
    top_p: float | None = Field(default=None, ge=0.0, le=1.0, description="Top-p sampling parameter")


class BatchJob(BaseModel):
    """Represents a batch processing job."""

    job_id: str = Field(..., description="Provider-specific job identifier")
    provider: BatchProvider = Field(..., description="Provider handling this job")
    status: BatchJobStatus = Field(..., description="Current status of the job")
    created_at: datetime = Field(..., description="When the job was created")
    completed_at: datetime | None = Field(default=None, description="When the job completed")
    request_count: int = Field(default=0, description="Number of requests in the batch")
    metadata: dict[str, Any] | None = Field(default=None, description="Additional job metadata")
    error_message: str | None = Field(default=None, description="Error message if job failed")


class BatchResult(BaseModel):
    """Result of a single request within a batch."""

    custom_id: str = Field(..., description="Original request identifier")
    success: bool = Field(..., description="Whether the request succeeded")
    response: dict[str, Any] | None = Field(default=None, description="Response data if successful")
    error: str | None = Field(default=None, description="Error message if failed")
