# -*- coding: utf-8 -*-

"""
Unit tests for the data_handler module.
"""

import pandas as pd
import pytest

from src.data_handler import get_stock_daily


def test_get_stock_daily_valid_code():
    """Tests if get_stock_daily returns a DataFrame for a valid stock code."""
    # Use a well-known stock code that is unlikely to be delisted, like Ping An Bank
    df = get_stock_daily(stock_code="000001", start_date="20240101", end_date="20240110")
    
    # Assert that the result is a pandas DataFrame
    assert isinstance(df, pd.DataFrame)
    
    # Assert that the DataFrame is not empty
    assert not df.empty
    
    # Assert that essential columns are present
    expected_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
    assert all(col in df.columns for col in expected_columns)

def test_get_stock_daily_invalid_code():
    """Tests if get_stock_daily returns an empty DataFrame for an invalid stock code."""
    # Use a stock code that is syntactically valid but does not exist
    df = get_stock_daily(stock_code="999999", start_date="20240101", end_date="20240110")
    
    # Assert that the result is a pandas DataFrame
    assert isinstance(df, pd.DataFrame)
    
    # Assert that the DataFrame is empty
    assert df.empty
