import logging
import threading
from PySide6.QtCore import QObject, Signal
from api import utils_anthropic
from api import utils_openai
from api import utils_gemini

logger = logging.getLogger(__name__)

class Worker(QObject):
    signal = Signal(dict)
    
    def __init__(self, backend, messages, response_mode, parent=None):
        super().__init__(parent)
        # Initialize attributes
        self.backend = backend
        self.messages = messages
        self.response_mode = response_mode
        self.stop_requested = False

    def _background_task(self):
        try:
            # Emit initial state
            self.signal.emit({"state": "waiting", "payload": None})
            
            if self.backend == "anthropic":
                graceful = utils_anthropic.run(self.messages, self.response_mode, parent=self)
            elif self.backend == "openai":
                graceful = utils_openai.run(self.messages, self.response_mode, parent=self)
            elif self.backend == "gemini":
                graceful = utils_gemini.run(self.messages, self.response_mode, parent=self)
            else:
                raise Exception("Unexpected backend")
            
            # Note: "ending" implies a graceful exit
            if graceful:
                self.signal.emit({"state": "ending", "payload": None})
        except Exception as e:
            logger.error(f"Worker exception: {e}")
            self.signal.emit({"state": "error", "payload": str(e)})

    
    def _background_task_with_cleanup(self):
        self._background_task()
        # Self-Deletion
        logger.debug("Calling deleteLater on Worker")
        self.deleteLater()

    def start(self):
        thread = threading.Thread(target=self._background_task_with_cleanup)
        thread.daemon = True
        thread.start()

    def request_stop(self):
        logger.debug("The task is requested to stop")
        self.stop_requested = True
