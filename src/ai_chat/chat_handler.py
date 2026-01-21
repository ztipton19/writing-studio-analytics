"""
Main chat handler for AI Chat Assistant.

Orchestrates:
- Data preparation
- Input validation
- Prompt construction
- LLM generation
- Response filtering
- Conversation history
"""

from typing import Dict, Any, Tuple
from .llm_engine import GemmaLLM
from .data_prep import prepare_data_context, prepare_chart_context
from .prompt_templates import build_system_prompt, build_full_prompt, format_query_with_data
from .safety_filters import InputValidator, ResponseFilter


class ChatHandler:
    """
    Main chat orchestration for AI Chat Assistant.
    
    Coordinates:
    - Input validation (pre-generation)
    - Context building
    - Prompt construction
    - LLM generation
    - Response filtering (post-generation)
    - Conversation history management
    """
    
    def __init__(self, model_path: str, verbose: bool = False):
        """
        Initialize chat handler.
        
        Args:
            model_path: Path to Gemma 3 4B model file
            verbose: Enable verbose logging
        """
        self.llm = GemmaLLM(model_path, verbose=verbose)
        self.input_validator = InputValidator()
        self.response_filter = ResponseFilter()
        self.conversation_history = []
        self.verbose = verbose
        
        if verbose:
            print("🤖 ChatHandler initialized")
    
    def check_system(self) -> Dict[str, Any]:
        """
        Check system requirements.
        
        Returns:
            Dict with system information
        """
        return self.llm.check_system_requirements()
    
    def handle_query(
        self,
        user_query: str,
        df_clean,
        metrics: Dict[str, Any],
        data_mode: str = 'scheduled',
        chart_path: str = None,
        include_csv: bool = True
    ) -> Tuple[str, Dict[str, Any]]:
        """
        Handle user query with full pipeline.
        
        Args:
            user_query: User's question
            df_clean: Cleaned DataFrame
            metrics: Metrics dictionary
            data_mode: 'scheduled' or 'walkin'
            chart_path: Optional path to chart image
            include_csv: Whether to include CSV in prompt
            
        Returns:
            (response: str, metadata: dict)
        """
        # 0. VALIDATE INPUT FIRST (pre-generation)
        is_valid, reason = self.input_validator.is_on_topic(user_query)
        
        if not is_valid:
            # Return rejection message immediately (no LLM call)
            rejection_msg = self.input_validator.get_rejection_message(reason)
            if self.verbose:
                print(f"❌ Query rejected: {reason}")
            
            return rejection_msg, {
                'rejected': True,
                'reason': reason,
                'llm_called': False
            }
        
        if self.verbose:
            print(f"✅ Query accepted: {user_query[:50]}...")
        
        # 1. Build data context
        data_context = prepare_data_context(df_clean, metrics, data_mode)
        
        # 2. Build system prompt
        system_prompt = build_system_prompt(data_context, data_mode)
        
        # 3. Format user query
        if include_csv:
            user_query_formatted = format_query_with_data(user_query, data_context['csv_summary'])
        else:
            user_query_formatted = user_query
        
        # 4. Prepare chart context (multimodal)
        chart_context = prepare_chart_context(chart_path)
        
        # 5. Build full prompt
        full_prompt = build_full_prompt(
            system_prompt,
            user_query_formatted,
            self.conversation_history
        )
        
        # Add chart note if available
        if chart_context:
            full_prompt += f"\n\n{chart_context['note']}\n"
        
        # 6. Generate response
        try:
            raw_response = self.llm.generate(
                full_prompt,
                max_tokens=512,
                temperature=0.7,
                top_p=0.9
            )
        except Exception as e:
            error_msg = f"I encountered an error generating a response: {str(e)}"
            if self.verbose:
                print(f"❌ Generation error: {str(e)}")
            
            return error_msg, {
                'error': True,
                'error_type': 'generation_error',
                'rejected': False,
                'llm_called': True
            }
        
        # 7. Filter response (PII check)
        safe_response = self.response_filter.filter_response(raw_response)
        
        # 8. Update conversation history
        self.conversation_history.append({
            'user': user_query,
            'assistant': safe_response
        })
        
        # Keep only last 5 turns to manage context
        if len(self.conversation_history) > 5:
            self.conversation_history = self.conversation_history[-5:]
        
        # Return metadata
        metadata = {
            'rejected': False,
            'llm_called': True,
            'pii_filtered': raw_response != safe_response,
            'data_mode': data_mode,
            'chart_used': chart_path is not None
        }
        
        if self.verbose:
            if metadata['pii_filtered']:
                print("⚠️ Response filtered for PII")
            print(f"✅ Response generated: {safe_response[:50]}...")
        
        return safe_response, metadata
    
    def clear_history(self):
        """Clear conversation history."""
        self.conversation_history = []
        if self.verbose:
            print("🧹 Conversation history cleared")
    
    def get_history(self) -> list:
        """Get conversation history."""
        return self.conversation_history.copy()
    
    def query_with_data(
        self,
        user_query: str,
        csv_payload: str,
        chart_path: str = None
    ) -> str:
        """
        Query with direct data payload (simplified interface).
        
        This is the method specified in the task requirements.
        It provides a simpler interface for direct CSV/JSON data queries.
        
        Args:
            user_query: User's question
            csv_payload: CSV-formatted data string
            chart_path: Optional path to chart image
            
        Returns:
            str: Generated response
        """
        # Build simple prompt
        prompt = f"""You are a Writing Center Data Analyst.

User Query: {user_query}

Data:
```
{csv_payload}
```

Analyze the data above and answer the user's question. Focus on:
- Patterns and trends
- Aggregated statistics (averages, totals, percentages)
- Key insights

STRICT RULES:
1. NEVER reveal individual records
2. NEVER discuss specific names or emails
3. ONLY discuss aggregated data
4. If asked about individuals, say you can only discuss aggregates

Provide a concise, professional response."""

        # Add chart note if available
        if chart_path:
            prompt += "\n\nA chart image is also available for visual analysis."

        # Generate response
        response = self.llm.generate(
            prompt,
            max_tokens=512,
            temperature=0.7
        )
        
        return response
