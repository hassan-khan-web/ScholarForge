import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship

# 1. SETUP
DB_FOLDER = "/app/data"
if not os.path.exists(DB_FOLDER):
    os.makedirs(DB_FOLDER, exist_ok=True)

SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_FOLDER}/scholarforge.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 2. MODELS (Tables)

class ReportDB(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, index=True)
    topic = Column(String, index=True)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    messages = relationship("ChatMessage", back_populates="session")

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"))
    role = Column(String)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    session = relationship("ChatSession", back_populates="messages")

class Hook(Base):
    __tablename__ = "hooks"
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

# 3. INIT FUNCTION
def init_db():
    Base.metadata.create_all(bind=engine)

# 4. HELPER FUNCTIONS (CRUD)

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
    """Fetches list of reports (metadata only) for the history panel."""
    db = SessionLocal()
    try:
        # We only need ID, Topic and Date for the list
        return db.query(ReportDB.id, ReportDB.topic, ReportDB.created_at).order_by(ReportDB.created_at.desc()).all()
    finally:
        db.close()

def get_report_content(report_id: int):
    """Fetches the full content of a specific report."""
    db = SessionLocal()
    try:
        return db.query(ReportDB).filter(ReportDB.id == report_id).first()
    finally:
        db.close()

def save_chat_message(role: str, content: str):
    db = SessionLocal()
    try:
        session = db.query(ChatSession).filter(ChatSession.id == 1).first()
        if not session:
            session = ChatSession(title="General Chat")
            db.add(session)
            db.commit()
            db.refresh(session)
        
        msg = ChatMessage(session_id=1, role=role, content=content)
        db.add(msg)
        db.commit()
    except Exception as e:
        print(f"DB Error saving chat: {e}")
    finally:
        db.close()

def save_hook(content: str):
    db = SessionLocal()
    try:
        new_hook = Hook(content=content)
        db.add(new_hook)
        db.commit()
    except Exception as e:
        print(f"DB Error saving hook: {e}")
    finally:
        db.close()