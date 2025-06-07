import os
import logging
from openai import OpenAI
from system_prompt.get_system_prompt import get_system_prompt

logger = logging.getLogger(__name__)
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def translate_messages(system_prompt, messages):
    """Translate from Anthropic to OpenAI format"""
    # Step 1: Add system prompt as a developer message
    messages_new = [{"role": "developer", "content": system_prompt}]
    # Step 2: Process each message
    for message in messages:
        content_old = message["content"]
        assert isinstance(content_old, list), "content must be a list"
        content_new = []
        for item in message["content"]:
            if item["type"] == "text":
                content_new.append({
                    "type": "input_text",
                    "text": item["text"],
                })
            elif item["type"] == "image":
                media_type = item["source"]["media_type"]
                base64_data = item["source"]["data"]
                content_new.append({
                    "type": "input_image",
                    "image_url": f"data:{media_type};base64,{base64_data}",
                })
        messages_new.append({"role": "user", "content": content_new})
    return messages_new


def get_stream(messages, response_mode):
    logger.debug(f"Sending messages to the API server")
    
    system_prompt = get_system_prompt()
    messages = translate_messages(system_prompt, messages)
    
    if response_mode == "normal":
        stream = client.responses.create(
            model="gpt-4.1",
            input=messages,
            stream=True,
            store=False,
        )
        return stream
    
    if response_mode == "thinking":
        stream = client.responses.create(
            model="o3",
            input=messages,
            stream=True,
            reasoning={"effort": "high", "summary": "detailed"},
            store=False,
        )
        return stream
    
    if response_mode == "research":
        stream = client.responses.create(
            model="gpt-4.1",
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
            
            if event.type == "response.reasoning_summary_text.delta":
                parent.signal.emit({"state": "thinking", "payload": None})
            
            if event.type == "response.output_text.delta":
                parent.signal.emit({"state": "generating", "payload": event.delta})
    # Exit gracefully
    return True
