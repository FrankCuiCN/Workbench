"""
This module is the single source of truth for the application icon
"""
from PySide6.QtWidgets import QStyle, QApplication
from PySide6.QtGui import QIcon


def get_app_icon() -> QIcon:
    return QApplication.style().standardIcon(QStyle.SP_FileDialogListView)
