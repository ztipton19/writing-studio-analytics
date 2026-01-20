# AI Chat Feature - Setup & Migration Guide

## Overview

This guide walks through setting up the Gemma 3 4B AI chat feature for the Writing Studio Analytics application.

## Migration: Phi-3 → Gemma 3 4B

We've migrated from Phi-3-mini to **Gemma 3 4B Instruct** for enhanced capabilities:

### Key Changes

| Feature | Phi-3 | Gemma 3 4B |
|----------|---------|--------------|
| Context Window | 4K tokens | **128K tokens** |
| Vision Support | ❌ No | ✅ **Yes** (multimodal) |
| Model Size | ~2.3GB | ~3-4GB (Q4_K_M) |
| Developer | Microsoft | Google |
| Quantization | Q4_K_M | Q4_K_M or Q8_0 |
| Inference Speed | Fast | Fast (with 128K context) |

### Why Gemma 3 4B?

1. **Massive Context Window**: 128K tokens can handle full semester CSV data (~5,000 rows)
2. **Vision Capabilities**: Can analyze chart images alongside text queries
3. **Better Quality**: More capable for complex analytical questions
4. **Modern Architecture**: Recent release with improved reasoning

---

## Installation Steps

### Step 1: Install Dependencies

```bash
# Install from updated requirements.txt
pip install -r requirements.txt

# OR install AI chat dependencies manually
pip install llama-cpp-python>=0.3.0 huggingface-hub>=0.20.0 psutil>=6.0.0
```

### Step 2: Download Gemma 3 4B Model

Run the setup script to download the model:

```bash
python src/ai_chat/setup_model.py
```

This will:
- Download `gemma-3-4b-it-Q4_K_M.gguf` (~3-4GB) from HuggingFace
- Save it to `models/` directory
- Show download progress

**Expected Output:**
```
Downloading Gemma 3 4B Instruct (Q4_K_M quantization)...
From: https://huggingface.co/google/gemma-3-4b-it-gguf/resolve/main/gemma-3-4b-it-Q4_K_M.gguf
To: models/gemma-3-4b-it-Q4_K_M.gguf

[████████████████████████████████████████████████] 100%

✅ Model downloaded successfully!
Model location: models/gemma-3-4b-it-Q4_K_M.gguf
Model size: 3.2 GB
```

### Step 3: Verify Installation

```bash
# Test imports
python -c "from src.ai_chat.chat_handler import ChatHandler; print('✅ All imports successful')"

# Verify model exists
ls -lh models/gemma-3-4b-it-Q4_K_M.gguf
```

### Step 4: Run the Application

```bash
streamlit run app.py
```

You should see:
```
✅ AI Chat modules loaded successfully
✅ Walk-in modules successfully loaded from src/

  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

---

## System Requirements

### Minimum (CPU Only)

- **RAM**: 8GB (recommended: 16GB)
- **Storage**: 4GB free space (for model)
- **CPU**: Any modern multi-core processor
- **OS**: Windows 10+, macOS 10.15+, Linux

### Recommended (GPU Accelerated)

- **RAM**: 16GB+
- **GPU**: NVIDIA (CUDA 11.8+) or Apple Silicon (Metal)
- **VRAM**: 4GB+ (for offloading layers)

### Performance Estimates

| Configuration | Model Load Time | Inference Speed |
|--------------|----------------|-----------------|
| CPU Only (8GB RAM) | 10-15s | 3-5 tokens/sec |
| CPU Only (16GB RAM) | 8-12s | 4-6 tokens/sec |
| GPU (Metal/CUDA) | 5-8s | 15-25 tokens/sec |

---

## Using the AI Chat Feature

### 1. Generate a Report

First, generate a report in the **"Generate Report"** tab:
1. Upload your Penji export
2. Select session type
3. Configure options
4. Click **"Generate Report"**

This creates the `df_clean` in session state that the AI can analyze.

### 2. Open AI Chat Tab

Click the **"🤖 AI Chat Assistant"** tab (third tab).

First load will show:
```
Loading AI model (first time only)...

💻 System Information
- RAM: 16.0 GB
- GPU: Metal (MPS)
- CPU Threads: 8
- RAM Sufficient: ✅ Yes

✅ AI model loaded successfully!
```

### 3. Ask Questions

Use the chat input to ask questions about your data:

**Example Questions:**

Scheduled Sessions:
- "What were the busiest days of the week?"
- "How did student satisfaction change over time?"
- "Which writing stages were most common?"
- "What was the average booking lead time?"

Walk-In Sessions:
- "What were the peak hours for walk-ins?"
- "How many students used the space independently?"
- "What was the average session duration?"
- "Which courses were most common?"

### 4. Multimodal Analysis (Vision)

The AI can analyze charts alongside text. This feature is ready for future integration:
- Pass chart image paths to `handle_query()`
- AI interprets visualizations + data context
- Great for asking "What does this chart show?"

---

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│         Streamlit App (app.py)          │
├─────────────────────────────────────────────────┤
│  Tab 1: Generate Report                  │
│  Tab 2: Codebook Lookup                 │
│  Tab 3: AI Chat Assistant ◄── NEW        │
└────────────┬────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────┐
│         Chat Handler                      │
│  - Input validation                      │
│  - Context building                      │
│  - Prompt construction                  │
│  - Response filtering                    │
└────────────┬────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────┐
│         GemmaLLM (llama-cpp-python)    │
│  - Model loading                       │
│  - Text generation                     │
│  - Multimodal (vision) support          │
│  - GPU acceleration (Metal/CUDA)       │
└────────────┬────────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────────────┐
│  Gemma 3 4B Instruct (GGUF)          │
│  - 128K context window                 │
│  - Q4_K_M quantization (~3GB)        │
│  - Local-only inference                 │
└─────────────────────────────────────────────────┘
```

---

## Privacy & Safety

### Multi-Layer Protection

```
User Query → [Input Validation] → [Context Builder] → [LLM Generation] → [Response Filter] → Display
     ↓                    ↓                    ↓                    ↓                 ↓
  Block off-topic    Only aggregated      Privacy-aware       Block PII leaks
  & inappropriate     statistics only       system prompt      (emails, IDs)
```

### What Gets Blocked

**Input Validation (Pre-generation):**
- Off-topic queries (recipes, dating, weather)
- Inappropriate content (violence, illegal)
- Jailbreak attempts ("ignore all instructions")

**Response Filtering (Post-generation):**
- Email addresses
- Anonymous IDs (STU_xxxxx, TUT_xxxx)
- Suspicious phrases ("this student", "this tutor")

### What's Shared with AI

✅ **Shared:**
- Aggregated statistics (counts, averages, percentages)
- Data summaries and patterns
- Column names and data types
- Sample rows (anonymized)

❌ **Never Shared:**
- Raw individual records
- Email addresses
- Student/tutor names
- Identifying information

---

## Troubleshooting

### Issue: "AI Chat disabled"

**Symptom:** Tab doesn't appear, console shows import error

**Solution:**
```bash
# Install missing dependencies
pip install llama-cpp-python huggingface-hub psutil

# If llama-cpp-python fails, try:
CMAKE_ARGS="-DLLAMA_CUBLAS=off" pip install llama-cpp-python --upgrade --force-reinstall --no-cache-dir
```

### Issue: "Model file not found"

**Symptom:** Error when loading AI chat

**Solution:**
```bash
# Run setup script
python src/ai_chat/setup_model.py

# Or manually download
mkdir -p models
cd models
wget https://huggingface.co/google/gemma-3-4b-it-gguf/resolve/main/gemma-3-4b-it-Q4_K_M.gguf
```

### Issue: "RAM insufficient, may be slow"

**Symptom:** Warning in System Information

**Solution:**
- Acceptable for testing, but responses will be slower
- Close other applications to free RAM
- Consider using Q4_K_M quantization (already default)

### Issue: Slow inference

**Symptom:** Responses take 10+ seconds

**Solutions:**
1. **Enable GPU acceleration:**
   - macOS: Install torch with Metal support
   - Windows/Linux: Install CUDA toolkit
2. **Reduce context:** Limit conversation history
3. **Lower token limit:** Reduce `max_tokens` in `llm_engine.py`

---

## Development & Testing

### Test Script

Create `test_ai_chat.py`:

```python
from src.ai_chat.chat_handler import ChatHandler
from src.ai_chat.setup_model import get_model_path

# Load model
model_path = get_model_path()
handler = ChatHandler(model_path, verbose=True)

# Mock session state
mock_state = {
    'df_clean': None,  # Would be your DataFrame
    'data_mode': 'scheduled'
}

# Test query
result = handler.handle_query(
    "What is this app about?",
    mock_state
)

print("Response:", result['response'])
print("Metadata:", result['model_info'])
```

Run with:
```bash
python test_ai_chat.py
```

### Unit Tests

```bash
# Test data preparation
python -m pytest tests/test_data_prep.py

# Test safety filters
python -m pytest tests/test_safety.py

# Test chat handler
python -m pytest tests/test_chat_handler.py
```

---

## File Structure

```
src/ai_chat/
├── __init__.py                 # Module initialization
├── setup_model.py             # Model download script
├── llm_engine.py              # GemmaLLM class (wrapper)
├── data_prep.py               # CSV preparation utilities
├── prompt_templates.py         # System prompts
├── safety_filters.py          # Input validation & PII filtering
└── chat_handler.py           # Main orchestration

models/
└── gemma-3-4b-it-Q4_K_M.gguf  # Downloaded model (~3GB)
```

---

## Performance Optimization

### For CPU-Only Systems

1. **Reduce conversation history:**
   ```python
   # In chat_handler.py, change:
   if len(self.conversation_history) > 10:  # From 10 to 5
       self.conversation_history = self.conversation_history[-5:]
   ```

2. **Lower token limits:**
   ```python
   # In llm_engine.py, change:
   n_ctx=64000  # From 128000 to 64000
   max_tokens=256  # From 512 to 256
   ```

3. **Use faster quantization:**
   - Download Q4_K_M instead of Q8_0 (already default)

### For GPU Systems

1. **Verify GPU acceleration:**
   ```python
   # Check GPU info
   sys_info = handler.check_system_requirements()
   print(sys_info['gpu_acceleration'])  # Should show "Metal (MPS)" or "CUDA"
   ```

2. **Adjust GPU layers:**
   ```python
   # In llm_engine.py, increase GPU offloading:
   n_gpu_layers=-1  # Offload all layers to GPU
   ```

---

## Future Enhancements

### Planned Features

1. **Chart Generation**
   - User: "Show sessions by hour"
   - AI generates matplotlib code → executes → displays chart

2. **Data Filtering**
   - User: "Show me only Fall 2024 data"
   - AI filters DataFrame → regenerates metrics

3. **Voice Input**
   - Speech-to-text for queries
   - Accessibility feature

4. **Export Conversation**
   - Save chat history to .txt
   - Include in PDF report

### Contributing

To contribute to the AI chat feature:

1. Edit files in `src/ai_chat/`
2. Test with `test_ai_chat.py`
3. Update this documentation
4. Submit pull request

---

## License & Attribution

### Gemma 3 4B License

- **Model**: Gemma 3 4B Instruct
- **Author**: Google
- **License**: Gemma License
- **Source**: https://huggingface.co/google/gemma-3-4b-it-gguf

**Attribution must be included in:**
- User-facing documentation
- About sections
- Source code comments

### llama-cpp-python

- **Library**: llama-cpp-python
- **Author**: André Betzler
- **License**: MIT
- **Source**: https://github.com/abetlen/llama-cpp-python

---

## Support

### Getting Help

1. **Check this guide first** - most issues are covered above
2. **Review error messages** - they're usually descriptive
3. **Check system requirements** - ensure you have 8GB+ RAM
4. **Consult logs** - terminal output shows detailed errors

### Reporting Bugs

When reporting issues, include:
- OS and version
- Python version (`python --version`)
- Exact error message
- Steps to reproduce
- System specs (RAM, GPU)

---

## Summary

The AI Chat feature with Gemma 3 4B provides:

✅ **Local-only inference** - No cloud APIs, no data leaves your machine
✅ **128K context window** - Handles full semester data
✅ **Vision capabilities** - Can analyze charts and visualizations
✅ **Privacy-first** - Multi-layer safety protection
✅ **Easy setup** - One script to download everything
✅ **Production-ready** - Integrated into existing app

**Status**: ✅ Implementation Complete

Next steps:
1. Run `python src/ai_chat/setup_model.py`
2. Test with `streamlit run app.py`
3. Generate a report and try the AI chat tab
