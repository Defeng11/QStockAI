# -*- coding: utf-8 -*-

"""
Streamlit page for stock screening based on defined strategies.
"""

import streamlit as st
from datetime import datetime, timedelta
import pandas as pd

# Import the screening workflow app
from src.screening_workflow import screening_app

def main():
    st.set_page_config(page_title="策略选股", layout="wide")

    st.title("📊 策略选股")
    st.markdown("根据预设的交易策略，批量筛选符合条件的股票。")

    with st.sidebar:
        st.header("筛选设置")
        
        # Date range selection for screening data
        today = datetime.now()
        one_year_ago = today - timedelta(days=365)
        start_date = st.date_input("数据开始日期", value=one_year_ago, min_value=datetime(2010, 1, 1), max_value=today)
        end_date = st.date_input("数据结束日期", value=today, min_value=start_date, max_value=today)

        # Signal type selection
        signal_type = st.selectbox("信号类型", ["buy", "sell"], format_func=lambda x: "买入信号" if x == "buy" else "卖出信号")
        
        # Recent days for signal filtering
        recent_days = st.slider("信号回溯天数 (最近几天内)", min_value=1, max_value=30, value=5)

        start_screening_button = st.button("开始选股", type="primary", use_container_width=True)
        st.markdown("---")
        st.header("免责声明")
        st.warning("本项目及所有内容仅供学习研究，不构成任何投资建议。股市有风险，投资需谨慎。")

    if start_screening_button:
        initial_screening_state = {
            "start_date": start_date.strftime("%Y%m%d"),
            "end_date": end_date.strftime("%Y%m%d"),
            "signal_type": signal_type,
            "recent_days": recent_days
        }
        
        st.markdown("### 筛选过程与结果")
        
        # Progress indicators
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        final_screening_state = {}
        try:
            with st.spinner("AI Agent 正在批量选股中，请稍候..."):
                stream_result = screening_app.stream(initial_screening_state)
                if stream_result is None:
                    st.error("错误：选股工作流流式处理返回了 None。请检查工作流配置或API Key。")
                    return

                for event in stream_result:
                    for key, value in event.items():
                        final_screening_state.update(value)
                        
                        # Update progress bar and status text
                        if "progress_batch_get_data" in value:
                            progress = value["progress_batch_get_data"]
                            status_text.info(f"正在获取股票数据... {progress}%")
                            progress_bar.progress(progress // 2) # Half of total progress for data fetching
                        elif "progress_batch_apply_strategy" in value:
                            progress = value["progress_batch_apply_strategy"]
                            status_text.info(f"正在应用策略... {progress}%")
                            progress_bar.progress(50 + progress // 2) # Second half for strategy application
                        elif key == "get_universe":
                            status_text.info("正在获取股票池...")
                            progress_bar.progress(0)
                        elif key == "filter_results":
                            status_text.info("正在筛选结果...")
                            progress_bar.progress(100) # Full progress when filtering starts

            # --- Final Display after stream is complete ---
            if final_screening_state and not final_screening_state.get("error"):
                found_signals = final_screening_state.get("found_signals", [])
                if found_signals:
                    status_text.success(f"选股完成！成功找到 {len(found_signals)} 个符合条件的股票！")
                    # Convert list of dicts to DataFrame for display
                    signals_df = pd.DataFrame(found_signals)
                    st.dataframe(signals_df, use_container_width=True)
                else:
                    status_text.info("选股完成！未找到符合当前筛选条件的股票。")
            else:
                error_message = final_screening_state.get("error", "发生未知错误。")
                status_text.error(f"选股过程中出现错误: {error_message}")

        except Exception as e:
            st.error(f"执行选股工作流时发生严重错误: {e}")

    else:
        st.info("请在左侧设置筛选条件，然后点击“开始选股”按钮。")

if __name__ == "__main__":
    main()
