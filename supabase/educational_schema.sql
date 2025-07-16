-- Educational flashcard schema - Updated for current tag structure
-- Run this AFTER applying cleanup_old_schema.sql

-- First drop any old indexes that have changed structure
DROP INDEX IF EXISTS idx_images_tags_colors;
DROP INDEX IF EXISTS idx_images_tags_objects;

-- Add indexes for educational flashcard queries
CREATE INDEX IF NOT EXISTS idx_images_tags_educational_category ON images USING GIN ((tags->'educationalContext'->'category'));
CREATE INDEX IF NOT EXISTS idx_images_tags_colors ON images USING GIN ((tags->'colorAnalysis'->'distinctColors'));
CREATE INDEX IF NOT EXISTS idx_images_tags_objects ON images USING GIN ((tags->'objects'->'realWorldItems'));
CREATE INDEX IF NOT EXISTS idx_images_tags_shapes ON images USING GIN ((tags->'shapes'->'geometricShapes'));
CREATE INDEX IF NOT EXISTS idx_images_tags_letters ON images USING GIN ((tags->'textContent'->'letters'));
CREATE INDEX IF NOT EXISTS idx_images_tags_numbers ON images USING GIN ((tags->'textContent'->'numbers'));
CREATE INDEX IF NOT EXISTS idx_images_tags_people ON images USING GIN ((tags->'people'));
CREATE INDEX IF NOT EXISTS idx_images_tags_animals ON images USING GIN ((tags->'animals'));

-- Function to search educational flashcards by content
CREATE OR REPLACE FUNCTION search_educational_images(
  category_filter TEXT DEFAULT NULL,
  has_letters BOOLEAN DEFAULT NULL,
  has_numbers BOOLEAN DEFAULT NULL,
  has_shapes BOOLEAN DEFAULT NULL,
  has_objects BOOLEAN DEFAULT NULL,
  color_filter TEXT DEFAULT NULL,
  difficulty_filter TEXT DEFAULT NULL,
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
    (category_filter IS NULL OR tags->'educationalContext'->>'category' = category_filter)
    AND (difficulty_filter IS NULL OR tags->'educationalContext'->>'difficulty' = difficulty_filter)
    AND (color_filter IS NULL OR tags->'colorAnalysis'->'distinctColors' ? color_filter)
    AND (has_letters IS NULL OR 
         CASE WHEN has_letters THEN jsonb_array_length(COALESCE(tags->'textContent'->'letters', '[]'::jsonb)) > 0 
              ELSE jsonb_array_length(COALESCE(tags->'textContent'->'letters', '[]'::jsonb)) = 0 END)
    AND (has_numbers IS NULL OR 
         CASE WHEN has_numbers THEN jsonb_array_length(COALESCE(tags->'textContent'->'numbers', '[]'::jsonb)) > 0 
              ELSE jsonb_array_length(COALESCE(tags->'textContent'->'numbers', '[]'::jsonb)) = 0 END)
    AND (has_shapes IS NULL OR 
         CASE WHEN has_shapes THEN jsonb_array_length(COALESCE(tags->'shapes'->'geometricShapes', '[]'::jsonb)) > 0 
              ELSE jsonb_array_length(COALESCE(tags->'shapes'->'geometricShapes', '[]'::jsonb)) = 0 END)
    AND (has_objects IS NULL OR 
         CASE WHEN has_objects THEN jsonb_array_length(COALESCE(tags->'objects'->'realWorldItems', '[]'::jsonb)) > 0 
              ELSE jsonb_array_length(COALESCE(tags->'objects'->'realWorldItems', '[]'::jsonb)) = 0 END)
  ORDER BY created_at DESC
  LIMIT limit_count;
$$;

-- Enhanced hybrid search for educational content
CREATE OR REPLACE FUNCTION search_educational_hybrid(
  query_embedding VECTOR(1536) DEFAULT NULL,
  similarity_threshold FLOAT DEFAULT 0.7,
  category_filter TEXT DEFAULT NULL,
  difficulty_filter TEXT DEFAULT NULL,
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
    AND (category_filter IS NULL OR tags->'educationalContext'->>'category' = category_filter)
    AND (difficulty_filter IS NULL OR tags->'educationalContext'->>'difficulty' = difficulty_filter)
  ORDER BY 
    CASE 
      WHEN query_embedding IS NOT NULL THEN embedding <-> query_embedding
      ELSE EXTRACT(EPOCH FROM created_at)
    END
  LIMIT match_count;
$$;

-- Educational analytics views
CREATE OR REPLACE VIEW educational_analytics AS
SELECT 
  COUNT(*) as total_images,
  COUNT(CASE WHEN tags IS NOT NULL THEN 1 END) as analyzed_images,
  COUNT(CASE WHEN embedding IS NOT NULL THEN 1 END) as searchable_images,
  COUNT(CASE WHEN tags->'educationalContext' IS NOT NULL THEN 1 END) as educational_images,
  AVG(confidence) as avg_confidence,
  SUM(total_tokens) as total_tokens_used,
  AVG(total_tokens) as avg_tokens_per_image,
  SUM(prompt_tokens) as total_prompt_tokens,
  SUM(completion_tokens) as total_completion_tokens
FROM images;

-- Educational category breakdown
CREATE OR REPLACE VIEW educational_categories AS
SELECT 
  COALESCE(tags->'educationalContext'->>'category', 'unknown') as category,
  COALESCE(tags->'educationalContext'->>'difficulty', 'unknown') as difficulty,
  COUNT(*) as count
FROM images 
WHERE tags->'educationalContext' IS NOT NULL
GROUP BY tags->'educationalContext'->>'category', tags->'educationalContext'->>'difficulty'
ORDER BY category, difficulty;

-- Content type breakdown for educational flashcards
CREATE OR REPLACE VIEW educational_content_types AS
SELECT 
  'Letters' as content_type,
  COUNT(*) as count
FROM images 
WHERE jsonb_array_length(COALESCE(tags->'textContent'->'letters', '[]'::jsonb)) > 0

UNION ALL

SELECT 
  'Numbers' as content_type,
  COUNT(*) as count
FROM images 
WHERE jsonb_array_length(COALESCE(tags->'textContent'->'numbers', '[]'::jsonb)) > 0

UNION ALL

SELECT 
  'Shapes' as content_type,
  COUNT(*) as count
FROM images 
WHERE jsonb_array_length(COALESCE(tags->'shapes'->'geometricShapes', '[]'::jsonb)) > 0

UNION ALL

SELECT 
  'Objects' as content_type,
  COUNT(*) as count
FROM images 
WHERE jsonb_array_length(COALESCE(tags->'objects'->'realWorldItems', '[]'::jsonb)) > 0

UNION ALL

SELECT 
  'People' as content_type,
  COUNT(*) as count
FROM images 
WHERE jsonb_array_length(COALESCE(tags->'people', '[]'::jsonb)) > 0

UNION ALL

SELECT 
  'Animals' as content_type,
  COUNT(*) as count
FROM images 
WHERE jsonb_array_length(COALESCE(tags->'animals', '[]'::jsonb)) > 0

ORDER BY count DESC;

-- Popular educational tags
CREATE OR REPLACE VIEW popular_educational_tags AS
SELECT 
  tag_type,
  tag_value,
  COUNT(*) as frequency
FROM (
  SELECT 'color' as tag_type, jsonb_array_elements_text(tags->'colorAnalysis'->'distinctColors') as tag_value 
  FROM images WHERE tags->'colorAnalysis'->'distinctColors' IS NOT NULL
  
  UNION ALL
  
  SELECT 'object' as tag_type, jsonb_array_elements_text(tags->'objects'->'realWorldItems') as tag_value 
  FROM images WHERE tags->'objects'->'realWorldItems' IS NOT NULL
  
  UNION ALL
  
  SELECT 'shape' as tag_type, jsonb_array_elements_text(tags->'shapes'->'geometricShapes') as tag_value 
  FROM images WHERE tags->'shapes'->'geometricShapes' IS NOT NULL
  
  UNION ALL
  
  SELECT 'letter' as tag_type, jsonb_array_elements_text(tags->'textContent'->'letters') as tag_value 
  FROM images WHERE tags->'textContent'->'letters' IS NOT NULL
  
  UNION ALL
  
  SELECT 'number' as tag_type, jsonb_array_elements_text(tags->'textContent'->'numbers') as tag_value 
  FROM images WHERE tags->'textContent'->'numbers' IS NOT NULL
  
  UNION ALL
  
  SELECT 'category' as tag_type, tags->'educationalContext'->>'category' as tag_value 
  FROM images WHERE tags->'educationalContext'->>'category' IS NOT NULL
  
  UNION ALL
  
  SELECT 'difficulty' as tag_type, tags->'educationalContext'->>'difficulty' as tag_value 
  FROM images WHERE tags->'educationalContext'->>'difficulty' IS NOT NULL
  
  UNION ALL
  
  SELECT 'people' as tag_type, jsonb_array_elements_text(tags->'people') as tag_value 
  FROM images WHERE tags->'people' IS NOT NULL
  
  UNION ALL
  
  SELECT 'animal' as tag_type, jsonb_array_elements_text(tags->'animals') as tag_value 
  FROM images WHERE tags->'animals' IS NOT NULL
) tag_frequency
GROUP BY tag_type, tag_value
ORDER BY tag_type, frequency DESC;

-- Grant permissions (adjust role name as needed)
-- GRANT EXECUTE ON FUNCTION search_educational_images TO authenticated;
-- GRANT EXECUTE ON FUNCTION search_educational_hybrid TO authenticated;
