# -*- coding: utf-8 -*-

"""
Configuration file for the LiangZiXuanGu project.
Loads environment variables.
"""

import os
from dotenv import load_dotenv

# Load environment variables from a .env file if it exists
load_dotenv()

# --- API Keys ---
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# You can add other configurations here, for example:
# DEFAULT_MODEL = "qwen-max"