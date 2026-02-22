# AI Models Directory

This application supports **any GGUF model** for local AI inference.

## Quick Start

### Option 1: Download via Command Line
```bash
# Download default model (Gemma 3 4B)
python -m src.ai_chat.setup_model

# Download a specific model
python -m src.ai_chat.setup_model --model phi3    # Phi-3 Mini (~2.3GB)
python -m src.ai_chat.setup_model --model gemma   # Gemma 3 4B (~2.5GB)
python -m src.ai_chat.setup_model --model llama2  # Llama 2 7B (~4.4GB)
python -m src.ai_chat.setup_model --model mistral # Mistral 7B (~4.4GB)

# List available models
python -m src.ai_chat.setup_model --list
```

### Option 2: Manual Download
1. Download any GGUF model from Hugging Face
2. Place the `.gguf` file in this `models/` folder
3. Restart the application
4. Select your model from the dropdown in AI Chat

## Supported Models

Any GGUF model will work. Popular options:

| Model | Size | Link |
|-------|------|------|
| Gemma 3 4B | ~2.5GB | [Download](https://huggingface.co/google/gemma-3-4b-it-qat-q4_0-gguf) |
| Phi-3 Mini | ~2.3GB | [Download](https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf) |
| Llama 2 7B | ~4.4GB | [Download](https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF) |
| Mistral 7B | ~4.4GB | [Download](https://huggingface.co/TheBloke/Mistral-7B-v0.1-GGUF) |

## Model Selection

When you open the AI Chat tab:
1. Select a model from the dropdown
2. Click "Load Model" 
3. Your selection is saved for next time

Use "Switch Model" to change models during a session.

## Multiple Models

You can have multiple GGUF files in this folder:
- All models are automatically discovered
- Models are sorted by size (smallest first)
- Your last-used model is remembered
