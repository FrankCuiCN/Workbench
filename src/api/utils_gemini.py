import os
from google import genai
from google.genai.types import GenerateContentConfig, ThinkingConfig
from google.genai.types import Tool, GoogleSearch

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Translate the stream object into standard stream
#   Using the yield pattern
