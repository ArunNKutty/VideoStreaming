#!/usr/bin/env python3
"""
Setup script for Mux Clone Video Infrastructure Platform
This script helps set up the development environment and initial configuration
"""

import os
import sys
import subprocess
import json
import uuid
from pathlib import Path

def run_command(command, check=True):
    """Run a shell command and return the result"""
    print(f"Running: {command}")
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if check and result.returncode != 0:
        print(f"Error running command: {command}")
        print(f"Error output: {result.stderr}")
        sys.exit(1)
    
    return result

def create_directory_structure():
    """Create the necessary directory structure"""
    directories = [
        "uploads",
        "videos",
        "logs",
        "config",
        "scripts",
        "tests",
        "docs",
        "migrations",
        "workers",
        "monitoring"
    ]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"Created directory: {directory}")

def create_env_file():
    """Create environment configuration file"""
    env_content = f"""# Video Infrastructure Platform Configuration

# Database Configuration
DATABASE_URL=postgresql://videouser:videopass@localhost:5432/videoplatform
DATABASE_TEST_URL=postgresql://videouser:videopass@localhost:5432/videoplatform_test

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_CACHE_URL=redis://localhost:6379/1

# API Configuration
API_SECRET_KEY={uuid.uuid4().hex}
API_ACCESS_TOKEN_EXPIRE_MINUTES=30
API_ALGORITHM=HS256

# File Storage Configuration
UPLOAD_DIR=uploads
VIDEO_DIR=videos
MAX_FILE_SIZE=1073741824  # 1GB in bytes
ALLOWED_VIDEO_TYPES=mp4,avi,mov,mkv,webm,flv

# FFmpeg Configuration
FFMPEG_PATH=ffmpeg
FFPROBE_PATH=ffprobe

# CDN Configuration (optional)
CDN_ENABLED=false
CDN_BASE_URL=https://your-cdn.com
CDN_API_KEY=your-cdn-api-key

# Cloud Storage (choose one)
# AWS S3
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_BUCKET_NAME=your-video-bucket
AWS_REGION=us-east-1

# Google Cloud Storage
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_BUCKET=your-video-bucket
GOOGLE_APPLICATION_CREDENTIALS=path/to/service-account.json

# Azure Blob Storage
AZURE_STORAGE_CONNECTION_STRING=your-connection-string
AZURE_CONTAINER_NAME=your-container

# Monitoring and Analytics
SENTRY_DSN=your-sentry-dsn
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=8001

# Email Configuration (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_TLS=true

# Development Settings
DEBUG=true
LOG_LEVEL=INFO
CORS_ORIGINS=["http://localhost:3000", "http://localhost:3001"]

# Production Settings (uncomment for production)
# DEBUG=false
# LOG_LEVEL=WARNING
# CORS_ORIGINS=["https://yourdomain.com"]

# Worker Configuration
CELERY_BROKER_URL=redis://localhost:6379/2
CELERY_RESULT_BACKEND=redis://localhost:6379/3
CELERY_WORKER_CONCURRENCY=4

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600  # 1 hour in seconds

# Transcoding Settings
TRANSCODING_PROFILES=720p,480p,360p
HLS_SEGMENT_DURATION=10
HLS_PLAYLIST_TYPE=vod

# Analytics Settings
ANALYTICS_RETENTION_DAYS=90
ANALYTICS_BATCH_SIZE=1000
"""

    with open('.env', 'w') as f:
        f.write(env_content)
    
    print("Created .env file with default configuration")

def create_docker_compose():
    """Create Docker Compose file for development"""
    docker_compose_content = """version: '3.8'

services:
  # Main API service
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://videouser:videopass@db:5432/videoplatform
      - REDIS_URL=redis://redis:6379/0
    volumes:
      - ./uploads:/app/uploads
      - ./videos:/app/videos
      - ./logs:/app/logs
    depends_on:
      - db
      - redis
    restart: unless-stopped

  # Background worker for video processing
  worker:
    build: .
    command: python -m celery worker -A workers.celery_app --loglevel=info
    environment:
      - DATABASE_URL=postgresql://videouser:videopass@db:5432/videoplatform
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/2
    volumes:
      - ./uploads:/app/uploads
      - ./videos:/app/videos
      - ./logs:/app/logs
    depends_on:
      - db
      - redis
    restart: unless-stopped

  # PostgreSQL database
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: videoplatform
      POSTGRES_USER: videouser
      POSTGRES_PASSWORD: videopass
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    restart: unless-stopped

  # Redis for caching and job queues
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  # Prometheus for monitoring
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    restart: unless-stopped

  # Grafana for dashboards
  grafana:
    image: grafana/grafana:latest
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana:/etc/grafana/provisioning
    restart: unless-stopped

  # MinIO for local S3-compatible storage (development)
  minio:
    image: minio/minio:latest
    ports:
      - "9000:9000"
      - "9001:9001"
    environment:
      MINIO_ROOT_USER: minioadmin
      MINIO_ROOT_PASSWORD: minioadmin
    volumes:
      - minio_data:/data
    command: server /data --console-address ":9001"
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  prometheus_data:
  grafana_data:
  minio_data:
"""

    with open('docker-compose.yml', 'w') as f:
        f.write(docker_compose_content)
    
    print("Created docker-compose.yml for development environment")

def create_dockerfile():
    """Create Dockerfile for the application"""
    dockerfile_content = """FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    ffmpeg \\
    libpq-dev \\
    gcc \\
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY enhanced_requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p uploads videos logs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "enhanced_main:app", "--host", "0.0.0.0", "--port", "8000"]
"""

    with open('Dockerfile', 'w') as f:
        f.write(dockerfile_content)
    
    print("Created Dockerfile")

def create_init_script():
    """Create database initialization script"""
    init_sql = """-- Initialize video platform database

-- Create extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create accounts table
CREATE TABLE IF NOT EXISTS accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    api_key VARCHAR(255) UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create video_assets table
CREATE TABLE IF NOT EXISTS video_assets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_id UUID REFERENCES accounts(id) ON DELETE CASCADE,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255),
    file_size BIGINT,
    duration FLOAT,
    width INTEGER,
    height INTEGER,
    bitrate INTEGER,
    codec VARCHAR(50),
    status VARCHAR(50) DEFAULT 'uploading',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create transcoding_jobs table
CREATE TABLE IF NOT EXISTS transcoding_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id UUID REFERENCES video_assets(id) ON DELETE CASCADE,
    profile VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'queued',
    progress INTEGER DEFAULT 0,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create playback_sessions table
CREATE TABLE IF NOT EXISTS playback_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_id UUID REFERENCES video_assets(id) ON DELETE CASCADE,
    viewer_id VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    country VARCHAR(2),
    started_at TIMESTAMP DEFAULT NOW(),
    ended_at TIMESTAMP,
    total_watch_time INTEGER DEFAULT 0,
    max_concurrent_viewers INTEGER DEFAULT 1
);

-- Create analytics_events table
CREATE TABLE IF NOT EXISTS analytics_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES playback_sessions(id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW(),
    data JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_video_assets_account_id ON video_assets(account_id);
CREATE INDEX IF NOT EXISTS idx_video_assets_status ON video_assets(status);
CREATE INDEX IF NOT EXISTS idx_transcoding_jobs_asset_id ON transcoding_jobs(asset_id);
CREATE INDEX IF NOT EXISTS idx_transcoding_jobs_status ON transcoding_jobs(status);
CREATE INDEX IF NOT EXISTS idx_playback_sessions_asset_id ON playback_sessions(asset_id);
CREATE INDEX IF NOT EXISTS idx_analytics_events_session_id ON analytics_events(session_id);
CREATE INDEX IF NOT EXISTS idx_analytics_events_event_type ON analytics_events(event_type);
CREATE INDEX IF NOT EXISTS idx_analytics_events_timestamp ON analytics_events(timestamp);

-- Insert default admin account
INSERT INTO accounts (name, email, api_key) 
VALUES ('Admin', 'admin@example.com', 'dev-api-key-12345')
ON CONFLICT (email) DO NOTHING;
"""

    os.makedirs('scripts', exist_ok=True)
    with open('scripts/init.sql', 'w') as f:
        f.write(init_sql)
    
    print("Created database initialization script")

def create_monitoring_config():
    """Create monitoring configuration files"""
    os.makedirs('monitoring', exist_ok=True)
    
    # Prometheus configuration
    prometheus_config = """global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'video-platform-api'
    static_configs:
      - targets: ['api:8000']
    metrics_path: '/metrics'
    scrape_interval: 5s

  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
"""

    with open('monitoring/prometheus.yml', 'w') as f:
        f.write(prometheus_config)
    
    print("Created monitoring configuration")

def main():
    """Main setup function"""
    print("🚀 Setting up Mux Clone Video Infrastructure Platform")
    print("=" * 60)
    
    # Check if FFmpeg is installed
    try:
        run_command("ffmpeg -version", check=False)
        print("✅ FFmpeg is installed")
    except:
        print("⚠️  FFmpeg not found. Please install FFmpeg:")
        print("   - macOS: brew install ffmpeg")
        print("   - Ubuntu: sudo apt install ffmpeg")
        print("   - Windows: Download from https://ffmpeg.org/")
    
    # Create directory structure
    print("\\n📁 Creating directory structure...")
    create_directory_structure()
    
    # Create configuration files
    print("\\n⚙️  Creating configuration files...")
    create_env_file()
    create_docker_compose()
    create_dockerfile()
    create_init_script()
    create_monitoring_config()
    
    # Create .gitignore
    gitignore_content = """# Environment variables
.env
.env.local
.env.production

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/

# Uploads and videos
uploads/
videos/
logs/

# Database
*.db
*.sqlite3

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Docker
.dockerignore

# Node modules (for frontend)
node_modules/

# Build artifacts
build/
dist/
"""

    with open('.gitignore', 'w') as f:
        f.write(gitignore_content)
    
    print("\\n✅ Setup completed successfully!")
    print("\\n🎯 Next steps:")
    print("1. Install Python dependencies: pip install -r enhanced_requirements.txt")
    print("2. Start services: docker-compose up -d")
    print("3. Run the API: python enhanced_main.py")
    print("4. Access the API docs: http://localhost:8000/docs")
    print("5. Set up the React frontend in the react-hls-player directory")
    print("\\n📚 Documentation:")
    print("- API Documentation: http://localhost:8000/docs")
    print("- Monitoring: http://localhost:9090 (Prometheus)")
    print("- Dashboards: http://localhost:3001 (Grafana)")
    print("- Object Storage: http://localhost:9001 (MinIO)")

if __name__ == "__main__":
    main()
