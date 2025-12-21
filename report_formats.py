# report_formats.py

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
    if page_count <= 5:
        tier = "short"
        target_sections = 4
        complexity_instruction = "Keep the structure concise. Focus only on the most critical high-level points."
    elif page_count <= 12:
        tier = "medium"
        target_sections = 7
        complexity_instruction = "Standard report depth. Include background, main analysis, and distinct sub-themes."
    elif page_count <= 20:
        tier = "long"
        target_sections = 10 
        complexity_instruction = "Comprehensive deep-dive. Add extra sections for Context, Economic Impact, Future Outlook."
    else:
        tier = "very_long"
        target_sections = 15
        complexity_instruction = "Extremely detailed research report. Deep analysis of all technical, economic, and strategic dimensions."

    selected_template = FORMAT_TEMPLATES.get(format_type, LIT_REVIEW_BASE)
    dynamic_middle_count = max(2, target_sections - 3)

    final_template = selected_template.format(
        section_count=str(dynamic_middle_count) + " to " + str(dynamic_middle_count + 2),
        complexity_note=complexity_instruction,
        last_n=str(target_sections - 1),
        last=str(target_sections)
    )

    return {
        "template_text": final_template,
        "target_sections": target_sections,
        "tier": tier
    }