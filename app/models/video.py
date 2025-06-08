"""
Video-related Pydantic models
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class VideoStatus(str, Enum):
    """Video processing status"""
    UPLOADING = "uploading"
    PROCESSING = "processing"
    READY = "ready"
    FAILED = "failed"
    DELETED = "deleted"


class VideoInfo(BaseModel):
    """Video information model"""
    duration: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    bitrate: Optional[int] = None
    codec: Optional[str] = None
    fps: Optional[float] = None
    file_size: Optional[int] = None


class VideoAsset(BaseModel):
    """Video asset model"""
    id: str = Field(..., description="Unique video identifier")
    filename: str = Field(..., description="Original filename")
    status: VideoStatus = Field(default=VideoStatus.UPLOADING, description="Processing status")
    info: Optional[VideoInfo] = Field(default=None, description="Video metadata")
    hls_url: Optional[str] = Field(default=None, description="HLS streaming URL")
    player_url: Optional[str] = Field(default=None, description="Player URL")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    error_message: Optional[str] = Field(default=None, description="Error message if processing failed")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class VideoUploadResponse(BaseModel):
    """Response model for video upload"""
    success: bool = Field(..., description="Upload success status")
    video_id: str = Field(..., description="Unique video identifier")
    message: str = Field(..., description="Response message")
    asset: VideoAsset = Field(..., description="Video asset details")


class VideoListResponse(BaseModel):
    """Response model for video list"""
    videos: List[VideoAsset] = Field(..., description="List of video assets")
    total: int = Field(..., description="Total number of videos")
    page: int = Field(default=1, description="Current page number")
    per_page: int = Field(default=10, description="Items per page")


class HealthResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Service status")
    timestamp: datetime = Field(default_factory=datetime.now, description="Check timestamp")
    version: str = Field(..., description="Application version")
    uptime: Optional[float] = Field(default=None, description="Uptime in seconds")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ErrorResponse(BaseModel):
    """Error response model"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[str] = Field(default=None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.now, description="Error timestamp")

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
