-- Step 1: Enable pgvector extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS vector;

-- Step 2: Add new columns to the images table
ALTER TABLE images
  ADD COLUMN description TEXT,
  ADD COLUMN confidence FLOAT DEFAULT 0.0,
  ADD COLUMN tags JSONB,
  ADD COLUMN raw_json JSONB,
  ADD COLUMN embedding VECTOR(1536),
  ADD COLUMN prompt_tokens INTEGER DEFAULT 0,
  ADD COLUMN completion_tokens INTEGER DEFAULT 0,
  ADD COLUMN total_tokens INTEGER DEFAULT 0,
  ADD COLUMN analysis_attempts INTEGER DEFAULT 1;

-- Step 3: Create index for semantic search (optional but recommended)
CREATE INDEX ON images USING ivfflat (embedding vector_l2_ops) WITH (lists = 100);

-- Step 4: Create a function for semantic similarity search
CREATE OR REPLACE FUNCTION search_similar_images(
  query_embedding VECTOR(1536),
  similarity_threshold FLOAT DEFAULT 0.8,
  match_count INT DEFAULT 10
)
RETURNS TABLE (
  id UUID,
  image_name TEXT,
  image_url TEXT,
  description TEXT,
  confidence FLOAT,
  tags JSONB,
  similarity FLOAT
)
LANGUAGE SQL
AS $$
  SELECT
    id,
    image_name,
    image_url,
    description,
    confidence,
    tags,
    1 - (embedding <-> query_embedding) AS similarity
  FROM images
  WHERE embedding IS NOT NULL
    AND 1 - (embedding <-> query_embedding) > similarity_threshold
  ORDER BY embedding <-> query_embedding
  LIMIT match_count;
$$;
