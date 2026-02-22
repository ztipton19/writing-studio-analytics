"""
Model Manager for AI Chat Assistant.

Handles:
- Model discovery (scan models/ folder for .gguf files)
- Model registry (map display names to file paths)
- Configuration persistence (save/load user's model preference)
- Model metadata extraction
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import re


@dataclass
class ModelInfo:
    """Information about an available model."""
    name: str           # Display name (e.g., "Gemma 3 4B (Q4_0)")
    filename: str       # Filename (e.g., "gemma-3-4b-it-q4_0.gguf")
    path: str           # Full path to model file
    size_bytes: int     # File size in bytes
    size_gb: float      # File size in GB
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ModelInfo':
        return cls(**data)


class ModelRegistry:
    """
    Registry for available GGUF models.
    
    Discovers models in the models/ folder and provides
    a mapping between display names and file paths.
    """
    
    def __init__(self, models_dir: str = "models"):
        """
        Initialize model registry.
        
        Args:
            models_dir: Directory containing model files
        """
        self.models_dir = Path(models_dir)
        self._models: Dict[str, ModelInfo] = {}
        self._scan()
    
    def _scan(self) -> None:
        """Scan models directory for .gguf files."""
        self._models.clear()
        
        if not self.models_dir.exists():
            self.models_dir.mkdir(parents=True, exist_ok=True)
            return
        
        # Find all .gguf files
        for gguf_file in self.models_dir.glob("*.gguf"):
            model_info = self._create_model_info(gguf_file)
            self._models[model_info.name] = model_info
    
    def _create_model_info(self, file_path: Path) -> ModelInfo:
        """
        Create ModelInfo from a GGUF file path.
        
        Args:
            file_path: Path to the .gguf file
            
        Returns:
            ModelInfo instance
        """
        filename = file_path.name
        size_bytes = file_path.stat().st_size
        size_gb = round(size_bytes / (1024 ** 3), 2)
        
        # Generate display name from filename
        # Examples:
        #   "gemma-3-4b-it-q4_0.gguf" -> "Gemma 3 4B (Q4_0)"
        #   "Phi-3-mini-4k-instruct-q4.gguf" -> "Phi 3 Mini 4K (Q4)"
        #   "llama-2-7b-chat.Q4_K_M.gguf" -> "Llama 2 7B Chat (Q4_K_M)"
        display_name = self._generate_display_name(filename)
        
        return ModelInfo(
            name=display_name,
            filename=filename,
            path=str(file_path.absolute()),
            size_bytes=size_bytes,
            size_gb=size_gb
        )
    
    def _generate_display_name(self, filename: str) -> str:
        """
        Generate a human-readable display name from filename.
        
        Args:
            filename: The model filename
            
        Returns:
            Human-readable display name
        """
        # Remove .gguf extension
        name = filename.replace('.gguf', '').replace('.GGUF', '')
        
        # Extract quantization info (common patterns)
        quant_patterns = [
            r'[.-]?(q[0-9]_[a-z0-9]+)',      # q4_0, q4_k_m, q5_k_m, q8_0
            r'[.-]?(q[0-9]+)',                # q4, q5, q8
            r'[.-]?(Q[0-9]_[A-Z0-9]+)',       # Q4_0, Q4_K_M
            r'[.-]?(Q[0-9]+)',                # Q4, Q5
        ]
        
        quantization = None
        for pattern in quant_patterns:
            match = re.search(pattern, name, re.IGNORECASE)
            if match:
                quantization = match.group(1).upper()
                name = re.sub(pattern, '', name, flags=re.IGNORECASE)
                break
        
        # Clean up the name
        name = name.replace('_', ' ').replace('-', ' ').replace('.', ' ')
        name = re.sub(r'\s+', ' ', name).strip()
        
        # Title case for most words, but handle special cases
        words = name.split()
        formatted_words = []
        for word in words:
            # Keep 'it', 'chat', 'instruct' lowercase if in middle
            if word.lower() in ['it', 'chat'] and formatted_words:
                formatted_words.append(word.lower())
            else:
                formatted_words.append(word.title())
        
        display_name = ' '.join(formatted_words)
        
        # Add quantization suffix
        if quantization:
            display_name += f" ({quantization})"
        
        return display_name
    
    def get_available_models(self) -> List[ModelInfo]:
        """
        Get list of all available models.
        
        Returns:
            List of ModelInfo instances
        """
        return list(self._models.values())
    
    def get_model_by_name(self, name: str) -> Optional[ModelInfo]:
        """
        Get model by display name.
        
        Args:
            name: Display name of the model
            
        Returns:
            ModelInfo if found, None otherwise
        """
        return self._models.get(name)
    
    def get_model_by_filename(self, filename: str) -> Optional[ModelInfo]:
        """
        Get model by filename.
        
        Args:
            filename: Filename of the model
            
        Returns:
            ModelInfo if found, None otherwise
        """
        for model in self._models.values():
            if model.filename == filename:
                return model
        return None
    
    def get_model_by_path(self, path: str) -> Optional[ModelInfo]:
        """
        Get model by full path.
        
        Args:
            path: Full path to the model file
            
        Returns:
            ModelInfo if found, None otherwise
        """
        for model in self._models.values():
            if model.path == path or Path(model.path) == Path(path):
                return model
        return None
    
    def refresh(self) -> None:
        """Re-scan models directory for changes."""
        self._scan()
    
    def has_models(self) -> bool:
        """Check if any models are available."""
        return len(self._models) > 0
    
    def get_default_model(self) -> Optional[ModelInfo]:
        """
        Get the default model (first available, preferring smaller models).
        
        Returns:
            ModelInfo if any models available, None otherwise
        """
        if not self.has_models():
            return None
        
        # Prefer smaller models (likely Q4 quantization)
        models = self.get_available_models()
        
        # Sort by size (smaller first)
        models_sorted = sorted(models, key=lambda m: m.size_bytes)
        
        return models_sorted[0]


class ModelConfigManager:
    """
    Manages model selection configuration persistence.
    
    Saves the user's selected model to a config file
    so it persists across application restarts.
    """
    
    DEFAULT_CONFIG_FILENAME = "model_config.json"
    
    def __init__(self, config_dir: str = None):
        """
        Initialize config manager.
        
        Args:
            config_dir: Directory for config file (defaults to app root)
        """
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            # Default to the project root (parent of src/)
            self.config_dir = Path(__file__).parent.parent.parent
        
        self.config_path = self.config_dir / self.DEFAULT_CONFIG_FILENAME
    
    def load_config(self) -> Dict[str, Any]:
        """
        Load model configuration from file.
        
        Returns:
            Configuration dict (empty if no config exists)
        """
        if not self.config_path.exists():
            return {}
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return {}
    
    def save_config(self, config: Dict[str, Any]) -> bool:
        """
        Save model configuration to file.
        
        Args:
            config: Configuration dict to save
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            return True
        except IOError:
            return False
    
    def get_selected_model_path(self) -> Optional[str]:
        """
        Get the path to the user's selected model.
        
        Returns:
            Model path if configured, None otherwise
        """
        config = self.load_config()
        return config.get('selected_model_path')
    
    def get_selected_model_filename(self) -> Optional[str]:
        """
        Get the filename of the user's selected model.
        
        Returns:
            Model filename if configured, None otherwise
        """
        config = self.load_config()
        return config.get('selected_model_filename')
    
    def save_selected_model(self, model: ModelInfo) -> bool:
        """
        Save the selected model to configuration.
        
        Args:
            model: ModelInfo of the selected model
            
        Returns:
            True if saved successfully, False otherwise
        """
        config = {
            'selected_model_name': model.name,
            'selected_model_filename': model.filename,
            'selected_model_path': model.path,
            'selected_model_size_gb': model.size_gb
        }
        return self.save_config(config)
    
    def clear_selected_model(self) -> bool:
        """
        Clear the saved model selection.
        
        Returns:
            True if cleared successfully, False otherwise
        """
        return self.save_config({})


# Convenience functions for backward compatibility

def get_available_models(models_dir: str = "models") -> List[ModelInfo]:
    """
    Get list of available models.
    
    Args:
        models_dir: Directory containing model files
        
    Returns:
        List of ModelInfo instances
    """
    registry = ModelRegistry(models_dir)
    return registry.get_available_models()


def get_model_path(models_dir: str = "models", prefer_saved: bool = True) -> Optional[str]:
    """
    Get the path to the model to use.
    
    Priority:
    1. User's saved selection (if prefer_saved=True)
    2. Default model (first available)
    
    Args:
        models_dir: Directory containing model files
        prefer_saved: Whether to check for saved selection first
        
    Returns:
        Model path if any model available, None otherwise
    """
    registry = ModelRegistry(models_dir)
    
    if prefer_saved:
        config_manager = ModelConfigManager()
        saved_path = config_manager.get_selected_model_path()
        
        if saved_path:
            # Verify the saved model still exists
            model = registry.get_model_by_path(saved_path)
            if model:
                return model.path
    
    # Fall back to default model
    default_model = registry.get_default_model()
    if default_model:
        return default_model.path
    
    return None


def scan_models(models_dir: str = "models") -> List[Dict[str, Any]]:
    """
    Scan models directory and return list of model info dicts.
    
    Args:
        models_dir: Directory containing model files
        
    Returns:
        List of model info dictionaries
    """
    registry = ModelRegistry(models_dir)
    return [model.to_dict() for model in registry.get_available_models()]