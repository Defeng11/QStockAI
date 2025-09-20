# -*- coding: utf-8 -*-

"""
Defines the LangGraph multi-agent workflow for stock analysis.
This is the "brain" of the AI agent.
"""

import pandas as pd
from typing import TypedDict, List
from langgraph.graph import StateGraph, END

# Import our custom modules
from src.data_handler import get_stock_daily
from src.analysis_handler import add_technical_indicators, get_available_indicators
from src.strategy_handler import apply_five_step_integrated_strategy
from src.llm_switcher import init_llm

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
    strategy_summary: str # Added for displaying strategy signals in expander
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
        # Use the new integrated strategy
        df_with_signals = apply_five_step_integrated_strategy(df_analyzed)
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
你是一位顶级的投资总监，以逻辑严谨、分析全面、数据驱动著称。你拥有超过15年的市场经验，擅长结合量化指标、宏观环境、行业趋势和公司基本面进行深度分析，能够排除主观偏见，提供客观、可操作的投资建议。

你的任务是为股票 {code} 生成一份专业的  最终投资分析报告  。报告必须严格基于你所提供的量化信号 {signal_summary}，并结合最新的、可公开获取的市场数据（例如：最新股价、PE、PB、PEG、ROE、市值、成交量、MACD、RSI等）。如果提供的信号中缺少关键数据，你必须准确地指出缺失的具体数据项，并说明其对分析结论的影响。

报告必须严格遵循以下结构和要求，确保每一部分内容都简洁、专业，并用数据和严密的逻辑来支持你的观点：

  一、报告摘要（核心判断与关键理由）  
    字数限制  ：100-200字。
    内容  ：以最精炼的语言概括股票 {code} 的当前状况。明确给出你的  核心判断  （“看涨”、“看跌”或“中性”），并总结支持这一判断的  2-3个关键理由  。该部分应提供快速阅读价值。

  二、市场与行业背景分析  
    内容  ：分析股票所属行业的当前趋势、周期位置，以及宏观经济因素（如宏观经济周期、货币政策、财政政策）和行业政策的影响。
    数据要求  ：必须引用相关指数（如  上证指数、深证成指或所属行业指数  ）的近期走势（例如近3个月涨跌幅），并分析板块资金流向、市场情绪等，以提供一个全面的宏观背景。

  三、量化信号深度解读  
    内容  ：对提供的量化信号 {signal_summary} 进行逐一、详细的解读。将信号分为  技术指标、估值指标和交易信号  三类进行分析。
    数据要求  ：
        技术指标（例如：MACD、RSI、KDJ、成交量、均线）  ：解释每个指标的当前状态和含义。例如，MACD金叉，RSI是否超买超卖，成交量是放量还是缩量。
        估值指标（例如：PE、PB、PEG、ROE、股息率）  ：不仅列出数值，更要进行  横向（与行业平均值对比）  和  纵向（与公司历史估值区间对比）  比较，从而评估其估值水平（例如，“当前PE为25，低于行业平均的35，且处于公司近五年历史PE分位数的20%，显示其估值相对低估”）。
        买卖信号  ：基于量化模型，明确指出当前是否存在买入或卖出信号，并评估其强度。

  四、核心观点与量化支持  
    内容  ：基于上述所有分析，再次清晰、果断地给出你的  最终判断  （“看涨”、“看跌”或“中性”）。
    量化支持  ：如果看涨，请  量化其潜在上涨空间  ，并给出  目标价位区间  （例如，目标价为10%-20%的上涨空间，即15元至16.5元）。如果看跌，请  量化其下行风险  并给出  止损价位  。该部分必须由数据和分析结论支撑。

  五、逻辑依据（专业洞察与数据佐证）  
    内容  ：详细阐述你的判断理由。该部分是报告的核心，必须将量化信号与  专业洞察  （如公司基本面、核心竞争力、管理层、潜在利好/利空事件）相结合。
    数据佐证  ：必须  用数据举例说明  。例如，“公司毛利率从上季度的25%提升至本季度的30%，显示其盈利能力正在改善”；或“PEG < 1 表示其成长性被市场低估”。确保每一个论点都有数据支撑。

  六、风险提示与控制策略  
    内容  ：系统性地列出  主要风险  ，包括但不限于市场系统性风险、行业政策变化、公司业绩不及预期、重大资金流出（如大股东减持）、突发风险事件等。
    量化风险  ：必须给出  量化止损位  （例如，建议止损位为买入价的5%）和  风险控制策略  （如  仓位管理  、  分批买入/卖出  ）。

  七、投资建议与操作指南  
    内容  ：给出清晰、可执行的投资建议（买入价格、卖出价格或持有）。
    具体操作  ：建议  仓位控制  （例如，建议总资金的2-5%），  时间框架  （例如，短线1-3周，中线1-3个月），并列出  核心监控指标  （例如，若RSI>75，MACD出现死叉，则考虑减仓）。

  报告风格与格式  ：
    语言  ：用中文撰写。
    文风  ：逻辑严谨、数据导向，避免使用“绝对化”语言，应使用“可能”、“基于当前数据来看”、“预计”等词汇。
    字数  ：控制在800-1200字。
    格式  ：使用Markdown格式，合理使用  粗体  、列表、表格，以增强可读性。数据引用时，使用表格或列表呈现数据。引用数据来源（如Akshare、东方财富），确保客观。
    客观性  ：确保报告内容客观公正，不带有任何情绪或主观偏好。
        """
        
        print("正在请求LLM生成最终报告...")
        response = llm.invoke(prompt)
        decision = response.content
        print(f"LLM最终报告: {decision}")
        
        # For simplicity, we are not generating a separate technical_summary anymore.
        # The final report is the main AI output.
        return { "final_decision": decision, "strategy_summary": signal_summary }
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
