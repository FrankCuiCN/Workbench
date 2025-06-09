import re
import logging

logger = logging.getLogger(__name__)


def parse_text(text):
    # Known Issue: Current layout appends a number of newline characters to allow scrolling past the last line
    # Workaround: Strip whitespace characters
    text = text.strip()
    
    # Split the text into lines
    lines = text.split("\n")
    
    # Identify anchor indices where lines are exactly "User:" or "Assistant:"
    anchor_indices = [idx for idx, line in enumerate(lines) if line == "User:" or line == "Assistant:"]
    
    # Validate that the text starts with "User:"
    if not anchor_indices or lines[anchor_indices[0]] != "User:":
        # Text must start with "User:"
        logger.debug("parse_text: Text must start with 'User:'")
        return None
    
    # Process each anchor and its content
    messages = []
    for idx in range(len(anchor_indices)):
        anchor_line = lines[anchor_indices[idx]]
        # Determine the role based on the anchor
        if anchor_line == "User:":
            role = "user"
        elif anchor_line == "Assistant:":
            role = "assistant"
        else:
            raise Exception("Unexpected error")
        # Extract content lines between current anchor and next anchor (or end)
        if idx < len(anchor_indices) - 1:
            content_lines = lines[anchor_indices[idx] + 1: anchor_indices[idx + 1]]
        else:
            content_lines = lines[anchor_indices[idx] + 1:]
        # Reconstruct content by joining lines with newlines
        content = "\n".join(content_lines)
        # Check if content is empty (violates rule 3)
        if not content:
            # All content must not be empty
            logger.debug("parse_text: All content must not be empty")
            return None
        # Construct content_list
        if not re.search(r"<8442d621>.*?</8442d621>", content):
            # No images
            content_list = [{"type": "text", "text": content}]
        else:
            # Split content into parts based on image tags
            parts = re.split(r'(<8442d621>.*?</8442d621>)', content)
            content_list = []
            # Process each part
            for part in parts:
                if re.match(r'<8442d621>.*?</8442d621>', part):
                    # Extract base64 string from image tag
                    base64_str = re.match(r'<8442d621>(.*?)</8442d621>', part).group(1)
                    content_list.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": base64_str,
                        },
                    })
                else:
                    # Known Issue: re.split introduces empty strings
                    # Workaround: ignore them
                    if part != "":
                        # Add text part, including empty strings
                        content_list.append({
                            "type": "text",
                            "text": part,
                        })
        # Add to messages
        messages.append({"role": role, "content": content_list})

    # Validate alternating roles and ending with "user"
    if len(messages) > 1:
        for idx in range(len(messages) - 1):
            if messages[idx]["role"] == messages[idx + 1]["role"]:
                # Roles must alternate between 'user' and 'assistant'
                logger.debug("parse_text: Roles must alternate between 'user' and 'assistant'")
                return None
    if messages and messages[-1]["role"] != "user":
        # Messages must end with 'user' role
        logger.debug("parse_text: Messages must end with 'user' role")
        return None
    return messages
