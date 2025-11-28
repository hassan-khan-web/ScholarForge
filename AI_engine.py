import os
import serpapi
from docx import Document
import httpx
from bs4 import BeautifulSoup
import json
import re
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# IMPORT THE FORMAT LOGIC
from report_formats import get_template_instructions

AI_MODEL_STRING = "x-ai/grok-4.1-fast:free" 
SEARCH_RESULTS_COUNT = 10
MAX_RESULTS_TO_SCRAPE = 3
WORDS_PER_PAGE = 400

# --- HELPER FUNCTIONS ---

def clean_ai_output(text: str) -> str:
    """Strips markdown fences to prevent raw code block rendering."""
    if not text: return ""
    cleaned = re.sub(r'^```\w*\n?', '', text)
    cleaned = re.sub(r'\n?```$', '', cleaned)
    return cleaned.strip()

# --- SCRAPING & SEARCHING ---

def _get_article_text(url: str) -> str:
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        with httpx.Client(timeout=10.0, follow_redirects=True) as client:
            response = client.get(url, headers=headers)
            
        if response.status_code != 200:
            return ""

        soup = BeautifulSoup(response.text, 'html.parser')
        
        for script in soup(["script", "style", "nav", "footer", "header", "aside", "form", "iframe"]):
            script.decompose()

        content = soup.find('article') or soup.find('main') or soup.find('div', class_=re.compile(r'content|post|article|body'))
        if not content: content = soup

        paragraphs = content.find_all(['p', 'h2', 'h3', 'li'])
        text_content = []
        
        for p in paragraphs:
            text = p.get_text().strip()
            if len(text.split()) > 6:
                text_content.append(text)

        article_text = "\n\n".join(text_content)
        return article_text[:3000]
    except Exception:
        return ""

def get_search_results(query: str) -> str:
    try:
        api_key = os.environ.get("SERPAPI_KEY") 
        if not api_key: return "Error: SERPAPI_KEY environment variable not set."
            
        params = {
            "q": query, "location": "US", "hl": "en", "gl": "us",
            "num": SEARCH_RESULTS_COUNT, "api_key": api_key, "engine": "google"
        }

        client = serpapi.Client(api_key=api_key)
        results = client.search(params)
        
        if "error" in results: return f"Error from SerpApi: {results['error']}"

        snippets = []
        if "organic_results" in results:
            for i, result in enumerate(results["organic_results"]):
                snippet_text = result.get("snippet", "")
                source_url = result.get("link", "")
                title = result.get('title', 'No Title')

                full_content_text = ""
                if i < MAX_RESULTS_TO_SCRAPE and source_url:
                    raw_text = _get_article_text(source_url)
                    if raw_text:
                        full_content_text = f"\n[Full Content Source {i+1}]:\n{raw_text}\n"

                formatted_snippet = f"Source [{i+1}]: {title}\nURL: {source_url}\nSummary: {snippet_text}{full_content_text}" 
                snippets.append(formatted_snippet)

        return "\n\n".join(snippets) if snippets else "No relevant search results were found."
    except Exception as e:
        return f"Search Error: {e}"

# --- AI GENERATION FUNCTIONS ---

def generate_summary(search_content: str, topic: str) -> str:
    try:
        api_key = os.environ.get("OPENROUTER_API_KEY")
        if not api_key: return "Error: OPENROUTER_API_KEY not set."

        system_instruction = "You are a Senior Research Analyst. Synthesize the raw data into a structured research briefing."
        prompt = f"Topic: {topic}\n\nRaw Search Data:\n{search_content[:12000]}\n\nTask: Create a comprehensive research summary." 

        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": AI_MODEL_STRING,
                    "messages": [
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.4,
                    "max_tokens": 1500
                }
            )
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"Summarization Error: {e}"

def generate_outline(topic: str, summary: str, format_type: str, target_pages: int) -> list:
    try:
        api_key = os.environ.get("OPENROUTER_API_KEY")
        
        format_data = get_template_instructions(format_type, target_pages)
        target_sections = format_data['target_sections']
        template_text = format_data['template_text']
        tier = format_data['tier']

        system_instruction = "You are a Report Architect. Return ONLY a valid JSON array of strings."
        prompt = (
            f"Topic: {topic}\n"
            f"Target: {target_sections} main sections ({tier}).\n"
            f"Structure Logic: {template_text}\n"
            f"Context: {summary[:2000]}\n\n"
            "Output Format: JSON Array ONLY. Example: [\"1. Introduction\", \"2. Analysis\", \"3. Conclusion\"]"
        )

        with httpx.Client(timeout=30.0) as client:
            response = client.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": AI_MODEL_STRING,
                    "messages": [
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3
                }
            )
            content = response.json()['choices'][0]['message']['content']
        
        match = re.search(r'\[.*\]', content.replace('\n', ' '), re.DOTALL)
        if match:
            return json.loads(match.group(0))
            
        if tier == "short": return ["1. Introduction", "2. Main Analysis", "3. Conclusion"]
        return ["1. Intro", "2. Background", "3. Analysis A", "4. Analysis B", "5. Conclusion"]

    except Exception as e:
        print(f"Outline Error: {e}")
        return ["1. Introduction", "2. Main Analysis", "3. Conclusion"]

def write_section(section_title: str, topic: str, summary: str, previous_context: str, word_limit: int) -> str:
    try:
        api_key = os.environ.get("OPENROUTER_API_KEY")
        
        system_instruction = (
            f"You are a Report Writer. Write detailed, academic content for the section: '{section_title}'."
            " Use Markdown formatting (bold, lists). Do not include the Section Title at the start."
        )
        
        prompt = (
            f"Report Topic: {topic}\n"
            f"Research Brief: {summary}\n"
            f"Write Section: {section_title}\n"
            f"Target Length: {word_limit} words.\n"
        )

        with httpx.Client(timeout=60.0) as client:
            response = client.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                json={
                    "model": AI_MODEL_STRING,
                    "messages": [
                        {"role": "system", "content": system_instruction},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.5,
                    "max_tokens": 2000 
                }
            )
            raw_content = response.json()['choices'][0]['message']['content']
            return clean_ai_output(raw_content)
    except Exception as e:
        return f"(Error writing section {section_title}: {e})"

# --- MAIN ORCHESTRATOR ---

def run_ai_engine_with_return(query: str, user_format: str, page_count: int = 15, task=None) -> tuple[str, str]: 
    
    def _update_status(message: str):
        print(message) 
        if task: task.update_state(state='PROGRESS', meta={'message': message})

    if not query: return "No query provided.", ""

    # 1. SEARCH
    _update_status("Step 1/5: Gathering Intelligence...")
    search_content = get_search_results(query)
    if search_content.startswith("Search Error"):
        search_content = "Search failed, proceeding with general knowledge."

    # 2. SUMMARY
    _update_status("Step 2/5: Analyzing Data...")
    summary = generate_summary(search_content, query)
    
    # 3. OUTLINE
    _update_status(f"Step 3/5: Structuring Report...")
    outline = generate_outline(query, summary, user_format, page_count)
    
    # 4. MATH LOGIC 
    total_target_words = page_count * WORDS_PER_PAGE 
    words_per_section = int(total_target_words / max(1, len(outline)))
    words_per_section = max(300, min(words_per_section, 1500))
    
    # 5. WRITE SECTIONS
    full_report = f"# {query.upper()}\n\n"
    total_sections = len(outline)
    
    for i, section in enumerate(outline):
        _update_status(f"Step 4/5: Writing Section {i+1}/{total_sections}...")
        section_content = write_section(section, query, summary, full_report, words_per_section)
        full_report += f"\n\n## {section}\n{section_content}\n"
    
    _update_status("Step 5/5: Finalizing Document...")
    full_report = clean_ai_output(full_report)
    
    return search_content, full_report

# --- CONVERTERS ---

def convert_to_txt(report_content: str, filepath: str) -> str:
    try:
        with open(filepath, "w", encoding="utf-8") as f: f.write(report_content)
        return f"Success: TXT file created at {filepath}"
    except Exception as e: return f"Error creating TXT: {e}"

def convert_to_docx(report_content: str, topic: str, filepath: str) -> str:
    try:
        doc = Document()
        doc.add_heading(topic, 0)
        lines = report_content.split('\n')
        for line in lines:
            line = line.strip()
            if not line: continue
            if line.startswith('## '): doc.add_heading(line.replace('## ', ''), level=2)
            elif line.startswith('# '): doc.add_heading(line.replace('# ', ''), level=1)
            elif line.startswith('### '): doc.add_heading(line.replace('### ', ''), level=3)
            elif line.startswith('* ') or line.startswith('- '): doc.add_paragraph(line[2:], style='List Bullet')
            else: doc.add_paragraph(line)
        doc.save(filepath)
        return f"Success: DOCX file created at {filepath}"
    except Exception as e: return f"Error creating DOCX: {e}"

def convert_to_pdf(report_content: str, topic: str, filepath: str) -> str:
    try:
        doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
        styles = getSampleStyleSheet()
        flowables = []
        flowables.append(Paragraph(topic, styles['Title']))
        flowables.append(Spacer(1, 12))
        
        style = ParagraphStyle('Body', parent=styles['Normal'], fontSize=11, leading=15, spaceAfter=10)
        heading_style = ParagraphStyle('Heading', parent=styles['Heading2'], fontSize=14, spaceAfter=10, spaceBefore=10)
        
        lines = report_content.split('\n')
        for line in lines:
            clean_line = line.strip().replace('#', '').replace('*', '&bull;')
            if not clean_line: continue
            if line.startswith('#'):
                flowables.append(Paragraph(clean_line, heading_style))
            else:
                flowables.append(Paragraph(clean_line, body_style))

        doc.build(flowables)
        return f"Success: PDF file created at {filepath}"
    except Exception as e: 
        return f"Error creating PDF: {e}"

def convert_to_json(report_content: str, topic: str, filepath: str) -> str:
    try:
        data = {
            "topic": topic,
            "content": report_content,
            "generated_by": "ScholarForge"
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        return f"Success: JSON file created at {filepath}"
    except Exception as e: return f"Error creating JSON: {e}"