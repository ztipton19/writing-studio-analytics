"""
Model Setup Script for Gemma 3 4B

Downloads and prepares the Gemma 3 4B Instruct GGUF model for local use.
"""

import os
import sys
from pathlib import Path
from huggingface_hub import hf_hub_download


def download_gemma_model(
    model_dir: str = "models",
    quantization: str = "Q4_K_M",
    force_download: bool = False
) -> str:
    """
    Download Gemma 3 4B Instruct GGUF model from Hugging Face.
    
    Args:
        model_dir: Directory to store the model
        quantization: Quantization level (Q4_K_M, Q5_K_M, Q8_0)
        force_download: Force re-download even if file exists
    
    Returns:
        Path to the downloaded model file
    """
    # Create models directory
    model_path = Path(model_dir)
    model_path.mkdir(parents=True, exist_ok=True)
    
    # Model configuration
    repo_id = "google/gemma-3-4b-it-GGUF"
    
    # Map quantization to filename
    filename_map = {
        "Q4_K_M": "gemma-3-4b-it-Q4_K_M.gguf",
        "Q5_K_M": "gemma-3-4b-it-Q5_K_M.gguf",
        "Q8_0": "gemma-3-4b-it-Q8_0.gguf",
        "f16": "gemma-3-4b-it-f16.gguf"
    }
    
    if quantization not in filename_map:
        print(f"Warning: Unknown quantization '{quantization}', using Q4_K_M")
        quantization = "Q4_K_M"
    
    filename = filename_map[quantization]
    local_path = model_path / filename
    
    # Check if model already exists
    if local_path.exists() and not force_download:
        print(f"✅ Model already exists: {local_path}")
        print(f"   Size: {local_path.stat().st_size / (1024**3):.2f} GB")
        return str(local_path)
    
    # Download from Hugging Face
    print(f"📥 Downloading Gemma 3 4B ({quantization}) from Hugging Face...")
    print(f"   Repository: {repo_id}")
    print(f"   File: {filename}")
    
    try:
        downloaded_path = hf_hub_download(
            repo_id=repo_id,
            filename=filename,
            cache_dir=model_dir,
            resume_download=True,
            local_dir=model_dir,
            local_dir_use_symlinks=False
        )
        
        print(f"✅ Download complete!")
        print(f"   Location: {downloaded_path}")
        print(f"   Size: {Path(downloaded_path).stat().st_size / (1024**3):.2f} GB")
        
        return str(downloaded_path)
    
    except Exception as e:
        print(f"❌ Error downloading model: {e}")
        raise


def check_system_requirements() -> dict:
    """
    Check if system meets minimum requirements for running Gemma 3 4B.
    
    Returns:
        Dictionary with system info and recommendations
    """
    import psutil
    
    total_ram = psutil.virtual_memory().total / (1024**3)  # GB
    
    # RAM requirements (conservative estimate)
    # Q4_K_M: ~3.5GB model + 2GB overhead = ~5.5GB minimum
    # Q8_0: ~7.5GB model + 2GB overhead = ~9.5GB minimum
    # Full context (128k): Additional RAM needed
    
    info = {
        'total_ram_gb': round(total_ram, 2),
        'recommended_quantization': None,
        'recommended_max_ctx': None,
        'warnings': [],
        'gpu_available': False
    }
    
    # RAM recommendations
    if total_ram < 6:
        info['recommended_quantization'] = 'Q4_K_M'
        info['recommended_max_ctx'] = 8192
        info['warnings'].append(
            f"Low RAM ({total_ram:.1f}GB). Use Q4_K_M quantization "
            f"and limit context window to 8192 tokens."
        )
    elif total_ram < 12:
        info['recommended_quantization'] = 'Q4_K_M'
        info['recommended_max_ctx'] = 32768
        info['warnings'].append(
            f"Moderate RAM ({total_ram:.1f}GB). Q4_K_M recommended "
            f"with context up to 32k tokens."
        )
    else:
        info['recommended_quantization'] = 'Q5_K_M' if total_ram < 16 else 'Q8_0'
        info['recommended_max_ctx'] = 128000
        print(f"✅ Good RAM ({total_ram:.1f}GB). Can use larger context window.")
    
    # Check for GPU support
    try:
        import torch
        if torch.cuda.is_available():
            info['gpu_available'] = True
            info['gpu_name'] = torch.cuda.get_device_name(0)
            print(f"✅ CUDA GPU detected: {info['gpu_name']}")
    except ImportError:
        pass
    
    # Check for Metal (macOS)
    if sys.platform == 'darwin':
        info['gpu_available'] = True
        info['gpu_name'] = 'Apple Metal (MPS)'
        print(f"✅ Apple Metal GPU available (macOS)")
    
    return info


def main():
    """Main entry point for model setup."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Download and setup Gemma 3 4B model for local inference"
    )
    parser.add_argument(
        '--quantization', '-q',
        choices=['Q4_K_M', 'Q5_K_M', 'Q8_0', 'f16'],
        default='Q4_K_M',
        help='Model quantization level (default: Q4_K_M)'
    )
    parser.add_argument(
        '--model-dir', '-d',
        default='models',
        help='Directory to store the model (default: models)'
    )
    parser.add_argument(
        '--force', '-f',
        action='store_true',
        help='Force re-download even if model exists'
    )
    parser.add_argument(
        '--check-only', '-c',
        action='store_true',
        help='Only check system requirements, dont download'
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("Gemma 3 4B Model Setup")
    print("=" * 60)
    print()
    
    # Check system requirements
    print("🔍 Checking system requirements...")
    info = check_system_requirements()
    print(f"   Total RAM: {info['total_ram_gb']:.1f} GB")
    if info['gpu_available']:
        print(f"   GPU: {info.get('gpu_name', 'Available')}")
    else:
        print(f"   GPU: Not detected (will use CPU)")
    print()
    
    if info['warnings']:
        print("⚠️  Warnings:")
        for warning in info['warnings']:
            print(f"   - {warning}")
        print()
    
    # Recommended settings
    if not args.quantization:
        args.quantization = info['recommended_quantization']
    
    if args.check_only:
        print("✅ System check complete.")
        print(f"   Recommended quantization: {args.quantization}")
        print(f"   Recommended max context: {info['recommended_max_ctx']:,} tokens")
        return
    
    # Download model
    try:
        model_path = download_gemma_model(
            model_dir=args.model_dir,
            quantization=args.quantization,
            force_download=args.force
        )
        
        print()
        print("=" * 60)
        print("✅ Setup complete!")
        print("=" * 60)
        print()
        print("Next steps:")
        print(f"1. Model saved to: {model_path}")
        print(f"2. Update your code to use this model path")
        print(f"3. Recommended max_ctx: {info['recommended_max_ctx']:,}")
        print()
        print("Example usage:")
        print("```python")
        print("from llama_cpp import Llama")
        print(f"llm = Llama(model_path='{model_path}', n_ctx={info['recommended_max_ctx']})")
        print("```")
        
    except Exception as e:
        print()
        print("=" * 60)
        print("❌ Setup failed!")
        print("=" * 60)
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
