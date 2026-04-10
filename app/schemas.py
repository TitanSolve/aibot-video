from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID


# Video Schemas
class VideoBase(BaseModel):
    filename: str
    author: Optional[str] = None
    source: Optional[str] = None


class VideoCreate(VideoBase):
    pass


class VideoResponse(VideoBase):
    id: UUID
    duration: Optional[float] = None
    fps: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    file_size: Optional[int] = None
    status: str
    uploaded_at: datetime
    processed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    segment_count: Optional[int] = None
    ai_description_count: Optional[int] = None
    
    class Config:
        from_attributes = True


# Segment Schemas - 20 Parameters (Requirements-aligned)
class SegmentDescription(BaseModel):
    """Complete 20-parameter description of animation segment aligned with requirements"""
    
    # Core Animation Attributes (6 params)
    motion_type: List[str] = Field(default_factory=list, description="enter, exit, scale, move, bounce, pulse, rotate, morph, hover, flip, slide, parallax")
    ui_elements_animated: List[str] = Field(default_factory=list, description="text, button, icon, card, sidebar, modal, nav, tooltip, input, dropdown, badge, menu")
    timing_function: Optional[str] = Field(None, description="ease-in, ease-out, ease-in-out, spring, linear, cubic-bezier")
    speed: Optional[str] = Field(None, description="instant (<0.1s), fast (0.1-0.3s), medium (0.3-0.6s), slow (>0.6s)")
    motion_character: Optional[str] = Field(None, description="smooth, bouncy, elastic, sharp, fluid, mechanical, organic")
    animation_pattern: List[str] = Field(default_factory=list, description="microinteraction, stagger, reveal_on_scroll, parallax_layer, sequential, simultaneous")
    
    # Context & Usage (5 params)
    usage_state: Optional[str] = Field(None, description="hover, click, load, scroll, idle, focus, drag")
    usage_context: Optional[str] = Field(None, description="landing, hero, cta, navigation, feedback, onboarding, testimonial, pricing")
    reusability: List[str] = Field(default_factory=list, description="cta_block, product_card, hover_effect, loading_state, nav_transition, form_feedback")
    device_target: Optional[str] = Field(None, description="desktop, mobile, both")
    
    # Visual & Style (4 params)
    design_style: Optional[str] = Field(None, description="minimal, brutalist, glassmorphism, neumorphism, flat, material, skeuomorphic")
    color_palette: List[Dict[str, Any]] = Field(default_factory=list, description="[{color: '#hex', dominance: 0-1}]")
    typography_style: Optional[str] = Field(None, description="geometric, humanist, serif, monospace, display, handwritten")
    storyline: Optional[str] = Field(None, description="Narrative of animation progression")
    
    # Semantic & Thematic (3 params)
    industries: List[str] = Field(default_factory=list, description="fintech, healthcare, ecommerce, saas, crypto, education, entertainment, agency, portfolio")
    metaphors: List[str] = Field(default_factory=list, description="growth, speed, trust, innovation, simplicity, power, precision, creativity, transformation")
    mood: Optional[str] = Field(None, description="professional, playful, elegant, energetic, calm, bold, luxurious, friendly")
    
    # Technical & Meta (2 params)
    visual_uniqueness: Optional[str] = Field(None, description="common, distinctive, unique, trendy, experimental")
    content_description: Optional[str] = Field(None, description="Overall description of animation content")


class SegmentBase(BaseModel):
    segment_index: int
    start_time: float
    end_time: float
    duration: float
    keyframe_paths: Optional[List[str]] = Field(default_factory=list, description="Paths to multiple keyframes (start, mid, end states)")


class SegmentCreate(SegmentBase):
    video_id: UUID
    description: Optional[SegmentDescription] = None


class SegmentResponse(SegmentBase):
    id: UUID
    video_id: UUID
    content_description: Optional[str] = None
    
    # All 20 parameters (requirements-aligned)
    motion_type: Optional[List[str]] = None
    ui_elements_animated: Optional[List[str]] = None
    timing_function: Optional[str] = None
    speed: Optional[str] = None
    motion_character: Optional[str] = None
    animation_pattern: Optional[List[str]] = None
    usage_state: Optional[str] = None
    usage_context: Optional[str] = None
    reusability: Optional[List[str]] = None
    device_target: Optional[str] = None
    design_style: Optional[str] = None
    color_palette: Optional[List[Dict[str, Any]]] = None
    typography_style: Optional[str] = None
    storyline: Optional[str] = None
    industries: Optional[List[str]] = None
    metaphors: Optional[List[str]] = None
    mood: Optional[str] = None
    visual_uniqueness: Optional[str] = None
    
    created_at: datetime
    
    class Config:
        from_attributes = True


class VideoWithSegments(VideoResponse):
    segments: List[SegmentResponse] = []


# Search Schemas
class SearchQuery(BaseModel):
    query: str = Field(..., description="Natural language search query")
    top_k: int = Field(20, ge=1, le=100, description="Number of results to return")
    filters: Optional[Dict[str, Any]] = Field(None, description="Additional filters")


class SearchResult(BaseModel):
    segment: SegmentResponse
    video: VideoResponse
    similarity_score: float = Field(..., ge=0, le=1)


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResult]
    total: int
    processing_time_ms: float
