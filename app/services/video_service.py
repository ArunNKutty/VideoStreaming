"""
Video processing and management service
"""
import os
import uuid
import subprocess
import shutil
import json
from pathlib import Path
from typing import Optional, Dict, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging

from app.core.config import settings
from app.core.exceptions import VideoProcessingError, FileUploadError
from app.models.video import VideoAsset, VideoStatus, VideoInfo

logger = logging.getLogger(__name__)


class VideoService:
    """Service for video processing and management"""
    
    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=settings.MAX_WORKERS)
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure required directories exist"""
        Path(settings.VIDEOS_DIR).mkdir(exist_ok=True)
        Path(settings.UPLOAD_DIR).mkdir(exist_ok=True)
    
    async def upload_video(self, file_content: bytes, filename: str) -> VideoAsset:
        """Upload and process a video file"""
        try:
            # Generate unique video ID
            video_id = str(uuid.uuid4())
            
            # Validate file
            self._validate_file(filename, len(file_content))
            
            # Save uploaded file
            upload_path = Path(settings.UPLOAD_DIR) / f"{video_id}_temp{Path(filename).suffix}"
            
            with open(upload_path, "wb") as f:
                f.write(file_content)
            
            # Create video asset
            asset = VideoAsset(
                id=video_id,
                filename=filename,
                status=VideoStatus.PROCESSING
            )
            
            # Start processing in background
            asyncio.create_task(self._process_video(video_id, str(upload_path)))
            
            return asset
            
        except Exception as e:
            logger.error(f"Upload failed: {str(e)}")
            raise FileUploadError(f"Upload failed: {str(e)}", filename)
    
    def _validate_file(self, filename: str, file_size: int):
        """Validate uploaded file"""
        # Check file size
        if file_size > settings.MAX_FILE_SIZE:
            raise FileUploadError(f"File too large. Maximum size: {settings.MAX_FILE_SIZE} bytes")
        
        # Check file extension
        file_ext = Path(filename).suffix.lower()
        if file_ext not in settings.ALLOWED_VIDEO_EXTENSIONS:
            raise FileUploadError(f"Invalid file type. Allowed: {settings.ALLOWED_VIDEO_EXTENSIONS}")
    
    async def _process_video(self, video_id: str, input_path: str):
        """Process video in background"""
        try:
            logger.info(f"Starting video processing for {video_id}")
            
            # Get video info
            video_info = await self._get_video_info(input_path)
            
            # Convert to HLS
            output_dir = Path(settings.VIDEOS_DIR) / video_id
            success = await self._convert_to_hls(input_path, str(output_dir))
            
            if success:
                logger.info(f"Video processing completed for {video_id}")
                # Update asset status (in a real app, this would update the database)
                self._update_asset_status(video_id, VideoStatus.READY, video_info)
            else:
                logger.error(f"Video processing failed for {video_id}")
                self._update_asset_status(video_id, VideoStatus.FAILED, error="Conversion failed")
            
            # Cleanup temp file
            if os.path.exists(input_path):
                os.remove(input_path)
                
        except Exception as e:
            logger.error(f"Video processing error for {video_id}: {str(e)}")
            self._update_asset_status(video_id, VideoStatus.FAILED, error=str(e))
            
            # Cleanup on error
            if os.path.exists(input_path):
                os.remove(input_path)
    
    async def _get_video_info(self, input_path: str) -> VideoInfo:
        """Get video metadata using ffprobe"""
        try:
            cmd = [
                settings.FFPROBE_PATH,
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                input_path
            ]
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                lambda: subprocess.run(cmd, capture_output=True, text=True)
            )
            
            if result.returncode != 0:
                logger.warning(f"ffprobe failed: {result.stderr}")
                return VideoInfo()
            
            data = json.loads(result.stdout)
            
            # Extract video stream info
            video_stream = next(
                (s for s in data.get("streams", []) if s.get("codec_type") == "video"),
                {}
            )
            
            format_info = data.get("format", {})
            
            return VideoInfo(
                duration=float(format_info.get("duration", 0)),
                width=video_stream.get("width"),
                height=video_stream.get("height"),
                bitrate=int(format_info.get("bit_rate", 0)) if format_info.get("bit_rate") else None,
                codec=video_stream.get("codec_name"),
                fps=self._parse_fps(video_stream.get("r_frame_rate")),
                file_size=int(format_info.get("size", 0))
            )
            
        except Exception as e:
            logger.error(f"Error getting video info: {str(e)}")
            return VideoInfo()
    
    def _parse_fps(self, fps_str: str) -> Optional[float]:
        """Parse FPS from ffprobe output"""
        try:
            if not fps_str or fps_str == "0/0":
                return None
            if "/" in fps_str:
                num, den = fps_str.split("/")
                return float(num) / float(den)
            return float(fps_str)
        except:
            return None
    
    async def _convert_to_hls(self, input_path: str, output_dir: str) -> bool:
        """Convert video to HLS format"""
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            cmd = [
                settings.FFMPEG_PATH,
                "-i", input_path,
                "-codec:", "copy",
                "-start_number", "0",
                "-hls_time", str(settings.HLS_SEGMENT_DURATION),
                "-hls_list_size", "0",
                "-hls_playlist_type", settings.HLS_PLAYLIST_TYPE,
                "-f", "hls",
                os.path.join(output_dir, "index.m3u8")
            ]
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                lambda: subprocess.run(cmd, capture_output=True, text=True, timeout=settings.PROCESSING_TIMEOUT)
            )
            
            if result.returncode == 0:
                logger.info(f"HLS conversion successful: {output_dir}")
                return True
            else:
                logger.error(f"FFmpeg error: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"Video processing timeout for {output_dir}")
            return False
        except Exception as e:
            logger.error(f"Conversion error: {str(e)}")
            return False
    
    def _update_asset_status(self, video_id: str, status: VideoStatus, info: VideoInfo = None, error: str = None):
        """Update asset status (placeholder for database update)"""
        # In a real application, this would update the database
        logger.info(f"Asset {video_id} status updated to {status}")
        if error:
            logger.error(f"Asset {video_id} error: {error}")
    
    def get_video_asset(self, video_id: str) -> Optional[VideoAsset]:
        """Get video asset by ID"""
        # Check if video directory exists
        video_dir = Path(settings.VIDEOS_DIR) / video_id
        if not video_dir.exists():
            return None
        
        # Check if HLS playlist exists
        playlist_path = video_dir / "index.m3u8"
        status = VideoStatus.READY if playlist_path.exists() else VideoStatus.PROCESSING
        
        return VideoAsset(
            id=video_id,
            filename=f"video_{video_id}",
            status=status,
            hls_url=f"/api/v1/videos/{video_id}/hls/index.m3u8" if status == VideoStatus.READY else None,
            player_url=f"/api/v1/videos/{video_id}/player" if status == VideoStatus.READY else None
        )
    
    def get_hls_file_path(self, video_id: str, filename: str) -> Optional[Path]:
        """Get path to HLS file"""
        file_path = Path(settings.VIDEOS_DIR) / video_id / filename
        return file_path if file_path.exists() else None


# Global service instance
video_service = VideoService()
