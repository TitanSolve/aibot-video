-- Migration: Update Segment taxonomy from generic to requirements-aligned schema
-- This migration updates the segments table to match the animation-focused taxonomy

-- Drop old indexes
DROP INDEX IF EXISTS idx_segments_animation_type;
DROP INDEX IF EXISTS idx_segments_motion_style;
DROP INDEX IF EXISTS idx_segments_easing;
DROP INDEX IF EXISTS idx_segments_tempo;
DROP INDEX IF EXISTS idx_segments_complexity;
DROP INDEX IF EXISTS idx_segments_interaction_type;
DROP INDEX IF EXISTS idx_segments_visual_hierarchy;
DROP INDEX IF EXISTS idx_segments_brand_identity;

-- Drop old columns
ALTER TABLE segments
  DROP COLUMN IF EXISTS keyframe_path,
  DROP COLUMN IF EXISTS ui_elements,
  DROP COLUMN IF EXISTS visual_hierarchy,
  DROP COLUMN IF EXISTS animation_type,
  DROP COLUMN IF EXISTS motion_style,
  DROP COLUMN IF EXISTS easing,
  DROP COLUMN IF EXISTS tempo,
  DROP COLUMN IF EXISTS complexity,
  DROP COLUMN IF EXISTS interaction_type,
  DROP COLUMN IF EXISTS style,
  DROP COLUMN IF EXISTS brand_identity,
  DROP COLUMN IF EXISTS performance_note,
  DROP COLUMN IF EXISTS accessibility_note;

-- Add new columns (requirements-aligned taxonomy)
ALTER TABLE segments
  ADD COLUMN IF NOT EXISTS keyframe_paths JSONB,
  ADD COLUMN IF NOT EXISTS motion_type JSONB,
  ADD COLUMN IF NOT EXISTS ui_elements_animated JSONB,
  ADD COLUMN IF NOT EXISTS timing_function VARCHAR(100),
  ADD COLUMN IF NOT EXISTS speed VARCHAR(50),
  ADD COLUMN IF NOT EXISTS motion_character VARCHAR(100),
  ADD COLUMN IF NOT EXISTS animation_pattern JSONB,
  ADD COLUMN IF NOT EXISTS usage_state VARCHAR(50),
  ADD COLUMN IF NOT EXISTS reusability JSONB,
  ADD COLUMN IF NOT EXISTS design_style VARCHAR(100),
  ADD COLUMN IF NOT EXISTS storyline TEXT,
  ADD COLUMN IF NOT EXISTS visual_uniqueness VARCHAR(50);

-- Create new indexes for filtering
CREATE INDEX IF NOT EXISTS idx_segments_timing_function ON segments(timing_function);
CREATE INDEX IF NOT EXISTS idx_segments_speed ON segments(speed);
CREATE INDEX IF NOT EXISTS idx_segments_usage_state ON segments(usage_state);
CREATE INDEX IF NOT EXISTS idx_segments_design_style ON segments(design_style);
CREATE INDEX IF NOT EXISTS idx_segments_mood ON segments(mood);

-- Create GIN indexes for JSONB array fields
CREATE INDEX IF NOT EXISTS idx_segments_motion_type ON segments USING GIN(motion_type);
CREATE INDEX IF NOT EXISTS idx_segments_ui_elements_animated ON segments USING GIN(ui_elements_animated);
CREATE INDEX IF NOT EXISTS idx_segments_animation_pattern ON segments USING GIN(animation_pattern);
CREATE INDEX IF NOT EXISTS idx_segments_reusability ON segments USING GIN(reusability);
CREATE INDEX IF NOT EXISTS idx_segments_industries ON segments USING GIN(industries);
CREATE INDEX IF NOT EXISTS idx_segments_metaphors ON segments USING GIN(metaphors);

-- Verify changes
SELECT 
  column_name, 
  data_type, 
  is_nullable
FROM information_schema.columns 
WHERE table_name = 'segments' 
ORDER BY ordinal_position;
