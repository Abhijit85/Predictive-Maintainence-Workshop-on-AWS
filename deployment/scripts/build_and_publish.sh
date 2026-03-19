#!/bin/sh

export AWS_ACCESS_KEY_ID=$2
export AWS_SECRET_ACCESS_KEY=$3
export AWS_SESSION_TOKEN=$4

set -e 

# Private ECR
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REGISTRY="$AWS_ACCOUNT_ID.dkr.ecr.$1.amazonaws.com"

# Login to private ECR
aws ecr get-login-password --region $1 | docker login --username AWS --password-stdin $ECR_REGISTRY

IMAGE_TAG="$ECR_REGISTRY/pred-maint-aws-mongodb:latest"

# Build and push multi-platform image
echo "Building and pushing multi-platform image for $PLATFORMS: $IMAGE_TAG"
docker build --platform linux/amd64 -f ../Dockerfile -t "$IMAGE_TAG" ../
docker push "$IMAGE_TAG"

echo "Image pushed successfully!"

unset AWS_ACCESS_KEY_ID
unset AWS_SECRET_ACCESS_KEY
unset AWS_SESSION_TOKEN