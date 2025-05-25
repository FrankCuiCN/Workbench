from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QStatusBar, QLabel

class StatusBar(QStatusBar):
    """Status bar for displaying application status"""
    
    def __init__(self, parent=None):
        """Initialize the status bar"""
        super().__init__(parent)
        # Configuration
        self.setSizeGripEnabled(False)
        # Add the label for follow mode
        self.follow_status = QLabel("")
        self.addPermanentWidget(self.follow_status)
        # Add the label for api backend
        self.backend_status = QLabel("")
        self.addPermanentWidget(self.backend_status)
        # Add the label for read-only status
        self.read_only_status = QLabel("")
        self.addPermanentWidget(self.read_only_status)
        # Internal state
        self.internal_state = None
        
    def update_session_status(self, status):
        if status == "idle":
            status_text = "Idle       | Ctrl+Enter: Fast Reply | Shift+Enter: Think More"
        elif status == "waiting":
            status_text = "Waiting    | Press Esc to interrupt"
        elif status == "thinking":
            status_text = "Thinking   | Press Esc to interrupt"
        elif status == "generating":
            status_text = "Generating | Press Esc to interrupt"
        else:
            raise ValueError(f"Unexpected status value: {status}")
        self.showMessage(status_text)
        # Update the internal state
        self.internal_state = status_text
    
    def update_following_status(self, is_following):
        follow_text = "Follow: ON" if is_following else "Follow: OFF"
        self.follow_status.setText(f"{follow_text} (F9)")
    
    def update_read_only_status(self, read_only):
        read_only_text = "Read-Only: ON" if read_only else "Read-Only: OFF"
        self.read_only_status.setText(read_only_text)
    
    def show_syntax_error(self):
        self.setStyleSheet("color: red;")
        self.showMessage("Syntax Error")
        def _callback():
            self.setStyleSheet("")
            self.showMessage(self.internal_state)
        QTimer.singleShot(1000, _callback)  # Recover in 1 second

    def update_backend_status(self, backend):
        if backend == "anthropic":
            self.backend_status.setText("Backend: Anthropic (F10)")
        elif backend == "openai":
            self.backend_status.setText("Backend: OpenAI (F10)")
        else:
            raise Exception("Unexpected API backend")
