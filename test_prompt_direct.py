#!/usr/bin/env python3
"""
Direct OpenAI Vision API test script for the educational flashcard prompt.
This bypasses Supabase and tests the prompt directly for faster iteration.
"""

import os
import json
import requests
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

def test_vision_prompt(image_url, model="gpt-4-turbo", max_tokens=2000):
    """Test the educational flashcard prompt directly with OpenAI Vision API"""
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in environment variables")
    
    # The exact prompt from the Edge Function
    prompt = """Analyze this educational flashcard quadrant image with precision for automatic question generation. Return a JSON object:

{
  "description": "Brief description of what's in the image",
  "confidence": "Relative confidence in the analysis based on your confidence and image quality, be specific (0.0 to 1.0)",
  "tags": {
    "colors": ["red", "blue", "green", "yellow", "orange", "purple", "pink", "black", "white", "brown", "gray"],
    "shapes": ["circle", "triangle", "square", "rectangle", "star", "heart", "diamond", "oval", "pentagon", "hexagon"],
    "letters": ["A", "B", "C"],
    "numbers": ["0", "1", "2", "3"],
    "words": ["red", "blue", "green"],
    "objects": ["umbrella", "bicycle", "tree", "violin", "igloo", "key", "house", "nest"],
    "people": ["boy", "girl", "man", "woman", "child"],
    "animals": ["cat", "dog", "bird", "fish", "horse"],
    "shapeColors": ["red circle", "blue triangle", "yellow square"],
    "shapeContents": ["letter F inside red square", "number 5 inside yellow star"],
    "nestedElements": ["black circle inside orange star", "white text inside blue shape"],
    "textColor": "actual display color of text",
    "textVsSemanticMismatch": "word 'red' displayed in blue color",
    "textLocation": "inside shape, on background, overlay",
    "objectColors": ["red umbrella", "blue bicycle"],
    "objectPositions": ["top", "bottom", "left", "right", "center", "overlapping"],
    "itemsInsideShapes": ["letter F inside red square", "number 17 inside yellow circle"],
    "overlappingItems": ["umbrella overlapping with tree"],
    "relativePositions": ["bicycle left of tree", "key above house"],
    "colorWordMismatches": ["word 'green' written in red", "word 'blue' written in yellow"],
    "highlightedElements": ["yellow square overlay", "colored border around item"],
    "backgroundColor": "specific background color",
    "hasColoredBackground": "true or false",
    "totalItems": "exact count of all distinct visual elements",
    "letterCount": "number of letters present",
    "numberCount": "number of numerical digits",
    "objectCount": "number of real-world objects",
    "shapeCount": "number of geometric shapes",
    "category": "letters|numbers|shapes|colors|objects|mixed|color-word-mismatch",
    "difficulty": "basic|intermediate|advanced",
    "questionTypes": ["identification", "counting", "color", "position", "relationship", "true-false"]
  }
}

CRITICAL ANALYSIS REQUIREMENTS:
1. **TEXT vs VISUAL DISCREPANCY**: Detect when color words don't match their display color (e.g., "red" written in blue)
2. **NESTED CONTENT**: Identify what's inside geometric shapes (letters, numbers, objects)
3. **SPATIAL RELATIONSHIPS**: Map relative positions and overlapping elements
4. **BACKGROUND CONTEXT**: Distinguish between background colors and shape colors
5. **HIGHLIGHTED ELEMENTS**: Detect yellow overlays, borders, or emphasis markers
6. **COUNTING PRECISION**: Count all distinct visual elements accurately
7. **COLOR SPECIFICITY**: Name exact colors, not generic terms
8. **OBJECT CLASSIFICATION**: Identify specific real-world items (violin, not just "instrument")
9. **TEXT EXTRACTION**: OCR all visible letters, numbers, and words
10. **RELATIONSHIP MAPPING**: What contains what, what's next to what

Enable questions like:
- "What color is the square in this quadrant?" 
- "What letter is inside the red shape?"
- "Name the color, not the word, in this image"
- "What number is on the yellow square?"
- "How many items are in this quadrant - two or three?"
- "What musical instrument has 6 letters and starts with this letter?"
- "True or false? There is an umbrella in this image"
- "What is the color and shape of this element?"
- "Which items are highlighted with yellow?"
- "What letters are in the yellow squares?"

IMPORTANT: Return ONLY the JSON object, no markdown formatting, no code blocks. Start with { and end with }."""

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": image_url}}
                ]
            }
        ],
        "max_tokens": max_tokens
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    print(f"🚀 Testing with {model}, max_tokens: {max_tokens}")
    print(f"📷 Image URL: {image_url}")
    print(f"📏 Prompt length: {len(prompt)} characters")
    print("=" * 80)
    
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )
        
        if not response.ok:
            print(f"❌ API Error: {response.status_code}")
            print(f"Error details: {response.text}")
            return None
            
        result = response.json()
        
        # Extract usage information
        usage = result.get("usage", {})
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", 0)
        
        print(f"📊 Token Usage:")
        print(f"  Prompt tokens: {prompt_tokens}")
        print(f"  Completion tokens: {completion_tokens}")
        print(f"  Total tokens: {total_tokens}")
        print("=" * 80)
        
        # Get the response content
        content = result["choices"][0]["message"]["content"]
        print(f"📝 Raw Response ({len(content)} chars):")
        print(content)
        print("=" * 80)
        
        # Try to parse as JSON
        try:
            parsed_json = json.loads(content)
            print("✅ JSON Parse: SUCCESS")
            print(f"📋 Parsed Structure:")
            print(f"  Description: {parsed_json.get('description', 'Missing')[:100]}...")
            print(f"  Confidence: {parsed_json.get('confidence', 'Missing')}")
            
            tags = parsed_json.get('tags', {})
            print(f"  Tags structure: {list(tags.keys()) if tags else 'Missing'}")
            
            if 'totalCount' in tags:
                print(f"  🎯 Total Count: {tags['totalCount']}")
            else:
                print("  ❌ Total Count: MISSING")
                
            # Check for key fields
            key_fields = ['colors', 'shapes', 'letters', 'numbers', 'objects']
            for field in key_fields:
                if field in tags:
                    items = tags[field]
                    if isinstance(items, list):
                        print(f"  {field}: {len(items)} items - {items}")
                    else:
                        print(f"  {field}: {items}")
                else:
                    print(f"  ❌ {field}: MISSING")
            
            return parsed_json
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON Parse Error: {e}")
            print("Attempting to extract JSON from markdown...")
            
            # Try to extract JSON from markdown blocks
            import re
            json_match = re.search(r'```(?:json)?\s*\n?(.*?)\n?```', content, re.DOTALL)
            if json_match:
                try:
                    extracted = json_match.group(1).strip()
                    parsed_json = json.loads(extracted)
                    print("✅ Extracted JSON from markdown successfully")
                    return parsed_json
                except json.JSONDecodeError:
                    print("❌ Even extracted JSON failed to parse")
            
            return None
            
    except requests.RequestException as e:
        print(f"❌ Request Error: {e}")
        return None

def test_multiple_models(image_url):
    """Test the prompt with different models for comparison"""
    models = [
        ("gpt-4-turbo", 2000),
        ("gpt-4o", 1500),
        ("gpt-4o-mini", 1000)
    ]
    
    results = {}
    
    for model, max_tokens in models:
        print(f"\n{'='*20} TESTING {model.upper()} {'='*20}")
        result = test_vision_prompt(image_url, model, max_tokens)
        results[model] = result
        
        if result:
            confidence = result.get('confidence', 'N/A')
            total_count = result.get('tags', {}).get('totalCount', 'N/A')
            print(f"✅ {model}: Confidence={confidence}, TotalCount={total_count}")
        else:
            print(f"❌ {model}: FAILED")
        
        print(f"{'='*60}")
    
    return results

def main():
    """Main test function"""
    print("🧪 OpenAI Vision API Direct Test")
    print("=" * 60)
    
    # Test image URL (you can change this)
    test_images = [
        "https://via.placeholder.com/400x400/ff0000/ffffff?text=A",
        # Add your actual test image URLs here
    ]
    
    # Get image URL from user input or use default
    image_url = input("Enter image URL (or press Enter for placeholder): ").strip()
    if not image_url:
        image_url = test_images[0]
        print(f"Using default test image: {image_url}")
    
    # Test with single model first
    print(f"\n🎯 Single Model Test")
    result = test_vision_prompt(image_url, "gpt-4-turbo", 2000)
    
    # Ask if user wants to test multiple models
    test_multiple = input("\nTest multiple models? (y/N): ").strip().lower()
    if test_multiple == 'y':
        print(f"\n🔄 Multi-Model Comparison")
        results = test_multiple_models(image_url)
        
        # Summary comparison
        print(f"\n📊 SUMMARY COMPARISON")
        print("=" * 60)
        for model, result in results.items():
            if result:
                confidence = result.get('confidence', 'N/A')
                total_count = result.get('tags', {}).get('totalCount', 'N/A')
                colors = len(result.get('tags', {}).get('colors', []))
                shapes = len(result.get('tags', {}).get('shapes', []))
                letters = len(result.get('tags', {}).get('letters', []))
                print(f"{model:12}: Conf={confidence}, Count={total_count}, C={colors}, S={shapes}, L={letters}")
            else:
                print(f"{model:12}: FAILED")

if __name__ == "__main__":
    main()
