"""Module for loading CSV files and initial data cleaning."""

import pandas as pd
from pathlib import Path
from typing import Optional


def load_transactions_csv(file_path: str) -> pd.DataFrame:
    """
    Load transaction data from CSV file.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        DataFrame with loaded transaction data
        
    Raises:
        Exception: If file cannot be loaded
    """
    try:
        # Use comma as delimiter, handle quoted strings, and specify UTF-8 encoding
        df = pd.read_csv(file_path, delimiter=',', quotechar='"', encoding='utf-8')
        
        # Strip any leading/trailing whitespace from column names
        df.columns = [col.strip() for col in df.columns]
        
        # Optionally, display full column content for long fields (like Merchant)
        pd.set_option('display.max_colwidth', None)
        
        return df
        
    except Exception as e:
        raise Exception(f"Error loading CSV file: {e}")


def initial_cleanup(df: pd.DataFrame) -> pd.DataFrame:
    """
    Perform initial data cleanup: remove quotes, filter rows, drop columns.
    
    Args:
        df: Input DataFrame
        
    Returns:
        Cleaned DataFrame
    """
    df = df.copy()
    
    # Remove quotes from Merchant and Notes columns
    if "Merchant" in df.columns:
        df["Merchant"] = df["Merchant"].str.replace('"', '', regex=False)
    if "Notes" in df.columns:
        df["Notes"] = df["Notes"].str.replace('"', '', regex=False)
    
    # Remove rows where 'Type' is 'REFUNDED'
    if "Type" in df.columns:
        df = df[df["Type"] != "REFUNDED"]
    
    # Remove rows where Notes is " del"
    if "Notes" in df.columns:
        df = df[df["Notes"] != " del"]
    
    # Drop unnecessary columns
    columns_to_drop = ["Export Format", "Txn Amount (Foreign Spend)"]
    df = df.drop(columns=[col for col in columns_to_drop if col in df.columns])
    
    return df


def standardize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize column names: rename and convert to lowercase with underscores.
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with standardized column names
    """
    df = df.copy()
    
    # Rename Date column
    if "Date (YYYY-MM-DD as UTC)" in df.columns:
        df = df.rename(columns={"Date (YYYY-MM-DD as UTC)": "date"})
    
    # Convert all column names to lowercase and replace spaces with underscores
    df.columns = df.columns.str.lower().str.replace(" ", "_")
    
    # Rename specific columns
    rename_map = {
        "time_(hh:mm:ss)": "time",
        "txn_amount_(funding_card)": "amount",
        "txn_currency_(funding_card)": "currency",
        "txn_currency_(foreign_spend)": "foreign_currency",
        "card_name": "card",
        "card_last_4_digits": "card_last4",
        "type": "txn_type",
        "category": "category",
        "notes": "notes"
    }
    
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})
    
    return df


def process_card_numbers(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean and process card_last4 column, then map to card names.
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with processed card information
    """
    import numpy as np
    from .config import CARD_MAPPING
    
    df = df.copy()
    
    if "card_last4" not in df.columns:
        return df
    
    # Clean 'card_last4' column
    df["card_last4"] = df["card_last4"].astype(str).str.strip()
    df["card_last4"] = df["card_last4"].replace("", np.nan)  # Convert empty strings to NaN
    df["card_last4"] = pd.to_numeric(df["card_last4"], errors="coerce")  # Convert valid numbers, NaN otherwise
    
    # Fill NaN values with -1 (placeholder that does not match actual card numbers)
    df["card_last4"] = df["card_last4"].fillna(-1).astype(int)
    
    # Map card numbers to card names
    if "card" in df.columns:
        df["card"] = df["card_last4"].astype(int).map(CARD_MAPPING).fillna(df["card"])
    
    return df


def load_and_prepare_data(file_path: str) -> pd.DataFrame:
    """
    Complete data loading and initial preparation pipeline.
    
    Args:
        file_path: Path to the CSV file
        
    Returns:
        Prepared DataFrame
    """
    df = load_transactions_csv(file_path)
    df = initial_cleanup(df)
    df = standardize_column_names(df)
    df = process_card_numbers(df)
    
    return df

