import os
import requests
import json

LLAMA_MODEL_STRING = "nvidia/nemotron-nano-12b-v2-vl:free" 

def get_chat_response(user_message: str, history: list) -> str:
    try:
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key: return "Error: OPENROUTER_API_KEY environment variable not set."

        system_instruction = "You are a helpful AI research assistant. Answer the user's questions clearly and concisely."
        messages = [{"role": "system", "content": system_instruction}]
        
        for turn in history:
            role = turn.get('role')
            content = turn.get('content')
            if role and content:
                api_role = "assistant" if role == 'model' else role
                messages.append({"role": api_role, "content": content})

        messages.append({"role": "user", "content": user_message})

        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            data=json.dumps({"model": LLAMA_MODEL_STRING, "messages": messages, "temperature": 0.7})
        )
        response.raise_for_status() 
        return response.json()['choices'][0]['message']['content'] or "No response from AI."

    except requests.exceptions.HTTPError as e: return f"OpenRouter API Error: {e.response.status_code} {e.response.text}"
    except Exception as e: return f"An unexpected error occurred: {e}"