-- Cleanup script to remove outdated schema elements
-- Run this BEFORE applying educational_schema.sql

-- Drop outdated indexes that don't match our current tag structure
DROP INDEX IF EXISTS idx_images_tags_category;
DROP INDEX IF EXISTS idx_images_tags_content_type;
DROP INDEX IF EXISTS idx_images_tags_mood;
DROP INDEX IF EXISTS idx_images_tags_setting;

-- Drop outdated search functions
DROP FUNCTION IF EXISTS search_images_by_tags(TEXT, TEXT, TEXT, TEXT, TEXT, TEXT, INT);
DROP FUNCTION IF EXISTS search_images_hybrid(VECTOR, FLOAT, TEXT, TEXT, INT);

-- Drop outdated analytics views
DROP VIEW IF EXISTS category_analytics;
DROP VIEW IF EXISTS content_type_analytics;
DROP VIEW IF EXISTS popular_tags;

-- Note: We keep these as they're still relevant:
-- - idx_images_tags_colors (will be updated in educational_schema.sql)
-- - idx_images_tags_objects (will be updated in educational_schema.sql)
-- - image_analytics (still useful basic stats)

-- The educational_schema.sql will create new, updated versions of:
-- - Indexes that match the nested tag structure
-- - Functions that work with educational content
-- - Views that provide educational insights
