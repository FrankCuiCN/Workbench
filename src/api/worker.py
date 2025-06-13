import logging
import threading
from PySide6.QtCore import QObject, Signal
from api import utils_anthropic
from api import utils_openai
from api import utils_gemini

logger = logging.getLogger(__name__)

class Worker(QObject):
    signal = Signal(dict)
    
    def __init__(self, backend, messages, response_mode):
        # Note: Worker relies on the self-deletion pattern for clean-up
        super().__init__(parent=None)
        # Initialize attributes
        self.backend = backend
        self.messages = messages
        self.response_mode = response_mode
        self.stop_requested = False

    def _background_task(self):
        try:
            # Emit initial state
            self.safe_signal_emit("waiting", None)
            
            # Known Issue: The background task can hang if this part never returns
            #   This would prevent the thread from ending, causing a memory leak
            if self.backend == "openai":
                graceful = utils_openai.run(self.messages, self.response_mode, parent=self)
            elif self.backend == "anthropic":
                graceful = utils_anthropic.run(self.messages, self.response_mode, parent=self)
            elif self.backend == "gemini":
                graceful = utils_gemini.run(self.messages, self.response_mode, parent=self)
            else:
                raise Exception("Unexpected backend")
            
            # Note: "ending" implies a graceful exit
            if graceful:
                self.safe_signal_emit("ending", None)
        except Exception as e:
            logger.error(f"Worker exception: {e}")
            self.safe_signal_emit("error", str(e))
        logger.debug("Exiting the thread")

    def safe_signal_emit(self, state, payload):
        # Note: This wrapper ensures that workers requested to stop do not emit signals
        if not self.stop_requested:
            self.signal.emit({"state": state, "payload": payload})

    def start(self):
        thread = threading.Thread(target=self._background_task)
        thread.daemon = True
        thread.start()

    def clean_up_resources(self):
        logger.debug("Requesting Worker to stop")
        self.stop_requested = True
        # Self-Deletion
        logger.debug("Calling deleteLater on Worker")
        self.deleteLater()
