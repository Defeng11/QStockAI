# -*- coding: utf-8 -*-

"""
Handles the implementation of specific trading strategies.
Each function in this module should represent a strategy and return a DataFrame
with a 'signal' column.
"""

import pandas as pd
import numpy as np

def apply_oversold_reversal_strategy(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies the "Oversold Reversal Combo" strategy.
    A buy signal is generated when RSI, Bollinger Bands, and Stochastic (KD)
    all indicate an oversold condition turning upwards.

    Args:
        df (pd.DataFrame): DataFrame with pre-calculated technical indicators.

    Returns:
        pd.DataFrame: The original DataFrame with an added 'signal' column.
                      Signal: 1 for buy, 0 for hold/no signal.
    """
    print("  - 应用“超卖反弹组合”策略...")
    df_strat = df.copy()
    
    # Define the conditions based on the provided strategy document
    # Condition 1: RSI is in oversold territory
    cond_rsi = df_strat['rsi'] < 25
    
    # Condition 2: Price touches or goes below the lower Bollinger Band
    # Ensure bbands_lower exists and is not NaN
    cond_bbands = (df_strat['bbands_lower'].notna()) & (df_strat['close'] <= df_strat['bbands_lower'])
    
    # Condition 3: Stochastic K line crosses above D line in the oversold area
    # Ensure k and d exist and are not NaN
    cond_kd_oversold = (df_strat['k'].notna()) & (df_strat['d'].notna()) & (df_strat['k'] < 20) & (df_strat['d'] < 20)
    cond_kd_cross = (df_strat['k'] > df_strat['d']) & (df_strat['k'].shift(1) < df_strat['d'].shift(1))
    
    # Combine all conditions
    buy_conditions = cond_rsi & cond_bbands & cond_kd_oversold & cond_kd_cross
    
    # Create the signal column
    df_strat['signal'] = np.where(buy_conditions, 1, 0)
    
    signal_points = df_strat[df_strat['signal'] == 1]
    print(f"  - 策略完成，共找到 {len(signal_points)} 个潜在买入信号点。")
    
    return df_strat

# In the future, we can add more strategy functions here, e.g.:
# def apply_momentum_breakout_strategy(df: pd.DataFrame) -> pd.DataFrame:
#     ...
#     return df

def apply_five_step_integrated_strategy(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies the "Five-Step Integrated Trading Strategy".

    This strategy combines macro trends, fundamental screening (assumed to be done
    beforehand in the stock pool), technical triggers, and volume validation.

    Args:
        df (pd.DataFrame): DataFrame with pre-calculated technical indicators.
                           Requires: 'close', 'ma20', 'ma200', 'macd_hist', 'rsi',
                                     'volume'.

    Returns:
        pd.DataFrame: The original DataFrame with an added 'signal' column.
                      Signal: 1 for buy, -1 for sell, 0 for hold.
    """
    print("  - 应用“五步集成交易”策略...")
    df_strat = df.copy()

    # --- Buy Signal Conditions ---

    # 1. Macro Trend Condition (optional, can be checked externally)
    # For this function, we assume the stock is already in a valid macro trend
    # e.g., df_strat['close'] > df_strat['ma200']

    # 2. Technical Trigger Conditions
    # Condition 2a: MACD golden cross (histogram turns from negative to positive)
    cond_macd_cross = (df_strat['macd_hist'] > 0) & (df_strat['macd_hist'].shift(1) <= 0)

    # Condition 2b: RSI rises from the oversold area
    cond_rsi_rise = (df_strat['rsi'] > 30) & (df_strat['rsi'].shift(1) <= 30)
    
    # Condition 2c: Price is above the 20-day moving average
    cond_ma20 = df_strat['close'] > df_strat['ma20']

    # Combine technical trigger conditions
    cond_tech_trigger = cond_macd_cross & cond_rsi_rise & cond_ma20

    # 3. Volume Validation Condition
    # Calculate 20-day average volume
    avg_volume_20 = df_strat['volume'].rolling(window=20).mean()
    # Condition 3a: Volume is 1.5x greater than the 20-day average
    cond_volume = df_strat['volume'] > (avg_volume_20 * 1.5)

    # Final Buy Condition
    buy_conditions = cond_tech_trigger & cond_volume

    # --- Sell Signal Conditions ---

    # Condition: MACD death cross (histogram turns from positive to negative)
    sell_conditions = (df_strat['macd_hist'] < 0) & (df_strat['macd_hist'].shift(1) >= 0)

    # --- Generate Signals ---
    df_strat['signal'] = 0  # Default to hold
    df_strat.loc[buy_conditions, 'signal'] = 1
    df_strat.loc[sell_conditions, 'signal'] = -1
    
    buy_points = df_strat[df_strat['signal'] == 1]
    sell_points = df_strat[df_strat['signal'] == -1]
    print(f"  - 策略完成，共找到 {len(buy_points)} 个买入信号和 {len(sell_points)} 个卖出信号。")

    return df_strat
