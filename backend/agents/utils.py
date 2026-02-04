import os
import httpx
import asyncio
import random

# Shared Models List
# THE COUNCIL: 5 Unique, Checked & Verified Models.
    "google/gemini-2.0-flash-001",             # [0] Research Director (Primary/Stable)
    "tngtech/tng-r1t-chimera:free",            # [1] Reasoning Specialist (Deep Reasoning)
    "nvidia/nemotron-3-nano-30b-a3b:free",     # [2] Efficiency Expert (Fast/Concise)
    "google/gemma-3n-e2b-it:free",             # [3] The Artisan (Creative Writer)
    "arcee-ai/trinity-large-preview:free"      # [4] The Inquisitor (Fact Checker)
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
