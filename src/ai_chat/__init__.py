"""
AI Chat Assistant for Writing Studio Analytics.

This module provides a local LLM-powered chat interface for analyzing
Writing Studio reservation data using Gemma 3 4B.

Main components:
- ChatHandler: Main orchestration class
- GemmaLLM: LLM wrapper with GPU acceleration
- InputValidator: Pre-generation query validation
- ResponseFilter: Post-generation PII filtering
"""

from .chat_handler import ChatHandler
from .llm_engine import GemmaLLM
from .data_prep import prepare_data_context
from .safety_filters import InputValidator, ResponseFilter

__version__ = "1.0.0"

__all__ = [
    "ChatHandler",
    "GemmaLLM",
    "prepare_data_context",
    "InputValidator",
    "ResponseFilter",
]
