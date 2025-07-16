# Image Recognition App

## Setup Instructions

### 1. Python Backend
- Create a virtual environment:
  ```cmd
  python -m venv venv
  venv\Scripts\activate
  pip install -r requirements.txt
  ```
- Copy `.env` and fill in your Supabase credentials.
- Run the app:
  ```cmd
  uvicorn app.main:app --reload
  ```

### 2. Supabase Edge Function
- Install Supabase CLI: https://supabase.com/docs/guides/cli
- Deploy function:
  ```cmd
  supabase functions deploy on-image-upload
  supabase functions invoke on-image-upload
  ```

### 3. Database Setup
- Run the SQL in `supabase/images_table.sql` to create the basic `images` table.
- **Required**: Apply `supabase/schema_update.sql` to add AI features (description, tags, embeddings).
- **Optional**: Apply `supabase/enhanced_schema.sql` for advanced search functions and indexes.

### 4. Webhook Configuration
- In your Supabase dashboard, go to Database > Webhooks
- Create a new webhook:
  - **Name**: `on-image-upload`
  - **Table**: `storage.objects`
  - **Events**: `INSERT`
  - **Type**: `HTTP Request`
  - **HTTP URL**: Your Edge Function URL
  - **HTTP Method**: `POST`
  - **HTTP Headers**: Add `Authorization: Bearer YOUR_ANON_KEY`

### 5. Frontend
- Access the upload UI at `http://localhost:8000/upload`

---

## Features

### 🤖 AI-Powered Analysis
- **Image Recognition**: Uses GPT-4-turbo Vision API to analyze uploaded images
- **Rich Tagging**: Extracts colors, objects, shapes, mood, setting, style, and more
- **Text Detection**: Identifies and extracts text content from images
- **Semantic Search**: Vector embeddings enable similarity-based image search

### 📊 Database Schema
- **Basic Info**: ID, filename, URL, upload timestamp
- **AI Metadata**: Description, structured tags (JSONB), raw AI response
- **Search Features**: Vector embeddings for semantic similarity
- **Performance**: Optimized indexes for tag-based filtering

### 🔧 Advanced Queries
- **Hybrid Search**: Combine semantic similarity with tag filtering
- **Analytics Views**: Popular tags, content distribution, processing stats
- **Monitoring**: System health, success rates, recent activity

---

## File Structure
- `app/` - FastAPI backend with image upload handling
- `static/` - JavaScript and CSS for upload UI
- `templates/` - HTML upload form template
- `supabase/` - Database and Edge Function code
  - `images_table.sql` - Basic table creation
  - `schema_update.sql` - AI features (required)
  - `enhanced_schema.sql` - Advanced search functions (optional)
  - `monitoring_queries.sql` - Analytics and monitoring queries
  - `functions/on-image-upload/` - Edge function for AI processing
- `.env` - Configuration file for API keys
- `requirements.txt` - Python dependencies

## Monitoring & Analytics

Use the queries in `supabase/monitoring_queries.sql` to:
- Check system health and processing success rates
- Analyze content distribution and popular tags
- Monitor recent upload activity and performance
- Identify failed processing attempts
- Track storage usage and image quality metrics
