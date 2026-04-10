from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, Form
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from pathlib import Path
import shutil
from uuid import uuid4
from typing import Optional

from app.database import get_db, Video, Segment
from app.schemas import VideoResponse
from app.config import settings
from app.utils.video_utils import get_video_info
from app.tasks.video_tasks import process_video_task

router = APIRouter(prefix="/videos", tags=["videos"])


@router.post("/upload", response_model=VideoResponse, status_code=201)
async def upload_video(
    file: UploadFile = File(...),
    author: Optional[str] = Form(None),
    source: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Upload a video file for processing.
    
    The video will be saved and queued for:
    1. Scene detection
    2. Frame extraction
    3. AI-powered description
    4. Embedding generation
    """
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in settings.ALLOWED_VIDEO_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(settings.ALLOWED_VIDEO_EXTENSIONS)}"
        )
    
    # Check file size (rough check from content)
    contents = await file.read()
    file_size_mb = len(contents) / (1024 * 1024)
    
    if file_size_mb > settings.MAX_VIDEO_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {settings.MAX_VIDEO_SIZE_MB}MB"
        )
    
    # Generate unique filename
    video_id = uuid4()
    safe_filename = f"{video_id}{file_ext}"
    video_path = settings.UPLOAD_DIR / safe_filename
    
    # Save file
    try:
        with open(video_path, 'wb') as f:
            f.write(contents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")
    
    # Get video metadata
    try:
        video_info = get_video_info(video_path)
    except Exception as e:
        # Clean up file
        video_path.unlink(missing_ok=True)
        raise HTTPException(status_code=400, detail=f"Invalid video file: {e}")
    
    # Create database record
    video = Video(
        id=video_id,
        filename=file.filename,
        original_path=str(video_path),
        duration=video_info['duration'],
        fps=video_info['fps'],
        width=video_info['width'],
        height=video_info['height'],
        file_size=len(contents),
        status="pending",
        author=author,
        source=source,
        metadata={
            'codec': video_info['codec'],
            'bitrate': video_info['bitrate']
        }
    )
    
    db.add(video)
    db.commit()
    db.refresh(video)
    
    # Queue processing task (async)
    try:
        process_video_task.delay(str(video.id))
    except Exception as e:
        print(f"Warning: Failed to queue task: {e}")
        # Don't fail the upload, just log it
    
    return video


@router.get("/{video_id}", response_model=VideoResponse)
def get_video(video_id: str, db: Session = Depends(get_db)):
    """Get video metadata by ID"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video


@router.delete("/{video_id}")
def delete_video(video_id: str, db: Session = Depends(get_db)):
    """Delete video and all associated segments"""
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Delete file
    try:
        Path(video.original_path).unlink(missing_ok=True)
    except Exception as e:
        print(f"Warning: Failed to delete video file: {e}")
    
    # Database cascade will delete segments
    db.delete(video)
    db.commit()
    
    return {"message": "Video deleted successfully"}


@router.get("/", response_model=list[VideoResponse])
def list_videos(
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all videos with optional filtering"""
    query = db.query(
        Video,
        func.count(Segment.id).label('segment_count'),
        func.sum(case((Segment.content_description.isnot(None), 1), else_=0)).label('ai_description_count')
    ).outerjoin(Segment, Video.id == Segment.video_id).group_by(Video.id)
    
    if status:
        query = query.filter(Video.status == status)
    
    results = query.offset(skip).limit(limit).all()
    
    # Add counts to video objects
    videos = []
    for video, seg_count, ai_count in results:
        video.segment_count = seg_count or 0
        video.ai_description_count = int(ai_count) if ai_count else 0
        videos.append(video)
    
    return videos
