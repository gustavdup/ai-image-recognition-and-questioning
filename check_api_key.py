import os
from dotenv import load_dotenv

load_dotenv()

print("🔍 Environment variable check:")
api_key = os.getenv('OPENAI_API_KEY')
if api_key:
    print(f"✅ API key loaded: {api_key[:10]}...{api_key[-10:]} (length: {len(api_key)})")
    print(f"🔍 Key starts with: {api_key[:3]}")
    
    # OpenAI keys should start with 'sk-'
    if api_key.startswith('sk-'):
        print("✅ Key format looks correct (starts with 'sk-')")
    else:
        print("❌ Key format looks incorrect (should start with 'sk-')")
        print("💡 This might be a project key or different format")
else:
    print("❌ No API key found in environment")

print("\n📁 Current working directory:", os.getcwd())
print("📄 .env file exists:", os.path.exists('.env'))

if os.path.exists('.env'):
    with open('.env', 'r') as f:
        content = f.read()
        print(f"📝 .env file contains OPENAI_API_KEY: {'OPENAI_API_KEY' in content}")
