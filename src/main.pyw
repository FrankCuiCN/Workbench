# Set up proper file paths before any other imports
import os
import sys
# Detect if app is packaged by PyInstaller, then obtain the base directory
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Setting CWD to BASE_DIR; Reason: CWD is not necessarily where the file is
os.chdir(BASE_DIR)
# Import other dependencies
import logging
from PySide6.QtWidgets import QApplication
from main_window import MainWindow


def setup_logging():
    """Configure logging for the application"""
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(os.path.join(BASE_DIR, "app.log"))
        ]
    )
    # Set logger levels for different modules
    # logging.getLogger("PySide6").setLevel(logging.WARNING)
    # logging.getLogger("httpcore").setLevel(logging.WARNING)
    # logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("anthropic").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)


def main():
    """Main application entry point"""
    # Set up logging
    setup_logging()
    logger = logging.getLogger(__name__)
    logger.info("Application starting")
    # Create Qt application
    app = QApplication(sys.argv)
    # Set application-wide attributes
    app.setApplicationName("Workbench")
    # Create main window
    window = MainWindow()
    window.show()
    # Run application event loop
    logger.info("Entering main event loop")
    result = app.exec()
    # Clean up remaining resources
    logger.info("Main event loop finished; Cleaning up remaining resources")
    app.processEvents()
    # Exit application
    logger.info("Application exiting")
    sys.exit(result)


if __name__ == "__main__":
    main()
