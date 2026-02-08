#!/bin/bash
# =============================================================================
# Database Tunnel Script
# =============================================================================
# Creates an SSM Session Manager tunnel to the RDS database through an ECS task.
# This allows you to connect to the private RDS instance from your local machine.
#
# Prerequisites:
# 1. AWS CLI configured with appropriate credentials
# 2. Session Manager plugin installed: brew install --cask session-manager-plugin
# 3. ECS service deployed with enable_execute_command = true
# 4. Terraform applied with the SSM permissions
#
# Usage:
#   ./scripts/db-tunnel.sh [convoy|temporal] [local_port]
#
# Environment Variables:
#   AWS_REGION          - AWS region (default: us-east-1)
#   AWS_PROFILE         - AWS CLI profile to use
#   CONVOY_SUFFIX       - Suffix used in Terraform (e.g., -dev, -prod)
#   CONVOY_CLUSTER_NAME - ECS cluster name (default: convoy-cluster${SUFFIX})
#   CONVOY_SERVICE_NAME - ECS service name (default: convoy-api)
#
# Examples:
#   ./scripts/db-tunnel.sh                          # Connect to convoy DB on localhost:5432
#   ./scripts/db-tunnel.sh convoy 5433              # Connect to convoy DB on localhost:5433
#   ./scripts/db-tunnel.sh temporal                 # Connect to temporal DB on localhost:5432
#   CONVOY_SUFFIX=-dev ./scripts/db-tunnel.sh      # Use -dev suffix
# =============================================================================

set -e

# Configuration
SUFFIX="${CONVOY_SUFFIX:-}"
CLUSTER_NAME="${CONVOY_CLUSTER_NAME:-convoy-cluster${SUFFIX}}"
SERVICE_NAME="${CONVOY_SERVICE_NAME:-convoy-api}"
AWS_REGION="${AWS_REGION:-us-east-1}"
DB_TYPE="${1:-convoy}"
LOCAL_PORT="${2:-5432}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔗 Database Tunnel Script${NC}"
echo "================================"
echo -e "${BLUE}Configuration:${NC}"
echo -e "  Region:  ${AWS_REGION}"
echo -e "  Suffix:  ${SUFFIX:-<none>}"
echo -e "  Cluster: ${CLUSTER_NAME}"
echo -e "  Service: ${SERVICE_NAME}"
echo -e "  DB Type: ${DB_TYPE}"
echo ""

# Check prerequisites
echo -e "${YELLOW}Checking prerequisites...${NC}"

if ! command -v aws &> /dev/null; then
    echo -e "${RED}❌ AWS CLI not found. Please install it first.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ AWS CLI found${NC}"

if ! command -v session-manager-plugin &> /dev/null; then
    echo -e "${RED}❌ Session Manager plugin not found.${NC}"
    echo "Install it with: brew install --cask session-manager-plugin"
    exit 1
fi
echo -e "${GREEN}✓ Session Manager plugin found${NC}"

# Test AWS credentials
echo -e "${YELLOW}Testing AWS credentials...${NC}"
if ! aws sts get-caller-identity --region "$AWS_REGION" &> /dev/null; then
    echo -e "${RED}❌ AWS credentials not configured or invalid.${NC}"
    echo "Run 'aws configure' or set AWS_PROFILE environment variable."
    exit 1
fi
echo -e "${GREEN}✓ AWS credentials valid${NC}"

# Get the RDS endpoint based on DB type
echo -e "${YELLOW}Getting RDS endpoint for ${DB_TYPE}...${NC}"

if [ "$DB_TYPE" = "convoy" ]; then
    RDS_IDENTIFIER="convoy-postgresql${SUFFIX}"
elif [ "$DB_TYPE" = "temporal" ]; then
    RDS_IDENTIFIER="temporal-postgresql${SUFFIX}"
else
    echo -e "${RED}❌ Unknown database type: ${DB_TYPE}${NC}"
    echo "Use 'convoy' or 'temporal'"
    exit 1
fi

echo -e "${BLUE}Looking for RDS instance: ${RDS_IDENTIFIER}${NC}"

RDS_ENDPOINT=$(aws rds describe-db-instances \
    --db-instance-identifier "$RDS_IDENTIFIER" \
    --query 'DBInstances[0].Endpoint.Address' \
    --output text \
    --region "$AWS_REGION" 2>&1) || {
    echo -e "${RED}❌ Could not find RDS instance: ${RDS_IDENTIFIER}${NC}"
    echo ""
    echo "Available RDS instances:"
    aws rds describe-db-instances \
        --query 'DBInstances[*].DBInstanceIdentifier' \
        --output table \
        --region "$AWS_REGION" 2>/dev/null || echo "  (none found or access denied)"
    echo ""
    echo "If your RDS has a suffix, set CONVOY_SUFFIX environment variable:"
    echo "  CONVOY_SUFFIX=-dev ./scripts/db-tunnel.sh"
    exit 1
}

if [ -z "$RDS_ENDPOINT" ] || [ "$RDS_ENDPOINT" = "None" ] || [ "$RDS_ENDPOINT" = "null" ]; then
    echo -e "${RED}❌ RDS instance found but endpoint is empty${NC}"
    exit 1
fi

echo -e "${GREEN}✓ RDS Endpoint: ${RDS_ENDPOINT}${NC}"

# Get a running task from the ECS service
echo -e "${YELLOW}Finding a running ECS task...${NC}"

TASK_ARN=$(aws ecs list-tasks \
    --cluster "$CLUSTER_NAME" \
    --service-name "$SERVICE_NAME" \
    --desired-status RUNNING \
    --query 'taskArns[0]' \
    --output text \
    --region "$AWS_REGION" 2>&1) || {
    echo -e "${RED}❌ Could not list tasks in cluster: ${CLUSTER_NAME}${NC}"
    echo ""
    echo "Available ECS clusters:"
    aws ecs list-clusters \
        --query 'clusterArns[*]' \
        --output table \
        --region "$AWS_REGION" 2>/dev/null || echo "  (none found or access denied)"
    exit 1
}

if [ -z "$TASK_ARN" ] || [ "$TASK_ARN" = "None" ] || [ "$TASK_ARN" = "null" ]; then
    echo -e "${RED}❌ No running tasks found in service: ${SERVICE_NAME}${NC}"
    echo ""
    echo "Available services in cluster ${CLUSTER_NAME}:"
    aws ecs list-services \
        --cluster "$CLUSTER_NAME" \
        --query 'serviceArns[*]' \
        --output table \
        --region "$AWS_REGION" 2>/dev/null || echo "  (none found)"
    echo ""
    echo "Make sure the ECS service is running with at least one task."
    exit 1
fi

# Extract task ID from ARN
TASK_ID=$(echo "$TASK_ARN" | cut -d'/' -f3)
echo -e "${GREEN}✓ Task ID: ${TASK_ID}${NC}"

# Get the runtime ID for the container
echo -e "${YELLOW}Getting container runtime ID...${NC}"

RUNTIME_ID=$(aws ecs describe-tasks \
    --cluster "$CLUSTER_NAME" \
    --tasks "$TASK_ARN" \
    --query 'tasks[0].containers[?name==`convoy-api`].runtimeId' \
    --output text \
    --region "$AWS_REGION" 2>&1) || {
    echo -e "${RED}❌ Could not describe task${NC}"
    exit 1
}

if [ -z "$RUNTIME_ID" ] || [ "$RUNTIME_ID" = "None" ] || [ "$RUNTIME_ID" = "null" ]; then
    echo -e "${RED}❌ Could not get container runtime ID${NC}"
    echo ""
    echo "This usually means one of:"
    echo "  1. enable_execute_command is not set to true on the ECS service"
    echo "  2. The task doesn't have the required SSM IAM permissions"
    echo "  3. The container name 'convoy-api' doesn't exist in the task"
    echo ""
    echo "Make sure you've applied the Terraform changes:"
    echo "  cd terraform && terraform apply"
    exit 1
fi

echo -e "${GREEN}✓ Runtime ID: ${RUNTIME_ID}${NC}"

# Build the SSM target
SSM_TARGET="ecs:${CLUSTER_NAME}_${TASK_ID}_${RUNTIME_ID}"

echo ""
echo -e "${GREEN}🚀 Starting SSM tunnel...${NC}"
echo "================================"
echo -e "Target:     ${SSM_TARGET}"
echo -e "RDS Host:   ${RDS_ENDPOINT}"
echo -e "Local Port: ${LOCAL_PORT}"
echo ""
echo -e "${YELLOW}Connect your database client to:${NC}"
echo -e "  Host:     localhost"
echo -e "  Port:     ${LOCAL_PORT}"
echo -e "  Database: ${DB_TYPE}"
echo -e "  Username: ${DB_TYPE}"
echo -e "  Password: (from AWS Secrets Manager)"
echo ""
echo -e "${YELLOW}Press Ctrl+C to close the tunnel${NC}"
echo ""

# Start the SSM session with port forwarding
aws ssm start-session \
    --target "$SSM_TARGET" \
    --document-name AWS-StartPortForwardingSessionToRemoteHost \
    --parameters "{\"host\":[\"${RDS_ENDPOINT}\"],\"portNumber\":[\"5432\"],\"localPortNumber\":[\"${LOCAL_PORT}\"]}" \
    --region "$AWS_REGION"
