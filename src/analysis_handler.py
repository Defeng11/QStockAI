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

def get_available_indicators() -> list[str]:
    """Returns a list of all registered indicator names."""
    return list(_indicator_functions.keys())

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

@register_indicator('ma')
def _add_ma(df: pd.DataFrame, timeperiod: int = 20) -> pd.DataFrame:
    """Calculates and adds a Simple Moving Average (SMA) to the DataFrame."""
    df[f'ma{timeperiod}'] = talib.SMA(df['close'], timeperiod=timeperiod)
    return df

@register_indicator('kd')
def _add_kd(df: pd.DataFrame, fastk_period: int = 9, slowk_period: int = 3, slowd_period: int = 3) -> pd.DataFrame:
    """Calculates and adds Stochastic Oscillator (%K and %D) to the DataFrame."""
    slowk, slowd = talib.STOCH(df['high'], df['low'], df['close'], 
                               fastk_period=fastk_period, 
                               slowk_period=slowk_period, 
                               slowk_matype=0, # SMA
                               slowd_period=slowd_period, 
                               slowd_matype=0) # SMA
    df['k'] = slowk
    df['d'] = slowd
    return df

@register_indicator('obv')
def _add_obv(df: pd.DataFrame) -> pd.DataFrame:
    """Calculates and adds On-Balance Volume (OBV) to the DataFrame."""
    df['obv'] = talib.OBV(df['close'], df['volume'])
    return df

@register_indicator('bbands')
def _add_bbands(df: pd.DataFrame, timeperiod: int = 20, nbdevup: int = 2, nbdevdn: int = 2) -> pd.DataFrame:
    """Calculates and adds Bollinger Bands to the DataFrame."""
    upper, middle, lower = talib.BBANDS(df['close'], 
                                        timeperiod=timeperiod, 
                                        nbdevup=nbdevup, 
                                        nbdevdn=nbdevdn, 
                                        matype=0) # SMA
    df['bbands_upper'] = upper
    df['bbands_middle'] = middle
    df['bbands_lower'] = lower
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

def calculate_strategy_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates all necessary technical indicators for the five-step strategy.
    """
    df_out = df.copy()
    
    # 1. MA (Moving Average)
    df_out['ma20'] = talib.SMA(df_out['close'], timeperiod=20)
    df_out['ma200'] = talib.SMA(df_out['close'], timeperiod=200)
    
    # 2. MACD (Moving Average Convergence Divergence)
    macd, macdsignal, macdhist = talib.MACD(df_out['close'], fastperiod=12, slowperiod=26, signalperiod=9)
    df_out['macd'] = macd
    df_out['macdsignal'] = macdsignal
    df_out['macdhist'] = macdhist
    
    # 3. RSI (Relative Strength Index)
    df_out['rsi'] = talib.RSI(df_out['close'], timeperiod=14)
    
    print("  - 已计算策略所需指标 (MA20, MA200, MACD, RSI)")
    return df_out


# --- Test Block ---
if __name__ == '__main__':
    # This block is for testing the functions in this module directly.
    # It will fetch data for a sample stock and calculate all registered indicators.
    from src.data_handler import get_stock_daily

    test_stock_code = "000001"  # 平安银行
    print(f"--- 测试 analysis_handler 模块 (股票代码: {test_stock_code}) ---")
    
    # 1. Get raw daily data
    daily_data = get_stock_daily(test_stock_code, start_date="20230101")

    if not daily_data.empty:
        # 2. Get all available indicators dynamically
        all_indicators = get_available_indicators()
        print(f"\n动态获取到所有可用指标: {all_indicators}")

        # 3. Add all indicators
        data_with_indicators = add_technical_indicators(daily_data, indicators=all_indicators)

        print("\n--- 计算结果预览 (最后5条数据) ---")
        # Display the last 5 rows to check the new columns
        print(data_with_indicators.tail())

        print("\n--- 数据列名和类型 ---")
        print(data_with_indicators.info())
    else:
        print("测试失败，未能获取到用于分析的原始数据。")