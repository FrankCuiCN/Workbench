import os
import logging
import anthropic
from openai import OpenAI

# Set up logging
logger = logging.getLogger(__name__)

def translate_messages(system_prompt, messages):
    """Translate from Anthropic to OpenAI format"""
    # Step 1: Add system prompt as a developer message
    translated_messages = [{"role": "developer", "content": system_prompt}]
    
    # Step 2: Process each original message
    for message in messages:
        if message["role"] == "user" and isinstance(message["content"], list):
            # Case 3: User message with mixed content (text and images)
            new_content = []
            for item in message["content"]:
                if item["type"] == "text":
                    new_content.append(item)
                elif item["type"] == "image":
                    media_type = item["source"]["media_type"]
                    base64_data = item["source"]["data"]
                    new_content.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:{media_type};base64,{base64_data}"}
                    })
            translated_messages.append({"role": "user", "content": new_content})
        else:
            # Case 1 & 2: Simple user or assistant messages
            translated_messages.append(message)
    
    return translated_messages

class Client:
    # The following procedures is put here in order to promote reuse and to
    #     avoid overhead in __init__
    # Initialize both clients
    client_anthropic = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
    client_openai = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    # Load system prompt from a local file
    system_prompt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "system_prompt.txt")
    with open(system_prompt_path, "r", encoding="utf-8") as f:
        system_prompt = f.read().strip()
    logger.info(f"Loaded system prompt from {system_prompt_path}")
    
    def __init__(self, backend):
        # Define attributes
        self.backend = backend
        # Select the active client based on backend
        if self.backend == "anthropic":
            self.client = self.client_anthropic
        elif self.backend == "openai":
            self.client = self.client_openai
        else:
            raise Exception()

    def change_backend(self, backend):
        """Change the active backend to either 'anthropic' or 'openai'."""
        self.backend = backend
        if self.backend == "anthropic":
            self.client = self.client_anthropic
        elif self.backend == "openai":
            self.client = self.client_openai
        else:
            raise Exception(f"Unknown backend: {self.backend}")
        logger.info(f"Backend changed to {self.backend}")

    def get_stream(self, messages, thinking_enabled=True):
        logger.debug(f"Sending messages to the API server")
        if self.backend == "anthropic":
            # Configure thinking parameter based on thinking_enabled setting
            thinking_param = {"type": "enabled", "budget_tokens": 32000} if thinking_enabled else {"type": "disabled"}
            # Construct and return the stream object
            stream = self.client.messages.stream(
                system=self.system_prompt,
                messages=messages,
                model="claude-3-7-sonnet-20250219",
                temperature=1.0,
                max_tokens=64000,
                thinking=thinking_param
            )
            return stream
        elif self.backend == "openai":
            messages = translate_messages(self.system_prompt, messages)
            stream = self.client.chat.completions.create(
                model="gpt-4.5-preview-2025-02-27",
                messages=messages,
                stream=True
            )
            return stream
        else:
            raise Exception()
