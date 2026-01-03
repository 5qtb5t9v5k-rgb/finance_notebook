"""Module for data cleaning, deduplication, and filtering."""

import pandas as pd
from typing import Optional
from .config import (
    EXCLUDE_CURRENCIES,
    EXCLUDE_CARD_LAST4,
    DEFAULT_START_DATE
)


def convert_date_column(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert date column to datetime format.
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with converted date column
    """
    df = df.copy()
    
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"])
    
    return df


def filter_by_date(df: pd.DataFrame, start_date: Optional[str] = None) -> pd.DataFrame:
    """
    Filter DataFrame by date range.
    
    Args:
        df: Input DataFrame
        start_date: Start date string (YYYY-MM-DD format). If None, uses DEFAULT_START_DATE
        
    Returns:
        Filtered DataFrame
    """
    df = df.copy()
    
    if "date" not in df.columns:
        return df
    
    if start_date is None:
        start_date = DEFAULT_START_DATE
    
    df = df.loc[df['date'] >= start_date]
    
    return df


def remove_duplicates(df: pd.DataFrame, verbose: bool = True) -> pd.DataFrame:
    """
    Remove duplicate transactions based on merchant, date, and amount.
    Keeps the last occurrence (by time).
    
    Args:
        df: Input DataFrame
        verbose: If True, print deleted rows
        
    Returns:
        DataFrame with duplicates removed
    """
    df = df.copy()
    
    # Check required columns
    required_cols = ['merchant', 'date', 'amount', 'time']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        return df
    
    # Sort by time to ensure last time is kept
    df_sorted = df.sort_values('time')
    
    # Identify duplicates based on 'merchant', 'date', and 'amount', keeping the last occurrence
    duplicates_mask = df_sorted.duplicated(subset=['merchant', 'date', 'amount'], keep='last')
    
    # Get the rows that will be deleted
    deleted_rows = df_sorted[duplicates_mask][['merchant', 'date', 'amount']]
    
    # Print deleted rows if verbose
    if verbose and not deleted_rows.empty:
        print("Deleted rows:")
        print(deleted_rows)
    
    # Create new dataframe keeping only the non-duplicate rows (last occurrence)
    df_clean = df_sorted[~duplicates_mask].reset_index(drop=True)
    
    # Sort by date and time
    df_clean = df_clean.sort_values(by=['date', 'time'])
    
    return df_clean


def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply various filters to exclude unwanted rows.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Filtered DataFrame
    """
    df = df.copy()
    
    # Filter out excluded currencies
    if "currency" in df.columns:
        for currency in EXCLUDE_CURRENCIES:
            df = df[df["currency"] != currency]
    
    # Filter out excluded card numbers
    if "card_last4" in df.columns:
        for card_num in EXCLUDE_CARD_LAST4:
            df = df[df["card_last4"] != card_num]
    
    # Drop txn_type column if it exists
    if "txn_type" in df.columns:
        df = df.drop(columns=["txn_type"])
    
    return df


def add_date_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add year and month columns from date.
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with year and month columns
    """
    df = df.copy()
    
    if "date" in df.columns:
        df["year"] = df["date"].dt.year
        df["month"] = df["date"].dt.month
    
    return df


def clean_data(df: pd.DataFrame, start_date: Optional[str] = None, verbose: bool = True) -> pd.DataFrame:
    """
    Complete data cleaning pipeline.
    
    Args:
        df: Input DataFrame
        start_date: Start date for filtering (YYYY-MM-DD format)
        verbose: If True, print information about cleaning operations
        
    Returns:
        Cleaned DataFrame
    """
    df = convert_date_column(df)
    df = filter_by_date(df, start_date)
    df = apply_filters(df)
    df = remove_duplicates(df, verbose=verbose)
    df = add_date_columns(df)
    
    return df

