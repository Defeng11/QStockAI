# -*- coding: utf-8 -*-

import akshare as ak
import pandas as pd

print(f"AkShare 版本: {ak.__version__}")

try:
    print("\n--- 正在测试 ak.sw_index_third_cons()，超时设置为30秒 ---")
    df = ak.sw_index_third_cons()
    print("调用成功！")
    print("\n列名:")
    print(df.columns)
    print("\n前5行数据:")
    print(df.head())
except Exception as e:
    print(f"\n调用 ak.sw_index_cons() 时发生错误: {e}")
    print("这可能是由于网络问题、API接口暂时不可用或akshare版本问题导致的。")

