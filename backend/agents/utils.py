import os
import httpx
import asyncio
import random

# Shared Models List
LEGION_MODELS = [
    "google/gemini-2.0-flash-exp:free",      # Primary/Old
    "mistralai/devstral-2512:free",          # Diverse reasoning
    "google/gemma-3-27b-it:free",            # Efficient
    "qwen/qwen3-next-80b-a3b-instruct:free", # Logic/Code heavy
    "deepseek/deepseek-r1-0528:free"         # Deep reasoning
]

async def call_model_async(model: str, system_prompt: str, user_prompt: str) -> str:
    """Helper to call OpenRouter async with retries"""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key: return "Error: No API Key"
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "http://localhost:5000",
        "X-Title": "ScholarForge Council"
    }
    
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 4000
    }

    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=data)
                
                if resp.status_code == 200:
                    try:
                        return resp.json()['choices'][0]['message']['content']
                    except: return ""
                
                # Rate limit handling
                if resp.status_code == 429:
                    await asyncio.sleep((2 ** attempt) + random.uniform(1, 3))
                    continue
                
                # Try next attempt on error
                print(f"Council Agent Error ({model}): {resp.status_code}")
                await asyncio.sleep(2)
        except Exception as e:
            print(f"Council Exception ({model}): {e}")
            await asyncio.sleep(2)
            
    return f"[Agent Failure: {model}]"
