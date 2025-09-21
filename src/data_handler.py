# -*- coding: utf-8 -*-

"""
Data handling module for fetching and processing stock data.
"""

import akshare as ak
import pandas as pd
from datetime import datetime
import struct # For binary parsing
import os     # For path manipulation

# Define the root path for Tongdaxin data
TDX_ROOT_PATH = "D:\\new_tdx\\"

# Helper function to read TDX .day files
def _read_tdx_day_file(file_path: str) -> pd.DataFrame:
    """
    Reads a Tongdaxin .day binary file and returns a pandas DataFrame.
    Each record is 32 bytes:
    Date (4 bytes, int)
    Open (4 bytes, int) * 100
    High (4 bytes, int) * 100
    Low (4 bytes, int) * 100
    Close (4 bytes, int) * 100
    Amount (4 bytes, float)
    Volume (4 bytes, int)
    Reserved (4 bytes)
    """
    records = []
    try:
        with open(file_path, 'rb') as f:
            while True:
                record_bytes = f.read(32)
                if len(record_bytes) < 32:
                    break
                # Use '<IIIIIfII' for little-endian unsigned int (I), float (f)
                # Note: Amount is float in TDX, others are int * 100
                date_int, open_int, high_int, low_int, close_int, amount_float, volume_int, _ = struct.unpack('<IIIIIfII', record_bytes)
                
                date = pd.to_datetime(str(date_int), format='%Y%m%d')
                open_price = open_int / 100.0
                high_price = high_int / 100.0
                low_price = low_int / 100.0
                close_price = close_int / 100.0
                volume = volume_int # Volume is already in shares
                amount = amount_float # Amount is already in yuan

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
        # Filter by date range if needed later, or handle in get_stock_daily
        return df
    except Exception as e:
        print(f"读取通达信本地文件 {file_path} 时发生错误: {e}")
        return pd.DataFrame()


def get_stock_daily(stock_code: str, start_date: str = "20230101", end_date: str = None) -> pd.DataFrame:
    """
    获取指定股票代码的日线行情数据。
    优先从本地通达信数据读取，如果失败则回退到AkShare。

    Args:
        stock_code (str): 股票代码 (e.g., "600519").
        start_date (str): 开始日期 (format: "YYYYMMDD").
        end_date (str): 结束日期 (format: "YYYYMMDD"). Defaults to today.

    Returns:
        pd.DataFrame: 包含日线数据的DataFrame，如果获取失败则返回空的DataFrame。
                      列名: [date, open, high, low, close, volume, amount]
    """
    if end_date is None:
        end_date = datetime.now().strftime("%Y%m%d")
    
    # 1. Try to read from local Tongdaxin data
    tdx_data_df = pd.DataFrame()
    try:
        market_prefix = ""
        if stock_code.startswith(('60', '68', '90')): # Shanghai stocks
            market_prefix = "sh"
        elif stock_code.startswith(('00', '30', '20')): # Shenzhen stocks
            market_prefix = "sz"
        
        if market_prefix:
            tdx_file_path = os.path.join(TDX_ROOT_PATH, "vipdoc", market_prefix, "lday", f"{market_prefix}{stock_code}.day")
            print(f"尝试从本地通达信文件读取: {tdx_file_path}")
            if os.path.exists(tdx_file_path):
                tdx_data_df = _read_tdx_day_file(tdx_file_path)
                if not tdx_data_df.empty:
                    # Filter by date range
                    tdx_data_df['date'] = pd.to_datetime(tdx_data_df['date'])
                    tdx_data_df = tdx_data_df[(tdx_data_df['date'] >= pd.to_datetime(start_date)) & 
                                              (tdx_data_df['date'] <= pd.to_datetime(end_date))]
                    print(f"成功从本地通达信获取 {len(tdx_data_df)} 条数据。")
                    return tdx_data_df
                else:
                    print("本地通达信文件为空或解析失败。")
            else:
                print("本地通达信文件不存在。")
        else:
            print(f"警告: 无法判断股票代码 {stock_code} 的市场类型，跳过本地通达信数据读取。")

    except Exception as e:
        print(f"读取本地通达信数据时发生错误: {e}。将回退到AkShare。")
        
    # 2. Fallback to AkShare if local data is not available or fails
    print(f"正在从AkShare获取股票 {stock_code} 从 {start_date} 到 {end_date} 的数据...")
    try:
        stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol=stock_code, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")
        
        if stock_zh_a_hist_df.empty:
            print(f"警告: 未能从AkShare获取到股票 {stock_code} 的数据，可能代码有误或该时段无数据。")
            return pd.DataFrame()
            
        # AkShare返回的列名是中文，统一为英文
        stock_zh_a_hist_df.rename(columns={
            '日期': 'date',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume',
            '成交额': 'amount',
            '振幅': 'amplitude',
            '涨跌幅': 'pct_chg',
            '涨跌额': 'change',
            '换手率': 'turnover'
        }, inplace=True)
        
        # 将date列转为datetime对象
        stock_zh_a_hist_df['date'] = pd.to_datetime(stock_zh_a_hist_df['date'])
        
        print(f"成功从AkShare获取并处理了 {len(stock_zh_a_hist_df)} 条数据。")
        return stock_zh_a_hist_df

    except Exception as e:
        print(f"从AkShare获取股票 {stock_code} 数据时发生错误: {e}")
        return pd.DataFrame()
