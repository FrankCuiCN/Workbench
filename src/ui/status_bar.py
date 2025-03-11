"""
Status bar component for displaying application status
"""
from PySide6.QtWidgets import QStatusBar, QLabel

class StatusBar(QStatusBar):
    """Status bar for displaying application status"""
    
    def __init__(self, parent=None):
        """Initialize the status bar"""
        super().__init__(parent)
        self.setSizeGripEnabled(False)
        
        # Create permanent widgets for status display on the right
        self.follow_status = QLabel("")
        # Add them to the right side of the status bar
        self.addPermanentWidget(self.follow_status)
        self.read_only_status = QLabel("")
        self.addPermanentWidget(self.read_only_status)
        
    def update_session_status(self, status):
        """Update the session status message in the status bar based on current state."""
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
    
    def update_following_status(self, is_following):
        """Update the following status label."""
        follow_text = "Follow: ON" if is_following else "Follow: OFF"
        self.follow_status.setText(f"{follow_text} (F9)")
    
    def update_read_only_status(self, read_only):
        """Update the read-only status label."""
        read_only_text = "Read-Only: ON" if read_only else "Read-Only: OFF"
        self.read_only_status.setText(read_only_text)
    
    def show_error(self, message):
        """Display error message in the status bar"""
        self.setStyleSheet("color: red;")
        self.showMessage(message)
    
    def reset_style(self):
        """Reset status bar to default style"""
        self.setStyleSheet("")
