import os
import serpapi
from docx import Document
from docx.shared import Inches, Pt, RGBColor
import httpx
from bs4 import BeautifulSoup
import json
import re
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
import fitz 

from report_formats import get_template_instructions

# --- CONFIGURATION ---
SMART_MODEL = "x-ai/grok-4.1-fast:free"
BACKUP_MODEL = "meta-llama/llama-3.3-70b-instruct:free"

SEARCH_RESULTS_COUNT = 10
MAX_RESULTS_TO_SCRAPE = 4
WORDS_PER_PAGE = 400

# --- HELPER FUNCTIONS ---
def clean_ai_output(text: str) -> str:
    if not text: return ""
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    text = re.sub(r'^```\w*\s*', '', text, flags=re.MULTILINE)
    text = re.sub(r'^```\s*$', '', text, flags=re.MULTILINE)
    return text.strip()

def clean_section_output(text: str, section_title: str) -> str:
    if not text: return ""
    text = clean_ai_output(text)
    lines = text.split('\n')
    while lines and not lines[0].strip(): lines.pop(0)
    if not lines: return ""
    first_line = lines[0].strip().lower()
    clean_title = section_title.lower().replace('#', '').strip()
    clean_first = first_line.replace('#', '').strip()
    if clean_title in clean_first or clean_first in clean_title:
        return "\n".join(lines[1:]).strip()
    return text.strip()

# --- LLM CALLER ---
def call_llm(target_model: str, system_prompt: str, user_prompt: str, temp: float = 0.4, attempt: int = 1) -> str:
    current_model = target_model
    if attempt == 2:
        current_model = BACKUP_MODEL
        print(f"   >>> Model Switch: {current_model}")
    elif attempt > 2:
        return "Error: AI models unavailable."

    try:
        api_key = os.environ.get("OPENROUTER_API_KEY")
        timeout = 90.0 
        
        system_prompt += " Output raw Markdown only. No code blocks."

        with httpx.Client(timeout=timeout) as client:
            response = client.post(
                url="https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}", 
                    "Content-Type": "application/json",
                    "HTTP-Referer": "http://localhost:5000",
                    "X-Title": "ScholarForge"
                },
                json={
                    "model": current_model,
                    "messages": [
                        {"role": "system", "content": system_prompt}, 
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": temp,
                    "max_tokens": 4000
                }
            )
            if response.status_code != 200:
                print(f"   [!] AI Error ({current_model}): {response.status_code}")
                return call_llm(target_model, system_prompt, user_prompt, temp, attempt + 1)
                
            return clean_ai_output(response.json()['choices'][0]['message']['content'])
    except Exception as e:
        print(f"   [!] Exception ({current_model}): {e}")
        return call_llm(target_model, system_prompt, user_prompt, temp, attempt + 1)

# --- SCRAPING & PDF ---

def extract_text_from_multiple_pdfs(file_bytes_list: list) -> str:
    """Feature: Extract text from MULTIPLE uploaded PDFs"""
    combined_text = "\n\n--- USER UPLOADED DOCUMENTS ---\n"
    
    try:
        for idx, file_bytes in enumerate(file_bytes_list):
            with fitz.open(stream=file_bytes, filetype="pdf") as doc:
                doc_text = ""
                # Limit to first 15 pages per doc to prevent overload
                for i, page in enumerate(doc):
                    if i > 15: break
                    doc_text += page.get_text()
                
                combined_text += f"\n[Document {idx+1} Content]:\n{doc_text[:10000]}\n" # Cap each doc
        
        combined_text += "\n------------------------------\n"
        return combined_text
    except Exception as e:
        print(f"PDF Error: {e}")
        return ""

def _get_article_text(url: str) -> str:
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        with httpx.Client(timeout=10.0, follow_redirects=True) as client:
            response = client.get(url, headers=headers)
        if response.status_code != 200: return ""
        
        if "application/pdf" in response.headers.get("Content-Type", "") or url.endswith(".pdf"):
            return "" 
            
        soup = BeautifulSoup(response.text, 'lxml')
        for tag in soup(['script', 'style', 'nav', 'footer', 'aside']): tag.decompose()
        return soup.get_text(separator='\n', strip=True)[:3000]
    except: return ""

def get_search_results(query: str, max_results: int = SEARCH_RESULTS_COUNT) -> str:
    """Feature: Structured Source Verification"""
    try:
        api_key = os.environ.get("SERPAPI_KEY") 
        if not api_key: return "Error: SERPAPI_KEY not set."
        client = serpapi.Client(api_key=api_key)
        results = client.search({"q": query, "location": "US", "hl": "en", "gl": "us", "num": 5, "engine": "google"})
        
        formatted_output = "--- VERIFIED SOURCES ---\n"
        
        if "organic_results" in results:
            for i, result in enumerate(results["organic_results"]):
                if i >= MAX_RESULTS_TO_SCRAPE: break
                
                url = result.get("link", "")
                title = result.get('title', 'Unknown Title')
                snippet = result.get("snippet", "")
                
                # Fetch deep content
                full_content = ""
                if url:
                    raw = _get_article_text(url)
                    if raw: full_content = f"\nEXTRACT: {raw}"
                
                # Index the source [1], [2]...
                formatted_output += f"SOURCE [{i+1}]\nTitle: {title}\nURL: {url}\nSummary: {snippet}{full_content}\n\n"
                
        return formatted_output
    except Exception as e: return f"Search Error: {e}"

# --- RECURSIVE AGENT LOGIC ---

# --- CONSOLIDATED PLANNING ---

def plan_report_consolidated(query: str, search_content: str, user_pdf_text: str, format_type: str, target_pages: int) -> dict:
    """Consolidates Summary, Chart JSON, and Outline into ONE API call."""
    format_data = get_template_instructions(format_type, target_pages)
    context = (user_pdf_text + "\n\n" + search_content) if user_pdf_text else search_content
    
    prompt = (
        f"Topic: {query}\n"
        f"Target Sections: {format_data['target_sections']}\n"
        f"Format Style: {format_data['template_text']}\n"
        f"Research Data:\n{context[:25000]}\n\n"
        "--- TASK ---\n"
        "Generate a structured report plan in JSON format with exactly three keys:\n"
        "1. 'summary': A 500-word master factual summary of all data.\n"
        "2. 'chart_data': { 'title': '...', 'x_label': '...', 'y_label': '...', 'data': [{'label': 'A', 'value': 10}] }\n"
        "3. 'outline': A list of strings for section titles.\n\n"
        "Output raw JSON only."
    )
    
    response_text = call_llm(SMART_MODEL, "You are a Research Director. Output JSON only.", prompt, temp=0.2)
    
    try:
        # Clean and parse JSON
        match = re.search(r'\{.*\}', response_text.replace('\n', ' '), re.DOTALL)
        if match:
            data = json.loads(match.group(0))
            return {
                "summary": data.get("summary", "Summary generation failed."),
                "chart_data": data.get("chart_data", {}),
                "outline": data.get("outline", ["Introduction", "Analysis", "Conclusion"])
            }
    except Exception as e:
        print(f"JSON Planning Error: {e}")
    
    # Fallback if JSON fails
    return {
        "summary": "Data synthesis in progress...",
        "chart_data": {},
        "outline": ["Introduction", "Analysis", "Conclusion"]
    }

def write_sections_bundle(section_titles: list, topic: str, summary: str, word_limit_per_section: int) -> str:
    """Writes multiple sections in ONE API call to save money/usage."""
    titles_str = ", ".join(section_titles)
    base_prompt = (
        f"Write the following sections for topic '{topic}': {titles_str}\n\n"
        f"Research Summary:\n{summary[:15000]}\n\n"
        f"INSTRUCTIONS:\n"
        f"1. Write approximately {word_limit_per_section} words for EACH section listed.\n"
        f"2. Use Markdown. Start each section with '## Section Title'.\n"
        f"3. CITATION REQUIREMENT: Cite sources using [1], [2] or [Doc 1].\n"
        "4. DO NOT repeat content across sections."
    )
    
    content = call_llm(SMART_MODEL, "You are a Report Writer. Focus on technical depth and citations.", base_prompt, temp=0.4)
    return clean_ai_output(content)

# write_section is now legacy, replaced by write_sections_bundle

# --- CHARTING ---
def generate_chart_from_data(summary: str, topic: str) -> str:
    try:
        chart_dir = "/app/static/charts"
        if not os.path.exists(chart_dir): os.makedirs(chart_dir, exist_ok=True)
        clean_name = re.sub(r'\W+', '', topic)[:15] 
        filename = f"chart_{clean_name}_{os.urandom(4).hex()}.png"
        filepath = os.path.join(chart_dir, filename)

        prompt = (
            f"Topic: {topic}\nContext: {summary[:3000]}\n"
            "Extract key numeric trends. Return JSON: {\"title\": \"...\", \"x_label\": \"...\", \"y_label\": \"...\", \"data\": [{\"label\": \"A\", \"value\": 10}]}"
        )
        content = call_llm(SMART_MODEL, "Return JSON only.", prompt, temp=0.1)
        match = re.search(r'\{.*\}', content.replace('\n', ' '), re.DOTALL)
        if not match: return None
        chart_data = json.loads(match.group(0))
        if not chart_data or 'data' not in chart_data: return None

        df = pd.DataFrame(chart_data['data'])
        fig, ax = plt.subplots(figsize=(10, 6))
        plt.style.use('ggplot')
        ax.bar(df['label'], df['value'], color='#4f46e5', alpha=0.8)
        ax.set_title(chart_data.get('title', 'Analysis'), fontsize=14, pad=20)
        ax.set_xlabel(chart_data.get('x_label', ''), fontsize=12)
        ax.set_ylabel(chart_data.get('y_label', ''), fontsize=12)
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        fig.tight_layout()
        fig.savefig(filepath, dpi=100)
        plt.close(fig)
        return filepath
    except: return None

# --- MAIN ORCHESTRATOR ---
def run_ai_engine_with_return(query: str, user_format: str, page_count: int = 15, pdf_bytes_list: list = None, task=None) -> tuple[str, str, str]: 
    def _update_status(message: str):
        print(message) 
        if task: task.update_state(state='PROGRESS', meta={'message': message})

    _update_status("Step 1/5: Processing & Initial Search...")
    
    # 1. Process User PDFs
    user_pdf_text = ""
    if pdf_bytes_list:
        user_pdf_text = extract_text_from_multiple_pdfs(pdf_bytes_list)
    
    search_content = get_search_results(query)
    
    _update_status("Step 2/5: Planning & Synthesis (Consolidated Call 1/X)...")
    # THE CONSOLIDATED PLANNING CALL
    plan = plan_report_consolidated(query, search_content, user_pdf_text, user_format, page_count)
    summary = plan['summary']
    outline = plan['outline']
    
    _update_status("Step 3/5: Generating Visuals...")
    chart_path = None
    if plan['chart_data']:
        try:
            chart_dir = "/app/static/charts"
            if not os.path.exists(chart_dir): os.makedirs(chart_dir, exist_ok=True)
            clean_name = re.sub(r'\W+', '', query)[:15] 
            filename = f"chart_{clean_name}_{os.urandom(4).hex()}.png"
            filepath = os.path.join(chart_dir, filename)

            df = pd.DataFrame(plan['chart_data']['data'])
            fig, ax = plt.subplots(figsize=(10, 6))
            plt.style.use('ggplot')
            ax.bar(df['label'], df['value'], color='#4f46e5', alpha=0.8)
            ax.set_title(plan['chart_data'].get('title', 'Analysis'), fontsize=14, pad=20)
            ax.set_xlabel(plan['chart_data'].get('x_label', ''), fontsize=12)
            ax.set_ylabel(plan['chart_data'].get('y_label', ''), fontsize=12)
            plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
            fig.tight_layout()
            fig.savefig(filepath, dpi=100)
            plt.close(fig)
            chart_path = filepath
        except: pass

    _update_status("Step 4/5: Deep Writing (Bundled Calls)...")
    
    # DETERMINE CALL COUNTS BASED ON USER SPECIFICATIONS
    # 7 pages -> 4 total calls (1 plan + 3 write)
    # 15 pages -> 8 total calls (1 plan + 7 write)
    # 25 pages -> 12 total calls (1 plan + 11 write)
    if page_count <= 12: max_writing_calls = 3 # 7 page case
    elif page_count <= 20: max_writing_calls = 7 # 15 page case
    else: max_writing_calls = 11 # 25 page case
    
    # Split outline into bundles precisely to hit the target call count
    num_sections = len(outline)
    bundles = []
    sections_left = outline[:]
    calls_left = max_writing_calls
    
    while sections_left and calls_left > 0:
        # Ceiling division to distribute fairly
        take = max(1, -(-len(sections_left) // calls_left))
        bundles.append(sections_left[:take])
        sections_left = sections_left[take:]
        calls_left -= 1

    full_report = f"# {query.upper()}\n\n"
    for i, bundle in enumerate(bundles):
        _update_status(f"   > Writing Bundle {i+1}/{len(bundles)}...")
        bundle_content = write_sections_bundle(bundle, query, summary, 500)
        full_report += f"\n{bundle_content}\n"
    
    _update_status("Step 5/5: Finalizing...")
    full_report = clean_ai_output(full_report)
    
    return search_content + "\n" + user_pdf_text, full_report, chart_path

# --- CONVERTERS (Unchanged) ---
def convert_to_txt(content, path):
    with open(path, "w", encoding="utf-8") as f: f.write(content)
    return "Success"
def convert_to_md(content, path):
    with open(path, "w", encoding="utf-8") as f: f.write(content)
    return "Success"
def convert_to_json(content, topic, path):
    data = {"topic": topic, "content": content, "generated_by": "ScholarForge"}
    with open(path, "w", encoding="utf-8") as f: json.dump(data, f, indent=4)
    return "Success"
def add_formatted_text(paragraph, text):
    parts = re.split(r'(\*\*[^*]+\*\*)', text)
    for part in parts:
        if part.startswith('**') and part.endswith('**'):
            run = paragraph.add_run(part[2:-2])
            run.bold = True
            run.font.color.rgb = RGBColor(0, 0, 0)
        else: paragraph.add_run(part)
def _add_markdown_table_to_docx(doc, table_block):
    lines = [l.strip() for l in table_block.strip().split('\n') if l.strip()]
    if len(lines) < 3: return
    rows = []
    for line in lines:
        if '---' in line: continue 
        cells = [c.strip().replace('**','') for c in line.strip('|').split('|')]
        rows.append(cells)
    if not rows: return
    table = doc.add_table(rows=len(rows), cols=len(rows[0]))
    table.style = 'Table Grid'
    for r_idx, row_data in enumerate(rows):
        for c_idx, cell_data in enumerate(row_data):
            if c_idx < len(table.columns):
                cell = table.cell(r_idx, c_idx)
                cell.text = cell_data
                if r_idx == 0: cell.paragraphs[0].runs[0].bold = True
def convert_to_docx(content, topic, path, chart_path=None):
    doc = Document()
    doc.add_heading(topic, 0)
    if chart_path and os.path.exists(chart_path):
        try: doc.add_picture(chart_path, width=Inches(6)); doc.add_paragraph("Figure 1: Analysis", style='Caption')
        except: pass
    lines = content.split('\n')
    table_buffer = []
    in_table = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('|') and '|' in stripped[1:]:
            in_table = True; table_buffer.append(stripped); continue
        elif in_table:
            _add_markdown_table_to_docx(doc, "\n".join(table_buffer)); table_buffer = []; in_table = False
        if not stripped: continue
        if stripped.startswith('## '): doc.add_heading(stripped.replace('## ', ''), level=2)
        elif stripped.startswith('# '): doc.add_heading(stripped.replace('# ', ''), level=1)
        elif stripped.startswith('### '): doc.add_heading(stripped.replace('### ', ''), level=3)
        elif stripped.startswith('* ') or stripped.startswith('- '): p = doc.add_paragraph(style='List Bullet'); add_formatted_text(p, stripped[2:])
        else: p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(6); add_formatted_text(p, stripped)
    if in_table and table_buffer: _add_markdown_table_to_docx(doc, "\n".join(table_buffer))
    doc.save(path); return "Success"
def format_pdf_text(text):
    text = text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)
def convert_to_pdf(content, topic, path, chart_path=None):
    doc = SimpleDocTemplate(path, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    styles = getSampleStyleSheet()
    story = [Paragraph(topic, styles['Title']), Spacer(1, 12)]
    if chart_path and os.path.exists(chart_path):
        try: story.append(RLImage(chart_path, width=450, height=250)); story.append(Spacer(1, 12))
        except: pass
    lines = content.split('\n')
    table_buffer = []
    in_table = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('|') and '|' in stripped[1:]:
            in_table = True; table_buffer.append(stripped); continue
        elif in_table:
            data = [[c.strip().replace('**','') for c in row.strip('|').split('|') if '---' not in row] for row in table_buffer if '---' not in row]
            if data: story.append(Table(data, style=[('GRID', (0,0), (-1,-1), 1, colors.black)])); story.append(Spacer(1, 12))
            table_buffer = []; in_table = False
        if not stripped: continue
        clean_text = format_pdf_text(stripped)
        if stripped.startswith('##'): story.append(Paragraph(clean_text.replace('#', ''), styles['Heading2']))
        elif stripped.startswith('*') or stripped.startswith('-'): story.append(Paragraph(f"• {clean_text[2:]}", styles['Normal']))
        else: story.append(Paragraph(clean_text, styles['Normal']))
    doc.build(story); return "Success"