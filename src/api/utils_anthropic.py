import os
import logging
import anthropic
from system_prompt.get_system_prompt import get_system_prompt

logger = logging.getLogger(__name__)
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))


def apply_cache_breakpoints(system_prompt, messages):
    """
    Apply 4 cache breakpoints to maximize cache hits:
    1. After system prompt
    2. At ~1/3 through messages
    3. At ~2/3 through messages
    4. At end of messages
    """
    # Breakpoint (1/4)
    system_prompt = [{"type": "text", "text": system_prompt, "cache_control": {"type": "ephemeral"}}]
    
    # Breakpoints (2/4 ~ 4/4)
    num_message = len(messages)
    if num_message == 1:
        idx_all = [0]
    elif num_message == 2:
        idx_all = [0, 1]
    elif num_message >= 3:
        idx_all = [idx * (num_message - 1) // 2 for idx in range(3)]
    else:
        Exception("Unexpected num_message")
    # Note: idx_all always includes the last message
    for idx in idx_all:
        messages[idx]["content"][-1]["cache_control"] = {"type": "ephemeral"}
    return system_prompt, messages


def get_stream(messages, response_mode):
    logger.debug(f"Sending messages to the API server")

    system_prompt = get_system_prompt()
    system_prompt, messages = apply_cache_breakpoints(system_prompt, messages)
    
    if response_mode == "normal":
        stream = client.messages.stream(
            system=system_prompt,
            messages=messages,
            model="claude-sonnet-4-20250514",
            temperature=1.0,
            max_tokens=32000,
            thinking={"type": "disabled"},
        )
        return stream
    
    if response_mode == "thinking":
        stream = client.messages.stream(
            system=system_prompt,
            messages=messages,
            model="claude-opus-4-20250514",
            temperature=1.0,
            max_tokens=32000,
            thinking={"type": "enabled", "budget_tokens": 31999},
        )
        return stream
    
    if response_mode == "research":
        tools = [{
            "type": "web_search_20250305",
            "name": "web_search",
            "max_uses": 10,
            "user_location": {"type": "approximate", "country": "US"},
        }]
        stream = client.messages.stream(
            system=system_prompt,
            messages=messages,
            model="claude-sonnet-4-20250514",  # Note: Opus is too expensive for multi-turn online research
            temperature=1.0,
            max_tokens=32000,
            thinking={"type": "enabled", "budget_tokens": 31999},
            tools=tools,
        )
        return stream
    raise Exception("Unexpected response_mode")


def run(messages, response_mode, parent):
    separate_next_tool_call = False
    with get_stream(messages, response_mode) as stream:
        for event in stream:
            # If stop requested
            if parent.stop_requested:
                # Update the logger
                logger.debug("The task is halting")
                # Exit ungracefully
                return False
            
            if event.type == "message_start":
                parent.signal.emit({"state": "thinking", "payload": None})
            
            # Issue: When the model writes text and then calls a tool, the API stream does not
            #   include a newline, causing later text be directed appended.
            # Workaround: We use a flag to detect when a text event is followed by a
            #   tool use event and manually insert a "\n\n" to create a visual break.
            if event.type == "content_block_start":
                if event.content_block.type == "server_tool_use":
                    if separate_next_tool_call:
                        parent.signal.emit({"state": "generating", "payload": "\n\n"})
                        separate_next_tool_call = False
            
            if event.type == "text":
                parent.signal.emit({"state": "generating", "payload": event.text})
                separate_next_tool_call = True
    # Exit gracefully
    return True
