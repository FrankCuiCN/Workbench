from PySide6.QtGui import QFont, QTextCharFormat, QColor, QSyntaxHighlighter

class SyntaxHighlighter(QSyntaxHighlighter):
    """
    Highlighter for message role labels in chat that highlights:
    1. A line with "Human:" on its own
    2. A line with "Agent:" on its own
    """
    def __init__(self, document):
        super().__init__(document)
        self.human_format = QTextCharFormat()
        self.human_format.setForeground(QColor(0, 200, 0))
        self.human_format.setFontWeight(QFont.Bold)
        self.agent_format = QTextCharFormat()
        self.agent_format.setForeground(QColor(200, 0, 0))
        self.agent_format.setFontWeight(QFont.Bold)

    def highlightBlock(self, text):
        if text == "Human:":
            self.setFormat(0, len(text), self.human_format)
        if text == "Agent:":
            self.setFormat(0, len(text), self.agent_format)