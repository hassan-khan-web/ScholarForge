"""
ScholarForge Configuration Module for CrewAI
"""
import os
from dotenv import load_dotenv

load_dotenv()

# CrewAI LLM Configuration
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# External APIs
SERPAPI_API_KEY = os.getenv("SERPAPI_API_KEY")

# Database Settings
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./scholarforge.db")

# Redis Settings
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Application Settings
APP_NAME = "ScholarForge"
APP_VERSION = "0.1.0"
DEBUG = os.getenv("DEBUG", "False") == "True"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
