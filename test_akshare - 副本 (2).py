# -*- coding: utf-8 -*-

import akshare as ak
import pandas as pd
import json
import os
from datetime import datetime, timedelta
from typing import List, Dict

print(f"AkShare 版本: {ak.__version__}")

# Define cache directory and file for this test script
TEST_CACHE_DIR = "test_cache"
TEST_UNIVERSE_CACHE_FILE = os.path.join(TEST_CACHE_DIR, "test_stock_universe_cache.json")
TEST_CACHE_EXPIRATION_HOURS = 0.1 # Very short cache for testing (6 minutes)

def test_get_stock_universe_logic(force_refresh: bool = False) -> List[Dict]:
    """
    Simulates the get_stock_universe logic for testing purposes.
    Fetches a list of all A-share stock codes, names, and industry with caching.
    Returns a list of dictionaries: [{'代码': '000001', '名称': '平安银行', '所属行业': '银行'}]
    """
    print("\n--- 正在测试 get_stock_universe 逻辑 ---")
    print("正在获取股票池 (代码、名称、行业)...")
    
    # Ensure test cache directory exists
    os.makedirs(TEST_CACHE_DIR, exist_ok=True)

    # Check if cache file exists and is fresh
    if not force_refresh and os.path.exists(TEST_UNIVERSE_CACHE_FILE):
        last_modified_timestamp = os.path.getmtime(TEST_UNIVERSE_CACHE_FILE)
        last_modified_datetime = datetime.fromtimestamp(last_modified_timestamp)
        
        if datetime.now() - last_modified_datetime < timedelta(hours=TEST_CACHE_EXPIRATION_HOURS):
            print("从测试缓存加载股票池...")
            with open(TEST_UNIVERSE_CACHE_FILE, "r", encoding="utf-8") as f:
                cache_data = json.load(f)
            stock_data = cache_data['data']
            print(f"已从测试缓存获取 {len(stock_data)} 只股票代码。")
            return stock_data

    print("从数据源获取股票池 (代码、名称、行业) 并更新测试缓存...")
    stock_data = []
    try:
        # --- Primary Attempt: Get industry list from Shenwan and then constituents ---
        print(f"AkShare 版本: {ak.__version__}")
        sw_index_df = ak.sw_index_third_cons()
        
        if sw_index_df.empty:
            print("警告: AkShare sw_index_third_cons() 返回空DataFrame。")
            raise ValueError("Empty Shenwan index constituent data")

        # Rename columns to a standard format
        # Based on previous test, columns are '股票代码', '股票简称', '申万1级', '申万2级', '申万3级'
        sw_index_df.rename(columns={'股票代码': '代码', '股票简称': '名称', '申万1级': '所属行业'}, inplace=True)

        if '代码' in sw_index_df.columns and '名称' in sw_index_df.columns and '所属行业' in sw_index_df.columns:
            processed_stock_data = []
            for item in sw_index_df[['代码', '名称', '所属行业']].to_dict(orient='records'):
                stock_code_raw = item['代码']
                stock_code_clean = stock_code_raw.split('.')[0] # Remove .SH or .SZ suffix
                item['代码'] = stock_code_clean
                processed_stock_data.append(item)
            stock_data = processed_stock_data
            print(f"已从AkShare (申万行业) 获取 {len(stock_data)} 只股票代码。")
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
                # Normalize column names for stock_info_df
                if 'code' in stock_info_df.columns:
                    stock_info_df.rename(columns={'code': '代码'}, inplace=True)
                if 'name' in stock_info_df.columns:
                    stock_info_df.rename(columns={'name': '名称'}, inplace=True)

                if '代码' in stock_info_df.columns and '名称' in stock_info_df.columns:
                    for _, row in stock_info_df.iterrows():
                        stock_data.append({
                            '代码': row['代码'],
                            '名称': row['名称'],
                            '所属行业': '未知' # Set industry to unknown
                        })
                    print(f"已从AkShare (备用接口) 获取 {len(stock_data)} 只股票代码。")
                else:
                    print("警告: AkShare stock_info_a_code_name() 缺少预期列。")
            else:
                print("警告: AkShare stock_info_a_code_name() 返回空DataFrame。")
        except Exception as e_fallback:
            print(f"从AkShare (备用接口) 获取股票池时发生错误: {e_fallback}。")
            stock_data = [] # Ensure empty if fallback also fails

    if not stock_data:
        print("未能从任何数据源获取到任何股票数据。将返回空列表。")
        return []

    # Save to test cache
    cache_data = {'date': datetime.now().isoformat(), 'data': stock_data}
    with open(TEST_UNIVERSE_CACHE_FILE, "w", encoding="utf-8") as f:
        json.dump(cache_data, f, ensure_ascii=False, indent=4)
    
    return stock_data

if __name__ == "__main__":
    # Delete old test cache to force fresh data fetching
    if os.path.exists(TEST_UNIVERSE_CACHE_FILE):
        os.remove(TEST_UNIVERSE_CACHE_FILE)
        print(f"已删除旧的测试缓存文件: {TEST_UNIVERSE_CACHE_FILE}")

    # Run the test logic
    result = test_get_stock_universe_logic(force_refresh=True)
    print("\n--- 测试结果 (前5条数据) ---")
    if result:
        for item in result[:5]:
            print(item)
        print(f"\n总共获取到 {len(result)} 只股票。")
    else:
        print("未能获取到任何股票数据。")