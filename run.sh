#!/bin/bash

# HLS Video Server - Docker Run Script
# Runs the container with environment variables from .env file

set -e

# Load environment variables from .env file
if [ -f .env ]; then
    echo "📄 Loading environment variables from .env file..."
    export $(grep -v '^#' .env | grep -v '^$' | xargs)
    echo "✅ Environment variables loaded"
else
    echo "❌ No .env file found. Please create one with your AWS credentials."
    echo "Example .env file:"
    echo "AWS_ACCESS_KEY_ID=your_aws_key"
    echo "AWS_SECRET_ACCESS_KEY=your_aws_secret"
    echo "AWS_REGION=us-east-2"
    echo "S3_BUCKET_NAME=cogito-videos"
    echo "PORT=8080"
    echo "DEBUG=false"
    exit 1
fi

# Container configuration
IMAGE_NAME="hls-server:latest"
CONTAINER_NAME="hls-video-server"
HOST_PORT="${PORT:-8080}"
CONTAINER_PORT="${PORT:-8080}"

echo "🚀 Starting HLS Video Server container..."
echo "📡 Port mapping: ${HOST_PORT}:${CONTAINER_PORT}"
echo "🪣 S3 Bucket: ${S3_BUCKET_NAME:-cogito-videos}"
echo "🌍 AWS Region: ${AWS_REGION:-us-east-2}"

# Stop existing container if running
if [ "$(docker ps -q -f name=${CONTAINER_NAME})" ]; then
    echo "🛑 Stopping existing container..."
    docker stop ${CONTAINER_NAME}
fi

# Remove existing container if exists
if [ "$(docker ps -aq -f name=${CONTAINER_NAME})" ]; then
    echo "🗑️  Removing existing container..."
    docker rm ${CONTAINER_NAME}
fi

# Run the container with environment variables
docker run -d \
    --name ${CONTAINER_NAME} \
    -p ${HOST_PORT}:${CONTAINER_PORT} \
    -e AWS_ACCESS_KEY_ID="${AWS_ACCESS_KEY_ID}" \
    -e AWS_SECRET_ACCESS_KEY="${AWS_SECRET_ACCESS_KEY}" \
    -e AWS_REGION="${AWS_REGION:-us-east-2}" \
    -e S3_BUCKET_NAME="${S3_BUCKET_NAME:-cogito-videos}" \
    -e DEBUG="${DEBUG:-false}" \
    -e LOG_LEVEL="${LOG_LEVEL:-INFO}" \
    --restart unless-stopped \
    ${IMAGE_NAME}

echo "✅ Container started successfully!"
echo ""
echo "🌐 Access the application:"
echo "  • API Server: http://localhost:${HOST_PORT}"
echo "  • API Docs: http://localhost:${HOST_PORT}/docs"
echo "  • Health Check: http://localhost:${HOST_PORT}/health"
echo ""
echo "📊 Container status:"
docker ps --filter name=${CONTAINER_NAME} --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""
echo "📝 To view logs:"
echo "docker logs -f ${CONTAINER_NAME}"
echo ""
echo "🛑 To stop the container:"
echo "docker stop ${CONTAINER_NAME}"
