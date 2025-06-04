import os
import logging
import base64
import io
from PIL import Image
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

    def _resize_base64_image(self, base64_str, max_edge=2048):
        """Resize image so that its longest edge is <= max_edge."""
        image_data = base64.b64decode(base64_str)
        image = Image.open(io.BytesIO(image_data))
        width, height = image.size
        scale = min(1.0, float(max_edge) / max(width, height))
        if scale < 1.0:
            new_size = (int(width * scale), int(height * scale))
            image = image.resize(new_size, Image.LANCZOS)
            logger.debug(f"Resized image to {new_size[0]}x{new_size[1]}")
        else:
            new_size = (width, height)
        buffer = io.BytesIO()
        image.save(buffer, format="PNG")
        encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return encoded, new_size

    def _preprocess_images(self, messages):
        """Resize images in messages and log their dimensions."""
        processed = []
        for msg in messages:
            msg_copy = msg.copy()
            content = msg.get("content")
            if isinstance(content, list):
                new_content = []
                for item in content:
                    if item.get("type") == "image" and item.get("source", {}).get("type") == "base64":
                        data = item["source"]["data"]
                        data, size = self._resize_base64_image(data)
                        item = {**item, "source": {**item["source"], "data": data}}
                        logger.info(f"Sending image of size {size[0]}x{size[1]}")
                    new_content.append(item)
                msg_copy["content"] = new_content
            processed.append(msg_copy)
        return processed

    def get_stream(self, messages, thinking_enabled=True):
        logger.debug("Sending messages to the API server")
        messages = self._preprocess_images(messages)
        if self.backend == "anthropic":
            if thinking_enabled:
                stream = self.client.messages.stream(
                    system=self.system_prompt,
                    messages=messages,
                    model="claude-opus-4-20250514",
                    temperature=1.0,
                    max_tokens=32000,
                    thinking={"type": "enabled", "budget_tokens": 31999},
                )
            else:
                stream = self.client.messages.stream(
                    system=self.system_prompt,
                    messages=messages,
                    model="claude-sonnet-4-20250514",
                    temperature=1.0,
                    max_tokens=32000,
                    thinking={"type": "disabled"},
                )
            return stream
        elif self.backend == "openai":
            messages = translate_messages(self.system_prompt, messages)
            if thinking_enabled:
                stream = self.client.chat.completions.create(
                    model="o3",
                    messages=messages,
                    stream=True,
                    reasoning_effort="high",
                )
            else:
                stream = self.client.chat.completions.create(
                    model="gpt-4.1",
                    messages=messages,
                    stream=True,
                )
            return stream
        else:
            raise Exception()
