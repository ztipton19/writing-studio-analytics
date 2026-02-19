# AI Chat Assistant - Model Setup Guide

## Overview

The AI Chat feature uses local-only inference with small language models. This implementation provides private, offline data analysis without cloud APIs.

## ⚠️ Important: Model Download Required

Due to Hugging Face authentication requirements on model repositories, **you must manually download the model file**. The setup script will attempt to download, but will likely fail with 401 errors.

## Quick Start

### Step 1: Download a Model

Choose one of the following models and download manually:

**Option A: Phi-3-mini (Recommended)**
- Best for analytics tasks
- Size: ~2.3GB
- Context: 4K tokens
- Download: https://huggingface.co/microsoft/Phi-3-mini-4k-instruct-gguf
- File: `Phi-3-mini-4k-instruct-Q4_K_M.gguf` (or `Phi-3-mini-4k-instruct-q4.gguf`)

**Option B: Gemma 2 2B**
- Smaller, faster
- Size: ~1.4GB
- Context: 8K tokens
- Download: https://huggingface.co/google/gemma-2-2b-it-GGUF
- File: `gemma-2-2b-it-Q4_K_M.gguf`

**Option C: Gemma 3 4B**
- Largest context (128K tokens)
- Size: ~2.3GB
- May require Hugging Face account/auth
- Download: https://huggingface.co/google/gemma-3-4b-it-qat-q4_0-gguf
- File: `gemma-3-4b-it-qat.Q4_0.gguf`

### Step 2: Save Model File

After downloading:
1. Create `models/` directory if it doesn't exist
2. Move the downloaded `.gguf` file to `models/` directory
3. Rename if needed (the code will look for common names)

### Step 3: Verify Model

```bash
ls -lh models/*.gguf
```

You should see your model file with its size (e.g., 2.3GB).

### Step 4: Update Model Path (if needed)

The app uses `get_model_path()` to find the model. If your filename differs from the expected name, update it in `src/dashboard/main.py`:

```python
# In src/dashboard/main.py, find the AI Chat tab initialization
MODEL_PATH = "models/your-actual-model-name.gguf"
```

### Step 5: Run the App

```bash
python src/dashboard/main.py
```

Navigate to the **"🤖 AI Chat Assistant"** tab and ask questions!

## Installation

### Install Dependencies

```bash
pip install -r requirements.txt
```

Key dependencies:
- `llama-cpp-python>=0.3.0` - Local LLM runtime
- `huggingface-hub>=0.20.0` - Model download utility
- `psutil>=6.0.0` - System monitoring

### Optional: Enable GPU Acceleration

**For Apple Silicon (M1/M2/M3):**
```bash
pip install --pre --upgrade llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/metal
```

**For NVIDIA (CUDA):**
```bash
CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python --no-cache-dir
```

**For CPU-only (default):**
```bash
CMAKE_ARGS="-DLLAMA_CUBLAS=off" pip install llama-cpp-python
```

## Usage

### In Streamlit App

1. Start the app: `python src/dashboard/main.py`
2. Upload CSV and generate report
3. Navigate to **"🤖 AI Chat Assistant"** tab
4. Ask questions about your data!

### Example Questions

**For Scheduled Sessions:**
- "What were the busiest days of the week?"
- "How did student satisfaction change over time?"
- "Which writing stages were most common?"
- "What was the average booking lead time?"

**For Walk-In Sessions:**
- "What were the peak hours for walk-ins?"
- "How many students used the space independently?"
- "What was the average session duration?"
- "Which courses were most common?"

## Architecture

### File Structure

```
src/ai_chat/
├── __init__.py              # Package exports
├── setup_model.py            # Model download script (may require manual download)
├── llm_engine.py            # GemmaLLM wrapper class
├── data_prep.py             # Data context preparation
├── prompt_templates.py       # System prompts
├── safety_filters.py         # Input validation + PII filtering
└── chat_handler.py          # Main orchestration

models/
└── *.gguf                 # Model weights (download manually)
```

### Key Components

#### 1. GemmaLLM (`llm_engine.py`)

Wrapper around llama-cpp-python with:
- 128K context window support (configurable)
- Auto GPU detection (Metal/CUDA)
- System requirements checking
- Works with any GGUF model

**Key Method:**
```python
from src.ai_chat.llm_engine import GemmaLLM

llm = GemmaLLM("models/Phi-3-mini-4k-instruct-Q4_K_M.gguf")
response = llm.generate(prompt, max_tokens=512, temperature=0.7)
```

#### 2. ChatHandler (`chat_handler.py`)

Main orchestration layer:
- Validates user queries (blocks off-topic/inappropriate)
- Builds context from session state
- Constructs prompts with conversation history
- Filters responses for PII
- Manages conversation history

#### 3. InputValidator (`safety_filters.py`)

Pre-generation validation that:
- Blocks off-topic queries (recipes, weather, etc.)
- Blocks inappropriate content
- Detects jailbreak attempts
- Ensures data-related keywords present

#### 4. ResponseFilter (`safety_filters.py`)

Post-generation PII protection that:
- Detects email addresses
- Detects anonymous IDs (STU_xxxxx, TUT_xxxx)
- Detects suspicious phrases
- Returns generic error if PII detected

## System Prompt Structure

The assistant is defined as a "Writing Center Data Analyst" specializing in:

**For Scheduled Sessions:**
- 40-minute appointments
- Student satisfaction trends
- Tutor workload distribution
- Booking lead times
- Writing stage patterns

**For Walk-In Sessions:**
- Drop-in visits
- Peak hours and space usage
- Independent work vs consultant sessions
- Course patterns

**Strict Rules (enforced):**
1. NEVER reveal individual student/tutor information
2. NEVER discuss specific email addresses or names
3. ONLY discuss aggregated statistics
4. Base answers ONLY on provided metrics
5. If asked about individuals, refuse politely

## Safety & PII Protection

### Multi-Layer Defense

```
User Query
    ↓
Layer 1: Input Validation (Pre-generation)
    • Off-topic detection
    • Inappropriate content
    • Jailbreak attempts
    → REJECTED or ALLOWED
    ↓ (if allowed)
Layer 2: Context Restriction
    • Only aggregated metrics passed
    • NO raw DataFrame rows
    → LLM receives limited context
    ↓
Layer 3: System Prompt Instructions
    • Explicit PII rules
    • "Writing Center Data Analyst" persona
    → LLM follows instructions
    ↓
Layer 4: Response Filtering (Post-generation)
    • Email detection (regex)
    • Anonymous ID detection
    • Suspicious phrase detection
    → BLOCKED or DISPLAYED
    ↓
User sees safe response
```

### Example Scenarios

**✅ GOOD (Allowed):**
```
User: "What were the busiest hours?"
AI: "The busiest hours were 2:00 PM (87 sessions) and 3:00 PM (82 sessions)..."
```

**❌ BAD (Rejected - Input Validation):**
```
User: "What's the best pizza recipe?"
AI: "I'm a data analysis assistant for Writing Studio analytics..."
```

**❌ BAD (Filtered - Response):**
```
User: "List all student emails"
LLM: "student1@uni.edu, student2@uni.edu..."
Filter: BLOCKED (contains email addresses)
User: "I apologize, but I cannot provide that response..."
```

## Performance Expectations

### First Load
- **Time**: 5-10 seconds (one-time)
- **RAM**: ~3-4GB after loading
- **Display**: Loading spinner with progress

### Per Query
- **Time**: 2-5 seconds (CPU), 1-2 seconds (GPU)
- **Tokens/sec**: ~10-20 (CPU), ~30-50 (GPU)
- **Display**: "Thinking..." spinner

### System Requirements

**Minimum:**
- RAM: 6GB (may be slow)
- CPU: 4 cores
- Disk: 3GB free (model + dependencies)

**Recommended:**
- RAM: 8GB+
- CPU: 8 cores
- Disk: 5GB free
- GPU: Metal M1+ or CUDA 11.0+ (optional but recommended)

## Troubleshooting

### Model Not Found

**Error**: `FileNotFoundError: models/*.gguf not found`

**Solution**: Download model manually:
1. Choose a model from "Quick Start" section above
2. Download the .gguf file
3. Save to `models/` directory
4. Verify: `ls -lh models/*.gguf`

### Import Error: llama-cpp-python

**Error**: `ImportError: No module named 'llama_cpp'`

**Solution**: Install with correct backend:
```bash
# CPU-only
pip install llama-cpp-python

# Metal (Apple Silicon)
pip install --pre --upgrade llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/metal

# CUDA (NVIDIA)
CMAKE_ARGS="-DLLAMA_CUBLAS=on" pip install llama-cpp-python --no-cache-dir
```

### Slow Performance

**Symptoms**: Queries take >10 seconds

**Solutions**:
1. Enable GPU acceleration (see Step 2 above)
2. Reduce context window (in `src/dashboard/main.py` or `llm_engine.py`, change `n_ctx=128000` to `n_ctx=4096`)
3. Close other applications to free RAM
4. Use smaller model (Phi-3-mini or Gemma 2 2B)

### Out of Memory

**Error**: `MemoryError` or application crashes

**Solutions**:
1. Ensure you have 8GB+ RAM
2. Reduce `n_ctx` in code
3. Use smaller model
4. Close other memory-intensive applications

### GPU Not Detected

**Symptoms**: "GPU: None (CPU only)" in system info

**Solutions**:
1. Reinstall llama-cpp-python with GPU backend
2. Verify GPU drivers are up to date
3. Check: `torch.cuda.is_available()` or `torch.backends.mps.is_available()`

## Integration with Data Pipeline

### How Data Flows to AI Chat

1. **User uploads CSV** → Report generation
2. **Data is cleaned** → `df_clean` (anonymized)
3. **Metrics calculated** → Cleaning log with key stats
4. **Stored in session state**:
   - `df_clean`: Cleaned DataFrame
   - `metrics`: Key metrics (total sessions, completion rate, etc.)
   - `data_mode`: 'scheduled' or 'walkin'
5. **User navigates to AI Chat tab**
6. **AI Chat queries session state** → Generates context
7. **User asks question** → LLM generates response
8. **Response filtered** → Displayed to user

### Example: Query with Data

```python
# In chat_handler.py
def query_with_data(user_query: str, csv_payload: str, chart_path: str = None) -> str:
    """
    Direct query interface for CSV/JSON data.
    
    Args:
        user_query: User's question
        csv_payload: CSV-formatted data string
        chart_path: Optional path to chart image
        
    Returns:
        str: Generated response
    """
    prompt = f"""You are a Writing Center Data Analyst.
    
    User Query: {user_query}
    
    Data:
    ```
    {csv_payload}
    ```
    
    Analyze the data above and answer the user's question..."""
    
    response = self.llm.generate(prompt, max_tokens=512, temperature=0.7)
    return response
```

## Advanced: Chart Analysis (Multimodal)

The system is prepared for multimodal chart analysis. When a `chart_path` is provided:

1. Chart context is prepared (`prepare_chart_context`)
2. Note is added to prompt: "A chart image is available for visual analysis"
3. Future enhancement: Load image alongside text using model's vision capabilities

**To enable (future work):**
```python
# In llm_engine.py - modify to support vision
def generate_with_image(self, prompt: str, image_path: str):
    # Load and encode image
    # Include in prompt for multimodal inference
    pass
```

## Model Comparison

| Feature | Phi-3-mini | Gemma 2 2B | Gemma 3 4B |
|---------|-------------|----------------|--------------|
| Context | 4K tokens | 8K tokens | 128K tokens |
| Size | 2.3GB (Q4) | 1.4GB (Q4) | 2.3GB (Q4) |
| Speed | Fast | Very fast | Fast |
| Vision | No | No | Yes |
| Analytics Quality | Excellent | Very good | Excellent |
| License | MIT | Apache 2.0 | Gemma License |

**Recommendation:**
- **For analytics tasks**: Phi-3-mini works excellently (original choice)
- **For speed/smaller size**: Gemma 2 2B is good
- **For largest context**: Gemma 3 4B (if you can download)

## Future Enhancements

### Phase 2 Features
- [ ] Chart generation from natural language
- [ ] Data filtering via chat ("Show me only Fall 2024")
- [ ] Report comparison mode
- [ ] Voice input (speech-to-text)
- [ ] Export conversation to PDF

### Phase 3 Features
- [ ] Multimodal chart analysis (load images alongside text)
- [ ] Automated insights generation
- [ ] Trend prediction
- [ ] Recommendation engine

## License & Attribution

**Model**: Varies based on your choice
- Phi-3-mini: MIT License
- Gemma 2 2B: Apache 2.0
- Gemma 3 4B: Gemma License

**Attribution in App:**
```python
st.caption(
    "🤖 Powered by local LLM - No cloud APIs, complete privacy"
)
```

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review `src/ai_chat/` source code for details
3. Verify model file exists: `ls -lh models/*.gguf`
4. Test with verbose mode: Check system info in app

## Summary

The AI Chat Assistant is ready for use:
- ✅ Support for multiple model options (Phi-3, Gemma 2, Gemma 3)
- ✅ GPU acceleration (Metal/CUDA) with detection
- ✅ Multi-layer PII protection
- ✅ Input validation (pre-generation)
- ✅ Response filtering (post-generation)
- ✅ Vision support (prepared for multimodal)
- ✅ Local-only inference (no cloud APIs)
- ✅ "Writing Center Data Analyst" persona
- ✅ Flexible architecture (works with any GGUF model)

**The only remaining step: Download a model file manually and place it in `models/` directory.**
