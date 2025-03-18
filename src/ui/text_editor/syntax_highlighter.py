from PySide6.QtGui import QFont, QTextCharFormat, QColor, QSyntaxHighlighter

class SyntaxHighlighter(QSyntaxHighlighter):
    """
    Highlighter for message role labels in chat that highlights:
    1. A line with "User:" on its own
    2. A line with "Assistant:" on its own
    """
    def __init__(self, document):
        super().__init__(document)
        self.user_format = QTextCharFormat()
        self.user_format.setForeground(QColor(0, 200, 0))
        self.user_format.setFontWeight(QFont.Bold)
        self.assistant_format = QTextCharFormat()
        self.assistant_format.setForeground(QColor(200, 0, 0))
        self.assistant_format.setFontWeight(QFont.Bold)

    def highlightBlock(self, text):
        if text == "User:":
            self.setFormat(0, len(text), self.user_format)
        if text == "Assistant:":
            self.setFormat(0, len(text), self.assistant_format)