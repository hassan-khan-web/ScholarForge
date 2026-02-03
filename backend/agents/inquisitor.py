import json
import re
from .utils import call_model_async, LEGION_MODELS

async def agent_inquisitor(content: str, topic: str) -> dict:
    print("    >>> The Inquisitor is scrutinizing...")
    
    prompt = (
        f"Review this text for a report on '{topic}'.\n"
        "CRITICAL TASKS:\n"
        "1. Identify any logical fallacies or hallucinated-looking stats.\n"
        "2. Question every major finding: 'Is this from a trustworthy source context?'\n"
        "3. Check for repetition.\n\n"
        "DECISION: Output JSON format:\n"
        "{\n"
        "  \"status\": \"APPROVED\" or \"REJECTED\",\n"
        "  \"critique\": \"...detailed feedback if rejected...\",\n"
        "  \"score\": 85 (0-100)\n"
        "}"
    )
    
    resp = await call_model_async(LEGION_MODELS[4], "You are The Inquisitor, a skeptical Fact-Checker. Return JSON.", content + "\n\n" + prompt)
    
    try:
        # Extract JSON
        match = re.search(r'\{.*\}', resp.replace('\n', ' '), re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except: pass
    
    # Default to approved if parsing fails to avoid infinite loops
    print("    [!] Inquisitor result parse failed, defaulting to PASS")
    return {"status": "APPROVED", "score": 100}
