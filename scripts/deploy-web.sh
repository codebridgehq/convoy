#!/bin/bash
# =============================================================================
# Build and Push Convoy Web Image to ECR
# =============================================================================
# This script builds the convoy-web Docker image and pushes it to ECR.
# It builds for linux/amd64 to ensure compatibility with ECS Fargate.
#
# Usage:
#   ./scripts/deploy-web.sh [OPTIONS]
#
# Options:
#   --region REGION           AWS region (default: us-east-1)
#   --tag TAG                 Image tag (default: latest)
#   --cluster CLUSTER         ECS cluster name (default: convoy-dev)
#   --skip-build              Skip building, only force ECS deployment
#
# Environment variables (optional):
#   AWS_REGION - AWS region
#   IMAGE_TAG - Image tag for web image
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
SKIP_BUILD=false

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
        --skip-build)
            SKIP_BUILD=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --region REGION    AWS region (default: us-east-1)"
            echo "  --tag TAG          Image tag (default: latest)"
            echo "  --cluster CLUSTER  ECS cluster name (default: convoy-dev)"
            echo "  --skip-build       Skip building, only force ECS deployment"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# Get AWS account ID
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_PREFIX="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com"

# Get script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
WEB_DIR="${PROJECT_ROOT}/web"

echo -e "${GREEN}==============================================================================${NC}"
echo -e "${GREEN}Building and Pushing Convoy Web Image to ECR${NC}"
echo -e "${GREEN}==============================================================================${NC}"
echo -e "AWS Account:    ${YELLOW}${ACCOUNT_ID}${NC}"
echo -e "Region:         ${YELLOW}${REGION}${NC}"
echo -e "ECR Prefix:     ${YELLOW}${ECR_PREFIX}${NC}"
echo -e "Image Tag:      ${YELLOW}${IMAGE_TAG}${NC}"
echo -e "Cluster:        ${YELLOW}${CLUSTER}${NC}"
echo -e "Skip Build:     ${YELLOW}${SKIP_BUILD}${NC}"
echo -e "${GREEN}==============================================================================${NC}"
echo ""

if [ "$SKIP_BUILD" = false ]; then
    # Login to ECR
    echo -e "${YELLOW}Logging in to ECR...${NC}"
    aws ecr get-login-password --region "$REGION" | docker login --username AWS --password-stdin "$ECR_PREFIX"
    echo -e "${GREEN}✓ ECR login successful${NC}"
    echo ""

    # Build and push web image
    FULL_IMAGE="${ECR_PREFIX}/convoy/web:${IMAGE_TAG}"
    
    echo -e "${BLUE}Building convoy-web image...${NC}"
    echo "  Dockerfile: ${WEB_DIR}/Dockerfile"
    echo "  Target: app_prod"
    echo "  Image: ${FULL_IMAGE}"
    echo ""
    
    # Build with explicit platform (important for Apple Silicon Macs)
    echo "  Building for linux/amd64..."
    docker build \
        --platform linux/amd64 \
        --file "${WEB_DIR}/Dockerfile" \
        --target "app_prod" \
        --tag "${FULL_IMAGE}" \
        "${WEB_DIR}"
    
    # Push to ECR
    echo "  Pushing to ECR..."
    docker push "${FULL_IMAGE}"
    
    echo -e "${GREEN}  ✓ Image built and pushed${NC}"
    echo ""
fi

# Force new deployment of ECS service
echo -e "${BLUE}Forcing new deployment of convoy-web service...${NC}"
aws ecs update-service \
    --cluster "$CLUSTER" \
    --service convoy-web \
    --force-new-deployment \
    --query 'service.serviceName' \
    --output text > /dev/null 2>&1 || echo -e "${YELLOW}  (convoy-web service may not exist yet)${NC}"

echo -e "${GREEN}  ✓ Deployment triggered${NC}"
echo ""

echo -e "${GREEN}==============================================================================${NC}"
echo -e "${GREEN}✓ Convoy Web deployment complete!${NC}"
echo -e "${GREEN}==============================================================================${NC}"
echo ""
echo "Image available in ECR:"
echo "  - ${ECR_PREFIX}/convoy/web:${IMAGE_TAG}"
echo ""
echo "Monitor deployment status:"
echo "  aws ecs describe-services --cluster $CLUSTER --services convoy-web --query 'services[*].{name:serviceName,status:status,running:runningCount,desired:desiredCount}' --output table"
echo ""
echo "View logs:"
echo "  aws logs tail /ecs/convoy-web --follow"
