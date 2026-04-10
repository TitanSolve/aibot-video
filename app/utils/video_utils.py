import subprocess
import json
from pathlib import Path
from typing import Dict, Any, Optional


def get_video_info(video_path: Path) -> Dict[str, Any]:
    """
    Extract video metadata using ffprobe.
    
    Returns:
        dict with duration, fps, width, height, codec, etc.
    """
    try:
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_format',
            '-show_streams',
            str(video_path)
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        
        # Find video stream
        video_stream = next(
            (s for s in data.get('streams', []) if s.get('codec_type') == 'video'),
            None
        )
        
        if not video_stream:
            raise ValueError("No video stream found")
        
        # Parse FPS
        fps_str = video_stream.get('r_frame_rate', '0/1')
        num, den = map(float, fps_str.split('/'))
        fps = num / den if den != 0 else 0
        
        return {
            'duration': float(data.get('format', {}).get('duration', 0)),
            'fps': fps,
            'width': int(video_stream.get('width', 0)),
            'height': int(video_stream.get('height', 0)),
            'codec': video_stream.get('codec_name', 'unknown'),
            'bitrate': int(data.get('format', {}).get('bit_rate', 0)),
        }
    
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"ffprobe failed: {e.stderr}")
    except Exception as e:
        raise RuntimeError(f"Failed to get video info: {e}")


def extract_frame(
    video_path: Path,
    timestamp: float,
    output_path: Path,
    width: Optional[int] = None,
    height: Optional[int] = None
) -> Path:
    """
    Extract a single frame from video at specified timestamp using ffmpeg.
    
    Args:
        video_path: Input video file
        timestamp: Time in seconds
        output_path: Output image path
        width: Optional resize width
        height: Optional resize height (maintains aspect ratio if only width given)
    
    Returns:
        Path to extracted frame
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        cmd = [
            'ffmpeg',
            '-ss', str(timestamp),
            '-i', str(video_path),
            '-vframes', '1',
            '-q:v', '2',  # High quality
        ]
        
        # Add scaling if requested
        if width or height:
            if width and height:
                scale = f'{width}:{height}'
            elif width:
                scale = f'{width}:-1'  # Maintain aspect ratio
            else:
                scale = f'-1:{height}'
            cmd.extend(['-vf', f'scale={scale}'])
        
        cmd.extend(['-y', str(output_path)])
        
        subprocess.run(cmd, capture_output=True, check=True)
        
        if not output_path.exists():
            raise RuntimeError("Frame extraction failed - output file not created")
        
        return output_path
    
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"ffmpeg frame extraction failed: {e.stderr.decode()}")
    except Exception as e:
        raise RuntimeError(f"Frame extraction error: {e}")


def extract_keyframes(
    video_path: Path,
    start_time: float,
    end_time: float,
    output_dir: Path,
    num_frames: int = 3,
    strategy: str = "animation_states"
) -> list[Path]:
    """
    Extract key frames from an animation segment.
    
    For animation analysis, we want to capture the STATES of the animation:
    - Start state (before animation)
    - Mid-transition (animation in progress)
    - End state (after animation)
    
    Args:
        video_path: Input video file
        start_time: Segment start time in seconds
        end_time: Segment end time in seconds
        output_dir: Directory to save frames
        num_frames: Number of frames to extract (default 3 for start/mid/end)
        strategy: "animation_states" (default), "diverse", or "even"
    
    Returns:
        List of paths to extracted frames
    """
    duration = end_time - start_time
    if duration <= 0:
        raise ValueError("Invalid segment duration")
    
    output_dir.mkdir(parents=True, exist_ok=True)
    frames = []
    
    if strategy == "animation_states":
        # Capture animation progression: START → TRANSITION → END
        if num_frames == 1:
            # Single frame: capture mid-animation (most motion)
            timestamps = [start_time + duration * 0.5]
        elif num_frames == 2:
            # Two frames: start and end states
            timestamps = [
                start_time + duration * 0.1,  # Start state (10% in, skip entry artifacts)
                start_time + duration * 0.9,  # End state (90% through)
            ]
        elif num_frames == 3:
            # Three frames: start, peak motion, end
            timestamps = [
                start_time + duration * 0.1,   # Start state
                start_time + duration * 0.5,   # Peak motion (middle)
                start_time + duration * 0.9,   # End state
            ]
        else:  # 4+ frames
            # Multiple transition states: start → multiple mid-points → end
            timestamps = []
            for i in range(num_frames):
                # Distribute from 10% to 90% to avoid edge artifacts
                ratio = 0.1 + (0.8 * i / max(num_frames - 1, 1))
                timestamps.append(start_time + duration * ratio)
    
    elif strategy == "diverse":
        # Original diverse strategy (kept for backward compatibility)
        if num_frames == 1:
            timestamps = [start_time + duration * 0.5]
        elif num_frames == 2:
            timestamps = [
                start_time + duration * 0.2,
                start_time + duration * 0.8,
            ]
        else:
            timestamps = []
            for i in range(num_frames):
                ratio = 0.15 + (0.70 * i / max(num_frames - 1, 1))
                timestamps.append(start_time + duration * ratio)
    
    else:  # "even" strategy
        # Evenly spaced frames
        timestamps = []
        for i in range(num_frames):
            if num_frames == 1:
                timestamps.append(start_time + duration / 2)
            else:
                timestamps.append(start_time + (duration * i / (num_frames - 1)))
    
    # Extract frames at calculated timestamps
    for i, timestamp in enumerate(timestamps):
        output_path = output_dir / f"frame_{i:03d}.jpg"
        frame_path = extract_frame(video_path, timestamp, output_path)
        frames.append(frame_path)
    
    return frames


def check_ffmpeg_installed() -> bool:
    """Check if ffmpeg and ffprobe are installed"""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        subprocess.run(['ffprobe', '-version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False
