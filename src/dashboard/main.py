# src/dashboard/main.py - Writing Studio Analytics PyQt Dashboard

# CRITICAL: Set matplotlib backend BEFORE any other imports
import matplotlib
matplotlib.use('qtagg')

import sys
import os
from pathlib import Path
import pandas as pd

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
    QFileDialog, QMessageBox, QStatusBar, QMenuBar,
    QLabel, QToolBar, QPushButton, QDialog, QCheckBox, QLineEdit,
    QRadioButton, QButtonGroup, QProgressBar, QFormLayout, QGroupBox,
    QScrollArea, QTextEdit
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon, QFont, QPalette, QColor, QAction

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg

# Application-wide imports
from src.core.data_cleaner import clean_data, detect_session_type
from src.core.privacy import anonymize_with_codebook
from src.core.metrics import calculate_all_metrics
from src.core.walkin_cleaner import clean_walkin_data
from src.core.walkin_metrics import calculate_all_metrics as calculate_walkin_metrics
from src.visualizations.report_generator import generate_full_report
from src.visualizations.walkin_report_generator import generate_walkin_report
from src.visualizations import charts as scheduled_charts
from src.visualizations import walkin_charts
from src.core.privacy import lookup_in_codebook, get_codebook_info
from src.ai_chat.chat_handler import ChatHandler
from src.ai_chat.setup_model import get_model_path, check_system_requirements
from src.utils.audit_logger import audit_event


class ProcessingOptionsDialog(QDialog):
    """Dialog for configuring data processing options."""
    
    def __init__(self, data_mode, parent=None):
        super().__init__(parent)
        self.data_mode = data_mode
        self.config = {}
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Data Processing Options")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout()
        
        # Session Type Info (read-only)
        mode_group = QGroupBox("Session Type (Auto-Detected)")
        mode_layout = QFormLayout()
        
        mode_text = QLabel("Scheduled 40-Minute Sessions" if self.data_mode == 'scheduled' else "Walk-In Sessions")
        mode_text.setStyleSheet("font-weight: bold; color: #2E86AB; font-size: 14px;")
        mode_layout.addRow("Detected Type:", mode_text)
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)
        
        # Processing Options
        options_group = QGroupBox("Processing Options")
        options_layout = QVBoxLayout()
        
        # Remove outliers
        self.remove_outliers_cb = QCheckBox("Remove statistical outliers")
        self.remove_outliers_cb.setChecked(True)
        self.remove_outliers_cb.setToolTip(
            "Remove extreme session lengths using IQR method (e.g., 23-hour sessions from forgot-to-close)"
        )
        options_layout.addWidget(self.remove_outliers_cb)
        
        # Generate codebook
        self.create_codebook_cb = QCheckBox("Generate codebook (supervisor access)")
        self.create_codebook_cb.setChecked(True)
        self.create_codebook_cb.setToolTip(
            "Creates encrypted lookup table for reversing anonymous IDs back to emails"
        )
        self.create_codebook_cb.toggled.connect(self.toggle_password_fields)
        options_layout.addWidget(self.create_codebook_cb)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # Password fields (initially disabled)
        self.password_group = QGroupBox("Codebook Password")
        password_layout = QFormLayout()
        
        self.password_field = QLineEdit()
        self.password_field.setEchoMode(QLineEdit.Password)
        self.password_field.setPlaceholderText("Enter password (12+ characters)")
        self.password_field.textChanged.connect(self.validate_password)
        self.password_field.setEnabled(False)
        password_layout.addRow("Password:", self.password_field)
        
        self.password_valid_label = QLabel("")
        password_layout.addRow("", self.password_valid_label)
        
        self.confirm_field = QLineEdit()
        self.confirm_field.setEchoMode(QLineEdit.Password)
        self.confirm_field.setPlaceholderText("Confirm password")
        self.confirm_field.textChanged.connect(self.validate_password)
        self.confirm_field.setEnabled(False)
        password_layout.addRow("Confirm:", self.confirm_field)
        
        self.match_label = QLabel("")
        password_layout.addRow("", self.match_label)
        
        self.password_group.setLayout(password_layout)
        self.password_group.setEnabled(False)
        layout.addWidget(self.password_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)
        
        self.process_btn = QPushButton("Process Data")
        self.process_btn.setDefault(True)
        self.process_btn.clicked.connect(self.validate_and_accept)
        self.process_btn.setEnabled(False)  # Disabled until valid
        button_layout.addWidget(self.process_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
    def toggle_password_fields(self, checked):
        """Enable/disable password fields based on codebook checkbox."""
        self.password_group.setEnabled(checked)
        if not checked:
            # Clear password fields
            self.password_field.clear()
            self.confirm_field.clear()
            self.password_valid_label.clear()
            self.match_label.clear()
        self.validate_password()
        
    def validate_password(self):
        """Validate password in real-time."""
        password = self.password_field.text()
        confirm = self.confirm_field.text()
        
        # Password length validation
        if len(password) == 0:
            self.password_valid_label.setText("")
            self.password_valid_label.setStyleSheet("")
        elif len(password) < 12:
            self.password_valid_label.setText(" Password must be at least 12 characters")
            self.password_valid_label.setStyleSheet("color: #C73E1D; font-weight: bold;")
        else:
            self.password_valid_label.setText(" Password length OK")
            self.password_valid_label.setStyleSheet("color: #06A77D; font-weight: bold;")
        
        # Password match validation
        if len(confirm) == 0:
            self.match_label.setText("")
            self.match_label.setStyleSheet("")
        elif password != confirm:
            self.match_label.setText(" Passwords do not match")
            self.match_label.setStyleSheet("color: #C73E1D; font-weight: bold;")
        else:
            self.match_label.setText(" Passwords match")
            self.match_label.setStyleSheet("color: #06A77D; font-weight: bold;")
        
        # Enable process button only if valid
        valid = self.is_valid()
        self.process_btn.setEnabled(valid)
        
    def is_valid(self):
        """Check if all inputs are valid."""
        if self.create_codebook_cb.isChecked():
            password = self.password_field.text()
            confirm = self.confirm_field.text()
            if len(password) < 12 or len(confirm) < 12:
                return False
            if password != confirm:
                return False
        return True
    
    def validate_and_accept(self):
        """Validate and accept dialog."""
        if not self.is_valid():
            QMessageBox.warning(
                self,
                "Invalid Input",
                "Please fix errors before proceeding.",
                QMessageBox.Ok
            )
            return
        
        # Build config
        self.config = {
            'data_mode': self.data_mode,
            'remove_outliers': self.remove_outliers_cb.isChecked(),
            'create_codebook': self.create_codebook_cb.isChecked(),
            'password': self.password_field.text() if self.create_codebook_cb.isChecked() else None,
            'confirm_password': self.confirm_field.text() if self.create_codebook_cb.isChecked() else None
        }
        
        self.accept()
        
    def get_config(self):
        """Return processing configuration."""
        return self.config


class ProgressDialog(QDialog):
    """Simple progress dialog for data processing."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Processing Data")
        self.setMinimumWidth(400)
        self.setModal(True)
        
        layout = QVBoxLayout()
        
        self.status_label = QLabel("Initializing...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont("Arial", 12))
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 5)  # 5 steps
        
        layout.addWidget(self.status_label)
        layout.addSpacing(20)
        layout.addWidget(self.progress_bar)
        self.setLayout(layout)
        
    def set_step(self, step, message):
        """Update progress step and message."""
        self.progress_bar.setValue(step)
        self.status_label.setText(message)
        QApplication.processEvents()  # Keep UI responsive


class CodebookLookupDialog(QDialog):
    """Dialog for looking up anonymized IDs in codebook."""
    
    def __init__(self, codebook_path, parent=None):
        super().__init__(parent)
        self.codebook_path = codebook_path
        self.codebook_unlocked = False
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("Codebook Lookup")
        self.setMinimumWidth(500)
        
        layout = QVBoxLayout()
        
        # Password entry section
        auth_group = QGroupBox("Unlock Codebook")
        auth_layout = QFormLayout()
        
        self.password_field = QLineEdit()
        self.password_field.setEchoMode(QLineEdit.Password)
        self.password_field.setPlaceholderText("Enter codebook password")
        self.password_field.setMaxLength(100)
        auth_layout.addRow("Password:", self.password_field)
        
        self.unlock_btn = QPushButton("Unlock Codebook")
        self.unlock_btn.clicked.connect(self.unlock_codebook)
        self.unlock_btn.setDefault(True)
        auth_layout.addRow("", self.unlock_btn)
        
        self.auth_status_label = QLabel("")
        self.auth_status_label.setWordWrap(True)
        auth_layout.addRow("", self.auth_status_label)
        
        auth_group.setLayout(auth_layout)
        layout.addWidget(auth_group)
        
        # Lookup section (disabled until unlocked)
        self.lookup_group = QGroupBox("ID Lookup")
        lookup_layout = QFormLayout()
        
        self.id_input = QLineEdit()
        self.id_input.setPlaceholderText("Enter anonymized ID (e.g., STU_04521 or TUT_0842)")
        self.id_input.setMaxLength(50)
        self.id_input.setEnabled(False)
        self.id_input.textChanged.connect(self.validate_id_format)
        self.id_input.returnPressed.connect(self.lookup_id)
        lookup_layout.addRow("Anonymized ID:", self.id_input)
        
        self.id_format_label = QLabel("")
        self.id_format_label.setStyleSheet("font-size: 11px; color: #666;")
        self.id_format_label.setWordWrap(True)
        lookup_layout.addRow("", self.id_format_label)
        
        self.lookup_btn = QPushButton("Lookup")
        self.lookup_btn.clicked.connect(self.lookup_id)
        self.lookup_btn.setEnabled(False)
        lookup_layout.addRow("", self.lookup_btn)
        
        self.result_label = QLabel("")
        self.result_label.setWordWrap(True)
        self.result_label.setStyleSheet("font-weight: bold; color: #2E86AB; min-height: 40px;")
        lookup_layout.addRow("Result:", self.result_label)
        
        # Copy button
        self.copy_btn = QPushButton("Copy to Clipboard")
        self.copy_btn.clicked.connect(self.copy_result)
        self.copy_btn.setEnabled(False)
        lookup_layout.addRow("", self.copy_btn)
        
        self.lookup_group.setLayout(lookup_layout)
        self.lookup_group.setEnabled(False)
        layout.addWidget(self.lookup_group)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)
        
        # Focus password field
        self.password_field.setFocus()
    
    def validate_id_format(self):
        """Validate ID format in real-time."""
        anon_id = self.id_input.text().strip().upper()
        
        if not anon_id:
            self.id_format_label.setText("")
            self.id_format_label.setStyleSheet("font-size: 11px; color: #666;")
            self.lookup_btn.setEnabled(False)
            return
        
        if anon_id.startswith('STU_'):
            self.id_format_label.setText(" Student ID format")
            self.id_format_label.setStyleSheet("font-size: 11px; color: #06A77D;")
            self.lookup_btn.setEnabled(True)
        elif anon_id.startswith('TUT_'):
            self.id_format_label.setText(" Tutor ID format")
            self.id_format_label.setStyleSheet("font-size: 11px; color: #06A77D;")
            self.lookup_btn.setEnabled(True)
        else:
            self.id_format_label.setText(" Invalid format. Must start with STU_ or TUT_")
            self.id_format_label.setStyleSheet("font-size: 11px; color: #C73E1D;")
            self.lookup_btn.setEnabled(False)
    
    def unlock_codebook(self):
        """Decrypt and load codebook with password."""
        password = self.password_field.text()
        
        if not password:
            self.auth_status_label.setText(" Please enter a password")
            self.auth_status_label.setStyleSheet("color: #C73E1D;")
            return
        
        try:
            # Get codebook info to verify password
            info = get_codebook_info(self.codebook_path, password)
            
            if 'error' in info:
                audit_event("codebook_unlock_failed", reason=info.get('error', 'unknown'))
                self.auth_status_label.setText(info['error'])
                self.auth_status_label.setStyleSheet("color: #C73E1D; font-weight: bold;")
                self.password_field.setFocus()
                self.password_field.selectAll()
                return
            
            # Success - display codebook info and unlock lookup
            audit_event(
                "codebook_unlocked",
                session_type=info.get('session_type', 'unknown'),
                total_students=info.get('total_students', 0),
                total_tutors=info.get('total_tutors', 0)
            )
            self.auth_status_label.setText(
                f" Unlocked!\n"
                f"Session Type: {info['session_type'].title()}\n"
                f"Students: {info['total_students']:,} | Tutors: {info['total_tutors']:,}\n"
                f"Date Range: {info['date_range']}"
            )
            self.auth_status_label.setStyleSheet("color: #06A77D; font-weight: bold;")
            
            # Unlock lookup section
            self.lookup_group.setEnabled(True)
            self.lookup_group.setTitle("ID Lookup (Unlocked)")
            self.id_input.setFocus()
            self.codebook_unlocked = True
            
            # Disable password field to prevent re-locking
            self.password_field.setEnabled(False)
            self.unlock_btn.setEnabled(False)
            
        except Exception as e:
            audit_event("codebook_unlock_error", error=str(e))
            self.auth_status_label.setText(f" Error: {str(e)}")
            self.auth_status_label.setStyleSheet("color: #C73E1D; font-weight: bold;")
    
    def lookup_id(self):
        """Lookup ID in decrypted codebook."""
        anon_id = self.id_input.text().strip().upper()
        
        if not self.codebook_unlocked:
            self.result_label.setText(" Codebook not unlocked")
            self.result_label.setStyleSheet("color: #C73E1D; font-weight: bold;")
            return
        
        if not anon_id:
            self.result_label.setText(" Please enter an ID")
            self.result_label.setStyleSheet("color: #C73E1D; font-weight: bold;")
            return
        
        # Get password
        password = self.password_field.text()
        
        # Perform lookup
        result = lookup_in_codebook(anon_id, self.codebook_path, password)
        audit_event(
            "codebook_lookup",
            id_type="STU" if anon_id.startswith("STU_") else ("TUT" if anon_id.startswith("TUT_") else "unknown"),
            success=not result.startswith('')
        )
        
        if result.startswith(''):
            # Error
            self.result_label.setText(result)
            self.result_label.setStyleSheet("color: #C73E1D; font-weight: bold;")
            self.copy_btn.setEnabled(False)
        else:
            # Success
            self.result_label.setText(result)
            self.result_label.setStyleSheet("color: #06A77D; font-weight: bold;")
            self.copy_btn.setEnabled(True)
    
    def copy_result(self):
        """Copy result to clipboard."""
        result = self.result_label.text()
        if result and not result.startswith(''):
            clipboard = QApplication.clipboard()
            clipboard.setText(result)
            
            # Show brief confirmation
            original_text = self.copy_btn.text()
            self.copy_btn.setText("Copied!")
            self.copy_btn.setStyleSheet("background-color: #06A77D; color: white;")
            
            # Reset after 1 second
            QTimer.singleShot(1000, lambda: self._reset_copy_button(original_text))
    
    def _reset_copy_button(self, original_text):
        """Reset copy button after brief confirmation."""
        self.copy_btn.setText(original_text)
        self.copy_btn.setStyleSheet("")


class ModelLoadingThread(QThread):
    """Thread for loading AI model in background to keep UI responsive."""
    
    model_loaded = pyqtSignal(object)  # Signal emitted when model loads (ChatHandler)
    loading_failed = pyqtSignal(str)    # Signal emitted if loading fails
    
    def __init__(self, model_path, df_clean, metrics, data_mode):
        super().__init__()
        self.model_path = model_path
        self.df_clean = df_clean
        self.metrics = metrics
        self.data_mode = data_mode
    
    def run(self):
        """Load model in background thread."""
        try:
            # Initialize chat handler
            handler = ChatHandler(
                model_path=self.model_path,
                verbose=True,
                enable_code_execution=True
            )
            
            # Set data for code execution
            handler.set_data_for_code_execution(self.df_clean)
            
            # Emit success signal
            self.model_loaded.emit(handler)
            
        except Exception as e:
            # Emit failure signal
            self.loading_failed.emit(str(e))


class AIChatTab(QWidget):
    """AI Chat tab with lazy model loading."""
    
    def __init__(self, df_clean, metrics, data_mode, parent=None):
        super().__init__(parent)
        self.df_clean = df_clean
        self.metrics = metrics
        self.data_mode = data_mode
        self.chat_handler = None
        self.model_loaded = False
        
        # Check if model file exists
        self.model_exists = self._check_model_file()
        
        self.init_ui()
    
    def _check_model_file(self):
        """Check if model file exists."""
        try:
            model_path = get_model_path()
            return Path(model_path).exists()
        except FileNotFoundError:
            return False
    
    def init_ui(self):
        """Initialize chat interface."""
        layout = QVBoxLayout()
        
        if not self.model_exists:
            # Model not found - show download instructions
            label = QLabel(
                "<h2>AI Model Not Found</h2>"
                "<p>The AI model file is not installed.</p>"
                "<p><b>To install the model:</b></p>"
                "<ul>"
                "<li>Open a terminal</li>"
                "<li>Run: <code>python src/ai_chat/setup_model.py</code></li>"
                "</ul>"
                "<p>This will download ~2.3GB model file to the <code>models/</code> directory.</p>"
                "<p>After downloading, reopen the application to use AI Chat.</p>"
            )
            label.setAlignment(Qt.AlignCenter)
            layout.addWidget(label)
            self.setLayout(layout)
            return
        
        # Model exists - show loading state initially
        self.loading_label = QLabel(
            "<h2>Loading AI Model...</h2>"
            "<p>Please wait while the AI model initializes.</p>"
            "<p>This may take 10-30 seconds on first load.</p>"
        )
        self.loading_label.setAlignment(Qt.AlignCenter)
        self.loading_label.setStyleSheet("color: #666;")
        layout.addWidget(self.loading_label)
        
        # Create chat interface (initially hidden)
        self.chat_container = QWidget()
        chat_layout = QVBoxLayout()
        
        # Chat history display
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setPlaceholderText("Chat history will appear here...")
        self.chat_display.setStyleSheet("""
            QTextEdit {
                background-color: #f5f5f5;
                border: 1px solid #ccc;
                border-radius: 5px;
                padding: 10px;
                font-size: 12px;
            }
        """)
        chat_layout.addWidget(self.chat_display, stretch=1)
        
        # Input area
        input_container = QWidget()
        input_layout = QHBoxLayout()
        
        self.chat_input = QLineEdit()
        self.chat_input.setPlaceholderText("Ask a question about your Writing Studio data...")
        self.chat_input.returnPressed.connect(self.send_message)
        input_layout.addWidget(self.chat_input, stretch=1)
        
        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self.send_message)
        self.send_btn.setEnabled(False)
        input_layout.addWidget(self.send_btn)
        
        input_container.setLayout(input_layout)
        chat_layout.addWidget(input_container)
        
        # Clear button
        self.clear_btn = QPushButton("Clear Chat History")
        self.clear_btn.clicked.connect(self.clear_chat)
        self.clear_btn.setEnabled(False)
        chat_layout.addWidget(self.clear_btn)
        
        self.chat_container.setLayout(chat_layout)
        self.chat_container.setVisible(False)
        layout.addWidget(self.chat_container)
        
        self.setLayout(layout)
        
        # Start model loading when widget is shown (lazy loading)
        # We'll trigger this from the tab widget's currentChanged signal
    
    def start_model_loading(self):
        """Start loading the model in background thread."""
        if self.model_loaded:
            return  # Already loaded
        
        try:
            model_path = get_model_path()
            
            # Create and start loading thread
            self.loading_thread = ModelLoadingThread(
                model_path,
                self.df_clean,
                self.metrics,
                self.data_mode
            )
            self.loading_thread.model_loaded.connect(self.on_model_loaded)
            self.loading_thread.loading_failed.connect(self.on_loading_failed)
            self.loading_thread.start()
            
        except FileNotFoundError as e:
            self.loading_label.setText(
                f"<h2>Model File Not Found</h2>"
                f"<p>{str(e)}</p>"
                f"<p>Please download the model using:</p>"
                f"<p><code>python src/ai_chat/setup_model.py</code></p>"
            )
    
    def on_model_loaded(self, handler):
        """Called when model loads successfully."""
        self.chat_handler = handler
        self.model_loaded = True
        
        # Hide loading label, show chat interface
        self.loading_label.setVisible(False)
        self.chat_container.setVisible(True)
        
        # Enable input
        self.send_btn.setEnabled(True)
        self.clear_btn.setEnabled(True)
        
        # Show welcome message
        welcome = """<b>AI Assistant:</b> Hello! I'm ready to help you analyze your Writing Studio data.

I can help you with questions like:
 "What's the average session length?"
 "How many students visited this semester?"
 "Which days are busiest?"
 "What's the completion rate?"

<b>Privacy Note:</b> I can only discuss aggregated data and statistics. I cannot reveal individual student or tutor information.

Ask me a question to get started!
"""
        self.append_message(welcome)
    
    def on_loading_failed(self, error_message):
        """Called when model loading fails."""
        self.loading_label.setText(
            f"<h2>Failed to Load Model</h2>"
            f"<p>Error: {error_message}</p>"
            f"<p>Please check that the model file exists and is valid.</p>"
        )
    
    def send_message(self):
        """Send user message to AI."""
        if not self.chat_handler or not self.model_loaded:
            return
        
        user_text = self.chat_input.text().strip()
        if not user_text:
            return
        
        # Display user message
        self.append_message(f"<b>You:</b> {user_text}")
        
        # Clear input
        self.chat_input.clear()
        
        # Disable input while generating
        self.chat_input.setEnabled(False)
        self.send_btn.setEnabled(False)
        
        # Show typing indicator
        self.append_message("<i>AI is thinking...</i>")
        
        # Process query (this will be slow - need to run in thread)
        self.query_thread = QueryThread(self.chat_handler, user_text, self.df_clean, self.metrics, self.data_mode)
        self.query_thread.response_ready.connect(self.on_response_ready)
        self.query_thread.query_failed.connect(self.on_query_failed)
        self.query_thread.start()
    
    def on_response_ready(self, response):
        """Called when AI response is ready."""
        # Remove typing indicator (last message)
        self._remove_last_message()
        
        # Display AI response
        self.append_message(f"<b>AI:</b> {response}")
        
        # Re-enable input
        self.chat_input.setEnabled(True)
        self.send_btn.setEnabled(True)
        self.chat_input.setFocus()
    
    def on_query_failed(self, error_message):
        """Called when query fails."""
        # Remove typing indicator
        self._remove_last_message()
        
        # Display error
        self.append_message(f"<b>Error:</b> {error_message}")
        
        # Re-enable input
        self.chat_input.setEnabled(True)
        self.send_btn.setEnabled(True)
    
    def clear_chat(self):
        """Clear chat history."""
        self.chat_display.clear()
        if self.chat_handler:
            self.chat_handler.clear_history()
    
    def append_message(self, message):
        """Append message to chat display."""
        self.chat_display.append(message)
        # Scroll to bottom
        scrollbar = self.chat_display.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def _remove_last_message(self):
        """Remove the last message from chat display."""
        cursor = self.chat_display.textCursor()
        cursor.movePosition(cursor.End)
        cursor.select(cursor.BlockUnderCursor)
        cursor.removeSelectedText()


class QueryThread(QThread):
    """Thread for running AI queries in background."""
    
    response_ready = pyqtSignal(str)  # Signal when response is ready
    query_failed = pyqtSignal(str)    # Signal if query fails
    
    def __init__(self, chat_handler, user_query, df_clean, metrics, data_mode):
        super().__init__()
        self.chat_handler = chat_handler
        self.user_query = user_query
        self.df_clean = df_clean
        self.metrics = metrics
        self.data_mode = data_mode
    
    def run(self):
        """Run query in background thread."""
        try:
            response, metadata = self.chat_handler.handle_query(
                self.user_query,
                self.df_clean,
                self.metrics,
                self.data_mode
            )
            self.response_ready.emit(response)
        except Exception as e:
            self.query_failed.emit(str(e))


class AnalyticsDashboard(QMainWindow):
    """Main application window for Writing Studio Analytics."""
    
    def __init__(self):
        super().__init__()
        
        # Initialize data storage
        self.df_clean = None
        self.cleaning_log = None
        self.metrics = None
        self.data_mode = None
        self.codebook_path = None
        self.ai_chat_tab = None
        
        # Initialize UI
        self.init_ui()
        
    def init_ui(self):
        """Initialize user interface."""
        self.setWindowTitle("Writing Studio Analytics")
        self.setGeometry(100, 100, 1400, 900)
        
        # Create central widget with tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.currentChanged.connect(self.on_tab_changed)
        self.setCentralWidget(self.tab_widget)
        
        # Create placeholder tabs initially
        self.create_empty_tabs()
        
        # Create menu bar
        self.create_menu_bar()
        
        # Create toolbar
        self.create_toolbar()
        
        # Create status bar
        self.create_status_bar()
    
    def add_chart_to_layout(self, layout, fig, title=None):
        """Embed a matplotlib figure into the given layout."""
        if fig is None:
            return
        
        # Optional title label
        if title:
            title_label = QLabel(f"<h3>{title}</h3>")
            title_label.setAlignment(Qt.AlignCenter)
            title_label.setStyleSheet("margin-bottom: 10px;")
            layout.addWidget(title_label)
        
        # Create canvas and add to layout
        canvas = FigureCanvasQTAgg(fig)
        canvas.setMinimumHeight(500)
        canvas.setStyleSheet("background-color: white;")
        layout.addWidget(canvas)
        
        # Add spacing between charts
        layout.addSpacing(20)
    
    def create_empty_tabs(self):
        """Create tabs showing 'no data loaded' message."""
        # Clear existing tabs
        while self.tab_widget.count() > 0:
            self.tab_widget.removeTab(0)
        
        # Single tab with message
        tab = QWidget()
        layout = QVBoxLayout()
        
        label = QLabel(
            "<h2>No Data Loaded</h2>"
            "<p style='text-align: center; color: #666; font-size: 14px;'>"
            "Click <b>Open File</b> to load a Penji export and begin analysis."
        )
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        layout.addStretch()
        
        tab.setLayout(layout)
        self.tab_widget.addTab(tab, "Overview")
    
    def create_overview_tab(self):
        """Create Overview tab with key metrics and charts."""
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout()
        
        # Key metrics cards
        if self.metrics:
            metrics_container = self.create_metric_cards()
            layout.addWidget(metrics_container)
            layout.addSpacing(20)
        
        # Sessions over time chart
        if self.df_clean is not None:
            charts_module = walkin_charts if self.data_mode == 'walkin' else scheduled_charts
            fig1 = charts_module.plot_sessions_over_time(self.df_clean)
            self.add_chart_to_layout(layout, fig1, "Sessions Over Time")
            
            # Semester comparison (only if 2+ semesters)
            if 'Semester_Label' in self.df_clean.columns:
                if self.df_clean['Semester_Label'].nunique() >= 2:
                    fig2 = scheduled_charts.plot_semester_metrics_comparison(
                        self.df_clean,
                        self.cleaning_log.get('context', {})
                    )
                    self.add_chart_to_layout(layout, fig2, "Semester Comparison")
        
        layout.addStretch()
        container.setLayout(layout)
        scroll.setWidget(container)
        
        return scroll
    
    def create_booking_tab(self):
        """Create Booking & Attendance tab."""
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout()
        
        if self.df_clean is not None:
            charts_module = walkin_charts if self.data_mode == 'walkin' else scheduled_charts
            
            # Charts to add
            charts_to_add = [
                (charts_module.plot_booking_lead_time_donut, "Booking Lead Time"),
                (charts_module.plot_sessions_by_day_of_week, "Sessions by Day of Week"),
                (charts_module.plot_sessions_heatmap_day_time, "Day/Time Heatmap"),
            ]
            
            # Add scheduled-only charts
            if self.data_mode == 'scheduled':
                charts_to_add.extend([
                    (scheduled_charts.plot_session_outcomes_pie, "Session Outcomes"),
                    (scheduled_charts.plot_no_show_by_day, "No-Show Rate by Day"),
                    (scheduled_charts.plot_outcomes_over_time, "Outcome Trends Over Time"),
                ])
            
            for chart_func, title in charts_to_add:
                fig = chart_func(self.df_clean)
                if fig:
                    self.add_chart_to_layout(layout, fig, title)
        
        layout.addStretch()
        container.setLayout(layout)
        scroll.setWidget(container)
        
        return scroll
    
    def create_students_tab(self):
        """Create Students tab."""
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout()
        
        if self.df_clean is not None:
            # Use scheduled charts (works for both data types)
            fig1 = scheduled_charts.plot_top_active_students(self.df_clean)
            self.add_chart_to_layout(layout, fig1, "Top Active Students")
            
            fig2 = scheduled_charts.plot_first_time_vs_returning(self.df_clean)
            self.add_chart_to_layout(layout, fig2, "First-Time vs Returning Students")
            
            fig3 = scheduled_charts.plot_student_retention_trends(self.df_clean)
            if fig3:
                self.add_chart_to_layout(layout, fig3, "Student Retention Trends")
        
        layout.addStretch()
        container.setLayout(layout)
        scroll.setWidget(container)
        
        return scroll
    
    def create_satisfaction_tab(self):
        """Create Satisfaction tab."""
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout()
        
        if self.df_clean is not None:
            charts_module = walkin_charts if self.data_mode == 'walkin' else scheduled_charts
            
            charts_to_add = [
                (charts_module.plot_confidence_comparison, "Confidence: Before vs After"),
                (charts_module.plot_confidence_change_distribution, "Confidence Change Distribution"),
                (charts_module.plot_satisfaction_distribution, "Satisfaction Distribution"),
                (charts_module.plot_satisfaction_trends, "Satisfaction Trends Over Time"),
            ]
            
            for chart_func, title in charts_to_add:
                fig = chart_func(self.df_clean)
                if fig:
                    self.add_chart_to_layout(layout, fig, title)
        
        layout.addStretch()
        container.setLayout(layout)
        scroll.setWidget(container)
        
        return scroll
    
    def create_tutors_tab(self):
        """Create Tutors tab."""
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout()
        
        if self.df_clean is not None:
            charts_module = walkin_charts if self.data_mode == 'walkin' else scheduled_charts
            
            charts_to_add = [
                (charts_module.plot_sessions_per_tutor, "Sessions per Tutor"),
                (charts_module.plot_tutor_workload_balance, "Tutor Workload Balance"),
                (charts_module.plot_session_length_by_tutor, "Session Length by Tutor"),
            ]
            
            for chart_func, title in charts_to_add:
                fig = chart_func(self.df_clean)
                if fig:
                    self.add_chart_to_layout(layout, fig, title)
        
        layout.addStretch()
        container.setLayout(layout)
        scroll.setWidget(container)
        
        return scroll
    
    def create_content_tab(self):
        """Create Session Content tab."""
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout()
        
        if self.df_clean is not None:
            charts_module = walkin_charts if self.data_mode == 'walkin' else scheduled_charts
            
            # Writing stages and focus areas
            fig1 = charts_module.plot_writing_stages(self.df_clean)
            if fig1:
                self.add_chart_to_layout(layout, fig1, "Writing Stages")
            
            fig2 = charts_module.plot_focus_areas(self.df_clean)
            if fig2:
                self.add_chart_to_layout(layout, fig2, "Focus Areas")
            
            # Course table (only if scheduled data and course codes exist)
            if self.data_mode == 'scheduled' and 'Course_Code' in self.df_clean.columns:
                fig3 = scheduled_charts.plot_course_table(self.df_clean)
                if fig3:
                    self.add_chart_to_layout(layout, fig3, "Course Enrollment")
        
        layout.addStretch()
        container.setLayout(layout)
        scroll.setWidget(container)
        
        return scroll
    
    def create_quality_tab(self):
        """Create Data Quality tab."""
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout()
        
        if self.df_clean is not None:
            context = self.cleaning_log.get('context', {})
            missing_report = self.cleaning_log.get('missing_values', {})
            
            fig1 = scheduled_charts.plot_survey_response_rates(context)
            if fig1:
                self.add_chart_to_layout(layout, fig1, "Survey Response Rates")
            
            fig2 = scheduled_charts.plot_missing_data_concern(missing_report)
            if fig2:
                self.add_chart_to_layout(layout, fig2, "Missing Data Concerns")
        
        layout.addStretch()
        container.setLayout(layout)
        scroll.setWidget(container)
        
        return scroll
    
    def create_incentives_tab(self):
        """Create Incentives tab (conditional - only shown if Incentivized column exists)."""
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        layout = QVBoxLayout()
        
        if self.df_clean is not None:
            # Only show incentives charts for scheduled sessions with Incentivized column
            if self.data_mode == 'scheduled' and 'Incentivized' in self.df_clean.columns:
                fig1 = scheduled_charts.plot_incentive_breakdown(self.df_clean)
                if fig1:
                    self.add_chart_to_layout(layout, fig1, "Incentive Breakdown")
                
                fig2 = scheduled_charts.plot_incentives_vs_tutor_rating(self.df_clean)
                if fig2:
                    self.add_chart_to_layout(layout, fig2, "Incentives vs Tutor Rating")
                
                fig3 = scheduled_charts.plot_incentives_vs_satisfaction(self.df_clean)
                if fig3:
                    self.add_chart_to_layout(layout, fig3, "Incentives vs Satisfaction")
            else:
                # Show message if no incentives data
                label = QLabel(
                    "<h2>No Incentives Data</h2>"
                    "<p>Incentives data is not available for this dataset.</p>"
                    "<p>This tab only appears for scheduled sessions with Incentivized column.</p>"
                )
                label.setAlignment(Qt.AlignCenter)
                layout.addWidget(label)
        
        layout.addStretch()
        container.setLayout(layout)
        scroll.setWidget(container)
        
        return scroll
    
    def should_show_incentives_tab(self):
        """Check if incentives tab should be displayed."""
        if self.df_clean is None:
            return False
        # Only show for scheduled sessions with Incentivized column
        return self.data_mode == 'scheduled' and 'Incentivized' in self.df_clean.columns
    
    def create_metric_cards(self):
        """Create horizontal row of key metric cards."""
        container = QWidget()
        layout = QHBoxLayout()
        
        if 'cancellations' in self.cleaning_log.get('context', {}):
            ctx = self.cleaning_log['context']['cancellations']
            
            metrics = [
                ("Total Sessions", f"{ctx['total_sessions']:,}", "#2E86AB"),
                ("Completion Rate", f"{ctx['completion_rate']:.1f}%", "#06A77D"),
                ("Cancellation Rate", f"{ctx['cancellation_rate']:.1f}%", "#A23B72"),
                ("No-Show Rate", f"{ctx['no_show_rate']:.1f}%", "#F18F01"),
            ]
        else:
            metrics = [
                ("Total Sessions", f"{len(self.df_clean):,}", "#2E86AB"),
            ]
        
        for title, value, color in metrics:
            card = QGroupBox()
            card_layout = QVBoxLayout()
            
            value_label = QLabel(f"<h2>{value}</h2>")
            value_label.setAlignment(Qt.AlignCenter)
            value_label.setStyleSheet(f"color: {color}; font-weight: bold; font-size: 24px;")
            
            title_label = QLabel(title)
            title_label.setAlignment(Qt.AlignCenter)
            title_label.setStyleSheet("font-size: 12px; color: #666;")
            
            card_layout.addWidget(value_label)
            card_layout.addWidget(title_label)
            card.setLayout(card_layout)
            card.setMaximumWidth(200)
            
            layout.addWidget(card)
        
        container.setLayout(layout)
        return container
    
    def update_tabs_with_data(self):
        """Recreate all tabs with actual charts after data is loaded."""
        # Clear existing tabs
        while self.tab_widget.count() > 0:
            self.tab_widget.removeTab(0)
        
        # Create tabs with data
        self.tab_widget.addTab(self.create_overview_tab(), "Overview")
        self.tab_widget.addTab(self.create_booking_tab(), "Booking & Attendance")
        self.tab_widget.addTab(self.create_students_tab(), "Students")
        self.tab_widget.addTab(self.create_satisfaction_tab(), "Satisfaction")
        self.tab_widget.addTab(self.create_tutors_tab(), "Tutors")
        
        # Add Incentives tab conditionally
        if self.should_show_incentives_tab():
            self.tab_widget.addTab(self.create_incentives_tab(), "Incentives")
        
        self.tab_widget.addTab(self.create_content_tab(), "Session Content")
        self.tab_widget.addTab(self.create_quality_tab(), "Data Quality")
        
        # Add AI Chat tab with lazy loading
        if self.df_clean is not None:
            self.ai_chat_tab = AIChatTab(self.df_clean, self.metrics, self.data_mode, self)
            self.tab_widget.addTab(self.ai_chat_tab, "AI Chat")
        else:
            # Placeholder if no data
            ai_tab = QWidget()
            ai_layout = QVBoxLayout()
            ai_label = QLabel("<h2>AI Chat</h2><p>Load data to use AI Chat.</p>")
            ai_label.setAlignment(Qt.AlignCenter)
            ai_layout.addWidget(ai_label)
            ai_tab.setLayout(ai_layout)
            self.tab_widget.addTab(ai_tab, "AI Chat")
    
    def create_menu_bar(self):
        """Create application menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        # Open action
        open_action = QAction("Open File...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.setStatusTip("Open a data file (CSV or Excel)")
        open_action.triggered.connect(self.open_file)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        # Export PDF action
        export_action = QAction("Export PDF Report...", self)
        export_action.setShortcut("Ctrl+E")
        export_action.setStatusTip("Export full report as PDF")
        export_action.triggered.connect(self.export_pdf)
        export_action.setEnabled(False)  # Disable until data is loaded
        self.export_action = export_action
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # Codebook lookup action
        lookup_action = QAction("Lookup Codebook...", self)
        lookup_action.setShortcut("Ctrl+L")
        lookup_action.setStatusTip("Lookup anonymized IDs to get original emails")
        lookup_action.triggered.connect(self.show_codebook_lookup)
        lookup_action.setEnabled(False)  # Disable until codebook is created
        self.lookup_action = lookup_action
        file_menu.addAction(lookup_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("About", self)
        about_action.setStatusTip("About Writing Studio Analytics")
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
    def create_toolbar(self):
        """Create main toolbar."""
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        
        # Open File button
        open_btn = QPushButton("Open File")
        open_btn.clicked.connect(self.open_file)
        toolbar.addWidget(open_btn)
        
        toolbar.addSeparator()
        
        # Export PDF button
        self.export_btn = QPushButton("Export PDF")
        self.export_btn.clicked.connect(self.export_pdf)
        self.export_btn.setEnabled(False)  # Disable until data is loaded
        toolbar.addWidget(self.export_btn)
        
    def create_status_bar(self):
        """Create status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Initial status message
        self.status_bar.showMessage("Ready - Open a file to begin analysis")
    
    def open_file(self):
        """Open a data file (CSV or Excel)."""
        # Show file dialog
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open Data File",
            "",
            "Data Files (*.csv *.xlsx *.xls);;CSV Files (*.csv);;Excel Files (*.xlsx *.xls)"
        )
        
        if file_path:
            audit_event("file_selected", file_path=file_path)
            try:
                self.load_file(file_path)
            except Exception as e:
                QMessageBox.critical(
                    self,
                    "Error Loading File",
                    f"Failed to load file:\n{str(e)}",
                    QMessageBox.Ok
                )
    
    def load_file(self, file_path):
        """Load and process data file."""
        try:
            # Step 1: Load file
            self.status_bar.showMessage(f"Loading: {file_path}")
            
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            self.status_bar.showMessage(f"Loaded {len(df):,} rows - Detecting session type...")
            
            # Step 2: Auto-detect session type
            data_mode = detect_session_type(df)
            audit_event("mode_detected", file_path=file_path, mode=data_mode, rows=len(df), columns=len(df.columns))
            
            if data_mode == 'unknown':
                audit_event("mode_detection_failed", file_path=file_path)
                QMessageBox.warning(
                    self,
                    "Unknown Data Type",
                    "Unable to detect session type. This file may not be a valid Penji export.\n\n"
                    "Supported formats: Scheduled 40-minute sessions or Walk-in sessions",
                    QMessageBox.Ok
                )
                self.status_bar.showMessage("Failed to detect session type")
                return
            
            # Show configuration dialog
            config_dialog = ProcessingOptionsDialog(data_mode, self)
            if config_dialog.exec_() == QDialog.Accepted:
                config = config_dialog.get_config()
                self.process_data(df, config)
            else:
                self.status_bar.showMessage("Cancelled")
                
        except Exception as e:
            audit_event("file_load_error", file_path=file_path, error=str(e))
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to load file:\n{str(e)}",
                QMessageBox.Ok
            )
            self.status_bar.showMessage("Error loading file")
    
    def process_data(self, df, config):
        """Process data through the full pipeline."""
        # Initialize progress dialog outside try so finally can access it
        progress = ProgressDialog(self)
        progress.show()
        
        try:
            audit_event(
                "process_started",
                mode=config.get('data_mode'),
                create_codebook=config.get('create_codebook'),
                remove_outliers=config.get('remove_outliers'),
                input_rows=len(df)
            )
            
            # Step 0: Starting
            progress.set_step(0, "Starting...")
            
            # Step 1: Anonymize
            progress.set_step(1, "Anonymizing data...")
            df_anon, codebook_path, anon_log = anonymize_with_codebook(
                df,
                create_codebook=config['create_codebook'],
                password=config['password'] if config['create_codebook'] else None,
                confirm_password=config['confirm_password'] if config['create_codebook'] else None,
                session_type=config['data_mode']
            )
            self.codebook_path = codebook_path
            audit_event("anonymize_complete", mode=config.get('data_mode'), codebook_created=bool(codebook_path))
            
            # Step 2: Clean
            progress.set_step(2, "Cleaning and processing data...")
            if config['data_mode'] == 'walkin':
                df_clean, cleaning_log = clean_walkin_data(df_anon)
            else:
                df_clean, cleaning_log = clean_data(
                    df_anon,
                    mode=config['data_mode'],
                    remove_outliers=config['remove_outliers'],
                    log_actions=False
                )
            
            # Step 3: Calculate metrics
            progress.set_step(3, "Calculating metrics...")
            if config['data_mode'] == 'walkin':
                metrics = calculate_walkin_metrics(df_clean)
            else:
                metrics = calculate_all_metrics(df_clean)
            
            # Step 4: Complete
            progress.set_step(4, "Complete!")
            
            # Store results
            self.df_clean = df_clean
            self.cleaning_log = cleaning_log
            self.metrics = metrics
            self.data_mode = config['data_mode']
            
            # Update status bar
            total_sessions = len(df_clean)
            if 'cancellations' in cleaning_log.get('context', {}):
                completion_rate = cleaning_log['context']['cancellations']['completion_rate']
            else:
                completion_rate = 0.0
            
            self.status_bar.showMessage(
                f"Loaded: {total_sessions:,} sessions | "
                f"Completion: {completion_rate:.1f}% | "
                f"Mode: {config['data_mode'].title()}"
            )
            audit_event(
                "process_completed",
                mode=config.get('data_mode'),
                total_sessions=total_sessions,
                completion_rate=completion_rate
            )
            
            # Update tabs with charts
            self.update_tabs_with_data()
            
            # Enable export buttons
            self.export_btn.setEnabled(True)
            self.export_action.setEnabled(True)
            
            # Enable codebook lookup if codebook was created
            if self.codebook_path:
                self.lookup_action.setEnabled(True)
            
            # Success message
            QMessageBox.information(
                self,
                "Data Loaded Successfully",
                f"Processed {total_sessions:,} sessions.\n\n"
                f"Session type: {config['data_mode'].title()}\n"
                f"Completion rate: {completion_rate:.1f}%\n\n"
                "View charts in the tabs above.",
                QMessageBox.Ok
            )
                
        except ValueError as e:
            audit_event("process_configuration_error", error=str(e))
            QMessageBox.critical(
                self,
                "Configuration Error",
                str(e),
                QMessageBox.Ok
            )
            self.status_bar.showMessage("Configuration error")
            
        except Exception as e:
            audit_event("process_error", error=str(e))
            import traceback
            error_details = traceback.format_exc()
            
            QMessageBox.critical(
                self,
                "Processing Error",
                f"Failed to process data:\n{str(e)}\n\n"
                "See details below for more information.",
                QMessageBox.Ok
            )
            
            # Show detailed error in dialog
            details_dialog = QMessageBox(self)
            details_dialog.setWindowTitle("Error Details")
            details_dialog.setText(str(e))
            details_dialog.setDetailedText(error_details)
            details_dialog.setIcon(QMessageBox.Critical)
            details_dialog.exec_()
            
            self.status_bar.showMessage("Error processing data")
            
        finally:
            # Close progress dialog if it exists
            if progress:
                progress.close()
    
    def export_pdf(self):
        """Export full report as PDF."""
        if self.df_clean is None or self.cleaning_log is None:
            QMessageBox.warning(
                self,
                "No Data",
                "Please load a data file first.",
                QMessageBox.Ok
            )
            return
        
        try:
            # Generate filename
            from datetime import datetime
            timestamp = datetime.now().strftime('%Y-%m-%d-%H%M')
            
            if self.data_mode == 'walkin':
                report_filename = f"WS_Analytics_WalkIns_{timestamp}.pdf"
                report_path = generate_walkin_report(
                    self.df_clean,
                    self.cleaning_log,
                    report_filename
                )
            else:
                report_filename = f"WS_Analytics_Sessions_{timestamp}.pdf"
                report_path = generate_full_report(
                    self.df_clean,
                    self.cleaning_log,
                    report_filename
                )
            
            # Success message
            QMessageBox.information(
                self,
                "Export Successful",
                f"PDF report saved:\n{report_path}\n\n"
                f"Sessions: {len(self.df_clean):,}\n"
                f"Filename: {report_filename}",
                QMessageBox.Ok
            )
            audit_event("export_pdf_success", path=report_path, sessions=len(self.df_clean), mode=self.data_mode)
            
        except Exception as e:
            audit_event("export_pdf_error", error=str(e), mode=self.data_mode)
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to export PDF:\n{str(e)}",
                QMessageBox.Ok
            )
    
    def show_codebook_lookup(self):
        """Show codebook lookup dialog."""
        if not self.codebook_path:
            QMessageBox.warning(
                self,
                "No Codebook",
                "No codebook was created for this dataset.\n\n"
                "To enable codebook lookup, reprocess data with 'Generate codebook' checked.",
                QMessageBox.Ok
            )
            return
        
        # Show codebook lookup dialog
        audit_event("codebook_lookup_opened", has_codebook=bool(self.codebook_path))
        dialog = CodebookLookupDialog(self.codebook_path, self)
        dialog.exec_()
    
    def on_tab_changed(self, index):
        """Handle tab change event - triggers lazy loading for AI Chat."""
        if self.ai_chat_tab is not None:
            # Check if current tab is AI Chat tab
            current_widget = self.tab_widget.widget(index)
            if current_widget == self.ai_chat_tab:
                # Trigger lazy loading of AI model
                if hasattr(self.ai_chat_tab, 'start_model_loading'):
                    self.ai_chat_tab.start_model_loading()
    
    def show_about(self):
        """Show about dialog."""
        about_text = """
        <h3>Writing Studio Analytics</h3>
        <p>Version 2.0 (PyQt Edition)</p>
        <p>Privacy-first analytics tool for University of Arkansas Writing Studio.</p>
        <p><b>Features:</b></p>
        <ul>
            <li>Session volume trends and patterns</li>
            <li>Booking behavior analysis</li>
            <li>Student satisfaction metrics</li>
            <li>Tutor workload distribution</li>
            <li>FERPA-compliant anonymization</li>
            <li>AI-powered natural language queries</li>
        </ul>
        <p><b>Created by:</b> Zachary Tipton (Graduate Assistant)</p>
        """
        
        QMessageBox.about(self, "About Writing Studio Analytics", about_text)


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    app.setApplicationName("Writing Studio Analytics")
    
    # Set style
    app.setStyle('Fusion')
    
    # Set color scheme
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(240, 240, 240))
    palette.setColor(QPalette.WindowText, QColor(0, 0, 0))
    palette.setColor(QPalette.Base, QColor(255, 255, 255))
    palette.setColor(QPalette.AlternateBase, QColor(245, 245, 245))
    palette.setColor(QPalette.ToolTipBase, QColor(255, 255, 220))
    palette.setColor(QPalette.ToolTipText, QColor(0, 0, 0))
    palette.setColor(QPalette.Text, QColor(0, 0, 0))
    palette.setColor(QPalette.Button, QColor(240, 240, 240))
    palette.setColor(QPalette.ButtonText, QColor(0, 0, 0))
    palette.setColor(QPalette.BrightText, QColor(255, 0, 0))
    palette.setColor(QPalette.Link, QColor(42, 130, 218))
    palette.setColor(QPalette.Highlight, QColor(76, 163, 252))
    palette.setColor(QPalette.HighlightedText, QColor(255, 255, 255))
    app.setPalette(palette)
    
    window = AnalyticsDashboard()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

