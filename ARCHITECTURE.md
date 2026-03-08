# Architecture

Convoy is a distributed batch processing system built with a microservices architecture. It uses Temporal for workflow orchestration, PostgreSQL for persistence, and supports multiple AI providers (AWS Bedrock, Anthropic) for batch inference.

## System Architecture

```mermaid
graph TB
    subgraph DockerNetwork["temporal-network"]
        subgraph ConvoyServices["Convoy Services"]
            API["🚂 convoy-api<br/>(FastAPI)<br/>:8000"]
            Worker["⚙️ convoy-worker<br/>(Temporal Worker)"]
        end

        subgraph ConvoyDB["Convoy Database"]
            PG["🗄️ convoy-postgresql<br/>:5433"]
        end

        subgraph TemporalStack["Temporal Stack"]
            Temporal["⚡ temporal<br/>(Temporal Server)<br/>:7233"]
            TemporalUI["🖥️ temporal-ui<br/>:8080"]
            TemporalPG["🗄️ temporal-postgresql<br/>:5432"]
            TemporalAdmin["🔧 temporal-admin-tools"]
        end
    end

    subgraph External["External Services"]
        Bedrock["☁️ AWS Bedrock"]
        S3["📦 AWS S3"]
        Webhook["📤 Client Webhook"]
    end

    Client["👤 Client"] -->|"HTTP :8000"| API
    API -->|"SQL :5433"| PG
    Worker -->|"SQL :5433"| PG
    Worker -->|"gRPC :7233"| Temporal
    Temporal -->|"SQL :5432"| TemporalPG
    TemporalUI -->|"gRPC :7233"| Temporal
    TemporalAdmin -->|"gRPC :7233"| Temporal
    Worker -->|"HTTPS"| Bedrock
    Worker -->|"HTTPS"| S3
    Worker -->|"HTTP POST"| Webhook
```

## Data Flow

```mermaid
sequenceDiagram
    participant C as Client
    participant API as Convoy API
    participant DB as PostgreSQL
    participant BSW as BatchSchedulerWorkflow
    participant P as Provider (Bedrock/Anthropic)
    participant CDW as CallbackDeliveryWorkflow
    participant WH as Client Webhook

    C->>API: POST /cargo/load
    API->>DB: Insert CargoRequest (PENDING)
    API-->>C: cargo_id

    loop Every 30s
        BSW->>DB: Check pending requests
        alt Threshold met (100 requests OR 1 hour)
            BSW->>DB: Create BatchJob
            BSW->>DB: Update CargoRequests (BATCHED)
            BSW->>P: Submit batch
            loop Until complete
                BSW->>P: Poll status
            end
            P-->>BSW: Results
            BSW->>DB: Store CargoResults (COMPLETED)
            BSW->>CDW: Start callback delivery
        end
    end

    CDW->>DB: Get callback payload
    loop Retry with backoff (1m, 5m, 15m, 1h)
        CDW->>WH: POST result
        alt Success
            CDW->>DB: Update status (CALLBACK_DELIVERED)
        else Failure
            CDW->>DB: Update retry count
        end
    end
```

## Cargo Status Lifecycle

```mermaid
stateDiagram-v2
    [*] --> PENDING: Request submitted
    PENDING --> BATCHED: Added to batch
    BATCHED --> PROCESSING: Batch submitted to provider
    PROCESSING --> COMPLETED: Results received
    PROCESSING --> FAILED: Provider error
    COMPLETED --> CALLBACK_PENDING: Ready for delivery
    CALLBACK_PENDING --> CALLBACK_DELIVERED: Webhook success
    CALLBACK_PENDING --> CALLBACK_FAILED: Max retries exceeded
    FAILED --> [*]
    CALLBACK_DELIVERED --> [*]
    CALLBACK_FAILED --> [*]
```

## Database Schema

```mermaid
erDiagram
    cargo_requests ||--o| batch_jobs : "belongs to"
    cargo_requests ||--o| cargo_results : "has"
    cargo_requests ||--o| callback_deliveries : "has"

    cargo_requests {
        uuid id PK
        string cargo_id UK
        enum provider
        string model
        jsonb params
        string callback_url
        enum status
        uuid batch_job_id FK
        timestamp created_at
        timestamp updated_at
    }

    batch_jobs {
        uuid id PK
        enum provider
        string provider_job_id
        enum status
        int request_count
        jsonb metadata
        text error_message
        timestamp created_at
        timestamp submitted_at
        timestamp completed_at
    }

    cargo_results {
        uuid id PK
        uuid cargo_request_id FK
        boolean success
        jsonb response
        text error_message
        timestamp created_at
        timestamp expires_at
    }

    callback_deliveries {
        uuid id PK
        uuid cargo_request_id FK
        enum status
        int attempt_count
        timestamp last_attempt_at
        timestamp next_retry_at
        int http_status_code
        text error_message
        timestamp created_at
        timestamp completed_at
    }
```

## Core Components

### Convoy API (FastAPI)

The REST API layer that handles incoming requests:

| Endpoint | Description |
|----------|-------------|
| `POST /cargo/load` | Submit prompts for batch processing |
| `GET /cargo/{id}/tracking` | Track the status of submitted cargo |
| `GET /health` | Health check endpoint |

### Services Layer

- **CargoLoaderService** - Persists incoming requests to the database with status `PENDING`
- **CargoTrackerService** - Retrieves cargo status and tracking information
- **BatchProcessingService** - Manages batch jobs across multiple providers

### Temporal Worker

Executes workflows and activities for batch processing orchestration:

**Workflows:**

| Workflow | Description |
|----------|-------------|
| `BatchSchedulerWorkflow` | Long-running workflow (one per provider) that monitors pending requests, creates batches when thresholds are met, submits to providers, and triggers callbacks |
| `CallbackDeliveryWorkflow` | Delivers results to client webhooks with exponential backoff retry (1min → 5min → 15min → 1hr) |
| `ResultCleanupWorkflow` | Periodic cleanup of expired results (default: 30 days) |

### Batch Processor Adapters

Provider-specific implementations for batch inference:

| Adapter | Description |
|---------|-------------|
| `BedrockBatchProcessor` | AWS Bedrock batch inference via S3 |
| `AnthropicBatchProcessor` | Anthropic Message Batches API |

## Configuration

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `BATCH_SIZE_THRESHOLD` | 100 | Max requests per batch |
| `BATCH_TIME_THRESHOLD_SECONDS` | 3600 | Max wait time before batching |
| `BATCH_CHECK_INTERVAL_SECONDS` | 30 | Interval to check for pending requests |
| `RESULT_RETENTION_DAYS` | 30 | Days to retain results before cleanup |
| `CALLBACK_MAX_RETRIES` | 5 | Max callback delivery attempts |
| `CALLBACK_HTTP_TIMEOUT_SECONDS` | 30 | HTTP timeout for callbacks |
