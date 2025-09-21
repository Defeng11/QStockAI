# -*- coding: utf-8 -*-

"""
Handles the core logic for stock screening, including fetching stock universe,
batch data retrieval, and batch strategy application.
"""

import pandas as pd
import time
from typing import List, Dict

# Import necessary modules from src
from src.data_handler import get_stock_daily
from src.strategy_handler import apply_five_step_integrated_strategy


def get_stock_universe() -> List[str]:
    """
    Fetches a list of all A-share stock codes.
    Currently uses a placeholder list. In a real scenario, this would fetch from a data source.
    """
    print("正在获取股票池...")
    # Placeholder for actual stock universe retrieval (e.g., from AkShare, Baostock)
    # For testing, return a small, fixed list.
    # In a real scenario, this would involve a call like akshare.stock_zh_a_spot_em()
    # or baostock.query_all_stock().
    stock_list = ["000001", "600000", "000002", "600036"] # Example stocks
    print(f"已获取 {len(stock_list)} 只股票代码。")
    return stock_list


def batch_get_stock_daily(stock_list: List[str], start_date: str, end_date: str, max_retries: int = 3, initial_delay: int = 2) -> Dict[str, pd.DataFrame]:
    """
    Batch fetches daily data for a list of stock codes with rate limiting and exponential backoff.

    Args:
        stock_list (List[str]): List of stock codes.
        start_date (str): Start date in YYYYMMDD format.
        end_date (str): End date in YYYYMMDD format.
        max_retries (int): Maximum number of retries for each stock.
        initial_delay (int): Initial delay in seconds before retrying.

    Returns:
        Dict[str, pd.DataFrame]: A dictionary where keys are stock codes and values are their DataFrames.
    """
    print(f"正在批量获取 {len(stock_list)} 只股票的历史数据...")
    all_stock_data = {}
    for i, stock_code in enumerate(stock_list):
        print(f"  获取 {stock_code} 数据 ({i+1}/{len(stock_list)})... ")
        retries = 0
        current_delay = initial_delay
        while retries <= max_retries:
            try:
                df = get_stock_daily(stock_code, start_date, end_date)
                if not df.empty:
                    all_stock_data[stock_code] = df
                    print(f"    {stock_code} 数据获取成功。")
                    break # Exit retry loop on success
                else:
                    print(f"    {stock_code} 数据获取失败或为空。")
                    if retries < max_retries:
                        print(f"    重试 {stock_code} ({retries + 1}/{max_retries})，等待 {current_delay} 秒...")
                        time.sleep(current_delay)
                        current_delay *= 2 # Exponential backoff
                        retries += 1
                    else:
                        print(f"    {stock_code} 达到最大重试次数，放弃获取。")
                        break # Exit retry loop after max retries
            except Exception as e:
                if retries < max_retries:
                    print(f"    获取 {stock_code} 数据时发生错误: {e}。重试 ({retries + 1}/{max_retries})，等待 {current_delay} 秒...")
                    time.sleep(current_delay)
                    current_delay *= 2 # Exponential backoff
                    retries += 1
                else:
                    print(f"    获取 {stock_code} 数据时发生错误: {e}。达到最大重试次数，放弃获取。")
                    break # Exit retry loop after max retries
        
        # Add a general delay between different stock requests to be polite
        time.sleep(initial_delay)

    print("批量数据获取完成。")
    return all_stock_data


def batch_apply_strategy(data_dict: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    """
    Applies the five-step integrated strategy to each stock's DataFrame in the dictionary.

    Args:
        data_dict (Dict[str, pd.DataFrame]): Dictionary of stock codes to their DataFrames.

    Returns:
        Dict[str, pd.DataFrame]: Dictionary with strategy applied and 'signal' column added.
    """
    print("正在批量应用策略...")
    processed_data = {}
    for stock_code, df in data_dict.items():
        if not df.empty:
            print(f"  对 {stock_code} 应用策略...")
            try:
                df_with_signals = apply_five_step_integrated_strategy(df)
                processed_data[stock_code] = df_with_signals
            except Exception as e:
                print(f"    对 {stock_code} 应用策略时发生错误: {e}")
        else:
            print(f"  跳过 {stock_code}，数据为空。")
    print("批量策略应用完成。")
    return processed_data


def filter_signals(data_dict: Dict[str, pd.DataFrame], signal_type: str = 'buy', recent_days: int = 5) -> List[Dict]:
    """
    Filters stocks based on generated signals within recent days.

    Args:
        data_dict (Dict[str, pd.DataFrame]): Dictionary of stock codes to their DataFrames with signals.
        signal_type (str): Type of signal to filter ('buy' or 'sell').
        recent_days (int): Look back for signals within this many recent days.

    Returns:
        List[Dict]: A list of dictionaries, each containing 'stock_code', 'signal_date', 'signal_type'.
    """
    print(f"正在筛选最近 {recent_days} 天内的 {signal_type} 信号...")
    found_signals = []
    target_signal = 1 if signal_type == 'buy' else -1

    for stock_code, df in data_dict.items():
        if not df.empty and 'signal' in df.columns:
            # Ensure 'date' column is datetime for comparison
            if not pd.api.types.is_datetime64_any_dtype(df['date']):
                df['date'] = pd.to_datetime(df['date'], format='%Y%m%d')
            
            # Filter for recent signals
            recent_df = df[df['date'] >= (pd.to_datetime(df['date'].max()) - pd.Timedelta(days=recent_days))]
            
            signals_in_recent_days = recent_df[recent_df['signal'] == target_signal]
            
            if not signals_in_recent_days.empty:
                for _, row in signals_in_recent_days.iterrows():
                    found_signals.append({
                        'stock_code': stock_code,
                        'signal_date': row['date'].strftime('%Y-%m-%d'),
                        'signal_type': signal_type
                    })
    print(f"筛选完成，共找到 {len(found_signals)} 个符合条件的信号。")
    return found_signals

# --- Test Block ---
if __name__ == '__main__':
    print("--- 测试 screening_handler 模块 ---")
    test_start_date = "20240101"
    test_end_date = "20240919"

    # 1. Get stock universe
    universe = get_stock_universe()

    # 2. Batch get data
    all_data = batch_get_stock_daily(universe, test_start_date, test_end_date)

    # 3. Batch apply strategy
    processed_all_data = batch_apply_strategy(all_data)

    # 4. Filter signals
    buy_signals = filter_signals(processed_all_data, signal_type='buy', recent_days=10)
    sell_signals = filter_signals(processed_all_data, signal_type='sell', recent_days=10)

    print("\n--- 筛选结果预览 ---")
    print("买入信号:", buy_signals)
    print("卖出信号:", sell_signals)

    if not buy_signals and not sell_signals:
        print("未找到任何买入或卖出信号。")
    print("\n--- screening_handler 模块测试结束 ---")
