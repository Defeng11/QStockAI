# -*- coding: utf-8 -*-

"""
Unit tests for the analysis_handler module.
"""

import pandas as pd
import numpy as np
import pytest

from src.analysis_handler import add_technical_indicators, get_available_indicators

@pytest.fixture
def sample_stock_data():
    """Creates a sample DataFrame with stock data for testing."""
    data = {
        'date': pd.to_datetime(pd.date_range(start='2024-01-01', periods=50)),
        'open': np.random.uniform(98, 102, 50),
        'high': np.random.uniform(100, 105, 50),
        'low': np.random.uniform(95, 100, 50),
        'close': np.linspace(100, 150, 50),
        'volume': np.random.randint(100000, 500000, 50).astype(float) # Volume needs to be float for talib
    }
    df = pd.DataFrame(data)
    df['high'] = df[['high', 'close']].max(axis=1)
    df['low'] = df[['low', 'close']].min(axis=1)
    return df

def test_get_available_indicators():
    """Tests if the helper function returns the correct list of indicators."""
    indicators = get_available_indicators()
    assert isinstance(indicators, list)
    expected_indicators = ['rsi', 'macd', 'ma', 'kd', 'obv', 'bbands']
    # Use set for order-independent comparison
    assert set(indicators) == set(expected_indicators)

def test_add_all_technical_indicators(sample_stock_data):
    """Tests adding all available indicators to a DataFrame."""
    df = sample_stock_data
    all_indicators = get_available_indicators()
    
    df_analyzed = add_technical_indicators(df, all_indicators)
    
    # Check if all expected columns were added
    assert 'rsi' in df_analyzed.columns
    assert 'macd' in df_analyzed.columns
    assert 'ma20' in df_analyzed.columns  # Default for MA is 20
    assert 'k' in df_analyzed.columns
    assert 'd' in df_analyzed.columns
    assert 'obv' in df_analyzed.columns
    assert 'bbands_upper' in df_analyzed.columns
    
    # Check that the new columns are not all empty (NaN)
    assert not pd.isna(df_analyzed['rsi'].iloc[-1])
    assert not pd.isna(df_analyzed['macd'].iloc[-1])
    assert not pd.isna(df_analyzed['ma20'].iloc[-1])
    assert not pd.isna(df_analyzed['k'].iloc[-1])
    assert not pd.isna(df_analyzed['obv'].iloc[-1])
    assert not pd.isna(df_analyzed['bbands_upper'].iloc[-1])

def test_add_technical_indicators_gracefully_handles_invalid(sample_stock_data):
    """Tests that the function handles unknown indicators gracefully."""
    df = sample_stock_data
    indicators_to_add = ['rsi', 'non_existent_indicator']
    
    df_analyzed = add_technical_indicators(df, indicators_to_add)
    
    # It should add the valid ones and ignore the invalid one
    assert 'rsi' in df_analyzed.columns
    assert 'non_existent_indicator' not in df_analyzed.columns