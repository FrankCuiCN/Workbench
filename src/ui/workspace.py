import logging
from PySide6.QtWidgets import QTabWidget
from PySide6.QtGui import QShortcut, QKeySequence
from ui.session import Session

logger = logging.getLogger(__name__)

class Workspace(QTabWidget):
    """Workspace for handling multiple sessions."""
    def __init__(self, client=None):
        super().__init__()
        self.client = client
        # Configuration: Enable close buttons
        self.setTabsClosable(True)
        # Configuration: Allow tabs to be reordered
        self.setMovable(True)
        # Configuration: A cleaner look
        self.setDocumentMode(True)
        # Signal: Emitted when the close button on a tab is clicked
        self.tabCloseRequested.connect(self.close_session)
        # Signal: Emitted whenever the current page index changes
        self.currentChanged.connect(self.focus)
        # Register keyboard shortcuts
        self.register_shortcuts()
        # Create the first session
        self.add_new_session()
    
    def add_new_session(self):
        """Add a new session in the workspace."""
        session = Session(self.client, parent=self)
        # Add the session with a sequential number
        # bug: if only one session exists and its name is session 2, this will create another session called session 2
        tab_index = self.addTab(session, f"Session {self.count() + 1}")
        # Move to the new session and set focus
        self.setCurrentIndex(tab_index)
    
    def close_session(self, index):
        """Close the session at a given index"""
        # Get the session so we can properly clean it up
        session = self.widget(index)
        # Clean up resources in the session before removing
        session.clean_up_resources()
        # Remove the session from the UI
        self.removeTab(index)
        if self.count() == 0:
            # Create a new session if none left
            self.add_new_session()
    
    def close_current_session(self):
        """Close the currently active session"""
        current_index = self.currentIndex()
        self.close_session(current_index)
    
    def reset_current_session(self):
        """Reset the current session by closing it and replacing it with a new session in the same tab position with the same tab label."""
        current_index = self.currentIndex()
        if current_index < 0:
            return
        label = self.tabText(current_index)
        session = self.widget(current_index)
        if session:
            session.clean_up_resources()
        self.removeTab(current_index)
        new_session = Session(self.client, parent=self)
        self.insertTab(current_index, new_session, label)
        self.setCurrentIndex(current_index)
    
    def next_session(self):
        """Switch to the next session"""
        if self.count() > 1:
            next_index = (self.currentIndex() + 1) % self.count()
            self.setCurrentIndex(next_index)
    
    def prev_session(self):
        """Switch to the previous session"""
        if self.count() > 1:
            prev_index = (self.currentIndex() - 1) % self.count()
            # Move to the previous session
            self.setCurrentIndex(prev_index)
    
    def focus(self):
        """Focus on the current text editor"""
        session = self.currentWidget()
        # session could be None because after removing the last session,
        # focus() is called (cf currentChanged), current session is None in this case
        if session is not None:
            session.focus()

    def register_shortcuts(self):
        """Register keyboard shortcuts for session operations."""
        QShortcut(QKeySequence("Ctrl+T"), self).activated.connect(self.add_new_session)
        QShortcut(QKeySequence("Ctrl+N"), self).activated.connect(self.add_new_session)
        QShortcut(QKeySequence("Ctrl+W"), self).activated.connect(self.close_current_session)
        QShortcut(QKeySequence("Ctrl+Tab"), self).activated.connect(self.next_session)
        QShortcut(QKeySequence("Ctrl+Shift+Tab"), self).activated.connect(self.prev_session)
        QShortcut(QKeySequence("Ctrl+R"), self).activated.connect(self.reset_current_session)
        QShortcut(QKeySequence("F5"), self).activated.connect(self.reset_current_session)

    def closeEvent(self, event):
        """Handle close event to clean up all sessions."""
        # bug: why is this function never called?
        # Clean up resources for all tabs
        logger.debug(f"Cleaning up resources for {self.count()} sessions")
        for i in range(self.count()):
            session = self.widget(i)
            if session:
                session.clean_up_resources()
        # Allow event propagation to continue
        super().closeEvent(event)
