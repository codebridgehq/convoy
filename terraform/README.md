# Convoy AWS Infrastructure

This directory contains Terraform configurations for deploying Convoy to AWS using ECS Fargate.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AWS Cloud                                       │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                         VPC (10.0.0.0/16)                             │  │
│  │                                                                       │  │
│  │  ┌─────────────────────────┐    ┌─────────────────────────────────┐  │  │
│  │  │    Public Subnets       │    │      Private Subnets            │  │  │
│  │  │                         │    │                                 │  │  │
│  │  │  ┌─────────────────┐    │    │  ┌─────────────────────────┐   │  │  │
│  │  │  │      ALB        │────┼────┼──│     convoy-api          │   │  │  │
│  │  │  └─────────────────┘    │    │  │     (ECS Fargate)       │   │  │  │
│  │  │                         │    │  └─────────────────────────┘   │  │  │
│  │  │  ┌─────────────────┐    │    │                                 │  │  │
│  │  │  │   NAT Gateway   │    │    │  ┌─────────────────────────┐   │  │  │
│  │  │  └─────────────────┘    │    │  │    convoy-worker        │   │  │  │
│  │  │                         │    │  │    (ECS Fargate)        │   │  │  │
│  │  └─────────────────────────┘    │  └─────────────────────────┘   │  │  │
│  │                                 │                                 │  │  │
│  │                                 │  ┌─────────────────────────┐   │  │  │
│  │                                 │  │      temporal           │   │  │  │
│  │                                 │  │    (ECS Fargate)        │   │  │  │
│  │                                 │  └─────────────────────────┘   │  │  │
│  │                                 │                                 │  │  │
│  │                                 │  ┌─────────────────────────┐   │  │  │
│  │                                 │  │  convoy-postgresql      │   │  │  │
│  │                                 │  │      (RDS)              │   │  │  │
│  │                                 │  └─────────────────────────┘   │  │  │
│  │                                 │                                 │  │  │
│  │                                 │  ┌─────────────────────────┐   │  │  │
│  │                                 │  │  temporal-postgresql    │   │  │  │
│  │                                 │  │      (RDS)              │   │  │  │
│  │                                 │  └─────────────────────────┘   │  │  │
│  │                                 └─────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │     ECR      │  │   Secrets    │  │  CloudWatch  │  │  S3 Bucket   │     │
│  │ Repositories │  │   Manager    │  │    Logs      │  │  (Bedrock)   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Prerequisites

1. **AWS CLI** configured with appropriate credentials
2. **Terraform** >= 1.0.0
3. **Docker** for building and pushing images
4. **S3 bucket** for Terraform state (configured in `terraform-backend.hcl`)

## Files Structure

| File | Description |
|------|-------------|
| `main.tf` | Provider configuration and backend |
| `variables.tf` | Input variables |
| `vpc.tf` | VPC, subnets, NAT gateway, security groups |
| `rds.tf` | RDS PostgreSQL instances |
| `ecr.tf` | ECR repositories |
| `secrets.tf` | Secrets Manager for credentials |
| `iam-ecs.tf` | IAM roles for ECS tasks |
| `ecs-cluster.tf` | ECS Fargate cluster |
| `ecs-convoy-api.tf` | convoy-api task definition and service |
| `ecs-convoy-worker.tf` | convoy-worker task definition and service |
| `ecs-temporal.tf` | Temporal server, schema setup, and namespace creation tasks |
| `alb.tf` | Application Load Balancer |
| `cloudwatch.tf` | CloudWatch log groups |
| `bedrock_batch_processing.tf` | S3 bucket and IAM for Bedrock |
| `outputs.tf` | Output values |

## Quick Start

### 1. Initialize Terraform

```bash
cd terraform
terraform init -backend-config=terraform-backend.hcl
```

### 2. Create a tfvars file

Create `terraform.tfvars`:

```hcl
aws_region  = "us-east-1"
aws_profile = "your-aws-profile"
suffix      = "-dev"
environment = "dev"

# Optional: Customize resources
rds_instance_class = "db.t3.medium"
api_cpu            = 512
api_memory         = 1024
worker_cpu         = 512
worker_memory      = 1024
temporal_cpu       = 512
temporal_memory    = 1024
```

### 3. Plan and Apply

```bash
# Review changes
terraform plan

# Apply infrastructure
terraform apply
```

### 4. Push Temporal Images to ECR (First-Time Setup Only)

Before starting Temporal services, you need to copy the Temporal images from Docker Hub to your ECR repositories. This avoids Docker Hub rate limiting.

```bash
# Set variables
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
REGION=us-east-1
TEMPORAL_VERSION=1.29.2

# Login to ECR
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com

# Pull, tag, and push temporal/server
docker pull temporalio/server:$TEMPORAL_VERSION
docker tag temporalio/server:$TEMPORAL_VERSION $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/temporal/server:$TEMPORAL_VERSION
docker push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/temporal/server:$TEMPORAL_VERSION

# Pull, tag, and push temporal/admin-tools
docker pull temporalio/admin-tools:$TEMPORAL_VERSION
docker tag temporalio/admin-tools:$TEMPORAL_VERSION $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/temporal/admin-tools:$TEMPORAL_VERSION
docker push $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/temporal/admin-tools:$TEMPORAL_VERSION
```

> **Note**: If you hit Docker Hub rate limits, wait a few hours or use a Docker Hub account.

### 5. Initialize Temporal Database (First-Time Setup Only)

After the infrastructure is created and images are pushed, you need to run one-time initialization tasks for Temporal:

#### Step 1: Run Schema Setup Task

This task creates the Temporal database schema. Run it once before starting the Temporal server for the first time:

```bash
# Get the subnet and security group IDs from terraform output
SUBNET_ID=$(terraform output -raw private_subnet_ids | cut -d',' -f1)
SECURITY_GROUP_ID=$(terraform output -raw temporal_security_group_id)

# Run the schema setup task
aws ecs run-task \
  --cluster convoy-dev \
  --task-definition temporal-schema-setup-dev \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_ID],securityGroups=[$SECURITY_GROUP_ID],assignPublicIp=DISABLED}"
```

Wait for the task to complete successfully. You can monitor progress in CloudWatch Logs:

```bash
aws logs tail /ecs/temporal-schema-setup-dev --follow
```

#### Step 2: Start Temporal Service

The Temporal service should start automatically after `terraform apply`. Verify it's running:

```bash
aws ecs describe-services --cluster convoy-dev --services temporal --query 'services[0].runningCount'
```

#### Step 3: Run Namespace Creation Task

After Temporal is healthy, create the default namespace:

```bash
aws ecs run-task \
  --cluster convoy-dev \
  --task-definition temporal-create-namespace-dev \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[$SUBNET_ID],securityGroups=[$SECURITY_GROUP_ID],assignPublicIp=DISABLED}"
```

Monitor progress:

```bash
aws logs tail /ecs/temporal-create-namespace-dev --follow
```

> **Note**: These initialization tasks only need to be run once during initial setup. For subsequent deployments, the schema and namespace will already exist.

### 6. Build and Push Docker Images

After infrastructure is created, build and push your application images:

```bash
# Get ECR login
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build and push convoy-api
docker build -t <account-id>.dkr.ecr.us-east-1.amazonaws.com/convoy/api:latest \
  --target api_prod \
  -f core/Dockerfile.api core/
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/convoy/api:latest

# Build and push convoy-worker
docker build -t <account-id>.dkr.ecr.us-east-1.amazonaws.com/convoy/worker:latest \
  --target worker_prod \
  -f core/Dockerfile.worker core/
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/convoy/worker:latest
```

### 7. Run Database Migrations

```bash
aws ecs run-task \
  --cluster convoy-dev \
  --task-definition convoy-api-dev \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[<subnet-id>],securityGroups=[<sg-id>],assignPublicIp=DISABLED}" \
  --overrides '{"containerOverrides":[{"name":"convoy-api","command":["uv","run","alembic","upgrade","head"]}]}'
```

### 8. Force New Deployment

After pushing new images:

```bash
aws ecs update-service --cluster convoy-dev --service convoy-api --force-new-deployment
aws ecs update-service --cluster convoy-dev --service convoy-worker --force-new-deployment
```

## Configuration Variables

### Required Variables

| Variable | Description |
|----------|-------------|
| `aws_profile` | AWS CLI profile to use |
| `suffix` | Resource name suffix (e.g., `-dev`, `-prod`) |

### Optional Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `aws_region` | `us-east-1` | AWS region |
| `environment` | `dev` | Environment name |
| `vpc_cidr` | `10.0.0.0/16` | VPC CIDR block |
| `rds_instance_class` | `db.t3.medium` | RDS instance type |
| `api_cpu` | `512` | CPU units for convoy-api |
| `api_memory` | `1024` | Memory (MB) for convoy-api |
| `api_desired_count` | `1` | Number of convoy-api tasks |
| `worker_cpu` | `512` | CPU units for convoy-worker |
| `worker_memory` | `1024` | Memory (MB) for convoy-worker |
| `worker_desired_count` | `1` | Number of convoy-worker tasks |
| `temporal_cpu` | `512` | CPU units for Temporal |
| `temporal_memory` | `1024` | Memory (MB) for Temporal |
| `temporal_version` | `1.29.2` | Temporal server version |
| `temporal_admin_tools_version` | `1.29.2` | Temporal admin-tools version |
| `acm_certificate_arn` | `""` | ACM cert ARN for HTTPS |

### Application Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `batch_size_threshold` | `100` | Batch size threshold |
| `batch_time_threshold_seconds` | `3600` | Batch time threshold |
| `batch_check_interval_seconds` | `30` | Batch check interval |
| `result_retention_days` | `30` | Days to retain results |
| `callback_max_retries` | `5` | Max callback retries |
| `callback_http_timeout_seconds` | `30` | Callback timeout |

## Outputs

After applying, Terraform outputs useful information:

```bash
terraform output

# Key outputs:
# - api_url: URL to access the API
# - ecr_convoy_api_repository_url: ECR URL for convoy-api
# - ecr_convoy_worker_repository_url: ECR URL for convoy-worker
# - deployment_commands: Ready-to-use deployment commands
# - migration_command: Command to run migrations
```

## Scaling

To scale services, update the `desired_count` variables:

```hcl
api_desired_count    = 2
worker_desired_count = 2
```

Or use AWS CLI:

```bash
aws ecs update-service --cluster convoy-dev --service convoy-api --desired-count 2
```

## HTTPS Setup

To enable HTTPS:

1. Create an ACM certificate in the AWS Console
2. Add the certificate ARN to your tfvars:

```hcl
acm_certificate_arn = "arn:aws:acm:us-east-1:123456789:certificate/xxx"
```

3. Apply changes: `terraform apply`

## Troubleshooting

### View Logs

```bash
# convoy-api logs
aws logs tail /ecs/convoy-api-dev --follow

# convoy-worker logs
aws logs tail /ecs/convoy-worker-dev --follow

# temporal logs
aws logs tail /ecs/temporal-dev --follow

# temporal schema setup logs (for debugging init issues)
aws logs tail /ecs/temporal-schema-setup-dev --follow

# temporal namespace creation logs
aws logs tail /ecs/temporal-create-namespace-dev --follow
```

### Re-running Temporal Init Tasks

If you need to re-run the initialization tasks (e.g., after a failed attempt):

```bash
# Schema setup is idempotent - safe to re-run
aws ecs run-task \
  --cluster convoy-dev \
  --task-definition temporal-schema-setup-dev \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[<subnet-id>],securityGroups=[<sg-id>],assignPublicIp=DISABLED}"

# Namespace creation is also idempotent
aws ecs run-task \
  --cluster convoy-dev \
  --task-definition temporal-create-namespace-dev \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[<subnet-id>],securityGroups=[<sg-id>],assignPublicIp=DISABLED}"
```

### Check Service Status

```bash
aws ecs describe-services --cluster convoy-dev --services convoy-api convoy-worker temporal
```

### Connect to RDS (for debugging)

The RDS instances are in private subnets and not publicly accessible. Use the SSM Session Manager tunnel to connect from your local machine.

#### Prerequisites

Install the AWS Session Manager plugin:

```bash
brew install --cask session-manager-plugin
```

#### Start the Database Tunnel

```bash
# Connect to convoy database
CONVOY_CLUSTER_NAME=convoy-dev CONVOY_SUFFIX=-dev ./scripts/db-tunnel.sh

# Connect to temporal database
CONVOY_CLUSTER_NAME=convoy-dev CONVOY_SUFFIX=-dev ./scripts/db-tunnel.sh temporal
```

#### Connect with TablePlus or psql

Once the tunnel is running, connect to:

| Field | Value |
|-------|-------|
| Host | `127.0.0.1` (use IPv4, not `localhost`) |
| Port | `5432` |
| User | `convoy` (or `temporal`) |
| Database | `convoy` (or `temporal`) |
| Password | Get from Secrets Manager (see below) |

#### Get the Database Password

```bash
# Convoy database password
aws secretsmanager get-secret-value \
    --secret-id "convoy/db-credentials-dev" \
    --query 'SecretString' \
    --output text \
    --region us-east-1 | jq -r '.password'

# Temporal database password
aws secretsmanager get-secret-value \
    --secret-id "temporal/db-credentials-dev" \
    --query 'SecretString' \
    --output text \
    --region us-east-1 | jq -r '.password'
```

> **Note**: Use `127.0.0.1` instead of `localhost` to ensure you connect via IPv4 to the SSM tunnel, especially if you have Docker running which may bind to port 5432 on IPv6.

## Cleanup

To destroy all resources:

```bash
terraform destroy
```

**Warning**: This will delete all data including databases. Make sure to backup any important data first.
