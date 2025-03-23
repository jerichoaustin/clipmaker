from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, HttpUrl
import subprocess
import os
from pathlib import Path
import uuid

app = FastAPI(title="Video Downloader API", description="API to download videos using lux")

# Configuration
DOWNLOAD_DIR = Path("downloads")
DOWNLOAD_DIR.mkdir(exist_ok=True)

class VideoRequest(BaseModel):
    url: HttpUrl
    filename: str = None

class VideoResponse(BaseModel):
    message: str
    file_path: str
    status: str

def download_video(url: str, filename: str = None):
    """Download a video using lux."""
    if not filename:
        filename = f"{uuid.uuid4()}"
    
    output_path = str(DOWNLOAD_DIR / filename)
    
    try:
        # Use lux to download the video
        result = subprocess.run(
            ["lux", "-o", output_path, url],
            capture_output=True,
            text=True,
            check=True
        )
        return {"status": "completed", "file_path": output_path}
    except subprocess.CalledProcessError as e:
        print(f"Error downloading video: {e.stderr}")
        return {"status": "failed", "error": e.stderr}

@app.post("/download", response_model=VideoResponse)
async def download_video_endpoint(video_request: VideoRequest, background_tasks: BackgroundTasks):
    """
    Download a video from the provided URL.
    
    - **url**: The URL of the video to download
    - **filename**: Optional custom filename for the downloaded video
    """
    # Start the download in the background
    filename = video_request.filename or f"{uuid.uuid4()}"
    file_path = str(DOWNLOAD_DIR / filename)
    
    # Execute the download in the background
    background_tasks.add_task(download_video, str(video_request.url), filename)
    
    return {
        "message": f"Video download initiated from {video_request.url}",
        "file_path": file_path,
        "status": "processing"
    }

@app.get("/status")
async def service_status():
    """Check if the service is running."""
    return {"status": "online", "downloads_dir": str(DOWNLOAD_DIR)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
