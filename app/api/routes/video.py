"""
Video-related API endpoints
"""
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import Response

from app.models.video import VideoUploadResponse, VideoAsset
from app.services.video_service import video_service
from app.services.s3_service import s3_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["video"])


@router.post("/upload", response_model=VideoUploadResponse)
async def upload_video(file: UploadFile = File(...)):
    """Upload and process a video file"""
    
    # Validate content type
    logger.info(f"Uploaded file: {file.filename}, Content-Type: {file.content_type}")

    # Accept video files and some common formats
    valid_types = ['video/', 'application/octet-stream']
    valid_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv']

    is_valid_type = file.content_type and any(file.content_type.startswith(t) for t in valid_types)
    is_valid_extension = file.filename and any(file.filename.lower().endswith(ext) for ext in valid_extensions)

    if not (is_valid_type or is_valid_extension):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Content-Type: {file.content_type}, Filename: {file.filename}. Please upload a video file."
        )
    
    # Read file content
    content = await file.read()
    
    # Process upload
    asset = await video_service.upload_video(content, file.filename)
    
    return VideoUploadResponse(
        success=True,
        video_id=asset.id,
        message="Video uploaded successfully and is being processed",
        asset=asset
    )


@router.get("/videos/{video_id}", response_model=VideoAsset)
async def get_video(video_id: str):
    """Get video asset information"""
    
    asset = video_service.get_video_asset(video_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Video not found")
    
    return asset


@router.get("/videos/{video_id}/hls/{filename}")
@router.head("/videos/{video_id}/hls/{filename}")
async def serve_hls_file(video_id: str, filename: str):
    """Serve HLS files from S3 or local storage as proxy"""

    # Try S3 first - serve as proxy
    if s3_service.check_file_exists(video_id, filename):
        logger.info(f"Serving S3 file as proxy for {video_id}/{filename}")
        try:
            # Get file content from S3
            s3_key = f"videos/{video_id}/hls/{filename}"
            s3_client = s3_service.s3_client
            if s3_client:
                response = s3_client.get_object(Bucket=s3_service.bucket_name, Key=s3_key)
                file_content = response['Body'].read()

                # Set appropriate content type
                if filename.endswith('.m3u8'):
                    media_type = "application/vnd.apple.mpegurl"
                elif filename.endswith('.ts'):
                    media_type = "video/MP2T"
                else:
                    media_type = "application/octet-stream"

                logger.info(f"Serving S3 file as proxy for {video_id}/{filename}")
                return Response(content=file_content, media_type=media_type)
        except Exception as e:
            logger.error(f"Error serving S3 file {video_id}/{filename}: {e}")

    # No local storage fallback - file not found
    raise HTTPException(status_code=404, detail="File not found")


