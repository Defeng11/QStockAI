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

def _create_signal_matrix(stock_data, recent_days, end_date):
    """
    Creates a DataFrame for the signal matrix view.
    
    Args:
        stock_data (pd.DataFrame): DataFrame with signal columns ('buy_signal', 'sell_signal').
        recent_days (int): The number of recent days to show in the matrix.
        end_date (datetime): The end date for the matrix.

    Returns:
        pd.DataFrame: A DataFrame formatted for the signal matrix.
    """
    # Define the date range for columns
    dates = [(end_date - timedelta(days=i)) for i in range(recent_days - 1, -1, -1)]
    date_strs = [d.strftime('%Y-%m-%d') for d in dates]
    
    # Create an empty matrix
    matrix_df = pd.DataFrame(index=['买入信号', '卖出信号'], columns=date_strs).fillna('')
    
    # Filter stock_data for the relevant date range
    relevant_data = stock_data[stock_data['date'].isin(dates)]
    
    # Populate the matrix with signals
    for _, row in relevant_data.iterrows():
        date_str = row['date'].strftime('%Y-%m-%d')
        if date_str in matrix_df.columns:
            if row.get('buy_signal') == 1:
                matrix_df.loc['买入信号', date_str] = '⭕'
            if row.get('sell_signal') == 1:
                matrix_df.loc['卖出信号', date_str] = '⭕'
                
    return matrix_df

def main():
    st.set_page_config(page_title="策略选股", layout="wide")

    st.title("📊 策略选股")
    st.markdown("根据预设的交易策略，批量筛选符合条件的股票。" )

    # --- Expander 1: Filtering Settings and Actions ---
    with st.expander("⚙️ 筛选设置与操作", expanded=True):
        col1, col2 = st.columns(2)

        with col1:
            today = datetime.now()
            one_year_ago = today - timedelta(days=365)
            start_date = st.date_input("数据开始日期", value=one_year_ago, min_value=datetime(2010, 1, 1), max_value=today)
            end_date = st.date_input("数据结束日期", value=today, min_value=start_date, max_value=today)
            signal_type = st.selectbox("信号类型", ["buy", "sell"], format_func=lambda x: "买入信号" if x == "buy" else "卖出信号")
            recent_days = st.slider("信号回溯天数 (最近几天内)", min_value=1, max_value=30, value=5)

        with col2:
            if st.button("更新板块数据", use_container_width=True):
                get_stock_universe(force_refresh=True)
                st.success("股票池已刷新！")

            universe_data = get_stock_universe()
            all_industries = sorted(list(set([item.get('所属行业', '未知') for item in universe_data])))
            
            st.markdown("#### 选择行业/板块")
            if 'selected_industries_checkbox' not in st.session_state:
                st.session_state.selected_industries_checkbox = []

            if st.button("全选/取消全选", key="select_all_industries_button"):
                if len(st.session_state.selected_industries_checkbox) == len(all_industries):
                    st.session_state.selected_industries_checkbox = []
                else:
                    st.session_state.selected_industries_checkbox = all_industries.copy()
                st.rerun()

            num_cols_checkbox = 3
            cols_checkbox = st.columns(num_cols_checkbox)
            selected_industries_temp = []
            for i, industry in enumerate(all_industries):
                with cols_checkbox[i % num_cols_checkbox]:
                    if st.checkbox(industry, value=(industry in st.session_state.selected_industries_checkbox), key=f"industry_checkbox_{industry}"):
                        selected_industries_temp.append(industry)
            
            selected_industries = selected_industries_temp
            st.session_state.selected_industries_checkbox = selected_industries_temp

        st.markdown("---")
        start_screening_button = st.button("开始选股", type="primary", use_container_width=True)

    # --- Expander 2: Process and Results Display ---
    expander = st.expander("📈 选股过程与结果", expanded=True)
    
    if start_screening_button:
        with expander:
            results_col, logs_col = st.columns([0.7, 0.3])

            # --- Right Column: Logs and Progress ---
            with logs_col:
                st.markdown("#### 实时状态")
                progress_bar_placeholder = st.empty()
                log_container = st.empty()
                log_container.text_area("筛选日志", value="等待启动...", height=350, disabled=True, key="log_area_init")

            # --- Left Column: Results ---
            with results_col:
                st.markdown("#### 筛选结果")
                results_placeholder = st.empty()
                results_placeholder.info("请在上方设置筛选条件，然后点击“开始选股”按钮。" )

        initial_screening_state = {
            "start_date": start_date.strftime("%Y%m%d"),
            "end_date": end_date.strftime("%Y%m%d"),
            "signal_type": signal_type,
            "recent_days": recent_days,
            "selected_industries": selected_industries
        }
        
        st.session_state.terminal_logs = "选股任务已启动...\n"
        log_container.text_area("筛选日志", value=st.session_state.terminal_logs, height=350, disabled=True, key="log_area_start")
        
        final_screening_state = {}
        try:
            stream_result = screening_app.stream(initial_screening_state)
            if stream_result is None:
                results_placeholder.error("错误：选股工作流返回了 None。请检查配置或API Key。" )
                return

            for event in stream_result:
                for key, value in event.items():
                    final_screening_state.update(value)
                    
                    log_message = ""
                    progress_value = -1

                    if key == "get_universe":
                        log_message = "正在获取股票池..."
                        progress_value = 5
                    elif "progress_batch_get_data" in value:
                        progress = value["progress_batch_get_data"]
                        log_message = f"获取数据: {progress}%"
                        progress_value = 5 + int(progress * 0.25) # 5% to 30%
                    elif "progress_batch_apply_strategy" in value:
                        progress = value["progress_batch_apply_strategy"]
                        log_message = f"应用策略: {progress}%"
                        progress_value = 30 + int(progress * 0.60) # 30% to 90%
                    elif key == "filter_results":
                        log_message = "筛选并整理结果..."
                        progress_value = 95
                    
                    if log_message:
                        st.session_state.terminal_logs += log_message + "\n"
                        log_container.text_area("筛选日志", value=st.session_state.terminal_logs, height=350, disabled=True, key=f"log_area_{progress_value}")
                    
                    if progress_value != -1:
                        progress_bar_placeholder.progress(progress_value, text=log_message)

            # --- Final Display after stream is complete ---
            progress_bar_placeholder.progress(100, text="选股完成！")
            
            with results_placeholder.container():
                if final_screening_state and not final_screening_state.get("error"):
                    found_signals = final_screening_state.get("found_signals", [])
                    if found_signals:
                        st.success(f"选股完成！成功找到 {len(found_signals)} 个符合条件的股票！")
                        st.session_state.terminal_logs += f"选股完成！成功找到 {len(found_signals)} 个符合条件的股票！\n"

                        signals_df = pd.DataFrame(found_signals)
                        display_cols = ['stock_code', 'stock_name', 'industry', 'signal_date', 'signal_type']
                        signals_df = signals_df[display_cols]
                        
                        processed_stock_data = final_screening_state.get("processed_stock_data", {})
                        
                        overview_tab, matrix_tab = st.tabs(["结果总览", "信号矩阵视图"])

                        with overview_tab:
                            st.dataframe(signals_df, use_container_width=True)

                        with matrix_tab:
                            st.markdown("##### 最近信号分布矩阵")
                            st.caption("“⭕”表示当天出现对应信号。" )
                            for _, stock_row in signals_df.iterrows():
                                stock_code = stock_row['stock_code']
                                stock_name = stock_row['stock_name']
                                if stock_code in processed_stock_data:
                                    st.subheader(f"{stock_code} - {stock_name}")
                                    matrix_df = _create_signal_matrix(processed_stock_data[stock_code], recent_days, end_date)
                                    st.dataframe(matrix_df, use_container_width=True)
                                else:
                                    st.warning(f"未找到 {stock_code} - {stock_name} 的详细信号数据。" )

                    else:
                        st.info("选股完成！未找到符合当前筛选条件的股票。" )
                        st.session_state.terminal_logs += "选股完成！未找到符合当前筛选条件的股票。\n"
                else:
                    error_message = final_screening_state.get("error", "发生未知错误。" )
                    st.error(f"选股过程中出现错误: {error_message}")
                    st.session_state.terminal_logs += f"选股过程中出现错误: {error_message}\n"

            # Final log update
            log_container.text_area("筛选日志", value=st.session_state.terminal_logs, height=350, disabled=True, key="log_area_final")

        except Exception as e:
            with expander:
                st.error(f"执行选股工作流时发生严重错误: {e}")
                st.session_state.terminal_logs += f"执行选股工作流时发生严重错误: {e}\n"
                # Ensure logs are displayed even on hard crash
                if 'log_container' in locals():
                    log_container.text_area("筛选日志", value=st.session_state.terminal_logs, height=350, disabled=True, key="log_area_exception")

    else:
        with expander:
            st.info("请在上方设置筛选条件，然后点击“开始选股”按钮。" )

if __name__ == "__main__":
    main()
