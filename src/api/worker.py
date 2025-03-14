import logging
import threading
from PySide6.QtCore import QObject, Signal

logger = logging.getLogger(__name__)

class Worker(QObject):
    # Unified signal for all worker events
    signal = Signal(dict)
    def __init__(self, client, messages, thinking_enabled=True):
        super().__init__()
        # Initialize attributes
        self.client = client
        self.messages = messages
        self.thinking_enabled = thinking_enabled
        self.stop_requested = False
        # debug: a bit convoluted
        # Preferably, the client should provide a unified interface
        #     so that worker does not need to care about the backend
        self.backend = client.backend

    def start(self):
        thread = threading.Thread(target=self._background_task)
        thread.daemon = True
        thread.start()

    def request_stop(self):
        self.stop_requested = True

    def _background_task(self):
        try:
            # Emit initial state
            self.signal.emit({"state": "waiting", "payload": None})
            # Process the stream
            with self.client.get_stream(self.messages, self.thinking_enabled) as stream:
                for event in stream:
                    # If stop requested
                    if self.stop_requested:
                        logger.debug("The task is halting")
                        # End the background task
                        return
                    # If backend is Anthropic
                    if self.backend == "anthropic":
                        # If thinking related
                        condition_1 = (event.type == "content_block_start" and hasattr(event, 'content_block') and event.content_block.type in ("thinking", "redacted_thinking"))
                        condition_2 = (event.type == "content_block_delta" and hasattr(event, 'delta') and event.delta.type == "thinking_delta")
                        condition_3 = (event.type == "content_block_stop" and hasattr(event, 'content_block') and event.content_block.type in ("thinking", "redacted_thinking"))
                        if condition_1 or condition_2 or condition_3:
                            self.signal.emit({"state": "thinking", "payload": None})
                        # If not thinking related
                        else:
                            # For text deltas, emit generating state with text content
                            if (event.type == "content_block_delta") and (event.delta.type == "text_delta"):
                                self.signal.emit({"state": "generating", "payload": event.delta.text})
                    # Else, if backend is OpenAI
                    elif self.backend == "openai":
                        delta = event.choices[0].delta.content
                        if delta is not None:
                            self.signal.emit({"state": "generating", "payload": delta})
            self.signal.emit({"state": "ending", "payload": None})
            return
        except Exception as e:
            logger.error(f"Worker exception: {e}")
            self.signal.emit({"state": "error", "payload": str(e)})
