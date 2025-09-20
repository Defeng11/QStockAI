import akshare as ak
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import talib

# 用户填写部分（请手动填写以下内容）
# --------------------------------------
stock_code = "600392"  # 股票代码（A股6位代码，如"301183" 东田微）
industry_name = "小金属"  # 行业名称（同花顺/申万分类，如"半导体"、"电子元件"，运行 `python -c "import akshare as ak; print(ak.stock_board_industry_name_ths()['name'])"` 查看列表）
expected_growth_rate = 53.74  # 预期年盈利增长率（%，PEG计算用，参考东方财富研报，东田微预测101.79%）
days = 60  # 技术指标数据天数（短线60，中线100）
# --------------------------------------

# 获取行业PB中位数（自动）
try:
    industry_data = ak.stock_board_industry_name_ths()  # 移除 symbol 参数
    industry_pb = 8.0  # 默认值（半导体行业参考）
    if industry_name in industry_data['name'].values:
        industry_pb = industry_data[industry_data['name'] == industry_name]['pb_median'].iloc[0]
        print(f"查询到 {industry_name} 行业PB中位数: {industry_pb:.2f}")
    else:
        print(f"行业 {industry_name} 未找到，使用默认PB中位数: {industry_pb:.2f}")
except Exception as e:
    print(f"行业数据查询失败: {e}，使用默认PB中位数: {industry_pb:.2f}")

# 获取股票基本信息（自动）
try:
    stock_info = ak.stock_individual_info_em(symbol=stock_code)
    if not stock_info.empty and "item" in stock_info.columns:
        current_price = stock_info.loc[stock_info["item"] == "最新价", "value"].iloc[0] if "最新价" in stock_info["item"].values else None
        pe_ttm = stock_info.loc[stock_info["item"] == "市盈率-动态", "value"].iloc[0] if "市盈率-动态" in stock_info["item"].values else None
        pb = stock_info.loc[stock_info["item"] == "市净率", "value"].iloc[0] if "市净率" in stock_info["item"].values else None
        print(f"获取基本信息成功: 价格={current_price}, PE={pe_ttm}, PB={pb}")
    else:
        raise ValueError("股票基本信息数据为空")
except Exception as e:
    print(f"获取基本信息失败: {e}，请检查股票代码或网络连接")
    current_price, pe_ttm, pb = None, None, None

# 获取财务数据（自动）
try:
    financials = ak.stock_financial_analysis_indicator(symbol=stock_code)
    eps = financials["basic_eps"].iloc[0] if "basic_eps" in financials.columns else 'N/A'
    roe = financials["roe"].iloc[0] if "roe" in financials.columns else 'N/A'
    bvps = financials["per_net_assets"].iloc[0] if "per_net_assets" in financials.columns else 'N/A'
    # 股息数据
    dividend_data = ak.stock_dividend_cninfo(symbol=stock_code)
    latest_dividend = dividend_data["每股股息(税前)"].iloc[0] if not dividend_data.empty and "每股股息(税前)" in dividend_data.columns else 0
    dividend_yield = (latest_dividend / current_price) * 100 if current_price else 'N/A'
    # 计算历史EPS增长率（自动）
    if 'basic_eps' in financials.columns and len(financials) >= 2:
        eps_current = financials["basic_eps"].iloc[0]
        eps_prev = financials["basic_eps"].iloc[1]
        historical_growth = ((eps_current / eps_prev) - 1) * 100 if eps_prev != 0 else 0
        print(f"历史1年EPS增长率: {historical_growth:.2f}% (可参考填写expected_growth_rate)")
    else:
        historical_growth = None
        print("无法计算历史增长率：数据不足，建议查东方财富研报（东田微预测101.79%）")
except Exception as e:
    print(f"获取财务数据失败: {e}")
    eps, roe, bvps, dividend_yield, historical_growth = 'N/A', 'N/A', 'N/A', 'N/A', None

# 计算PEG和PB估值合理价（自动）
peg = pe_ttm / expected_growth_rate if pe_ttm != 'N/A' and expected_growth_rate else 'N/A'
pb_value = bvps * industry_pb if bvps != 'N/A' else 'N/A'

# 获取历史数据（技术指标，自动）
end_date = datetime.now().strftime("%Y%m%d")
start_date = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
data = ak.stock_zh_a_hist(symbol=stock_code, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")
data = data[["日期", "开盘", "最高", "最低", "收盘", "成交量"]].copy()
data.columns = ["Date", "Open", "High", "Low", "Close", "Volume"]

# 计算技术指标（自动）
data["macd"], data["macd_signal"], _ = talib.MACD(data["Close"], fastperiod=12, slowperiod=26, signalperiod=9)
data["rsi"] = talib.RSI(data["Close"], timeperiod=14)
data["volume_ma20"] = data["Volume"].rolling(window=20).mean()
data["sma50"] = data["Close"].rolling(window=50).mean()

# 买入/卖出信号（自动）
data["buy_signal"] = (data["macd"] > data["macd_signal"]) & (data["macd"].shift(1) <= data["macd_signal"].shift(1)) & \
                     (data["rsi"] < 30) & (data["Volume"] > 1.5 * data["volume_ma20"]) & \
                     (data["Close"] > data["sma50"])
data["sell_signal"] = (data["macd"] < data["macd_signal"]) & (data["macd"].shift(1) >= data["macd_signal"].shift(1)) & \
                      (data["rsi"] > 70) & (data["Volume"] < 0.8 * data["volume_ma20"])

# 判断估值高低（自动）
def judge_valuation(current_price, pe_ttm, pb, peg, roe, dividend_yield, pb_value):
    judgments = []
    if pe_ttm != 'N/A':
        if pe_ttm < 50:
            judgments.append("PE偏低（低估）")
        elif pe_ttm > 80:
            judgments.append("PE偏高（高估）")
        else:
            judgments.append("PE中性")
    if pb != 'N/A':
        if pb < industry_pb:
            judgments.append("PB偏低（低估）")
        elif pb > industry_pb * 1.2:
            judgments.append("PB偏高（高估）")
    if peg != 'N/A':
        if peg < 1:
            judgments.append("PEG低估（增长好）")
        elif peg > 1.5:
            judgments.append("PEG高估")
    if roe != 'N/A' and roe > 15:
        judgments.append("ROE优质")
    if dividend_yield != 'N/A' and dividend_yield > 2:
        judgments.append("股息率吸引")
    if pb_value != 'N/A' and current_price:
        if current_price < pb_value:
            judgments.append(f"PB估值低估（当前价{current_price:.2f} < 合理价{pb_value:.2f}）")
        else:
            judgments.append(f"PB估值高估（当前价{current_price:.2f} > 合理价{pb_value:.2f}）")
    return judgments if judgments else ["中性估值"]

# 输出结果
print(f"\n股票: {stock_code}")
print(f"行业: {industry_name}, PB中位数: {industry_pb:.2f}")
print(f"当前价格: {current_price if current_price else 'N/A'}")
print(f"PE (TTM): {pe_ttm if pe_ttm else 'N/A'}")
print(f"PB: {pb if pb else 'N/A'}")
print(f"PEG (假设增长率 {expected_growth_rate}%): {peg if peg != 'N/A' else 'N/A'}")
print(f"ROE: {roe if roe != 'N/A' else 'N/A'}%")
print(f"EPS: {eps if eps != 'N/A' else 'N/A'}")
print(f"每股净资产: {bvps if bvps != 'N/A' else 'N/A'}")
print(f"股息率: {dividend_yield if dividend_yield != 'N/A' else 'N/A'}%")
print(f"PB估值合理价: {pb_value if pb_value != 'N/A' else 'N/A'}")
print("估值判断: " + " | ".join(judge_valuation(current_price, pe_ttm, pb, peg, roe, dividend_yield, pb_value)))
print("\n买入信号（最近5个）：")
print(data[data["buy_signal"]][["Date", "Close"]].tail())
print("\n卖出信号（最近5个）：")
print(data[data["sell_signal"]][["Date", "Close"]].tail())