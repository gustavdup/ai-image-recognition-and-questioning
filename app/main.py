import os
import uuid
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
import httpx

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
SUPABASE_BUCKET_NAME = os.getenv("SUPABASE_BUCKET_NAME", "images")

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

@app.get("/")
def root():
    return {"message": "Image Recognition API", "routes": {"upload": "/upload", "gallery": "/gallery", "api": "/api/images"}}

@app.get("/upload", response_class=HTMLResponse)
def upload_form(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})

@app.get("/gallery", response_class=HTMLResponse)
def gallery_page(request: Request):
    return templates.TemplateResponse("gallery.html", {"request": request})

@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        return {"error": "Supabase config missing"}
    
    if not file.filename:
        return {"error": "No filename provided"}
    
    # Check if file is an image
    if not file.content_type or not file.content_type.startswith('image/'):
        return {"error": "Only image files are allowed"}
    
    # Generate UUID filename with original extension
    file_ext = os.path.splitext(file.filename)[1].lower()
    filename = f"{uuid.uuid4()}{file_ext}"
    
    async with httpx.AsyncClient() as client:
        upload_url = f"{SUPABASE_URL}/storage/v1/object/{SUPABASE_BUCKET_NAME}/{filename}"
        headers = {
            "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": file.content_type
        }
        data = await file.read()
        resp = await client.post(upload_url, headers=headers, content=data)
        if resp.status_code == 200:
            return {"success": True, "filename": filename}
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
                "select": "id,image_name,image_url,description,tags,created_at",
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
