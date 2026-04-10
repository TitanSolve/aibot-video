from sqlalchemy import create_engine, Column, String, Float, Integer, BigInteger, DateTime, Text, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector
import uuid
from datetime import datetime

from app.config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Video(Base):
    __tablename__ = "videos"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    original_path = Column(Text, nullable=False)
    duration = Column(Float)  # seconds
    fps = Column(Float)
    width = Column(Integer)
    height = Column(Integer)
    file_size = Column(BigInteger)
    
    # Metadata
    status = Column(String(50), default="pending")  # pending, processing, completed, failed
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    author = Column(String(255), nullable=True)
    source = Column(String(255), nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Additional metadata (renamed from 'metadata' to avoid SQLAlchemy conflict)
    video_metadata = Column(JSONB, nullable=True)
    
    # Relationships
    segments = relationship("Segment", back_populates="video", cascade="all, delete-orphan")


class Segment(Base):
    __tablename__ = "segments"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    video_id = Column(UUID(as_uuid=True), ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    segment_index = Column(Integer, nullable=False)
    
    # Timing
    start_time = Column(Float, nullable=False)
    end_time = Column(Float, nullable=False)
    duration = Column(Float, nullable=False)
    
    # Visual content
    keyframe_paths = Column(JSONB, nullable=True)  # List of frame paths [start, mid, end states]
    content_description = Column(Text, nullable=True)
    
    # CORRECT TAXONOMY - Matching Requirements
    
    # 1. Motion Type (what kind of animation)
    motion_type = Column(JSONB, nullable=True)  # [enter, exit, scale, move, bounce, pulse, rotate, morph, hover, click, loader]
    
    # 2. UI Elements Animated (what's moving)
    ui_elements_animated = Column(JSONB, nullable=True)  # [text, button, icon, card, sidebar, modal, nav, chart, form, tabs]
    
    # 3. Motion Style / Timing (how it moves)
    timing_function = Column(String(100), nullable=True)  # ease-in, ease-out, spring, cubic-bezier, linear
    speed = Column(String(50), nullable=True)  # slow, medium, fast
    motion_character = Column(String(100), nullable=True)  # natural, playful, functional, cinematic, smooth, bouncy
    
    # 4. Usage Context (where it's used)
    usage_context = Column(String(100), nullable=True)  # landing, hero, cta, navigation, feedback, onboarding
    usage_state = Column(String(50), nullable=True)  # hover, click, load, scroll, idle, focus
    device_target = Column(String(50), nullable=True)  # desktop, mobile, both
    
    # 5. Animation Pattern (recognized patterns)
    animation_pattern = Column(JSONB, nullable=True)  # [microinteraction, stagger, reveal_on_scroll, shared_element, loader]
    
    # 6. Reusability (where can be reused)
    reusability = Column(JSONB, nullable=True)  # [cta_block, product_card, section_transition, feature_block, hover_effect]
    
    # 7. Style & Visual Design
    design_style = Column(String(100), nullable=True)  # 3d, illustration, video, minimal, brutalist, glassmorphism
    color_palette = Column(JSONB, nullable=True)  # [{color: "#hex", dominance: 0-1}]
    typography_style = Column(String(100), nullable=True)  # geometric, humanist, serif
    
    # 8. Semantic & Metaphors
    metaphors = Column(JSONB, nullable=True)  # [growth, speed, trust, innovation, security, transformation]
    industries = Column(JSONB, nullable=True)  # [crypto, fintech, healthcare, ecommerce, saas, edtech]
    mood = Column(String(100), nullable=True)  # professional, playful, elegant, energetic, calm
    
    # 9. Storyline & Meaning (for deep understanding)
    storyline = Column(Text, nullable=True)  # What narrative/story the animation tells
    visual_uniqueness = Column(String(50), nullable=True)  # common, distinctive, unique, trendy, experimental
    
    # Vector embedding for semantic search
    description_embedding = Column(Vector(settings.EMBED_DIM), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    video = relationship("Video", back_populates="segments")
    
    # Indexes for fast queries
    __table_args__ = (
        Index('idx_segments_video', 'video_id'),
        Index('idx_segments_timing_function', 'timing_function'),
        Index('idx_segments_speed', 'speed'),
        Index('idx_segments_usage_state', 'usage_state'),
        Index('idx_segments_design_style', 'design_style'),
        Index('idx_segments_mood', 'mood'),
    )


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database and create tables"""
    Base.metadata.create_all(bind=engine)
