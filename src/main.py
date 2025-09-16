# -*- coding: utf-8 -*-

"""
Main entry point for the Streamlit application.
Provides the user interface for the LiangZiXuanGu AI Agent.
"""

import streamlit as st
import pandas as pd

# Import the compiled graph app from our workflow module
from graph_workflow import app

def main():
    st.set_page_config(page_title="LiangZiXuanGu - 量子选股", layout="wide")

    # --- Header ---
    st.title("量子选股 (LiangZiXuanGu) AI Agent")
    st.markdown("一个基于LangGraph多代理工作流的A股智能分析投研工具。")

    # --- Sidebar for Inputs ---
    with st.sidebar:
        st.header("分析设置")
        
        stock_code = st.text_input("请输入股票代码", value="000001", help="例如：平安银行输入 000001")
        
        # Get available indicators from the analysis handler
        # (For now, we hardcode them, but this could be dynamic in a future version)
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

        # Prepare inputs for the graph
        initial_state = {
            "stock_code": stock_code,
            "indicators": selected_indicators
        }

        # Placeholders for the results
        final_report_placeholder = st.empty()
        summary_placeholder = st.empty()
        chart_placeholder = st.empty()
        data_placeholder = st.empty()

        final_report_placeholder.info(f"正在为您分析股票: {stock_code}，请稍候...", icon="🤖")

        # Stream the graph execution
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
                # Store the final state when the graph finishes
                if END in event:
                    final_state = event[END]
            
            status.update(label="分析完成！", state="complete", expanded=False)

        # Clear the initial message
        final_report_placeholder.empty()

        # --- Display Results ---
        if final_state and not final_state.get("error"):
            st.subheader("📈 最终投研报告")
            st.markdown(final_state.get("final_decision", "未能生成报告。"))

            with st.expander("查看AI技术面分析摘要"):
                st.markdown(final_state.get("technical_summary", "未能生成技术面摘要。"))

            with st.expander("查看详细数据与指标"):
                df = final_state.get("analyzed_data")
                if isinstance(df, pd.DataFrame):
                    st.dataframe(df)
                    
                    # Chart
                    st.subheader("📊 股价与RSI指标图")
                    chart_data = df.set_index('date')
                    st.line_chart(chart_data[['close', 'rsi']])
                else:
                    st.warning("无法显示详细数据。")
        else:
            error_message = final_state.get("error", "发生未知错误。")
            st.error(f"分析过程中出现错误: {error_message}")

    else:
        st.info("请在左侧输入股票代码，然后点击“开始分析”按钮。")


if __name__ == "__main__":
    # To run the app, use the command:
    # venv\Scripts\activate && streamlit run src/main.py
    main()