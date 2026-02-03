from .agents.legion import agent_legion
from .agents.nexus import agent_nexus
from .agents.inquisitor import agent_inquisitor
from .agents.artisan import agent_artisan

async def run_council(section_title: str, topic: str, context: str, update_status_callback=None) -> str:
    """The recursive loop of the Council"""
    
    if update_status_callback: update_status_callback(f"The Legion is generating variants for '{section_title}'...")
    
    # Step 1: Legion
    drafts = await agent_legion(section_title, topic, context)
    
    if update_status_callback: update_status_callback(f"The Nexus is merging {len(drafts)} drafts...")
    
    # Step 2: Nexus
    master_draft = await agent_nexus(drafts, section_title)
    
    # Step 3: Optimization Loop (Inquisitor <-> Artisan)
    max_loops = 3
    current_content = master_draft
    
    for i in range(max_loops):
        if update_status_callback: update_status_callback(f"Council Review Cycle {i+1}: Inquisitor & Artisan working...")
        
        # Inquisitor Check
        review = await agent_inquisitor(current_content, topic)
        print(f"    >>> Inquisitor Status: {review.get('status')} (Score: {review.get('score')})")
        
        if review.get('status') == 'APPROVED' and review.get('score', 0) > 85:
            # Final Polish pass even if approved
            final_polish = await agent_artisan(current_content)
            return final_polish
            
        # If Rejected or Low Score, Artisan fixes it based on critique
        critique = review.get('critique', 'Improve verification and flow.')
        current_content = await agent_artisan(current_content, critique)
    
    return current_content
