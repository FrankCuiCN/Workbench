# Workbench
A text editor that talks to language and reasoning models.

## System Requirements
```
Tested on:
- Windows 11
- Python 3.12.9
```

## Installing Dependencies:
Step 1: Set the following environment variables with valid API keys:
```
- ANTHROPIC_API_KEY  (Anthropic)
- OPENAI_API_KEY     (OpenAI)
- GEMINI_API_KEY     (Google Gemini)
```

Step 2: Run the following command:
```
pip install PySide6==6.9.1 pywin32==311 openai==1.97.0 anthropic==0.58.2 google-genai==1.26.0
```

## Disclaimer
- Please note that our tool functions solely as a user interface for accessing third-party AI API services. While we do our best to provide a reliable experience, we are not responsible or liable for users' actions, decisions, or consequences resulting from interactions with these APIs.
- We highly recommend users define their own "system_prompt.txt" file to clearly steer the AI's behavior according to their specific needs. The system prompt we provide should serve merely as a helpful reference example.
- Users remain solely responsible for content generated and for any resulting consequences.
- By using our tool, you agree to act responsibly and adhere to all applicable guidelines and policies.

## License Information
This project is licensed under the MIT License (see LICENSE for details).
It includes the third-party dependency [PySide6 (Qt for Python)](https://github.com/pyside/pyside-setup), licensed under LGPLv3. PySide6's source code is available [here](https://github.com/pyside/pyside-setup), and Qt's official source code repository can be found [here](https://code.qt.io/). The full LGPLv3 license text can be accessed [here](https://www.gnu.org/licenses/lgpl-3.0.html).
