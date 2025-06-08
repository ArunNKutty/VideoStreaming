"""
Application configuration settings
"""
import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Project info
    PROJECT_NAME: str = "HLS Video Streaming Server"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "A scalable video streaming platform with HLS support"
    API_V1_STR: str = "/api/v1"
    
    # Server settings
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    DEBUG: bool = True
    
    # CORS settings
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # Directory settings
    VIDEOS_DIR: str = "videos"
    UPLOAD_DIR: str = "uploads"
    STATIC_DIR: str = "static"
    
    # File upload settings
    MAX_FILE_SIZE: int = 1024 * 1024 * 1024  # 1GB
    ALLOWED_VIDEO_EXTENSIONS: List[str] = [".mp4", ".avi", ".mov", ".mkv", ".webm", ".flv"]
    ALLOWED_MIME_TYPES: List[str] = [
        "video/mp4", "video/avi", "video/quicktime", 
        "video/x-msvideo", "video/webm", "video/x-flv"
    ]
    
    # FFmpeg settings
    FFMPEG_PATH: str = "ffmpeg"
    FFPROBE_PATH: str = "ffprobe"
    HLS_SEGMENT_DURATION: int = 10
    HLS_PLAYLIST_TYPE: str = "vod"
    
    # Processing settings
    MAX_WORKERS: int = 2
    PROCESSING_TIMEOUT: int = 3600  # 1 hour
    
    # Logging
    LOG_LEVEL: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create global settings instance
settings = Settings()
