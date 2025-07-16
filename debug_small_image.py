"""
Debug script to understand token usage patterns for small images
"""

def analyze_small_image_tokens():
    print("🔍 ANALYZING 10KB IMAGE WITH 9,035 INPUT TOKENS")
    print("=" * 55)
    
    # Your actual data
    total_tokens = 9381
    input_tokens = 9035
    output_tokens = 346
    prompt_tokens = 512  # Our measured prompt size
    
    # Calculate image processing tokens
    image_tokens = input_tokens - prompt_tokens
    
    print(f"📊 Token Breakdown:")
    print(f"   Total: {total_tokens:,}")
    print(f"   Input: {input_tokens:,}")
    print(f"   Output: {output_tokens:,}")
    print()
    print(f"📝 Prompt tokens: {prompt_tokens:,}")
    print(f"🖼️  Image processing tokens: {image_tokens:,}")
    print()
    
    # For a 10KB image, this is VERY unusual
    print("🚨 DIAGNOSIS:")
    print(f"   A 10KB image should only cost ~255-765 tokens")
    print(f"   You're seeing {image_tokens:,} tokens - that's 10x higher!")
    print()
    
    print("💡 POSSIBLE CAUSES:")
    print("1. 🔄 Multiple API calls (retries, two-tier system)")
    print("2. 📱 Image dimensions vs file size (highly compressed but large resolution)")
    print("3. 🔗 Base64 encoding accidentally sent instead of URL")
    print("4. 🏷️  Additional context/conversation history being sent")
    print("5. 🔧 Model confusion (using wrong model pricing)")
    print()
    
    # Check if multiple calls could explain this
    expected_single_call = 512 + 425  # prompt + small image
    num_calls = image_tokens // 425 if image_tokens > 425 else 1
    
    print("🔍 HYPOTHESIS TESTING:")
    if image_tokens > 3000:
        print(f"   Theory: Multiple API calls")
        print(f"   If {num_calls} calls were made: {num_calls} × 425 = {num_calls * 425:,} tokens")
        print(f"   Your image tokens: {image_tokens:,}")
        print(f"   Difference: {abs(image_tokens - (num_calls * 425)):,}")
        print()
        
    print("🛠️  NEXT STEPS:")
    print("1. Check Edge Function logs for multiple API calls")
    print("2. Verify image dimensions (width × height)")
    print("3. Check if two-tier system is triggering multiple calls")
    print("4. Verify we're sending image URL, not base64 data")

if __name__ == "__main__":
    analyze_small_image_tokens()
