"""
AI Chat Assistant for Writing Studio Analytics.

This module provides a local LLM-powered chat interface for analyzing
Writing Studio reservation data using any GGUF model.

Main components:
- ChatHandler: Main orchestration class
- LocalLLM: LLM wrapper with GPU acceleration (supports any GGUF model)
- ModelRegistry: Discovers and manages available models
- ModelConfigManager: Persists user's model selection
- InputValidator: Pre-generation query validation
- ResponseFilter: Post-generation PII filtering
"""

from .chat_handler import ChatHandler
from .llm_engine import LocalLLM
from .model_manager import ModelRegistry, ModelConfigManager, ModelInfo, get_available_models
from .data_prep import prepare_data_context
from .safety_filters import InputValidator, ResponseFilter

# Backward compatibility alias
GemmaLLM = LocalLLM

__version__ = "2.0.0"

__all__ = [
    "ChatHandler",
    "LocalLLM",
    "GemmaLLM",  # Backward compatibility
    "ModelRegistry",
    "ModelConfigManager",
    "ModelInfo",
    "get_available_models",
    "prepare_data_context",
    "InputValidator",
    "ResponseFilter",
]
