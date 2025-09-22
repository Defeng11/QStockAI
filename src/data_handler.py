# -*- coding: utf-8 -*- 

"""
Data handling module for fetching and processing stock data.
"""

import akshare as ak
import pandas as pd
from datetime import datetime, timedelta
import struct # For binary parsing
import os     # For path manipulation
import json
import time
from typing import List, Dict

# --- Constants ---

# Define the root path for Tongdaxin data
TDX_ROOT_PATH = "D:\\new_tdx\\"

# Define cache directory and file for stock universe
CACHE_DIR = "cache"
UNIVERSE_CACHE_FILE = os.path.join(CACHE_DIR, "stock_universe_cache.json")
CACHE_EXPIRATION_HOURS = 24 # Cache universe for 24 hours


# --- Helper Functions ---

def _read_tdx_day_file(file_path: str) -> pd.DataFrame:
    """
    Reads a Tongdaxin .day binary file and returns a pandas DataFrame.
    Each record is 32 bytes.
    """
    records = []
    try:
        with open(file_path, 'rb') as f:
            while True:
                record_bytes = f.read(32)
                if len(record_bytes) < 32:
                    break
                date_int, open_int, high_int, low_int, close_int, amount_float, volume_int, _ = struct.unpack('<IIIIIfII', record_bytes)
                
                date = pd.to_datetime(str(date_int), format='%Y%m%d')
                open_price = open_int / 100.0
                high_price = high_int / 100.0
                low_price = low_int / 100.0
                close_price = close_int / 100.0
                volume = volume_int
                amount = amount_float

                records.append({
                    'date': date,
                    'open': open_price,
                    'high': high_price,
                    'low': low_price,
                    'close': close_price,
                    'volume': volume,
                    'amount': amount
                })
        df = pd.DataFrame(records)
        return df
    except Exception as e:
        print(f"读取通达信本地文件 {file_path} 时发生错误: {e}")
        return pd.DataFrame()


# --- Main Data Functions ---

def get_stock_daily(stock_code: str, start_date: str = "20230101", end_date: str = None) -> pd.DataFrame:
    """
    获取指定股票代码的日线行情数据。
    优先从本地通达信数据读取，如果失败则回退到AkShare。
    """
    if end_date is None:
        end_date = datetime.now().strftime("%Y%m%d")
    
    # 1. Try to read from local Tongdaxin data
    try:
        market_prefix = ""
        if stock_code.startswith(('60', '68', '90')):
            market_prefix = "sh"
        elif stock_code.startswith(('00', '30', '20')):
            market_prefix = "sz"
        
        if market_prefix:
            tdx_file_path = os.path.join(TDX_ROOT_PATH, "vipdoc", market_prefix, "lday", f"{market_prefix}{stock_code}.day")
            if os.path.exists(tdx_file_path):
                tdx_data_df = _read_tdx_day_file(tdx_file_path)
                if not tdx_data_df.empty:
                    tdx_data_df['date'] = pd.to_datetime(tdx_data_df['date'])
                    tdx_data_df = tdx_data_df[(tdx_data_df['date'] >= pd.to_datetime(start_date)) & 
                                              (tdx_data_df['date'] <= pd.to_datetime(end_date))]
                    print(f"成功从本地通达信获取 {stock_code} 的 {len(tdx_data_df)} 条数据。")
                    return tdx_data_df
    except Exception as e:
        print(f"读取本地通达信数据时发生错误: {e}。将回退到AkShare。")
        
    # 2. Fallback to AkShare
    print(f"正在从AkShare获取股票 {stock_code} 从 {start_date} 到 {end_date} 的数据...")
    try:
        stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol=stock_code, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")
        
        if stock_zh_a_hist_df.empty:
            print(f"警告: 未能从AkShare获取到股票 {stock_code} 的数据。")
            return pd.DataFrame()
            
        stock_zh_a_hist_df.rename(columns={
            '日期': 'date', '开盘': 'open', '收盘': 'close', '最高': 'high', '最低': 'low',
            '成交量': 'volume', '成交额': 'amount', '振幅': 'amplitude', '涨跌幅': 'pct_chg',
            '涨跌额': 'change', '换手率': 'turnover'
        }, inplace=True)
        
        stock_zh_a_hist_df['date'] = pd.to_datetime(stock_zh_a_hist_df['date'])
        print(f"成功从AkShare获取并处理了 {len(stock_zh_a_hist_df)} 条数据。")
        return stock_zh_a_hist_df

    except Exception as e:
        print(f"从AkShare获取股票 {stock_code} 数据时发生错误: {e}")
        return pd.DataFrame()

def get_stock_universe(force_refresh: bool = False) -> List[Dict]:
    """
    获取完整的A股股票池，包含代码、名称和所属行业。
    数据会被缓存24小时以提高性能。

    Args:
        force_refresh (bool): 如果为True，则强制从数据源刷新，忽略现有缓存。

    Returns:
        List[Dict]: 一个包含股票信息的字典列表。
                     示例: [{'代码': '000001', '名称': '平安银行', '所属行业': '银行'}]
    """
    print("正在获取股票池 (代码、名称、行业)...")
    
    os.makedirs(CACHE_DIR, exist_ok=True)

    if not force_refresh and os.path.exists(UNIVERSE_CACHE_FILE):
        last_modified_timestamp = os.path.getmtime(UNIVERSE_CACHE_FILE)
        last_modified_datetime = datetime.fromtimestamp(last_modified_timestamp)
        
        if datetime.now() - last_modified_datetime < timedelta(hours=CACHE_EXPIRATION_HOURS):
            print("从缓存加载股票池...")
            with open(UNIVERSE_CACHE_FILE, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
            stock_data = cache_data['data']
            print(f"已从缓存获取 {len(stock_data)} 只股票。")
            return stock_data

    print("从数据源获取股票池并更新缓存...")
    stock_data = []
    try:
        # --- 主方案: 获取东方财富所有行业及其成分股 ---
        industry_summary_df = ak.stock_board_industry_name_em()
        
        if industry_summary_df.empty or '板块名称' not in industry_summary_df.columns:
            raise ValueError("AkShare stock_board_industry_name_em() 返回数据无效")

        total_industries = len(industry_summary_df)
        for i, row in industry_summary_df.iterrows():
            industry_name = row['板块名称']
            print(f"  正在获取行业 '{industry_name}' 的股票 ({i+1}/{total_industries})...")
            try:
                cons_df = ak.stock_board_industry_cons_em(symbol=industry_name)
                if not cons_df.empty and '代码' in cons_df.columns and '名称' in cons_df.columns:
                    for _, stock_row in cons_df.iterrows():
                        stock_code_clean = str(stock_row['代码']).split('.')[0]
                        stock_data.append({
                            '代码': stock_code_clean,
                            '名称': stock_row['名称'],
                            '所属行业': industry_name
                        })
                else:
                    print(f"    警告: 行业 '{industry_name}' 未获取到股票数据。")
            except Exception as e:
                print(f"    获取行业 '{industry_name}' 股票时出错: {e}")
            time.sleep(1)

        if not stock_data:
            raise ValueError("未能从东方财富行业板块获取任何股票数据")

        stock_df_final = pd.DataFrame(stock_data).drop_duplicates(subset=['代码'])
        stock_data = stock_df_final.to_dict(orient='records')
        print(f"已从AkShare (东方财富) 获取 {len(stock_data)} 只股票。")
        
    except Exception as e:
        print(f"从AkShare (东方财富) 获取股票池时发生错误: {e}。将尝试备用接口。")
        stock_data = []

        # --- 备用方案: 获取所有A股代码和名称，行业设为'未知' ---
        try:
            stock_info_df = ak.stock_info_a_code_name()
            if not stock_info_df.empty:
                stock_info_df.rename(columns={'code': '代码', 'name': '名称'}, inplace=True)
                for _, row in stock_info_df.iterrows():
                    stock_code_clean = str(row['代码']).split('.')[0]
                    stock_data.append({
                        '代码': stock_code_clean,
                        '名称': row['名称'],
                        '所属行业': '未知'
                    })
                print(f"已从AkShare (备用接口) 获取 {len(stock_data)} 只股票。")
        except Exception as e_fallback:
            print(f"从AkShare (备用接口) 获取股票池时发生错误: {e_fallback}。")
            stock_data = []

    if not stock_data:
        print("未能从任何数据源获取到股票数据。")
        return []

    cache_data = {'date': datetime.now().isoformat(), 'data': stock_data}
    with open(UNIVERSE_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=4)
    
    return stock_data