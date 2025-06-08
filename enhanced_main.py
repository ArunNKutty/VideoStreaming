"""
Enhanced Video Infrastructure API - Mux Clone
Building on the existing HLS server with advanced features
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import asyncio
import asyncpg
import aiofiles
import os
import uuid
import json
import subprocess
from datetime import datetime, timedelta
from typing import Optional, List, Dict
import logging
from pydantic import BaseModel
import redis.asyncio as redis

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Pydantic models
class VideoAsset(BaseModel):
    id: str
    filename: str
    status: str
    duration: Optional[float] = None
    created_at: datetime
    playback_url: Optional[str] = None

class UploadResponse(BaseModel):
    id: str
    url: str
    expires_at: datetime

class AnalyticsEvent(BaseModel):
    session_id: str
    event_type: str
    data: Dict
    timestamp: Optional[datetime] = None

class PlaybackSession(BaseModel):
    id: str
    asset_id: str
    viewer_id: str
    started_at: datetime

# FastAPI app initialization
app = FastAPI(
    title="Video Infrastructure API",
    description="Mux-like video streaming platform",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security
security = HTTPBearer()

# Global variables for connections
db_pool = None
redis_client = None

# Configuration
UPLOAD_DIR = "uploads"
VIDEO_DIR = "videos"
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:pass@localhost:5432/videoplatform")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

# Ensure directories exist
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(VIDEO_DIR, exist_ok=True)

# Mount static files
app.mount("/videos", StaticFiles(directory="videos"), name="videos")

@app.on_event("startup")
async def startup():
    """Initialize database and Redis connections"""
    global db_pool, redis_client
    
    try:
        # Initialize database pool
        db_pool = await asyncpg.create_pool(DATABASE_URL)
        logger.info("Database connection established")
        
        # Initialize Redis
        redis_client = redis.from_url(REDIS_URL)
        logger.info("Redis connection established")
        
        # Create tables if they don't exist
        await create_tables()
        
    except Exception as e:
        logger.error(f"Startup error: {e}")

@app.on_event("shutdown")
async def shutdown():
    """Close database and Redis connections"""
    global db_pool, redis_client
    
    if db_pool:
        await db_pool.close()
    if redis_client:
        await redis_client.close()

async def create_tables():
    """Create database tables"""
    async with db_pool.acquire() as conn:
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name VARCHAR(255) NOT NULL,
                api_key VARCHAR(255) UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS video_assets (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                account_id UUID REFERENCES accounts(id),
                filename VARCHAR(255),
                duration FLOAT,
                status VARCHAR(50) DEFAULT 'uploading',
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            )
        """)
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS playback_sessions (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                asset_id UUID,
                viewer_id VARCHAR(255),
                started_at TIMESTAMP DEFAULT NOW(),
                ended_at TIMESTAMP,
                total_watch_time INTEGER DEFAULT 0
            )
        """)
        
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS analytics_events (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                session_id UUID,
                event_type VARCHAR(50),
                timestamp TIMESTAMP DEFAULT NOW(),
                data JSONB
            )
        """)

async def verify_api_key(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify API key authentication"""
    api_key = credentials.credentials
    
    async with db_pool.acquire() as conn:
        account = await conn.fetchrow(
            "SELECT id, name FROM accounts WHERE api_key = $1", api_key
        )
        
        if not account:
            raise HTTPException(status_code=401, detail="Invalid API key")
        
        return {"id": account["id"], "name": account["name"]}

# API Routes

@app.get("/")
async def root():
    """Welcome message"""
    return {"message": "Video Infrastructure API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "timestamp": datetime.now()}

@app.post("/v1/video/assets", response_model=VideoAsset)
async def create_video_asset(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    account: dict = Depends(verify_api_key)
):
    """Upload and create a new video asset"""
    
    # Validate file type
    if not file.content_type.startswith('video/'):
        raise HTTPException(status_code=400, detail="File must be a video")
    
    # Generate asset ID
    asset_id = str(uuid.uuid4())
    
    # Save uploaded file
    file_path = os.path.join(UPLOAD_DIR, f"{asset_id}.{file.filename.split('.')[-1]}")
    
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
    
    # Save to database
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO video_assets (id, account_id, filename, status)
            VALUES ($1, $2, $3, $4)
        """, asset_id, account["id"], file.filename, "processing")
    
    # Queue transcoding job
    background_tasks.add_task(transcode_video, asset_id, file_path)
    
    return VideoAsset(
        id=asset_id,
        filename=file.filename,
        status="processing",
        created_at=datetime.now()
    )

@app.get("/v1/video/assets/{asset_id}", response_model=VideoAsset)
async def get_video_asset(asset_id: str, account: dict = Depends(verify_api_key)):
    """Get video asset details"""
    
    async with db_pool.acquire() as conn:
        asset = await conn.fetchrow("""
            SELECT id, filename, duration, status, created_at
            FROM video_assets 
            WHERE id = $1 AND account_id = $2
        """, asset_id, account["id"])
        
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        playback_url = None
        if asset["status"] == "ready":
            playback_url = f"/v1/video/assets/{asset_id}/playback"
        
        return VideoAsset(
            id=asset["id"],
            filename=asset["filename"],
            duration=asset["duration"],
            status=asset["status"],
            created_at=asset["created_at"],
            playback_url=playback_url
        )

@app.get("/v1/video/assets/{asset_id}/playback")
async def get_playback_url(asset_id: str, account: dict = Depends(verify_api_key)):
    """Get HLS playback URL"""
    
    # Verify asset exists and belongs to account
    async with db_pool.acquire() as conn:
        asset = await conn.fetchrow("""
            SELECT status FROM video_assets 
            WHERE id = $1 AND account_id = $2
        """, asset_id, account["id"])
        
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        
        if asset["status"] != "ready":
            raise HTTPException(status_code=400, detail="Asset not ready for playback")
    
    # Return HLS playlist
    playlist_path = os.path.join(VIDEO_DIR, asset_id, "index.m3u8")
    
    if not os.path.exists(playlist_path):
        raise HTTPException(status_code=404, detail="Playlist not found")
    
    return FileResponse(playlist_path, media_type="application/vnd.apple.mpegurl")

@app.post("/v1/analytics/sessions", response_model=PlaybackSession)
async def create_analytics_session(
    asset_id: str,
    viewer_id: str = "anonymous",
    account: dict = Depends(verify_api_key)
):
    """Create analytics session for video playback"""
    
    session_id = str(uuid.uuid4())
    
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO playback_sessions (id, asset_id, viewer_id)
            VALUES ($1, $2, $3)
        """, session_id, asset_id, viewer_id)
    
    return PlaybackSession(
        id=session_id,
        asset_id=asset_id,
        viewer_id=viewer_id,
        started_at=datetime.now()
    )

@app.post("/v1/analytics/events")
async def track_analytics_event(event: AnalyticsEvent):
    """Track analytics event"""
    
    async with db_pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO analytics_events (session_id, event_type, data)
            VALUES ($1, $2, $3)
        """, event.session_id, event.event_type, json.dumps(event.data))
    
    return {"status": "success"}

@app.get("/v1/analytics/assets/{asset_id}")
async def get_asset_analytics(asset_id: str, account: dict = Depends(verify_api_key)):
    """Get analytics for a specific asset"""
    
    async with db_pool.acquire() as conn:
        result = await conn.fetchrow("""
            SELECT 
                COUNT(DISTINCT ps.id) as total_views,
                AVG(ps.total_watch_time) as avg_watch_time,
                COUNT(ae.id) as total_events
            FROM playback_sessions ps
            LEFT JOIN analytics_events ae ON ps.id = ae.session_id
            WHERE ps.asset_id = $1
        """, asset_id)
        
        return {
            "asset_id": asset_id,
            "total_views": result["total_views"] or 0,
            "avg_watch_time": float(result["avg_watch_time"] or 0),
            "total_events": result["total_events"] or 0
        }

# Background task for video transcoding
async def transcode_video(asset_id: str, input_path: str):
    """Transcode video to HLS format"""
    
    try:
        output_dir = os.path.join(VIDEO_DIR, asset_id)
        os.makedirs(output_dir, exist_ok=True)
        
        # Basic HLS transcoding
        cmd = [
            "ffmpeg", "-i", input_path,
            "-codec:v", "libx264",
            "-codec:a", "aac",
            "-hls_time", "10",
            "-hls_playlist_type", "vod",
            "-hls_segment_filename", f"{output_dir}/segment_%03d.ts",
            f"{output_dir}/index.m3u8"
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.wait()
        
        if process.returncode == 0:
            # Update asset status to ready
            async with db_pool.acquire() as conn:
                await conn.execute("""
                    UPDATE video_assets 
                    SET status = 'ready', updated_at = NOW()
                    WHERE id = $1
                """, asset_id)
            
            logger.info(f"Transcoding completed for asset {asset_id}")
        else:
            # Update asset status to failed
            async with db_pool.acquire() as conn:
                await conn.execute("""
                    UPDATE video_assets 
                    SET status = 'failed', updated_at = NOW()
                    WHERE id = $1
                """, asset_id)
            
            logger.error(f"Transcoding failed for asset {asset_id}: {stderr}")
            
    except Exception as e:
        logger.error(f"Transcoding error for asset {asset_id}: {e}")
        
        # Update asset status to failed
        async with db_pool.acquire() as conn:
            await conn.execute("""
                UPDATE video_assets 
                SET status = 'failed', updated_at = NOW()
                WHERE id = $1
            """, asset_id)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
