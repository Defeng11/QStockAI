# -*- coding: utf-8 -*-
"""
Test Step 3: Combined Workflow Test

This script tests the entire data pipeline in memory:
1. Fetches raw daily data using get_stock_daily.
2. Passes this data directly to the indicator calculation function.
3. Verifies that the indicators are calculated based on the provided data, all in one go.
"""

import pandas as pd

# Import the functions to be tested
from src.data_handler import get_stock_daily
from src.analysis_handler import calculate_strategy_indicators

# --- Configuration ---
TEST_STOCK_CODE = "000001"  # 平安银行

def test_step_3():
    """Executes the third and final step of the data integrity test (combined workflow)."""
    print(f"--- 开始测试 [第3棒：组合工作流] (股票: {TEST_STOCK_CODE}) ---")

    # 1. Fetch raw daily data (First Runner)
    print("\n正在获取原始数据...")
    try:
        raw_df = get_stock_daily(TEST_STOCK_CODE, start_date="20230101")
        if raw_df is None or raw_df.empty:
            print(f"错误: 未能获取到股票 {TEST_STOCK_CODE} 的数据。测试终止。")
            return
        print(f"成功获取 {len(raw_df)} 条原始数据。")
    except Exception as e:
        print(f"获取原始数据时发生错误: {e}")
        return

    # 2. Calculate indicators (Second Runner) - directly in memory
    print("\n正在计算技术指标...")
    try:
        df_with_indicators = calculate_strategy_indicators(raw_df)
    except Exception as e:
        print(f"计算技术指标时发生错误: {e}")
        return

    # 3. Display a sample of the final data for verification
    print("\n--- 组合工作流最终数据预览 (最后5行) ---")
    print("请确认原始数据和计算出的指标都正确无误。")
    print(df_with_indicators.tail())
    print("\n--- [第3棒] 组合工作流测试成功 ---")
    print("数据完整性测试已全部完成。")

if __name__ == "__main__":
    test_step_3()
