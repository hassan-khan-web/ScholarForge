import os
import json
import httpx 

LLAMA_MODEL_STRING = "nvidia/nemotron-nano-12b-v2-vl:free" 

async def get_chat_response_async(user_message: str, history: list) -> str:
    """
    Async version of chat response using HTTPX.
    """
    try:
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key: return "Error: OPENROUTER_API_KEY environment variable not set."

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
                data=json.dumps({"model": LLAMA_MODEL_STRING, "messages": messages, "temperature": 0.7}),
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            return result['choices'][0]['message']['content'] or "No response from AI."

    except httpx.HTTPStatusError as e:
        return f"API Error: {e.response.status_code}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"