from PySide6.QtCore import QTimer
from PySide6.QtGui import QTextCursor


class AnimatedInsertionManager:
    """
    Manages the animated insertion of text at the end of a QTextEdit document.

    This class encapsulates the logic required for inserting text with an animation effect,
    character by character, into a text editor widget. The animation speed dynamically adjusts
    based on the total number of pending characters, ensuring a smooth and responsive user experience.

    Key responsibilities:
    - Maintaining a queue of text strings to insert.
    - Handling the insertion of text one character at a time with a QTimer.
    - Calculating an insertion offset to account for trailing newline characters in the text editor.
    - Dynamically adjusting the speed of insertion based on the number of characters left to process.

    The class interacts with the TextEditor instance by manipulating its QTextCursor to
    append characters, ensuring that visible changes are smoothly animated.
    """
    
    def __init__(self, text_editor, ignore_trailing_newline=True):
        # Store a reference to the associated TextEditor instance.
        self.text_editor = text_editor
        # Determines whether to ignore trailing newline characters during insertion.
        self.ignore_trailing_newline = ignore_trailing_newline
        # Queue to hold pending text strings for animated insertion.
        self.queue = []
        # The text string currently being processed for animation.
        self.current_text = None
        # Index of the next character to be inserted from current_text.
        self.current_index = 0
        # Flag indicating whether an animation is currently in progress.
        self.is_animating = False
        # QTimer object for scheduling character insertion with varying speeds.
        self.timer = QTimer(self.text_editor)
        # Set the timer to fire only once per start.
        self.timer.setSingleShot(True)
        # Connect the timer's timeout signal to the method that processes the next character.
        self.timer.timeout.connect(self._process_animation)
        # Tracks the total number of characters pending insertion across all queued texts.
        self.total_pending_chars = 0
        # Determines an offset for insertion, used to handle trailing newline characters.
        self.insertion_offset = 0
    
    def _process_animation(self):
        """
        Process the insertion of characters one at a time.

        This method is called each time the QTimer fires. It performs the following steps:
        1. Check if there is any pending text in the queue or current_text is being processed.
           If nothing is pending, stop the animation.
        2. If there is no current_text but the queue is non-empty, dequeue the next text for processing.
        3. Insert the next character from current_text at the end of the text editor.
           If an insertion offset is set (due to trailing newlines), adjust the cursor appropriately.
        4. Update the current_index and recalculate the remaining characters.
        5. Dynamically determine the delay for the next character based on the total pending characters.
        6. Schedule the next call to _process_animation using the QTimer.
        """
        # If there is no more text to process, stop the animation and reset state.
        if not self.queue and self.current_text is None:
            self.is_animating = False
            self.timer.stop()
            self.total_pending_chars = 0
            self.insertion_offset = 0
            return
        
        # If there is no current text chunk but the queue has pending texts,
        # then start processing the next text chunk.
        if self.current_text is None and self.queue:
            self.current_text = self.queue.pop(0)
            self.current_index = 0
        
        # If the current text chunk still has characters to be inserted:
        if self.current_text and self.current_index < len(self.current_text):
            # Retrieve the next character to insert.
            char = self.current_text[self.current_index]
            # Create a separate QTextCursor for the entire document.
            cursor = QTextCursor(self.text_editor.document())
            # Move the cursor to the end of the document.
            cursor.movePosition(QTextCursor.End)
            # Move the cursor backwards by 'insertion_offset' characters.
            cursor.movePosition(QTextCursor.PreviousCharacter, QTextCursor.MoveAnchor, self.insertion_offset)
            # Insert the character at the current cursor position.
            cursor.insertText(char)
            # Move to the next character in the current text chunk.
            self.current_index += 1
            # Calculate the number of remaining characters in the current text chunk.
            remaining_in_current = len(self.current_text) - self.current_index
            # Update the total pending characters by summing remaining characters and the lengths of queued texts.
            self.total_pending_chars = remaining_in_current + sum(len(t) for t in self.queue)
            # Adjust speed based on how many characters are left in total.
            if self.total_pending_chars < 25:
                speed = 16
            elif self.total_pending_chars < 50:
                speed = 8
            elif self.total_pending_chars < 100:
                speed = 4
            elif self.total_pending_chars < 200:
                speed = 2
            else:
                speed = 0
            # Schedule the next character insertion by starting the timer with the calculated delay.
            self.timer.start(speed)
        else:
            # If the current text chunk is fully processed, reset current_text and immediately process the next.
            self.current_text = None
            self._process_animation()
    
    def insert_at_end(self, text, number_of_trailing_newline_characters=0):
        """Queue new text for animated insertion at the end of the text editor."""
        # If no animation is currently running
        if not self.is_animating:
            if self.ignore_trailing_newline:
                self.insertion_offset = number_of_trailing_newline_characters
            else:
                self.insertion_offset = 0
        # Increase the counter for total pending characters by the length of the new text.
        self.total_pending_chars += len(text)
        # Add the new text to the queue for animated insertion.
        self.queue.append(text)
        # If no animation is currently running, enable the animation flag and start processing.
        if not self.is_animating:
            self.is_animating = True
            self._process_animation()
