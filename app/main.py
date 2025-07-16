import os
import uuid
from datetime import datetime
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import httpx
from PIL import Image
import io
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from question_generator import QuestionGenerator, QuestionSet

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_BUCKET_NAME = os.getenv("SUPABASE_BUCKET_NAME", "images")

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

def resize_image_for_vision_api(image_file, max_width=512, max_height=512, quality=75):
    """
    Resize image to reduce token costs for OpenAI Vision API.
    
    AGGRESSIVE SIZING FOR TOKEN COST TESTING:
    Target: ~512x512 or smaller to minimize token usage
    This should reduce image tokens from 8000+ to 200-500 tokens
    """
    try:
        # Open the image
        image = Image.open(image_file)
        original_size = image.size
        
        # Convert to RGB if necessary (handles RGBA, grayscale, etc.)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        # Calculate new size maintaining aspect ratio
        width, height = image.size
        aspect_ratio = width / height
        
        if width > max_width or height > max_height:
            if aspect_ratio > 1:  # Landscape
                new_width = min(width, max_width)
                new_height = int(new_width / aspect_ratio)
            else:  # Portrait
                new_height = min(height, max_height)
                new_width = int(new_height * aspect_ratio)
            
            # Ensure we don't exceed maximum dimensions
            if new_width > max_width:
                new_width = max_width
                new_height = int(new_width / aspect_ratio)
            if new_height > max_height:
                new_height = max_height
                new_width = int(new_height * aspect_ratio)
            
            # Resize the image
            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
        # Save to bytes buffer
        output_buffer = io.BytesIO()
        image.save(output_buffer, format='JPEG', quality=quality, optimize=True)
        output_buffer.seek(0)
        
        new_size = image.size
        compression_ratio = len(output_buffer.getvalue()) / len(image_file.read())
        image_file.seek(0)  # Reset file pointer
        
        print(f"🖼️ Image resized: {original_size} -> {new_size}, compression: {compression_ratio:.2f}")
        
        return output_buffer
        
    except Exception as e:
        print(f"❌ Image resize error: {e}")
        # Return original file if resize fails
        image_file.seek(0)
        return image_file

@app.get("/")
def root():
    return {"message": "Image Recognition API", "routes": {"upload": "/upload", "gallery": "/gallery", "api": "/api/images"}}

@app.get("/upload", response_class=HTMLResponse)
def upload_form(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})

@app.get("/gallery", response_class=HTMLResponse)
def gallery_page(request: Request):
    return templates.TemplateResponse("gallery.html", {"request": request})

@app.get("/detailed", response_class=HTMLResponse)
def detailed_view(request: Request):
    return templates.TemplateResponse("detailed_view.html", {"request": request})

@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        return {"error": "Supabase config missing"}
    
    if not file.filename:
        return {"error": "No filename provided"}
    
    # Check if file is an image
    if not file.content_type or not file.content_type.startswith('image/'):
        return {"error": "Only image files are allowed"}
    
    print(f"📤 Processing upload: {file.filename} ({file.content_type})")
    
    # Get original file size for debugging
    original_data = await file.read()
    original_size_bytes = len(original_data)
    original_size_mb = original_size_bytes / (1024 * 1024)
    
    print(f"📏 Original file size: {original_size_bytes:,} bytes ({original_size_mb:.2f} MB)")
    
    # Reset file pointer for resizing
    file.file.seek(0)
    
    # Resize image to reduce Vision API token costs
    try:
        resized_image = resize_image_for_vision_api(file.file)
        data = resized_image.getvalue()
        final_size_bytes = len(data)
        final_size_mb = final_size_bytes / (1024 * 1024)
        reduction_ratio = (original_size_bytes - final_size_bytes) / original_size_bytes * 100
        
        print(f"💾 Resized image size: {final_size_bytes:,} bytes ({final_size_mb:.2f} MB)")
        print(f"📉 Size reduction: {reduction_ratio:.1f}%")
        
        # 🚨 WARN ABOUT POTENTIALLY HIGH TOKEN USAGE
        if final_size_mb > 5:
            print(f"🚨 WARNING: Large image file ({final_size_mb:.1f} MB) may cause high token usage!")
        elif final_size_mb > 2:
            print(f"⚠️ Moderate size image ({final_size_mb:.1f} MB) - may use more tokens")
        else:
            print(f"✅ Good size for Vision API ({final_size_mb:.1f} MB)")
            
    except Exception as resize_error:
        print(f"⚠️ Resize failed, using original: {resize_error}")
        data = original_data
    
    # Generate UUID filename with original extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    filename = f"{uuid.uuid4()}{file_ext}"
    
    async with httpx.AsyncClient() as client:
        upload_url = f"{SUPABASE_URL}/storage/v1/object/{SUPABASE_BUCKET_NAME}/{filename}"
        headers = {
            "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": "image/jpeg"  # Always JPEG after resize
        }
        resp = await client.post(upload_url, headers=headers, content=data)
        if resp.status_code == 200:
            print(f"✅ Upload successful: {filename}")
            return {"success": True, "filename": filename}
        print(f"❌ Upload failed: {resp.status_code} - {resp.text}")
        return {"success": False, "error": resp.text}

@app.get("/api/images")
async def get_images():
    """Get all images with their AI analysis data"""
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        return JSONResponse(
            status_code=500,
            content={"error": "Supabase config missing"}
        )
    
    try:
        async with httpx.AsyncClient() as client:
            # Get all images
            images_url = f"{SUPABASE_URL}/rest/v1/images"
            headers = {
                "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
                "apikey": SUPABASE_SERVICE_ROLE_KEY,
                "Content-Type": "application/json"
            }
            
            # Query with ordering by created_at descending
            params = {
                "select": "id,image_name,image_url,description,confidence,tags,prompt_tokens,completion_tokens,total_tokens,analysis_attempts,created_at",
                "order": "created_at.desc"
            }
            
            resp = await client.get(images_url, headers=headers, params=params)
            
            if resp.status_code != 200:
                return JSONResponse(
                    status_code=resp.status_code,
                    content={"error": f"Database error: {resp.text}"}
                )
            
            images = resp.json()
            
            # Generate signed URLs for each image if bucket is private
            for image in images:
                # Try to create a signed URL for display
                signed_url_endpoint = f"{SUPABASE_URL}/storage/v1/object/sign/{SUPABASE_BUCKET_NAME}/{image['image_name']}"
                sign_payload = {"expiresIn": 3600}  # 1 hour
                
                sign_resp = await client.post(
                    signed_url_endpoint,
                    headers=headers,
                    json=sign_payload
                )
                
                if sign_resp.status_code == 200:
                    sign_data = sign_resp.json()
                    # Update the image URL to use signed URL for display
                    image['display_url'] = f"{SUPABASE_URL}/storage/v1{sign_data['signedURL']}"
                else:
                    # Fallback to original URL (works if bucket is public)
                    image['display_url'] = image['image_url']
            
            # Get stats
            stats = {
                "total": len(images),
                "analyzed": len([img for img in images if img.get("tags")]),
                "searchable": len([img for img in images if img.get("tags")])  # Assuming if tags exist, embedding exists
            }
            
            return {
                "images": images,
                "stats": stats
            }
            
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to fetch images: {str(e)}"}
        )

@app.post("/api/generate-questions/{image_id}")
async def generate_questions(
    image_id: str, 
    difficulty: str = "elementary",
    num_questions: int = 5,
    question_types: str | None = None  # Comma-separated list like "identification,counting,spatial"
):
    """
    Generate educational questions for a specific image
    
    Args:
        image_id: UUID of the image
        difficulty: preschool, elementary, middle, high
        num_questions: Number of questions to generate (1-10)
        question_types: Optional comma-separated list of types to generate
    """
    try:
        # Validate parameters
        if num_questions < 1 or num_questions > 10:
            return JSONResponse(
                status_code=400,
                content={"error": "num_questions must be between 1 and 10"}
            )
        
        valid_difficulties = ["preschool", "elementary", "middle", "high"]
        if difficulty not in valid_difficulties:
            return JSONResponse(
                status_code=400,
                content={"error": f"difficulty must be one of: {', '.join(valid_difficulties)}"}
            )
        
        # Parse question types if provided
        types_list = None
        if question_types:
            types_list = [t.strip() for t in question_types.split(",")]
            valid_types = ["identification", "counting", "spatial", "true_false", "multiple_choice"]
            invalid_types = [t for t in types_list if t not in valid_types]
            if invalid_types:
                return JSONResponse(
                    status_code=400,
                    content={"error": f"Invalid question types: {', '.join(invalid_types)}. Valid types: {', '.join(valid_types)}"}
                )
        
        # Validate environment variables
        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            return JSONResponse(
                status_code=500,
                content={"error": "Missing Supabase configuration"}
            )
        
        # Fetch image data from Supabase
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SUPABASE_URL}/rest/v1/images",
                headers={
                    "apikey": SUPABASE_SERVICE_ROLE_KEY,
                    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
                },
                params={"id": f"eq.{image_id}", "select": "*"}
            )
            
            if response.status_code != 200:
                return JSONResponse(
                    status_code=500,
                    content={"error": f"Failed to fetch image data: {response.status_code}"}
                )
            
            images = response.json()
            if not images:
                return JSONResponse(
                    status_code=404,
                    content={"error": "Image not found"}
                )
            
            image_data = images[0]
            
            # Check if image has been analyzed
            if not image_data.get("tags"):
                return JSONResponse(
                    status_code=400,
                    content={"error": "Image has not been analyzed yet. Please wait for AI analysis to complete."}
                )
            
            # Generate questions
            print(f"🧠 Generating questions for image {image_id}")
            print(f"📝 Image data keys: {list(image_data.keys())}")
            print(f"🏷️ Tags type: {type(image_data.get('tags'))}")
            print(f"🏷️ Tags preview: {str(image_data.get('tags', {}))[:200]}...")
            
            generator = QuestionGenerator()
            question_set = await generator.generate_questions(
                image_data=image_data,
                difficulty_level=difficulty,
                num_questions=num_questions,
                question_types=types_list
            )
            
            return question_set.dict()
            
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to generate questions: {str(e)}"}
        )

@app.get("/api/question-types")
async def get_question_types():
    """Get available question types and difficulty levels"""
    return {
        "question_types": [
            {"value": "identification", "label": "Identification", "description": "What color/shape/object is this?"},
            {"value": "counting", "label": "Counting", "description": "How many items are there?"},
            {"value": "spatial", "label": "Spatial", "description": "Where is the object located?"},
            {"value": "true_false", "label": "True/False", "description": "True or false statements"},
            {"value": "multiple_choice", "label": "Multiple Choice", "description": "Choose from 4 options"},
            {"value": "comparison", "label": "Comparison", "description": "Compare across multiple images"}
        ],
        "difficulty_levels": [
            {"value": "preschool", "label": "Preschool", "description": "Ages 3-5"},
            {"value": "elementary", "label": "Elementary", "description": "Ages 5-10"},
            {"value": "middle", "label": "Middle School", "description": "Ages 10-14"},
            {"value": "high", "label": "High School", "description": "Ages 14-18"}
        ]
    }

@app.post("/api/generate-questions-multi")
async def generate_questions_multi(
    request: Request
):
    """
    Generate educational questions for multiple selected images
    
    Request body should contain:
    {
        "image_ids": ["id1", "id2", "id3"],
        "block_assignments": {"id1": "A", "id2": "B", "id3": "C"},
        "difficulty": "elementary",
        "num_questions": 5,
        "question_types": "counting,comparison,true_false,block_identification"
    }
    """
    try:
        body = await request.json()
        image_ids = body.get('image_ids', [])
        block_assignments = body.get('block_assignments', {})
        difficulty = body.get('difficulty', 'elementary')
        num_questions = body.get('num_questions', 5)
        question_types = body.get('question_types', None)
        
        # Validate parameters
        if not image_ids or len(image_ids) < 2:
            return JSONResponse(
                status_code=400,
                content={"error": "At least 2 image IDs are required for multi-image questions"}
            )
        
        if len(image_ids) > 10:
            return JSONResponse(
                status_code=400,
                content={"error": "Maximum 10 images allowed for multi-image questions"}
            )
        
        if num_questions < 1 or num_questions > 15:
            return JSONResponse(
                status_code=400,
                content={"error": "num_questions must be between 1 and 15 for multi-image questions"}
            )
        
        valid_difficulties = ["preschool", "elementary", "middle", "high"]
        if difficulty not in valid_difficulties:
            return JSONResponse(
                status_code=400,
                content={"error": f"difficulty must be one of: {', '.join(valid_difficulties)}"}
            )
        
        # Parse question types if provided
        types_list = None
        if question_types:
            types_list = [t.strip() for t in question_types.split(",")]
            valid_types = ["identification", "counting", "spatial", "true_false", "multiple_choice", "comparison", "block_identification"]
            invalid_types = [t for t in types_list if t not in valid_types]
            if invalid_types:
                return JSONResponse(
                    status_code=400,
                    content={"error": f"Invalid question types: {', '.join(invalid_types)}. Valid types: {', '.join(valid_types)}"}
                )
        
        # Validate environment variables
        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            return JSONResponse(
                status_code=500,
                content={"error": "Missing Supabase configuration"}
            )
        
        # Fetch all image data from Supabase
        async with httpx.AsyncClient() as client:
            # Build proper query for multiple IDs
            id_list = ",".join(f'"{img_id}"' for img_id in image_ids)
            
            response = await client.get(
                f"{SUPABASE_URL}/rest/v1/images",
                headers={
                    "apikey": SUPABASE_SERVICE_ROLE_KEY,
                    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
                },
                params={"select": "*", "id": f"in.({id_list})"}
            )
            
            if response.status_code != 200:
                return JSONResponse(
                    status_code=500,
                    content={"error": f"Failed to fetch image data: {response.status_code}"}
                )
            
            images = response.json()
            if len(images) != len(image_ids):
                found_ids = [img['id'] for img in images]
                missing_ids = [id for id in image_ids if id not in found_ids]
                return JSONResponse(
                    status_code=404,
                    content={"error": f"Images not found: {missing_ids}"}
                )
            
            # Check if all images have been analyzed
            unanalyzed_images = [img['id'] for img in images if not img.get("tags")]
            if unanalyzed_images:
                return JSONResponse(
                    status_code=400,
                    content={"error": f"Some images have not been analyzed yet: {unanalyzed_images}. Please wait for AI analysis to complete."}
                )
            
            # Generate multi-image questions
            print(f"🔧 Generating questions for {len(images)} images with block assignments")
            generator = QuestionGenerator()
            question_set = await generator.generate_questions(
                image_data=images,  # Pass list of images for multi-image generation
                difficulty_level=difficulty,
                num_questions=num_questions,
                question_types=types_list,
                block_assignments=block_assignments
            )
            
            print(f"✅ Generated {question_set.total_questions} multi-image questions")
            return question_set.dict()
            
    except Exception as e:
        print(f"❌ Error in generate_questions_multi: {e}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to generate multi-image questions: {str(e)}"}
        )

@app.get("/questions/{image_id}")
async def questions_page(request: Request, image_id: str):
    """Display questions page for a specific image"""
    try:
        # Validate environment variables
        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
            return templates.TemplateResponse("error.html", {
                "request": request,
                "error": "Missing Supabase configuration"
            })
        
        # Fetch image data
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{SUPABASE_URL}/rest/v1/images",
                headers={
                    "apikey": SUPABASE_SERVICE_ROLE_KEY,
                    "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
                },
                params={"id": f"eq.{image_id}", "select": "*"}
            )
            
            if response.status_code == 200:
                images = response.json()
                if images:
                    image_data = images[0]
                    return templates.TemplateResponse("questions.html", {
                        "request": request,
                        "image": image_data
                    })
        
        # If we get here, image wasn't found
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": "Image not found"
        })
        
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e)
        })
