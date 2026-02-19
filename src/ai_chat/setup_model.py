"""
Model Setup Script for Gemma 3 4B

Downloads and prepares the Gemma 3 4B Instruct GGUF model for local use.
"""

import sys
from pathlib import Path
from huggingface_hub import hf_hub_download


def download_gemma_model(
    model_dir: str = "models",
    quantization: str = "Q4_0",
    force_download: bool = False
) -> str:
    """
    Download Gemma 3 4B Instruct GGUF model from Hugging Face.
    
    Note: Gemma 3 GGUF models may not be available yet. This function will
    attempt to download and provide helpful error messages if unavailable.
    
    Args:
        model_dir: Directory to store the model
        quantization: Quantization level (Q4_0, Q4_K_M, Q5_K_M, Q8_0)
        force_download: Force re-download even if file exists
    
    Returns:
        Path to the downloaded model file
    """
    # Create models directory
    model_path = Path(model_dir)
    model_path.mkdir(parents=True, exist_ok=True)
    
    # Try multiple repository sources
    repo_options = [
        # Primary: Gemma 3 4B (target model, requires authentication)
        "google/gemma-3-4b-it-qat-q4_0-gguf",
        # Fallback: Phi-3-mini (works excellently)
        "microsoft/Phi-3-mini-4k-instruct-gguf",
        # Fallback: Gemma 2 2B
        "google/gemma-2-2b-it-GGUF",
    ]
    
    # Map quantization to filename
    # Gemma 3 4B
    filename_map = {
        "Q4_0": "gemma-3-4b-it-q4_0.gguf",
        "Q4_K_M": "gemma-3-4b-it-q4_0.gguf",
        "Q5_K_M": "gemma-3-4b-it-q5_0.gguf",
        "Q8_0": "gemma-3-4b-it-q8_0.gguf",
        "f16": "gemma-3-4b-it-f16.gguf"
    }
    
    if quantization not in filename_map:
        print(f"Warning: Unknown quantization '{quantization}', using Q4_0")
        quantization = "Q4_0"
    
    filename = filename_map[quantization]
    local_path = model_path / filename
    
    # Check if model already exists
    if local_path.exists() and not force_download:
        print(f" Model already exists: {local_path}")
        print(f"   Size: {local_path.stat().st_size / (1024**3):.2f} GB")
        return str(local_path)
    
    # Try downloading from each repository
    print(f" Attempting to download Gemma 3 4B ({quantization})...")
    print(f"   Target file: {filename}")
    print()
    
    for i, repo_id in enumerate(repo_options, 1):
        print(f"Attempting repository {i}/{len(repo_options)}: {repo_id}")
        
        try:
            downloaded_path = hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                cache_dir=model_dir,
                local_dir=model_dir,
            )
            
            print(" Download complete!")
            print(f"   Location: {downloaded_path}")
            print(f"   Size: {Path(downloaded_path).stat().st_size / (1024**3):.2f} GB")
            
            return str(downloaded_path)
            
        except Exception as e:
            error_msg = str(e)
            print(f"  Failed: {error_msg[:100]}")
            print()
            
            # If it's the last repo and all failed
            if i == len(repo_options):
                print("=" * 60)
                print(" Model download failed from all sources")
                print("=" * 60)
                print()
                print("This may mean:")
                print("1. Gemma 3 GGUF models are not yet available")
                print("2. The model requires Hugging Face authentication")
                print("3. The repository names have changed")
                print()
                print("Alternative solutions:")
                print()
                print("Option A: Use Gemma 2 2B (smaller, available)")
                print("  Repo: google/gemma-2-2b-it-GGUF")
                print("  File: gemma-2-2b-it-Q4_K_M.gguf")
                print("  Size: ~1.4GB")
                print()
                print("Option B: Download model manually")
                print("  1. Visit: https://huggingface.co/models")
                print("  2. Search: 'gemma-3-4b-it gguf'")
                print("  3. Download .gguf file")
                print("  4. Place in: " + str(model_path))
                print()
                print("Option C: Use Phi-3-mini (original choice)")
                print("  Repo: microsoft/Phi-3-mini-4k-instruct-gguf")
                print("  File: Phi-3-mini-4k-instruct-q4.gguf")
                print("  Size: ~2.3GB")
                print()
                
                raise Exception(
                    "Could not download Gemma 3 4B model. "
                    "Please try one of the alternative solutions above."
                )


def get_model_path(model_dir: str = "models", quantization: str = "Q4_0") -> str:
    """
    Get the path to the Gemma 3 4B model file.
    
    Args:
        model_dir: Directory where model is stored
        quantization: Quantization level (Q4_0, Q4_K_M, Q8_0)
    
    Returns:
        Full path to the model file
    
    Raises:
        FileNotFoundError: If model file doesn't exist
    """
    # Map quantization to filename
    filename_map = {
        "Q4_0": "gemma-3-4b-it-q4_0.gguf",
        "Q4_K_M": "gemma-3-4b-it-q4_0.gguf",
        "Q5_K_M": "gemma-3-4b-it-q5_0.gguf",
        "Q8_0": "gemma-3-4b-it-q8_0.gguf",
        "f16": "gemma-3-4b-it-f16.gguf"
    }
    
    if quantization not in filename_map:
        print(f"Warning: Unknown quantization '{quantization}', using Q4_0")
        quantization = "Q4_0"
    
    filename = filename_map[quantization]
    model_path = Path(model_dir) / filename
    
    if not model_path.exists():
        raise FileNotFoundError(
            f"Model file not found: {model_path}\n"
            f"Please run: python src/ai_chat/setup_model.py\n"
            f"Or download from: https://huggingface.co/TheBloke/Phi-3-mini-4k-instruct-GGUF"
        )
    
    return str(model_path)


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
        info['recommended_quantization'] = 'Q4_0'
        info['recommended_max_ctx'] = 8192
        info['warnings'].append(
            f"Low RAM ({total_ram:.1f}GB). Use Q4_0 quantization "
            f"and limit context window to 8192 tokens."
        )
    elif total_ram < 12:
        info['recommended_quantization'] = 'Q4_0'
        info['recommended_max_ctx'] = 32768
        info['warnings'].append(
            f"Moderate RAM ({total_ram:.1f}GB). Q4_0 recommended "
            f"with context up to 32k tokens."
        )
    else:
        info['recommended_quantization'] = 'Q5_K_M' if total_ram < 16 else 'Q8_0'
        info['recommended_max_ctx'] = 128000
        print(f" Good RAM ({total_ram:.1f}GB). Can use larger context window.")
    
    # Check for GPU support
    try:
        import torch  # type: ignore
        if torch.cuda.is_available():
            info['gpu_available'] = True
            info['gpu_name'] = torch.cuda.get_device_name(0)
            print(f" CUDA GPU detected: {info['gpu_name']}")
    except ImportError:
        pass
    
    # Check for Metal (macOS)
    if sys.platform == 'darwin':
        info['gpu_available'] = True
        info['gpu_name'] = 'Apple Metal (MPS)'
        print(" Apple Metal GPU available (macOS)")
    
    return info


def main():
    """Main entry point for model setup."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Download and setup Gemma 3 4B model for local inference"
    )
    parser.add_argument(
        '--quantization', '-q',
        choices=['Q4_0', 'Q4_K_M', 'Q5_K_M', 'Q8_0', 'f16'],
        default='Q4_0',
        help='Model quantization level (default: Q4_0)'
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
    print(" Checking system requirements...")
    info = check_system_requirements()
    print(f"   Total RAM: {info['total_ram_gb']:.1f} GB")
    if info['gpu_available']:
        print(f"   GPU: {info.get('gpu_name', 'Available')}")
    else:
        print("   GPU: Not detected (will use CPU)")
    print()
    
    if info['warnings']:
        print("  Warnings:")
        for warning in info['warnings']:
            print(f"   - {warning}")
        print()
    
    # Recommended settings
    if not args.quantization:
        args.quantization = info['recommended_quantization']
    
    if args.check_only:
        print(" System check complete.")
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
        print(" Setup complete!")
        print("=" * 60)
        print()
        print("Next steps:")
        print(f"1. Model saved to: {model_path}")
        print("2. Update your code to use this model path")
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
        print(" Setup failed!")
        print("=" * 60)
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()


