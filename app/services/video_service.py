"""
Video processing and management service
"""
import os
import uuid
import subprocess
import shutil
import json
from pathlib import Path
from typing import Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor
import logging

from app.core.config import settings
from app.core.exceptions import FileUploadError
from app.models.video import VideoAsset, VideoStatus, VideoInfo
from app.services.s3_service import s3_service

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
                # Upload HLS files to S3 (required - no local storage)
                try:
                    uploaded_files = await s3_service.upload_hls_files(video_id, str(output_dir))
                    if uploaded_files:
                        logger.info(f"Uploaded {len(uploaded_files)} HLS files to S3 for video {video_id}")

                        # Clean up local HLS files after successful S3 upload
                        if output_dir.exists():
                            shutil.rmtree(output_dir)
                            logger.info(f"Cleaned up local HLS files for {video_id}")

                        logger.info(f"Video processing completed for {video_id} (S3 only)")
                        self._update_asset_status(video_id, VideoStatus.READY, video_info)
                    else:
                        logger.error(f"S3 upload failed for {video_id} - no local storage fallback")
                        self._update_asset_status(video_id, VideoStatus.FAILED, error="S3 upload failed")

                        # Clean up local files on failure
                        if output_dir.exists():
                            shutil.rmtree(output_dir)

                except Exception as s3_error:
                    logger.error(f"S3 upload failed: {s3_error}. No local storage fallback available.")
                    self._update_asset_status(video_id, VideoStatus.FAILED, error=f"S3 upload failed: {s3_error}")

                    # Clean up local files on failure
                    if output_dir.exists():
                        shutil.rmtree(output_dir)
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
        if info:
            logger.info(f"Asset {video_id} info: duration={info.duration}s, {info.width}x{info.height}")
    
    def get_video_asset(self, video_id: str) -> Optional[VideoAsset]:
        """Get video asset by ID"""
        # Check if HLS playlist exists in S3
        s3_playlist_exists = s3_service.check_file_exists(video_id, "index.m3u8")

        if s3_playlist_exists:
            # Video is ready in S3
            status = VideoStatus.READY
            hls_url = s3_service.get_hls_url(video_id)
        else:
            # Check if processing directory exists (temporary processing)
            video_dir = Path(settings.VIDEOS_DIR) / video_id
            if video_dir.exists():
                # Processing is still ongoing
                status = VideoStatus.PROCESSING
                hls_url = None
            else:
                # Video not found
                return None

        return VideoAsset(
            id=video_id,
            filename=f"video_{video_id}",
            status=status,
            hls_url=hls_url,
            player_url=f"/api/v1/videos/{video_id}/player" if status == VideoStatus.READY else None
        )
    
    def get_hls_file_url(self, video_id: str, filename: str) -> Optional[str]:
        """Get URL for HLS file (S3 or local)"""
        # Check S3 first
        if s3_service.check_file_exists(video_id, filename):
            return s3_service.get_file_url(video_id, filename)
        return None

    def get_hls_file_path(self, video_id: str, filename: str) -> Optional[Path]:
        """Local storage disabled - always returns None"""
        # Parameters kept for API compatibility but not used
        return None


# Global service instance
video_service = VideoService()
