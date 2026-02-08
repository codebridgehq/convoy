#!/bin/bash
# =============================================================================
# Build and Push Convoy Images to ECR
# =============================================================================
# This script builds the convoy-api and convoy-worker Docker images and pushes
# them to ECR. It builds for linux/amd64 to ensure compatibility with ECS Fargate.
#
# Usage:
#   ./scripts/push-convoy-images.sh [--region REGION] [--tag TAG] [--api-only] [--worker-only]
#
# Environment variables (optional):
#   AWS_REGION - AWS region (default: us-east-1)
#   IMAGE_TAG - Image tag (default: latest)
# =============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values
REGION="${AWS_REGION:-us-east-1}"
IMAGE_TAG="${IMAGE_TAG:-latest}"
BUILD_API=true
BUILD_WORKER=true

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
        --api-only)
            BUILD_WORKER=false
            shift
            ;;
        --worker-only)
            BUILD_API=false
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--region REGION] [--tag TAG] [--api-only] [--worker-only]"
            echo ""
            echo "Options:"
            echo "  --region REGION    AWS region (default: us-east-1)"
            echo "  --tag TAG          Image tag (default: latest)"
            echo "  --api-only         Only build and push the API image"
            echo "  --worker-only      Only build and push the worker image"
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
CORE_DIR="${PROJECT_ROOT}/core"

echo -e "${GREEN}==============================================================================${NC}"
echo -e "${GREEN}Building and Pushing Convoy Images to ECR${NC}"
echo -e "${GREEN}==============================================================================${NC}"
echo -e "AWS Account:    ${YELLOW}${ACCOUNT_ID}${NC}"
echo -e "Region:         ${YELLOW}${REGION}${NC}"
echo -e "ECR Prefix:     ${YELLOW}${ECR_PREFIX}${NC}"
echo -e "Image Tag:      ${YELLOW}${IMAGE_TAG}${NC}"
echo -e "Build API:      ${YELLOW}${BUILD_API}${NC}"
echo -e "Build Worker:   ${YELLOW}${BUILD_WORKER}${NC}"
echo -e "${GREEN}==============================================================================${NC}"
echo ""

# Login to ECR
echo -e "${YELLOW}Logging in to ECR...${NC}"
aws ecr get-login-password --region "$REGION" | docker login --username AWS --password-stdin "$ECR_PREFIX"
echo -e "${GREEN}✓ ECR login successful${NC}"
echo ""

# Function to build and push an image
build_and_push() {
    local dockerfile=$1
    local target=$2
    local image_name=$3
    local full_image="${ECR_PREFIX}/${image_name}:${IMAGE_TAG}"
    
    echo -e "${YELLOW}Building: ${image_name}${NC}"
    echo "  Dockerfile: ${dockerfile}"
    echo "  Target: ${target}"
    echo "  Image: ${full_image}"
    echo ""
    
    # Build with explicit platform (important for Apple Silicon Macs)
    echo "  Building for linux/amd64..."
    docker build \
        --platform linux/amd64 \
        --file "${CORE_DIR}/${dockerfile}" \
        --target "${target}" \
        --tag "${full_image}" \
        "${CORE_DIR}"
    
    # Push to ECR
    echo "  Pushing to ECR..."
    docker push "${full_image}"
    
    echo -e "${GREEN}  ✓ Done${NC}"
    echo ""
}

# Build and push convoy-api
if [ "$BUILD_API" = true ]; then
    build_and_push "Dockerfile.api" "api_prod" "convoy/api"
fi

# Build and push convoy-worker
if [ "$BUILD_WORKER" = true ]; then
    build_and_push "Dockerfile.worker" "worker_prod" "convoy/worker"
fi

echo -e "${GREEN}==============================================================================${NC}"
echo -e "${GREEN}✓ All Convoy images built and pushed successfully!${NC}"
echo -e "${GREEN}==============================================================================${NC}"
echo ""
echo "Images available in ECR:"
if [ "$BUILD_API" = true ]; then
    echo "  - ${ECR_PREFIX}/convoy/api:${IMAGE_TAG}"
fi
if [ "$BUILD_WORKER" = true ]; then
    echo "  - ${ECR_PREFIX}/convoy/worker:${IMAGE_TAG}"
fi
echo ""
echo "To deploy to ECS, update the service:"
if [ "$BUILD_API" = true ]; then
    echo "  aws ecs update-service --cluster convoy-dev --service convoy-api --force-new-deployment"
fi
if [ "$BUILD_WORKER" = true ]; then
    echo "  aws ecs update-service --cluster convoy-dev --service convoy-worker --force-new-deployment"
fi
