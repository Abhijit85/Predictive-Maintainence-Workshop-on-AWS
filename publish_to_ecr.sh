#!/bin/sh

# Optional: export AWS credentials if needed
# export AWS_ACCESS_KEY_ID=""
# export AWS_SECRET_ACCESS_KEY=""
# export AWS_SESSION_TOKEN=""

# Configuration
AWS_REGION=""        # Set for private ECR usage
USE_PUBLIC_ECR=true  # Set to true if you want to push to public ECR
PLATFORMS="linux/amd64,linux/arm64"  # Multi-platform build

# Ensure Docker Buildx is enabled for multi-platform builds
docker buildx create --use || echo "Buildx already enabled"

if [ "$USE_PUBLIC_ECR" = true ]; then
    # Public ECR
    ECR_REGISTRY="public.ecr.aws/your-public-repo-prefix"  # Replace with your public repo prefix

    # Login to public ECR
    aws ecr-public get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ECR_REGISTRY

    IMAGE_TAG="$ECR_REGISTRY/pred-maint-aws-mongodb:latest"
else
    # Private ECR
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    ECR_REGISTRY="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

    # Login to private ECR
    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REGISTRY

    IMAGE_TAG="$ECR_REGISTRY/pred-maint-aws-mongodb:latest"
fi

# Build and push multi-platform image
echo "Building and pushing multi-platform image for $PLATFORMS: $IMAGE_TAG"
docker buildx build --platform $PLATFORMS . --tag "$IMAGE_TAG" --push

echo "Image pushed successfully!"
