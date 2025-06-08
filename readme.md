# 🎬 Video Platform with Email Scheduler

A comprehensive video infrastructure platform similar to Mux.com, featuring HLS video streaming and automated email scheduling capabilities.

## 🚀 Features

### Video Infrastructure
- **HLS Video Streaming**: Efficient video streaming using HLS protocol
- **Multiple Video Players**: HLS.js integration with adaptive bitrate streaming
- **Video Upload & Processing**: Support for video file uploads and HLS conversion
- **FastAPI Backend**: High-performance Python server with automatic API documentation

### Email Scheduling System
- **Automated Email Delivery**: Schedule video emails using Resend service
- **Multiple Email Templates**: Standard, Premium, and Minimal designs
- **Flexible Scheduling**: Once, Daily, Weekly, Monthly, or Custom frequencies
- **Calendar Interface**: Visual scheduling with FullCalendar.js
- **Background Processing**: APScheduler for automated email delivery

### Frontend
- **TypeScript React App**: Modern, type-safe frontend application
- **Responsive Design**: Mobile-friendly interface
- **Real-time Statistics**: Dashboard with analytics and metrics
- **Interactive Calendar**: Drag-and-drop scheduling interface

## 📋 Prerequisites

- **Python 3.8+** with pip
- **Node.js** (v16 or higher) and **npm**
- **FFmpeg** (for video processing)
- **Resend Account** (for email functionality)
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

# Set up environment variables
cp .env.example .env
# Edit .env with your Resend API key and other settings

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
- **Calendar Interface**: http://localhost:8080/api/v1/calendar

## 📧 Email Scheduler Setup

### 1. Get Resend API Key
1. Sign up at [resend.com](https://resend.com)
2. Create an API key
3. Verify your sending domain

### 2. Configure Environment
```bash
# Update .env file
RESEND_API_KEY=re_your_api_key_here
FROM_EMAIL=noreply@yourdomain.com
FROM_NAME=Video Platform
```

### 3. Using the Scheduler
1. **Via React Interface**:
   - Go to http://localhost:3000
   - Click "Email Scheduler" tab
   - Create new schedules with the form

2. **Via Calendar Interface**:
   - Visit http://localhost:8080/api/v1/calendar
   - Visual calendar with drag-and-drop

3. **Via API**:
   ```bash
   curl -X POST "http://localhost:8080/api/v1/schedules" \
     -H "Content-Type: application/json" \
     -d '{
       "video_id": "your-video-id",
       "recipient_email": "user@example.com",
       "scheduled_date": "2024-12-25T10:00:00",
       "subject": "Your video is ready!",
       "template": "premium"
     }'
   ```

## 📁 Project Structure

```
VideoStreaming/
├── main.py                    # FastAPI server entry point
├── requirements.txt           # Python dependencies
├── .env.example              # Environment variables template
├── EMAIL_SCHEDULER_SETUP.md  # Detailed scheduler setup guide
├── app/                      # Backend application
│   ├── __init__.py
│   ├── main.py              # FastAPI app configuration
│   ├── core/                # Core configuration
│   │   ├── config.py        # Settings and configuration
│   │   └── __init__.py
│   ├── models/              # Pydantic models
│   │   ├── video.py         # Video-related models
│   │   ├── scheduler.py     # Scheduler models
│   │   └── __init__.py
│   ├── services/            # Business logic
│   │   ├── video_service.py # Video processing
│   │   ├── email_service.py # Email functionality
│   │   ├── scheduler_service.py # Scheduling logic
│   │   └── __init__.py
│   └── api/                 # API routes
│       ├── routes/
│       │   ├── video.py     # Video endpoints
│       │   ├── scheduler.py # Scheduler endpoints
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
    │   │   ├── VideoScheduler.tsx # Email scheduler
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

### Email Scheduler Endpoints
- `POST /api/v1/schedules` - Create new schedule
- `GET /api/v1/schedules` - List all schedules
- `GET /api/v1/schedules/{id}` - Get specific schedule
- `PUT /api/v1/schedules/{id}` - Update schedule
- `DELETE /api/v1/schedules/{id}` - Delete schedule
- `GET /api/v1/calendar` - Calendar interface
- `GET /api/v1/calendar/events` - Calendar events

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