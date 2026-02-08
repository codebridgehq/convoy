#!/bin/bash
# =============================================================================
# Full Deployment Script
# =============================================================================
# This script handles the complete deployment workflow:
# 1. Build and push Convoy images to ECR
# 2. Optionally push Temporal images to ECR (skipped by default)
# 3. Optionally run Temporal schema setup
# 4. Force new deployment of ECS services
#
# Usage:
#   ./scripts/deploy.sh [OPTIONS]
#
# Options:
#   --region REGION           AWS region (default: us-east-1)
#   --tag TAG                 Image tag (default: latest)
#   --with-temporal           Also push Temporal images (skipped by default)
#   --skip-convoy             Skip building Convoy images
#   --run-schema-setup        Run Temporal schema setup task
#   --run-namespace-setup     Run Temporal namespace creation task
#   --cluster CLUSTER         ECS cluster name (default: convoy-dev)
#
# Environment variables (optional):
#   AWS_REGION - AWS region
#   IMAGE_TAG - Image tag for Convoy images
# =============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
REGION="${AWS_REGION:-us-east-1}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
CLUSTER="convoy-dev"
PUSH_TEMPORAL=false  # Skipped by default - Temporal images rarely change
PUSH_CONVOY=true
RUN_SCHEMA_SETUP=false
RUN_NAMESPACE_SETUP=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --region)
            REGION="$2"
            shift 2
            ;;
        --tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
        --cluster)
            CLUSTER="$2"
            shift 2
            ;;
        --with-temporal)
            PUSH_TEMPORAL=true
            shift
            ;;
        --skip-convoy)
            PUSH_CONVOY=false
            shift
            ;;
        --run-schema-setup)
            RUN_SCHEMA_SETUP=true
            shift
            ;;
        --run-namespace-setup)
            RUN_NAMESPACE_SETUP=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --region REGION           AWS region (default: us-east-1)"
            echo "  --tag TAG                 Image tag (default: latest)"
            echo "  --cluster CLUSTER         ECS cluster name (default: convoy-dev)"
            echo "  --with-temporal           Also push Temporal images (skipped by default)"
            echo "  --skip-convoy             Skip building Convoy images"
            echo "  --run-schema-setup        Run Temporal schema setup task"
            echo "  --run-namespace-setup     Run Temporal namespace creation task"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${GREEN}==============================================================================${NC}"
echo -e "${GREEN}Convoy Deployment Script${NC}"
echo -e "${GREEN}==============================================================================${NC}"
echo -e "Region:              ${YELLOW}${REGION}${NC}"
echo -e "Image Tag:           ${YELLOW}${IMAGE_TAG}${NC}"
echo -e "Cluster:             ${YELLOW}${CLUSTER}${NC}"
echo -e "Push Temporal:       ${YELLOW}${PUSH_TEMPORAL}${NC}"
echo -e "Push Convoy:         ${YELLOW}${PUSH_CONVOY}${NC}"
echo -e "Run Schema Setup:    ${YELLOW}${RUN_SCHEMA_SETUP}${NC}"
echo -e "Run Namespace Setup: ${YELLOW}${RUN_NAMESPACE_SETUP}${NC}"
echo -e "${GREEN}==============================================================================${NC}"
echo ""

# Step 1: Build and push Convoy images
if [ "$PUSH_CONVOY" = true ]; then
    echo -e "${BLUE}Step 1: Building and pushing Convoy images to ECR...${NC}"
    AWS_REGION="$REGION" IMAGE_TAG="$IMAGE_TAG" "${SCRIPT_DIR}/push-convoy-images.sh"
else
    echo -e "${YELLOW}Step 1: Skipping Convoy images (--skip-convoy)${NC}"
fi
echo ""

# Step 2: Push Temporal images (optional)
if [ "$PUSH_TEMPORAL" = true ]; then
    echo -e "${BLUE}Step 2: Pushing Temporal images to ECR...${NC}"
    AWS_REGION="$REGION" "${SCRIPT_DIR}/push-temporal-images.sh"
else
    echo -e "${YELLOW}Step 2: Skipping Temporal images (use --with-temporal to include)${NC}"
fi
echo ""

# Step 3: Run Temporal schema setup (if requested)
if [ "$RUN_SCHEMA_SETUP" = true ]; then
    echo -e "${BLUE}Step 3: Running Temporal schema setup...${NC}"
    
    # Get VPC configuration from ECS service
    TEMPORAL_SERVICE_CONFIG=$(aws ecs describe-services \
        --cluster "$CLUSTER" \
        --services temporal \
        --query 'services[0].networkConfiguration.awsvpcConfiguration' \
        --output json 2>/dev/null || echo "{}")
    
    if [ "$TEMPORAL_SERVICE_CONFIG" != "{}" ] && [ "$TEMPORAL_SERVICE_CONFIG" != "null" ]; then
        SUBNETS=$(echo "$TEMPORAL_SERVICE_CONFIG" | jq -r '.subnets | join(",")')
        SECURITY_GROUPS=$(echo "$TEMPORAL_SERVICE_CONFIG" | jq -r '.securityGroups | join(",")')
        
        echo "  Subnets: $SUBNETS"
        echo "  Security Groups: $SECURITY_GROUPS"
        
        # Determine task definition name based on cluster suffix
        SUFFIX=""
        if [[ "$CLUSTER" == *"-dev" ]]; then
            SUFFIX="-dev"
        elif [[ "$CLUSTER" == *"-prod" ]]; then
            SUFFIX="-prod"
        fi
        
        TASK_ARN=$(aws ecs run-task \
            --cluster "$CLUSTER" \
            --task-definition "temporal-schema-setup${SUFFIX}" \
            --launch-type FARGATE \
            --network-configuration "awsvpcConfiguration={subnets=[$SUBNETS],securityGroups=[$SECURITY_GROUPS],assignPublicIp=DISABLED}" \
            --query 'tasks[0].taskArn' \
            --output text)
        
        echo -e "${GREEN}  ✓ Schema setup task started: ${TASK_ARN}${NC}"
        echo "  Monitor logs: aws logs tail /ecs/temporal-schema-setup${SUFFIX} --follow"
    else
        echo -e "${RED}  ✗ Could not get network configuration from temporal service${NC}"
        echo "  Please run schema setup manually"
    fi
else
    echo -e "${YELLOW}Step 3: Skipping schema setup (use --run-schema-setup to enable)${NC}"
fi
echo ""

# Step 4: Run Temporal namespace setup (if requested)
if [ "$RUN_NAMESPACE_SETUP" = true ]; then
    echo -e "${BLUE}Step 4: Running Temporal namespace creation...${NC}"
    
    # Get VPC configuration from ECS service
    TEMPORAL_SERVICE_CONFIG=$(aws ecs describe-services \
        --cluster "$CLUSTER" \
        --services temporal \
        --query 'services[0].networkConfiguration.awsvpcConfiguration' \
        --output json 2>/dev/null || echo "{}")
    
    if [ "$TEMPORAL_SERVICE_CONFIG" != "{}" ] && [ "$TEMPORAL_SERVICE_CONFIG" != "null" ]; then
        SUBNETS=$(echo "$TEMPORAL_SERVICE_CONFIG" | jq -r '.subnets | join(",")')
        SECURITY_GROUPS=$(echo "$TEMPORAL_SERVICE_CONFIG" | jq -r '.securityGroups | join(",")')
        
        # Determine task definition name based on cluster suffix
        SUFFIX=""
        if [[ "$CLUSTER" == *"-dev" ]]; then
            SUFFIX="-dev"
        elif [[ "$CLUSTER" == *"-prod" ]]; then
            SUFFIX="-prod"
        fi
        
        TASK_ARN=$(aws ecs run-task \
            --cluster "$CLUSTER" \
            --task-definition "temporal-create-namespace${SUFFIX}" \
            --launch-type FARGATE \
            --network-configuration "awsvpcConfiguration={subnets=[$SUBNETS],securityGroups=[$SECURITY_GROUPS],assignPublicIp=DISABLED}" \
            --query 'tasks[0].taskArn' \
            --output text)
        
        echo -e "${GREEN}  ✓ Namespace creation task started: ${TASK_ARN}${NC}"
        echo "  Monitor logs: aws logs tail /ecs/temporal-create-namespace${SUFFIX} --follow"
    else
        echo -e "${RED}  ✗ Could not get network configuration from temporal service${NC}"
        echo "  Please run namespace creation manually"
    fi
else
    echo -e "${YELLOW}Step 4: Skipping namespace setup (use --run-namespace-setup to enable)${NC}"
fi
echo ""

# Step 5: Force new deployment of ECS services
echo -e "${BLUE}Step 5: Forcing new deployment of ECS services...${NC}"

# Update Temporal service
echo "  Updating temporal service..."
aws ecs update-service --cluster "$CLUSTER" --service temporal --force-new-deployment --query 'service.serviceName' --output text > /dev/null 2>&1 || echo "  (temporal service may not exist yet)"

# Update convoy-api service
if [ "$PUSH_CONVOY" = true ]; then
    echo "  Updating convoy-api service..."
    aws ecs update-service --cluster "$CLUSTER" --service convoy-api --force-new-deployment --query 'service.serviceName' --output text > /dev/null 2>&1 || echo "  (convoy-api service may not exist yet)"
    
    echo "  Updating convoy-worker service..."
    aws ecs update-service --cluster "$CLUSTER" --service convoy-worker --force-new-deployment --query 'service.serviceName' --output text > /dev/null 2>&1 || echo "  (convoy-worker service may not exist yet)"
fi

echo -e "${GREEN}  ✓ Deployment triggered${NC}"
echo ""

echo -e "${GREEN}==============================================================================${NC}"
echo -e "${GREEN}✓ Deployment complete!${NC}"
echo -e "${GREEN}==============================================================================${NC}"
echo ""
echo "Monitor deployment status:"
echo "  aws ecs describe-services --cluster $CLUSTER --services temporal convoy-api convoy-worker --query 'services[*].{name:serviceName,status:status,running:runningCount,desired:desiredCount}' --output table"
echo ""
echo "View logs:"
echo "  aws logs tail /ecs/temporal --follow"
echo "  aws logs tail /ecs/convoy-api --follow"
echo "  aws logs tail /ecs/convoy-worker --follow"
