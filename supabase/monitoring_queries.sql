-- Monitoring and Analytics Queries for Image Recognition System
-- Use these queries to monitor system performance and analyze usage

-- 1. System Health Overview
SELECT 
  'Total Images' as metric,
  COUNT(*)::TEXT as value
FROM images
UNION ALL
SELECT 
  'Analyzed Images',
  COUNT(*)::TEXT
FROM images 
WHERE tags IS NOT NULL
UNION ALL
SELECT 
  'Searchable Images',
  COUNT(*)::TEXT
FROM images 
WHERE embedding IS NOT NULL
UNION ALL
SELECT 
  'Analysis Success Rate',
  ROUND(
    COUNT(*) FILTER (WHERE tags IS NOT NULL) * 100.0 / NULLIF(COUNT(*), 0), 
    2
  )::TEXT || '%'
FROM images;

-- 2. Recent Upload Activity (last 24 hours)
SELECT 
  DATE_TRUNC('hour', created_at) as hour,
  COUNT(*) as uploads,
  COUNT(*) FILTER (WHERE tags IS NOT NULL) as analyzed,
  ROUND(
    COUNT(*) FILTER (WHERE tags IS NOT NULL) * 100.0 / COUNT(*), 
    1
  ) as success_rate_percent
FROM images 
WHERE created_at > NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', created_at)
ORDER BY hour DESC;

-- 3. Content Analysis Breakdown
SELECT 
  tags->>'category' as category,
  tags->>'contentType' as content_type,
  COUNT(*) as count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as percentage
FROM images 
WHERE tags IS NOT NULL
GROUP BY tags->>'category', tags->>'contentType'
ORDER BY count DESC;

-- 4. Popular Colors and Objects
WITH color_stats AS (
  SELECT 
    jsonb_array_elements_text(tags->'colors') as color,
    COUNT(*) as frequency
  FROM images 
  WHERE tags->'colors' IS NOT NULL
  GROUP BY jsonb_array_elements_text(tags->'colors')
  ORDER BY frequency DESC
  LIMIT 10
),
object_stats AS (
  SELECT 
    jsonb_array_elements_text(tags->'objects') as object,
    COUNT(*) as frequency
  FROM images 
  WHERE tags->'objects' IS NOT NULL
  GROUP BY jsonb_array_elements_text(tags->'objects')
  ORDER BY frequency DESC
  LIMIT 10
)
SELECT 'color' as type, color as value, frequency FROM color_stats
UNION ALL
SELECT 'object' as type, object as value, frequency FROM object_stats
ORDER BY type, frequency DESC;

-- 5. Performance Analysis (if you have timing data)
-- Note: This would require adding timing data to your database
SELECT 
  'Recent Processing Times' as metric,
  'N/A - Add timing to Edge Function' as note;

-- 6. Failed Processing Detection
-- Images uploaded but not analyzed (potential issues)
SELECT 
  id,
  image_name,
  created_at,
  CASE 
    WHEN tags IS NULL AND embedding IS NULL THEN 'No Analysis'
    WHEN tags IS NOT NULL AND embedding IS NULL THEN 'Missing Embedding'
    WHEN tags IS NULL AND embedding IS NOT NULL THEN 'Missing Tags'
    ELSE 'Complete'
  END as status
FROM images 
WHERE created_at > NOW() - INTERVAL '1 day'
  AND (tags IS NULL OR embedding IS NULL)
ORDER BY created_at DESC;

-- 7. Storage Usage Estimation
SELECT 
  COUNT(*) as total_images,
  ROUND(
    COUNT(*) * 0.5, -- Rough estimate: 500KB per image
    2
  ) as estimated_storage_mb,
  COUNT(*) FILTER (WHERE tags IS NOT NULL) as processed_images,
  COUNT(*) FILTER (WHERE embedding IS NOT NULL) as indexed_images;

-- 8. Image Quality Distribution
SELECT 
  tags->>'quality' as quality,
  COUNT(*) as count,
  ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) as percentage
FROM images 
WHERE tags->>'quality' IS NOT NULL
GROUP BY tags->>'quality'
ORDER BY 
  CASE tags->>'quality' 
    WHEN 'high' THEN 1 
    WHEN 'medium' THEN 2 
    WHEN 'low' THEN 3 
    ELSE 4 
  END;

-- 9. Mood and Setting Analysis
SELECT 
  'Mood Distribution' as analysis_type,
  tags->>'mood' as value,
  COUNT(*) as count
FROM images 
WHERE tags->>'mood' IS NOT NULL
GROUP BY tags->>'mood'
UNION ALL
SELECT 
  'Setting Distribution',
  tags->>'setting',
  COUNT(*)
FROM images 
WHERE tags->>'setting' IS NOT NULL
GROUP BY tags->>'setting'
ORDER BY analysis_type, count DESC;

-- 10. Text Detection Summary
SELECT 
  CASE 
    WHEN tags->>'text' IS NULL OR tags->>'text' = 'null' THEN 'No Text'
    WHEN LENGTH(tags->>'text') > 0 THEN 'Text Detected'
    ELSE 'Unknown'
  END as text_status,
  tags->>'textLanguage' as detected_language,
  COUNT(*) as count
FROM images 
WHERE tags IS NOT NULL
GROUP BY 
  CASE 
    WHEN tags->>'text' IS NULL OR tags->>'text' = 'null' THEN 'No Text'
    WHEN LENGTH(tags->>'text') > 0 THEN 'Text Detected'
    ELSE 'Unknown'
  END,
  tags->>'textLanguage'
ORDER BY count DESC;
