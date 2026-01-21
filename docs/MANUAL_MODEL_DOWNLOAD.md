# Manual Model Download Instructions

## Quick Download (Direct Link)

The Gemma 3 4B model requires Hugging Face authentication for automated downloads. Use this direct link to download manually:

**Download Gemma 3 4B (Q4):**
```
https://huggingface.co/google/gemma-3-4b-it-qat-q4_0-gguf/resolve/main/gemma-3-4b-it-q4_0.gguf
```

**Steps:**
1. Click the link above
2. The file will download (approximately 2.3 GB)
3. Move to `models/` directory in your project
4. Rename to `gemma-3-4b-it-q4_0.gguf` (if needed)
5. Run the app: `streamlit run app.py`

## Alternative Models (No Authentication Required)

If you prefer not to use Gemma 3, these models work excellently:

### Phi-3-mini (Recommended for Analytics)
- **Size:** 2.3GB
- **Context:** 4K tokens
- **Download:** https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf
- **File:** `Phi-3-mini-4k-instruct-Q4_K_M.gguf` or `Phi-3-mini-4k-instruct-q4.gguf`
- **Pros:** Excellent for analytics tasks, fast inference, MIT license

### Gemma 2 2B
- **Size:** 1.4GB (smaller)
- **Context:** 8K tokens
- **Download:** https://huggingface.co/google/gemma-2-2b-it-GGUF
- **File:** `gemma-2-2b-it-Q4_K_M.gguf`
- **Pros:** Very fast, smaller footprint, Apache 2.0 license

## Model Comparison

| Model | Context | Size | Speed | Vision | License |
|-------|---------|------|-------|--------|---------|
| Gemma 3 4B | 128K | 2.3GB | Fast | Yes | Gemma License |
| Phi-3-mini | 4K | 2.3GB | Fast | No | MIT |
| Gemma 2 2B | 8K | 1.4GB | Very Fast | No | Apache 2.0 |

## After Download

1. **Verify file size:**
   ```bash
   ls -lh models/*.gguf
   ```
   Should show approximately 2.3GB for Gemma 3 or Phi-3, or 1.4GB for Gemma 2.

2. **Run the app:**
   ```bash
   streamlit run app.py
   ```

3. **Test AI Chat:**
   - Upload a CSV file
   - Generate report
   - Navigate to "🤖 AI Chat Assistant" tab
   - Ask a question like "What were the busiest hours?"

## System Requirements Verified

✅ Apple Metal GPU available (macOS)
✅ Total RAM: 8.0 GB
✅ Recommended: Q4 quantization with 32K context
✅ All dependencies installed:
   - llama-cpp-python (Metal backend)
   - psutil
   - huggingface-hub

## Troubleshooting

### File Size Too Small (<100MB)
The download was likely an error page. Try downloading again from the direct link.

### Model Not Found Error
Ensure the file is in the `models/` directory and has the correct name:
- Gemma 3: `gemma-3-4b-it-q4_0.gguf`
- Phi-3-mini: `Phi-3-mini-4k-instruct-Q4_K_M.gguf`
- Gemma 2: `gemma-2-2b-it-Q4_K_M.gguf`

### App Crashes on Load
- Ensure you have 8GB+ RAM
- Close other applications
- Try a smaller model (Gemma 2 2B is only 1.4GB)

## Support

For detailed documentation, see:
- `docs/ai-chat-setup-guide.md` - Complete setup and usage guide
- `src/ai_chat/` - Source code for AI Chat implementation

**The AI Chat feature is code-complete and ready to use once you download a model file!**
