# -*- coding: utf-8 -*-

"""
Defines the LangGraph workflow for stock screening.
"""

import pandas as pd
from typing import TypedDict, List, Dict
from langgraph.graph import StateGraph, END

# Import functions from screening_handler
from src.screening_handler import (
    get_stock_universe,
    batch_get_stock_daily,
    batch_apply_strategy,
    filter_signals
)

# --- 1. Define the State ---

class ScreeningState(TypedDict):
    """Defines the state that is passed between nodes in the screening graph."""
    stock_universe: List[Dict] # Now stores list of dicts with code, name, industry
    stock_codes: List[str] # List of just codes for batch fetching
    stock_names_map: Dict[str, str] # Map from code to name
    stock_industry_map: Dict[str, str] # Map from code to industry
    start_date: str
    end_date: str
    all_stock_data: Dict[str, pd.DataFrame] # Raw data for all stocks
    processed_stock_data: Dict[str, pd.DataFrame] # Data after strategy applied
    signal_type: str # 'buy' or 'sell'
    recent_days: int # Look back for signals
    found_signals: List[Dict] # List of dictionaries with found signals
    error: str

# --- 2. Define the Nodes ---

def get_universe_node(state: ScreeningState) -> ScreeningState:
    """Node to fetch the stock universe (code, name, industry) and create mappings."""
    print("-- 选股工作流: 1. 获取股票池 --")
    try:
        universe_data = get_stock_universe() # This now returns List[Dict]
        if not universe_data:
            return { "error": "未能获取股票池。" }
        
        stock_codes = [item['代码'] for item in universe_data]
        stock_names_map = {item['代码']: item['名称'] for item in universe_data}
        stock_industry_map = {item['代码']: item.get('所属行业', '未知') for item in universe_data} # Use .get for safety
        
        return { 
            "stock_universe": universe_data, # Store the full data
            "stock_codes": stock_codes, # Store just codes for batch fetching
            "stock_names_map": stock_names_map,
            "stock_industry_map": stock_industry_map
        }
    except Exception as e:
        return { "error": f"获取股票池时出错: {e}" }

def batch_get_data_node(state: ScreeningState) -> ScreeningState:
    """Node to batch fetch daily data for the stock universe."""
    print("-- 选股工作流: 2. 批量获取数据 --")
    try:
        stock_codes = state.get("stock_codes") # Use stock_codes now
        start_date = state.get("start_date")
        end_date = state.get("end_date")
        all_data = batch_get_stock_daily(stock_codes, start_date, end_date)
        if not all_data:
            return { "error": "未能批量获取股票数据。" }
        return { "all_stock_data": all_data }
    except Exception as e:
        return { "error": f"批量获取数据时出错: {e}" }

def batch_apply_strategy_node(state: ScreeningState) -> ScreeningState:
    """Node to batch apply the strategy to all stock data."""
    print("-- 选股工作流: 3. 批量应用策略 --")
    try:
        all_stock_data = state.get("all_stock_data")
        processed_data = batch_apply_strategy(all_stock_data)
        if not processed_data:
            return { "error": "未能批量应用策略。" }
        return { "processed_stock_data": processed_data }
    except Exception as e:
        return { "error": f"批量应用策略时出错: {e}" }

def filter_results_node(state: ScreeningState) -> ScreeningState:
    """Node to filter stocks based on signals."""
    print("-- 选股工作流: 4. 筛选结果 --")
    try:
        processed_stock_data = state.get("processed_stock_data")
        signal_type = state.get("signal_type", 'buy')
        recent_days = state.get("recent_days", 5)
        found_signals = filter_signals(processed_stock_data, signal_type, recent_days)
        return { "found_signals": found_signals }
    except Exception as e:
        return { "error": f"筛选结果时出错: {e}" }

def handle_error_node(state: ScreeningState) -> ScreeningState:
    """Node to handle and print errors for the screening workflow."""
    print("-- 选股工作流: 错误处理 --")
    err = state.get("error")
    print(f"选股工作流发生错误: {err}")
    return {}

# --- 3. Assemble the Graph ---

def should_continue_screening(state: ScreeningState) -> str:
    """Determines whether to continue or to handle an error in screening workflow."""
    if state.get("error"):
        return "handle_error"
    return "continue"

# Create the graph builder
screening_workflow_builder = StateGraph(ScreeningState)

# Add nodes
screening_workflow_builder.add_node("get_universe", get_universe_node)
screening_workflow_builder.add_node("batch_get_data", batch_get_data_node)
screening_workflow_builder.add_node("batch_apply_strategy", batch_apply_strategy_node)
screening_workflow_builder.add_node("filter_results", filter_results_node)
screening_workflow_builder.add_node("handle_error", handle_error_node)

# Define the edges and conditional branching
screening_workflow_builder.set_entry_point("get_universe")
screening_workflow_builder.add_conditional_edges(
    "get_universe",
    should_continue_screening,
    { "continue": "batch_get_data", "handle_error": "handle_error" }
)
screening_workflow_builder.add_conditional_edges(
    "batch_get_data",
    should_continue_screening,
    { "continue": "batch_apply_strategy", "handle_error": "handle_error" }
)
screening_workflow_builder.add_conditional_edges(
    "batch_apply_strategy",
    should_continue_screening,
    { "continue": "filter_results", "handle_error": "handle_error" }
)
screening_workflow_builder.add_conditional_edges(
    "filter_results",
    should_continue_screening,
    { "continue": END, "handle_error": "handle_error" }
)
screening_workflow_builder.add_edge("handle_error", END)

# Compile the graph
screening_app = screening_workflow_builder.compile()

# --- Test Block ---
if __name__ == '__main__':
    print("--- 测试 screening_workflow 模块 ---")
    test_initial_state = {
        "start_date": "20240101",
        "end_date": "20240919",
        "signal_type": "buy",
        "recent_days": 10
    }

    print(f"输入: {test_initial_state}")

    final_screening_state = {}
    try:
        for event in screening_app.stream(test_initial_state):
            for key, value in event.items():
                final_screening_state.update(value)
                print(f"--- Event: {key} ---")
                # print(value) # Uncomment for verbose output

        print("\n-- 选股工作流测试结束，最终状态: --")
        print(final_screening_state.get("found_signals", "未找到信号"))
        if final_screening_state.get("error"):
            print(f"错误: {final_screening_state.get('error')}")

    except Exception as e:
        print(f"执行选股工作流时发生严重错误: {e}")

    print("\n--- screening_workflow 模块测试结束 ---")
