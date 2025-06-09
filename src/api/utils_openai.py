import os
import logging
from openai import OpenAI
from system_prompt.get_system_prompt import get_system_prompt

logger = logging.getLogger(__name__)
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def translate_messages(messages):
    """Translate from Anthropic to OpenAI format"""
    messages_new = []
    for message in messages:
        role    = message["role"]
        content = message["content"]
        assert isinstance(content, list), "content must be a list"
        # Construct content_new
        content_new = []
        if role == "user":
            for item in content:
                if item["type"] == "text":
                    content_new.append({"type": "input_text", "text": item["text"]})
                elif item["type"] == "image":
                    media_type = item["source"]["media_type"]
                    base64_data = item["source"]["data"]
                    content_new.append({"type": "input_image", "image_url": f"data:{media_type};base64,{base64_data}"})
        elif role == "assistant":
            content_new = []
            for item in content:
                assert item["type"] == "text", "We expect assistant outputs to be text-only"
                content_new.append({"type": "output_text", "text": item["text"]})
        else:
            raise Exception("Unexpected role")
        # Append the new content to messages_new
        messages_new.append({"role": role, "content": content_new})
    return messages_new


def get_stream(messages, response_mode):
    logger.debug(f"Sending messages to the API server")
    
    system_prompt = get_system_prompt()
    messages = translate_messages(messages)
    
    if response_mode == "normal":
        stream = client.responses.create(
            model="gpt-4.1",
            instructions=system_prompt,
            input=messages,
            stream=True,
            store=False,
        )
        return stream
    elif response_mode == "thinking":
        stream = client.responses.create(
            model="o3",
            instructions=system_prompt,
            input=messages,
            stream=True,
            reasoning={"effort": "high", "summary": "detailed"},
            store=False,
        )
        return stream
    elif response_mode == "research":
        stream = client.responses.create(
            model="gpt-4.1",
            instructions=system_prompt,
            input=messages,
            stream=True,
            store=False,
            tools=[{
                "type": "web_search_preview",
                "search_context_size": "high",
                "user_location": {
                    "type": "approximate",
                    "country": "US",
                },
            }],
        )
        return stream
    else:
        raise Exception("Unexpected response_mode")


def run(messages, response_mode, parent):
    with get_stream(messages, response_mode) as stream:
        for event in stream:
            # If stop requested
            if parent.stop_requested:
                # Update the logger
                logger.debug("The task is halting")
                # Exit ungracefully
                return False

            # Debug: refusal is not being handled
            
            if event.type == "response.reasoning_summary_text.delta":
                parent.signal.emit({"state": "thinking", "payload": None})
            
            if event.type == "response.output_text.delta":
                parent.signal.emit({"state": "generating", "payload": event.delta})

    # Exit gracefully
    return True
