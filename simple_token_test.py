import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def simple_token_test():
    api_key = os.getenv('OPENAI_API_KEY')
    image_url = "https://drlwgbnnutlyjzejpfny.supabase.co/storage/v1/object/public/images/02c8902e-971f-4bd1-a862-5a5e9c97d784.png"
    prompt = 'Analyze this image. Return JSON: {"description": "what you see", "confidence": 0.8, "tags": {"basic": "test"}}'
    
    print("=" * 60)
    print("🧪 SIMPLE TOKEN USAGE TEST")
    print("=" * 60)
    print(f"Image: {image_url}")
    print(f"Prompt: {prompt}")
    print(f"Prompt length: {len(prompt)} chars")
    print("-" * 60)
    
    payload = {
        "model": "gpt-4o-mini",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {"type": "image_url", "image_url": {"url": image_url}}
            ]
        }],
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
            print(f"📊 Prompt tokens: {usage.get('prompt_tokens', 0)}")
            print(f"📊 Completion tokens: {usage.get('completion_tokens', 0)}")
            print(f"📊 Total tokens: {usage.get('total_tokens', 0)}")
            
            prompt_tokens = usage.get('prompt_tokens', 0)
            if prompt_tokens > 5000:
                print("🚨 HIGH TOKEN USAGE!")
            elif prompt_tokens > 1000:
                print("⚠️ Elevated token usage")
            else:
                print("✅ Normal token usage")
                
        else:
            print(f"❌ Error: {response.status_code}")
            print(response.text[:500])
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    simple_token_test()
