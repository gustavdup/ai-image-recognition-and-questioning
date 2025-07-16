import math

def calculate_image_tokens(width, height):
    """
    Calculate image tokens for OpenAI Vision API based on image dimensions.
    This follows OpenAI's vision token calculation methodology.
    """
    # OpenAI charges tokens based on image processing
    # High detail images are broken into 512x512 tiles
    
    # Calculate how many 512x512 tiles the image would need
    tiles_width = math.ceil(width / 512)
    tiles_height = math.ceil(height / 512)
    total_tiles = tiles_width * tiles_height
    
    # Base tokens per tile (approximate based on OpenAI documentation)
    base_tokens_per_tile = 170  # Base tokens for processing each 512x512 tile
    additional_tokens = 85      # Additional base tokens per image
    
    total_image_tokens = (total_tiles * base_tokens_per_tile) + additional_tokens
    
    return total_image_tokens, total_tiles

def analyze_token_usage():
    print("🔍 ANALYZING YOUR HIGH TOKEN USAGE")
    print("=" * 50)
    
    # Your reported token usage
    total_tokens = 9381
    input_tokens = 9035
    output_tokens = 346
    prompt_tokens = 512  # Our calculated prompt size
    
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
    
    # Common image sizes and their token costs
    common_sizes = [
        ("Phone photo (standard)", 3024, 4032),
        ("Phone photo (compressed)", 1512, 2016),
        ("Web image (large)", 1920, 1080),
        ("Web image (medium)", 1024, 768),
        ("Web image (small)", 512, 512),
    ]
    
    print("🖼️  ESTIMATED IMAGE TOKEN COSTS:")
    print("-" * 40)
    for name, width, height in common_sizes:
        tokens, tiles = calculate_image_tokens(width, height)
        print(f"{name:25} | {width:4}x{height:<4} | {tiles:2} tiles | {tokens:4} tokens")
    
    print()
    print("💡 ANALYSIS:")
    if image_tokens > 5000:
        print("🚨 You're uploading HIGH RESOLUTION images!")
        print("   This is the main cause of your token costs.")
        print()
        print("💰 SOLUTIONS:")
        print("1. ✅ Resize images to 1024x768 or smaller before upload")
        print("2. ✅ Compress images to reduce file size")
        print("3. ✅ Use image processing to auto-resize in your backend")
        print("4. ✅ Add image size validation in your upload form")
        
        # Calculate potential savings
        small_image_tokens = 425  # ~1024x768 image
        savings_per_image = image_tokens - small_image_tokens
        savings_percentage = (savings_per_image / image_tokens) * 100
        
        print()
        print(f"💸 POTENTIAL SAVINGS:")
        print(f"   Current image cost: {image_tokens:,} tokens")
        print(f"   Optimized image cost: {small_image_tokens:,} tokens")
        print(f"   Savings per image: {savings_per_image:,} tokens ({savings_percentage:.1f}%)")
        print(f"   At 1000 images: ${(savings_per_image * 1000 * 0.000150):.2f} saved")
    
    elif image_tokens > 1000:
        print("⚠️  You're uploading medium-resolution images.")
        print("   Consider optimizing for better cost efficiency.")
    else:
        print("✅ Image size looks reasonable.")
        print("   The high cost might be from multiple API calls or retries.")

if __name__ == "__main__":
    analyze_token_usage()
