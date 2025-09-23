# -*- coding: utf-8 -*-
"""
Test Step 2: Indicator Calculation

This script tests the second part of the data pipeline:
1. Reads the raw data from the temporary CSV file created by step 1.
2. Passes this data to the indicator function.
3. Verifies that the indicators are calculated based on the provided data.
"""

import pandas as pd
import os

# Import the function to be tested
from src.analysis_handler import calculate_strategy_indicators

# --- Configuration ---
TEMP_DATA_FILE = "temp_stock_data.csv"

def test_step_2():
    """Executes the second step of the data integrity test."""
    print(f"--- 开始测试 [第2棒：指标计算] ---")

    # 1. Check if the temporary data file exists
    if not os.path.exists(TEMP_DATA_FILE):
        print(f"错误: 找不到临时数据文件 '{TEMP_DATA_FILE}'.")
        print("请先成功运行 test_step1_fetch_data.py。测试终止。")
        return
    
    print(f"成功找到由上一棒选手创建的数据文件: {TEMP_DATA_FILE}")

    # 2. Load the raw data from the file
    try:
        raw_df = pd.read_csv(TEMP_DATA_FILE)
        # The 'date' column was saved as a string, convert it back to datetime for talib
        raw_df['date'] = pd.to_datetime(raw_df['date'])
        print(f"已从文件加载 {len(raw_df)} 条原始数据。")
    except Exception as e:
        print(f"从CSV文件读取数据时发生错误: {e}")
        return

    # 3. Pass the DataFrame to the calculation function
    print("\n将原始数据传递给指标计算函数...")
    try:
        df_with_indicators = calculate_strategy_indicators(raw_df)
    except Exception as e:
        print(f"指标计算过程中发生错误: {e}")
        return

    # 4. Display a sample of the final data for verification
    print("\n--- 包含指标的最终数据预览 (最后5行) ---")
    print("请注意，现在表格中应包含原始的'close'列和新计算的'macdhist', 'rsi'等列。")
    print(df_with_indicators.tail())
    print("\n--- [第2棒] 测试成功 ---")
    print(f"下一步，请运行 test_combined_workflow.py 来进行最终的集成测试。")

if __name__ == "__main__":
    test_step_2()
