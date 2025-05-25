import base64
import uuid
import logging
from typing import Callable
from PySide6.QtWidgets import QTextEdit
from PySide6.QtCore import Qt, QUrl, QByteArray, QBuffer, QTimer
from PySide6.QtGui import QFont, QImage, QTextDocument, QTextImageFormat
from ui.text_editor.syntax_highlighter import SyntaxHighlighter
from ui.text_editor.animated_insertion_manager import AnimatedInsertionManager

logger = logging.getLogger(__name__)


class TextEditor(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Disable rich text support, per the requirements
        self.setAcceptRichText(False)
        # Always show the vertical scrollbar
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        # Set custom font
        font = QFont("Sarasa Mono SC", 12)
        font.setFeature(QFont.Tag("calt"), 0)  # Disable ligatures
        font.setFeature(QFont.Tag("liga"), 0)
        font.setFeature(QFont.Tag("dlig"), 0)
        self.setFont(font)
        # Initialize external modules
        self.highlighter = SyntaxHighlighter(self.document())
        self.animation_manager = AnimatedInsertionManager(self)
        # Internal state for follow mode; default is False
        self.follow_mode = False
        # Logger: Initialization completion
        logger.debug("TextEditor initialized")

    def set_follow_mode(self, enabled: bool):
        """Set follow mode explicitly."""
        self.follow_mode = enabled
        logger.debug(f"Follow mode set to: {self.follow_mode}")

    def insertFromMimeData(self, source):
        """Override to handle pasted image content."""
        if source.hasImage():
            # Get image from source
            image = source.imageData()
            image = QImage(image)
            # Create a unique URL with UUID for the image
            image_url = QUrl("image://{}".format(str(uuid.uuid4())))
            # Add the image to the document's resources
            # Note: Images are not being garbage collected before session clean-up
            self.document().addResource(QTextDocument.ImageResource, image_url, image)
            # Create an image format and set its name to our URL
            imageFormat = QTextImageFormat()
            imageFormat.setName(image_url.toString())
            # Resize the image (only for display)
            imageFormat.setWidth(64)
            imageFormat.setHeight(64)
            # Insert the image at the cursor position using the format
            self.textCursor().insertImage(imageFormat)
        else:
            super().insertFromMimeData(source)

    def get_text(self):
        """
        Retrieve the text content with embedded images converted to base64 tags.
        Images are converted to tags like:
          <8442d621>base64-data</8442d621>
        """
        document = self.document()
        result_text = ""
        block = document.begin()
        while block.isValid():
            it = block.begin()
            while not it.atEnd():
                fragment = it.fragment()
                if fragment.isValid():
                    char_format = fragment.charFormat()
                    if char_format.isImageFormat():
                        image_format = char_format.toImageFormat()
                        image_url = image_format.name()
                        # Get the image resource from the document
                        image = document.resource(QTextDocument.ImageResource, QUrl(image_url))
                        if image is not None:
                            base64_data = self._image_to_base64(image)
                            result_text += f"<8442d621>{base64_data}</8442d621>"
                            logger.debug(f"Converted image with URL {image_url} to base64 tag")
                        else:
                            logger.error(f"Image resource not found: {image_url}")
                            raise Exception("unexpected error: image resource not found")
                    else:
                        # Append normal text fragments
                        result_text += fragment.text()
                it += 1
            block = block.next()
            # Add a newline between blocks (except after the final block)
            if block.isValid():
                result_text += "\n"
        return result_text

    def _image_to_base64(self, image):
        """Convert QImage to a base64 encoded PNG data string."""
        # Create a byte array to store the image data
        byte_array = QByteArray()
        # Create a buffer using the byte array
        buffer = QBuffer(byte_array)
        buffer.open(QBuffer.WriteOnly)
        # Save the image to the buffer in PNG format
        success = image.save(buffer, "PNG")
        if not success:
            logger.error("Failed to save image to buffer")
        # Make sure to close the buffer
        buffer.close()
        base64_data = base64.b64encode(byte_array.data()).decode('utf-8')
        return base64_data

    def insert_at_end(self, text, number_of_trailing_newline_characters=0):
        self.animation_manager.insert_at_end(text, number_of_trailing_newline_characters)

    def flush_animation(self, callback: Callable):
        # Workaround: The current implementation is based on polling (every 10 ms)
        if self.animation_manager.is_animating:
            # Schedule to call itself 10 ms later
            QTimer.singleShot(10, lambda: self.flush_animation(callback))
        else:
            callback()
