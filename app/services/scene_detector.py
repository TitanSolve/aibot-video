from pathlib import Path
from typing import List, Tuple
from scenedetect import open_video, SceneManager
from scenedetect.detectors import ContentDetector
from scenedetect.scene_manager import save_images

from app.config import settings


class SceneDetector:
    """Video scene detection using PySceneDetect"""
    
    def __init__(self, threshold: float = None, min_scene_len: float = None):
        """
        Args:
            threshold: Scene change threshold (default from settings)
            min_scene_len: Minimum scene duration in seconds (default from settings)
        """
        self.threshold = threshold or settings.SCENE_THRESHOLD
        self.min_scene_len = min_scene_len or settings.MIN_SCENE_DURATION
    
    def detect_scenes(self, video_path: Path) -> List[Tuple[float, float]]:
        """
        Detect scene changes in video.
        
        Args:
            video_path: Path to video file
            
        Returns:
            List of (start_time, end_time) tuples in seconds
        """
        try:
            # Open video
            video = open_video(str(video_path))
            
            # Create scene manager and detector
            scene_manager = SceneManager()
            scene_manager.add_detector(
                ContentDetector(
                    threshold=self.threshold,
                    min_scene_len=int(self.min_scene_len * video.frame_rate)
                )
            )
            
            # Detect scenes
            scene_manager.detect_scenes(video)
            scene_list = scene_manager.get_scene_list()
            
            # Convert frame numbers to timestamps
            scenes = []
            for i, scene in enumerate(scene_list):
                start_frame, end_frame = scene
                start_time = start_frame.get_seconds()
                end_time = end_frame.get_seconds()
                scenes.append((start_time, end_time))
            
            # If no scenes detected, treat entire video as one scene
            if not scenes:
                duration = video.duration.get_seconds()
                scenes = [(0.0, duration)]
            
            return scenes
        
        except Exception as e:
            raise RuntimeError(f"Scene detection failed: {e}")
    
    def detect_with_info(self, video_path: Path) -> dict:
        """
        Detect scenes and return additional information.
        
        Returns:
            dict with scenes, total_duration, scene_count, etc.
        """
        try:
            video = open_video(str(video_path))
            duration = video.duration.get_seconds()
            fps = video.frame_rate
            
            scenes = self.detect_scenes(video_path)
            
            return {
                'scenes': scenes,
                'scene_count': len(scenes),
                'total_duration': duration,
                'fps': fps,
                'avg_scene_duration': sum(e - s for s, e in scenes) / len(scenes) if scenes else 0,
            }
        
        except Exception as e:
            raise RuntimeError(f"Scene detection with info failed: {e}")


def quick_detect(video_path: Path) -> List[Tuple[float, float]]:
    """Convenience function for quick scene detection with default settings"""
    detector = SceneDetector()
    return detector.detect_scenes(video_path)
