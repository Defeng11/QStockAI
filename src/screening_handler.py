# -*- coding: utf-8 -*-

"""
Handles the core logic for stock screening, including fetching stock universe,
batch data retrieval, and batch strategy application.
"""

import pandas as pd
import time
import os
import json
import concurrent.futures
from datetime import datetime, timedelta
from typing import List, Dict

# Import necessary modules from src
from src.data_handler import get_stock_daily, get_stock_universe
from src.strategy_handler import apply_five_step_integrated_strategy
from src.analysis_handler import calculate_strategy_indicators
import akshare as ak

# Define cache directory and file
CACHE_DIR = "cache"
UNIVERSE_CACHE_FILE = os.path.join(CACHE_DIR, "stock_universe_cache.json")
CACHE_EXPIRATION_HOURS = 24 # Cache expires after 24 hours




def _fetch_single_stock_with_retry(args):
    """
    Helper function to fetch data for a single stock with retry logic.
    To be used by a ThreadPoolExecutor.
    """
    stock_code, start_date, end_date, max_retries, initial_delay = args
    retries = 0
    current_delay = initial_delay
    while retries <= max_retries:
        try:
            df = get_stock_daily(stock_code, start_date, end_date)
            if df is not None and not df.empty:
                print(f"    {stock_code} 数据获取成功。")
                return stock_code, df
            else:
                # This case is treated as a failure to be retried
                raise ValueError(f"{stock_code} 数据获取为空。")
        except Exception as e:
            if retries < max_retries:
                print(f"    获取 {stock_code} 数据时发生错误: {e}。重试 ({retries + 1}/{max_retries})，等待 {current_delay} 秒...")
                time.sleep(current_delay)
                current_delay *= 2  # Exponential backoff
                retries += 1
            else:
                print(f"    获取 {stock_code} 数据时发生错误: {e}。达到最大重试次数，放弃获取。")
                return stock_code, None # Return None on final failure
    return stock_code, None

def batch_get_stock_daily(stock_list: List[str], start_date: str, end_date: str, max_retries: int = 3, initial_delay: int = 1, max_workers: int = 10) -> Dict[str, pd.DataFrame]:
    """
    Concurrently fetches daily data for a list of stock codes using a thread pool.

    Args:
        stock_list (List[str]): List of stock codes.
        start_date (str): Start date in YYYYMMDD format.
        end_date (str): End date in YYYYMMDD format.
        max_retries (int): Maximum number of retries for each stock.
        initial_delay (int): Initial delay in seconds before retrying.
        max_workers (int): The number of concurrent threads to use.

    Returns:
        Dict[str, pd.DataFrame]: A dictionary where keys are stock codes and values are their DataFrames.
    """
    total_stocks = len(stock_list)
    if total_stocks == 0:
        print("股票列表为空，无需获取数据。")
        return {}
        
    print(f"正在通过 {max_workers} 个线程，批量获取 {total_stocks} 只股票的历史数据...")
    all_stock_data = {}
    
    # Prepare arguments for each task
    tasks = [(code, start_date, end_date, max_retries, initial_delay) for code in stock_list]

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Using executor.map to maintain order and simplify result collection
        results = executor.map(_fetch_single_stock_with_retry, tasks)
        
        completed_count = 0
        for stock_code, df in results:
            if df is not None:
                all_stock_data[stock_code] = df
            
            # Update progress
            completed_count += 1
            progress_percent = int((completed_count / total_stocks) * 100)
            # Make sure progress is printed on a single line and flushed
            print(f"PROGRESS_BATCH_GET_DATA:{progress_percent}", flush=True)
            print(f"  进度: {completed_count}/{total_stocks} ({progress_percent}%)", flush=True)

    print("批量数据获取完成。")
    return all_stock_data


def batch_apply_strategy(data_dict: Dict[str, pd.DataFrame]) -> Dict[str, pd.DataFrame]:
    """
    Applies the five-step integrated strategy to each stock's DataFrame in the dictionary.
    This now includes calculating the necessary indicators before applying the strategy.

    Args:
        data_dict (Dict[str, pd.DataFrame]): Dictionary of stock codes to their raw DataFrames.

    Returns:
        Dict[str, pd.DataFrame]: Dictionary with strategy applied and 'signal' column added.
    """
    total_stocks = len(data_dict)
    print("正在批量应用策略...")
    processed_data = {}
    for i, (stock_code, df) in enumerate(data_dict.items()):
        # Calculate progress percentage
        progress_percent = int(((i + 1) / total_stocks) * 100)
        print(f"PROGRESS_BATCH_APPLY_STRATEGY:{progress_percent}", flush=True)

        if not df.empty:
            print(f"  对 {stock_code} 应用策略 ({i+1}/{total_stocks})... ")
            try:
                # Step 1: Calculate indicators required by the strategy
                df_with_indicators = calculate_strategy_indicators(df)
                
                # Step 2: Apply the actual strategy function
                df_with_signals = apply_five_step_integrated_strategy(df_with_indicators)
                processed_data[stock_code] = df_with_signals
            except Exception as e:
                print(f"    对 {stock_code} 应用策略时发生错误: {e}")
        else:
            print(f"  跳过 {stock_code}，数据为空。")
    print("批量策略应用完成。")
    return processed_data


def filter_signals(data_dict: Dict[str, pd.DataFrame], stock_names_map: Dict[str, str], stock_industry_map: Dict[str, str], signal_type: str = 'buy', recent_days: int = 5) -> List[Dict]:
    """
    Filters stocks based on generated signals within recent days, including stock name and industry.

    Args:
        data_dict (Dict[str, pd.DataFrame]): Dictionary of stock codes to their DataFrames with signals.
        stock_names_map (Dict[str, str]): Map from stock code to stock name.
        stock_industry_map (Dict[str, str]): Map from stock code to stock industry.
        signal_type (str): Type of signal to filter ('buy' or 'sell').
        recent_days (int): Look back for signals within this many recent days.

    Returns:
        List[Dict]: A list of dictionaries, each containing 'stock_code', 'stock_name', 'industry', 'signal_date', 'signal_type'.
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
                        'stock_name': stock_names_map.get(stock_code, '未知名称'),
                        'industry': stock_industry_map.get(stock_code, '未知行业'),
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
    universe_data = get_stock_universe() # This now returns List[Dict]
    stock_names_map = {item['代码']: item['名称'] for item in universe_data}
    stock_industry_map = {item['代码']: item.get('所属行业', '未知') for item in universe_data}

    # 2. Batch get data
    # Need to pass just stock codes to batch_get_stock_daily
    stock_codes = [item['代码'] for item in universe_data]
    all_data = batch_get_stock_daily(stock_codes, test_start_date, test_end_date)

    # 3. Batch apply strategy
    processed_all_data = batch_apply_strategy(all_data)

    # 4. Filter signals
    buy_signals = filter_signals(processed_all_data, stock_names_map, stock_industry_map, signal_type='buy', recent_days=10)
    sell_signals = filter_signals(processed_all_data, stock_names_map, stock_industry_map, signal_type='sell', recent_days=10)

    print("\n--- 筛选结果预览 ---")
    print("买入信号:", buy_signals)
    print("卖出信号:", sell_signals)

    if not buy_signals and not sell_signals:
        print("未找到任何买入或卖出信号。")
    print("\n--- screening_handler 模块测试结束 ---")
