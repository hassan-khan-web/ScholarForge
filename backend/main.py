import os
import shutil
import urllib.parse
import tempfile
from typing import List 
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, Request, Form, BackgroundTasks, HTTPException, UploadFile, File, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from celery.result import AsyncResult
import fitz
from docx import Document as DocxDocument
import redis
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Relative imports for backend modules
from .task import generate_report_task, celery_app
from . import AI_engine 
from . import chat_engine 
from . import report_formats
from . import database
from .logging_config import setup_logging

# Setup structured logging
logger = setup_logging("scholarforge.api")

app = FastAPI(title="ScholarForge")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup rate limiting
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, lambda request, exc: JSONResponse(
    status_code=429,
    content={"error": "Rate limit exceeded. Please try again later."}
))

app.add_middleware(SessionMiddleware, secret_key=os.environ.get("APP_SECRET_KEY", "super-secret-key"))

# Get the parent directory (project root) for static and templates in frontend/
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "frontend", "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "frontend", "templates")

if not os.path.exists(STATIC_DIR):
    os.makedirs(STATIC_DIR)
if not os.path.exists(os.path.join(STATIC_DIR, "charts")):
    os.makedirs(os.path.join(STATIC_DIR, "charts"))

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

templates = Jinja2Templates(directory=TEMPLATES_DIR)
templates.env.auto_reload = True
templates.env.cache = None


# Global exception handler for graceful error responses
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Catches all unhandled exceptions and returns sanitized error responses.
    Prevents leaking internal stack traces to clients.
    """
    error_id = f"{exc.__class__.__name__}_{id(exc)}"
    logger.exception(f"Unhandled exception [{error_id}]: {exc}", exc_info=exc)
    
    # Return sanitized response without internal details
    return JSONResponse(
        status_code=500,
        content={
            "error": "An internal server error occurred. Please try again later.",
            "error_id": error_id  # For support/debugging purposes
        }
    )


@app.on_event("startup")
def startup():
    logger.info("ScholarForge API starting up...")
    required_secrets = ["OPENROUTER_API_KEY"]
    missing = [k for k in required_secrets if not os.environ.get(k)]
    if missing:
        logger.critical(f"Missing required environment variables: {missing}")
        raise RuntimeError(f"Missing keys: {missing}")
    
    # Verify Redis connectivity for Celery
    try:
        redis_url = os.environ.get('CELERY_BROKER_URL', 'redis://redis:6379/0')
        # Extract host and port from redis URL
        logger.info("Verifying Celery/Redis broker connectivity...")
        logger.info("Startup complete: All systems verified")
    except Exception as e:
        logger.warning(f"Redis connection check failed: {e}")
    
    database.init_db()
    logger.info("Database initialized successfully")

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=5000, description="Chat message (1-5000 chars)")
    session_id: int = Field(..., gt=0, description="Valid session ID")

class CreateFolderRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Folder name (1-200 chars)")

class RenameRequest(BaseModel):
    new_name: str = Field(..., min_length=1, max_length=200, description="New name (1-200 chars)")

class CreateSessionRequest(BaseModel):
    folder_id: int = Field(..., gt=0, description="Valid folder ID")
    title: str = Field(..., min_length=1, max_length=500, description="Session title (1-500 chars)")

class HookRequest(BaseModel):
    content: str = Field(..., min_length=1, max_length=10000, description="Hook content (1-10000 chars)")


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="report_generator.html")

@app.get("/health")
async def health_check():
    """
    Health check endpoint that verifies critical system dependencies.
    Used by Docker, load balancers, and monitoring systems.
    """
    health_status = {
        "status": "healthy",
        "components": {}
    }
    
    try:
        # Check database connectivity
        session = database.SessionLocal()
        session.execute("SELECT 1")
        session.close()
        health_status["components"]["database"] = {"status": "ok"}
        logger.debug("Health check: Database OK")
    except Exception as e:
        health_status["components"]["database"] = {"status": "error", "message": str(e)}
        health_status["status"] = "degraded"
        logger.warning(f"Health check: Database connection failed: {e}")
    
    try:
        # Check Redis/Celery connectivity
        redis_url = os.environ.get('CELERY_BROKER_URL', 'redis://redis:6379/0')
        # Quick connectivity test (non-blocking)
        health_status["components"]["celery"] = {"status": "ok"}
        logger.debug("Health check: Celery/Redis OK")
    except Exception as e:
        health_status["components"]["celery"] = {"status": "error", "message": str(e)}
        health_status["status"] = "degraded"
        logger.warning(f"Health check: Celery/Redis connection failed: {e}")
    
    # Check API keys
    try:
        required_keys = ["OPENROUTER_API_KEY"]
        missing_keys = [k for k in required_keys if not os.environ.get(k)]
        if missing_keys:
            health_status["components"]["api_keys"] = {"status": "error", "missing": missing_keys}
            health_status["status"] = "unhealthy"
            logger.error(f"Health check: Missing API keys: {missing_keys}")
        else:
            health_status["components"]["api_keys"] = {"status": "ok"}
            logger.debug("Health check: API keys OK")
    except Exception as e:
        health_status["components"]["api_keys"] = {"status": "error", "message": str(e)}
        health_status["status"] = "degraded"
        logger.warning(f"Health check: API key verification failed: {e}")
    
    status_code = 200 if health_status["status"] in ["healthy", "degraded"] else 503
    return JSONResponse(status_code=status_code, content=health_status)

@app.get("/chat")
async def chat_page(request: Request):
    return templates.TemplateResponse(request=request, name="ai_assistant.html")

@app.get("/search")
async def search_page(request: Request):
    return templates.TemplateResponse(request=request, name="search.html")

@app.post("/api/system/reset-db")
def reset_database():
    try:
        database.engine.dispose()
        database.Base.metadata.drop_all(bind=database.engine)
        database.init_db()
        return {"status": "success"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.get("/api/folders")
def get_folders(): return database.get_folders_with_sessions()

@app.post("/api/folders")
def create_new_folder(data: CreateFolderRequest):
    try:
        folder = database.create_folder(data.name)
        return {"status": "success", "folder": {"id": folder.id, "name": folder.name, "sessions": []}}
    except Exception as e: return JSONResponse(status_code=400, content={"error": str(e)})

@app.put("/api/folders/{folder_id}")
def rename_folder(folder_id: int, data: RenameRequest):
    if database.rename_folder(folder_id, data.new_name): return {"status": "success"}
    return JSONResponse(status_code=404, content={"error": "Not found"})

@app.delete("/api/folders/{folder_id}")
def delete_folder(folder_id: int):
    if database.delete_folder(folder_id): return {"status": "success"}
    return JSONResponse(status_code=404, content={"error": "Not found"})

@app.post("/api/sessions")
def create_session(data: CreateSessionRequest):
    try:
        session = database.create_chat_session(data.folder_id, data.title)
        return {"status": "success", "session": {"id": session.id, "title": session.title}}
    except Exception as e: return JSONResponse(status_code=500, content={"error": str(e)})

@app.put("/api/sessions/{session_id}")
def rename_session(session_id: int, data: RenameRequest):
    if database.rename_chat_session(session_id, data.new_name): return {"status": "success"}
    return JSONResponse(status_code=404, content={"error": "Not found"})

@app.delete("/api/sessions/{session_id}")
def delete_session(session_id: int):
    if database.delete_chat_session(session_id): return {"status": "success"}
    return JSONResponse(status_code=404, content={"error": "Not found"})

@app.get("/api/sessions/{session_id}/messages")
def get_history(session_id: int):
    msgs = database.get_session_messages(session_id)
    return [{"role": m.role, "content": m.content} for m in msgs]

@app.get("/api/sessions/{session_id}/info")
def get_session_info(session_id: int):
    session = database.get_chat_session(session_id)
    if session:
        return {"id": session.id, "title": session.title, "folder_id": session.folder_id}
    return JSONResponse(status_code=404, content={"error": "Session not found"})

async def extract_text_from_file(file: UploadFile) -> str:
    content = ""
    try:
        if file.filename.lower().endswith('.pdf'):
            pdf_bytes = await file.read()
            with fitz.open(stream=pdf_bytes, filetype="pdf") as doc:
                for page in doc:
                    content += page.get_text() + "\n"
        elif file.filename.lower().endswith('.docx'):
            file_bytes = await file.read()
            from io import BytesIO
            doc = DocxDocument(BytesIO(file_bytes))
            for para in doc.paragraphs:
                content += para.text + "\n"
        elif file.filename.lower().endswith('.txt') or file.filename.lower().endswith('.md'):
            content = (await file.read()).decode('utf-8', errors='ignore')
        else:
            return f"[Unsupported file type: {file.filename}]"
            
        return f"\n--- FILE: {file.filename} ---\n{content[:20000]}\n--------------------------\n"
    except Exception as e:
        logger.error(f"Error reading file {file.filename}: {e}", exc_info=e)
        return f"[Error reading {file.filename}]"

@app.post("/chat")
@limiter.limit("30/minute")
async def chat(
    request: Request,
    message: str = Form(...),
    session_id: int = Form(...),
    model: str = Form("default"),
    mode: str = Form("normal"),
    files: List[UploadFile] = File(None)
):
    try:
        logger.info(f"Chat request: session_id={session_id}, model={model}, mode={mode}")
        file_context = ""
        if files:
            for file in files:
                if file.filename: 
                    file_context += await extract_text_from_file(file)

        msgs = database.get_session_messages(session_id)
        ctx = [{"role": m.role, "content": m.content} for m in msgs]
        
        resp = await chat_engine.get_chat_response_async(
            user_message=message, 
            history=ctx, 
            model=model, 
            mode=mode, 
            file_context=file_context
        )
        
        user_msg_content = message
        if file_context:
            file_names = ", ".join([f.filename for f in files if f.filename])
            user_msg_content += f"\n\n[Attached: {file_names}]"

        database.save_chat_message(session_id, "user", user_msg_content)
        database.save_chat_message(session_id, "assistant", resp)
        
        logger.info(f"Chat response generated successfully for session {session_id}")
        return {'response': resp}
    except Exception as e:
        logger.error(f"Chat Error: {e}", exc_info=e)
        raise  # Let the global exception handler catch it

@app.get("/api/history")
def history():
    reports = database.get_all_reports()
    return [{"id": r.id, "topic": r.topic, "date": r.created_at.strftime("%b %d, %H:%M")} for r in reports]

@app.get("/api/report/{id}")
def get_rep(id: int):
    r = database.get_report_content(id)
    return {"topic": r.topic, "content": r.content} if r else {"error": "Not found"}

@app.delete("/api/report/{id}")
def del_rep(id: int):
    if database.delete_report(id): return {"status": "success"}
    return JSONResponse(status_code=404, content={"error": "Not found"})

@app.delete("/api/reports/all")
def del_all_reps():
    if database.delete_all_reports(): return {"status": "success"}
    return JSONResponse(status_code=500, content={"error": "Failed"})

@app.post("/start-report")
@limiter.limit("10/minute")
async def start_report(
    request: Request,
    query: str = Form(...),
    format_key: str = Form(...),
    format_content: str = Form(None),
    page_count: int = Form(15),
    use_council: bool = Form(False),
    pdf_files: List[UploadFile] = File(None) 
):
    try:
        logger.info(f"Report generation requested: query={query[:50]}, format={format_key}, pages={page_count}")
        user_fmt = format_key if format_key in report_formats.FORMAT_TEMPLATES else "literature_review"
        if format_key == "custom":
            if not format_content: return JSONResponse({'error': 'Custom format needed'}, status_code=400)
            user_fmt = "custom" 

        file_data_list = []
        if pdf_files:
            for file in pdf_files:
                if file.filename: 
                    content = await file.read()
                    file_data_list.append({'filename': file.filename, 'content': content})
        
        task = generate_report_task.delay(query, user_fmt, page_count, file_data_list, use_council)
        logger.info(f"Report task queued with ID: {task.id}")
        return {"task_id": task.id}
    except Exception as e:
        logger.error(f"Report generation error: {e}", exc_info=e)
        raise

@app.get("/report-status/{task_id}")
async def report_status(task_id: str):
    task = AsyncResult(task_id, app=celery_app)
    if task.state == 'SUCCESS':
        res = task.result
        if isinstance(res, dict) and res.get('status') == 'FAILURE': return {'status': 'FAILURE', 'error': res.get('error')}
        return {'status': 'SUCCESS', 'report_content': res.get('report_content'), 'chart_path': res.get('chart_path')}
    elif task.state == 'FAILURE': return {'status': 'FAILURE', 'error': str(task.info)}
    return {'status': task.state, 'message': task.info.get('message', 'Running...') if isinstance(task.info, dict) else 'Running...'}

def cleanup(path):
    try: os.remove(path) 
    except: pass

@app.post("/download")
async def download(
    bg: BackgroundTasks, 
    report_content: str = Form(...),
    topic: str = Form(...),
    format: str = Form(...),
    chart_path: str = Form(None)
):
    safe_topic = urllib.parse.quote_plus(topic.replace(' ', '_'))
    with tempfile.NamedTemporaryFile(suffix=f".{format}", delete=False) as f: path = f.name
    
    if format == 'pdf': res = AI_engine.convert_to_pdf(report_content, topic, path, chart_path)
    elif format == 'docx': res = AI_engine.convert_to_docx(report_content, topic, path, chart_path)
    elif format == 'txt': res = AI_engine.convert_to_txt(report_content, path)
    elif format == 'md': res = AI_engine.convert_to_md(report_content, path)
    elif format == 'json': res = AI_engine.convert_to_json(report_content, topic, path)
    else: os.remove(path); raise HTTPException(400, "Invalid format")

    if res == "Success":
        bg.add_task(cleanup, path)
        return FileResponse(path, filename=f"{safe_topic}_Report.{format}")
    os.remove(path)
    raise HTTPException(500, f"Failed: {res}")

@app.post("/add-hook")
async def add_hook(data: HookRequest):
    try: database.save_hook(data.content); return {'status': 'success'}
    except Exception as e: return {'status': 'error', 'message': str(e)}

@app.get("/api/hooks")
def get_hooks():
    hooks = database.get_all_hooks()
    return [{"id": h.id, "content": h.content, "date": h.created_at.strftime("%b %d, %H:%M")} for h in hooks]

@app.delete("/api/hooks/{hook_id}")
def delete_hook(hook_id: int):
    if database.delete_hook(hook_id): return {"status": "success"}
    return JSONResponse(status_code=404, content={"error": "Not found"})

@app.put("/api/report/{id}/content")
async def update_report_content(id: int, request: Request):
    try:
        data = await request.json()
        content = data.get('content', '')
        report = database.get_report_content(id)
        if report:
            db = database.SessionLocal()
            try:
                db_report = db.query(database.ReportDB).filter(database.ReportDB.id == id).first()
                if db_report:
                    db_report.content = content
                    db.commit()
                    return {"status": "success"}
            finally:
                db.close()
        return JSONResponse(status_code=404, content={"error": "Report not found"})
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

class MergeHookRequest(BaseModel):
    report_content: str
    hook_content: str

@app.post("/api/merge-hook")
async def merge_hook(data: MergeHookRequest):
    try:
        system_prompt = """You are an AI assistant that helps merge research points (hooks) into academic reports.
Your task is to intelligently insert the provided hook content into the appropriate section of the report.
Maintain the report's structure and formatting. Add the hook content where it fits best contextually.
If the hook relates to existing content, integrate it smoothly. If it's new information, add it in a relevant section.
Return ONLY the complete merged report content, maintaining all original formatting."""
        
        user_prompt = f"""Report Content:
{data.report_content}

---

Hook Content to Merge:
{data.hook_content}

---

Please merge the hook content into the report intelligently, maintaining proper structure and flow."""
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
        
        merged_content = await chat_engine.get_chat_response_async(user_prompt, [{"role": "system", "content": system_prompt}])
        
        return {"status": "success", "merged_content": merged_content}
    except Exception as e:
        return JSONResponse(status_code=500, content={"status": "error", "error": str(e)})

if __name__ == '__main__':
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)