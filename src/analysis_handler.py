# -*- coding: utf-8 -*- 

"""
Handles the calculation of various technical analysis indicators.
This module is designed to be flexible, allowing new indicators to be added easily.
"""

import pandas as pd
import talib

# A registry to map indicator names to their calculation functions
_indicator_functions = {}

def register_indicator(name):
    """A decorator to register a new indicator calculation function."""
    def decorator(func):
        _indicator_functions[name] = func
        return func
    return decorator

@register_indicator('rsi')
def _add_rsi(df: pd.DataFrame, timeperiod: int = 14) -> pd.DataFrame:
    """Calculates and adds the RSI (Relative Strength Index) to the DataFrame."""
    df['rsi'] = talib.RSI(df['close'], timeperiod=timeperiod)
    return df

@register_indicator('macd')
def _add_macd(df: pd.DataFrame, fastperiod: int = 12, slowperiod: int = 26, signalperiod: int = 9) -> pd.DataFrame:
    """Calculates and adds MACD (Moving Average Convergence Divergence) to the DataFrame."""
    macd, macdsignal, macdhist = talib.MACD(df['close'], fastperiod=fastperiod, slowperiod=slowperiod, signalperiod=signalperiod)
    df['macd'] = macd
    df['macdsignal'] = macdsignal
    df['macdhist'] = macdhist
    return df

def add_technical_indicators(df: pd.DataFrame, indicators: list[str]) -> pd.DataFrame:
    """
    A flexible function to add a list of technical indicators to a DataFrame.

    Args:
        df (pd.DataFrame): The input DataFrame with stock data (must have 'close' column).
        indicators (list[str]): A list of indicator names to calculate (e.g., ['rsi', 'macd']).

    Returns:
        pd.DataFrame: The DataFrame with the added indicator columns.
    """
    print(f"开始计算技术指标: {indicators}")
    df_with_indicators = df.copy()
    for indicator_name in indicators:
        if indicator_name in _indicator_functions:
            df_with_indicators = _indicator_functions[indicator_name](df_with_indicators)
            print(f"  - 已添加 {indicator_name.upper()}")
        else:
            print(f"警告: 未知指标 '{indicator_name}'，将被忽略。")
    print("技术指标计算完成。")
    return df_with_indicators

# --- Test Block ---
if __name__ == '__main__':
    # This block is for testing the functions in this module directly.
    # It will fetch data for a sample stock and calculate the registered indicators.
    from data_handler import get_stock_daily

    test_stock_code = "000001"  # 平安银行
    print(f"--- 测试 analysis_handler 模块 (股票代码: {test_stock_code}) ---")
    
    # 1. Get raw daily data
    daily_data = get_stock_daily(test_stock_code, start_date="20230101")

    if not daily_data.empty:
        # 2. Define which indicators we want to calculate
        indicators_to_calc = ['rsi', 'macd', 'non_existent_indicator']

        # 3. Add the indicators
        data_with_indicators = add_technical_indicators(daily_data, indicators=indicators_to_calc)

        print("\n--- 计算结果预览 (最后5条数据) ---")
        # Display the last 5 rows to check the new columns
        print(data_with_indicators.tail())

        print("\n--- 数据列名和类型 ---")
        print(data_with_indicators.info())
    else:
        print("测试失败，未能获取到用于分析的原始数据。")
