"""
Video-related API endpoints
"""
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, Response
from typing import Optional

from app.models.video import VideoUploadResponse, VideoAsset
from app.services.video_service import video_service
from app.services.s3_service import s3_service
from app.core.config import settings

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

    # Check persistent directories (Docker volumes)
    persistent_file_path = s3_service.get_persistent_file_path(video_id, filename)
    if persistent_file_path:
        # Set appropriate content type
        if filename.endswith('.m3u8'):
            media_type = "application/vnd.apple.mpegurl"
        elif filename.endswith('.ts'):
            media_type = "video/MP2T"
        else:
            media_type = "application/octet-stream"

        logger.info(f"Serving persistent file for {video_id}/{filename}")
        return FileResponse(persistent_file_path, media_type=media_type)

    # Fallback to local storage
    file_path = video_service.get_hls_file_path(video_id, filename)
    if not file_path:
        raise HTTPException(status_code=404, detail="File not found")

    # Set appropriate content type
    if filename.endswith('.m3u8'):
        media_type = "application/vnd.apple.mpegurl"
    elif filename.endswith('.ts'):
        media_type = "video/MP2T"
    else:
        media_type = "application/octet-stream"

    logger.info(f"Serving local file for {video_id}/{filename}")
    return FileResponse(file_path, media_type=media_type)


@router.get("/videos/{video_id}/player")
async def video_player(video_id: str):
    """Serve HTML video player with hls.js"""
    
    # Check if video exists
    asset = video_service.get_video_asset(video_id)
    if not asset:
        raise HTTPException(status_code=404, detail="Video not found")
    
    if asset.status != "ready":
        raise HTTPException(
            status_code=400, 
            detail=f"Video is {asset.status}. Please wait for processing to complete."
        )
    
    # Use direct S3 URL for better performance
    hls_url = asset.hls_url if asset.hls_url else f"http://localhost:{settings.PORT}{settings.API_V1_STR}/videos/{video_id}/hls/index.m3u8"
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>HLS Video Player - {asset.filename}</title>
        <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
        <style>
            body {{
                margin: 0;
                padding: 20px;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                min-height: 100vh;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
            }}
            .video-container {{
                position: relative;
                width: 100%;
                max-width: 900px;
                margin: 0 auto;
                background: #000;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            }}
            #video {{
                width: 100%;
                height: auto;
                display: block;
            }}
            .video-info {{
                background: rgba(255,255,255,0.1);
                backdrop-filter: blur(10px);
                padding: 20px;
                border-radius: 8px;
                margin: 20px 0;
                text-align: center;
            }}
            .error {{
                background: #ff4444;
                color: white;
                padding: 15px;
                border-radius: 8px;
                margin: 20px 0;
                display: none;
            }}
            .loading {{
                text-align: center;
                padding: 40px;
                font-size: 18px;
            }}
            .spinner {{
                border: 3px solid rgba(255,255,255,0.3);
                border-top: 3px solid white;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 0 auto 20px;
            }}
            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎬 HLS Video Player</h1>
                <p>Powered by {settings.PROJECT_NAME}</p>
            </div>
            
            <div class="video-info">
                <strong>📹 Video:</strong> {asset.filename}<br>
                <strong>🆔 ID:</strong> {video_id}<br>
                <strong>📡 Stream URL:</strong> {hls_url}
            </div>
            
            <div class="loading" id="loading">
                <div class="spinner"></div>
                Loading video...
            </div>
            
            <div class="video-container" style="display: none;" id="videoContainer">
                <video id="video" controls muted>
                    Your browser does not support the video tag.
                </video>
            </div>
            
            <div class="error" id="error"></div>
        </div>

        <script>
            const video = document.getElementById('video');
            const errorDiv = document.getElementById('error');
            const loadingDiv = document.getElementById('loading');
            const videoContainer = document.getElementById('videoContainer');
            const url = "{hls_url}";
            
            function showError(message) {{
                errorDiv.textContent = message;
                errorDiv.style.display = 'block';
                loadingDiv.style.display = 'none';
                console.error(message);
            }}
            
            function hideLoading() {{
                loadingDiv.style.display = 'none';
                videoContainer.style.display = 'block';
            }}
            
            if (Hls.isSupported()) {{
                const hls = new Hls({{
                    enableWorker: true,
                    lowLatencyMode: true,
                }});
                
                hls.loadSource(url);
                hls.attachMedia(video);
                
                hls.on(Hls.Events.MANIFEST_PARSED, function() {{
                    console.log('Manifest loaded successfully');
                    hideLoading();
                }});
                
                hls.on(Hls.Events.ERROR, function(event, data) {{
                    console.error('HLS Error:', data);
                    if (data.fatal) {{
                        switch(data.type) {{
                            case Hls.ErrorTypes.NETWORK_ERROR:
                                showError('Network error occurred. Please check your connection.');
                                break;
                            case Hls.ErrorTypes.MEDIA_ERROR:
                                showError('Media error occurred. Trying to recover...');
                                hls.recoverMediaError();
                                break;
                            default:
                                showError('Fatal error occurred: ' + data.details);
                                hls.destroy();
                                break;
                        }}
                    }}
                }});
                
            }} else if (video.canPlayType('application/vnd.apple.mpegurl')) {{
                // Native HLS support (Safari)
                video.src = url;
                video.addEventListener('loadedmetadata', function() {{
                    hideLoading();
                }});
                video.addEventListener('error', function(e) {{
                    showError('Error loading video: ' + e.message);
                }});
            }} else {{
                showError('Your browser does not support HLS playback.');
            }}
        </script>
    </body>
    </html>
    """
    
    return HTMLResponse(content=html_content)


# Legacy endpoints for backward compatibility
@router.get("/hls/{video_id}/{filename}")
async def serve_hls_file_legacy(video_id: str, filename: str):
    """Legacy HLS file serving endpoint"""
    return await serve_hls_file(video_id, filename)


@router.get("/player")
async def video_player_legacy(url: Optional[str] = Query(None)):
    """Legacy video player endpoint"""
    if not url:
        raise HTTPException(status_code=400, detail="URL parameter is required")
    
    # Extract video ID from URL if it's our format
    if "/hls/" in url and "/index.m3u8" in url:
        try:
            video_id = url.split("/hls/")[1].split("/")[0]
            return await video_player(video_id)
        except:
            pass
    
    # Fallback to simple player
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Video Player</title>
        <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
    </head>
    <body>
        <video id="video" controls style="width: 100%; max-width: 800px;"></video>
        <script>
            const video = document.getElementById('video');
            if (Hls.isSupported()) {{
                const hls = new Hls();
                hls.loadSource('{url}');
                hls.attachMedia(video);
            }} else if (video.canPlayType('application/vnd.apple.mpegurl')) {{
                video.src = '{url}';
            }}
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)
