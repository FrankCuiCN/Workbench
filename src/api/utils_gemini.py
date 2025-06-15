import os
import base64
import logging
from google import genai
from google.genai.types import Part, Content
from google.genai.types import GenerateContentConfig, ThinkingConfig
from google.genai.types import Tool, GoogleSearch, UrlContext
from system_prompt.get_system_prompt import get_system_prompt

logger = logging.getLogger(__name__)
if "GEMINI_API_KEY" in os.environ:
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
else:
    client = None


def translate_messages(messages):
    """Translate internal message format to Gemini API content format"""
    contents = []
    for message in messages:
        content_items = message["content"]
        assert isinstance(content_items, list), "content must be a list"
        # Build parts for this message
        parts = []
        for item in content_items:
            if item["type"] == "text":
                # Add text part
                parts.append(Part.from_text(text=item["text"]))
            elif item["type"] == "image":
                # Add image part from base64
                media_type = item["source"]["media_type"]
                b64_data = item["source"]["data"]
                try:
                    image_bytes = base64.b64decode(b64_data)
                except Exception as e:
                    logger.error(f"Failed to decode image data: {e}")
                    continue
                parts.append(Part.from_bytes(data=image_bytes, mime_type=media_type))
        # Determine role (default to 'user' if not specified)
        role = message.get("role", "user")
        if role in ("developer", "system"):
            # System prompts will be handled via system_instruction (skip here)
            continue
        elif role in ("assistant", "model"):
            gemini_role = "model"
        else:
            gemini_role = "user"
        if parts:
            contents.append(Content(role=gemini_role, parts=parts))
    return contents

def get_stream(messages, response_mode):
    logger.debug(f"Sending messages to the API server")

    system_prompt = get_system_prompt()
    contents = translate_messages(messages)
    
    if response_mode == "normal":
        model = "gemini-2.5-pro-preview-06-05"
        config = GenerateContentConfig(
            system_instruction=system_prompt,
            thinking_config=ThinkingConfig(include_thoughts=True, thinking_budget=128),
        )
    elif response_mode == "thinking":
        model = "gemini-2.5-pro-preview-06-05"
        config = GenerateContentConfig(
            system_instruction=system_prompt,
            thinking_config=ThinkingConfig(include_thoughts=True, thinking_budget=32768),
        )
    elif response_mode == "advanced":
        model = "gemini-2.5-pro-preview-06-05"
        config = GenerateContentConfig(
            system_instruction=system_prompt,
            thinking_config=ThinkingConfig(include_thoughts=True, thinking_budget=32768),
            tools=[Tool(url_context=UrlContext()), Tool(google_search=GoogleSearch())],
        )
    else:
        raise Exception("Unexpected response_mode")
    
    stream = client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=config
    )
    return stream


def run(messages, response_mode, parent):
    # Debug: Gemini does not offer early stopping support yet
    stream = get_stream(messages, response_mode)
    for event in stream:
        # If stop requested
        if parent.stop_requested:
            # Exit ungracefully
            return False
        # Depending on the event content, determine state
        text_event = getattr(event, "text", None)
        if text_event is None:
            # Some events might not contain text (e.g., tool metadata); skip those
            continue
        if text_event == "":
            # Skip empty text events (no content to display)
            continue
        # If the model is outputting "thinking"/analysis segments:
        part = getattr(event, "part", None)
        # If event.part.thought is True, it indicates a thought segment.
        # Python's short-circuiting ensures the second getattr is not called on None.
        if part and getattr(part, "thought", False):
            # Known Issue: This part is not invoked
            parent.safe_signal_emit("thinking", None)
        else:
            # If no thought metadata is available, default to the "generating" state.
            parent.safe_signal_emit("generating", text_event)
    # Exit gracefully
    return True
