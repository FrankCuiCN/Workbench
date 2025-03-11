import os
import logging
import anthropic

# Set up logging
logger = logging.getLogger(__name__)

class Client:
    def __init__(self):
        # Create the anthropic client
        self.client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
        # Load system prompt from a local file
        system_prompt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "system_prompt.txt")
        with open(system_prompt_path, "r", encoding="utf-8") as f:
            self.system_prompt = f.read().strip()
        logger.info(f"Loaded system prompt from {system_prompt_path}")

    def get_stream(self, messages, thinking_enabled=True):
        logger.debug(f"Sending messages to the API server")
        # Configure thinking parameter based on thinking_enabled setting
        thinking_param = {"type": "enabled", "budget_tokens": 32000} if thinking_enabled else {"type": "disabled"}
        # Construct and return the stream object
        return self.client.messages.stream(
            system=self.system_prompt,
            messages=messages,
            model="claude-3-7-sonnet-20250219",
            temperature=1.0,
            max_tokens=64000,
            thinking=thinking_param
        )
