# Convoy Docker Compose Example

Run Convoy locally using pre-built Docker images from Docker Hub.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) (v20.10+)
- [Docker Compose](https://docs.docker.com/compose/install/) (v2.0+)

## Quick Start

```bash
# 1. Navigate to this directory
cd examples/docker-compose

# 2. Copy environment file
cp .env.example .env

# 3. Start all services
docker compose up -d

# 4. Check service status
docker compose ps
```

## Access Services

Once all services are up and running:

| Service | URL |
|---------|-----|
| Convoy API | http://localhost:8000 |
| API Swagger Docs | http://localhost:8000/docs |
| Temporal UI | http://localhost:8080 |
| Convoy PostgreSQL | localhost:5433 |
| Temporal PostgreSQL | localhost:5432 |

Visit http://localhost:8000/docs to explore the API using Swagger documentation.

For detailed usage instructions and guides, refer to [docs.cnvy.ai](https://docs.cnvy.ai).

## Configuration

### Version Pinning

We recommend pinning Convoy to a specific version in production. Edit `.env`:

```env
# Use the same version for both API and Worker
CONVOY_VERSION=1.0.0
```

### Provider Configuration

**Anthropic Provider** - No additional configuration required. Set your API key in the request.

**Bedrock Provider** - Requires AWS credentials. Configure in `.env`:

```env
AWS_DIRECTORY_PATH=~/.aws
AWS_PROFILE=your-profile
AWS_REGION=us-east-1
BEDROCK_S3_BUCKET=your-bucket
BEDROCK_ROLE_ARN=arn:aws:iam::123456789012:role/BedrockBatchRole
```

Alternative AWS credential methods:
- IAM roles (ECS/EKS)
- Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
- OIDC (`AWS_WEB_IDENTITY_TOKEN_FILE`)

## Commands

```bash
# Start services
docker compose up -d

# View logs
docker compose logs -f

# View specific service logs
docker compose logs -f convoy-api

# Stop services
docker compose down

# Stop and remove volumes (clean slate)
docker compose down -v

# Restart a service
docker compose restart convoy-worker
```

## Troubleshooting

**Services not starting?**
```bash
# Check logs for errors
docker compose logs temporal-schema-setup
docker compose logs temporal-create-namespace
```

**Database connection issues?**
```bash
# Verify PostgreSQL is healthy
docker compose ps convoy-postgresql
docker compose ps temporal-postgresql
```

**Reset everything:**
```bash
docker compose down -v
docker compose up -d
```
