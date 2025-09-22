# -*- coding: utf-8 -*-
import pandas as pd
from collections import defaultdict

# Import the function to be tested
from src.data_handler import get_stock_universe

def analyze_universe_data():
    """
    Loads the stock universe and analyzes the industry distribution.
    """
    print("--- 开始测试行业数据结构 ---")
    
    # 1. Load the stock universe data
    print("正在加载股票池数据 (将使用缓存)...")
    try:
        universe_data = get_stock_universe(force_refresh=False)
        if not universe_data:
            print("错误：未能加载股票池数据。")
            return
        print(f"成功加载 {len(universe_data)} 条股票记录。")
    except Exception as e:
        print(f"加载股票池时发生错误: {e}")
        return

    # 2. Group stocks by industry
    print("\n--- 按行业对股票进行分组和计数 ---")
    industry_groups = defaultdict(list)
    for stock in universe_data:
        industry = stock.get('所属行业', '行业未知')
        industry_groups[industry].append(stock)

    if not industry_groups:
        print("错误：未能将任何股票归类到行业中。")
        return

    # 3. Print the analysis
    print(f"共找到 {len(industry_groups)} 个不同的行业板块。")
    print("-" * 30)
    for industry, stocks in sorted(industry_groups.items()):
        print(f'行业: "{industry}" - 包含股票数: {len(stocks)}')
    print("-" * 30)

    # 4. Print samples for verification
    print("\n--- 抽样检查部分行业的股票数据 ---")
    
    # Sample 1: Pick a specific industry if it exists
    sample_industry_1 = "贵金属"
    if sample_industry_1 in industry_groups:
        print(f'\n抽样行业: "{sample_industry_1}" (前3只股票)')
        for stock in industry_groups[sample_industry_1][:3]:
            print(f"  - {stock}")

    # Sample 2: Pick another specific industry
    sample_industry_2 = "软件开发"
    if sample_industry_2 in industry_groups:
        print(f'\n抽样行业: "{sample_industry_2}" (前3只股票)')
        for stock in industry_groups[sample_industry_2][:3]:
            print(f"  - {stock}")
            
    # Sample 3: Check for unknown industry
    if "行业未知" in industry_groups:
        print(f'\n警告: 存在未归类行业的股票，共 {len(industry_groups["行业未知"])} 只')
        print("抽样 '行业未知' 的股票 (前3只):")
        for stock in industry_groups['行业未知'][:3]:
            print(f"  - {stock}")

    print("\n--- 测试结束 ---")


if __name__ == "__main__":
    analyze_universe_data()
