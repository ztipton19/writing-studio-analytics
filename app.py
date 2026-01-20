# app.py - Writing Studio Analytics Streamlit App

import streamlit as st
import pandas as pd
import os
from datetime import datetime

from src.core.data_cleaner import clean_data, detect_session_type
from src.core.privacy import anonymize_with_codebook, lookup_in_codebook, get_codebook_info
from src.visualizations.report_generator import generate_full_report

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
# MAIN APP - TABS
# ============================================================================

tab1, tab2 = st.tabs(["📊 Generate Report", "🔍 Codebook Lookup"])


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
            
            if expected_mode == 'walkin':
                st.info(
                    "📊 **Walk-In Report Includes:**\n"
                    "- Consultant workload analysis\n"
                    "- Temporal patterns (peak hours/days)\n"
                    "- Duration analysis by session type\n"
                    "- Independent space usage metrics\n"
                    "- Course distribution"
                )
            
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

                        df_clean = clean_walkin_data(df_anon, cap_duration=True, max_duration_minutes=180)
                        cleaning_log = {
                            'mode': 'walkin',
                            'context': {},
                            'final_rows': len(df_clean),
                            'final_cols': len(df_clean.columns),
                            'original_rows': len(df),
                            'original_cols': len(df.columns)
                        }
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

                    timestamp = datetime.now().strftime('%Y-%m-%d_%H%M%S')
                    
                    if expected_mode == 'walkin':
                        report_filename = f"walkin_report_{timestamp}.pdf"
                        report_path = generate_walkin_report(df_clean, report_filename)
                    else:
                        report_filename = f"writing_studio_report_{timestamp}.pdf"
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