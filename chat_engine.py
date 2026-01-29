import os
import json
import httpx 

AVAILABLE_MODELS = {
    "default": "nvidia/nemotron-nano-12b-v2-vl:free",
    "qwen-80b": "qwen/qwen3-next-80b-a3b-instruct:free",
    "mistral": "mistralai/devstral-2512:free",
    "gemini": "google/gemini-2.0-flash-exp:free",
    "gpt-oss": "openai/gpt-oss-120b:free",
    "gemma": "google/gemma-3-27b-it:free",
    "deepseek": "deepseek/deepseek-r1-0528:free"
}

# Standard mode: ChatGPT/Gemini style responses
STANDARD_SYSTEM_PROMPT = (
    "You are a helpful, knowledgeable assistant. Respond like ChatGPT or Gemini would.\n\n"
    "FORMATTING RULES:\n"
    "- Use ## for main section headings (they will appear larger and bold)\n"
    "- DO NOT use '---' or '***' as separators - just use headings\n"
    "- Write detailed paragraphs with rich explanations, not brief bullet points\n"
    "- When you do use bullet points, make each point a full sentence or paragraph\n"
    "- Provide context, examples, and 'why it matters' for each topic\n"
    "- Be comprehensive and thorough, not brief\n"
    "- Code examples should be in proper code blocks with language specified\n"
    "- Keep a conversational, helpful tone throughout"
)

# Deep Dive mode: Think internally, rich detailed output
DEEP_DIVE_PROMPT = (
    "You are an expert research assistant. Before responding, think deeply and silently about:\n"
    "- What is the user really asking?\n"
    "- What context and background do they need?\n"
    "- What are the key concepts, nuances, and practical applications?\n\n"
    "DO NOT show your thinking process. Just provide the final answer.\n\n"
    "OUTPUT FORMATTING:\n"
    "- Use ## for main section headings (will render as large bold text)\n"
    "- NEVER use '---' or '***' or hyphens as separators\n"
    "- Write detailed, comprehensive paragraphs - not brief bullet points\n"
    "- Each section should have multiple sentences explaining the topic thoroughly\n"
    "- Include practical examples, use cases, and 'why this matters'\n"
    "- When listing items, explain each one with context, not just names\n"
    "- Be thorough like a knowledgeable friend explaining something important\n"
    "- Use code blocks with language specification for any code examples"
)

import asyncio
import random

# Fallback order for models (will try these if primary model fails)
FALLBACK_ORDER = ["gemini", "gemma", "mistral", "qwen-80b", "default", "deepseek"]

async def get_chat_response_async(user_message: str, history: list, model: str = "default", mode: str = "normal", file_context: str = "") -> str:
    """
    Async version of chat response using HTTPX.
    Supports model selection, response modes, file context, and automatic retry with fallback.
    """
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key: 
        return "Error: OPENROUTER_API_KEY environment variable not set."

    # Choose system prompt based on mode
    if mode == "deep_dive":
        system_instruction = DEEP_DIVE_PROMPT
    else:
        system_instruction = STANDARD_SYSTEM_PROMPT

    if file_context:
        system_instruction += f"\n\nCONTEXT FROM ATTACHED FILES:\n{file_context}\n\nUse the above context to answer the user's question if relevant."

    messages = [{"role": "system", "content": system_instruction}]
    
    for turn in history:
        role = turn.get('role')
        content = turn.get('content')
        if role and content:
            api_role = "assistant" if role == 'model' else role
            messages.append({"role": api_role, "content": content})

    messages.append({"role": "user", "content": user_message})

    # Build list of models to try (primary first, then fallbacks)
    models_to_try = [model]
    for fb in FALLBACK_ORDER:
        if fb != model and fb not in models_to_try:
            models_to_try.append(fb)

    last_error = None
    
    for model_key in models_to_try:
        selected_model = AVAILABLE_MODELS.get(model_key, AVAILABLE_MODELS["default"])
        
        # Try up to 3 times per model with exponential backoff
        for attempt in range(3):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        url="https://openrouter.ai/api/v1/chat/completions",
                        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                        json={"model": selected_model, "messages": messages, "temperature": 0.7},
                        timeout=90.0
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        content = result.get('choices', [{}])[0].get('message', {}).get('content')
                        if content:
                            return content
                        # If no content, try again
                        continue
                    
                    # Rate limit - wait and retry
                    if response.status_code == 429:
                        wait_time = (2 ** attempt) + random.uniform(0.5, 1.5)
                        await asyncio.sleep(wait_time)
                        continue
                    
                    # Server error - try next model
                    if response.status_code in [502, 503, 504]:
                        last_error = f"Model {model_key} unavailable (Error {response.status_code})"
                        break  # Try next model
                    
                    # Other errors
                    response.raise_for_status()
                    
            except httpx.TimeoutException:
                last_error = f"Request timed out for model {model_key}"
                break  # Try next model
            except httpx.HTTPStatusError as e:
                last_error = f"API Error: {e.response.status_code}"
                if e.response.status_code == 429:
                    wait_time = (2 ** attempt) + random.uniform(0.5, 1.5) 
                    await asyncio.sleep(wait_time)
                    continue
                break  # Try next model
            except Exception as e:
                last_error = f"Error: {str(e)}"
                break  # Try next model
    
    return last_error or "All models are currently unavailable. Please try again in a few moments."