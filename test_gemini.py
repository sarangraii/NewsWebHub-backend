import httpx
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def test_model(model_name, api_version="v1beta"):
    GEMINI_KEY = os.getenv("GEMINI_API_KEY")
    API_URL = f"https://generativelanguage.googleapis.com/{api_version}/models/{model_name}:generateContent?key={GEMINI_KEY}"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                API_URL,
                json={
                    "contents": [{"parts": [{"text": "Say hello"}]}]
                },
                timeout=10.0
            )
            
            if response.status_code == 200:
                print(f"✅ {model_name} WORKS!")
                return True
            else:
                print(f"❌ {model_name} - {response.status_code}")
                return False
    except Exception as e:
        print(f"❌ {model_name} - Error: {e}")
        return False

async def main():
    models = [
        "gemini-pro",
        "gemini-1.5-pro",
        "gemini-1.5-flash",
        "gemini-2.0-flash-exp",
    ]
    
    print("Testing models...\n")
    for model in models:
        await test_model(model)
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())