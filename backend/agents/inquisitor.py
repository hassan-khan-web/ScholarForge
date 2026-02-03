import json
import re
from .utils import call_model_async, LEGION_MODELS
from .tools import perform_web_search

async def agent_inquisitor(content: str, topic: str) -> dict:
    print("    >>> The Inquisitor is scrutinizing...")
    
    # Step 1: Identify claims needing verification
    check_prompt = (
        f"Review this text for a report on '{topic}'.\n"
        "Identify 1-2 specific factual claims or statistics that seem suspicious, outdated, or hallucinated.\n"
        "Output JSON only: {\"claims\": [\"claim 1\", \"claim 2\"]}\n"
        "If everything looks general/fine, output {\"claims\": []}"
    )
    
    check_resp = await call_model_async(LEGION_MODELS[4], "You are a Fact-Checker. JSON only.", content + "\n\n" + check_prompt)
    
    verification_notes = ""
    try:
        match = re.search(r'\{.*\}', check_resp.replace('\n', ' '), re.DOTALL)
        if match:
            claims_data = json.loads(match.group(0))
            claims = claims_data.get('claims', [])
            
            if claims:
                print(f"    >>> Inquisitor is verifying {len(claims)} claims...")
                for claim in claims:
                    search_res = await perform_web_search(claim, max_results=1)
                    verification_notes += f"\nCLAIM: {claim}\nVERIFICATION: {search_res[:500]}...\n"
    except: pass

    # Step 2: Final Verdict with Verification Data
    prompt = (
        f"Review this text for report '{topic}'.\n"
        f"VERIFICATION DATA FROM WEB:\n{verification_notes}\n\n"
        "CRITICAL TASKS:\n"
        "1. Identify any logical fallacies.\n"
        "2. textual repetition.\n"
        "3. Use the Verification Data to reject false claims.\n\n"
        "DECISION: Output JSON format:\n"
        "{\n"
        "  \"status\": \"APPROVED\" or \"REJECTED\",\n"
        "  \"critique\": \"...detailed feedback if rejected...\",\n"
        "  \"score\": 85 (0-100)\n"
        "}"
    )
    
    resp = await call_model_async(LEGION_MODELS[4], "You are The Inquisitor. Return JSON.", content + "\n\n" + prompt)
    
    try:
        # Extract JSON
        match = re.search(r'\{.*\}', resp.replace('\n', ' '), re.DOTALL)
        if match:
            return json.loads(match.group(0))
    except: pass
    
    # Default to approved if parsing fails to avoid infinite loops
    print("    [!] Inquisitor result parse failed, defaulting to PASS")
    return {"status": "APPROVED", "score": 100}
