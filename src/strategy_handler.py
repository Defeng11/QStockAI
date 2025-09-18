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
    cond_bbands = df_strat['close'] <= df_strat['bbands_lower']
    
    # Condition 3: Stochastic K line crosses above D line in the oversold area
    cond_kd_oversold = (df_strat['k'] < 20) & (df_strat['d'] < 20)
    cond_kd_cross = (df_strat['k'] > df_strat['d']) & (df_strat['k'].shift(1) < df_strat['d'].shift(1))
    
    # Combine all conditions
    buy_conditions = cond_rsi & cond_bbands & cond_kd_oversold & cond_kd_cross
    
    # Create the signal column
    # np.where(condition, value_if_true, value_if_false)
    df_strat['signal'] = np.where(buy_conditions, 1, 0)
    
    signal_points = df_strat[df_strat['signal'] == 1]
    print(f"  - 策略完成，共找到 {len(signal_points)} 个潜在买入信号点。")
    
    return df_strat

# In the future, we can add more strategy functions here, e.g.:
# def apply_momentum_breakout_strategy(df: pd.DataFrame) -> pd.DataFrame:
#     ...
#     return df
