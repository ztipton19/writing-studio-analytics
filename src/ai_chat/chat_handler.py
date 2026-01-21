"""
Main chat handler for AI Chat Assistant.

Orchestrates:
- Data preparation
- Input validation
- Prompt construction
- LLM generation
- Code generation & execution (for dynamic queries)
- Response filtering
- Conversation history
"""

from typing import Dict, Any, Tuple, Optional
from .llm_engine import GemmaLLM
from .data_prep import prepare_data_context, prepare_chart_context
from .prompt_templates import build_system_prompt, build_full_prompt, format_query_with_data
from .safety_filters import InputValidator, ResponseFilter
from .code_executor import CodeExecutor


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
    
    def __init__(self, model_path: str, verbose: bool = False, enable_code_execution: bool = False):
        """
        Initialize chat handler.
        
        Args:
            model_path: Path to Gemma 3 4B model file
            verbose: Enable verbose logging
            enable_code_execution: Enable LLM code generation for dynamic queries
        """
        self.llm = GemmaLLM(model_path, verbose=verbose)
        self.input_validator = InputValidator()
        self.response_filter = ResponseFilter()
        self.conversation_history = []
        self.verbose = verbose
        self.enable_code_execution = enable_code_execution
        self.code_executor: Optional[CodeExecutor] = None
        
        if verbose:
            print("🤖 ChatHandler initialized")
            if enable_code_execution:
                print("🔧 Code execution enabled for dynamic queries")
    
    def check_system(self) -> Dict[str, Any]:
        """
        Check system requirements.
        
        Returns:
            Dict with system information
        """
        return self.llm.check_system_requirements()
    
    def set_data_for_code_execution(self, df_clean):
        """
        Initialize code executor with DataFrame.
        
        Call this after loading data if you want to enable dynamic queries.
        
        Args:
            df_clean: Cleaned DataFrame
        """
        if self.enable_code_execution:
            self.code_executor = CodeExecutor(df_clean, verbose=self.verbose)
            if self.verbose:
                print(f"📊 Code executor ready for {len(df_clean)} records")
    
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
            # Log blocked query for review
            self.input_validator.log_blocked_query(user_query, reason)
            
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
        
        # 3. Format user query (no CSV - use only schema + pre-computed metrics)
        # CSV removed for performance - LLM now uses pre-computed metrics in system prompt
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
        
        # 6. Check if we should use code execution for this query
        use_code_exec = self.enable_code_execution and self.code_executor and self._should_use_code_execution(user_query)
        
        raw_response = ""
        
        try:
            if use_code_exec:
                # Use code generation workflow
                raw_response = self._handle_with_code_execution(
                    user_query,
                    df_clean,
                    metrics,
                    data_context
                )
            else:
                # Standard LLM generation
                raw_response = self.llm.generate(
                    full_prompt,
                    max_tokens=1024,
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
    
    def _should_use_code_execution(self, user_query: str) -> bool:
        """
        Determine if a query requires dynamic code execution.
        
        Simple heuristic: check for keywords that suggest computation.
        
        Args:
            user_query: The user's question
            
        Returns:
            bool: True if code execution should be used
        """
        # Keywords that might require dynamic computation
        computation_keywords = [
            'count', 'how many', 'number of', 'average', 'mean', 'median',
            'percentage', 'percent', 'greater than', 'less than', 'more than',
            'between', 'maximum', 'minimum', 'highest', 'lowest', 'most', 'least',
            'distribution', 'breakdown', 'compare', 'difference', 'correlation'
        ]
        
        query_lower = user_query.lower()
        
        # Check if query contains computation keywords
        has_computation = any(keyword in query_lower for keyword in computation_keywords)
        
        return has_computation
    
    def _handle_with_code_execution(
        self,
        user_query: str,
        df_clean,
        metrics: Dict[str, Any],
        data_context: Dict[str, Any]
    ) -> str:
        """
        Handle query using code generation and execution.
        
        Workflow:
        1. LLM generates pandas code
        2. CodeExecutor executes it
        3. Result passed back to LLM for formatting
        
        Args:
            user_query: User's question
            df_clean: DataFrame
            metrics: Pre-computed metrics
            data_context: Data context from prepare_data_context
            
        Returns:
            str: Formatted natural language response
        """
        if self.verbose:
            print(f"🔧 Using code execution for: {user_query[:50]}...")
        
        # 1. Generate code via LLM and execute
        success, result, error = self.code_executor.safe_execute_query(
            user_query=user_query,
            llm_generate_fn=self.llm.generate,
            columns=data_context['columns'],
            metrics=data_context['key_metrics']
        )
        
        if not success:
            # Fallback to standard LLM if code execution fails
            if self.verbose:
                print(f"⚠️ Code execution failed, falling back to standard LLM: {error}")
            system_prompt = build_system_prompt(data_context, 'scheduled' if 'booking' in metrics else 'walkin')
            full_prompt = build_full_prompt(system_prompt, user_query, self.conversation_history)
            return self.llm.generate(full_prompt, max_tokens=1024, temperature=0.7, top_p=0.9)
        
        # 2. Format result using LLM
        format_prompt = f"""You are a Writing Center Data Analyst.

User asked: {user_query}

Computation result: {result}

Provide a concise, professional answer (1-3 sentences) explaining this result.
Focus on what the number means in context."""
        
        formatted_response = self.llm.generate(format_prompt, max_tokens=256, temperature=0.5)
        
        if self.verbose:
            print(f"✅ Code execution result: {result}")
            print(f"✅ Formatted response: {formatted_response[:50]}...")
        
        return formatted_response
    
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
            max_tokens=1024,
            temperature=0.7
        )
        
        return response
