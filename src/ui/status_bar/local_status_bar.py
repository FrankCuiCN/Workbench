from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QStatusBar, QLabel


class LocalStatusBar(QStatusBar):
    """Local status bar for individual session status"""
    
    def __init__(self, parent=None):
        """Initialize the local status bar"""
        super().__init__(parent)
        # Configuration
        self.setSizeGripEnabled(False)
        # Add the label for read-only status
        self.read_only_status = QLabel("")
        self.addPermanentWidget(self.read_only_status)
        # Internal state
        self.internal_state = None
        
    def update_session_status(self, status):
        if status == "idle":
            status_text = "Idle        |  Ctrl+Enter: Fast Reply  |  Shift+Enter: Think More"
        elif status == "waiting":
            status_text = "Waiting     |  Press Esc to interrupt"
        elif status == "thinking":
            status_text = "Thinking    |  Press Esc to interrupt"
        elif status == "generating":
            status_text = "Generating  |  Press Esc to interrupt"
        else:
            raise ValueError(f"Unexpected status value: {status}")
        self.showMessage(status_text)
        # Update the internal state
        self.internal_state = status_text
    
    def update_read_only_status(self, read_only):
        # Workaround: Pad one whitespace on the right
        # Background: Rare display issues may cut-off 1~2 characters
        read_only_text = "Read-Only: ON " if read_only else "Read-Only: OFF "
        self.read_only_status.setText(read_only_text)
    
    def show_syntax_error(self):
        self.setStyleSheet("color: rgb(200, 0, 0);")
        self.showMessage("Syntax Error")
        def _callback():
            self.setStyleSheet("")
            self.showMessage(self.internal_state)
        QTimer.singleShot(1000, _callback)  # Recover in 1 second