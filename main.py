import os
import shutil
import urllib.parse
import tempfile
from typing import List 
from dotenv import load_dotenv
load_dotenv()
from fastapi import FastAPI, Request, Form, BackgroundTasks, HTTPException, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse, FileResponse
from starlette.middleware.sessions import SessionMiddleware
from pydantic import BaseModel
from celery.result import AsyncResult

# Import modules
from task import generate_report_task, celery_app
import AI_engine 
import chat_engine 
import report_formats
import database 

app = FastAPI(title="ScholarForge")

app.add_middleware(SessionMiddleware, secret_key=os.environ.get("APP_SECRET_KEY", "super-secret-key"))

if not os.path.exists("static"):
    os.makedirs("static")
if not os.path.exists("static/charts"):
    os.makedirs("static/charts")

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

@app.on_event("startup")
def startup():
    # 1. Secret Check
    required_secrets = ["API_KEY", "OPENROUTER_API_KEY"]
    missing = [k for k in required_secrets if not os.environ.get(k)]
    if missing:
        print(f"CRITICAL: Missing keys: {missing}")
        raise RuntimeError(f"Missing keys: {missing}")
    # 2. Database
    database.init_db()

# --- PYDANTIC MODELS ---
class ChatRequest(BaseModel):
    message: str
    session_id: int 

class CreateFolderRequest(BaseModel):
    name: str

class RenameRequest(BaseModel):
    new_name: str

class CreateSessionRequest(BaseModel):
    folder_id: int
    title: str

class HookRequest(BaseModel):
    content: str

# --- ROUTES ---

@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse("report_generator.html", {"request": request})

@app.get("/chat")
async def chat_page(request: Request):
    return templates.TemplateResponse('ai_assistant.html', {"request": request})

# --- SYSTEM ---
@app.post("/api/system/reset-db")
def reset_database():
    try:
        database.engine.dispose()
        database.Base.metadata.drop_all(bind=database.engine)
        database.init_db()
        return {"status": "success"}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# --- FOLDER/CHAT ---
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

@app.post("/chat")
async def chat(data: ChatRequest):
    msgs = database.get_session_messages(data.session_id)
    ctx = [{"role": m.role, "content": m.content} for m in msgs]
    resp = await chat_engine.get_chat_response_async(data.message, ctx)
    database.save_chat_message(data.session_id, "user", data.message)
    database.save_chat_message(data.session_id, "assistant", resp)
    return {'response': resp}

# --- REPORTS ---
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

# --- START REPORT ---
@app.post("/start-report")
async def start_report(
    query: str = Form(...),
    format_key: str = Form(...),
    format_content: str = Form(None),
    page_count: int = Form(15),
    pdf_files: List[UploadFile] = File(None) 
):
    try:
        user_fmt = format_key if format_key in report_formats.FORMAT_TEMPLATES else "literature_review"
        if format_key == "custom":
            if not format_content: return JSONResponse({'error': 'Custom format needed'}, status_code=400)
            user_fmt = "custom" 

        # Handle Multiple Files
        pdf_data_list = []
        if pdf_files:
            for file in pdf_files:
                if file.filename: # check if file was actually uploaded
                    content = await file.read()
                    pdf_data_list.append(content)
        
        # Pass list of bytes to task
        task = generate_report_task.delay(query, user_fmt, page_count, pdf_data_list)
        return {"task_id": task.id}
    except Exception as e:
        return JSONResponse({'error': f'Failed: {str(e)}'}, status_code=500)

@app.get("/report-status/{task_id}")
async def report_status(task_id: str):
    task = AsyncResult(task_id, app=celery_app)
    if task.state == 'SUCCESS':
        res = task.result
        if isinstance(res, dict) and res.get('status') == 'FAILURE': return {'status': 'FAILURE', 'error': res.get('error')}
        return {'status': 'SUCCESS', 'report_content': res.get('report_content'), 'chart_path': res.get('chart_path')}
    elif task.state == 'FAILURE': return {'status': 'FAILURE', 'error': str(task.info)}
    return {'status': task.state, 'message': task.info.get('message', 'Running...') if isinstance(task.info, dict) else 'Running...'}

# --- DOWNLOAD ---
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

if __name__ == '__main__':
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=5000, reload=True)