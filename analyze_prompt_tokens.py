import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

def test_with_your_image():
    """Test with the specific Supabase image that's causing high token usage"""
    
    # Your specific image URL
    image_url = "https://drlwgbnnutlyjzejpfny.supabase.co/storage/v1/object/public/images/02c8902e-971f-4bd1-a862-5a5e9c97d784.png"
    
    # Same minimal prompt as in the Edge Function
    prompt = 'Analyze this image. Return JSON: {"description": "what you see", "confidence": 0.8, "tags": {"basic": "test"}}'
    
    print(f"🧪 Testing with your specific Supabase image")
    print(f"📷 Image URL: {image_url}")
    print(f"📝 Prompt: {prompt}")
    print(f"📝 Prompt length: {len(prompt)} characters")
    print(f"📝 Prompt word count: {len(prompt.split())}")
    
    # Check image size
    try:
        print(f"\n🔍 Checking image properties...")
        response = requests.head(image_url)
        if response.status_code == 200:
            content_length = response.headers.get('content-length')
            content_type = response.headers.get('content-type')
            
            if content_length:
                size_bytes = int(content_length)
                size_kb = size_bytes / 1024
                size_mb = size_kb / 1024
                
                print(f"📏 Image size: {size_bytes:,} bytes ({size_kb:.1f} KB, {size_mb:.2f} MB)")
                print(f"📷 Content type: {content_type}")
                
                # Estimate token usage based on image size
                if size_mb > 5:
                    print(f"🚨 VERY LARGE IMAGE! This will cause high token usage (likely 5000-10000+ tokens)")
                elif size_mb > 2:
                    print(f"⚠️ Large image - may cause elevated token usage (likely 2000-5000 tokens)")
                elif size_mb > 1:
                    print(f"� Medium image - moderate token usage (likely 500-2000 tokens)")
                else:
                    print(f"✅ Small image - should have low token usage (likely 100-500 tokens)")
            else:
                print("❌ Could not determine image size")
        else:
            print(f"❌ Could not access image: {response.status_code}")
    except Exception as e:
        print(f"❌ Error checking image: {e}")
    
    # Test OpenAI API call
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("\n❌ No OpenAI API key found - cannot test API call")
        print("💡 Make sure OPENAI_API_KEY is set in your .env file")
        return
    
    print(f"\n🚀 Making OpenAI Vision API call...")
    print(f"🔑 API key found: {api_key[:20]}...")  # Show first 20 chars for verification
    
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            }
        ],
        "max_tokens": 200
    }
    
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            usage = result.get('usage', {})
            
            print("✅ SUCCESS!")
            print(f"📊 Model: {result.get('model', 'unknown')}")
            print(f"📊 Prompt tokens: {usage.get('prompt_tokens', 0)}")
            print(f"📊 Completion tokens: {usage.get('completion_tokens', 0)}")
            print(f"📊 Total tokens: {usage.get('total_tokens', 0)}")
            print(f"📝 Response: {result['choices'][0]['message']['content']}")
            
            # Analyze token usage
            prompt_tokens = usage.get('prompt_tokens', 0)
            estimated_text_tokens = len(prompt) / 4
            estimated_image_tokens = prompt_tokens - estimated_text_tokens
            
            print(f"\n🔍 Token breakdown:")
            print(f"  • Text prompt: ~{estimated_text_tokens:.0f} tokens")
            print(f"  • Image processing: ~{estimated_image_tokens:.0f} tokens")
            print(f"  • Total prompt: {prompt_tokens} tokens")
            
            if prompt_tokens > 5000:
                print(f"� HIGH TOKEN USAGE CONFIRMED! This image is causing {prompt_tokens} prompt tokens")
                print(f"💡 Recommendation: Resize image to 512x512 or smaller to reduce costs")
            elif prompt_tokens > 1000:
                print(f"⚠️ Elevated token usage: {prompt_tokens} tokens")
            else:
                print(f"✅ Normal token usage: {prompt_tokens} tokens")
                
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ API call failed: {e}")

if __name__ == "__main__":
    test_with_your_image()
