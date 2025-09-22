# QStockAI

> "The universe is not only stranger than we imagine, it is stranger than we can imagine." - Werner Heisenberg

QStockAI is not merely a stock analysis tool; it is a digital oracle for the financial cosmos. It listens to the market's subtle whispers and complex data streams, seeking to decipher the signal from the noise. By harnessing the analytical power of quantitative models and the inferential capabilities of advanced AI agents, this project attempts to illuminate potential future trajectories hidden within the chaos of stock fluctuations.

This is an exploration into the art of financial divination, powered by code.

---

## 核心功能 (Core Features)

*   **多源数据接入 (Multi-Source Data)**: 优先从本地通达信读取数据，失败则自动回退至 `AkShare`，确保数据获取的稳定与高效。
*   **全市场股票池 (Comprehensive Stock Universe)**: 动态获取并缓存完整的A股市场股票及其所属行业，支持按行业板块进行筛选。
*   **自动化技术指标 (Automated Technical Indicators)**: 自动为股票数据计算多种关键技术指标 (MA, MACD, RSI)，为策略分析提供弹药。
*   **多线程加速 (Multi-threaded Acceleration)**: 在批量获取数据时采用并发处理，显著缩短等待时间，提升操作效率。
*   **AI Agent 策略分析 (AI Agent Strategy Analysis)**: 基于 `LangGraph` 构建核心分析引擎，模拟专家行为，对股票进行深度分析和信号研判。
*   **交互式Web界面 (Interactive Web UI)**: 通过 `Streamlit` 构建了多页面Web应用，提供“诊股”与“选股”两大核心功能模块，操作直观。

## 项目结构 (Project Structure)

```
.
├── app.py                      # Streamlit 主程序入口
├── start.bat                   # Windows 启动脚本
├── requirements.txt            # 项目依赖
├── config.env.example          # 环境变量示例文件
├── README.md                   # 您正在阅读的文件
├── cache/                      # 存放缓存数据 (如股票池)
│   └── stock_universe_cache.json
├── pages/                      # Streamlit 页面模块
│   ├── 1_诊股.py
│   └── 2_选股.py
├── src/                        # 核心源代码
│   ├── __init__.py
│   ├── analysis_handler.py     # 技术指标计算
│   ├── config.py               # 配置加载
│   ├── data_handler.py         # 数据获取 (股票池, 历史数据)
│   ├── graph_workflow.py       # “诊股”功能的AI工作流
│   ├── llm_switcher.py         # LLM模型切换
│   ├── screening_handler.py    # “选股”功能的批量处理
│   ├── screening_workflow.py   # “选股”功能的AI工作流
│   └── strategy_handler.py     # 交易策略实现
└── tests/                      # 测试脚本
    ├── test_analysis_handler.py
    ├── test_data_handler.py
    └── test_strategy_handler.py
```

## 如何运行 (Getting Started)

1.  **安装依赖**:
    ```shell
    pip install -r requirements.txt
    ```
2.  **配置API Key**:
    *   复制 `config.env.example` 并重命名为 `.env`。
    *   在 `.env` 文件中填入您自己的LLM API Key。
3.  **启动程序**:
    *   直接运行 `start.bat` 脚本。
    *   或在终端中执行 `streamlit run app.py`。

## 免责声明 (Disclaimer)

本项目及所有内容仅供学习、研究和技术交流，不构成任何投资建议。所有数据和分析结果仅供参考，不应作为任何投资决策的依据。股市有风险，投资需谨慎。
