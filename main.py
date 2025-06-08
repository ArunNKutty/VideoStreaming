import os
import uuid
import subprocess
import shutil
from pathlib import Path
from typing import Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI(title="HLS Video Streaming Server", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create directories
VIDEOS_DIR = Path("videos")
STATIC_DIR = Path("static")
VIDEOS_DIR.mkdir(exist_ok=True)
STATIC_DIR.mkdir(exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Thread pool for video processing
executor = ThreadPoolExecutor(max_workers=2)

def convert_to_hls(input_path: str, output_dir: str) -> bool:
    """Convert video to HLS format using ffmpeg"""
    try:
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # FFmpeg command for HLS conversion
        cmd = [
            "ffmpeg",
            "-i", input_path,
            "-codec:", "copy",
            "-start_number", "0",
            "-hls_time", "10",
            "-hls_list_size", "0",
            "-f", "hls",
            os.path.join(output_dir, "index.m3u8")
        ]
        
        # Run ffmpeg
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            # Remove the original uploaded file
            os.remove(input_path)
            return True
        else:
            print(f"FFmpeg error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"Conversion error: {str(e)}")
        return False

@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    """Upload and convert video to HLS format"""
    
    # Validate file type
    if not file.content_type or not file.content_type.startswith('video/'):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a video file.")
    
    # Generate unique ID
    video_id = str(uuid.uuid4())
    
    # Create paths
    upload_path = VIDEOS_DIR / f"{video_id}_temp{Path(file.filename).suffix}"
    output_dir = VIDEOS_DIR / video_id
    
    try:
        # Save uploaded file
        with open(upload_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        # Convert to HLS in background
        loop = asyncio.get_event_loop()
        success = await loop.run_in_executor(
            executor, 
            convert_to_hls, 
            str(upload_path), 
            str(output_dir)
        )
        
        if success:
            hls_url = f"http://localhost:8080/hls/{video_id}/index.m3u8"
            return {
                "success": True,
                "video_id": video_id,
                "hls_url": hls_url,
                "player_url": f"http://localhost:8080/player?url={hls_url}"
            }
        else:
            # Cleanup on failure
            if upload_path.exists():
                upload_path.unlink()
            if output_dir.exists():
                shutil.rmtree(output_dir)
            raise HTTPException(status_code=500, detail="Video conversion failed")
            
    except Exception as e:
        # Cleanup on error
        if upload_path.exists():
            upload_path.unlink()
        if output_dir.exists():
            shutil.rmtree(output_dir)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/hls/{video_id}/{filename}")
async def serve_hls_file(video_id: str, filename: str):
    """Serve HLS files (m3u8 playlist and ts segments)"""
    
    file_path = VIDEOS_DIR / video_id / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    # Set appropriate content type
    if filename.endswith('.m3u8'):
        media_type = "application/vnd.apple.mpegurl"
    elif filename.endswith('.ts'):
        media_type = "video/MP2T"
    else:
        media_type = "application/octet-stream"
    
    return FileResponse(file_path, media_type=media_type)

@app.get("/player")
async def video_player(url: Optional[str] = None):
    """Serve HTML video player with hls.js"""
    
    if not url:
        raise HTTPException(status_code=400, detail="URL parameter is required")
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>HLS Video Player</title>
        <script src="https://cdn.jsdelivr.net/npm/hls.js@latest"></script>
        <style>
            body {{
                margin: 0;
                padding: 20px;
                font-family: Arial, sans-serif;
                background-color: #1a1a1a;
                color: white;
            }}
            .container {{
                max-width: 1200px;
                margin: 0 auto;
            }}
            .video-container {{
                position: relative;
                width: 100%;
                max-width: 800px;
                margin: 0 auto;
                background: #000;
                border-radius: 8px;
                overflow: hidden;
                box-shadow: 0 4px 20px rgba(0,0,0,0.3);
            }}
            #video {{
                width: 100%;
                height: auto;
                display: block;
            }}
            .controls {{
                margin-top: 20px;
                text-align: center;
            }}
            .url-display {{
                background: #333;
                padding: 10px;
                border-radius: 4px;
                margin: 20px 0;
                word-break: break-all;
                font-family: monospace;
                font-size: 14px;
            }}
            .error {{
                background: #ff4444;
                color: white;
                padding: 10px;
                border-radius: 4px;
                margin: 20px 0;
                display: none;
            }}
            h1 {{
                text-align: center;
                margin-bottom: 30px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>HLS Video Player</h1>
            
            <div class="url-display">
                <strong>Stream URL:</strong> {url}
            </div>
            
            <div class="video-container">
                <video id="video" controls muted autoplay>
                    Your browser does not support the video tag.
                </video>
            </div>
            
            <div class="error" id="error"></div>
            
            <div class="controls">
                <p>Video player powered by hls.js</p>
            </div>
        </div>

        <script>
            const video = document.getElementById('video');
            const errorDiv = document.getElementById('error');
            const url = "{url}";
            
            function showError(message) {{
                errorDiv.textContent = message;
                errorDiv.style.display = 'block';
                console.error(message);
            }}
            
            function hideError() {{
                errorDiv.style.display = 'none';
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
                    hideError();
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

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "HLS Video Streaming Server",
        "endpoints": {
            "upload": "POST /upload - Upload video file for HLS conversion",
            "stream": "GET /hls/{video_id}/index.m3u8 - Access HLS stream",
            "player": "GET /player?url={hls_url} - Video player interface"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080) 