# -*- coding: utf-8 -*-

"""
Handles the core logic for stock screening, including fetching stock universe,
batch data retrieval, and batch strategy application.
"""

import pandas as pd
import time
import os
import json
from datetime import datetime, timedelta
from typing import List, Dict

# Import necessary modules from src
from src.data_handler import get_stock_daily
from src.strategy_handler import apply_five_step_integrated_strategy
import akshare as ak

# Define cache directory and file
CACHE_DIR = "cache"
UNIVERSE_CACHE_FILE = os.path.join(CACHE_DIR, "stock_universe_cache.json")
CACHE_EXPIRATION_HOURS = 24 # Cache expires after 24 hours

def get_stock_universe() -> List[Dict]: # Return list of dicts now
    """
    Fetches a list of all A-share stock codes, names, and industry with caching.
    Returns a list of dictionaries: [{'code': '000001', 'name': '平安银行', 'industry': '银行'}]
    """
    print("正在获取股票池 (代码、名称、行业)...")
    
    # Ensure cache directory exists
    os.makedirs(CACHE_DIR, exist_ok=True)

    # Check if cache file exists and is fresh
    if os.path.exists(UNIVERSE_CACHE_FILE):
        last_modified_timestamp = os.path.getmtime(UNIVERSE_CACHE_FILE)
        last_modified_datetime = datetime.fromtimestamp(last_modified_timestamp)
        
        if datetime.now() - last_modified_datetime < timedelta(hours=CACHE_EXPIRATION_HOURS):
            print("从缓存加载股票池...")
            with open(UNIVERSE_CACHE_FILE, "r", encoding="utf-8") as f:
                stock_data = json.load(f)
            print(f"已从缓存获取 {len(stock_data)} 只股票代码。")
            return stock_data

    print("从数据源获取股票池 (代码、名称、行业) 并更新缓存...")
    try:
        stock_data = []
        # --- Primary Attempt: Get industry list from Shenwan and then constituents ---
        try:
            print(f"AkShare 版本: {ak.__version__}")
            sw_index_df = ak.sw_index_third_cons()
            
            if sw_index_df.empty:
                print("警告: AkShare sw_index_third_cons() 返回空DataFrame。")
                raise ValueError("Empty Shenwan index constituent data")

            # Rename columns to a standard format
            sw_index_df.rename(columns={'stock_code': '代码', 'stock_name': '名称', 'industry_name': '所属行业'}, inplace=True)

            if '代码' in sw_index_df.columns and '名称' in sw_index_df.columns and '所属行业' in sw_index_df.columns:
                stock_data = sw_index_df[['代码', '名称', '所属行业']].to_dict(orient='records')
                print(f"已从AkShare (申万行业) 获取 {len(stock_data)} 只股票代码并更新缓存。")
            else:
                print("警告: AkShare sw_index_third_cons() 缺少预期列。")
                raise ValueError("Missing expected columns in Shenwan index constituent data")
            
        except Exception as e:
            print(f"从AkShare (申万行业) 获取股票池时发生错误: {e}。将尝试备用接口。")
            stock_data = [] # Clear any partial data

            # --- Fallback Attempt: Get all A-share codes and names, set industry to '未知' ---
            try:
                stock_info_df = ak.stock_info_a_code_name()
                if not stock_info_df.empty:
                    if 'code' in stock_info_df.columns and 'name' in stock_info_df.columns:
                        for _, row in stock_info_df.iterrows():
                            stock_data.append({
                                '代码': row['code'],
                                '名称': row['name'],
                                '所属行业': '未知' # Set industry to unknown
                            })
                        print(f"已从AkShare (备用接口) 获取 {len(stock_data)} 只股票代码并更新缓存。")
                    else:
                        print("警告: AkShare stock_info_a_code_name() 缺少预期列。")
                else:
                    print("警告: AkShare stock_info_a_code_name() 返回空DataFrame。")
            except Exception as e_fallback:
                print(f"从AkShare (备用接口) 获取股票池时发生错误: {e_fallback}。")
                stock_data = [] # Ensure empty if fallback also fails

        if not stock_data:
            print("未能从AkShare获取到任何股票数据。将返回空列表。
")
            return []

        # Save to cache
        with open(UNIVERSE_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(stock_data, f, ensure_ascii=False, indent=4)
        
        return stock_data
    except Exception as e:
        print(f"获取股票池时发生错误: {e}。将返回空列表。")
        return []


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
    total_stocks = len(stock_list)
    print(f"正在批量获取 {total_stocks} 只股票的历史数据...")
    all_stock_data = {}
    for i, stock_code in enumerate(stock_list):
        # Calculate progress percentage
        progress_percent = int(((i + 1) / total_stocks) * 100)
        print(f"PROGRESS_BATCH_GET_DATA:{progress_percent}") # Progress indicator for workflow
        
        print(f"  获取 {stock_code} 数据 ({i+1}/{total_stocks})... ")
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
    total_stocks = len(data_dict)
    print("正在批量应用策略...")
    processed_data = {}
    for i, (stock_code, df) in enumerate(data_dict.items()):
        # Calculate progress percentage
        progress_percent = int(((i + 1) / total_stocks) * 100)
        print(f"PROGRESS_BATCH_APPLY_STRATEGY:{progress_percent}") # Progress indicator for workflow

        if not df.empty:
            print(f"  对 {stock_code} 应用策略 ({i+1}/{total_stocks})... ")
            try:
                df_with_signals = apply_five_step_integrated_strategy(df)
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
