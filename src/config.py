# -*- coding: utf-8 -*-

"""
Configuration file for the QStockAI project.
Loads environment variables from a .env file.
"""

import os
from dotenv import load_dotenv

# Load environment variables from a .env file if it exists
load_dotenv()

# --- API Keys ---

# MiniMax API Key (推荐 - 支持 OpenAI 兼容接口)
MINIMAX_API_KEY = os.getenv("MINIMAX_API_KEY", "")

# Qwen (通义千问) API Key
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")

# OpenAI API Key (可选)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Google Gemini API Key (可选)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# --- Model Configuration ---

# 默认 LLM 模型
DEFAULT_MODEL = os.getenv("DEFAULT_MODEL", "minimax")

# MiniMax 模型 (使用 OpenAI 兼容接口)
MINIMAX_MODEL = os.getenv("MINIMAX_MODEL", "abab6.5s-chat")

# Qwen 模型
QWEN_MODEL = os.getenv("QWEN_MODEL", "qwen-max")

# --- API Base URLs (用于 OpenAI 兼容接口) ---

# MiniMax API 端点
MINIMAX_API_BASE = os.getenv("MINIMAX_API_BASE", "https://api.minimax.chat/v1")

# Qwen (DashScope) API 端点
DASHSCOPE_API_BASE = os.getenv("DASHSCOPE_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")

# --- 其他配置 ---

# 默认时区
TIMEZONE = "Asia/Shanghai"
