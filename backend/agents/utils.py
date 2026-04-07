import os
import httpx
import asyncio
import random
from ..logging_config import setup_logging

logger = setup_logging("scholarforge.agents")

# Shared Models List
# THE COUNCIL: 5 Unique, Checked & Verified Models.
LEGION_MODELS = [
    "google/gemini-2.0-flash-001",             # [0] Research Director (Primary/Stable)
    "llama-3.3-70b-versatile",                 # [1] Reasoning Specialist (Deep Reasoning via Groq)
    "nvidia/nemotron-3-nano-30b-a3b:free",     # [2] Efficiency Expert (Fast/Concise)
    "llama-3.1-8b-instant",                    # [3] The Artisan (Creative Writer via Groq - Replaced Gemma due to Context Limits)
    "llama-3.1-8b-instant"                     # [4] The Inquisitor (Fact Checker via Groq)
]

async def call_model_async(model: str, system_prompt: str, user_prompt: str) -> str:
    """Helper to call OpenRouter or Groq async with retries"""
    is_groq = model.startswith("llama-")
    
    if is_groq:
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key: return "Error: No GROQ_API_KEY"
        api_url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    else:
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key: return "Error: No OPENROUTER_API_KEY"
        api_url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:5000",
            "X-Title": "ScholarForge Council"
        }
    
    data = {"model": model, "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}], "temperature": 0.7, "max_tokens": 4000}

    for attempt in range(3):
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(api_url, headers=headers, json=data)
                
                if resp.status_code == 200:
                    try:
                        return resp.json()['choices'][0]['message']['content']
                    except: return ""
                
                # Rate limit handling
                if resp.status_code == 429:
                    await asyncio.sleep((2 ** attempt) + random.uniform(1, 3))
                    continue
                
                # Try next attempt on error
                logger.error(f"Council Agent Error ({model}): {resp.status_code}")
                await asyncio.sleep(2)
        except Exception as e:
            logger.error(f"Council Exception ({model}): {e}", exc_info=e)
            await asyncio.sleep(2)
            
    return f"[Agent Failure: {model}]"
