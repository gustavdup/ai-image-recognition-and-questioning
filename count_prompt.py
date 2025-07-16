import re

# Read the file
with open('supabase/functions/on-image-upload/index.ts', 'r', encoding='utf-8') as f:
    content = f.read()

# Extract the prompt between the backticks
prompt_match = re.search(r'const prompt = `(.*?)`;\s*\n', content, re.DOTALL)
if prompt_match:
    prompt = prompt_match.group(1)
    char_count = len(prompt)
    # Rough estimate: 1 token ≈ 4 characters for English text
    estimated_tokens = char_count // 4
    print(f'Prompt character count: {char_count:,}')
    print(f'Estimated token count: {estimated_tokens:,}')
    print()
    print("🚨 THIS IS THE PROBLEM!")
    print(f"Your prompt is roughly {estimated_tokens:,} tokens!")
    print("That's why gpt-4o-mini costs so much - it's the INPUT tokens, not output!")
    print()
    print("For comparison:")
    print("- GPT-4o-mini: $0.000150 per 1K input tokens")
    print(f"- Your prompt cost per image: ${(estimated_tokens/1000) * 0.000150:.4f}")
    print("- At 1000 images: ${:.2f}".format((estimated_tokens/1000) * 0.000150 * 1000))
else:
    print('Could not find prompt in file')
