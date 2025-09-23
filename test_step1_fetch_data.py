# -*- coding: utf-8 -*-
"""
Test Step 1: Data Fetching

This script tests the first part of the data pipeline:
1. Fetches raw daily data for a single stock using get_stock_daily.
2. Saves the result to a temporary CSV file to act as the 'sealed envelope' for the next step.
"""

import pandas as pd
import os

# Import the function to be tested
from src.data_handler import get_stock_daily

# --- Configuration ---
TEST_STOCK_CODE = "000001"  # 平安银行
TEMP_DATA_FILE = "temp_stock_data.csv"

def test_step_1():
    """Executes the first step of the data integrity test."""
    print(f"--- 开始测试 [第1棒：数据获取] (股票: {TEST_STOCK_CODE}) ---")

    # 1. Fetch raw daily data
    # The get_stock_daily function will print whether it's using a local file or AkShare
    try:
        raw_df = get_stock_daily(TEST_STOCK_CODE, start_date="20230101")
        if raw_df is None or raw_df.empty:
            print(f"错误: 未能获取到股票 {TEST_STOCK_CODE} 的数据。测试终止。")
            return
    except Exception as e:
        print(f"获取数据时发生未知错误: {e}")
        return

    # 2. Save the data to a temporary file
    try:
        raw_df.to_csv(TEMP_DATA_FILE, index=False, encoding='utf-8-sig')
        print(f"\n成功将获取到的 {len(raw_df)} 条原始数据保存到临时文件: {TEMP_DATA_FILE}")
    except Exception as e:
        print(f"保存到CSV文件时发生错误: {e}")
        return

    # 3. Display a sample of the saved data for verification
    print("\n--- 已保存数据的最后5行预览 ---")
    print(raw_df.tail())
    print("\n--- [第1棒] 测试成功 --- ")
    print(f"下一步，请运行 test_step2_calculate_indicators.py 来验证计算过程。")

if __name__ == "__main__":
    # Clean up old temp file before running
    if os.path.exists(TEMP_DATA_FILE):
        os.remove(TEMP_DATA_FILE)
        print(f"已删除旧的临时文件: {TEMP_DATA_FILE}")
    test_step_1()
