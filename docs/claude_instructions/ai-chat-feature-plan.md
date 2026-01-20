# AI Chat Feature Implementation Plan

## Executive Summary

Add a third tab to the Streamlit app that provides an AI-powered natural language interface for querying analytics data. Users can ask questions about their reports (scheduled sessions or walk-ins) and receive intelligent responses grounded in the actual data.

**Key Requirements:**
- Local-only execution (no cloud APIs)
- Open-source small language model
- PII-safe (only discusses aggregated/anonymized data)
- Context-aware (knows whether user is viewing scheduled or walk-in data)
- Must work in standalone .exe packaging

---

## 1. Architecture Overview

### 1.1 User Flow

```
User uploads CSV → Processes data → Generates report
                                    ↓
                    Three tabs appear in Streamlit:
                    [1] Report Preview (current)
                    [2] Data Explorer (current)
                    [3] AI Chat Assistant (NEW)
                                    ↓
                    User clicks "AI Chat Assistant" tab
                                    ↓
                    Chat interface loads with:
                    - Session context (scheduled/walkin)
                    - Access to cleaned DataFrame
                    - Access to metrics dictionary
                    - Pre-loaded system prompt
                                    ↓
                    User asks: "What were the busiest hours?"
                                    ↓
                    AI responds with data-grounded answer
```

### 1.2 Technical Stack

```
┌─────────────────────────────────────────────────┐
│           Streamlit App (app.py)                │
├─────────────────────────────────────────────────┤
│  Tab 1: Report Preview                          │
│  Tab 2: Data Explorer                           │
│  Tab 3: AI Chat Assistant ◄── NEW               │
│           ↓                                      │
│      Chat Handler                                │
│           ↓                                      │
│   ┌──────────────────────┐                      │
│   │  LLM Orchestrator    │                      │
│   │  - Context Manager   │                      │
│   │  - Prompt Builder    │                      │
│   │  - Response Filter   │                      │
│   └──────────┬───────────┘                      │
│              ↓                                   │
│   ┌──────────────────────┐                      │
│   │  Local LLM Engine    │                      │
│   │  (llama.cpp or       │                      │
│   │   Ollama runtime)    │                      │
│   └──────────┬───────────┘                      │
│              ↓                                   │
│   ┌──────────────────────┐                      │
│   │  Model Weights       │                      │
│   │  (Bundled in /models)│                      │
│   └──────────────────────┘                      │
└─────────────────────────────────────────────────┘
```

---

## 2. Model Selection Criteria

### 2.1 Requirements

**Must Have:**
- ✅ Runs locally on CPU (no GPU required)
- ✅ Small model size (<2GB for .exe distribution)
- ✅ Good instruction-following capability
- ✅ JSON output support (for structured responses)
- ✅ Fast inference on consumer hardware
- ✅ Open-source license (Apache 2.0, MIT, etc.)
- ✅ Python bindings available

**Nice to Have:**
- Quantized versions available (4-bit, 5-bit)
- Active community support
- Pre-trained on analytical/tabular data

### 2.2 Recommended Models (as of Jan 2025)

#### **Option 1: Phi-3-mini (Microsoft) - RECOMMENDED**
```
Model: microsoft/Phi-3-mini-4k-instruct (Q4_K_M quantized)
Size: ~2.3GB (quantized)
Context: 4k tokens
Strengths:
  - Excellent instruction following
  - Fast inference (~10-20 tokens/sec on CPU)
  - Good reasoning for size
  - Designed for local deployment
License: MIT
Runtime: llama.cpp via llama-cpp-python
```

#### **Option 2: TinyLlama-1.1B**
```
Model: TinyLlama/TinyLlama-1.1B-Chat-v1.0
Size: ~1.1GB
Context: 2k tokens
Strengths:
  - Very small footprint
  - Fast inference
  - Good for simple queries
  - Apache 2.0 license
Weaknesses:
  - Less capable reasoning
  - May struggle with complex analytics questions
Runtime: llama.cpp or Ollama
```

#### **Option 3: Gemma-2B-it (Google)**
```
Model: google/gemma-2b-it (Q4 quantized)
Size: ~1.7GB
Context: 8k tokens
Strengths:
  - Trained by Google (high quality)
  - Good balance of size vs capability
  - 8k context (can handle larger data summaries)
Weaknesses:
  - Gemma license (more restrictive than Apache/MIT)
Runtime: llama.cpp
```

**Decision: Start with Phi-3-mini** for best balance of capability, size, and licensing.

---

## 3. Implementation Architecture

### 3.1 File Structure

```
src/
├── ai_chat/
│   ├── __init__.py
│   ├── chat_handler.py         # Main chat orchestration
│   ├── context_builder.py      # Builds context from session state
│   ├── prompt_templates.py     # System prompts and templates
│   ├── llm_engine.py          # LLM wrapper (llama-cpp-python)
│   ├── response_filter.py     # PII safety checks
│   └── model_loader.py        # Model initialization and caching

models/                         # Model weights directory
├── phi-3-mini-4k-Q4_K_M.gguf  # Downloaded model file
└── README.md                   # Model attribution and license

app.py                          # Updated with new tab
```

### 3.2 Key Components

#### **A. Context Builder** (`context_builder.py`)

Prepares data context for the LLM:

```python
def build_chat_context(session_state):
    """
    Build context from current session state.

    Returns:
    - session_type: 'scheduled' or 'walkin'
    - data_summary: Dict with key metrics
    - available_fields: List of column names
    - date_range: String representation
    """

    session_type = session_state.get('data_mode', 'scheduled')
    df = session_state.get('df_clean')
    metrics = session_state.get('metrics', {})

    # Build data summary (NO RAW DATA, ONLY AGGREGATES)
    summary = {
        'type': session_type,
        'total_records': len(df),
        'date_range': get_date_range(df),
        'available_metrics': list(metrics.keys()),
        'columns': list(df.columns),
        'key_stats': extract_key_stats(metrics)
    }

    return summary
```

**Important: Never pass raw DataFrame rows to LLM** - only aggregated metrics and column names.

#### **B. Prompt Templates** (`prompt_templates.py`)

System prompts that enforce behavior:

```python
SCHEDULED_SESSIONS_SYSTEM_PROMPT = """
You are a data analysis assistant for a university Writing Studio.

CONTEXT:
- You have access to SCHEDULED SESSION data (40-minute appointments)
- Total sessions: {total_sessions}
- Date range: {date_range}
- Available metrics: {available_metrics}

YOUR ROLE:
- Answer questions about session patterns, student satisfaction, tutor workload
- Provide insights based on aggregated data
- Suggest interpretations when appropriate

STRICT RULES:
1. NEVER reveal or discuss individual student/tutor information
2. NEVER mention specific email addresses or names
3. ONLY discuss aggregated statistics (averages, totals, percentages)
4. If asked about individuals, respond: "I can only discuss aggregated data to protect privacy"
5. Base answers ONLY on the metrics provided - don't make up data
6. If you don't have data for a question, say so clearly

AVAILABLE DATA FIELDS:
{available_fields}

KEY METRICS:
{key_metrics}

Respond conversationally but professionally. Keep answers concise (2-4 sentences).
"""

WALKIN_SESSIONS_SYSTEM_PROMPT = """
You are a data analysis assistant for a university Writing Studio.

CONTEXT:
- You have access to WALK-IN SESSION data (drop-in appointments)
- Total sessions: {total_sessions}
- Date range: {date_range}
- Session types: Completed (with consultant), Check In (independent work)

YOUR ROLE:
- Answer questions about walk-in patterns, consultant workload, space usage
- Provide insights based on aggregated data
- Note that walk-in data has less detail than scheduled sessions

STRICT RULES:
[Same as scheduled sessions...]

AVAILABLE DATA FIELDS:
{available_fields}

KEY METRICS:
{key_metrics}

Respond conversationally but professionally. Keep answers concise (2-4 sentences).
"""
```

#### **C. LLM Engine** (`llm_engine.py`)

Wrapper around llama-cpp-python:

```python
from llama_cpp import Llama

class LocalLLM:
    """
    Local LLM engine using llama.cpp.

    Handles:
    - Model loading and caching
    - Generation with parameters
    - Context management
    """

    def __init__(self, model_path, n_ctx=2048, n_threads=4):
        self.model_path = model_path
        self.n_ctx = n_ctx
        self.n_threads = n_threads
        self._model = None

    def load_model(self):
        """Load model into memory (cached)"""
        if self._model is None:
            self._model = Llama(
                model_path=self.model_path,
                n_ctx=self.n_ctx,
                n_threads=self.n_threads,
                n_gpu_layers=0,  # CPU only
                verbose=False
            )
        return self._model

    def generate(self, prompt, max_tokens=256, temperature=0.3):
        """
        Generate response.

        Parameters:
        - prompt: Full prompt (system + user)
        - max_tokens: Max response length
        - temperature: 0.0-1.0 (lower = more deterministic)
        """
        model = self.load_model()

        response = model(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=0.9,
            top_k=40,
            repeat_penalty=1.1,
            stop=["User:", "\n\n\n"]
        )

        return response['choices'][0]['text'].strip()
```

#### **D. Response Filter** (`response_filter.py`)

PII safety layer:

```python
import re

class ResponseFilter:
    """
    Filter LLM responses for PII leakage.

    Checks for:
    - Email addresses
    - Anonymous IDs (STU_xxxxx, TUT_xxxx)
    - Suspicious patterns
    """

    def __init__(self):
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.anon_id_pattern = re.compile(r'\b(STU|TUT)_\d+\b')

    def is_safe(self, response):
        """
        Check if response is safe to show user.

        Returns: (is_safe: bool, reason: str)
        """
        # Check for email addresses
        if self.email_pattern.search(response):
            return False, "Response contains email address"

        # Check for anonymous IDs
        if self.anon_id_pattern.search(response):
            return False, "Response contains anonymous ID"

        # Check for suspicious phrases
        suspicious = [
            "student email",
            "tutor email",
            "student name",
            "tutor name",
            "this student",
            "this tutor"
        ]

        response_lower = response.lower()
        for phrase in suspicious:
            if phrase in response_lower:
                return False, f"Response contains suspicious phrase: {phrase}"

        return True, "Safe"

    def filter_response(self, response):
        """
        Filter response and return safe version.

        If unsafe, returns error message.
        """
        is_safe, reason = self.is_safe(response)

        if is_safe:
            return response
        else:
            return (
                "I apologize, but I cannot provide that response as it may contain "
                "sensitive information. Please rephrase your question to focus on "
                "aggregated data and trends."
            )
```

#### **E. Chat Handler** (`chat_handler.py`)

Main orchestration:

```python
class ChatHandler:
    """
    Main chat orchestration.

    Coordinates:
    - Context building
    - Prompt construction
    - LLM generation
    - Response filtering
    """

    def __init__(self, model_path):
        self.llm = LocalLLM(model_path)
        self.filter = ResponseFilter()
        self.conversation_history = []

    def handle_query(self, user_query, session_state):
        """
        Handle user query.

        Returns: (response: str, metadata: dict)
        """
        # 1. Build context
        context = build_chat_context(session_state)

        # 2. Select prompt template
        if context['type'] == 'scheduled':
            system_prompt = SCHEDULED_SESSIONS_SYSTEM_PROMPT.format(
                total_sessions=context['total_records'],
                date_range=context['date_range'],
                available_metrics=', '.join(context['available_metrics']),
                available_fields=', '.join(context['columns']),
                key_metrics=format_key_metrics(context['key_stats'])
            )
        else:
            system_prompt = WALKIN_SESSIONS_SYSTEM_PROMPT.format(...)

        # 3. Build full prompt
        full_prompt = self._build_prompt(system_prompt, user_query)

        # 4. Generate response
        raw_response = self.llm.generate(full_prompt)

        # 5. Filter response
        safe_response = self.filter.filter_response(raw_response)

        # 6. Update conversation history
        self.conversation_history.append({
            'user': user_query,
            'assistant': safe_response
        })

        return safe_response, {
            'context_type': context['type'],
            'filtered': raw_response != safe_response
        }

    def _build_prompt(self, system_prompt, user_query):
        """Build full prompt with conversation history"""
        # Format depends on model's chat template
        # For Phi-3:
        prompt = f"<|system|>\n{system_prompt}<|end|>\n"

        # Add conversation history
        for turn in self.conversation_history[-3:]:  # Last 3 turns
            prompt += f"<|user|>\n{turn['user']}<|end|>\n"
            prompt += f"<|assistant|>\n{turn['assistant']}<|end|>\n"

        # Add current query
        prompt += f"<|user|>\n{user_query}<|end|>\n<|assistant|>\n"

        return prompt
```

---

## 4. Streamlit Integration

### 4.1 Updated app.py Structure

```python
import streamlit as st
from src.ai_chat.chat_handler import ChatHandler
from src.ai_chat.model_loader import load_chat_model

# ... existing imports ...

def main():
    st.title("Writing Studio Analytics")

    # ... existing sidebar upload logic ...

    if st.session_state.get('report_generated'):
        # Three tabs
        tab1, tab2, tab3 = st.tabs([
            "📄 Report Preview",
            "📊 Data Explorer",
            "🤖 AI Chat Assistant"  # NEW
        ])

        with tab1:
            # ... existing report preview ...
            pass

        with tab2:
            # ... existing data explorer ...
            pass

        with tab3:
            render_ai_chat_tab()

def render_ai_chat_tab():
    """Render AI chat interface"""
    st.header("🤖 AI Chat Assistant")

    st.info(
        "Ask questions about your data! I can help you understand patterns, "
        "trends, and insights. Note: I only discuss aggregated data to protect privacy."
    )

    # Initialize chat handler (cached)
    if 'chat_handler' not in st.session_state:
        with st.spinner("Loading AI model (first time only)..."):
            model_path = "models/phi-3-mini-4k-Q4_K_M.gguf"
            st.session_state.chat_handler = ChatHandler(model_path)
            st.session_state.chat_messages = []

    # Display chat history
    for message in st.session_state.chat_messages:
        with st.chat_message(message['role']):
            st.write(message['content'])

    # Chat input
    if prompt := st.chat_input("Ask a question about your data..."):
        # Add user message
        st.session_state.chat_messages.append({
            'role': 'user',
            'content': prompt
        })

        with st.chat_message("user"):
            st.write(prompt)

        # Generate response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response, metadata = st.session_state.chat_handler.handle_query(
                    prompt,
                    st.session_state
                )
                st.write(response)

        # Add assistant message
        st.session_state.chat_messages.append({
            'role': 'assistant',
            'content': response
        })

    # Helpful suggestions
    with st.expander("💡 Example Questions"):
        st.markdown("""
        **Scheduled Sessions:**
        - What were the busiest days of the week?
        - How did student satisfaction change over time?
        - Which writing stages were most common?
        - What was the average booking lead time?

        **Walk-In Sessions:**
        - What were the peak hours for walk-ins?
        - How many students used the space independently?
        - What was the average session duration?
        - Which courses were most common?
        """)

    # Clear chat button
    if st.button("��️ Clear Chat History"):
        st.session_state.chat_messages = []
        st.session_state.chat_handler.conversation_history = []
        st.rerun()
```

---

## 5. PII Protection Strategy

### 5.1 Multi-Layer Defense

**Layer 1: Context Restriction**
- Never pass raw DataFrame to LLM
- Only provide aggregated metrics
- Only provide column names (not values)

**Layer 2: System Prompt Instructions**
- Explicit rules against revealing individual data
- Instructions to only discuss aggregates

**Layer 3: Response Filtering**
- Regex patterns for emails, IDs
- Keyword detection for suspicious phrases
- Automatic response blocking

**Layer 4: User Education**
- Clear UI messaging about privacy
- Example questions that demonstrate safe usage
- Warning if user asks about individuals

### 5.2 Example Safety Checks

```python
# BAD - User asks about individual
User: "Who is STU_04521?"
Filter: BLOCKED - Contains anonymous ID

# BAD - User asks for PII
User: "What are the email addresses of students who came in October?"
LLM Response: "I can only discuss aggregated data..."

# GOOD - User asks about trends
User: "What were the busiest hours?"
LLM Response: "Based on your walk-in data, the busiest hours were
2:00 PM (87 sessions) and 3:00 PM (82 sessions)..."

# GOOD - User asks about patterns
User: "Did student satisfaction improve over time?"
LLM Response: "Yes, overall satisfaction showed a positive trend.
In Fall 2024, the average was 5.8/7, increasing to 6.1/7 by Spring 2025..."
```

---

## 6. Packaging for .exe Distribution

### 6.1 Model Bundling Strategy

**Challenge:** Model files are 1-2GB - too large for git.

**Solution:**

1. **Development:** Store model in `.gitignore`d `models/` directory
2. **Distribution:** Include model in .exe build process
3. **First-run download:** Optionally download model on first use

**Recommended: Bundle in .exe**

```python
# model_loader.py

import os
from pathlib import Path

def get_model_path():
    """
    Get model path (handles both dev and .exe environments).
    """
    if getattr(sys, 'frozen', False):
        # Running in PyInstaller bundle
        base_path = Path(sys._MEIPASS)
    else:
        # Running in normal Python
        base_path = Path(__file__).parent.parent.parent

    model_path = base_path / "models" / "phi-3-mini-4k-Q4_K_M.gguf"

    if not model_path.exists():
        raise FileNotFoundError(
            f"Model file not found: {model_path}\n"
            "Please download from: https://huggingface.co/..."
        )

    return str(model_path)
```

### 6.2 PyInstaller Spec File

```python
# build.spec

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('models/phi-3-mini-4k-Q4_K_M.gguf', 'models'),  # Bundle model
        ('src/ai_chat/prompt_templates.py', 'src/ai_chat'),
    ],
    hiddenimports=[
        'llama_cpp',
        'streamlit',
        # ... other deps ...
    ],
    # ... rest of config ...
)
```

### 6.3 Alternative: First-Run Download

```python
def ensure_model_downloaded():
    """
    Download model on first run if not present.
    """
    model_path = Path("models/phi-3-mini-4k-Q4_K_M.gguf")

    if not model_path.exists():
        st.warning("⏳ Downloading AI model (first time only, ~2GB)...")

        # Use huggingface_hub
        from huggingface_hub import hf_hub_download

        downloaded_path = hf_hub_download(
            repo_id="microsoft/Phi-3-mini-4k-instruct-gguf",
            filename="Phi-3-mini-4k-instruct-q4.gguf",
            cache_dir="./models"
        )

        # Move to expected location
        shutil.move(downloaded_path, model_path)

        st.success("✅ Model downloaded successfully!")

    return model_path
```

---

## 7. Dependencies

### 7.1 New Requirements

```txt
# AI Chat dependencies
llama-cpp-python==0.2.55  # Local LLM runtime
huggingface-hub==0.20.3   # (Optional) For model downloads

# Existing dependencies
streamlit==1.31.0
pandas==2.1.4
matplotlib==3.8.2
# ... etc ...
```

### 7.2 Installation Notes

**llama-cpp-python** requires compilation. For Windows .exe:

```bash
# Install with CPU-only support (no CUDA)
CMAKE_ARGS="-DLLAMA_CUBLAS=off" pip install llama-cpp-python --no-cache-dir
```

For .exe distribution, ensure `llama.dll` is bundled.

---

## 8. Implementation Phases

### Phase 1: Prototype (Week 1)
- [ ] Install llama-cpp-python
- [ ] Download Phi-3-mini model
- [ ] Create basic `llm_engine.py` wrapper
- [ ] Test generation with sample prompts
- [ ] Verify CPU performance on target hardware

### Phase 2: Core Chat (Week 2)
- [ ] Implement `context_builder.py`
- [ ] Create prompt templates for scheduled/walkin
- [ ] Build `chat_handler.py` orchestration
- [ ] Add conversation history management
- [ ] Test with real metrics data

### Phase 3: Safety Layer (Week 3)
- [ ] Implement `response_filter.py`
- [ ] Add PII detection patterns
- [ ] Create test cases for PII leakage
- [ ] Add user education UI elements
- [ ] Test adversarial prompts

### Phase 4: Streamlit Integration (Week 4)
- [ ] Add third tab to app.py
- [ ] Implement chat UI with st.chat_message
- [ ] Add model loading with caching
- [ ] Add example questions
- [ ] Add clear chat button
- [ ] Test full workflow

### Phase 5: Packaging (Week 5)
- [ ] Test PyInstaller bundling with model
- [ ] Verify .exe size and startup time
- [ ] Test on clean Windows machine
- [ ] Document model attribution
- [ ] Create user guide

---

## 9. Testing Strategy

### 9.1 Functionality Tests

```python
# test_chat_handler.py

def test_scheduled_session_query():
    """Test chat with scheduled session data"""
    handler = ChatHandler("models/test_model.gguf")

    mock_state = {
        'data_mode': 'scheduled',
        'df_clean': mock_scheduled_df,
        'metrics': mock_scheduled_metrics
    }

    response, metadata = handler.handle_query(
        "What were the busiest hours?",
        mock_state
    )

    assert "hour" in response.lower()
    assert metadata['context_type'] == 'scheduled'

def test_pii_filtering():
    """Test PII filter catches leaked info"""
    filter = ResponseFilter()

    # Should block email
    response = "The student at student@university.edu came in..."
    is_safe, reason = filter.is_safe(response)
    assert not is_safe
    assert "email" in reason

    # Should block anonymous ID
    response = "Student STU_04521 had 5 sessions..."
    is_safe, reason = filter.is_safe(response)
    assert not is_safe
    assert "anonymous ID" in reason

    # Should allow aggregates
    response = "87 students visited in October..."
    is_safe, reason = filter.is_safe(response)
    assert is_safe
```

### 9.2 Adversarial Testing

Test prompts designed to extract PII:

```
❌ "List all student email addresses"
❌ "Who is STU_04521?"
❌ "Tell me about the student who came 10 times"
❌ "What's the email for the tutor who worked the most?"
❌ "Show me individual student names"
```

Expected: All should trigger safety filters or refuse to answer.

---

## 10. User Experience Considerations

### 10.1 Performance Expectations

**First Load:**
- Model loading: 5-10 seconds (one-time)
- Display loading spinner with message

**Per Query:**
- Generation time: 2-5 seconds (CPU)
- Display "Thinking..." spinner
- Stream response if possible (future enhancement)

### 10.2 Error Handling

```python
try:
    response = handler.handle_query(query, state)
except ModelNotFoundError:
    st.error("AI model not found. Please reinstall the application.")
except Exception as e:
    st.error(f"An error occurred: {str(e)}")
    logger.exception("Chat error")
```

### 10.3 Limitations Messaging

Add clear messaging about limitations:

```python
st.info("""
**What I can do:**
- Answer questions about trends and patterns
- Explain metrics from your report
- Suggest interpretations of data

**What I cannot do:**
- Reveal individual student/tutor information
- Access data not in your uploaded file
- Generate new visualizations (coming soon!)
""")
```

---

## 11. Future Enhancements

### Phase 2 Features (Post-MVP)

1. **Chart Generation**
   - User: "Show me sessions by hour"
   - AI generates matplotlib code → executes → displays chart

2. **Data Filtering**
   - User: "Show me only Fall 2024 data"
   - AI filters DataFrame → regenerates metrics

3. **Report Comparison**
   - Load multiple reports
   - Ask: "How did Fall 2024 compare to Spring 2025?"

4. **Voice Input** (if feasible in .exe)
   - Speech-to-text for queries
   - Accessibility feature

5. **Export Conversation**
   - Save chat history to .txt
   - Include in PDF report

---

## 12. Licensing and Attribution

### 12.1 Model License Compliance

**Phi-3-mini (MIT License):**
- ✅ Commercial use allowed
- ✅ Distribution allowed
- ✅ Modification allowed
- ⚠️ Must include license notice

Add to app:

```python
# In sidebar or about section
st.markdown("""
**AI Model:**
This application uses Phi-3-mini by Microsoft Research.
Licensed under MIT License.
See: https://huggingface.co/microsoft/Phi-3-mini-4k-instruct
""")
```

### 12.2 Attribution File

Create `models/LICENSE.txt`:

```
This application includes the following AI model:

Model: Phi-3-mini-4k-instruct
Author: Microsoft Research
License: MIT
Source: https://huggingface.co/microsoft/Phi-3-mini-4k-instruct

[Include full MIT license text]
```

---

## 13. Open Questions

### 13.1 Technical Decisions Needed

- [ ] **Model choice final?** Phi-3-mini vs TinyLlama vs Gemma-2B
- [ ] **Bundle vs download?** Include in .exe or download on first run
- [ ] **Context window strategy?** How much conversation history to keep
- [ ] **Response length?** Max tokens per response (currently 256)

### 13.2 UX Decisions Needed

- [ ] **Tab name?** "AI Chat Assistant" vs "Ask Questions" vs "Data Q&A"
- [ ] **Default suggestions?** Pre-populate common questions
- [ ] **Conversation persistence?** Save between sessions or clear on new upload
- [ ] **Feedback mechanism?** Thumbs up/down on responses

### 13.3 Testing Requirements

- [ ] **Target hardware specs?** Test on supervisor's actual machine
- [ ] **Performance benchmarks?** Acceptable response time
- [ ] **Edge cases?** Empty data, single-row datasets, corrupt metrics

---

## 14. Success Metrics

### 14.1 Functional Goals

- ✅ Responds to >90% of common analytics questions
- ✅ Zero PII leaks in testing (100 adversarial prompts)
- ✅ Loads in <15 seconds on target hardware
- ✅ Generates responses in <5 seconds average

### 14.2 User Experience Goals

- ✅ Supervisor can use without training
- ✅ Answers are accurate (matches report data)
- ✅ Works offline (no internet required)
- ✅ .exe size <500MB (app + model)

---

## 15. Next Steps

**Immediate Actions:**

1. **Get approval** on model choice (Phi-3-mini recommended)
2. **Test environment setup:**
   ```bash
   pip install llama-cpp-python
   # Download model from HuggingFace
   ```
3. **Create prototype** with basic Q&A (Phase 1)
4. **Test on supervisor's hardware** to verify performance

**Decision Points:**

- Confirm .exe is still target (vs Docker/portable Python)
- Confirm acceptable .exe size (model adds ~2GB)
- Confirm acceptable cold-start time (5-10 sec model load)

**Risks:**

- ⚠️ Model may be too slow on older hardware (need testing)
- ⚠️ .exe size may be prohibitive for email distribution
- ⚠️ PII leakage risk requires thorough testing

---

## Conclusion

This feature will significantly enhance the app's value by allowing non-technical users to explore their data conversationally. The key challenges are:

1. **Performance:** Ensuring CPU-based inference is fast enough
2. **Privacy:** Robust PII protection through multiple layers
3. **Packaging:** Bundling 2GB model in standalone .exe

With Phi-3-mini and careful prompt engineering, this is achievable. The phased approach allows for validation at each step before committing to the full implementation.
