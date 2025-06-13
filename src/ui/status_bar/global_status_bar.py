from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QStatusBar, QLabel


class GlobalStatusBar(QStatusBar):
    """Global status bar for application-wide status"""
    def __init__(self, parent):
        """Initialize the global status bar"""
        super().__init__(parent)
        # Configuration
        self.setSizeGripEnabled(False)
        # Add the label for api backend
        self.backend_status = QLabel("")
        self.addPermanentWidget(self.backend_status)
        # Internal state
        self.internal_state = "Ctrl+F: Find  |  Ctrl+R: Reset Current Session  |  Ctrl+Shift+T: Restore Closed Sessions"
        self.showMessage(self.internal_state)
    
    def update_backend_status(self, backend):
        # Workaround: Add one space to the right
        # Background: Rare display issues may cut off 1~2 characters
        if backend == "openai":
            self.backend_status.setText("Backend: OpenAI (F10) ")
        elif backend == "anthropic":
            self.backend_status.setText("Backend: Anthropic (F10) ")
        elif backend == "gemini":
            self.backend_status.setText("Backend: Gemini (F10) ")
        else:
            raise Exception("Unexpected API backend")
    
    def show_save_success(self, message):
        self.setStyleSheet("color: rgb(0, 200, 0);")
        self.showMessage(message)
        def _callback():
            self.setStyleSheet("")
            self.showMessage(self.internal_state)
        QTimer.singleShot(1000, _callback)  # Recover in 1 second
    
    def show_save_error(self, message):
        self.setStyleSheet("color: rgb(200, 0, 0);")
        self.showMessage(message)
        def _callback():
            self.setStyleSheet("")
            self.showMessage(self.internal_state)
        QTimer.singleShot(5000, _callback)  # Recover in 5 seconds
