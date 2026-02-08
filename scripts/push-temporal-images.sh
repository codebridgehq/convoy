#!/bin/bash
# =============================================================================
# Push Temporal Images to ECR
# =============================================================================
# This script pulls Temporal images from Docker Hub and pushes them to ECR.
# It explicitly pulls linux/amd64 images to ensure compatibility with ECS Fargate.
#
# Usage:
#   ./scripts/push-temporal-images.sh [--region REGION]
#
# Environment variables (optional):
#   AWS_REGION - AWS region (default: us-east-1)
#   TEMPORAL_VERSION - Temporal server version (default: 1.29.2)
#   TEMPORAL_ADMIN_TOOLS_VERSION - Admin tools version (default: 1.29)
#   TEMPORAL_UI_VERSION - Temporal UI version (default: 2.36.2)
# =============================================================================

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Default values (matching terraform/variables.tf)
REGION="${AWS_REGION:-us-east-1}"
TEMPORAL_VERSION="${TEMPORAL_VERSION:-1.29.2}"
TEMPORAL_ADMIN_TOOLS_VERSION="${TEMPORAL_ADMIN_TOOLS_VERSION:-1.29}"
TEMPORAL_UI_VERSION="${TEMPORAL_UI_VERSION:-2.36.2}"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --region)
            REGION="$2"
            shift 2
            ;;
        --temporal-version)
            TEMPORAL_VERSION="$2"
            shift 2
            ;;
        --admin-tools-version)
            TEMPORAL_ADMIN_TOOLS_VERSION="$2"
            shift 2
            ;;
        --ui-version)
            TEMPORAL_UI_VERSION="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [--region REGION] [--temporal-version VERSION] [--admin-tools-version VERSION] [--ui-version VERSION]"
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

echo -e "${GREEN}==============================================================================${NC}"
echo -e "${GREEN}Pushing Temporal Images to ECR${NC}"
echo -e "${GREEN}==============================================================================${NC}"
echo -e "AWS Account:    ${YELLOW}${ACCOUNT_ID}${NC}"
echo -e "Region:         ${YELLOW}${REGION}${NC}"
echo -e "ECR Prefix:     ${YELLOW}${ECR_PREFIX}${NC}"
echo -e "Temporal:       ${YELLOW}${TEMPORAL_VERSION}${NC}"
echo -e "Admin Tools:    ${YELLOW}${TEMPORAL_ADMIN_TOOLS_VERSION}${NC}"
echo -e "UI:             ${YELLOW}${TEMPORAL_UI_VERSION}${NC}"
echo -e "${GREEN}==============================================================================${NC}"
echo ""

# Login to ECR
echo -e "${YELLOW}Logging in to ECR...${NC}"
aws ecr get-login-password --region "$REGION" | docker login --username AWS --password-stdin "$ECR_PREFIX"
echo -e "${GREEN}✓ ECR login successful${NC}"
echo ""

# Function to pull, tag, and push an image
push_image() {
    local source_image=$1
    local target_image=$2
    
    echo -e "${YELLOW}Processing: ${source_image} -> ${target_image}${NC}"
    
    # Pull with explicit platform (important for Apple Silicon Macs)
    echo "  Pulling ${source_image} (linux/amd64)..."
    docker pull --platform linux/amd64 "$source_image"
    
    # Tag for ECR
    echo "  Tagging as ${target_image}..."
    docker tag "$source_image" "$target_image"
    
    # Push to ECR
    echo "  Pushing to ECR..."
    docker push "$target_image"
    
    echo -e "${GREEN}  ✓ Done${NC}"
    echo ""
}

# Push temporal/server
push_image \
    "temporalio/server:${TEMPORAL_VERSION}" \
    "${ECR_PREFIX}/temporal/server:${TEMPORAL_VERSION}"

# Push temporal/admin-tools
push_image \
    "temporalio/admin-tools:${TEMPORAL_ADMIN_TOOLS_VERSION}" \
    "${ECR_PREFIX}/temporal/admin-tools:${TEMPORAL_ADMIN_TOOLS_VERSION}"

# Push temporal/ui
push_image \
    "temporalio/ui:${TEMPORAL_UI_VERSION}" \
    "${ECR_PREFIX}/temporal/ui:${TEMPORAL_UI_VERSION}"

echo -e "${GREEN}==============================================================================${NC}"
echo -e "${GREEN}✓ All Temporal images pushed successfully!${NC}"
echo -e "${GREEN}==============================================================================${NC}"
echo ""
echo "Images available in ECR:"
echo "  - ${ECR_PREFIX}/temporal/server:${TEMPORAL_VERSION}"
echo "  - ${ECR_PREFIX}/temporal/admin-tools:${TEMPORAL_ADMIN_TOOLS_VERSION}"
echo "  - ${ECR_PREFIX}/temporal/ui:${TEMPORAL_UI_VERSION}"
