# tests/test_models.py
from langchain_google_genai import ChatGoogleGenerativeAI
from src.utils.config import Config

models_to_try = [
    "gemini-2.5-flash",
    "gemini-2.5-pro", 
    "gemini-1.5-flash-latest",
    "gemini-1.5-flash-001",
    "gemini-pro",
]

print("Testing available Gemini models...\n")
print(f"API Key loaded: {Config.GEMINI_API_KEY[:20]}...\n")

for model_name in models_to_try:
    try:
        llm = ChatGoogleGenerativeAI(
            model=model_name,
            temperature=0,
            google_api_key=Config.GEMINI_API_KEY  # ← Use Config, not os.getenv
        )
        response = llm.invoke("Hi")
        print(f"✅ {model_name}: WORKS - Response: {response.content[:50]}")
        print(f"\n🎯 Use this model in your GeminiClient class!")
        break
    except Exception as e:
        error_msg = str(e)
        if "404" in error_msg or "NOT_FOUND" in error_msg:
            print(f"❌ {model_name}: Not found (404)")
        elif "API key" in error_msg:
            print(f"⚠️  {model_name}: API key issue")
        else:
            print(f"⚠️  {model_name}: {error_msg[:100]}")
