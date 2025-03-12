import re
import logging

logger = logging.getLogger(__name__)


def parse_text(text):
    # Workaround: The current layout appends a number of
    #     \n characters at the end to allow for scrolling beyond the last line.
    text = text.strip()  # Debug: Remove this after updating to the new layout
    
    # Split the text into lines
    lines = text.split("\n")
    
    # Identify anchor indices where lines are exactly "Human:" or "Agent:"
    anchor_indices = [i for i, line in enumerate(lines) if
                      line == "Human:" or line == "Agent:"]
    
    # Validate that the text starts with "Human:"
    if not anchor_indices or lines[anchor_indices[0]] != "Human:":
        # Text must start with 'Human:'
        print("Text must start with 'Human:'")
        return None
    
    messages = []
    
    # Process each anchor and its content
    for j in range(len(anchor_indices)):
        anchor_line = lines[anchor_indices[j]]
        
        # Determine the role based on the anchor
        if anchor_line == "Human:":
            role = "user"
        elif anchor_line == "Agent:":
            role = "assistant"
        else:
            raise Exception("Unexpected error")
        
        # Extract content lines between current anchor and next anchor (or end)
        if j < len(anchor_indices) - 1:
            content_lines = lines[anchor_indices[j] + 1: anchor_indices[j + 1]]
        else:
            content_lines = lines[anchor_indices[j] + 1:]
        
        # Reconstruct content by joining lines with newlines
        content = "\n".join(content_lines)
        
        # Check if content is empty (violates rule 3)
        if not content:
            # All content must not be empty
            print("All content must not be empty")
            return None
        
        # Check if content contains image tags
        if re.search(r'<8442d621>.*?</8442d621>', content):
            # Split content into parts based on image tags
            parts = re.split(r'(<8442d621>.*?</8442d621>)', content)
            content_list = []
            # Process each part
            for part in parts:
                if re.match(r'<8442d621>.*?</8442d621>', part):
                    # Extract base64 string from image tag
                    base64_str = re.match(r'<8442d621>(.*?)</8442d621>',
                                          part).group(1)
                    content_list.append({
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": base64_str
                        }
                    })
                else:
                    # Debug: re.split introduces empty strings
                    # Workaround: ignore them
                    if part != "":
                        # Add text part, including empty strings
                        content_list.append({
                            "type": "text",
                            "text": part
                        })
            messages.append({"role": role, "content": content_list})
        else:
            # Text-only content remains a string
            messages.append({"role": role, "content": content})
    
    # Validate alternating roles and ending with "user"
    if len(messages) > 1:
        for i in range(len(messages) - 1):
            if messages[i]["role"] == messages[i + 1]["role"]:
                # Roles must alternate between 'user' and 'assistant'
                print("Roles must alternate between 'user' and 'assistant'")
                return None
    if messages and messages[-1]["role"] != "user":
        # Messages must end with 'user' role
        print("Messages must end with 'user' role")
        return None
    
    return messages