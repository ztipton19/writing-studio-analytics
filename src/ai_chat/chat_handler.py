"""
Main Chat Handler

Orchestrates all components for AI chat functionality.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path

from .llm_engine import GemmaLLM
from .data_prep import prepare_chat_context
from .prompt_templates import (
    build_scheduled_prompt,
    build_walkin_prompt
)
from .safety_filters import InputValidator, ResponseFilter


class ChatHandler:
    """
    Main chat orchestration.
    
    Coordinates:
    - Input validation
    - Context building
    - Prompt construction
    - LLM generation
    - Response filtering
    - Conversation history
    """
    
    def __init__(
        self,
        model_path: str,
        verbose: bool = False
    ):
        """
        Initialize chat handler.
        
        Args:
            model_path: Path to Gemma 3 4B GGUF model
            verbose: Enable verbose logging
        """
        # Initialize LLM
        self.llm = GemmaLLM(
            model_path=model_path,
            verbose=verbose
        )
        
        # Initialize safety layers
        self.input_validator = InputValidator()
        self.response_filter = ResponseFilter()
        
        # Conversation history
        self.conversation_history: List[Dict[str, str]] = []
        
        # Track model info
        self.model_info = {
            'model_path': model_path,
            'gpu_acceleration': self.llm.gpu_info['acceleration']
        }
    
    def handle_query(
        self,
        user_query: str,
        session_state: Dict[str, Any],
        chart_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Handle user query.
        
        Args:
            user_query: User's question
            session_state: Streamlit session state with DataFrame
            chart_path: Optional path to chart image
            
        Returns:
            Dictionary with response and metadata
        """
        # Step 1: Validate input (before LLM generation)
        is_valid, reason = self.input_validator.is_on_topic(user_query)
        
        if not is_valid:
            # Return rejection immediately (no LLM call)
            rejection_msg = self.input_validator.get_rejection_message(reason)
            return {
                'response': rejection_msg,
                'rejected': True,
                'reason': reason,
                'llm_called': False,
                'model_info': self.model_info
            }
        
        # Step 2: Build context from session state
        df_clean = session_state.get('df_clean')
        if df_clean is None:
            return {
                'response': "No data available. Please upload a CSV file first.",
                'rejected': True,
                'reason': 'no_data',
                'llm_called': False,
                'model_info': self.model_info
            }
        
        context = prepare_chat_context(df_clean, session_state)
        
        # Step 3: Build system prompt based on session type
        if context['session_type'] == 'scheduled':
            system_prompt = build_scheduled_prompt(
                total_sessions=context['total_records'],
                date_range=context['date_range'],
                available_fields=context['metrics']['columns'],
                key_metrics=context['metrics_str']
            )
        else:  # walkin
            system_prompt = build_walkin_prompt(
                total_sessions=context['total_records'],
                date_range=context['date_range'],
                available_fields=context['metrics']['columns'],
                key_metrics=context['metrics_str']
            )
        
        # Step 4: Build full prompt with conversation history
        full_prompt = self._build_prompt(
            system_prompt=system_prompt,
            user_query=user_query,
            csv_payload=context['csv_payload']
        )
        
        # Step 5: Generate response from LLM
        result = self.llm.query_with_data(
            user_query=full_prompt,
            csv_payload="",  # Already in full_prompt
            chart_path=chart_path
        )
        
        # Step 6: Filter response for PII
        safe_response = self.response_filter.filter_response(result)
        
        # Step 7: Update conversation history
        self.conversation_history.append({
            'user': user_query,
            'assistant': safe_response
        })
        
        # Keep only last 10 turns to manage context
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]
        
        # Return response with metadata
        return {
            'response': safe_response,
            'rejected': False,
            'reason': 'valid',
            'llm_called': True,
            'context_type': context['session_type'],
            'total_records': context['total_records'],
            'model_info': self.model_info
        }
    
    def _build_prompt(
        self,
        system_prompt: str,
        user_query: str,
        csv_payload: str
    ) -> str:
        """
        Build full prompt with system prompt, data, and conversation history.
        
        Args:
            system_prompt: System instructions
            user_query: Current user question
            csv_payload: Formatted CSV data
            
        Returns:
            Complete prompt string
        """
        # Start with system prompt and data
        prompt = f"{system_prompt}\n\n"
        prompt += f"{csv_payload}\n\n"
        
        # Add conversation history (last 3 turns)
        if self.conversation_history:
            prompt += "CONVERSATION HISTORY:\n"
            for turn in self.conversation_history[-3:]:
                prompt += f"User: {turn['user']}\n"
                prompt += f"Assistant: {turn['assistant']}\n\n"
        
        # Add current query
        prompt += f"Question: {user_query}\n"
        prompt += "Assistant:"
        
        return prompt
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get conversation history."""
        return self.conversation_history.copy()
    
    def check_system_requirements(self) -> Dict[str, Any]:
        """
        Check system requirements (RAM, GPU).
        
        Returns:
            Dictionary with system info
        """
        import psutil
        
        # Get RAM info
        ram_gb = psutil.virtual_memory().total / (1024**3)
        
        # Get GPU info
        gpu_acceleration = self.llm.gpu_info['acceleration']
        has_gpu = gpu_acceleration != 'CPU'
        
        # Get CPU info
        cpu_count = self.llm.n_threads
        
        return {
            'ram_gb': round(ram_gb, 1),
            'has_gpu': has_gpu,
            'gpu_acceleration': gpu_acceleration,
            'cpu_threads': cpu_count,
            'ram_sufficient': ram_gb >= 8.0,
            'model_loaded': self.llm._model is not None
        }
