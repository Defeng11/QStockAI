# -*- coding: utf-8 -*-

"""
Streamlit page for stock screening based on defined strategies.
"""

import streamlit as st
from datetime import datetime, timedelta
import pandas as pd

# Import the screening workflow app
from src.screening_workflow import screening_app
from src.screening_handler import get_stock_universe

def main():
    st.set_page_config(page_title="策略选股", layout="wide")

    st.title("📊 策略选股")
    st.markdown("根据预设的交易策略，批量筛选符合条件的股票。")

    # --- Expander 1: Filtering Settings and Actions ---
    with st.expander("⚙️ 筛选设置与操作"): # New expander
        col1, col2 = st.columns(2) # Create two columns

        with col1: # Left column
            # Date range selection for screening data
            today = datetime.now()
            one_year_ago = today - timedelta(days=365)
            start_date = st.date_input("数据开始日期", value=one_year_ago, min_value=datetime(2010, 1, 1), max_value=today)
            end_date = st.date_input("数据结束日期", value=today, min_value=start_date, max_value=today)

            # Signal type selection
            signal_type = st.selectbox("信号类型", ["buy", "sell"], format_func=lambda x: "买入信号" if x == "buy" else "卖出信号")
            
            # Recent days for signal filtering
            recent_days = st.slider("信号回溯天数 (最近几天内)", min_value=1, max_value=30, value=5)

        with col2: # Right column
            # Change button text and functionality
            if st.button("更新板块数据", use_container_width=True): # Changed button text
                get_stock_universe(force_refresh=True)
                st.success("股票池已刷新！")

            universe_data = get_stock_universe()
            all_industries = sorted(list(set([item.get('所属行业', '未知') for item in universe_data])))
            
            st.markdown("#### 选择行业/板块") # New sub-header for checkboxes

            # --- Select All Button ---
            select_all_button = st.button("全选/取消全选", key="select_all_industries_button")

            # Initialize selected_industries_checkbox in session_state if not present
            if 'selected_industries_checkbox' not in st.session_state:
                st.session_state.selected_industries_checkbox = []

            # Handle Select All button click
            if select_all_button:
                if len(st.session_state.selected_industries_checkbox) == len(all_industries):
                    # If all are currently selected, deselect all
                    st.session_state.selected_industries_checkbox = []
                else:
                    # Otherwise, select all
                    st.session_state.selected_industries_checkbox = all_industries.copy()
                st.rerun() # Force rerun to update checkbox states

            # --- Checkbox Grid for Industries ---
            num_cols_checkbox = 3 # Number of columns for checkboxes
            cols_checkbox = st.columns(num_cols_checkbox)
            
            selected_industries_temp = []
            for i, industry in enumerate(all_industries):
                with cols_checkbox[i % num_cols_checkbox]: # Place checkbox in a column
                    # Use a unique key for each checkbox
                    if st.checkbox(industry, value=(industry in st.session_state.selected_industries_checkbox), key=f"industry_checkbox_{industry}"):
                        selected_industries_temp.append(industry)
            
            # Update the actual selected_industries for the workflow
            selected_industries = selected_industries_temp
            st.session_state.selected_industries_checkbox = selected_industries_temp # Store for persistence

        st.markdown("---") # Separator below columns

        # Action Button (outside columns, spans full width)
        start_screening_button = st.button("开始选股", type="primary", use_container_width=True)

    # --- Expander 2: Process and Results Display ---
    with st.expander("📈 选股过程与结果"): # New expander
        st.markdown("### 筛选过程与结果")
        
        # Progress indicators
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Placeholder for terminal output
        if 'terminal_logs' not in st.session_state:
            st.session_state.terminal_logs = ""
        
        # This text_area will be updated *after* the stream completes
        terminal_output_placeholder = st.empty() # Use st.empty() to hold the text_area

    # --- Sidebar (only disclaimer remains) ---
    with st.sidebar: # Keep sidebar for disclaimer
        st.header("免责声明")
        st.warning("本项目及所有内容仅供学习研究，不构成任何投资建议。股市有风险，投资需谨慎。")

    # --- Logic for start_screening_button (outside expander context) ---
    if start_screening_button:
        initial_screening_state = {
            "start_date": start_date.strftime("%Y%m%d"),
            "end_date": end_date.strftime("%Y%m%d"),
            "signal_type": signal_type,
            "recent_days": recent_days,
            "selected_industries": selected_industries # Pass selected industries to workflow
        }
        
        # Clear logs on new run
        st.session_state.terminal_logs = "" 
        
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
                            status_text.info(f"正在获取股票数据... {progress}%") # Fixed: removed newline here # Added newline
                            st.session_state.terminal_logs += f"正在获取股票数据... {progress}%\n" # Append to logs
                            progress_bar.progress(progress // 2) # Half of total progress for data fetching
                        elif "progress_batch_apply_strategy" in value:
                            progress = value["progress_batch_apply_strategy"]
                            status_text.info(f"正在应用策略... {progress}%") # Fixed: removed newline here # Added newline
                            st.session_state.terminal_logs += f"正在应用策略... {progress}%\n" # Append to logs
                            progress_bar.progress(50 + progress // 2) # Second half for strategy application
                        elif key == "get_universe":
                            status_text.info("正在获取股票池...") # Fixed: removed newline here # Added newline
                            st.session_state.terminal_logs += "正在获取股票池...\n" # Append to logs
                            progress_bar.progress(0)
                        elif key == "filter_results":
                            status_text.info("正在筛选结果...") # Fixed: removed newline here # Added newline
                            st.session_state.terminal_logs += "正在筛选结果...\n" # Append to logs
                            progress_bar.progress(100)
                        
                        # Note: Real-time update of text_area within stream loop is complex.
                        # This will update st.session_state.terminal_logs, and the text_area
                        # will be rendered with the final value after the loop.

            # --- Final Display after stream is complete ---
            if final_screening_state and not final_screening_state.get("error"):
                found_signals = final_screening_state.get("found_signals", [])
                if found_signals:
                    status_text.success(f"选股完成！成功找到 {len(found_signals)} 个符合条件的股票！")
                    st.session_state.terminal_logs += f"选股完成！成功找到 {len(found_signals)} 个符合条件的股票！\n"
                    # Convert list of dicts to DataFrame for display
                    signals_df = pd.DataFrame(found_signals)
                    # Reorder columns for better display
                    display_cols = ['stock_code', 'stock_name', 'industry', 'signal_date', 'signal_type']
                    signals_df = signals_df[display_cols]
                    st.dataframe(signals_df, use_container_width=True)
                else:
                    status_text.info("选股完成！未找到符合当前筛选条件的股票。")
                    st.session_state.terminal_logs += "选股完成！未找到符合当前筛选条件的股票。\n"
            else:
                error_message = final_screening_state.get("error", "发生未知错误。")
                status_text.error(f"选股过程中出现错误: {error_message}")
                st.session_state.terminal_logs += f"选股过程中出现错误: {error_message}\n"

            # Final update to the text area after the loop
            terminal_output_placeholder.text_area(
                "终端输出 (仅显示关键日志)", 
                value=st.session_state.terminal_logs, 
                height=300, 
                disabled=True, 
                key="final_terminal_output"
            )

        except Exception as e:
            st.error(f"执行选股工作流时发生严重错误: {e}")
            st.session_state.terminal_logs += f"执行选股工作流时发生严重错误: {e}\n"
            terminal_output_placeholder.text_area(
                "终端输出 (仅显示关键日志)", 
                value=st.session_state.terminal_logs, 
                height=300, 
                disabled=True, 
                key="exception_terminal_output" # Unique key for exception case
            )

    else:
        st.info("请在上方设置筛选条件，然后点击“开始选股”按钮。") # Updated message

if __name__ == "__main__":
    main()
