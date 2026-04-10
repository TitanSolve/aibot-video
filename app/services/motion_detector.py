"""
Motion-based Animation Detector

Replaces scene-based segmentation (PySceneDetect) with animation-aware segmentation.

Key differences:
- Scene detection: Finds visual changes (camera cuts, scene transitions)
- Animation detection: Finds continuous MOTION within scenes (button hover, card scale, icon rotate)

Uses optical flow to detect when UI elements are animating.
"""

import cv2
import numpy as np
from pathlib import Path
from typing import List, Tuple
from dataclasses import dataclass


@dataclass
class AnimationSegment:
    """Represents a detected animation"""
    start_time: float
    end_time: float
    peak_motion_time: float  # When motion is strongest
    motion_intensity: float  # Average optical flow magnitude
    motion_area_ratio: float  # Percentage of frame with motion


class MotionAnimationDetector:
    """
    Detects animations in videos using optical flow analysis.
    
    Algorithm:
    1. Compute dense optical flow between consecutive frames
    2. Identify periods of significant motion (animations)
    3. Group continuous motion into animation segments
    4. Reject camera motion (whole-frame movement)
    5. Focus on localized UI element motion
    """
    
    def __init__(
        self,
        motion_threshold: float = 2.0,      # Minimum pixel movement to count as motion
        min_motion_ratio: float = 0.01,     # Min 1% of frame must be moving
        min_duration: float = 0.1,          # Minimum animation duration (seconds)
        max_gap: float = 0.3,               # Max gap between motions to merge (seconds)
        min_intensity: float = 1.5          # Minimum average motion intensity
    ):
        self.motion_threshold = motion_threshold
        self.min_motion_ratio = min_motion_ratio
        self.min_duration = min_duration
        self.max_gap = max_gap
        self.min_intensity = min_intensity
    
    def detect_animations(self, video_path: Path) -> List[AnimationSegment]:
        """
        Detect animation segments in video.
        
        Args:
            video_path: Path to video file
            
        Returns:
            List of AnimationSegment objects
        """
        cap = cv2.VideoCapture(str(video_path))
        if not cap.isOpened():
            raise ValueError(f"Could not open video: {video_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        print(f"[MotionDetector] Analyzing {total_frames} frames at {fps} FPS")
        
        # Read first frame
        ret, prev_frame = cap.read()
        if not ret:
            raise ValueError("Could not read first frame")
        
        prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
        h, w = prev_gray.shape
        frame_area = h * w
        
        # Store motion data for each frame
        motion_data = []
        frame_idx = 1
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Compute dense optical flow (Farneback method)
            flow = cv2.calcOpticalFlowFarneback(
                prev_gray, gray,
                None,
                pyr_scale=0.5,
                levels=3,
                winsize=15,
                iterations=3,
                poly_n=5,
                poly_sigma=1.2,
                flags=0
            )
            
            # Calculate motion magnitude
            mag, ang = cv2.cartToPolar(flow[..., 0], flow[..., 1])
            
            # Identify pixels with significant motion
            motion_mask = mag > self.motion_threshold
            motion_pixels = np.sum(motion_mask)
            motion_ratio = motion_pixels / frame_area
            
            # Calculate average motion intensity in moving regions
            if motion_pixels > 0:
                avg_intensity = np.mean(mag[motion_mask])
            else:
                avg_intensity = 0.0
            
            # Detect if motion is localized (animation) vs whole-frame (camera movement)
            is_localized = self._is_localized_motion(motion_mask, h, w)
            
            timestamp = frame_idx / fps
            
            motion_data.append({
                'timestamp': timestamp,
                'motion_ratio': motion_ratio,
                'avg_intensity': avg_intensity,
                'is_localized': is_localized,
                'has_motion': motion_ratio >= self.min_motion_ratio and avg_intensity >= self.min_intensity and is_localized
            })
            
            prev_gray = gray
            frame_idx += 1
            
            # Progress indicator
            if frame_idx % 100 == 0:
                print(f"[MotionDetector] Processed {frame_idx}/{total_frames} frames")
        
        cap.release()
        
        # Extract animation segments from motion data
        segments = self._extract_segments(motion_data)
        
        print(f"[MotionDetector] Detected {len(segments)} animation segments")
        return segments
    
    def _is_localized_motion(self, motion_mask: np.ndarray, h: int, w: int) -> bool:
        """
        Check if motion is localized (UI animation) vs whole-frame (camera pan).
        
        Strategy: Divide frame into 3x3 grid. If motion is in < 70% of cells, it's localized.
        """
        cell_h, cell_w = h // 3, w // 3
        cells_with_motion = 0
        
        for i in range(3):
            for j in range(3):
                cell = motion_mask[i*cell_h:(i+1)*cell_h, j*cell_w:(j+1)*cell_w]
                if np.mean(cell) > 0.1:  # Cell has >10% moving pixels
                    cells_with_motion += 1
        
        return cells_with_motion < 7  # Less than 70% of grid cells
    
    def _extract_segments(self, motion_data: List[dict]) -> List[AnimationSegment]:
        """
        Group continuous motion periods into animation segments.
        """
        segments = []
        current_segment = None
        
        for data in motion_data:
            if data['has_motion']:
                if current_segment is None:
                    # Start new segment
                    current_segment = {
                        'start_time': data['timestamp'],
                        'end_time': data['timestamp'],
                        'intensities': [data['avg_intensity']],
                        'timestamps': [data['timestamp']]
                    }
                else:
                    # Check if gap is too large
                    gap = data['timestamp'] - current_segment['end_time']
                    if gap > self.max_gap:
                        # Finalize current segment
                        if current_segment['end_time'] - current_segment['start_time'] >= self.min_duration:
                            segments.append(self._create_segment(current_segment))
                        # Start new segment
                        current_segment = {
                            'start_time': data['timestamp'],
                            'end_time': data['timestamp'],
                            'intensities': [data['avg_intensity']],
                            'timestamps': [data['timestamp']]
                        }
                    else:
                        # Extend current segment
                        current_segment['end_time'] = data['timestamp']
                        current_segment['intensities'].append(data['avg_intensity'])
                        current_segment['timestamps'].append(data['timestamp'])
            else:
                # No motion - finalize segment if exists
                if current_segment is not None:
                    if current_segment['end_time'] - current_segment['start_time'] >= self.min_duration:
                        segments.append(self._create_segment(current_segment))
                    current_segment = None
        
        # Finalize last segment
        if current_segment is not None:
            if current_segment['end_time'] - current_segment['start_time'] >= self.min_duration:
                segments.append(self._create_segment(current_segment))
        
        return segments
    
    def _create_segment(self, seg_data: dict) -> AnimationSegment:
        """Create AnimationSegment from accumulated data"""
        intensities = seg_data['intensities']
        timestamps = seg_data['timestamps']
        
        # Find peak motion time
        peak_idx = np.argmax(intensities)
        peak_time = timestamps[peak_idx]
        
        avg_intensity = np.mean(intensities)
        
        # Estimate motion area (simplified - using intensity as proxy)
        motion_area_ratio = min(avg_intensity / 10.0, 1.0)
        
        return AnimationSegment(
            start_time=seg_data['start_time'],
            end_time=seg_data['end_time'],
            peak_motion_time=peak_time,
            motion_intensity=avg_intensity,
            motion_area_ratio=motion_area_ratio
        )
    
    def get_animation_timestamps(self, video_path: Path) -> List[Tuple[float, float]]:
        """
        Convenience method returning just (start, end) timestamps.
        Compatible with existing video_tasks.py interface.
        """
        segments = self.detect_animations(video_path)
        return [(seg.start_time, seg.end_time) for seg in segments]


def detect_animations_simple(video_path: Path) -> List[Tuple[float, float]]:
    """Simple API for animation detection"""
    detector = MotionAnimationDetector()
    return detector.get_animation_timestamps(video_path)
