# -*- coding: utf-8 -*-

"""
Unit tests for the analysis_handler module.
"""

import pandas as pd
import numpy as np
import pytest

# Add src to the path to allow direct import of our modules
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.analysis_handler import add_technical_indicators

@pytest.fixture
def sample_stock_data():
    """Creates a sample DataFrame with stock data for testing."""
    # Create a DataFrame with enough data points for TA-Lib to calculate indicators
    # (e.g., MACD needs at least 26 + 9 = 35 periods)
    data = {
        'date': pd.to_datetime(pd.date_range(start='2024-01-01', periods=50)),
        'open': np.random.uniform(98, 102, 50),
        'high': np.random.uniform(100, 105, 50),
        'low': np.random.uniform(95, 100, 50),
        'close': np.linspace(100, 150, 50), # A clear trend to ensure non-trivial indicator values
        'volume': np.random.randint(100000, 500000, 50)
    }
    df = pd.DataFrame(data)
    # Ensure high is always >= close and low is always <= close
    df['high'] = df[['high', 'close']].max(axis=1)
    df['low'] = df[['low', 'close']].min(axis=1)
    return df

def test_add_technical_indicators(sample_stock_data):
    """Tests the main function for adding a list of indicators."""
    df = sample_stock_data
    indicators_to_add = ['rsi', 'macd']
    
    df_analyzed = add_technical_indicators(df, indicators_to_add)
    
    # 1. Check if the new columns are added
    assert 'rsi' in df_analyzed.columns
    assert 'macd' in df_analyzed.columns
    assert 'macdsignal' in df_analyzed.columns
    assert 'macdhist' in df_analyzed.columns
    
    # 2. Check that the new columns are not all empty (NaN)
    # TA-Lib indicators have a startup period where values are NaN, so we check the last value.
    assert not pd.isna(df_analyzed['rsi'].iloc[-1])
    assert not pd.isna(df_analyzed['macd'].iloc[-1])

def test_add_technical_indicators_invalid_indicator(sample_stock_data):
    """Tests that the function handles unknown indicators gracefully."""
    df = sample_stock_data
    # 'bollinger' is a valid indicator, but we haven't registered it yet.
    indicators_to_add = ['rsi', 'bollinger']
    
    df_analyzed = add_technical_indicators(df, indicators_to_add)
    
    # It should add the valid ones and ignore the invalid one
    assert 'rsi' in df_analyzed.columns
    assert 'bollinger' not in df_analyzed.columns # Or however we decide to handle it
