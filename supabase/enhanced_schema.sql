-- Enhanced database schema for better performance and querying
-- Run this AFTER applying the basic schema_update.sql

-- Add indexes for common JSONB queries
CREATE INDEX IF NOT EXISTS idx_images_tags_colors ON images USING GIN ((tags->'colors'));
CREATE INDEX IF NOT EXISTS idx_images_tags_objects ON images USING GIN ((tags->'objects'));
CREATE INDEX IF NOT EXISTS idx_images_tags_category ON images USING GIN ((tags->'category'));
CREATE INDEX IF NOT EXISTS idx_images_tags_content_type ON images USING GIN ((tags->'contentType'));
CREATE INDEX IF NOT EXISTS idx_images_tags_mood ON images USING GIN ((tags->'mood'));
CREATE INDEX IF NOT EXISTS idx_images_tags_setting ON images USING GIN ((tags->'setting'));

-- Add a function to search by specific tag categories
CREATE OR REPLACE FUNCTION search_images_by_tags(
  category_filter TEXT DEFAULT NULL,
  content_type_filter TEXT DEFAULT NULL,
  color_filter TEXT DEFAULT NULL,
  object_filter TEXT DEFAULT NULL,
  mood_filter TEXT DEFAULT NULL,
  setting_filter TEXT DEFAULT NULL,
  limit_count INT DEFAULT 20
)
RETURNS TABLE (
  id UUID,
  image_name TEXT,
  image_url TEXT,
  description TEXT,
  tags JSONB,
  created_at TIMESTAMPTZ
)
LANGUAGE SQL
AS $$
  SELECT
    id,
    image_name,
    image_url,
    description,
    tags,
    created_at
  FROM images
  WHERE 
    (category_filter IS NULL OR tags->>'category' = category_filter)
    AND (content_type_filter IS NULL OR tags->>'contentType' = content_type_filter)
    AND (color_filter IS NULL OR tags->'colors' ? color_filter)
    AND (object_filter IS NULL OR tags->'objects' ? object_filter)
    AND (mood_filter IS NULL OR tags->>'mood' = mood_filter)
    AND (setting_filter IS NULL OR tags->>'setting' = setting_filter)
  ORDER BY created_at DESC
  LIMIT limit_count;
$$;

-- Add a function for combined semantic + tag search
CREATE OR REPLACE FUNCTION search_images_hybrid(
  query_embedding VECTOR(1536) DEFAULT NULL,
  similarity_threshold FLOAT DEFAULT 0.7,
  category_filter TEXT DEFAULT NULL,
  content_type_filter TEXT DEFAULT NULL,
  match_count INT DEFAULT 10
)
RETURNS TABLE (
  id UUID,
  image_name TEXT,
  image_url TEXT,
  description TEXT,
  tags JSONB,
  similarity FLOAT,
  created_at TIMESTAMPTZ
)
LANGUAGE SQL
AS $$
  SELECT
    id,
    image_name,
    image_url,
    description,
    tags,
    CASE 
      WHEN query_embedding IS NOT NULL THEN 1 - (embedding <-> query_embedding)
      ELSE NULL 
    END AS similarity,
    created_at
  FROM images
  WHERE 
    embedding IS NOT NULL
    AND (query_embedding IS NULL OR 1 - (embedding <-> query_embedding) > similarity_threshold)
    AND (category_filter IS NULL OR tags->>'category' = category_filter)
    AND (content_type_filter IS NULL OR tags->>'contentType' = content_type_filter)
  ORDER BY 
    CASE 
      WHEN query_embedding IS NOT NULL THEN embedding <-> query_embedding
      ELSE EXTRACT(EPOCH FROM created_at)
    END
  LIMIT match_count;
$$;

-- Add useful views for analytics
CREATE OR REPLACE VIEW image_analytics AS
SELECT 
  COUNT(*) as total_images,
  COUNT(CASE WHEN tags IS NOT NULL THEN 1 END) as analyzed_images,
  COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) as searchable_images
FROM images;

-- Separate view for category counts
CREATE OR REPLACE VIEW category_analytics AS
SELECT 
  COALESCE(tags->>'category', 'unknown') as category,
  COUNT(*) as count
FROM images 
WHERE tags IS NOT NULL
GROUP BY tags->>'category'
ORDER BY count DESC;

-- Separate view for content type counts
CREATE OR REPLACE VIEW content_type_analytics AS
SELECT 
  COALESCE(tags->>'contentType', 'unknown') as content_type,
  COUNT(*) as count
FROM images 
WHERE tags IS NOT NULL
GROUP BY tags->>'contentType'
ORDER BY count DESC;

-- Add a view for popular tags
CREATE OR REPLACE VIEW popular_tags AS
SELECT 
  tag_type,
  tag_value,
  COUNT(*) as frequency
FROM (
  SELECT 'color' as tag_type, jsonb_array_elements_text(tags->'colors') as tag_value FROM images WHERE tags->'colors' IS NOT NULL
  UNION ALL
  SELECT 'object' as tag_type, jsonb_array_elements_text(tags->'objects') as tag_value FROM images WHERE tags->'objects' IS NOT NULL
  UNION ALL
  SELECT 'shape' as tag_type, jsonb_array_elements_text(tags->'shapes') as tag_value FROM images WHERE tags->'shapes' IS NOT NULL
  UNION ALL
  SELECT 'category' as tag_type, tags->>'category' as tag_value FROM images WHERE tags->>'category' IS NOT NULL
  UNION ALL
  SELECT 'mood' as tag_type, tags->>'mood' as tag_value FROM images WHERE tags->>'mood' IS NOT NULL
  UNION ALL
  SELECT 'setting' as tag_type, tags->>'setting' as tag_value FROM images WHERE tags->>'setting' IS NOT NULL
) tag_frequency
GROUP BY tag_type, tag_value
ORDER BY tag_type, frequency DESC;
