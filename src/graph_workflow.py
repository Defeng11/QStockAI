# -*- coding: utf-8 -*-

"""
Defines the LangGraph multi-agent workflow for stock analysis.
This is the "brain" of the AI agent.
"""

import pandas as pd
from typing import TypedDict, List
from langgraph.graph import StateGraph, END

# Import our custom modules
from .data_handler import get_stock_daily
from .analysis_handler import add_technical_indicators, get_available_indicators
from .strategy_handler import apply_oversold_reversal_strategy # New import
from .llm_switcher import init_llm

# --- 1. Define the State ---

class AgentState(TypedDict):
    """Defines the state that is passed between nodes in the graph."""
    stock_code: str
    indicators: List[str]
    start_date: str
    end_date: str
    raw_data: pd.DataFrame
    analyzed_data: pd.DataFrame # This will now include signals
    technical_summary: str
    final_decision: str
    error: str

# --- 2. Define the Nodes ---

def get_data_node(state: AgentState) -> AgentState:
    """Node to fetch raw stock data."""
    print("-- Node: 1. 获取数据 --")
    try:
        code = state.get("stock_code")
        start_date = state.get("start_date")
        end_date = state.get("end_date")
        print(f"股票代码: {code}, 时间范围: {start_date} - {end_date}")
        df = get_stock_daily(stock_code=code, start_date=start_date, end_date=end_date)
        if df.empty:
            return { "error": f"未能获取股票 {code} 的数据。" }
        return { "raw_data": df }
    except Exception as e:
        return { "error": f"获取数据时出错: {e}" }

def analyze_indicators_node(state: AgentState) -> AgentState:
    """Node to calculate technical indicators."""
    print("-- Node: 2. 计算指标 --")
    try:
        df = state.get("raw_data")
        indicators = state.get("indicators")
        df_analyzed = add_technical_indicators(df, indicators)
        return { "analyzed_data": df_analyzed }
    except Exception as e:
        return { "error": f"计算技术指标时出错: {e}" }


def apply_strategy_node(state: AgentState) -> AgentState:
    """Node to apply a trading strategy and generate signals."""
    print("-- Node: 3. 应用策略 --")
    try:
        df_analyzed = state.get("analyzed_data")
        # Currently, we only have one strategy. This can be made dynamic in the future.
        df_with_signals = apply_oversold_reversal_strategy(df_analyzed)
        return { "analyzed_data": df_with_signals } # Overwrite analyzed_data with the one including signals
    except Exception as e:
        return { "error": f"应用策略时出错: {e}" }


def generate_report_node(state: AgentState) -> AgentState:
    """Node to generate the final analysis report using an LLM."""
    print("-- Node: 4. 生成报告 --")
    try:
        code = state.get("stock_code")
        df_final = state.get("analyzed_data")
        
        # Find the data points where a buy signal was triggered
        buy_signals = df_final[df_final['signal'] == 1]
        
        llm = init_llm()
        if not llm:
            return { "error": "无法初始化LLM以生成报告。" }

        # Create a dynamic prompt based on whether signals were found
        if not buy_signals.empty:
            signal_summary = "\n\n量化策略信号总结：\n在以下日期触发了‘超卖反弹’买入信号：\n"
            for index, row in buy_signals.iterrows():
                signal_summary += f"- {row['date'].strftime('%Y-%m-%d')}\n"
            signal_summary += "\n请结合这些明确的量化信号进行分析。"
        else:
            signal_summary = "\n\n量化策略信号总结：\n在分析的时间范围内，未触发任何‘超卖反弹’买入信号。请基于整体技术形态进行判断。"

        prompt = f"""
        你是一位顶级的投资总监，以逻辑严谨、分析全面著称。
        你的任务是为股票 {code} 生成一份最终的投资分析报告。
        {signal_summary}

        报告必须包含以下部分：
        1.  **核心观点**: 根据信号和你的分析，清晰地给出“看涨”、“看跌”或“中性”的核心判断。
        2.  **逻辑依据**: 详细阐述你做出判断的理由。必须结合上面提供的量化信号（如果有），并可以引入你自己的市场洞察（例如，当前市场情绪、板块轮动等宏观因素）。
        3.  **风险提示**: 指出当前策略可能面临的主要风险。
        
        请生成你的最终投资分析报告。
        """
        
        print("正在请求LLM生成最终报告...")
        response = llm.invoke(prompt)
        decision = response.content
        print(f"LLM最终报告: {decision}")
        
        # For simplicity, we are not generating a separate technical_summary anymore.
        # The final report is the main AI output.
        return { "final_decision": decision }
    except Exception as e:
        return { "error": f"生成报告时出错: {e}" }


def handle_error_node(state: AgentState) -> AgentState:
    """Node to handle and print errors."""
    print("-- Node: 错误处理 --")
    err = state.get("error")
    print(f"工作流发生错误: {err}")
    return {}

# --- 3. Assemble the Graph ---

def should_continue(state: AgentState) -> str:
    """Determines whether to continue or to handle an error."""
    if state.get("error"):
        return "handle_error"
    return "continue"

workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("get_data", get_data_node)
workflow.add_node("analyze_indicators", analyze_indicators_node)
workflow.add_node("apply_strategy", apply_strategy_node) # New node
workflow.add_node("generate_report", generate_report_node) # Renamed node
workflow.add_node("handle_error", handle_error_node)

# Define the edges and conditional branching
workflow.set_entry_point("get_data")
workflow.add_conditional_edges(
    "get_data",
    should_continue,
    { "continue": "analyze_indicators", "handle_error": "handle_error" }
)
workflow.add_conditional_edges(
    "analyze_indicators",
    should_continue,
    { "continue": "apply_strategy", "handle_error": "handle_error" } # Edge to new node
)
workflow.add_conditional_edges(
    "apply_strategy",
    should_continue,
    { "continue": "generate_report", "handle_error": "handle_error" } # Edge to new node
)
workflow.add_conditional_edges(
    "generate_report",
    should_continue,
    { "continue": END, "handle_error": "handle_error" }
)
workflow.add_edge("handle_error", END)

# Compile the graph
app = workflow.compile()

# --- Test Block ---
if __name__ == '__main__':
    print("-- 开始测试核心工作流 --")
    
    initial_state = {
        "stock_code": "000001",
        "indicators": get_available_indicators(), # Test with all indicators
        "start_date": "20230101",
        "end_date": "20240918"
    }
    
    print(f"输入: {initial_state}")
    
    for event in app.stream(initial_state):
        for key, value in event.items():
            print(f"--- Event: {key} ---")
            # print(value) # Uncomment for verbose output

    print("\n-- 工作流测试结束 --")
