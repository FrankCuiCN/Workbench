import logging
from PySide6.QtWidgets import QTabWidget
from PySide6.QtGui import QShortcut, QKeySequence
from ui.session.session import Session

logger = logging.getLogger(__name__)

class Workspace(QTabWidget):
    """Workspace for handling multiple sessions."""
    def __init__(self):
        super().__init__()
        # Define attributes
        self.closed_sessions = []  # Store recently closed sessions
        # Configuration
        self.setMovable(True)       # Allow tabs to be reordered
        self.setTabsClosable(True)  # Enable close buttons
        self.setDocumentMode(True)  # A cleaner look
        # Signal: Emitted when the close button on a tab is clicked
        self.tabCloseRequested.connect(self.close_session)
        # Signal: Emitted whenever the current page index changes
        self.currentChanged.connect(self.focus)
        # Create the first session
        self.new_session()
        # Register keyboard shortcuts
        QShortcut(QKeySequence("Ctrl+T"), self).activated.connect(self.new_session)
        QShortcut(QKeySequence("Ctrl+N"), self).activated.connect(self.new_session)
        QShortcut(QKeySequence("Ctrl+W"), self).activated.connect(self.close_current_session)
        QShortcut(QKeySequence("Ctrl+Tab"), self).activated.connect(self.next_session)
        QShortcut(QKeySequence("Ctrl+Shift+Tab"), self).activated.connect(self.prev_session)
        QShortcut(QKeySequence("Ctrl+Shift+T"), self).activated.connect(self.reopen_closed_session)
        QShortcut(QKeySequence("F5"), self).activated.connect(self.reset_current_session)
        # QShortcut(QKeySequence("F9"), self).activated.connect(self.toggle_follow_mode)
        # QShortcut(QKeySequence("F10"), self).activated.connect(self.change_api_backend)
    
    def new_session(self, tab_index=None):
        if tab_index is None:
            tab_index = self.count()
        session = Session(parent=self)
        self.insertTab(tab_index, session, "Session")
        self.setCurrentIndex(tab_index)
    
    def close_session(self, index, open_new=True):
        # Get the session
        session = self.widget(index)
        # Store session before closing
        self.closed_sessions.append(session.get_data())
        if len(self.closed_sessions) > 10: # Keep only the last 10
            self.closed_sessions.pop(0)
        logger.debug(f"Stored closed tab. Stack size: {len(self.closed_sessions)}")
        # Clean up resources in the session before removing
        session.clean_up_resources()
        # Remove the session from the UI
        self.removeTab(index)
        # Open a new session if none left
        if open_new and (self.count() == 0):
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
        session = Session(parent=self)
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
        # Clear existing tabs
        for idx in reversed(range(self.count())):
            self.close_session(idx, open_new=False)
        # Recreate sessions
        for session_data in session_data_all:
            session = Session(parent=self)
            session.set_data(session_data)
            self.addTab(session, "Session")
    
    def closeEvent(self, event):
        """Handle close event to clean up all sessions."""
        # Bug: why is this function never called?
        # Clean up resources for all sessions
        logger.debug(f"Cleaning up resources for {self.count()} sessions")
        for i in range(self.count()):
            session = self.widget(i)
            if session:
                session.clean_up_resources()
        # Allow event propagation to continue
        super().closeEvent(event)
