"""
GemmaLLM class - Wrapper for Gemma 3 4B using llama-cpp-python.
"""

import os
import psutil
from typing import Optional, Dict, Any, TYPE_CHECKING
from pathlib import Path

try:
    from llama_cpp import Llama
    LLAMA_AVAILABLE = True
except ImportError:
    LLAMA_AVAILABLE = False

# For type hints
if TYPE_CHECKING:
    from llama_cpp import Llama


class GemmaLLM:
    """Local LLM engine using Gemma 3 4B via llama.cpp."""
    
    def __init__(self, model_path: str, n_ctx: int = 4096,
                 n_threads: int = None, n_gpu_layers: int = -1, 
                 verbose: bool = False):
        if not LLAMA_AVAILABLE:
            raise ImportError("llama-cpp-python not installed")
        
        self.model_path = model_path
        self.n_ctx = n_ctx
        self.n_threads = n_threads or self._detect_optimal_threads()
        self.n_gpu_layers = n_gpu_layers
        self.verbose = verbose
        self._model: Optional[Llama] = None
        
        if verbose:
            print(f"🤖 GemmaLLM initialized: {Path(model_path).name}")
    
    @staticmethod
    def _detect_optimal_threads() -> int:
        return min(os.cpu_count() or 4, 8)
    
    def check_system_requirements(self) -> Dict[str, Any]:
        ram_info = psutil.virtual_memory()
        ram_gb = ram_info.total / (1024**3)
        ram_available_gb = ram_info.available / (1024**3)
        ram_sufficient = ram_available_gb >= 8.0
        cpu_threads = os.cpu_count() or 4
        gpu_available = False
        gpu_acceleration = "None (CPU only)"
        
        try:
            import torch
            if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                gpu_available = True
                gpu_acceleration = "Metal (MPS)"
        except ImportError:
            pass
        
        try:
            import torch
            if torch.cuda.is_available():
                gpu_available = True
                gpu_acceleration = "CUDA"
        except ImportError:
            pass
        
        return {
            'ram_gb': round(ram_gb, 1),
            'ram_available_gb': round(ram_available_gb, 1),
            'ram_sufficient': ram_sufficient,
            'cpu_threads': cpu_threads,
            'gpu_available': gpu_available,
            'gpu_acceleration': gpu_acceleration
        }
    
    def load_model(self) -> Llama:
        if self._model is None:
            if self.verbose:
                print("⏳ Loading model...")
            
            sys_info = self.check_system_requirements()
            if not sys_info['gpu_available']:
                if self.n_gpu_layers != 0:
                    if self.verbose:
                        print("⚠️ No GPU detected, CPU-only mode")
                    self.n_gpu_layers = 0
            
            self._model = Llama(
                model_path=self.model_path,
                n_ctx=self.n_ctx,
                n_threads=self.n_threads,
                n_gpu_layers=self.n_gpu_layers,
                verbose=self.verbose
            )
            
            if self.verbose:
                print("✅ Model loaded!")
        
        return self._model
    
    def generate_chat(self, messages: list, max_tokens: int = 1024,
                   temperature: float = 0.7, top_p: float = 0.9,
                   top_k: int = 40, stop: Optional[list] = None) -> str:
        """
        Generate response using chat completion API.
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-1.0)
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
            stop: Stop tokens
            
        Returns:
            Generated response text
        """
        model = self.load_model()
        
        if stop is None:
            # Changed from "\n\n" to prevent premature response cutoff
            # Using more specific end-of-sequence markers
            stop = ["<end_of_turn>model\n", "```", "END_OF_RESPONSE"]
        
        response = model.create_chat_completion(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            stop=stop
        )
        
        return response['choices'][0]['message']['content'].strip()
    
    def generate(self, prompt: str, max_tokens: int = 1024,
                temperature: float = 0.7, top_p: float = 0.9,
                top_k: int = 40, stop: Optional[list] = None,
                echo: bool = False) -> str:
        """
        Generate response from text prompt (wrapper for backwards compatibility).
        
        This method converts a text prompt to messages format and uses chat completion.
        
        Args:
            prompt: Full text prompt (including system instructions)
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-1.0)
            top_p: Nucleus sampling parameter
            top_k: Top-k sampling parameter
            stop: Stop tokens
            echo: Whether to echo prompt (ignored in chat completion mode)
            
        Returns:
            Generated response text
        """
        # Convert prompt to messages format
        # For Gemma 3, we use user role for everything
        messages = [{"role": "user", "content": prompt}]
        
        return self.generate_chat(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=top_k,
            stop=stop
        )
