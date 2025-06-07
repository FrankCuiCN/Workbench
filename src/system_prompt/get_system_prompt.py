import os
import logging

logger = logging.getLogger(__name__)

system_prompt_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "./system_prompt/system_prompt.txt")
with open(system_prompt_path, mode="r", encoding="utf-8") as f:
    system_prompt = f.read().strip()
    
logger.info(f"Loaded system prompt from {system_prompt_path}")

def get_system_prompt():
    return system_prompt
