import logging
import win32con
from ctypes import windll, wintypes
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget, QApplication, QSystemTrayIcon, QMenu
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction
from ui.workspace import Workspace
from utils.app_icons import get_app_icon

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Configure window
        self.setWindowTitle("Workbench")
        self.resize(800, 600)
        self.setWindowIcon(get_app_icon())

        # Set up the main user interface
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        self.workspace = Workspace()
        layout.addWidget(self.workspace)
        QApplication.processEvents()
        # Focus on the workspace
        self.workspace.focus()

        # Hotkey IDs
        self.alt_o_id = 1
        self.alt_u_id = 2

        # Set up system tray and global hotkeys
        self.is_in_tray = False
        self.setup_system_tray()
        self.register_global_hotkeys()

    def setup_system_tray(self):
        """Configure system tray icon and menu"""
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(get_app_icon())
        # Create context menu with only exit option
        self.tray_menu = QMenu(self)
        quit_action = QAction("Exit", self)
        quit_action.triggered.connect(self.quit_application)
        self.tray_menu.addAction(quit_action)
        # Apply settings
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.setToolTip("Workbench")
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()

    def tray_icon_activated(self, reason):
        """Handle tray icon activation"""
        if reason == QSystemTrayIcon.DoubleClick:
            logger.debug("Tray icon double-clicked")
            self.show_window()

    def show_window(self):
        def _show_window():
            # Workaround: To prevent flicker when showing the window on Win 11
            # Procedure:
            #   (1) Add the 'minimized' state to the window
            #   (2) Show the window (when it's minimized, no flicker appears)
            #   (3) Remove the 'minimized' state to restore the window
            # Why this works:
            #   (1) Directly rendering the window causes a flicker on Windows 11
            #   (2) Rendering it in the taskbar (minimized) avoids the flicker
            #   (3) Restoring the window from minimized state is flicker-free
            self.setWindowState(self.windowState() | Qt.WindowMinimized)
            self.show()
            self.setWindowState(self.windowState() & ~Qt.WindowMinimized)
            self.activateWindow()
            self.is_in_tray = False
        if self.is_in_tray:
            logger.debug("Show window: already in tray, will show window")
            _show_window()
        else:
            logger.debug("Show window: not in tray; hide, delay, then show")
            self.hide_window()
            # Workaround: To accommodate moving between virtual desktops on Win11
            QTimer.singleShot(100, _show_window)

    def hide_window(self):
        """Hide window to system tray if not already hidden."""
        if not self.is_in_tray:
            logger.debug("Hide window: hiding window to tray")
            self.is_in_tray = True
            self.hide()

    def register_global_hotkeys(self):
        """Register global hotkeys."""
        try:
            # Register ALT+O
            result1 = windll.user32.RegisterHotKey(
                int(self.winId()),
                self.alt_o_id,
                win32con.MOD_ALT,
                ord('O')
            )
            if not result1:
                logger.warning("Failed to register global hotkey ALT+O")
            
            # Register ALT+U
            result2 = windll.user32.RegisterHotKey(
                int(self.winId()),
                self.alt_u_id,
                win32con.MOD_ALT,
                ord('U')
            )
            if not result2:
                logger.warning("Failed to register global hotkey ALT+U")

            return result1 and result2
        except Exception as e:
            logger.error(f"Hotkey registration exception: {e}")
            return False

    def unregister_global_hotkeys(self):
        """Unregister global hotkeys."""
        try:
            windll.user32.UnregisterHotKey(int(self.winId()), self.alt_o_id)
            windll.user32.UnregisterHotKey(int(self.winId()), self.alt_u_id)
            logger.debug("Global hotkeys unregistered")
        except Exception as e:
            logger.error(f"Error unregistering hotkeys: {e}")

    def quit_application(self):
        """Exit the application."""
        logger.info("Quit application requested")
        self.unregister_global_hotkeys()
        self.tray_icon.hide()
        QApplication.quit()

    def nativeEvent(self, eventType, message):
        """Handle native system events (such as global hotkeys)."""
        try:
            msg = wintypes.MSG.from_address(int(message))
            if msg.message == win32con.WM_HOTKEY:
                if msg.wParam == self.alt_o_id:
                    logger.debug("ALT+O hotkey detected")
                    self.show_window()
                    return True, 0
                elif msg.wParam == self.alt_u_id:
                    logger.debug("ALT+U hotkey detected")
                    self.hide_window()
                    return True, 0
        except Exception as e:
            logger.error(f"Error handling native event: {e}")
        return False, 0

    def closeEvent(self, event):
        """Handle window close event."""
        self.hide_window()
        event.ignore()
