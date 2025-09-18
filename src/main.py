# -*- coding: utf-8 -*-

"""
Main entry point for the Streamlit application.
Provides the user interface for the LiangZiXuanGu AI Agent.
"""

import streamlit as st
from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from langgraph.graph import END

# Import the compiled graph app from our workflow module
from .graph_workflow import app
from .analysis_handler import get_available_indicators

def create_candlestick_chart(df: pd.DataFrame):
    """Creates an interactive Candlestick chart with MAs and MACD using Plotly."""
    if df.empty:
        return go.Figure()

    # Calculate Moving Averages
    df['ma10'] = df['close'].rolling(window=10).mean()
    df['ma20'] = df['close'].rolling(window=20).mean()

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.05, subplot_titles=('K线与移动平均线', 'MACD'), 
                        row_heights=[0.7, 0.3])

    fig.add_trace(go.Candlestick(x=df['date'], open=df['open'], high=df['high'], low=df['low'], close=df['close'], name="K线"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['date'], y=df['ma10'], mode='lines', name='MA10', line=dict(color='orange', width=1)), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['date'], y=df['ma20'], mode='lines', name='MA20', line=dict(color='purple', width=1)), row=1, col=1)

    colors = ['green' if val >= 0 else 'red' for val in df['macdhist']]
    fig.add_trace(go.Bar(x=df['date'], y=df['macdhist'], name='MACD Hist', marker_color=colors), row=2, col=1)
    fig.add_trace(go.Scatter(x=df['date'], y=df['macd'], mode='lines', name='MACD'), row=2, col=1)
    fig.add_trace(go.Scatter(x=df['date'], y=df['macdsignal'], mode='lines', name='Signal'), row=2, col=1)

    fig.update_layout(title_text='股价走势与技术指标', xaxis_rangeslider_visible=False, height=600, legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    fig.update_yaxes(title_text="价格", row=1, col=1)
    fig.update_yaxes(title_text="MACD", row=2, col=1)

    return fig

def main():
    st.set_page_config(page_title="LiangZiXuanGu - 量子选股", layout="wide")

    st.title("量子选股 (LiangZiXuanGu) AI Agent")
    st.markdown("一个基于LangGraph多代理工作流的A股智能分析投研工具。")

    with st.sidebar:
        st.header("分析设置")
        stock_code = st.text_input("请输入股票代码", value="000001", help="例如：平安银行输入 000001")

        # Date range selection
        today = datetime.now()
        one_year_ago = today - timedelta(days=365)
        start_date = st.date_input("开始日期", value=one_year_ago, min_value=datetime(2010, 1, 1), max_value=today)
        end_date = st.date_input("结束日期", value=today, min_value=start_date, max_value=today)

        available_indicators = get_available_indicators()
        selected_indicators = st.multiselect("选择技术指标", options=available_indicators, default=available_indicators)
        start_button = st.button("开始分析", type="primary", use_container_width=True)
        st.markdown("---")
        st.header("免责声明")
        st.warning("本项目及所有内容仅供学习研究，不构成任何投资建议。股市有风险，投资需谨慎。")

    if start_button:
        if not stock_code:
            st.error("请输入有效的股票代码。")
            return

        initial_state = {
            "stock_code": stock_code, 
            "indicators": selected_indicators,
            "start_date": start_date.strftime("%Y%m%d"),
            "end_date": end_date.strftime("%Y%m%d"),
        }
        
        st.markdown("### 分析流程")
        # Create two separate, expanded expanders as per the new request
        data_details_expander = st.expander("详细数据", expanded=True)
        ai_summary_expander = st.expander("AI技术面总结", expanded=True)
        final_report_container = st.container()

        # --- Column Name Translation Map ---
        COLUMN_MAP = {
            'date': '日期', 'open': '开盘', 'close': '收盘', 'high': '最高', 'low': '最低',
            'volume': '成交量', 'amount': '成交额', 'amplitude': '振幅', 'pct_chg': '涨跌幅',
            'change': '涨跌额', 'turnover': '换手率', 'rsi': 'RSI', 'macd': 'MACD',
            'macdsignal': 'Signal', 'macdhist': 'Hist', 'ma20': 'MA20', 'k': 'K', 'd': 'D',
            'obv': 'OBV', 'bbands_upper': '布林上轨', 'bbands_middle': '布林中轨', 'bbands_lower': '布林下轨'
        }

        last_known_state = {}
        try:
            with st.spinner("AI Agent 正在工作中，请稍候..."):
                for event in app.stream(initial_state):
                    for key, value in event.items():
                        last_known_state.update(value) # Continuously update state
                        
                        if key == "analyze_data":
                            # Populate the first expander with the data table
                            with data_details_expander:
                                analyzed_df = value.get('analyzed_data', pd.DataFrame())
                                if not analyzed_df.empty:
                                    st.write("带指标的详细数据：")
                                    display_df = analyzed_df.copy()
                                    display_df.rename(columns={k: v for k, v in COLUMN_MAP.items() if k in display_df.columns}, inplace=True)
                                    st.dataframe(display_df)
                                else:
                                    st.write("未能生成详细数据。")
                            
                            # Populate the second expander with the AI summary
                            with ai_summary_expander:
                                st.info(value.get('technical_summary', "未能生成AI总结。"))

            # --- Final Display after stream is complete ---
            final_report_container.markdown("### 📈 最终投研报告")
            if last_known_state and not last_known_state.get("error"):
                final_decision_text = last_known_state.get("final_decision", "未能生成报告。")
                final_report_container.markdown(final_decision_text)
                final_report_container.download_button(
                    label="📥 下载投研报告 (.md)",
                    data=final_decision_text,
                    file_name=f'{stock_code}_analysis_report.md',
                    mime='text/markdown',
                )
                
                df_analyzed = last_known_state.get("analyzed_data")
                if isinstance(df_analyzed, pd.DataFrame) and not df_analyzed.empty:
                    st.markdown("---")
                    st.subheader("📊 交互式K线图")
                    fig = create_candlestick_chart(df_analyzed)
                    st.plotly_chart(fig, use_container_width=True)
            else:
                if last_known_state:
                    error_message = last_known_state.get("error", "发生未知错误。")
                else:
                    error_message = "工作流未能返回任何状态，执行可能被中断。"
                st.error(f"分析过程中出现错误: {error_message}")

        except Exception as e:
            st.error(f"执行工作流时发生严重错误: {e}")

    else:
        st.info("请在左侧输入股票代码，然后点击“开始分析”按钮。")

if __name__ == "__main__":
    main()
