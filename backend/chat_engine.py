import os
import httpx 

AVAILABLE_MODELS = {
    "default": "nvidia/nemotron-nano-12b-v2-vl:free",
    "llama-70b": "llama-3.3-70b-versatile",
    "gpt-oss": "openai/gpt-oss-120b",
    "gemma": "google/gemma-3-27b-it:free",
    "llama-8b": "llama-3.1-8b-instant"
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

DEEP_DIVE_PROMPT = (
    "You are a Senior Post-Doctoral Research Analyst conducting a comprehensive Deep Dive analysis.\n\n"
    "Your objective is to provide a highly structured, encyclopedic breakdown of the topic.\n"
    "DO NOT provide a conversational or friendly response. You must output an academic and analytical report.\n\n"
    "STRICT OUTPUT STRUCTURE:\n"
    "1. EXECUTIVE SUMMARY: A dense 3-4 sentence overview of the core mechanical or philosophical truth of the topic.\n"
    "2. THEORETICAL FRAMEWORK / CORE MECHANICS: Use `###` sub-headers to break down exactly how this works or its historical context.\n"
    "3. COMPARATIVE ANALYSIS (MANDATORY TABLE): You MUST include a strict Markdown format Table (using `|`) comparing this concept to leading alternatives, pros/cons, or historical eras.\n"
    "4. REAL-WORLD IMPLICATIONS: Specific use cases, current industry/scientific deployment, and economic/social impact.\n"
    "5. CRITICAL LIMITATIONS & FUTURE OUTLOOK: What are the bottlenecks, unsolved problems, or next evolutionary steps?\n\n"
    "FORMATTING RULES:\n"
    "- Use `##` for the 5 main section headings above.\n"
    "- Use `###` for nested sub-topics.\n"
    "- Never use simple bulleted lists without bolding the prefix term and providing a dense paragraph of explanation for each point.\n"
    "- Tone: Encyclopedic, highly clinical, objective, and extremely detailed.\n"
    "- THINKING PROCESS: You MUST internally reason and structure your answer before writing it. Enclose your ENTIRE thought process precisely in `<think>` and `</think>` HTML tags at the very beginning of your response. Start your response immediately with `<think>`."
)

import asyncio
import random

# Fallback order for models (will try these if primary model fails)
FALLBACK_ORDER = ["llama-70b", "llama-8b", "gpt-oss", "gemma", "default"]

async def get_chat_response_async(user_message: str, history: list, model: str = "default", mode: str = "normal", file_context: str = "") -> str:
    """
    Async version of chat response using HTTPX.
    Supports model selection, response modes, file context, and automatic retry with fallback.
    """
    # API keys resolved dynamically per model in the loop below

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
        
        is_groq = selected_model.startswith("llama-")
        if is_groq:
            api_key = os.environ.get("GROQ_API_KEY")
            api_url = "https://api.groq.com/openai/v1/chat/completions"
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        else:
            api_key = os.environ.get("OPENROUTER_API_KEY")
            api_url = "https://openrouter.ai/api/v1/chat/completions"
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json", "HTTP-Referer": "http://localhost:5000"}

        if not api_key:
            last_error = f"API Key missing for {selected_model}"
            continue

        # Try up to 3 times per model with exponential backoff
        for attempt in range(3):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        url=api_url,
                        headers=headers,
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