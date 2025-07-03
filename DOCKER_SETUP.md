# Docker Setup for HLS Video Streaming Platform

This document explains how to run the HLS video streaming platform using Docker with persistent storage.

## 🐳 Docker Architecture

The platform uses a **dual-storage approach**:
1. **S3 Storage**: Primary cloud storage for scalability
2. **Persistent Local Directories**: Docker volumes for local persistence and fallback

## 📁 Directory Structure

```
/app/persistent/
├── hls/           # HLS files (playlists and segments) mapped to Docker volume
│   └── {video_id}/
│       ├── index.m3u8
│       └── *.ts
└── videos/        # Original video files mapped to Docker volume

./docker-volumes/  # Host directories (created automatically)
├── hls/           # Persistent HLS files
├── videos/        # Persistent video files  
├── local-videos/  # Local fallback storage
├── uploads/       # Temporary upload directory
└── static/        # Static assets
```

## 🚀 Quick Start

### 1. Using Docker Compose (Recommended)

```bash
# Clone the repository
git clone <repository-url>
cd HLS-Server

# Set AWS credentials (optional - will fallback to local storage)
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key

# Start all services
docker-compose up -d

# View logs
docker-compose logs -f hls-server
```

### 2. Using Docker Build

```bash
# Build the image
docker build -t hls-server .

# Run with volume mapping
docker run -d \
  --name hls-server \
  -p 8080:8080 \
  -v $(pwd)/docker-volumes/hls:/app/persistent/hls \
  -v $(pwd)/docker-volumes/videos:/app/persistent/videos \
  -v $(pwd)/docker-volumes/local-videos:/app/videos \
  -v $(pwd)/docker-volumes/uploads:/app/uploads \
  -e AWS_ACCESS_KEY_ID=your_access_key \
  -e AWS_SECRET_ACCESS_KEY=your_secret_key \
  hls-server
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `AWS_ACCESS_KEY_ID` | AWS S3 access key | - |
| `AWS_SECRET_ACCESS_KEY` | AWS S3 secret key | - |
| `AWS_REGION` | AWS S3 region | `us-east-2` |
| `S3_BUCKET_NAME` | S3 bucket name | `cogito-videos` |
| `DEBUG` | Enable debug mode | `true` |

### Volume Mappings

| Container Path | Host Path | Purpose |
|----------------|-----------|---------|
| `/app/persistent/hls` | `./docker-volumes/hls` | HLS files (persistent) |
| `/app/persistent/videos` | `./docker-volumes/videos` | Video files (persistent) |
| `/app/videos` | `./docker-volumes/local-videos` | Local fallback storage |
| `/app/uploads` | `./docker-volumes/uploads` | Temporary uploads |

## 📊 Storage Strategy

### File Storage Priority:
1. **S3 Upload**: Files uploaded to AWS S3 (if configured)
2. **Persistent Directories**: Files always saved to `/app/persistent/` (Docker volumes)
3. **Local Fallback**: Traditional local storage in `/app/videos/`

### File Serving Priority:
1. **S3 Proxy**: Serve from S3 through API proxy (if available)
2. **Persistent Files**: Serve from persistent directories
3. **Local Files**: Serve from local fallback storage

## 🎯 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `POST /api/v1/upload` | POST | Upload video file |
| `GET /api/v1/videos/{id}` | GET | Get video information |
| `GET /api/v1/videos/{id}/hls/index.m3u8` | GET | HLS playlist |
| `GET /api/v1/videos/{id}/hls/{file}` | GET | HLS segments |
| `GET /api/v1/videos/{id}/player` | GET | Built-in video player |

## 🧪 Testing

### 1. Upload a video:
```bash
curl -X POST "http://localhost:8080/api/v1/upload" \
  -F "file=@your_video.mp4"
```

### 2. Get video info:
```bash
curl "http://localhost:8080/api/v1/videos/{VIDEO_ID}"
```

### 3. Play HLS stream:
```bash
# Direct HLS URL
http://localhost:8080/api/v1/videos/{VIDEO_ID}/hls/index.m3u8

# Built-in player
http://localhost:8080/api/v1/videos/{VIDEO_ID}/player

# React frontend
http://localhost:8081
```

## 🔍 Monitoring

### Check container health:
```bash
docker-compose ps
docker-compose logs hls-server
```

### Check persistent storage:
```bash
ls -la docker-volumes/hls/
ls -la docker-volumes/videos/
```

### Check S3 integration:
```bash
docker-compose exec hls-server curl http://localhost:8080/health
```

## 🛠 Troubleshooting

### Common Issues:

1. **Permission Issues**:
   ```bash
   sudo chown -R $USER:$USER docker-volumes/
   ```

2. **S3 Access Denied**:
   - Files will fallback to persistent directories
   - Check AWS credentials and bucket permissions

3. **FFmpeg Not Found**:
   - Rebuild Docker image to ensure FFmpeg is installed

4. **Port Conflicts**:
   - Change ports in docker-compose.yml if 8080/8081 are in use

## 🔒 Security Notes

- Files in persistent directories are accessible to the container user
- S3 files remain private and are served through API proxy
- Use proper AWS IAM policies for S3 access
- Consider using Docker secrets for production AWS credentials

## 📈 Scaling

For production scaling:
1. Use external storage (AWS EFS, NFS) for persistent volumes
2. Deploy multiple container instances behind a load balancer
3. Use Redis for session management
4. Implement proper logging and monitoring
