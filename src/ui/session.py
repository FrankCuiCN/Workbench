import logging
from enum import Enum, auto
from PySide6.QtCore import QEvent, Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QDialog, QLineEdit
from api.worker import Worker
from ui.status_bar.local_status_bar import LocalStatusBar
from ui.text_editor.text_editor import TextEditor
from utils.parse_text import parse_text

logger = logging.getLogger(__name__)


class SessionState(Enum):
    IDLE = auto()
    WAITING = auto()
    THINKING = auto()
    GENERATING = auto()


class Session(QWidget):
    """A single instance of a text editing session"""
    def __init__(self, parent):
        # Note: Session relies on the self-deletion pattern for clean-up
        super().__init__(parent=None)
        # Define attributes
        self.workspace = parent
        self.search_text = ""
        # Set up layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        # Create text editor
        self.text_editor = TextEditor()
        self.text_editor.insertPlainText("User:\n")
        # Add multiple lines to the end
        # Workaround: Enable scrolling past the last line
        cursor_position = self.text_editor.textCursor().position()
        self.text_editor.insertPlainText(20 * "\n")  # Add empty lines
        cursor = self.text_editor.textCursor()  # Get current text cursor
        cursor.setPosition(cursor_position)     # Set cursor to stored position
        self.text_editor.setTextCursor(cursor)  # Apply cursor position to editor
        # stretch=1: expands to occupy available space
        layout.addWidget(self.text_editor, stretch=1)
        # Initialize session state
        self.session_state = SessionState.IDLE
        # Initialize worker
        self.worker = None
        # Install event filter on text editor to handle key events
        self.text_editor.installEventFilter(self)
        # Initialize the local status bar
        self.status_bar = LocalStatusBar(self)
        self.status_bar.update_session_status(self.session_state.name.lower())
        self.status_bar.update_read_only_status(self.text_editor.isReadOnly())
        layout.addWidget(self.status_bar)
        # Workaround for scrolling past the last line
        #     New attribute required to store trailing newline count
        self.number_of_trailing_newline_characters = 0

    def set_session_state(self, state):
        """Update the session state"""
        self.session_state = state
        self.status_bar.update_session_status(state.name.lower())

    def set_read_only(self, enabled):
        self.text_editor.setReadOnly(enabled)
        self.status_bar.update_read_only_status(enabled)

    def generate_response(self, response_mode):
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
            self.status_bar.show_syntax_error()
            return
        # Otherwise, create a worker and start it
        else:
            # Workaround for scrolling beyond the last line:
            #     Calculate and update "num_of_trailing_newline_characters"
            trailing_newlines = 0
            index = len(current_text) - 1
            while index >= 0 and current_text[index] == "\n":
                trailing_newlines += 1
                index -= 1
            self.number_of_trailing_newline_characters = trailing_newlines
            # Create a worker
            self.worker = Worker(self.workspace.backend, messages, response_mode)
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
                self.text_editor.insert_at_end("\nAssistant:\n", self.number_of_trailing_newline_characters)
                self.set_session_state(SessionState.GENERATING)
            self.text_editor.insert_at_end(payload, self.number_of_trailing_newline_characters)
        # If the worker is ending gracefully
        elif state == "ending":
            # Clean up and remove the worker
            self.remove_worker()
            # Insert the user tag
            self.text_editor.insert_at_end("\nUser:\n", self.number_of_trailing_newline_characters)
            # Flush the text animation, and then reset UI state
            self.text_editor.flush_animation(self.reset_ui_state)
        # If the worker experienced an error
        elif state == "error":
            # Clean up and remove the worker
            self.remove_worker()
            # Insert the error message
            self.text_editor.insert_at_end("\n<Error: {}>".format(payload), self.number_of_trailing_newline_characters)
            # Flush the text animation, and then reset UI state
            self.text_editor.flush_animation(self.reset_ui_state)
        else:
            raise Exception()
    
    def eventFilter(self, source, event):
        if (source is self.text_editor) and (event.type() == QEvent.KeyPress):
            mods, key = event.modifiers(), event.key()
            # Ctrl+Enter
            if mods == Qt.ControlModifier:
                if key == Qt.Key_Return:
                    self.key_press_ctrl_enter()
                    return True
            # Shift+Enter
            if mods == Qt.ShiftModifier:
                if key == Qt.Key_Return:
                    self.key_press_shift_enter()
                    return True
            # Ctrl+Shift+Enter
            if mods == (Qt.ControlModifier | Qt.ShiftModifier):
                if key == Qt.Key_Return:
                    self.key_press_ctrl_shift_enter()
                    return True
            # Tab
            if not mods:
                if key == Qt.Key_Tab:
                    self.key_press_tab()
                    return True
            # Esc
            if not mods:
                if key == Qt.Key_Escape:
                    self.key_press_escape()
                    return True
            # Ctrl+F
            if mods == Qt.ControlModifier:
                if key == Qt.Key_F:
                    self.show_search_dialog()
                    return True
            # F3
            if not mods:
                if key == Qt.Key_F3:
                    self.find_next()
                    return True
        return super().eventFilter(source, event)
    
    def key_press_ctrl_enter(self):
        if self.session_state == SessionState.IDLE:
            self.generate_response(response_mode="normal")
    
    def key_press_shift_enter(self):
        if self.session_state == SessionState.IDLE:
            self.generate_response(response_mode="thinking")

    def key_press_ctrl_shift_enter(self):
        if self.session_state == SessionState.IDLE:
            self.generate_response(response_mode="advanced")
    
    def key_press_tab(self):
        self.text_editor.insertPlainText("    ")
    
    def key_press_escape(self):
        if self.session_state != SessionState.IDLE:
            # Edge case: worker has ended, but text editor is still flushing the animation
            #     So SessionState is not IDLE
            if self.worker:
                logger.debug("Escape key pressed, halting the worker")
                # Clean up and remove the worker
                self.remove_worker()
                # If already generating, add the User tag
                if self.session_state == SessionState.GENERATING:
                    self.text_editor.insert_at_end("\nUser:\n", self.number_of_trailing_newline_characters)
                # Flush the text animation, and then reset UI state
                self.text_editor.flush_animation(self.reset_ui_state)
    
    def reset_ui_state(self):
        # Turn off read-only
        self.set_read_only(False)
        # Update session state
        self.set_session_state(SessionState.IDLE)
    
    def get_data(self):
        # Note: get_data() should not interfere with session activities
        return {"text_content": self.text_editor.toPlainText()}
    
    def set_data(self, data):
        # Note: We assume set_data() is always used with a new session
        #   That is, we don't worry about session activities
        # Set content
        self.text_editor.setPlainText(data["text_content"])
        # Set cursor to the top
        cursor = self.text_editor.textCursor()
        cursor.setPosition(0)
        self.text_editor.setTextCursor(cursor)

    def remove_worker(self):
        if self.worker:
            self.worker.clean_up_resources()
            self.worker = None

    def clean_up_resources(self):
        """Clean up any resources used by this session"""
        logger.debug("Cleaning up session resources")
        # Clean up and remove the worker
        self.remove_worker()
        # Clean up text editor resources
        self.text_editor.clean_up_resources()
        # Self-deletion
        self.deleteLater()
    
    def focus(self):
        self.text_editor.setFocus()
    
    def show_search_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Enter: Submit        F3: Find Next")
        dialog.setModal(True)  # Note: Prevent interaction with main window
        dialog.setFixedWidth(400)
        layout = QVBoxLayout(dialog)
        line_edit = QLineEdit(self.search_text, dialog)
        layout.addWidget(line_edit)
        def _submit():
            self.search_text = line_edit.text()
            dialog.accept()
        line_edit.returnPressed.connect(_submit)
        dialog.exec()
    
    def find_next(self):
        if not self.search_text:
            return
        # Get current cursor position
        cursor = self.text_editor.textCursor()
        # Search forward from current position
        # Note: By default find() is case insensitive (PySide 6.9)
        found_cursor = self.text_editor.document().find(self.search_text, cursor)
        # If not found, wrap around to the beginning
        if found_cursor.isNull():
            found_cursor = self.text_editor.document().find(self.search_text, 0)
        # If still not found, nothing to do
        if found_cursor.isNull():
            return
        # Select the found text
        self.text_editor.setTextCursor(found_cursor)
        self.text_editor.ensureCursorVisible()
