from pydantic_settings import BaseSettings
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://aibot:aibot123@localhost:5434/aibot_video"
    
    # Redis
    REDIS_URL: str = "redis://localhost:6380/0"
    
    # Qdrant
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION: str = "video_segments"
        

    # Models
    OPENAI_EMBED_MODEL: str = "text-embedding-3-large"
    GEMINI_MODEL: str = "gemini-2.0-flash-exp"
    EMBED_DIM: int = 3072
    
    # File Storage
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    FRAMES_DIR: Path = BASE_DIR / "frames"
    MAX_VIDEO_SIZE_MB: int = 500
    ALLOWED_VIDEO_EXTENSIONS: list = [".mp4", ".mov", ".avi", ".webm", ".mkv"]
    
    # Video Processing
    MIN_SCENE_DURATION: float = 0.5  # seconds (legacy, now using motion detection)
    SCENE_THRESHOLD: float = 27.0     # PySceneDetect threshold (legacy)
    MAX_FRAMES_PER_SEGMENT: int = 3   # Key frames: start/mid/end animation states
    FRAME_EXTRACTION_STRATEGY: str = "animation_states"  # "animation_states", "diverse", or "even"
    
    # Motion Detection (for animation segmentation)
    MOTION_THRESHOLD: float = 2.0          # Minimum pixel movement
    MIN_MOTION_RATIO: float = 0.01         # Min 1% of frame must be moving
    MIN_ANIMATION_DURATION: float = 0.1    # Min 100ms animation
    MAX_ANIMATION_GAP: float = 0.3         # Merge animations within 300ms
    MIN_MOTION_INTENSITY: float = 1.5      # Minimum motion strength
    
    # Search
    SEARCH_TOP_K: int = 20
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()

# Ensure directories exist
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
settings.FRAMES_DIR.mkdir(parents=True, exist_ok=True)
