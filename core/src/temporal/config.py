"""Configuration for Temporal workflows and activities.

Note: These configurations are read at module load time to avoid
Temporal sandbox restrictions on os.getenv() calls inside workflows.
"""

import os


class TemporalConfig:
    """Temporal server connection configuration."""

    address: str = os.getenv("TEMPORAL_ADDRESS", "temporal:7233")
    namespace: str = os.getenv("TEMPORAL_NAMESPACE", "default")
    task_queue: str = os.getenv("TEMPORAL_TASK_QUEUE", "convoy-tasks")


class BatchConfig:
    """Batch processing configuration."""

    size_threshold: int = int(os.getenv("BATCH_SIZE_THRESHOLD", "100"))
    time_threshold_seconds: int = int(os.getenv("BATCH_TIME_THRESHOLD_SECONDS", "3600"))
    # How often to check for pending requests (seconds)
    check_interval_seconds: int = int(os.getenv("BATCH_CHECK_INTERVAL_SECONDS", "30"))


class CallbackConfig:
    """Callback delivery configuration."""

    max_retries: int = int(os.getenv("CALLBACK_MAX_RETRIES", "5"))
    # Retry delays in seconds: 1min, 5min, 15min, 1hr
    retry_delays: tuple[int, ...] = (60, 300, 900, 3600)
    # HTTP timeout for callback delivery
    http_timeout_seconds: int = int(os.getenv("CALLBACK_HTTP_TIMEOUT_SECONDS", "30"))


class CleanupConfig:
    """Result cleanup configuration."""

    retention_days: int = int(os.getenv("RESULT_RETENTION_DAYS", "30"))
    # Batch size for deletion operations
    deletion_batch_size: int = int(os.getenv("CLEANUP_BATCH_SIZE", "1000"))


class BedrockConfig:
    """AWS Bedrock batch processing configuration."""

    region: str = os.getenv("AWS_REGION", "")
    s3_bucket: str = os.getenv("BEDROCK_S3_BUCKET", "")
    role_arn: str = os.getenv("BEDROCK_ROLE_ARN", "")
    s3_input_prefix: str = os.getenv("BEDROCK_S3_INPUT_PREFIX", "batch-inputs")
    s3_output_prefix: str = os.getenv("BEDROCK_S3_OUTPUT_PREFIX", "batch-outputs")
