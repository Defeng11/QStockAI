# -*- coding: utf-8 -*- 

"""
Defines the LangGraph multi-agent workflow for stock analysis.
This is the "brain" of the AI agent.
"""

import pandas as pd
from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

# Import our custom modules with relative paths
from data_handler import get_stock_daily
from analysis_handler import add_technical_indicators
from llm_switcher import init_llm

# --- 1. Define the State ---

class AgentState(TypedDict):
    """Defines the state that is passed between nodes in the graph."""
    stock_code: str
    indicators: List[str]
    raw_data: pd.DataFrame
    analyzed_data: pd.DataFrame
    technical_summary: str
    final_decision: str
    error: str

# --- 2. Define the Nodes ---

def get_data_node(state: AgentState) -> AgentState:
    """Node to fetch raw stock data."""
    print("--- Node: 获取数据 ---")
    try:
        code = state.get("stock_code")
        print(f"股票代码: {code}")
        df = get_stock_daily(code)
        if df.empty:
            return { "error": f"未能获取股票 {code} 的数据。" }
        return { "raw_data": df }
    except Exception as e:
        return { "error": f"获取数据时出错: {e}" }

def analyze_data_node(state: AgentState) -> AgentState:
    """Node to perform technical analysis and get a summary from the LLM."""
    print("--- Node: 技术分析 ---")
    try:
        df = state.get("raw_data")
        indicators = state.get("indicators", ['rsi', 'macd']) # Default indicators
        
        # Add technical indicators to the dataframe
        df_analyzed = add_technical_indicators(df, indicators)
        
        # Ask the LLM for a technical summary
        llm = init_llm()
        if not llm:
            return { "error": "无法初始化LLM以进行技术分析。" }

        # Prepare a prompt for the LLM
        # We only show the last 30 days of data to keep the prompt concise
        prompt = f"""
        你是一位资深的股票技术分析师。请根据以下最近30天的股票数据（包含RSI和MACD指标），
        分析当前的技术形态、趋势、关键支撑位和阻力位，并给出一个简短的技术面总结。
        请不要给出任何买卖建议，只做客观的技术分析。

        数据：
        {df_analyzed.tail(30).to_markdown()}
        """
        
        print("正在请求LLM进行技术面总结...")
        response = llm.invoke(prompt)
        summary = response.content
        print(f"LLM技术面总结: {summary}")
        
        return { "analyzed_data": df_analyzed, "technical_summary": summary }
    except Exception as e:
        return { "error": f"技术分析时出错: {e}" }


def decision_node(state: AgentState) -> AgentState:
    """Node to make the final decision based on all gathered information."""
    print("--- Node: 最终决策 ---")
    try:
        summary = state.get("technical_summary")
        code = state.get("stock_code")
        
        llm = init_llm()
        if not llm:
            return { "error": "无法初始化LLM以进行最终决策。" }

        prompt = f"""
        你是一位顶级的投资总监，以逻辑严谨、分析全面著称。
        你的任务是基于下属分析师提交的技术面总结，结合你对市场的宏观理解，
        为股票 {code} 生成一份最终的投资分析报告。

        报告必须包含以下部分：
        1.  **核心观点**: 清晰地给出“看涨”、“看跌”或“中性”的核心判断。
        2.  **逻辑依据**: 详细阐述你做出判断的理由。结合技术面总结，并可以引入你自己的市场洞察（例如，当前市场情绪、板块轮动等宏观因素）。
        3.  **风险提示**: 指出当前策略可能面临的主要风险。

        下属提交的技术面总结如下：
        --- Technical Summary ---
        {summary}
        --- End of Summary ---
        
        请生成你的最终投资分析报告。
        """
        
        print("正在请求LLM进行最终决策...")
        response = llm.invoke(prompt)
        decision = response.content
        print(f"LLM最终决策报告: {decision}")
        
        return { "final_decision": decision }
    except Exception as e:
        return { "error": f"最终决策时出错: {e}" }


def handle_error_node(state: AgentState) -> AgentState:
    """Node to handle and print errors."""
    print("--- Node: 错误处理 ---")
    err = state.get("error")
    print(f"工作流发生错误: {err}")
    return {}

# --- 3. Assemble the Graph ---

# Define conditional logic for branching
def should_continue(state: AgentState) -> str:
    """Determines whether to continue or to handle an error."""
    if state.get("error"):
        return "handle_error"
    return "continue"

# Create the graph builder
workflow = StateGraph(AgentState)

# Add nodes
workflow.add_node("get_data", get_data_node)
workflow.add_node("analyze_data", analyze_data_node)
workflow.add_node("make_decision", decision_node)
workflow.add_node("handle_error", handle_error_node)

# Define the edges and conditional branching
workflow.set_entry_point("get_data")
workflow.add_conditional_edges(
    "get_data",
    should_continue,
    { "continue": "analyze_data", "handle_error": "handle_error" }
)
workflow.add_conditional_edges(
    "analyze_data",
    should_continue,
    { "continue": "make_decision", "handle_error": "handle_error" }
)
workflow.add_conditional_edges(
    "make_decision",
    should_continue,
    { "continue": END, "handle_error": "handle_error" }
)
workflow.add_edge("handle_error", END)

# Compile the graph
app = workflow.compile()

# --- Test Block ---
if __name__ == '__main__':
    print("--- 开始测试核心工作流 ---")
    
    # Ensure you have a .env file with your DASHSCOPE_API_KEY
    
    initial_state = {
        "stock_code": "000001", # 平安银行
        "indicators": ['rsi', 'macd']
    }
    
    print(f"输入: {initial_state}")
    
    # Stream the output of the graph as it runs
    for event in app.stream(initial_state):
        for key, value in event.items():
            print(f"--- Event: {key} ---")
            # print(f"{value}") # Uncomment for very verbose output
    
    # Alternatively, get the final state
    # final_state = app.invoke(initial_state)
    # print("\n--- 工作流执行完毕，最终状态: ---")
    # print(final_state)

    print("\n--- 工作流测试结束 ---")
