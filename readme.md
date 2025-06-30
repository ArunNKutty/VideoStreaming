# 🎬 HLS Video Streaming Platform

A comprehensive video infrastructure platform similar to Mux.com, featuring HLS video streaming with upload and playback capabilities.

## 🚀 Features

### Video Infrastructure
- **HLS Video Streaming**: Efficient video streaming using HLS protocol
- **Video Player**: HLS.js integration with adaptive bitrate streaming
- **Video Upload & Processing**: Support for video file uploads and HLS conversion
- **FastAPI Backend**: High-performance Python server with automatic API documentation

### Frontend
- **TypeScript React App**: Modern, type-safe frontend application
- **Responsive Design**: Mobile-friendly interface
- **Video Player Interface**: Clean and intuitive video playback experience

## 📋 Prerequisites

- **Python 3.8+** with pip
- **Node.js** (v16 or higher) and **npm**
- **FFmpeg** (for video processing)
- **Docker** (optional, for containerized deployment)

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/ArunNKutty/VideoStreaming.git
cd VideoStreaming
```

### 2. Backend Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Set up environment variables (optional)
cp .env.example .env

# Start the FastAPI server
python main.py
```

### 3. Frontend Setup
```bash
# Navigate to frontend directory
cd react-hls-player

# Install dependencies
npm install

# Start the React development server
npm start
```

### 4. Access the Application
- **React App**: http://localhost:3000
- **API Server**: http://localhost:8080
- **API Documentation**: http://localhost:8080/docs



## 📁 Project Structure

```
VideoStreaming/
├── main.py                    # FastAPI server entry point
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
├── app/                      # Backend application
│   ├── __init__.py
│   ├── main.py              # FastAPI app configuration
│   ├── core/                # Core configuration
│   │   ├── config.py        # Settings and configuration
│   │   └── __init__.py
│   ├── models/              # Pydantic models
│   │   ├── video.py         # Video-related models
│   │   └── __init__.py
│   ├── services/            # Business logic
│   │   ├── video_service.py # Video processing
│   │   └── __init__.py
│   └── api/                 # API routes
│       ├── routes/
│       │   ├── video.py     # Video endpoints
│       │   ├── health.py    # Health check
│       │   └── __init__.py
│       └── __init__.py
├── videos/                  # HLS video files
│   └── [video-id]/
│       ├── index.m3u8      # HLS playlist
│       └── *.ts            # Video segments
└── react-hls-player/       # TypeScript React frontend
    ├── src/
    │   ├── App.tsx          # Main application
    │   ├── index.tsx        # Entry point
    │   ├── components/      # React components
    │   │   ├── HLSPlayer.tsx      # Video player
    │   │   └── *.css        # Component styles
    │   └── types/           # TypeScript definitions
    │       ├── api.ts       # API response types
    │       └── hls.d.ts     # HLS.js type definitions
    ├── public/
    ├── package.json
    ├── tsconfig.json        # TypeScript configuration
    └── package-lock.json
```

## 🔧 API Endpoints

### Core Endpoints
- `GET /api/v1/health` - Health check
- `GET /docs` - Interactive API documentation
- `GET /redoc` - Alternative API documentation

### Video Endpoints
- `GET /api/v1/videos` - List all videos
- `POST /api/v1/videos/upload` - Upload video file
- `GET /api/v1/videos/{video_id}` - Get video details
- `GET /api/v1/videos/{video_id}/player` - Video player page
- `GET /api/v1/videos/{video_id}/hls` - HLS playlist
- `GET /api/v1/videos/{video_id}/thumbnail` - Video thumbnail



## 🎥 Using the Video Player

1. **Start both servers** (backend on :8080, frontend on :3000)
2. **Open the React app** at http://localhost:3000
3. **Enter a video ID** that exists in the `/videos/` directory
4. **Click play** to start streaming

## 🚀 Deployment

### Using Docker (Recommended)
```bash
# Build and run
docker build -t hls-server .
docker run -p 8000:8000 hls-server
```

### Using Docker Compose (Optional)
Create a `docker-compose.yml` for multi-service deployment:
```yaml
version: '3.8'
services:
  backend:
    build: .
    ports:
      - "8000:8000"
  frontend:
    build: ./react-hls-player
    ports:
      - "3000:3000"
    depends_on:
      - backend
```

## 🔍 Troubleshooting

### Common Issues

1. **Port Already in Use**
   ```bash
   # Check what's using the port
   lsof -i :8000
   # Kill the process or use a different port
   ```

2. **CORS Issues**
   - Ensure the backend CORS settings allow your frontend domain
   - Check browser console for CORS errors

3. **Video Not Playing**
   - Verify video files exist in `/videos/[video-id]/`
   - Check HLS playlist format (`.m3u8`)
   - Ensure video segments (`.ts` files) are accessible

4. **Docker Build Issues**
   ```bash
   # Clean Docker cache
   docker system prune -a
   # Rebuild without cache
   docker build --no-cache -t hls-server .
   ```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is open source and available under the [MIT License](LICENSE).

## 🆘 Support

If you encounter any issues or have questions:
1. Check the troubleshooting section above
2. Review the API documentation at `/docs`
3. Open an issue on GitHub

---

**Happy Streaming! 🎬**