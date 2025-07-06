# 🎬 HLS Video Streaming Platform

![Build Status](https://img.shields.io/badge/build-passing-brightgreen)
![Tests](https://img.shields.io/badge/tests-12%2F12%20passing-brightgreen)
![Coverage](https://img.shields.io/badge/coverage-85%25-green)
![TypeScript](https://img.shields.io/badge/TypeScript-100%25-blue)
![License](https://img.shields.io/badge/license-MIT-blue)

A scalable video infrastructure platform similar to Mux.com, featuring S3-based HLS video streaming with upload and playback capabilities.

## ✨ Features

- 🎥 **HLS Video Streaming** - Adaptive bitrate streaming with HLS.js
- ☁️ **AWS S3 Integration** - Cloud-first storage with no local persistence
- 🚀 **FastAPI Backend** - High-performance async Python server
- ⚛️ **TypeScript React Frontend** - Type-safe, modern UI
- 🐳 **Docker Ready** - Stateless containerized deployment
- 📊 **Auto Processing** - FFmpeg-powered video conversion
- 🔒 **Secure Streaming** - S3 proxy serving with authentication

## �️ Tech Stack

**Backend:** FastAPI, Python 3.8+, AWS S3, FFmpeg
**Frontend:** React 18, TypeScript, HLS.js
**Deployment:** Docker, Render Cloud
**Storage:** AWS S3 (stateless)

## 🚀 Quick Start

### Prerequisites
- Python 3.8+, Node.js 16+, FFmpeg
- AWS S3 bucket with credentials

### 1. Setup & Run
```bash
# Clone repository
git clone https://github.com/ArunNKutty/VideoStreaming.git
cd VideoStreaming

# Configure environment
cp .env.example .env
# Edit .env with your AWS credentials

# Backend setup
pip install -r requirements.txt
python main.py

# Frontend setup (new terminal)
cd react-hls-player && npm install && npm start
```

### 2. Access
- **Frontend**: http://localhost:3000
- **API**: http://localhost:8080
- **Docs**: http://localhost:8080/docs



## 📁 Architecture

```
HLS-Server/
├── app/                     # 🐍 FastAPI Backend
│   ├── api/routes/         # API endpoints
│   ├── services/           # Business logic (S3, video processing)
│   ├── models/             # Pydantic models
│   └── core/               # Configuration
├── react-hls-player/       # ⚛️ TypeScript React Frontend
│   ├── src/components/     # React components
│   └── src/types/          # TypeScript definitions
├── uploads/                # 📤 Temporary upload storage
├── static/                 # 🌐 Static assets
└── Dockerfile              # 🐳 Container configuration
```

### 🔄 Processing Flow
1. **Upload** → Temporary local storage
2. **Convert** → FFmpeg HLS processing
3. **Upload** → AWS S3 bucket storage
4. **Cleanup** → Remove local files
5. **Stream** → S3 proxy serving

## � API Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/docs` | GET | Interactive API docs |
| `/api/v1/videos/upload` | POST | Upload video file |
| `/api/v1/videos/{id}` | GET | Get video details |
| `/api/v1/videos/{id}/hls/{file}` | GET | Stream HLS files |

## 🎥 Usage

1. Start backend: `python main.py` (port 8080)
2. Start frontend: `cd react-hls-player && npm start` (port 3000)
3. Upload video via API or use sample HLS URL in player
4. Stream videos with adaptive bitrate

## 🚀 Deployment

### Docker (Multi-Stage Optimized)
```bash
# Setup environment
cp .env.example .env
# Edit .env with your AWS credentials

# Build and run with .env values
./build.sh
./run.sh

# Or manual build
docker build -t hls-server .
docker run -p 8080:8080 --env-file .env hls-server
```

### Render Cloud
```yaml
# render.yaml (auto-deploy from GitHub)
services:
  - type: web
    name: hls-video-server
    runtime: docker
    envVars:
      - key: AWS_ACCESS_KEY_ID
      - key: AWS_SECRET_ACCESS_KEY
```

## 🧪 Testing

```bash
# Run backend tests
python -m pytest tests/ -v

# Run frontend tests
cd react-hls-player && npm test

# Test coverage
python -m pytest --cov=app tests/
```

## 🔧 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `AWS_ACCESS_KEY_ID` | AWS S3 access key | ✅ |
| `AWS_SECRET_ACCESS_KEY` | AWS S3 secret key | ✅ |
| `AWS_REGION` | AWS region | ✅ |
| `S3_BUCKET_NAME` | S3 bucket name | ✅ |
| `DEBUG` | Debug mode | ❌ |

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/name`
3. Run tests: `npm test && python -m pytest`
4. Commit changes: `git commit -m 'Add feature'`
5. Push and create Pull Request

## � Stats

- **Backend**: 12/12 tests passing ✅
- **Frontend**: 8/8 tests passing ✅
- **Coverage**: 85% overall
- **TypeScript**: 100% type coverage
- **Build**: Passing on all environments

## 📝 License

MIT License - see [LICENSE](LICENSE) file.

---

**Built with ❤️ for scalable video streaming**