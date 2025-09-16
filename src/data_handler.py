# -*- coding: utf-8 -*-

"""
Data handling module for fetching and processing stock data.
"""

import akshare as ak
import pandas as pd
from datetime import datetime

def get_stock_daily(stock_code: str, start_date: str = "20230101", end_date: str = None) -> pd.DataFrame:
    """
    获取指定股票代码的日线行情数据。

    Args:
        stock_code (str): 股票代码 (e.g., "600519").
        start_date (str): 开始日期 (format: "YYYYMMDD").
        end_date (str): 结束日期 (format: "YYYYMMDD"). Defaults to today.

    Returns:
        pd.DataFrame: 包含日线数据的DataFrame，如果获取失败则返回空的DataFrame。
                      列名: [open, high, low, close, volume, ...]
    """
    if end_date is None:
        end_date = datetime.now().strftime("%Y%m%d")
        
    try:
        # print(f"正在从AkShare获取股票 {stock_code} 从 {start_date} 到 {end_date} 的数据...")
        stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol=stock_code, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")
        
        if stock_zh_a_hist_df.empty:
            print(f"警告: 未能获取到股票 {stock_code} 的数据，可能代码有误或该时段无数据。")
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
        
        # print(f"成功获取并处理了 {len(stock_zh_a_hist_df)} 条数据。")
        return stock_zh_a_hist_df

    except Exception as e:
        print(f"获取股票 {stock_code} 数据时发生错误: {e}")
        return pd.DataFrame()
