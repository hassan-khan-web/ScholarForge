import os
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, text
from sqlalchemy.orm import sessionmaker, relationship, declarative_base

# 1. SETUP
# Get URL from environment or fallback to default (Docker service name is 'db')
SQLALCHEMY_DATABASE_URL = os.environ.get(
    "DATABASE_URL", 
    "postgresql://scholar:forgepass@db:5432/scholarforge"
)

# Postgres engine does not need "check_same_thread"
engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 2. MODELS (Unchanged)

class ReportDB(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String, index=True)
    content = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

class ProjectFolder(Base):
    __tablename__ = "project_folders"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    sessions = relationship("ChatSession", back_populates="folder", cascade="all, delete-orphan")

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id = Column(Integer, primary_key=True, index=True)
    folder_id = Column(Integer, ForeignKey("project_folders.id")) 
    title = Column(String)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    
    folder = relationship("ProjectFolder", back_populates="sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"))
    role = Column(String)
    content = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    session = relationship("ChatSession", back_populates="messages")

class Hook(Base):
    __tablename__ = "hooks"
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

# 3. INIT
def init_db():
    try:
        Base.metadata.create_all(bind=engine)
        print(">>> Database initialized (PostgreSQL).")
    except Exception as e:
        print(f">>> Database Init Error: {e}")

# 4. CRUD OPERATIONS (Unchanged)

def create_folder(name: str):
    db = SessionLocal()
    try:
        existing = db.query(ProjectFolder).filter(ProjectFolder.name == name).first()
        if existing: raise Exception("Folder already exists")
        folder = ProjectFolder(name=name)
        db.add(folder)
        db.commit()
        db.refresh(folder)
        return folder
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def get_folders_with_sessions():
    db = SessionLocal()
    try:
        folders = db.query(ProjectFolder).order_by(ProjectFolder.created_at.desc()).all()
        result = []
        for f in folders:
            sessions = sorted(f.sessions, key=lambda s: s.created_at, reverse=True)
            result.append({
                "id": f.id,
                "name": f.name,
                "sessions": [{"id": s.id, "title": s.title} for s in sessions]
            })
        return result
    finally:
        db.close()

def create_chat_session(folder_id: int, title: str):
    db = SessionLocal()
    try:
        session = ChatSession(folder_id=folder_id, title=title)
        db.add(session)
        db.commit()
        db.refresh(session)
        return session
    finally:
        db.close()

def get_session_messages(session_id: int):
    db = SessionLocal()
    try:
        return db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc()).all()
    finally:
        db.close()

def save_chat_message(session_id: int, role: str, content: str):
    db = SessionLocal()
    try:
        msg = ChatMessage(session_id=session_id, role=role, content=content)
        db.add(msg)
        db.commit()
    finally:
        db.close()

def save_report(topic: str, content: str):
    db = SessionLocal()
    try:
        new_report = ReportDB(topic=topic, content=content)
        db.add(new_report)
        db.commit()
    except Exception as e:
        print(f"DB Error saving report: {e}")
    finally:
        db.close()

def get_all_reports():
    db = SessionLocal()
    try:
        return db.query(ReportDB.id, ReportDB.topic, ReportDB.created_at).order_by(ReportDB.created_at.desc()).all()
    finally:
        db.close()

def get_report_content(report_id: int):
    db = SessionLocal()
    try:
        return db.query(ReportDB).filter(ReportDB.id == report_id).first()
    finally:
        db.close()

def delete_report(report_id: int):
    db = SessionLocal()
    try:
        report = db.query(ReportDB).filter(ReportDB.id == report_id).first()
        if report:
            db.delete(report)
            db.commit()
            return True
        return False
    finally:
        db.close()

def save_hook(content: str):
    db = SessionLocal()
    try:
        new_hook = Hook(content=content)
        db.add(new_hook)
        db.commit()
    finally:
        db.close()