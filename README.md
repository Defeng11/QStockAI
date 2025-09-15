# LiangZiXuanGu (量子选股)

An AI stock selection agent based on LangGraph and multi-agent LLM reasoning.

## Features

- Fetches A-share data from AkShare/Baostock.
- Calculates technical/extended indicators (RSI, MACD, Chip Distribution, etc.).
- Uses a multi-agent LLM workflow (default: Qwen-Max) to generate trading signals.
- Supports dynamic switching of LLM models (OpenAI, Gemini, Qwen, DeepSeek).
- Interactive UI via Streamlit.

## Project Structure

```
.
├── src/                # Core source code
│   ├── main.py             # Streamlit UI entry point
│   ├── data_handler.py     # Data fetching and processing
│   ├── llm_switcher.py     # LLM model switching logic
│   ├── graph_workflow.py   # LangGraph agent workflow
│   └── config.py           # Configuration
├── tests/              # Pytest tests
├── logs/               # Log files
├── .gitignore          # Git ignore file
├── requirements.txt    # Python dependencies
└── README.md           # This file
```
