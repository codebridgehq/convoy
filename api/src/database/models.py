"""SQLAlchemy models for cargo request storage and batch processing."""

import enum
import uuid
from datetime import datetime, timedelta, timezone

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
        Enum(ProviderType, name="provider_type", create_constraint=True),
        nullable=False,
    )
    provider_job_id: Mapped[str | None] = mapped_column(
        String(256),
        nullable=True,
    )
    status: Mapped[BatchStatus] = mapped_column(
        Enum(BatchStatus, name="batch_status", create_constraint=True),
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
        Enum(ProviderType, name="provider_type", create_constraint=True),
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
        Enum(CargoStatus, name="cargo_status", create_constraint=True),
        nullable=False,
        default=CargoStatus.PENDING,
    )
    batch_job_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("batch_jobs.id"),
        nullable=True,
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
        Enum(CallbackStatus, name="callback_status", create_constraint=True),
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
