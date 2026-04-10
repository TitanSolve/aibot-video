from __future__ import annotations
import json
from pathlib import Path
from typing import Any, List
from PIL import Image
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from app.config import settings
from app.schemas import SegmentDescription


# Configure Gemini
if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)


ANIMATION_ANALYSIS_PROMPT = """You are analyzing UI/UX animations for professional design work. This is technical analysis of interface motion patterns.

**TASK**: Extract 20 animation parameters from these interface frames showing START → MID → END states.

**IMPORTANT**: This is professional UI animation analysis for designers and developers. The content shows user interface elements and their motion patterns.

**20 REQUIRED PARAMETERS**:

**1. CORE ANIMATION ATTRIBUTES (6 params)**:
- **motion_type** (array): enter, exit, scale, move, bounce, pulse, rotate, morph, hover, flip, slide, parallax, fade, squeeze, shake, swing
- **ui_elements_animated** (array): text, button, icon, card, sidebar, modal, nav, tooltip, input, dropdown, badge, menu, avatar, image, background, form
- **timing_function** (string): ease-in, ease-out, ease-in-out, spring, linear, cubic-bezier, custom
- **speed** (string): instant (<0.1s), fast (0.1-0.3s), medium (0.3-0.6s), slow (>0.6s)
- **motion_character** (string): smooth, bouncy, elastic, sharp, fluid, mechanical, organic, snappy, gentle
- **animation_pattern** (array): microinteraction, stagger, reveal_on_scroll, parallax_layer, sequential, simultaneous, cascade, magnetic, morph_transition

**2. CONTEXT & USAGE (5 params)**:
- **usage_state** (string): hover, click, load, scroll, idle, focus, drag, blur, error, success
- **usage_context** (string): landing, hero, cta, navigation, feedback, onboarding, testimonial, pricing, feature, footer
- **reusability** (array): cta_block, product_card, hover_effect, loading_state, nav_transition, form_feedback, hero_animation, modal_entrance
- **device_target** (string): desktop, mobile, both
- **content_description** (string): Brief description of animation content

**3. VISUAL & STYLE (4 params)**:
- **design_style** (string): minimal, brutalist, glassmorphism, neumorphism, flat, material, skeuomorphic, gradient, neon
- **color_palette** (array of objects): [{"color": "#hex", "dominance": 0.0-1.0}]
- **typography_style** (string): geometric, humanist, serif, monospace, display, handwritten, condensed
- **storyline** (string): Narrative describing animation progression (e.g., "Button scales up on hover, bounces back on click")

**4. SEMANTIC & THEMATIC (3 params)**:
- **industries** (array): fintech, healthcare, ecommerce, saas, crypto, education, entertainment, agency, portfolio, food, travel, gaming, social
- **metaphors** (array): growth, speed, trust, innovation, simplicity, power, precision, creativity, transformation, connection, playfulness
- **mood** (string): professional, playful, elegant, energetic, calm, bold, luxurious, friendly, dramatic, minimalist

**5. TECHNICAL & META (2 params)**:
- **visual_uniqueness** (string): common, distinctive, unique, trendy, experimental, classic
- **content_description** (string): Overall description of what's happening

**OUTPUT FORMAT**: Return ONLY a valid JSON object. No markdown code blocks, no ```json```, no explanatory text before or after. Start with { and end with }.

Example output format:
{
  "motion_type": ["hover", "scale"],
  "ui_elements_animated": ["button", "icon"],
  "timing_function": "ease-out",
  "speed": "fast",
  "motion_character": "bouncy",
  "animation_pattern": ["microinteraction"],
  "usage_state": "hover",
  "usage_context": "cta",
  "reusability": ["cta_block", "hover_effect"],
  "device_target": "both",
  "design_style": "minimal",
  "color_palette": [{"color": "#6366f1", "dominance": 0.7}],
  "typography_style": "geometric",
  "storyline": "Button scales to 110% on hover with slight bounce, icon rotates 15deg",
  "industries": ["saas", "fintech"],
  "metaphors": ["innovation", "speed"],
  "mood": "professional",
  "visual_uniqueness": "common",
  "content_description": "Primary CTA button with hover animation and icon rotation"
}

Now analyze these frames showing the animation's START → MID → END states:
"""



def extract_json(text: str) -> Any:
    """Extract JSON from potentially messy LLM response"""
    s = text.strip()
    
    # Try direct parse
    try:
        return json.loads(s)
    except Exception:
        pass
    
    # Remove markdown code blocks
    for fence in ("```json", "```"):
        if s.lower().startswith(fence):
            inner = s[len(fence):]
            end = inner.rfind("```")
            if end != -1:
                candidate = inner[:end].strip()
                try:
                    return json.loads(candidate)
                except Exception:
                    pass
    
    # Extract JSON object from text
    first, last = s.find("{"), s.rfind("}")
    if first != -1 and last != -1 and last > first:
        candidate = s[first:last + 1]
        try:
            return json.loads(candidate)
        except Exception as e:
            # Try to fix truncated JSON by adding missing closing braces
            if "Expecting" in str(e) or "Unterminated" in str(e):
                # Count open vs closed braces
                open_braces = candidate.count('{') + candidate.count('[')
                close_braces = candidate.count('}') + candidate.count(']')
                missing = open_braces - close_braces
                
                # Add missing closing braces/brackets
                if missing > 0:
                    fixed = candidate
                    # Try to intelligently close arrays and objects
                    for _ in range(missing):
                        if fixed.rstrip().endswith(','):
                            fixed = fixed.rstrip()[:-1]  # Remove trailing comma
                        if '[' in fixed and ']' not in fixed[-20:]:
                            fixed += ']'
                        else:
                            fixed += '}'
                    
                    try:
                        return json.loads(fixed)
                    except Exception:
                        pass
    
    raise ValueError("Could not extract valid JSON from response")


class VideoSegmentDescriber:
    """AI-powered video segment analysis using Gemini"""
    
    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.GEMINI_MODEL
        if not settings.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not set")
        self.model = genai.GenerativeModel(self.model_name)
    
    def describe_segment(
        self,
        frame_paths: List[Path],
        additional_context: str = "",
        max_retries: int = 3,
        retry_delay: int = 30
    ) -> SegmentDescription:
        """
        Analyze video segment from key frames with retry logic for rate limits.
        
        Args:
            frame_paths: List of paths to key frames
            additional_context: Optional additional context about the video
            max_retries: Maximum number of retries for 429 errors (default: 3)
            retry_delay: Delay in seconds between retries (default: 30)
            
        Returns:
            SegmentDescription with all 20 parameters
        """
        import time
        
        for attempt in range(max_retries + 1):
            try:
                # Load images and resize to reduce size (helps with safety filters)
                images = []
                for fp in frame_paths:
                    img = Image.open(fp)
                    # Resize to max 800px width to reduce file size and potential filter triggers
                    if img.width > 800:
                        ratio = 800 / img.width
                        new_size = (800, int(img.height * ratio))
                        img = img.resize(new_size, Image.Resampling.LANCZOS)
                    images.append(img)
                
                # Build prompt
                context_note = f"\n\nAdditional context: {additional_context}" if additional_context else ""
                enforced_note = "\n\nREMEMBER: Return ONLY valid JSON, no markdown blocks, no extra text."
                full_prompt = ANIMATION_ANALYSIS_PROMPT + context_note + enforced_note
                
                # Create content for Gemini
                content = [full_prompt] + images
                
                # Generate description with timeout (30 seconds)
                # Configure generation with JSON mode
                generation_config = genai.types.GenerationConfig(
                    temperature=0.7,
                    top_p=0.95,
                    top_k=40,
                    max_output_tokens=4096,  # Increased to prevent JSON truncation
                    response_mime_type="application/json",  # Force JSON output
                )
                
                # Disable safety filters for animation analysis (not harmful content)
                safety_settings = {
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                }
                
                request_options = {
                    "timeout": 20  # 20 second timeout - most requests complete in 5-10s
                }
                
                start_time = time.time()
                response = self.model.generate_content(
                    content,
                    generation_config=generation_config,
                    safety_settings=safety_settings,
                    request_options=request_options
                )
                elapsed = time.time() - start_time
                print(f"[AI Describer] Gemini API call completed in {elapsed:.2f}s")
                
                # Check if response was blocked
                if not response.candidates or not response.candidates[0].content.parts:
                    # Response was blocked by safety filter or other issue
                    print(f"[AI Describer] Response blocked. Finish reason: {response.candidates[0].finish_reason if response.candidates else 'NO_CANDIDATES'}")
                    print(f"[AI Describer] Safety ratings: {response.candidates[0].safety_ratings if response.candidates else 'N/A'}")
                    # Don't retry for content filter - just skip this attempt
                    if attempt >= max_retries:
                        raise ValueError("Response blocked by content filter")
                    continue  # Try again with different processing
                
                response_text = (response.text or "").strip()
                print(f"[AI Describer] Response length: {len(response_text)} chars")
                if len(response_text) > 500:
                    print(f"[AI Describer] Response preview (first 500): {response_text[:500]}...")
                else:
                    print(f"[AI Describer] Full response: {response_text}")
                
                # Extract and parse JSON
                try:
                    data = extract_json(response_text)
                except ValueError as json_err:
                    # If JSON extraction failed and we have retries left, try again
                    if "Could not extract valid JSON" in str(json_err) and attempt < max_retries:
                        print(f"[AI Describer] ⚠️ JSON truncation detected. Retrying with attempt {attempt + 2}/{max_retries + 1}")
                        time.sleep(2)  # Short delay before retry
                        continue
                    else:
                        raise
                
                # Validate and create schema
                description = SegmentDescription(**data)
                return description
            
            except Exception as e:
                error_msg = str(e)
                print(f"[AI Describer] ERROR on attempt {attempt + 1}/{max_retries + 1}: {type(e).__name__}: {e}")
                
                # Check if it's a rate limit error (429)
                if "429" in error_msg or "ResourceExhausted" in str(type(e).__name__):
                    if attempt < max_retries:
                        # Extract retry delay from error message if available
                        import re
                        match = re.search(r'retry in ([\d.]+)s', error_msg)
                        wait_time = float(match.group(1)) if match else retry_delay
                        wait_time = max(wait_time, 30)  # Minimum 30 seconds for free tier
                        
                        print(f"[AI Describer] ⏳ Rate limit hit. Waiting {wait_time:.1f}s before retry...")
                        time.sleep(wait_time)
                        continue  # Retry
                    else:
                        print(f"[AI Describer] ❌ Max retries reached for rate limit error")
                        raise RuntimeError(f"Segment description failed after {max_retries} retries: {e}")
                
                # Check if it's a timeout error (504)
                elif "504" in error_msg or "DeadlineExceeded" in str(type(e).__name__):
                    if attempt < max_retries:
                        print(f"[AI Describer] ⏳ Timeout error. Waiting {retry_delay}s before retry...")
                        time.sleep(retry_delay)
                        continue  # Retry
                    else:
                        print(f"[AI Describer] ❌ Max retries reached for timeout error")
                        raise RuntimeError(f"Segment description failed after {max_retries} retries: {e}")
                
                # Other errors - don't retry
                else:
                    raise RuntimeError(f"Segment description failed: {e}")
        
        # Should never reach here, but just in case
        raise RuntimeError("Segment description failed: Unknown error")
    
    def describe_from_paths(
        self,
        frame_paths: List[str | Path]
    ) -> SegmentDescription:
        """Convenience method accepting string paths"""
        paths = [Path(p) for p in frame_paths]
        return self.describe_segment(paths)


def quick_describe(frame_paths: List[Path]) -> dict:
    """Quick description returning raw dict"""
    describer = VideoSegmentDescriber()
    result = describer.describe_segment(frame_paths)
    return result.model_dump()
