# -*- coding: utf-8 -*- 

"""
Unit tests for the strategy_handler module.
"""

import pandas as pd
import numpy as np
import pytest

# Add src to the path to allow direct import of our modules
from src.strategy_handler import apply_oversold_reversal_strategy

@pytest.fixture
def mock_analyzed_data():
    """Creates a mock DataFrame that simulates data with indicators."""
    data = {
        'date': pd.to_datetime(pd.date_range(start='2024-01-01', periods=5)),
        # Use floats for price data and set the specific value for the test case
        'close': [10.0, 11.0, 11.5, 13.0, 14.0],
        # RSI values: normal, oversold, oversold, normal, normal
        'rsi': [50, 24, 20, 35, 40],
        # BBands: normal, price touches lower, price inside, price inside, price inside
        'bbands_lower': [9.0, 11.0, 11.5, 12.0, 13.0],
        # KD: no cross, no cross, K crosses D in oversold, no cross, no cross
        'k': [25, 18, 19, 22, 25],
        'd': [28, 20, 18, 21, 24],
    }
    return pd.DataFrame(data)

def test_apply_oversold_reversal_strategy(mock_analyzed_data):
    """Tests that the strategy correctly identifies a buy signal."""
    df = mock_analyzed_data
    # The mock data is now pre-configured to trigger a signal at index 2
    df_with_signals = apply_oversold_reversal_strategy(df)

    # Check that the 'signal' column is added
    assert 'signal' in df_with_signals.columns
    
    expected_signals = [0, 0, 1, 0, 0]
    actual_signals = df_with_signals['signal'].tolist()
    
    assert actual_signals == expected_signals, \
        f"Expected signals {expected_signals} but got {actual_signals}"


def test_strategy_with_no_signals(mock_analyzed_data):
    """Tests that the strategy returns no signals if conditions are not met."""
    df = mock_analyzed_data
    # Modify data so no signal should be generated
    df['rsi'] = 50 # Set all RSI values to be normal
    
    df_with_signals = apply_oversold_reversal_strategy(df)
    
    # Assert that no buy signals (1) are present
    assert 1 not in df_with_signals['signal'].tolist()
