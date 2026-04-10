from celery import Celery
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session
from uuid import UUID
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

from app.config import settings
from app.database import SessionLocal, Video, Segment
from app.services.motion_detector import MotionAnimationDetector  # CHANGED: motion-based instead of scene-based
from app.utils.video_utils import extract_keyframes
from app.services.ai_describer import VideoSegmentDescriber
from app.services.embeddings import embed_single

# Initialize Celery
celery_app = Celery(
    'aibot_video',
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)

celery_app.conf.task_routes = {
    'app.tasks.video_tasks.*': {'queue': 'video_processing'}
}


def get_db() -> Session:
    """Get database session"""
    db = SessionLocal()
    try:
        return db
    finally:
        pass  # Don't close here, close in task


@celery_app.task(name='process_video', bind=True, max_retries=3, time_limit=600, soft_time_limit=540)
def process_video_task(self, video_id: str):
    """
    Main task to process uploaded video:
    1. Detect scenes
    2. Extract key frames
    3. Generate AI descriptions
    4. Create embeddings
    5. Store in database
    """
    db = SessionLocal()
    
    try:
        # Get video from database
        video = db.query(Video).filter(Video.id == UUID(video_id)).first()
        if not video:
            raise ValueError(f"Video {video_id} not found")
        
        # Update status
        video.status = "processing"
        db.commit()
        
        print(f"[Task] Processing video: {video.filename}")
        video_path = Path(video.original_path)
        
        # Step 1: Detect animations (motion-based, not scene-based)
        print(f"[Task] Detecting animations using optical flow analysis...")
        detector = MotionAnimationDetector(
            motion_threshold=settings.MOTION_THRESHOLD,
            min_motion_ratio=settings.MIN_MOTION_RATIO,
            min_duration=settings.MIN_ANIMATION_DURATION,
            max_gap=settings.MAX_ANIMATION_GAP,
            min_intensity=settings.MIN_MOTION_INTENSITY
        )
        animation_segments = detector.detect_animations(video_path)
        
        # Convert to (start, end) tuples for compatibility
        animations = [(seg.start_time, seg.end_time) for seg in animation_segments]
        print(f"[Task] Found {len(animations)} animation segments (motion-based detection)")
        
        # Step 2 & 3: Process segments in parallel (max 5 concurrent)
        describer = VideoSegmentDescriber()
        segments_data = []
        
        def process_single_segment(idx, start_time, end_time):
            """Process a single segment and return its data"""
            print(f"[Task] Processing animation segment {idx + 1}/{len(animations)}")
            
            # Create segment directory
            segment_dir = settings.FRAMES_DIR / str(video.id) / f"segment_{idx:04d}"
            segment_dir.mkdir(parents=True, exist_ok=True)
            
            # Extract key frames (reduced to 3 frames)
            try:
                frame_paths = extract_keyframes(
                    video_path,
                    start_time,
                    end_time,
                    segment_dir,
                    num_frames=3,  # Reduced from 5 to 3 for faster processing
                    strategy=settings.FRAME_EXTRACTION_STRATEGY
                )
                keyframe_paths_list = [str(fp) for fp in frame_paths] if frame_paths else []
            except Exception as e:
                print(f"[Task] Frame extraction failed for segment {idx}: {e}")
                frame_paths = []
                keyframe_paths_list = []
            
            # Generate AI description
            description = None
            if frame_paths:
                try:
                    print(f"[Task] Calling Gemini API for segment {idx}...")
                    description = describer.describe_segment(
                        frame_paths,
                        additional_context=f"From video: {video.filename}"
                    )
                    print(f"[Task] ✅ AI description generated for segment {idx}")
                except TimeoutError as e:
                    print(f"[Task] ⚠️ Gemini API timeout for segment {idx}: {e}")
                except Exception as e:
                    print(f"[Task] ⚠️ AI description failed for segment {idx}: {type(e).__name__}: {e}")
            
            return {
                'idx': idx,
                'start_time': start_time,
                'end_time': end_time,
                'keyframe_paths_list': keyframe_paths_list,
                'description': description
            }
        
        # Process segments in parallel (max 5 concurrent to avoid overwhelming Gemini API)
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(process_single_segment, idx, start, end): idx 
                for idx, (start, end) in enumerate(animations)
            }
            
            for future in as_completed(futures):
                try:
                    seg_data = future.result()
                    segments_data.append(seg_data)
                    print(f"[Task] Segment {seg_data['idx']} completed")
                except Exception as e:
                    print(f"[Task] Segment processing error: {e}")
        
        # Sort by index to maintain order
        segments_data.sort(key=lambda x: x['idx'])
        
        # Create database records
        for seg_data in segments_data:
            idx = seg_data['idx']
            start_time = seg_data['start_time']
            end_time = seg_data['end_time']
            keyframe_paths_list = seg_data['keyframe_paths_list']
            description = seg_data['description']
            
            # Create segment record
            segment = Segment(
                video_id=video.id,
                segment_index=idx,
                start_time=start_time,
                end_time=end_time,
                duration=end_time - start_time,
                keyframe_paths=keyframe_paths_list
            )
            
            # Populate description fields if available (requirements-aligned taxonomy)
            if description:
                desc_dict = description.model_dump()
                segment.content_description = desc_dict.get('content_description')
                segment.motion_type = desc_dict.get('motion_type')
                segment.ui_elements_animated = desc_dict.get('ui_elements_animated')
                segment.timing_function = desc_dict.get('timing_function')
                segment.speed = desc_dict.get('speed')
                segment.motion_character = desc_dict.get('motion_character')
                segment.animation_pattern = desc_dict.get('animation_pattern')
                segment.usage_state = desc_dict.get('usage_state')
                segment.usage_context = desc_dict.get('usage_context')
                segment.reusability = desc_dict.get('reusability')
                segment.device_target = desc_dict.get('device_target')
                segment.design_style = desc_dict.get('design_style')
                segment.color_palette = desc_dict.get('color_palette')
                segment.typography_style = desc_dict.get('typography_style')
                segment.storyline = desc_dict.get('storyline')
                segment.industries = desc_dict.get('industries')
                segment.metaphors = desc_dict.get('metaphors')
                segment.mood = desc_dict.get('mood')
                segment.visual_uniqueness = desc_dict.get('visual_uniqueness')
                
                # Generate embedding from key fields
                try:
                    motion_types = " ".join(desc_dict.get('motion_type', []))
                    ui_elements = " ".join(desc_dict.get('ui_elements_animated', []))
                    patterns = " ".join(desc_dict.get('animation_pattern', []))
                    industries = " ".join(desc_dict.get('industries', []))
                    metaphors = " ".join(desc_dict.get('metaphors', []))
                    
                    embedding_text = f"{segment.content_description} {motion_types} {ui_elements} {patterns} {segment.usage_context} {segment.design_style} {industries} {metaphors}"
                    embedding = embed_single(embedding_text)
                    segment.description_embedding = embedding.tolist()
                    print(f"[Task] Embedding generated for segment {idx}")
                except Exception as e:
                    print(f"[Task] Embedding failed for segment {idx}: {e}")
            
            db.add(segment)
        
        # Update video status
        video.status = "completed"
        video.processed_at = datetime.utcnow()
        db.commit()
        
        print(f"[Task] Video {video_id} processing completed successfully")
        return {"status": "success", "segments": len(animation_segments)}
    
    except Exception as e:
        # Mark as failed
        if db and video:
            video.status = "failed"
            video.error_message = str(e)
            db.commit()
        
        print(f"[Task] Video {video_id} processing failed: {e}")
        
        # Retry if possible
        raise self.retry(exc=e, countdown=60)
    
    finally:
        if db:
            db.close()
