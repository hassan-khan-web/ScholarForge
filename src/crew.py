"""
ScholarForge AI Crew Module
This module serves as the main entry point for AI-powered research and analysis.
"""
import sys
import os

# Add backend to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.AI_engine import AIEngine
from backend.chat_engine import ChatEngine
from backend.council import CouncilAI

# Initialize AI components
ai_engine = AIEngine()
chat_engine = ChatEngine()
council = CouncilAI()

__all__ = ["ai_engine", "chat_engine", "council"]
