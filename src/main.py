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
        available_indicators = ['rsi', 'macd']
        selected_indicators = st.multiselect("选择技术指标", options=available_indicators, default=available_indicators)
        start_button = st.button("开始分析", type="primary", use_container_width=True)
        st.markdown("---")
        st.header("免责声明")
        st.warning("本项目及所有内容仅供学习研究，不构成任何投资建议。股市有风险，投资需谨慎。")

    if start_button:
        if not stock_code:
            st.error("请输入有效的股票代码。")
            return

        initial_state = {"stock_code": stock_code, "indicators": selected_indicators}
        
        st.markdown("### 分析流程")
        raw_data_expander = st.expander("1. 数据获取结果", expanded=False)
        indicator_expander = st.expander("2. 技术分析结果", expanded=False)
        final_report_container = st.container()

        last_known_state = {}
        try:
            with st.spinner("AI Agent 正在工作中，请稍候..."):
                for event in app.stream(initial_state):
                    for key, value in event.items():
                        last_known_state.update(value) # Continuously update state
                        if key == "get_data":
                            with raw_data_expander:
                                st.write(f"已成功获取 **{stock_code}** 的 {len(value.get('raw_data', []))} 条日线数据。")
                                st.dataframe(value.get('raw_data', pd.DataFrame()).head())
                        elif key == "analyze_data":
                            with indicator_expander:
                                st.write("数据指标计算完成，AI技术面总结如下：")
                                st.info(value.get('technical_summary', ""))
                                st.write("带指标的详细数据：")
                                st.dataframe(value.get('analyzed_data', pd.DataFrame()))

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
