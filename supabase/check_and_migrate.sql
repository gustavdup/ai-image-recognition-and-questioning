-- Check current table structure and missing columns
-- Note: Run this in your Supabase SQL editor or psql

-- Check if new columns exist
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns 
WHERE table_name = 'images' 
ORDER BY ordinal_position;

-- Check if we need to add any columns
DO $$
BEGIN
    -- Add confidence if missing
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'images' AND column_name = 'confidence') THEN
        ALTER TABLE images ADD COLUMN confidence FLOAT DEFAULT 0.0;
        RAISE NOTICE 'Added confidence column';
    END IF;
    
    -- Add token columns if missing
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'images' AND column_name = 'prompt_tokens') THEN
        ALTER TABLE images ADD COLUMN prompt_tokens INTEGER DEFAULT 0;
        ALTER TABLE images ADD COLUMN completion_tokens INTEGER DEFAULT 0;
        ALTER TABLE images ADD COLUMN total_tokens INTEGER DEFAULT 0;
        ALTER TABLE images ADD COLUMN analysis_attempts INTEGER DEFAULT 1;
        RAISE NOTICE 'Added token tracking and attempts columns';
    END IF;
END $$;
