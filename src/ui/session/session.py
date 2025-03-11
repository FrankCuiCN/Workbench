import logging
from enum import Enum, auto
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import QTimer, QEvent, QThread, Qt
from ui.text_editor.text_editor import TextEditor
from ui.status_bar import StatusBar
from api.worker import Worker
from utils.parse_text import parse_text

logger = logging.getLogger(__name__)

class SessionState(Enum):
    IDLE = auto()
    WAITING = auto()
    THINKING = auto()
    GENERATING = auto()

class Session(QWidget):
    """A single instance of a text editing session"""
    def __init__(self, client=None, parent=None):
        super().__init__(parent)
        self.client = client
        # Set up layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        # Create text editor
        self.text_editor = TextEditor(self)
        self.text_editor.insertPlainText("Human:\n")
        # Add 10 lines to the end
        cursor_position = self.text_editor.textCursor().position()
        self.text_editor.insertPlainText("\n" * 10)  # Add empty lines
        cursor = self.text_editor.textCursor()  # Get current text cursor
        cursor.setPosition(cursor_position)  # Set cursor to stored position
        self.text_editor.setTextCursor(cursor)  # Apply cursor position to editor
        # stretch=1: expands to occupy available space
        layout.addWidget(self.text_editor, stretch=1)
        # Initialize session state
        self.session_state = SessionState.IDLE
        # Initialize worker
        self.worker = None
        # Install event filter on text editor to handle key events
        self.text_editor.installEventFilter(self)
        # Initialize the status bar
        self.status_bar = StatusBar(self)
        self.status_bar.update_session_status(self.session_state.name.lower())
        self.status_bar.update_following_status(self.text_editor.follow_mode)
        self.status_bar.update_read_only_status(self.text_editor.isReadOnly())
        layout.addWidget(self.status_bar)

    def set_session_state(self, state):
        """Update the session state"""
        self.session_state = state
        self.status_bar.update_session_status(state.name.lower())

    def set_read_only(self, enabled):
        self.text_editor.setReadOnly(enabled)
        self.status_bar.update_read_only_status(enabled)

    def generate_response(self, thinking_enabled=False):
        # Update UI state to waiting and set text editor to read only
        self.set_session_state(SessionState.WAITING)
        self.set_read_only(True)
        # Get current text from editor (now in read-only mode)
        current_text = self.text_editor.get_text()
        # Parse messages from text and check for syntax errors
        messages = parse_text(current_text)
        # If there is a syntax error then clean up and exit
        if messages is None:
            # Turn off read-only
            self.set_read_only(False)
            # Return to IDLE
            self.set_session_state(SessionState.IDLE)
            # Show error in red
            self.status_bar.show_error("Syntax Error")
            # Schedule Reset style after a wait
            # bug: (1) did not recover the original status bar content
            #      (2) does not ensure such task is singleton
            QTimer.singleShot(1000, self.status_bar.reset_style)
            return
        # Otherwise, create a worker and start it
        else:
            # Create a worker
            self.worker = Worker(self.client, messages, thinking_enabled)
            # Connect the signal
            self.worker.signal.connect(self.on_worker_event)
            # Start the worker
            self.worker.start()

    def on_worker_event(self, event_data):
        state, payload = event_data["state"], event_data["payload"]
        # Handle state updates
        if state == "waiting":
            # If first transitioning to WAITING
            if self.session_state != SessionState.WAITING:
                self.set_session_state(SessionState.WAITING)
        elif state == "thinking":
            # If first transitioning to THINKING
            if self.session_state != SessionState.THINKING:
                self.set_session_state(SessionState.THINKING)
        elif state == "generating":
            # If first transitioning to GENERATING
            if self.session_state != SessionState.GENERATING:
                self.text_editor.insert_at_end("\nAgent:\n")
                self.set_session_state(SessionState.GENERATING)
            self.text_editor.insert_at_end(payload)
        # If the worker is ending gracefully
        elif state == "ending":
            self.worker = None
            self.text_editor.insert_at_end("\nHuman:\n")
            # Flush the text animation, and then reset UI state
            def _callback():
                self.set_read_only(False)
                self.set_session_state(SessionState.IDLE)
            self.text_editor.flush_animation(_callback)
        # If the worker experienced an error
        elif state == "error":
            self.worker = None
            # Flush the text animation, and then reset UI state
            def _callback():
                self.set_read_only(False)
                self.set_session_state(SessionState.IDLE)
            self.text_editor.flush_animation(_callback)
        else:
            raise Exception()

    def clean_up_resources(self):
        """Clean up any resources used by this session"""
        logger.debug("Cleaning up session resources")
        # Halt the worker if active
        if self.worker:
            self.worker.request_stop()
            self.worker = None

    def focus(self):
        self.text_editor.setFocus()

    def eventFilter(self, source, event):
        if (source is self.text_editor) and (event.type() == QEvent.KeyPress):
            mods, key = event.modifiers(), event.key()
            if (mods == Qt.ControlModifier) and (key == Qt.Key_Return):
                self.key_press_ctrl_enter()
                return True
            elif (mods == Qt.ShiftModifier) and (key == Qt.Key_Return):
                self.key_press_shift_enter()
                return True
            elif (not mods) and (key == Qt.Key_Tab):
                self.key_press_tab()
                return True
            elif (not mods) and (key == Qt.Key_Escape):
                self.key_press_escape()
                return True
            elif (not mods) and (key == Qt.Key_F9):
                self.key_press_f9()
                return True
        return super().eventFilter(source, event)
    
    def key_press_ctrl_enter(self):
        if self.session_state == SessionState.IDLE:
            self.generate_response(thinking_enabled=False)
    
    def key_press_shift_enter(self):
        if self.session_state == SessionState.IDLE:
            self.generate_response(thinking_enabled=True)
    
    def key_press_tab(self):
        self.text_editor.insertPlainText("    ")
    
    def key_press_escape(self):
        if self.session_state != SessionState.IDLE:
            # Edge case: worker has ended, but text editor is still flushing the animation
            #     So SessionState is not IDLE
            if self.worker:
                logger.debug("Escape key pressed, halting the worker")
                self.worker.request_stop()
                # If already generating, add the human tag
                if self.session_state == SessionState.GENERATING:
                    self.text_editor.insert_at_end("\nHuman:\n")
                # Flush the text animation, and then reset UI state
                def _callback():
                    self.set_read_only(False)
                    self.set_session_state(SessionState.IDLE)
                self.text_editor.flush_animation(_callback)

    def key_press_f9(self):
        self.text_editor.set_follow_mode(not self.text_editor.follow_mode)
        self.status_bar.update_following_status(self.text_editor.follow_mode)
