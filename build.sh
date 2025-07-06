#!/bin/bash

# HLS Video Server - Optimized Docker Build Script
# Multi-stage build for production deployment

set -e

echo "🐳 Building HLS Video Server with Multi-Stage Docker..."

# Load environment variables from .env file
if [ -f .env ]; then
    echo "📄 Loading environment variables from .env file..."
    export $(grep -v '^#' .env | grep -v '^$' | xargs)
    echo "✅ Environment variables loaded"
else
    echo "⚠️  No .env file found. Using default values."
fi

# Build arguments
IMAGE_NAME="hls-server"
TAG="${1:-latest}"
FULL_IMAGE_NAME="${IMAGE_NAME}:${TAG}"

echo "📦 Building image: ${FULL_IMAGE_NAME}"

# Build with BuildKit for better performance
export DOCKER_BUILDKIT=1

# Build the multi-stage image
docker build \
    --tag "${FULL_IMAGE_NAME}" \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    --progress=plain \
    .

echo "✅ Build completed successfully!"

# Show image size
echo "📊 Image size:"
docker images "${IMAGE_NAME}" --format "table {{.Repository}}\t{{.Tag}}\t{{.Size}}\t{{.CreatedAt}}"

echo ""
echo "🚀 To run the container with .env values:"

# Check if required AWS variables are set
if [ -n "$AWS_ACCESS_KEY_ID" ] && [ -n "$AWS_SECRET_ACCESS_KEY" ]; then
    echo "docker run -p ${PORT:-8080}:${PORT:-8080} \\"
    echo "  -e AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID} \\"
    echo "  -e AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY} \\"
    echo "  -e AWS_REGION=${AWS_REGION:-us-east-2} \\"
    echo "  -e S3_BUCKET_NAME=${S3_BUCKET_NAME:-cogito-videos} \\"
    echo "  -e DEBUG=${DEBUG:-false} \\"
    echo "  ${FULL_IMAGE_NAME}"

    echo ""
    echo "🎬 Or run directly with loaded environment:"
    echo "./run.sh"
else
    echo "⚠️  AWS credentials not found in .env file"
    echo "docker run -p ${PORT:-8080}:${PORT:-8080} \\"
    echo "  -e AWS_ACCESS_KEY_ID=your_aws_key \\"
    echo "  -e AWS_SECRET_ACCESS_KEY=your_aws_secret \\"
    echo "  -e AWS_REGION=us-east-2 \\"
    echo "  -e S3_BUCKET_NAME=cogito-videos \\"
    echo "  ${FULL_IMAGE_NAME}"
fi

echo ""
echo "🔍 To inspect the image:"
echo "docker run --rm -it ${FULL_IMAGE_NAME} /bin/bash"
