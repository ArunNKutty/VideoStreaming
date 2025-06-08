# HLS Video Streaming Server

A complete HLS (HTTP Live Streaming) video streaming solution with a Python FastAPI backend and React frontend player.

## 🚀 Features

- **HLS Video Streaming**: Efficient video streaming using HLS protocol
- **FastAPI Backend**: High-performance Python server with automatic API documentation
- **React Frontend**: Modern video player with HLS.js integration
- **Docker Support**: Containerized deployment for easy setup
- **CORS Enabled**: Cross-origin resource sharing for frontend-backend communication
- **Video Upload**: Support for video file uploads and HLS conversion

## 📋 Prerequisites

- **Docker** (for containerized deployment)
- **Node.js** (v14 or higher) and **npm** (for frontend development)
- **Python 3.8+** (for local development without Docker)

## 🐳 Quick Start with Docker

### 1. Clone the Repository
```bash
git clone https://github.com/ArunNKutty/VideoStreaming.git
cd VideoStreaming
```

### 2. Build and Run the Docker Container
```bash
# Build the Docker image
docker build -t hls-server .

# Run the container
docker run -p 8000:8000 hls-server
```

### 3. Access the Server
- **API Server**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 🖥️ Frontend Setup (React HLS Player)

### 1. Navigate to Frontend Directory
```bash
cd react-hls-player
```

### 2. Install Dependencies
```bash
npm install
```

### 3. Start the Development Server
```bash
npm start
```

### 4. Access the Frontend
- **React App**: http://localhost:3000

## 🛠️ Local Development (Without Docker)

### Backend Setup

1. **Install Python Dependencies**
```bash
pip install -r requirements.txt
```

2. **Run the FastAPI Server**
```bash
python main.py
```

The server will start on http://localhost:8000

### Frontend Setup

1. **Navigate to Frontend Directory**
```bash
cd react-hls-player
```

2. **Install Dependencies**
```bash
npm install
```

3. **Start Development Server**
```bash
npm start
```

## 📁 Project Structure

```
VideoStreaming/
├── main.py                 # FastAPI server
├── Dockerfile             # Docker configuration
├── requirements.txt       # Python dependencies
├── readme.md             # This file
├── videos/               # HLS video files directory
│   ├── [video-id]/
│   │   ├── index.m3u8   # HLS playlist
│   │   └── *.ts         # Video segments
├── react-hls-player/     # React frontend
│   ├── src/
│   │   ├── App.js
│   │   ├── components/
│   │   │   └── HLSPlayer.js
│   │   └── index.js
│   ├── public/
│   ├── package.json
│   └── package-lock.json
└── terminal_commands*.sh  # Deployment scripts
```

## 🔧 API Endpoints

### Main Endpoints
- `GET /` - Welcome message
- `GET /health` - Health check
- `GET /docs` - Interactive API documentation
- `GET /videos/{video_id}/index.m3u8` - HLS playlist
- `GET /videos/{video_id}/{segment}` - Video segments

### Video Management
- Upload and manage HLS video content through the API

## 🎥 Using the Video Player

1. **Start both servers** (backend on :8000, frontend on :3000)
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