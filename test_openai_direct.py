#!/usr/bin/env python3
"""
Direct OpenAI Vision API test to establish baseline token usage
"""
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def test_multiple_scenarios():
    """Test different scenarios to understand token usage"""
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ No OpenAI API key found")
        return
    
    scenarios = [
        {
            "name": "Your Supabase image (GPT-4o-mini)", 
            "image_url": "https://drlwgbnnutlyjzejpfny.supabase.co/storage/v1/object/public/images/02c8902e-971f-4bd1-a862-5a5e9c97d784.png",
            "prompt": "What do you see?",
            "model": "gpt-4o-mini"
        },
        {
            "name": "Your Supabase image (GPT-4o)", 
            "image_url": "https://drlwgbnnutlyjzejpfny.supabase.co/storage/v1/object/public/images/02c8902e-971f-4bd1-a862-5a5e9c97d784.png",
            "prompt": "What do you see?",
            "model": "gpt-4o"
        },
        {
            "name": "Text-only (GPT-4o-mini)",
            "image_url": None,
            "prompt": "Just respond with 'hello'",
            "model": "gpt-4o-mini"
        },
        {
            "name": "Text-only (GPT-4o)",
            "image_url": None,
            "prompt": "Just respond with 'hello'",
            "model": "gpt-4o"
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{'='*60}")
        print(f"🧪 TEST {i}: {scenario['name']}")
        print(f"{'='*60}")
        
        if scenario['image_url']:
            content = [
                {"type": "text", "text": scenario['prompt']},
                {"type": "image_url", "image_url": {"url": scenario['image_url']}}
            ]
        else:
            content = [{"type": "text", "text": scenario['prompt']}]
        
        payload = {
            "model": scenario.get("model", "gpt-4o-mini"),
            "messages": [{"role": "user", "content": content}],
            "max_tokens": 50
        }
        
        print(f"🤖 Model: {payload['model']}")
        
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
                prompt_tokens = usage.get('prompt_tokens', 0)
                
                print(f"✅ Prompt tokens: {prompt_tokens}")
                print(f"🤖 Model: {result.get('model', 'unknown')}")
                print(f"📝 Response: {result['choices'][0]['message']['content']}")
                
                if scenario['image_url'] is None:
                    print(f"📊 BASELINE (text-only): {prompt_tokens} tokens")
                else:
                    baseline = 10  # Rough estimate for text-only
                    image_tokens = prompt_tokens - baseline
                    print(f"📊 Estimated image processing: ~{image_tokens} tokens")
                    
            else:
                print(f"❌ Error: {response.status_code} - {response.text[:200]}")
                
        except Exception as e:
            print(f"❌ Exception: {e}")

def test_openai_vision_direct():
    """Test OpenAI Vision API directly with a known small image"""
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ No OpenAI API key found")
        return
    
    # Use a known small test image URL (this is a small 100x100 pixel PNG)
    test_image_url = "https://via.placeholder.com/100x100.png?text=Test"
    
    # Minimal prompt (same as in our Edge Function)
    prompt = 'Analyze this image. Return JSON: {"description": "what you see", "confidence": 0.8, "tags": {"basic": "test"}}'
    
    print(f"🧪 Testing OpenAI Vision API directly")
    print(f"📷 Image URL: {test_image_url}")
    print(f"📝 Prompt length: {len(prompt)} characters")
    print(f"📝 Prompt: {prompt}")
    
    payload = {
        "model": "gpt-4o-mini",
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": test_image_url}}
                ]
            }
        ],
        "max_tokens": 200
    }
    
    print(f"📤 Request payload size: {len(json.dumps(payload))} characters")
    
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json=payload
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
            
            # Check for high token usage
            prompt_tokens = usage.get('prompt_tokens', 0)
            if prompt_tokens > 5000:
                print(f"🚨 HIGH TOKEN USAGE! {prompt_tokens} prompt tokens is unusually high for a small image + minimal prompt")
                print("💡 This suggests OpenAI Vision API has high baseline token usage")
            elif prompt_tokens > 1000:
                print(f"⚠️ Elevated token usage: {prompt_tokens} prompt tokens")
            else:
                print(f"✅ Normal token usage: {prompt_tokens} prompt tokens")
                
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    print("🚨 INVESTIGATING HIGH TOKEN USAGE")
    print("Running multiple test scenarios...\n")
    test_multiple_scenarios()
    print(f"\n{'='*60}")
    print("📋 CONCLUSION: If all image tests show 8000+ tokens,")
    print("this is normal OpenAI Vision API behavior, not our bug!")
    print(f"{'='*60}")
