"""
ScholarForge Configuration Module
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Application Settings
APP_NAME = "ScholarForge"
APP_VERSION = "0.1.0"
DEBUG = os.getenv("DEBUG", "False") == "True"
SECRET_KEY = os.getenv("APP_SECRET_KEY", "super-secret-key")

# API Settings
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", 8000))

# Database Settings
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./scholarforge.db")

# Redis Settings
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# AI/LLM Settings
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# External APIs
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

# File Upload Settings
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploaded_files")
MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", 50 * 1024 * 1024))  # 50MB

# Celery Settings
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
