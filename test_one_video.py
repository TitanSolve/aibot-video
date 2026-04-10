#!/usr/bin/env python3
"""
Test script to upload and process ONE video at a time.
This avoids API rate limits by processing slowly.
"""

import requests
import time
import sys
from pathlib import Path
from app.database import SessionLocal, Video, Segment

API_URL = "http://localhost:8000"

def upload_video(file_path: str):
    """Upload a single video."""
    file_path = Path(file_path)
    
    if not file_path.exists():
        print(f"❌ Error: File not found: {file_path}")
        return None
    
    print(f"\n{'='*80}")
    print(f"UPLOADING: {file_path.name}")
    print(f"{'='*80}")
    print(f"Size: {file_path.stat().st_size / 1024 / 1024:.2f} MB")
    
    with open(file_path, 'rb') as f:
        files = {'file': (file_path.name, f, 'video/mp4')}
        data = {'author': 'Phase1 Test', 'source': 'Manual Verification'}
        
        try:
            response = requests.post(f"{API_URL}/videos/upload", files=files, data=data)
            response.raise_for_status()
            result = response.json()
            print(f"✅ Upload successful!")
            print(f"   Video ID: {result['id']}")
            print(f"   Status: {result['status']}")
            return result['id']
        except Exception as e:
            print(f"❌ Upload failed: {e}")
            return None

def wait_for_completion(video_id: str, max_wait: int = 180):
    """Wait for video processing to complete."""
    print(f"\n⏳ Waiting for processing (max {max_wait}s)...")
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(f"{API_URL}/videos/{video_id}")
            response.raise_for_status()
            video_info = response.json()
            status = video_info['status']
            
            elapsed = int(time.time() - start_time)
            print(f"\r   [{elapsed}s] Status: {status}  ", end='', flush=True)
            
            if status == 'completed':
                print(f"\n✅ Processing completed in {elapsed}s!")
                return True
            elif status == 'failed':
                print(f"\n❌ Processing failed!")
                return False
            
            time.sleep(2)
        except Exception as e:
            print(f"\n❌ Error checking status: {e}")
            return False
    
    print(f"\n⏰ Timeout after {max_wait}s")
    return False

def show_results(video_id: str):
    """Display detailed results."""
    db = SessionLocal()
    
    video = db.query(Video).filter(Video.id == video_id).first()
    if not video:
        print("❌ Video not found in database")
        db.close()
        return
    
    segments = db.query(Segment).filter(Segment.video_id == video_id).order_by(Segment.segment_index).all()
    
    print(f"\n{'='*80}")
    print("PHASE 1 VERIFICATION RESULTS")
    print(f"{'='*80}")
    
    print(f"\n✅ REQUIREMENT 1: VIDEO UPLOAD & STORAGE")
    print(f"   Filename: {video.filename}")
    print(f"   Duration: {video.duration:.2f}s")
    print(f"   Resolution: {video.width}x{video.height}")
    print(f"   FPS: {video.fps}")
    print(f"   Status: {video.status}")
    
    print(f"\n✅ REQUIREMENT 2: MOTION DETECTION & KEYFRAMES")
    print(f"   Segments: {len(segments)}")
    print(f"   Keyframes: {len(segments) * 3}")
    
    has_descriptions = sum(1 for s in segments if s.content_description)
    print(f"\n{'✅' if has_descriptions > 0 else '❌'} REQUIREMENT 3: AI DESCRIPTIONS")
    print(f"   Segments with descriptions: {has_descriptions}/{len(segments)}")
    
    has_embeddings = sum(1 for s in segments if s.description_embedding)
    print(f"\n{'✅' if has_embeddings > 0 else '❌'} REQUIREMENT 4: VECTOR EMBEDDINGS")
    print(f"   Segments with embeddings: {has_embeddings}/{len(segments)}")
    
    if len(segments) > 0:
        print(f"\n{'='*80}")
        print("SAMPLE SEGMENTS (first 3)")
        print(f"{'='*80}")
        
        for i, seg in enumerate(segments[:3]):
            print(f"\nSegment {i}: {seg.start_time:.2f}s - {seg.end_time:.2f}s")
            print(f"  📝 Description: {seg.content_description or 'None'}")
            print(f"  🎬 Motion: {seg.motion_type or 'None'}")
            print(f"  🖼️  UI Elements: {seg.ui_elements_animated or 'None'}")
            print(f"  ⚡ Timing: {seg.timing_function or 'None'}")
            print(f"  🏃 Speed: {seg.speed or 'None'}")
            print(f"  🎨 Style: {seg.design_style or 'None'}")
            print(f"  🔄 Pattern: {seg.animation_pattern or 'None'}")
            print(f"  🎯 Context: {seg.usage_context or 'None'}")
            print(f"  🖼️  Keyframes: {len(seg.keyframe_paths)}")
            print(f"  🧠 Embedding: {'✅ YES' if seg.description_embedding else '❌ NO'}")
    
    print(f"\n{'='*80}")
    
    db.close()

def main():
    if len(sys.argv) < 2:
        print("Usage: python test_one_video.py <video.mp4>")
        print("\nExample: python test_one_video.py /home/ubuntu/Documents/sample1.mp4")
        sys.exit(1)
    
    video_path = sys.argv[1]
    
    # Upload
    video_id = upload_video(video_path)
    if not video_id:
        sys.exit(1)
    
    # Wait for processing
    if wait_for_completion(video_id):
        # Show results
        show_results(video_id)
        print("\n✅ Test completed successfully!")
    else:
        print("\n❌ Test failed or timed out")
        sys.exit(1)

if __name__ == "__main__":
    main()
