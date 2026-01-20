"""
LLM Engine for Gemma 3 4B

Wraps llama-cpp-python for local inference with vision support.
"""

import os
import sys
from pathlib import Path
from typing import Optional, Dict, Any
import base64

try:
    from llama_cpp import Llama
    LLAMA_AVAILABLE = True
except ImportError:
    LLAMA_AVAILABLE = False


class GemmaLLM:
    """Gemma 3 4B Instruct LLM wrapper with multimodal support."""
    
    def __init__(
        self,
        model_path: str,
        n_ctx: int = 128000,
        n_threads: Optional[int] = None,
        n_gpu_layers: int = -1,
        verbose: bool = False
    ):
        """Initialize Gemma 3 4B LLM."""
        if not LLAMA_AVAILABLE:
            raise RuntimeError(
                "llama-cpp-python not installed. "
                "Install with: pip install llama-cpp-python --upgrade --force-reinstall --no-cache-dir"
            )
        
        self.model_path = Path(model_path)
        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Model file not found: {model_path}\n"
                f"Run: python src/ai_chat/setup_model.py"
            )
        
        self.n_ctx = n_ctx
        self.n_threads = n_threads if n_threads else os.cpu_count() or 4
        self.n_gpu_layers = n_gpu_layers
        self.verbose = verbose
        self._model = None
        self._detect_gpu_acceleration()
    
    def _detect_gpu_acceleration(self) -> Dict[str, bool]:
        """Detect available GPU acceleration (Metal/CUDA)."""
        self.gpu_info = {
            'metal': False,
            'cuda': False,
            'acceleration': 'CPU'
        }
        
        if sys.platform == 'darwin':
            try:
                import torch
                if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                    self.gpu_info['metal'] = True
                    self.gpu_info['acceleration'] = 'Metal (MPS)'
            except ImportError:
                pass
        
        try:
            import torch
            if torch.cuda.is_available():
                self.gpu_info['cuda'] = True
                self.gpu_info['acceleration'] = f"CUDA ({torch.cuda.get_device_name(0)})"
        except ImportError:
            pass
        
        if self.verbose:
            print(f"GPU Acceleration: {self.gpu_info['acceleration']}")
        
        return self.gpu_info
    
    def load_model(self) -> Llama:
        """Load model into memory (cached)."""
        if self._model is not None:
            return self._model
        
        if self.verbose:
            print(f"Loading model: {self.model_path}")
            print(f"Context window: {self.n_ctx:,} tokens")
            print(f"Threads: {self.n_threads}")
            print(f"GPU layers: {self.n_gpu_layers}")
        
        gpu_layers = self.n_gpu_layers
        if gpu_layers == -1:
            if self.gpu_info['metal'] or self.gpu_info['cuda']:
                gpu_layers = 35
            else:
                gpu_layers = 0
        
        self._model = Llama(
            model_path=str(self.model_path),
            n_ctx=self.n_ctx,
            n_threads=self.n_threads,
            n_gpu_layers=gpu_layers,
            verbose=self.verbose
        )
        
        if self.verbose:
            print("Model loaded successfully!")
        
        return self._model
    
    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64 for multimodal input."""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def _prepare_multimodal_prompt(
        self,
        prompt: str,
        image_path: Optional[str] = None
    ) -> str:
        """Prepare prompt with optional image for multimodal input."""
        if image_path:
            image_b64 = self._encode_image(image_path)
            multimodal_prompt = f"""<image>
data:image/png;base64,{image_b64}
</image>

{prompt}"""
            return multimodal_prompt
        return prompt
    
    def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.3,
        top_p: float = 0.9,
        top_k: int = 40,
        repeat_penalty: float = 1.1,
        image_path: Optional[str] = None,
        stop: Optional[list] = None
    ) -> Dict[str, Any]:
        """Generate response from model."""
        model = self.load_model()
        
        if image_path:
            prompt = self._prepare_multimodal_prompt(prompt, image_path)
        
        if stop is None:
            stop = ["User:", "\n\n"]
        
        response = model(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            repeat_penalty=repeat_penalty,
            stop=stop,
            echo=False
        )
        
        generated_text = response['choices'][0]['text'].strip()
        
        return {
            'text': generated_text,
            'model_used': str(self.model_path),
            'gpu_acceleration': self.gpu_info['acceleration'],
            'tokens_generated': response.get('usage', {}).get('completion_tokens', 0),
            'prompt_tokens': response.get('usage', {}).get('prompt_tokens', 0)
        }
    
    def query_with_data(
        self,
        user_query: str,
        csv_payload: str,
        chart_path: Optional[str] = None
    ) -> str:
        """Query model with CSV data and optional chart."""
        system_prompt = """You are a Writing Center Data Analyst. Your role is to help interpret student reservation trends and patterns from writing studio data.

You have access to:
- Cleaned session data in CSV format
- Optional charts/visualizations
- Key metrics and statistics

Your guidelines:
1. Answer questions based ONLY on provided data
2. Focus on aggregated statistics, not individual records
3. Provide clear, concise insights
4. If data is insufficient for a question, say so
5. Be professional and helpful
6. Never make up data not present in context

Data Context:
"""
        
        full_prompt = f"{system_prompt}\n{csv_payload}\n\nQuestion: {user_query}"
        
        result = self.generate(
            prompt=full_prompt,
            max_tokens=512,
            temperature=0.3,
            image_path=chart_path
        )
        
        return result['text']
