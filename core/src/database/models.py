"""SQLAlchemy models for cargo request storage and batch processing."""

import enum
import uuid
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    pass


class Project(Base):
    """Represents a project/tenant in the system."""

    __tablename__ = "projects"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    slug: Mapped[str] = mapped_column(
        String(63),
        unique=True,
        nullable=False,
        index=True,
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    settings: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Project-specific settings (rate limits, allowed models, etc.)",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    api_keys: Mapped[list["APIKey"]] = relationship(
        "APIKey",
        back_populates="project",
        lazy="selectin",
    )
    cargo_requests: Mapped[list["CargoRequest"]] = relationship(
        "CargoRequest",
        back_populates="project",
        lazy="selectin",
    )

    __table_args__ = (
        Index("idx_projects_slug", "slug"),
        Index("idx_projects_is_active", "is_active"),
    )

    def __repr__(self) -> str:
        return f"<Project(slug={self.slug}, name={self.name})>"


class APIKey(Base):
    """Stores hashed API keys for project authentication."""

    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Human-readable name for the key (e.g., 'Production', 'Development')",
    )
    key_prefix: Mapped[str] = mapped_column(
        String(12),
        nullable=False,
        comment="First 12 chars of key for identification (e.g., 'convoy_sk_7k')",
    )
    key_hash: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
        index=True,
        comment="SHA-256 hash of the full API key",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Optional expiration date for the key",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    # Relationships
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="api_keys",
    )

    __table_args__ = (
        Index("idx_api_keys_project_id", "project_id"),
        Index("idx_api_keys_key_hash", "key_hash"),
        Index("idx_api_keys_active", "is_active", postgresql_where="is_active = true"),
    )

    def __repr__(self) -> str:
        return f"<APIKey(id={self.id}, name={self.name}, prefix={self.key_prefix})>"


class ProviderType(str, enum.Enum):
    """Supported batch processing providers."""

    BEDROCK = "bedrock"
    ANTHROPIC = "anthropic"


class CargoStatus(str, enum.Enum):
    """Status of a cargo request."""

    PENDING = "pending"
    BATCHED = "batched"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CALLBACK_PENDING = "callback_pending"
    CALLBACK_DELIVERED = "callback_delivered"
    CALLBACK_FAILED = "callback_failed"

    @property
    def description(self) -> str:
        """Return a human-readable description of the status."""
        return CARGO_STATUS_DESCRIPTIONS.get(self, "Unknown status")


# Human-readable descriptions for cargo statuses
CARGO_STATUS_DESCRIPTIONS: dict[CargoStatus, str] = {
    CargoStatus.PENDING: "Cargo is waiting to be assigned to a batch",
    CargoStatus.BATCHED: "Cargo has been assigned to a batch job",
    CargoStatus.PROCESSING: "Batch is being processed by the provider",
    CargoStatus.COMPLETED: "Processing completed successfully",
    CargoStatus.FAILED: "Processing failed",
    CargoStatus.CALLBACK_PENDING: "Result ready, callback delivery pending",
    CargoStatus.CALLBACK_DELIVERED: "Callback successfully delivered",
    CargoStatus.CALLBACK_FAILED: "Callback delivery failed",
}


class BatchStatus(str, enum.Enum):
    """Status of a batch job."""

    PENDING = "pending"
    READY = "ready"
    SUBMITTED = "submitted"
    PROCESSING = "processing"
    COMPLETED = "completed"
    PARTIALLY_COMPLETED = "partially_completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class CallbackStatus(str, enum.Enum):
    """Status of a callback delivery."""

    PENDING = "pending"
    RETRYING = "retrying"
    DELIVERED = "delivered"
    FAILED = "failed"
    MANUAL_RETRY = "manual_retry"


class BatchJob(Base):
    """Tracks batch jobs submitted to providers."""

    __tablename__ = "batch_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    provider: Mapped[ProviderType] = mapped_column(
        Enum(ProviderType, name="provider_type", create_constraint=True, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    provider_job_id: Mapped[str | None] = mapped_column(
        String(256),
        nullable=True,
    )
    status: Mapped[BatchStatus] = mapped_column(
        Enum(BatchStatus, name="batch_status", create_constraint=True, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=BatchStatus.PENDING,
    )
    request_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    metadata_: Mapped[dict | None] = mapped_column(
        "metadata",
        JSONB,
        nullable=True,
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    cargo_requests: Mapped[list["CargoRequest"]] = relationship(
        "CargoRequest",
        back_populates="batch_job",
        lazy="selectin",
    )

    __table_args__ = (
        Index("idx_batch_jobs_status", "status"),
        Index("idx_batch_jobs_provider_status", "provider", "status"),
        Index("idx_batch_jobs_provider_job_id", "provider_job_id"),
        Index("idx_batch_jobs_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<BatchJob(id={self.id}, provider={self.provider}, status={self.status})>"


class CargoRequest(Base):
    """Stores individual requests received from the /cargo/load endpoint."""

    __tablename__ = "cargo_requests"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    cargo_id: Mapped[str] = mapped_column(
        String(64),
        unique=True,
        nullable=False,
    )
    provider: Mapped[ProviderType] = mapped_column(
        Enum(ProviderType, name="provider_type", create_constraint=True, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    model: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
    )
    params: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )
    callback_url: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
    )
    status: Mapped[CargoStatus] = mapped_column(
        Enum(CargoStatus, name="cargo_status", create_constraint=True, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=CargoStatus.PENDING,
    )
    batch_job_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("batch_jobs.id"),
        nullable=True,
    )
    # Project association - required for all cargo requests
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Relationships
    batch_job: Mapped[BatchJob | None] = relationship(
        "BatchJob",
        back_populates="cargo_requests",
    )
    project: Mapped["Project"] = relationship(
        "Project",
        back_populates="cargo_requests",
    )
    result: Mapped["CargoResult | None"] = relationship(
        "CargoResult",
        back_populates="cargo_request",
        uselist=False,
        lazy="selectin",
    )
    callback_delivery: Mapped["CallbackDelivery | None"] = relationship(
        "CallbackDelivery",
        back_populates="cargo_request",
        uselist=False,
        lazy="selectin",
    )

    __table_args__ = (
        Index("idx_cargo_requests_status", "status"),
        Index("idx_cargo_requests_provider_status", "provider", "status"),
        Index("idx_cargo_requests_batch_job_id", "batch_job_id"),
        Index("idx_cargo_requests_created_at", "created_at"),
        Index("idx_cargo_requests_project_id", "project_id"),
        Index("idx_cargo_requests_project_status", "project_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<CargoRequest(cargo_id={self.cargo_id}, status={self.status})>"


def _default_expires_at() -> datetime:
    """Calculate default expiration date (30 days from now)."""
    return datetime.now(timezone.utc) + timedelta(days=30)


class CargoResult(Base):
    """Stores processing results for each request."""

    __tablename__ = "cargo_results"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    cargo_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cargo_requests.id"),
        unique=True,
        nullable=False,
    )
    success: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
    )
    response: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=_default_expires_at,
    )

    # Relationships
    cargo_request: Mapped[CargoRequest] = relationship(
        "CargoRequest",
        back_populates="result",
    )

    __table_args__ = (
        Index("idx_cargo_results_cargo_request_id", "cargo_request_id"),
        Index("idx_cargo_results_expires_at", "expires_at"),
    )

    def __repr__(self) -> str:
        return f"<CargoResult(id={self.id}, success={self.success})>"


class CallbackDelivery(Base):
    """Tracks callback delivery attempts and status."""

    __tablename__ = "callback_deliveries"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    cargo_request_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cargo_requests.id"),
        unique=True,
        nullable=False,
    )
    status: Mapped[CallbackStatus] = mapped_column(
        Enum(CallbackStatus, name="callback_status", create_constraint=True, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=CallbackStatus.PENDING,
    )
    attempt_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    last_attempt_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    next_retry_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    http_status_code: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    cargo_request: Mapped[CargoRequest] = relationship(
        "CargoRequest",
        back_populates="callback_delivery",
    )

    __table_args__ = (
        Index("idx_callback_deliveries_status", "status"),
        Index(
            "idx_callback_deliveries_next_retry_at",
            "next_retry_at",
            postgresql_where="status IN ('pending', 'retrying', 'manual_retry')",
        ),
        Index("idx_callback_deliveries_cargo_request_id", "cargo_request_id"),
    )

    def __repr__(self) -> str:
        return f"<CallbackDelivery(id={self.id}, status={self.status}, attempts={self.attempt_count})>"
