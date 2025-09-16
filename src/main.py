# -*- coding: utf-8 -*-

"""
Main entry point for the Streamlit application.
Provides the user interface for the LiangZiXuanGu AI Agent.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from langgraph.graph import END

# Import the compiled graph app from our workflow module
from graph_workflow import app

def create_candlestick_chart(df: pd.DataFrame):
    """Creates an interactive Candlestick chart with MAs and MACD using Plotly."""
    
    # Calculate Moving Averages
    df['ma10'] = df['close'].rolling(window=10).mean()
    df['ma20'] = df['close'].rolling(window=20).mean()

    # Create figure with secondary y-axis
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.03, subplot_titles=('K线与移动平均线', 'MACD'), 
                        row_width=[0.2, 0.7])

    # Plot Candlestick chart
    fig.add_trace(go.Candlestick(x=df['date'],
                    open=df['open'], high=df['high'],
                    low=df['low'], close=df['close'],
                    name="K线"), 
                  row=1, col=1)

    # Plot Moving Averages
    fig.add_trace(go.Scatter(x=df['date'], y=df['ma10'], mode='lines', name='MA10', line=dict(color='orange', width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['date'], y=df['ma20'], mode='lines', name='MA20', line=dict(color='purple', width=1)), row=1, col=1)

    # Plot MACD
    colors = ['green' if val >= 0 else 'red' for val in df['macdhist']]
    fig.add_trace(go.Bar(x=df['date'], y=df['macdhist'], name='MACD Hist', marker_color=colors), row=2, col=1)
    fig.add_trace(go.Scatter(x=df['date'], y=df['macd'], mode='lines', name='MACD'), row=2, col=1)
    fig.add_trace(go.Scatter(x=df['date'], y=df['macdsignal'], mode='lines', name='Signal'), row=2, col=1)

    # Update layout
    fig.update_layout(
        title='股价走势与技术指标',
        xaxis_title="日期",
        yaxis_title="价格",
        xaxis_rangeslider_visible=False, # Hide the range slider
        height=600,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    fig.update_yaxes(title_text="MACD", row=2, col=1)

    return fig

def main():
    st.set_page_config(page_title="LiangZiXuanGu - 量子选股", layout="wide")

    # --- Header ---
    st.title("量子选股 (LiangZiXuanGu) AI Agent")
    st.markdown("一个基于LangGraph多代理工作流的A股智能分析投研工具。")

    # --- Sidebar for Inputs ---
    with st.sidebar:
        st.header("分析设置")
        
        stock_code = st.text_input("请输入股票代码", value="000001", help="例如：平安银行输入 000001")
        
        available_indicators = ['rsi', 'macd']
        selected_indicators = st.multiselect(
            "选择技术指标",
            options=available_indicators,
            default=available_indicators
        )

        start_button = st.button("开始分析", type="primary", use_container_width=True)
        
        st.markdown("---")
        st.header("免责声明")
        st.warning(
            "本项目及所有内容仅供学习研究，不构成任何投资建议。"
            "股市有风险，投资需谨慎。"
        )

    # --- Main Content Area ---
    if start_button:
        if not stock_code:
            st.error("请输入有效的股票代码。")
            return

        initial_state = {"stock_code": stock_code, "indicators": selected_indicators}
        
        st.info(f"正在为您分析股票: {stock_code}，请稍候...", icon="🤖")

        with st.status("AI Agent 正在工作中...", expanded=True) as status:
            final_state = None
            for event in app.stream(initial_state):
                for key, value in event.items():
                    if key == "get_data":
                        status.update(label="步骤 1/3: 获取行情数据...", state="running")
                    elif key == "analyze_data":
                        status.update(label="步骤 2/3: 计算指标并进行AI技术面分析...", state="running")
                    elif key == "make_decision":
                        status.update(label="步骤 3/3: AI生成最终投研报告...", state="running")
                if END in event:
                    final_state = event[END]
            status.update(label="分析完成！", state="complete", expanded=False)

        # --- Display Results ---
        if final_state and not final_state.get("error"):
            st.subheader("📈 最终投研报告")
            final_decision_text = final_state.get("final_decision", "未能生成报告。")
            st.markdown(final_decision_text)
            
            st.download_button(
                label="📥 下载投研报告 (.md)",
                data=final_decision_text,
                file_name=f'{stock_code}_analysis_report.md',
                mime='text/markdown',
            )
            
            st.markdown("---")
            st.subheader("📊 交互式K线图")
            df = final_state.get("analyzed_data")
            if isinstance(df, pd.DataFrame) and not df.empty:
                fig = create_candlestick_chart(df)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("无法生成图表，数据为空。")

            with st.expander("查看AI技术面分析摘要"):
                st.markdown(final_state.get("technical_summary", "未能生成技术面摘要。"))

            with st.expander("查看详细数据与指标"):
                if isinstance(df, pd.DataFrame):
                    st.dataframe(df)
                else:
                    st.warning("无法显示详细数据。")
        else:
            error_message = final_state.get("error", "发生未知错误。")
            st.error(f"分析过程中出现错误: {error_message}")

    else:
        st.info("请在左侧输入股票代码，然后点击“开始分析”按钮。")

if __name__ == "__main__":
    main()
