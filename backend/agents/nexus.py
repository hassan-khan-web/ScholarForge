from typing import List
from .utils import call_model_async, LEGION_MODELS

async def agent_nexus(drafts: List[str], section_title: str) -> str:
    print(f"    >>> The Nexus is synthesizing {len(drafts)} drafts...")
    
    combined_input = ""
    for i, draft in enumerate(drafts):
        combined_input += f"\n--- DRAFT {i+1} ---\n{draft}\n"
        
    prompt = (
        f"Synthesize the following {len(drafts)} drafts for the section '{section_title}' into ONE superior, cohesive master draft.\n"
        "RULES:\n"
        "1. Remove all repetition/redundancy.\n"
        "2. Keep the BEST stats, tables, and insights from ALL drafts.\n"
        "3. Maintain a unified professional tone.\n"
        "4. Structure with clear Markdown headers.\n"
        "5. Output ONLY the synthesized content."
    )
    
    return await call_model_async(LEGION_MODELS[0], "You are The Nexus, a Master Synthesizer.", combined_input + prompt)
