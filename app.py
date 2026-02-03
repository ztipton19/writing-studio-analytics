# app.py - Writing Studio Analytics Streamlit App

import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime

from src.core.data_cleaner import clean_data, detect_session_type
from src.core.privacy import anonymize_with_codebook, lookup_in_codebook, get_codebook_info
from src.core.metrics import calculate_all_metrics
from src.core.walkin_metrics import calculate_all_metrics as calculate_walkin_metrics
from src.visualizations.report_generator import generate_full_report


def calculate_and_store_metrics(df_clean, data_mode):
    """Calculate metrics from cleaned DataFrame for AI Chat."""
    try:
        if data_mode == 'walkin':
            # Use walk-in specific metrics
            metrics_dict = calculate_walkin_metrics(df_clean)
        else:
            # Use scheduled session metrics
            metrics_dict = calculate_all_metrics(df_clean)
        return metrics_dict
    except Exception as e:
        print(f"Error calculating metrics: {e}")
        return {'total_sessions': len(df_clean) if df_clean is not None else 0}

# AI Chat imports
AI_CHAT_AVAILABLE = False
try:
    from src.ai_chat.chat_handler import ChatHandler
    from src.ai_chat.setup_model import get_model_path
    AI_CHAT_AVAILABLE = True
    print("✅ AI Chat modules loaded successfully")
except ImportError as e:
    AI_CHAT_AVAILABLE = False
    print(f"⚠️ AI Chat disabled: {e}")

# Model download configuration
MODEL_DOWNLOAD_URL = "https://ws-analytics-chatbot.s3.us-east-2.amazonaws.com/gemma-3-4b-it-q4_0.gguf"
MODEL_FILENAME = "gemma-3-4b-it-q4_0.gguf"
MODEL_DIR = "models"

# Walk-in specific imports
WALKIN_AVAILABLE = False
try:
    from src.core.walkin_cleaner import clean_walkin_data
    from src.visualizations.walkin_report_generator import generate_walkin_report
    WALKIN_AVAILABLE = True
    # We use st.write/st.sidebar for Streamlit visibility, or print for terminal
    print("✅ Walk-in modules successfully loaded from src/")
except ImportError as e:
    # This only triggers if BOTH fail
    WALKIN_AVAILABLE = False
    print(f"⚠️ Walk-in analysis disabled: {e}")


# ============================================================================
# PAGE CONFIG
# ============================================================================

st.set_page_config(
    page_title="Writing Studio Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ============================================================================
# SIDEBAR
# ============================================================================

st.sidebar.title("📊 Writing Studio Analytics")
st.sidebar.markdown("---")
st.sidebar.info(
    "**Privacy-First Analytics Tool**\n\n"
    "Generate comprehensive reports from Penji."
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    "**About This Tool**\n\n"
    "Built for University of Arkansas Writing Studio. "
    "Generates FERPA-compliant analytics reports with optional "
    "encrypted reverse-lookup capability.\n\n"
    "Created by Zachary Tipton (Graduate Assistant)"
)


# ============================================================================
# AI MODEL DOWNLOAD HELPER
# ============================================================================

def _model_file_exists() -> bool:
    """Check if the AI model file is present in the models directory."""
    model_path = os.path.join(MODEL_DIR, MODEL_FILENAME)
    return os.path.isfile(model_path)


def render_model_download_ui():
    """Show a user-friendly download interface when the AI model is missing."""
    st.header("🤖 AI Chat Assistant")
    st.info(
        "The AI Chat feature requires a language model file (~3 GB) that isn't "
        "included in the default install. You can download it below — this is a "
        "one-time setup."
    )

    st.markdown(
        f"**Model:** `{MODEL_FILENAME}`  \n"
        f"**Destination:** `{os.path.abspath(MODEL_DIR)}`  \n"
        f"**Size:** ~3 GB"
    )

    if st.button("Download AI Model"):
        import requests
        os.makedirs(MODEL_DIR, exist_ok=True)
        dest_path = os.path.join(MODEL_DIR, MODEL_FILENAME)
        try:
            with requests.get(MODEL_DOWNLOAD_URL, stream=True, timeout=30) as r:
                r.raise_for_status()
                total = int(r.headers.get("content-length", 0))
                progress_bar = st.progress(0, text="Starting download...")
                downloaded = 0
                with open(dest_path, "wb") as f:
                    for chunk in r.iter_content(chunk_size=8 * 1024 * 1024):
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total:
                            pct = downloaded / total
                            progress_bar.progress(
                                pct,
                                text=f"Downloading... {downloaded / (1024**3):.2f} / {total / (1024**3):.2f} GB"
                            )
                progress_bar.progress(1.0, text="Download complete!")
            st.success("Model downloaded successfully! Reloading...")
            st.rerun()
        except Exception as e:
            # Clean up partial download
            if os.path.exists(dest_path):
                os.remove(dest_path)
            st.error(f"Download failed: {e}")
            st.markdown(
                "You can also download the file manually and place it in the "
                f"`{os.path.abspath(MODEL_DIR)}` folder:\n\n"
                f"[Direct download link]({MODEL_DOWNLOAD_URL})"
            )


# ============================================================================
# AI CHAT TAB FUNCTION (defined before use)
# ============================================================================

def render_ai_chat_tab():
    """Render AI chat interface."""
    st.header("🤖 AI Chat Assistant")
    
    st.info(
        "Ask questions about your data! I can help you understand patterns, "
        "trends, and insights. Note: I only discuss aggregated data to protect privacy."
    )
    
    # Check if data is available
    if 'df_clean' not in st.session_state:
        st.warning(
            "⚠️ No data available. Please generate a report in **Generate Report** tab first."
        )
        return
    
    # Initialize chat handler
    if 'chat_handler' not in st.session_state:
        with st.spinner("Loading AI model (first time only)..."):
            try:
                model_path = get_model_path()
                st.session_state.chat_handler = ChatHandler(model_path, verbose=False, enable_code_execution=True)
                st.session_state.chat_messages = []
                
                # Initialize code executor with data if available
                if 'df_clean' in st.session_state:
                    st.session_state.chat_handler.set_data_for_code_execution(st.session_state['df_clean'])
                
                # Show system info
                sys_info = st.session_state.chat_handler.check_system()
                with st.expander("💻 System Information"):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write(f"- **RAM**: {sys_info['ram_gb']} GB")
                        st.write(f"- **GPU**: {sys_info['gpu_acceleration']}")
                    with col2:
                        st.write(f"- **CPU Threads**: {sys_info['cpu_threads']}")
                        st.write(f"- **RAM Sufficient**: {'✅ Yes' if sys_info['ram_sufficient'] else '⚠️ No (may be slow)'}")
                
                st.success("✅ AI model loaded successfully!")
            except Exception as e:
                st.error(f"❌ Error loading AI model: {str(e)}")
                st.info("💡 Make sure you've downloaded the model by running: `python src/ai_chat/setup_model.py`")
                return
    else:
        # Chat handler exists - check if code executor needs data
        if 'df_clean' in st.session_state:
            try:
                # Check if code executor is initialized
                if st.session_state.chat_handler.code_executor is None:
                    st.session_state.chat_handler.set_data_for_code_execution(st.session_state['df_clean'])
            except Exception as e:
                st.warning(f"⚠️ Could not initialize code executor: {e}")
    
    # Display chat history
    if 'chat_messages' in st.session_state:
        for message in st.session_state.chat_messages:
            with st.chat_message(message['role']):
                st.write(message['content'])
    
    # Chat input
    if prompt := st.chat_input("Ask a question about your data..."):
        # Add user message to history
        st.session_state.chat_messages.append({
            'role': 'user',
            'content': prompt
        })
        
        # Generate response with progress tracking
        with st.chat_message("assistant"):
            with st.status("Processing your question...", expanded=True) as status:
                try:
                    # Get data from session state
                    df_clean = st.session_state.get('df_clean')
                    metrics = st.session_state.get('metrics', {})
                    data_mode = st.session_state.get('data_mode', 'scheduled')
                    
                    if df_clean is None:
                        st.error("❌ No data available. Please generate a report first.")
                        response = "I don't have any data to analyze yet. Please generate a report first."
                        status.update(label="❌ No data available", state="error")
                    elif not metrics:
                        st.error("❌ No metrics available.")
                        response = "I don't have metrics data yet. Please generate a report first."
                        status.update(label="❌ No metrics available", state="error")
                    else:
                        # Update status to show we're processing
                        status.update(label="🔍 Checking pre-computed metrics...", state="running")
                        
                        response, metadata = st.session_state.chat_handler.handle_query(
                            prompt,
                            df_clean,
                            metrics,
                            data_mode
                        )
                        
                        # Final status based on what was used
                        if metadata.get('pii_filtered'):
                            status.update(label="✅ Answered (filtered for privacy)", state="complete")
                        else:
                            status.update(label="✅ Answer complete", state="complete")
                        
                        st.write(response)
                except Exception as e:
                    import traceback
                    st.error(f"❌ Error: {str(e)}")
                    with st.expander("🔍 Error Details"):
                        st.code(traceback.format_exc())
                    response = f"I encountered an error: {str(e)}. Please try again."
                    status.update(label="❌ Error occurred", state="error")
        
        # Add assistant message to history
        st.session_state.chat_messages.append({
            'role': 'assistant',
            'content': response
        })
        
        # Rerun to display all messages above the input box
        st.rerun()
    
    # Helpful suggestions
    with st.expander("💡 Example Questions"):
        session_type = st.session_state.get('data_mode', 'scheduled')
        
        if session_type == 'scheduled':
            st.markdown("""
            **Scheduled Sessions:**
            - What were the busiest days of the week?
            - How did student satisfaction change over time?
            - Which writing stages were most common?
            - What was the average booking lead time?
            """)
        else:
            st.markdown("""
            **Walk-In Sessions:**
            - What were the peak hours for walk-ins?
            - How many students used the space independently?
            - What was the average session duration?
            - Which courses were most common?
            """)
    
    # Clear chat button
    if st.button("🗑️ Clear Chat History"):
        if 'chat_handler' in st.session_state:
            st.session_state.chat_handler.clear_history()
        st.session_state.chat_messages = []
        st.rerun()
    
    # Model info
    st.markdown("---")
    st.caption(
        "🤖 Powered by Gemma 3 4B (Google) - Local-only inference, no cloud APIs"
    )


# ============================================================================
# COLUMN MAPPING HELPERS
# ============================================================================

MAPPING_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'column_mapping.json')


def load_column_mapping():
    """Load column mapping config from JSON."""
    try:
        with open(MAPPING_PATH, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"scheduled": [], "walkin": []}


def save_column_mapping(mapping):
    """Write updated column mapping back to JSON."""
    with open(MAPPING_PATH, 'w') as f:
        json.dump(mapping, f, indent=2)


def validate_columns(df, session_type):
    """
    Check which expected columns are present in the uploaded CSV.
    Returns list of dicts — each entry from the mapping plus 'found' and 'found_as'.
    """
    mapping = load_column_mapping()
    entries = mapping.get(session_type, [])
    results = []
    for entry in entries:
        source = entry['source']
        aliases = entry.get('aliases', [])
        if source in df.columns:
            results.append({**entry, 'found': True, 'found_as': source})
        else:
            matched_alias = next((a for a in aliases if a in df.columns), None)
            results.append({**entry, 'found': bool(matched_alias), 'found_as': matched_alias})
    return results


def normalize_columns(df, session_type):
    """
    Rename columns in the uploaded CSV so they match what the app code expects.
    For each mapping entry: source → target.
    Aliases are also handled: if source is missing but an alias is present,
    the alias gets renamed to target instead.
    This runs ONCE before anonymization/cleaning so all downstream code
    works unchanged regardless of what Penji called the columns.
    """
    mapping = load_column_mapping()
    entries = mapping.get(session_type, [])
    rename_dict = {}
    for entry in entries:
        target = entry['target']
        source = entry['source']
        aliases = entry.get('aliases', [])
        if source in df.columns:
            if source != target:
                rename_dict[source] = target
        else:
            for alias in aliases:
                if alias in df.columns:
                    if alias != target:
                        rename_dict[alias] = target
                    break
    return df.rename(columns=rename_dict)


# ============================================================================
# MAIN APP - TABS
# ============================================================================

tab1, tab2, tab3, tab4 = st.tabs(["📊 Generate Report", "🔍 Codebook Lookup", "🤖 AI Chat Assistant", "🗺️ Column Mapping"])


# ============================================================================
# TAB 1: GENERATE REPORT
# ============================================================================

with tab1:
    st.header("📊 Generate Analytics Report")
    
    st.markdown("""
    Upload your Penji export file to generate a comprehensive analytics report with:
    - Session volume trends and patterns
    - Booking behavior analysis  
    - Student satisfaction metrics
    - Tutor workload distribution
    - And much more!
    """)
    
    st.markdown("---")
    
    # ========================================================================
    # STEP 1: SESSION TYPE SELECTION
    # ========================================================================
    
    st.subheader("Step 1: Select Session Type")
    
    # Check if walk-in modules are available
    walkin_options = ["40-Minute Sessions (Scheduled)", "Walk-In Sessions"] if WALKIN_AVAILABLE else ["40-Minute Sessions (Scheduled)"]
    
    session_mode = st.radio(
        "What type of sessions are you analyzing?",
        options=walkin_options,
        index=0,
        help="Select the type of data you're uploading. The tool will adjust its analysis accordingly."
    )
    
    if not WALKIN_AVAILABLE and session_mode != "40-Minute Sessions (Scheduled)":
        st.error("❌ Walk-in modules not installed. Contact system administrator.")
        st.stop()
    
    # Convert to internal format
    if session_mode == "40-Minute Sessions (Scheduled)":
        expected_mode = 'scheduled'
        st.info("📅 **Scheduled Sessions**: Pre-booked 40-minute appointments with full survey data")
    else:
        expected_mode = 'walkin'
        st.warning("🚶 **Walk-In Sessions**: Drop-in visits with variable duration, minimal survey data")
    
    st.markdown("---")
    
    # ========================================================================
    # STEP 2: FILE UPLOAD
    # ========================================================================
    
    st.subheader("Step 2: Upload Data File")
    
    uploaded_file = st.file_uploader(
        "Choose your Penji export file",
        type=['xlsx', 'xls', 'csv'],
        help="Upload CSV or Excel file exported from Penji"
    )
    
    if uploaded_file is not None:
        # Load data
        try:
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            # Auto-detect session type
            detected_type = detect_session_type(df)
            
            # Show file info
            st.success(f"✅ File loaded: {len(df):,} rows × {len(df.columns)} columns")
            
            # Warn if mismatch
            if detected_type != expected_mode and detected_type != 'unknown':
                st.warning(
                    f"⚠️ **Type Mismatch Detected!**\n\n"
                    f"You selected **{session_mode}** but the file appears to contain "
                    f"**{'scheduled' if detected_type == 'scheduled' else 'walk-in'}** sessions.\n\n"
                    f"Please switch the radio button above or upload the correct file."
                )
                st.stop()

            # ============================================================
            # COLUMN VALIDATION + NORMALIZE
            # ============================================================

            column_validation = validate_columns(df, expected_mode)
            st.session_state['column_validation'] = column_validation
            st.session_state['uploaded_columns'] = list(df.columns)
            st.session_state['expected_mode'] = expected_mode

            missing_cols = [r for r in column_validation if not r['found']]
            if missing_cols:
                st.warning(
                    f"⚠️ {len(missing_cols)} column(s) not matched in your file. "
                    f"The report will skip those sections. "
                    f"See the **Column Mapping** tab to fix."
                )

            # Normalize: rename CSV columns → what the app expects internally
            df = normalize_columns(df, expected_mode)

            # Show preview
            with st.expander("📋 Data Summary"):
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("**📅 Date Information:**")
                    date_col = None
                    if 'Requested At Date' in df.columns:
                        date_col = 'Requested At Date'
                    elif 'Check In At Date' in df.columns:
                        date_col = 'Check In At Date'
                    
                    if date_col:
                        dates = pd.to_datetime(df[date_col], errors='coerce')
                        st.write(f"- First session: {dates.min().strftime('%B %d, %Y')}")
                        st.write(f"- Last session: {dates.max().strftime('%B %d, %Y')}")
                        st.write(f"- Span: {(dates.max() - dates.min()).days} days")

                    st.markdown("**📊 Session Statistics:**")
                    
                    # For walk-in data, use Status field
                    if expected_mode == 'walkin' and 'Status' in df.columns:
                        status_counts = df['Status'].value_counts()
                        for status, count in status_counts.items():
                            pct = (count / len(df)) * 100
                            st.write(f"- {status}: {count:,} ({pct:.1f}%)")
                    else:
                        # For scheduled sessions, use Attendance_Status
                        if 'Student Attendance' in df.columns:
                            attendance_col = 'Student Attendance'
                        elif 'Attendance_Status' in df.columns:
                            attendance_col = 'Attendance_Status'
                        else:
                            attendance_col = None

                        if attendance_col:
                            # Count Present (Completed), Absent (No-shows)
                            completed = df[attendance_col].str.lower().str.contains('present', na=False).sum()
                            no_show = df[attendance_col].str.lower().str.contains('absent', na=False).sum()

                            completed_pct = (completed / len(df)) * 100
                            no_show_pct = (no_show / len(df)) * 100

                            st.write(f"- Completed: {completed:,} ({completed_pct:.1f}%)")
                            st.write(f"- Absent (no-show): {no_show:,} ({no_show_pct:.1f}%)")

                        # Count cancellations from Status column
                        if 'Status' in df.columns:
                            cancelled = df['Status'].str.lower().str.contains('cancel', na=False).sum()
                            cancelled_pct = (cancelled / len(df)) * 100
                            st.write(f"- Cancelled: {cancelled:,} ({cancelled_pct:.1f}%)")

                with col2:
                    st.markdown("**👥 Participation:**")
                    # Count unique tutors by email
                    if 'Tutor Email' in df.columns:
                        unique_tutors = df['Tutor Email'].nunique()
                        st.write(f"- Unique tutors: {unique_tutors}")

                    # Count unique students by email
                    if 'Student Email' in df.columns:
                        unique_students = df['Student Email'].nunique()
                        st.write(f"- Unique students: {unique_students}")

                    # Count total sessions
                    if 'Unique ID' in df.columns:
                        unique_sessions = df['Unique ID'].nunique()
                        st.write(f"- Total sessions: {unique_sessions:,}")
                    else:
                        st.write(f"- Total sessions: {len(df):,}")
            
            st.markdown("---")
            
            # ================================================================
            # STEP 3: OPTIONS
            # ================================================================
            
            st.subheader("Step 3: Configure Options")
            
            col1, col2 = st.columns(2)
            
            with col1:
                remove_outliers = st.checkbox(
                    "Remove statistical outliers",
                    value=True,
                    help="Remove extreme session lengths using IQR method (e.g., 23-hour sessions from forgot-to-close)"
                )
                
                if remove_outliers:
                    st.caption("✓ Will use IQR method to filter outliers")
                else:
                    st.caption("⚠️ Raw data will be used (may skew statistics)")
            
            with col2:
                create_codebook = st.checkbox(
                    "Generate codebook (supervisor access)",
                    value=True,
                    help="Creates encrypted lookup table for reversing anonymous IDs back to emails"
                )
                
                if create_codebook:
                    st.caption("✓ Enables investigation of specific students/tutors")
                else:
                    st.caption("ℹ️ Anonymous IDs cannot be reversed")
            
            # ================================================================
            # STEP 4: CODEBOOK PASSWORD (if enabled)
            # ================================================================

            password = None
            confirm_password = None
            password_valid = False

            # Initialize password key counter in session state
            if 'password_key_counter' not in st.session_state:
                st.session_state['password_key_counter'] = 0

            if create_codebook:
                st.markdown("---")
                st.subheader("Step 4: Set Codebook Password")

                st.info(
                    "🔐 Set a strong password to encrypt the codebook. "
                    "You'll need this password later to look up anonymous IDs."
                )

                col1, col2 = st.columns(2)

                with col1:
                    password = st.text_input(
                        "Password (12+ characters)",
                        type="password",
                        help="Choose a strong password - you'll need this for lookups!",
                        key=f"password_{st.session_state['password_key_counter']}"
                    )

                with col2:
                    confirm_password = st.text_input(
                        "Confirm Password",
                        type="password",
                        key=f"confirm_password_{st.session_state['password_key_counter']}"
                    )

                # Password validation
                if password or confirm_password:
                    if not password or not confirm_password:
                        st.warning("⚠️ Please enter password in both fields")
                    elif password != confirm_password:
                        st.error("❌ Passwords do not match!")
                    elif len(password) < 12:
                        st.warning(f"⚠️ Password too short ({len(password)}/12 characters)")
                    else:
                        st.success("✅ Password validated")
                        password_valid = True
            else:
                password_valid = True  # No password needed if no codebook
            
            st.markdown("---")
            
            # ================================================================
            # STEP 5: GENERATE REPORT
            # ================================================================
            
            st.subheader("Step 5: Generate Report")
            
            # Show what will be generated
            st.markdown("**Your report will include:**")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("📄 **PDF Report**\n- Anonymized charts\n- Safe to share publicly")
            with col2:
                st.markdown("📊 **Cleaned CSV**\n- Anonymized dataset\n- Ready for analysis")
            with col3:
                if create_codebook:
                    st.markdown("🔐 **Codebook**\n- Encrypted mapping\n- Supervisor only!")
                else:
                    st.markdown("ℹ️ **No Codebook**\n- IDs cannot be\n- reversed")
            
            # Generate button
            can_generate = password_valid
            
            if not can_generate and create_codebook:
                st.warning("⚠️ Please set a valid password before generating")
            
            if st.button(
                "🚀 Generate Report",
                type="primary",
                use_container_width=True,
                disabled=not can_generate
            ):
                # Progress tracking
                progress_bar = st.progress(0)
                status_text = st.empty()

                try:
                    # Step 1: Anonymize
                    status_text.text("🔒 Step 1/4: Anonymizing data...")
                    progress_bar.progress(25)

                    df_anon, codebook_path, anon_log = anonymize_with_codebook(
                        df,
                        create_codebook=create_codebook,
                        password=password if create_codebook else None,
                        confirm_password=confirm_password if create_codebook else None,
                        session_type=expected_mode  # Pass session type for codebook metadata
                    )

                    # Step 2: Clean
                    status_text.text("🧹 Step 2/4: Cleaning and processing...")
                    progress_bar.progress(50)

                    if expected_mode == 'walkin':
                        # Use walk-in specific cleaner
                        if not WALKIN_AVAILABLE:
                            st.error("❌ Walk-in modules not available. Please check installation.")
                            st.stop()

                        df_clean, cleaning_log = clean_walkin_data(df_anon)
                    else:
                        # Use scheduled session cleaner
                        df_clean, cleaning_log = clean_data(
                            df_anon,
                            mode=expected_mode,
                            remove_outliers=remove_outliers,
                            log_actions=False
                        )

                    # Step 3: Generate report
                    status_text.text("📊 Step 3/4: Creating visualizations...")
                    progress_bar.progress(75)

                    timestamp = datetime.now().strftime('%Y-%m-%d-%H%M')
                    
                    if expected_mode == 'walkin':
                        report_filename = f"WS_Analytics_WalkIns_{timestamp}.pdf"
                        report_path = generate_walkin_report(df_clean, cleaning_log, report_filename)
                    else:
                        report_filename = f"WS_Analytics_Sessions_{timestamp}.pdf"
                        report_path = generate_full_report(df_clean, cleaning_log, report_filename)

                    # Step 4: Save CSV
                    status_text.text("💾 Step 4/4: Finalizing outputs...")
                    progress_bar.progress(90)

                    csv_filename = f"cleaned_data_{timestamp}.csv"
                    df_clean.to_csv(csv_filename, index=False)

                    # Load files into memory for persistent downloads
                    with open(report_path, 'rb') as f:
                        pdf_data = f.read()
                    with open(csv_filename, 'rb') as f:
                        csv_data = f.read()
                    codebook_data = None
                    if create_codebook and codebook_path:
                        with open(codebook_path, 'rb') as f:
                            codebook_data = f.read()

                    # Store in session state to persist across reruns
                    st.session_state['pdf_data'] = pdf_data
                    st.session_state['pdf_filename'] = report_filename
                    st.session_state['csv_data'] = csv_data
                    st.session_state['csv_filename'] = csv_filename
                    st.session_state['codebook_data'] = codebook_data
                    st.session_state['codebook_filename'] = os.path.basename(codebook_path) if codebook_path else None
                    st.session_state['cleaning_log'] = cleaning_log
                    st.session_state['anon_log'] = anon_log
                    st.session_state['create_codebook'] = create_codebook
                    
                    # Store for AI Chat access
                    st.session_state['df_clean'] = df_clean
                    st.session_state['metrics'] = calculate_and_store_metrics(df_clean, expected_mode)
                    st.session_state['data_mode'] = expected_mode

                    # Increment password key counter to clear password fields on next rerun
                    st.session_state['password_key_counter'] += 1

                    # Cleanup temp files immediately after reading into memory
                    try:
                        if os.path.exists(report_path):
                            os.remove(report_path)
                        if os.path.exists(csv_filename):
                            os.remove(csv_filename)
                        if codebook_path and os.path.exists(codebook_path):
                            os.remove(codebook_path)
                    except OSError as e:
                        print(f"Cleanup failed: {e}")
                        pass

                    progress_bar.progress(100)
                    status_text.empty()

                    # Success!
                    st.success("🎉 Report generated successfully!")

                except Exception as e:
                    st.error(f"❌ Error generating report: {str(e)}")
                    progress_bar.empty()
                    status_text.empty()

                    # Show detailed error in expander
                    with st.expander("🔍 Error Details"):
                        import traceback
                        st.code(traceback.format_exc())

            # ========================================================
            # DOWNLOAD SECTION (persists across reruns)
            # ========================================================

            if 'pdf_data' in st.session_state:
                st.markdown("---")
                st.subheader("📥 Download Your Files")

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.download_button(
                        label="📄 Download Report (PDF)",
                        data=st.session_state['pdf_data'],
                        file_name=st.session_state['pdf_filename'],
                        mime="application/pdf",
                        use_container_width=True
                    )
                    st.caption("✅ Safe to share publicly")

                with col2:
                    st.download_button(
                        label="📊 Download Cleaned Data (CSV)",
                        data=st.session_state['csv_data'],
                        file_name=st.session_state['csv_filename'],
                        mime="text/csv",
                        use_container_width=True
                    )
                    st.caption("✅ Anonymized dataset")

                with col3:
                    if st.session_state['codebook_data']:
                        st.download_button(
                            label="🔐 Download Codebook",
                            data=st.session_state['codebook_data'],
                            file_name=st.session_state['codebook_filename'],
                            mime="application/octet-stream",
                            use_container_width=True
                        )
                        st.caption("⚠️ Supervisor only!")
                    else:
                        st.button(
                            "ℹ️ No Codebook",
                            use_container_width=True,
                            disabled=True
                        )
                        st.caption("Not generated")

                # ========================================================
                # SUMMARY STATS
                # ========================================================

                st.markdown("---")
                st.subheader("📊 Report Summary for last report generated")

                cleaning_log = st.session_state['cleaning_log']
                anon_log = st.session_state['anon_log']
                create_codebook = st.session_state['create_codebook']

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    total_sessions = cleaning_log.get('final_rows', len(st.session_state.get('df_clean', [])))
                    st.metric("Total Sessions", f"{total_sessions:,}")

                with col2:
                    if 'context' in cleaning_log and 'cancellations' in cleaning_log['context']:
                        rate = cleaning_log['context']['cancellations']['completion_rate']
                        st.metric("Completion Rate", f"{rate:.1f}%")
                    else:
                        st.metric("Completion Rate", "N/A")

                with col3:
                    if create_codebook:
                        st.metric("Tutors", f"{anon_log['tutors_anonymized']}")
                    else:
                        final_cols = cleaning_log.get('final_cols', 'N/A')
                        st.metric("Columns", f"{final_cols}")

                with col4:
                    if 'outliers_removed' in cleaning_log:
                        removed = cleaning_log['outliers_removed']['removed_count']
                        st.metric("Outliers Removed", f"{removed}")
                    else:
                        st.metric("Outliers Removed", "0")

                # Important reminder
                if create_codebook:
                    st.warning(
                        "⚠️ **IMPORTANT**: The codebook file contains sensitive mappings. "
                        "Give this file + password to your supervisor ONLY. "
                        "Do NOT commit to GitHub or share via insecure channels."
                    )
        
        except Exception as e:
            st.error(f"❌ Error loading file: {str(e)}")
            with st.expander("🔍 Error Details"):
                import traceback
                st.code(traceback.format_exc())


# ============================================================================
# TAB 2: CODEBOOK LOOKUP
# ============================================================================

with tab2:
    st.header("🔍 Codebook Lookup")
    
    st.markdown("""
    Use this tool to reverse-lookup anonymized IDs from reports back to email addresses.
    
    **When to use this:**
    - Investigating a specific student or tutor flagged in the report
    - Following up on concerning trends (e.g., declining confidence, high no-shows)
    - Verifying data accuracy for specific cases
    """)
    
    st.markdown("---")
    
    # Upload codebook
    codebook_file = st.file_uploader(
        "Upload Codebook File (.enc)",
        type=['enc'],
        help="Upload the encrypted codebook file generated with your report",
        key="lookup_codebook"
    )
    
    if codebook_file is not None:
        # Save temporarily
        temp_codebook_path = "temp_codebook_lookup.enc"
        with open(temp_codebook_path, 'wb') as f:
            f.write(codebook_file.read())
        
        # Password input
        lookup_password = st.text_input(
            "Codebook Password",
            type="password",
            help="Enter the password you set when generating the report",
            key="lookup_password"
        )
        
        if lookup_password:
            # Test password and show info
            info = get_codebook_info(temp_codebook_path, lookup_password)
            
            if 'error' in info:
                st.error(info['error'])
            else:
                st.success("✅ Codebook unlocked!")
                
                # Show codebook info
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Total Students", f"{info['total_students']:,}")
                    st.metric("Created", info['created'].split('T')[0])
                
                with col2:
                    st.metric("Total Tutors", f"{info['total_tutors']}")
                    st.metric("Date Range", info['date_range'])
                
                st.markdown("---")
                
                # Lookup interface
                st.subheader("Lookup Anonymous ID")
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    anon_id = st.text_input(
                        "Anonymous ID",
                        placeholder="STU_04521 or TUT_0842",
                        help="Enter the anonymous ID from your report",
                        key="anon_id_input"
                    )
                
                with col2:
                    st.markdown("<br>", unsafe_allow_html=True)  # Spacer
                    lookup_button = st.button("🔍 Lookup", use_container_width=True)
                
                if lookup_button:
                    if not anon_id:
                        st.warning("⚠️ Please enter an anonymous ID")
                    else:
                        with st.spinner("Looking up..."):
                            result = lookup_in_codebook(anon_id, temp_codebook_path, lookup_password)
                        
                        if result.startswith('❌'):
                            st.error(result)
                        else:
                            st.success(f"**{anon_id}** → **{result}**")
                            
                            st.info(
                                f"💡 **Next Step**: Search Penji for `{result}` to see "
                                "full session history and contact information."
                            )
        
        # Cleanup
        try:
            if os.path.exists(temp_codebook_path):
                os.remove(temp_codebook_path)
        except OSError as e:
            print(f"Cleanup failed: {e}")
            pass


# ============================================================================
# TAB 3: AI CHAT ASSISTANT
# ============================================================================

with tab3:
    if AI_CHAT_AVAILABLE and _model_file_exists():
        render_ai_chat_tab()
    elif AI_CHAT_AVAILABLE and not _model_file_exists():
        # Library installed but model file missing — offer download
        render_model_download_ui()
    else:
        # Library not installed at all
        st.header("🤖 AI Chat Assistant")
        st.warning(
            "The AI Chat feature requires the `llama-cpp-python` package, "
            "which is not currently installed. Run `pip install llama-cpp-python` "
            "and restart the app to enable this feature."
        )


# ============================================================================
# TAB 4: COLUMN MAPPING
# ============================================================================

with tab4:
    st.header("🗺️ Column Mapping")

    # Toast if we just saved
    if st.session_state.pop('mapping_just_saved', False):
        st.success("✅ Column mapping updated! The next report will use the new column names.")

    if 'column_validation' not in st.session_state:
        st.info(
            "📋 Upload a data file in the **Generate Report** tab first, "
            "then come back here to check column connections."
        )
    else:
        validation = st.session_state['column_validation']
        session_type = st.session_state.get('expected_mode', 'scheduled')
        uploaded_cols = st.session_state.get('uploaded_columns', [])

        connected = [r for r in validation if r['found']]
        missing = [r for r in validation if not r['found']]

        # ── Summary ──────────────────────────────────────────────────────
        if not missing:
            st.success(f"✅ All {len(connected)} columns connected successfully.")
        else:
            st.warning(
                f"⚠️ {len(missing)} column(s) not found in your file. "
                f"The report will skip those sections."
            )

        # ── Missing columns: needs fixing ────────────────────────────────
        if missing:
            st.markdown("### Columns to fix")
            st.caption(
                "Pick the correct column from your uploaded file for each one below, "
                "then click **Save Changes**."
            )

            changes = {}

            # Group missing by category, preserving order
            seen_cats = []
            for r in missing:
                if r['category'] not in seen_cats:
                    seen_cats.append(r['category'])

            for cat in seen_cats:
                cat_items = [r for r in missing if r['category'] == cat]
                st.markdown(f"**{cat}**")

                for entry in cat_items:
                    col1, col2 = st.columns([1, 2])

                    with col1:
                        req_badge = " *(required)*" if entry.get('required') else ""
                        st.markdown(f"❌ **{entry['label']}**{req_badge}")
                        # Show what we were looking for (truncate long names)
                        source_display = entry['source']
                        if len(source_display) > 55:
                            source_display = source_display[:52] + "..."
                        st.caption(f'Looking for: "{source_display}"')

                    with col2:
                        selected = st.selectbox(
                            "Map to column in your file:",
                            options=["— not mapped —"] + sorted(uploaded_cols),
                            key=f"remap_{entry['target']}"
                        )
                        if selected != "— not mapped —":
                            changes[entry['target']] = selected

                st.markdown("")  # spacing between categories

            # Save button — only active when user has picked at least one
            if changes:
                if st.button("💾 Save Changes", type="primary", use_container_width=True):
                    full_mapping = load_column_mapping()
                    for entry in full_mapping[session_type]:
                        if entry['target'] in changes:
                            entry['source'] = changes[entry['target']]
                    save_column_mapping(full_mapping)
                    st.session_state['mapping_just_saved'] = True
                    st.rerun()
            else:
                st.info("Select a column from the dropdowns above to enable Save.")

        # ── Connected columns: expandable detail ─────────────────────────
        with st.expander(f"✅ {len(connected)} columns connected", expanded=False):
            seen_cats = []
            for r in connected:
                if r['category'] not in seen_cats:
                    seen_cats.append(r['category'])

            for cat in seen_cats:
                cat_items = [r for r in connected if r['category'] == cat]
                st.markdown(f"**{cat}**")
                for entry in cat_items:
                    st.markdown(f"  ✅ **{entry['label']}** ← `{entry['found_as']}`")
                st.markdown("")
