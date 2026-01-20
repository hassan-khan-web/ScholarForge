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

DEEP_DIVE_PROMPT = (
    "\n\nMODE: DEEP DIVE ANALYSIS\n"
    "You are in 'Deep Dive' mode. Your response must be extremely comprehensive, structured, and detailed. "
    "Do NOT give a simple answer. "
    "1. PLAN: First, briefly outline how you will approach this question (Chain of Thought). "
    "2. EXECUTE: Provide a thorough explanation, covering historical context, technical details, conflicting theories, and practical examples. "
    "3. CLARITY: Use analogies where complex. Ensure every claim is explained. "
    "4. LENGTH: Your response should be significantly longer and more detailed than a standard reply."
)

async def get_chat_response_async(user_message: str, history: list, model: str = "default", mode: str = "normal", file_context: str = "") -> str:
    """
    Async version of chat response using HTTPX.
    Supports model selection, response modes, and file context.
    """
    try:
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key: return "Error: OPENROUTER_API_KEY environment variable not set."

        selected_model = AVAILABLE_MODELS.get(model, AVAILABLE_MODELS["default"])

        system_instruction = (
            "You are a dedicated Senior Research Assistant. Your ONLY purpose is to assist with academic, scientific, and technical research.\n"
            "STRICT BEHAVIOR PROTOCOLS:\n"
            "1. NO SMALL TALK: You must strictly REFUSE to engage in greetings, pleasantries, or casual conversation (e.g., 'Hi', 'Hello', 'What's up'). "
            "If the user input is not a research query, reply EXACTLY and ONLY with: 'I am a specialized research assistant. Please provide a specific research topic or academic question to proceed.'\n"
            "2. DEPTH OF CONTENT: When answering research questions, provide EXTENSIVE, detailed, and comprehensive responses. "
            "Avoid brevity. Expand on historical context, underlying theories, conflicting viewpoints, and practical applications. "
            "Your goal is to provide a 'deep dive' analysis, not a summary.\n"
            "3. TONE: Maintain a formal, doctoral-level academic tone at all times."
        )

        if mode == "deep_dive":
            system_instruction += DEEP_DIVE_PROMPT

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

        async with httpx.AsyncClient() as client:
            response = await client.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                data=json.dumps({"model": selected_model, "messages": messages, "temperature": 0.7}),
                timeout=60.0
            )
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content'] or "No response from AI."

    except httpx.HTTPStatusError as e:
        return f"API Error: {e.response.status_code}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"