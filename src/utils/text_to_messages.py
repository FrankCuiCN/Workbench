import logging
logger = logging.getLogger(__name__)

def jump_to_next(text):
    """
    Jump to the next user/assistant pattern
    Returns the role (user/assistant/None)
    Returns the content before the pattern
    Returns the remaining text
    """
    user_pattern = "\nHuman:\n"
    assistant_pattern = "\nAgent:\n"

    idx_human = text.find(user_pattern)
    idx_agent = text.find(assistant_pattern)

    idx_human = float("inf") if idx_human == -1 else idx_human
    idx_agent = float("inf") if idx_agent == -1 else idx_agent

    if (idx_human == float("inf")) and (idx_agent == float("inf")):
        # No more patterns found
        return None, text, ""
    elif idx_human < idx_agent:
        # Human pattern is next
        content = text[:idx_human]
        remaining_text = text[idx_human + len(user_pattern):]
        return "user", content, remaining_text
    else:
        # Agent pattern is next
        content = text[:idx_agent]
        remaining_text = text[idx_agent + len(assistant_pattern):]
        return "assistant", content, remaining_text


def process_text_with_image_tags(content):
    """
    Process content with embedded image tags in the format <8442d621>base64-data</8442d621>
    Returns a list of content blocks (text and image)
    """
    import re

    # Regular expression to find image tags (now without UUID suffix)
    image_pattern = r'<8442d621>(.*?)</8442d621>'

    # Find all image tags in the text
    image_matches = re.finditer(image_pattern, content)

    # Combine and sort all matches by their position in the text
    all_matches = []
    for match in image_matches:
        all_matches.append(('image', match.start(), match.end(), match.group(1)))

    if not all_matches:
        # No image tags, just return the text content
        logger.debug(f"No image tags found, returning text only")
        return [{"type": "text", "text": content}]

    logger.debug(f"Found {len(all_matches)} image tags in text")

    content_blocks = []
    last_end = 0

    # Process each match in order
    for match_type, start, end, data in all_matches:
        # Add the text before the tag
        if start > last_end:
            text_before = content[last_end:start]
            if text_before:
                content_blocks.append({"type": "text", "text": text_before})
        # Add the image block
        if match_type == 'image':
            logger.debug(f"Adding image with base64 data length: {len(data)}")
            content_blocks.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": data
                }
            })
        last_end = end

    # Add any remaining text
    if last_end < len(content):
        remaining_text = content[last_end:]
        if remaining_text:
            content_blocks.append({"type": "text", "text": remaining_text})

    logger.debug(f"Created {len(content_blocks)} content blocks")

    return content_blocks


def text_to_messages(text):
    """
    Constructs messages and validates them
    Returns the messages if valid, otherwise None

    Args:
        text: The text content with possible embedded image tags
    """
    logger.debug("text_to_messages called")

    # Define patterns
    init_pattern = "Human:\n"

    # Validation 001: Must start with init_pattern
    if not text.startswith(init_pattern):
        logger.warning("Validation failed: Message must start with 'Human:'")
        return None

    # Preparation
    text = text[len(init_pattern):]
    messages = []
    current_role = "user"

    # Start constructing messages
    while True:
        next_role, current_content, text = jump_to_next(text)
        # Validation 002: Must alternate between user and assistant
        if current_role == next_role:
            logger.warning(f"Validation failed: Messages must alternate between user and assistant (found {current_role} followed by {next_role})")
            return None
        # Validation 003: Content cannot be empty
        if current_content == "":
            logger.warning("Validation failed: Message content cannot be empty")
            return None
            
        # Process the content
        if current_role == "user":
            # For user messages, check for image tags and process
            logger.debug(f"Processing user message for image tags")
            content_blocks = process_text_with_image_tags(current_content)
            messages.append({"role": "user", "content": content_blocks})
        else:  # "assistant"
            # For assistant messages, use text only
            # Anthropic API requires content to be a string for assistant messages
            messages.append({"role": "assistant", "content": current_content})
            
        if next_role is None:
            # Validation 004: Must end with user message
            if current_role == "assistant":
                logger.warning("Validation failed: Conversation must end with a user message")
                return None
            return messages
        current_role = next_role
