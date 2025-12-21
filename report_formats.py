LIT_REVIEW_BASE = """
# 1. Introduction (Scope & Rationale)
# 2. Main Thematic Analysis
[INSTRUCTION: Generate {section_count} distinct thematic sections based on the research. 
{complexity_note}]
# {last_n}. Conclusion & Future Research
# {last}. References
"""

CASE_STUDY_BASE = """
# 1. Executive Summary
# 2. Introduction & Problem Statement
# 3. Context/Background
[INSTRUCTION: Analyze the case phases. Generate {section_count} sections covering the Strategy, Execution, and Outcome. 
{complexity_note}]
# {last_n}. Key Lessons Learned
# {last}. Conclusion
"""

WHITE_PAPER_BASE = """
# 1. Executive Summary
# 2. Market Context
[INSTRUCTION: Compare solutions. Generate {section_count} sections analyzing the technical and business ROI of the proposed solution. 
{complexity_note}]
# {last_n}. Implementation Framework
# {last}. Call to Action
"""

TECH_MANUAL_BASE = """
# 1. System Overview
# 2. Quick Start Guide
[INSTRUCTION: Technical Breakdown. Generate {section_count} sections covering Core Features, Advanced Configuration, and API usage. 
{complexity_note}]
# {last_n}. Troubleshooting
# {last}. Glossary/Appendix
"""

ARTICLE_BASE = """
# 1. The Lead (Headline)
[INSTRUCTION: Narrative Flow. Generate {section_count} sections that tell the story chronologically or thematically. Use punchy headers.
{complexity_note}]
# {last}. The Kicker (Conclusion)
"""

FORMAT_TEMPLATES = {
    "literature_review": LIT_REVIEW_BASE,
    "case_study": CASE_STUDY_BASE,
    "business_white_paper": WHITE_PAPER_BASE,
    "technical_manual": TECH_MANUAL_BASE,
    "journalistic_article": ARTICLE_BASE,
    "custom": LIT_REVIEW_BASE
}

def get_template_instructions(format_type: str, page_count: int) -> dict:
    # UPDATED LOGIC:
    # We aim for roughly 1 section per page to prevent "huge paragraphs".
    # This forces the AI to break down the topic into smaller, more specific sub-headers.
    
    if page_count <= 4:
        tier = "short"
        target_sections = 4
        complexity_instruction = "Keep the structure concise. Focus only on the most critical high-level points."
    
    elif page_count <= 8:
        tier = "standard"
        target_sections = 8 
        complexity_instruction = "Standard report depth. Break down the main topic into distinct sub-themes for clarity."
    
    elif page_count <= 14:
        tier = "deep"
        target_sections = 12
        complexity_instruction = "Deep-dive analysis. Include sections for Background, Economic Impact, Technical Nuance, and Future Outlook."
    
    elif page_count <= 20:
        tier = "comprehensive"
        target_sections = 16
        complexity_instruction = "Comprehensive coverage. dedicating specific sections to Case Studies, Data Analysis, and Strategic Implications."
    
    else:
        tier = "monograph"
        target_sections = 20
        complexity_instruction = "Extremely detailed research monograph. Exhaustive analysis of all dimensions, including historical context and global impact."

    selected_template = FORMAT_TEMPLATES.get(format_type, LIT_REVIEW_BASE)
    
    # Calculate how many "dynamic" sections go in the middle
    # We subtract 3 because usually 3 sections are fixed (Intro, [Middle...], Conclusion, Refs)
    dynamic_middle_count = max(2, target_sections - 3)

    final_template = selected_template.format(
        section_count=str(dynamic_middle_count),
        complexity_note=complexity_instruction,
        last_n=str(target_sections - 1),
        last=str(target_sections)
    )

    return {
        "template_text": final_template,
        "target_sections": target_sections,
        "tier": tier
    }