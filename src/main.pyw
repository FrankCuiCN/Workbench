# Obtain BASE_DIR before any other imports
# Note: (1) BASE_DIR must be respected throughout the codebase;
#     (2) CWD is not necessarily the directory containing the running file;
#     (3) Changing the CWD dynamically is not recommended
import os
import sys
# Check if the app is packaged by PyInstaller
if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Import other dependencies
import logging
from logging.handlers import RotatingFileHandler
from PySide6.QtWidgets import QApplication
from main_window import MainWindow


def setup_logging():
    log_dir = os.path.join(BASE_DIR, "logs")
    # Check if log directory exists, if not, create it
    os.makedirs(log_dir, exist_ok=True)
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            RotatingFileHandler(
                os.path.join(log_dir, "app.log"),
                maxBytes=5 * 1024 * 1024,
                backupCount=5
            )
        ]
    )
    # Set logger levels for different modules
    logging.getLogger("PySide6").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
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
