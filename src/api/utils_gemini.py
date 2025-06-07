import os
import logging
from google import genai
from google.genai.types import Tool, GenerateContentConfig, GoogleSearch, ThinkingConfig
from system_prompt.get_system_prompt import get_system_prompt

logger = logging.getLogger(__name__)
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
