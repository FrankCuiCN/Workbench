import logging
from PySide6.QtWidgets import QTabWidget
from PySide6.QtGui import QShortcut, QKeySequence
from ui.session import Session

logger = logging.getLogger(__name__)


class Workspace(QTabWidget):
    """Workspace for handling multiple sessions."""
    def __init__(self, parent):
        # Note: Workspace relies on the self-deletion pattern for clean-up
        super().__init__(parent=None)
        # Define attributes
        self.main_window = parent
        self.closed_sessions = []  # Store recently closed sessions
        self.backend = "openai"    # Default backend
        # Configuration
        self.setTabsClosable(True)  # Enable close buttons
        self.setMovable(True)       # Allow tabs to be reordered
        self.setDocumentMode(True)  # A cleaner look
        # Signal
        self.tabCloseRequested.connect(self.close_session)  # Session close button is clicked
        self.currentChanged.connect(self.focus)  # The current session index changes
        # Create the first session
        self.new_session()
        # Register keyboard shortcuts
        QShortcut(QKeySequence("Ctrl+T"), self).activated.connect(self.new_session)
        QShortcut(QKeySequence("Ctrl+N"), self).activated.connect(self.new_session)
        QShortcut(QKeySequence("Ctrl+W"), self).activated.connect(self.close_current_session)
        QShortcut(QKeySequence("Ctrl+Tab"), self).activated.connect(self.next_session)
        QShortcut(QKeySequence("Ctrl+Shift+Tab"), self).activated.connect(self.prev_session)
        QShortcut(QKeySequence("Ctrl+Shift+T"), self).activated.connect(self.reopen_closed_session)
        QShortcut(QKeySequence("Ctrl+R"), self).activated.connect(self.reset_current_session)
        QShortcut(QKeySequence("F5"), self).activated.connect(self.reset_current_session)
        QShortcut(QKeySequence("F10"), self).activated.connect(self.change_api_backend)
    
    def new_session(self, tab_index=None):
        if tab_index is None:
            tab_index = self.count()
        session = Session(self)
        self.insertTab(tab_index, session, "Session")
        self.setCurrentIndex(tab_index)
    
    def close_session(self, index, open_new=True, store_session=True):
        # Get the session
        session = self.widget(index)
        # Store session before closing
        if store_session:
            self.closed_sessions.append(session.get_data())
            if len(self.closed_sessions) > 20:  # Keep the last 20 sessions
                self.closed_sessions.pop(0)
            logger.debug(f"Stored closed tab. Stack size: {len(self.closed_sessions)}")
        # Clean up resources in the session before removing
        session.clean_up_resources()
        # Remove the session from the UI
        self.removeTab(index)
        # Open a new session if none left
        if open_new:
            if self.count() == 0:
                self.new_session()
    
    def close_current_session(self):
        current_index = self.currentIndex()
        self.close_session(current_index)
    
    def reset_current_session(self):
        open_new = self.count() > 1
        current_index = self.currentIndex()
        self.close_current_session()
        if open_new:
            self.new_session(current_index)

    def next_session(self):
        if self.count() > 1:
            next_index = (self.currentIndex() + 1) % self.count()
            self.setCurrentIndex(next_index)
    
    def prev_session(self):
        if self.count() > 1:
            prev_index = (self.currentIndex() - 1) % self.count()
            # Move to the previous session
            self.setCurrentIndex(prev_index)
    
    def focus(self):
        # Focus on the current text editor
        session = self.currentWidget()
        # session could be None because after removing the last session
        #   focus() is called (Cf currentChanged), current session is None in this case
        if session is not None:
            session.focus()

    def reopen_closed_session(self):
        if not self.closed_sessions:
            logger.debug("No closed sessions to reopen.")
            return
        # Get session_data
        session_data = self.closed_sessions.pop()
        logger.debug(f"Reopening tab. Stack size: {len(self.closed_sessions)}")
        # Create the session
        session = Session(self)
        session.set_data(session_data)
        # Add to the end
        tab_index = self.addTab(session, "Session")
        self.setCurrentIndex(tab_index)
    
    def get_data(self):
        session_data_all = []
        for idx in range(self.count()):
            session = self.widget(idx)
            session_data_all.append(session.get_data())
        return {"session_data_all": session_data_all}
    
    def set_data(self, data):
        session_data_all = data["session_data_all"]
        # Clear existing tabs without storing them
        for idx in reversed(range(self.count())):
            self.close_session(idx, open_new=False, store_session=False)
        # Clean up closed sessions
        self.closed_sessions = []
        # Recreate sessions
        for session_data in session_data_all:
            session = Session(self)
            session.set_data(session_data)
            self.addTab(session, "Session")
    
    def change_api_backend(self):
        """Change API backend for all sessions"""
        # Loop through available backends
        if self.backend == "openai":
            self.backend = "anthropic"
        elif self.backend == "anthropic":
            self.backend = "gemini"
        elif self.backend == "gemini":
            self.backend = "openai"
        else:
            raise Exception(f"Unexpected backend: {self.backend}")
        # Update the global status bar
        self.main_window.global_status_bar.update_backend_status(self.backend)
        # Update logger
        logger.debug(f"Backend changed to: {self.backend}")
    
    def clean_up_resources(self):
        logger.debug(f"Cleaning up resources for {self.count()} sessions")
        # Clear existing tabs
        for idx in reversed(range(self.count())):
            self.close_session(idx, open_new=False, store_session=False)
        # Clear closed_sessions
        self.closed_sessions = []
        # Self-Deletion
        self.deleteLater()
