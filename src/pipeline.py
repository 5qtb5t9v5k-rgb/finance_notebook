"""Main pipeline orchestrator with auto-detection of new CSV files."""

import pandas as pd
from pathlib import Path
from typing import Optional, List
import json
from datetime import datetime
import hashlib

from .data_loader import (
    load_and_prepare_data, 
    load_transactions_csv, 
    initial_cleanup,
    standardize_column_names,
    process_card_numbers
)
from .data_cleaner import clean_data
from .cost_allocator import apply_cost_allocation
from .categorizer import categorize_data
from .config import (
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    DEFAULT_CSV_PATH
)


def get_processed_files_log() -> Path:
    """Get path to the processed files log."""
    return PROCESSED_DATA_DIR / ".processed_files.json"


def load_processed_files_log() -> dict:
    """Load the log of processed files."""
    log_file = get_processed_files_log()
    if log_file.exists():
        try:
            with open(log_file, 'r') as f:
                return json.load(f)
        except:
            return {}
    return {}


def save_processed_files_log(log: dict):
    """Save the log of processed files."""
    log_file = get_processed_files_log()
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(log_file, 'w') as f:
        json.dump(log, f, indent=2)


def get_file_info(file_path: Path) -> dict:
    """Get file modification time and size."""
    stat = file_path.stat()
    return {
        "modified_time": stat.st_mtime,
        "size": stat.st_size,
        "processed_time": datetime.now().isoformat()
    }

def _make_processed_log_key(file_path: Path) -> str:
    """
    Create a stable, privacy-preserving key for processed-files log entries.

    - If the file is under RAW_DATA_DIR, store it as a relative path (no user home leaks).
    - Otherwise, store a deterministic hash of the absolute path.
    """
    try:
        rel = file_path.resolve().relative_to(RAW_DATA_DIR.resolve())
        return str(rel)
    except Exception:
        digest = hashlib.sha256(str(file_path.resolve()).encode("utf-8")).hexdigest()
        return f"external:{digest}"


def is_file_new_or_updated(file_path: Path, processed_log: dict) -> bool:
    """Check if file is new or has been updated since last processing."""
    log_key = _make_processed_log_key(file_path)
    legacy_key = str(file_path)
    entry = processed_log.get(log_key) or processed_log.get(legacy_key)
    if not entry:
        return True
    
    current_stat = file_path.stat()
    last_modified = entry.get("modified_time", 0)
    
    return current_stat.st_mtime > last_modified


def find_csv_files(directory: Optional[Path] = None) -> List[Path]:
    """
    Find all CSV files in the specified directory.
    
    Args:
        directory: Directory to search. If None, uses RAW_DATA_DIR
        
    Returns:
        List of CSV file paths
    """
    if directory is None:
        directory = RAW_DATA_DIR
    
    if not directory.exists():
        return []
    
    return list(directory.glob("*.csv"))


def detect_new_files(directory: Optional[Path] = None) -> List[Path]:
    """
    Detect new or updated CSV files that need processing.
    
    Args:
        directory: Directory to search. If None, uses RAW_DATA_DIR
        
    Returns:
        List of new/updated CSV file paths
    """
    csv_files = find_csv_files(directory)
    processed_log = load_processed_files_log()
    
    new_files = [
        f for f in csv_files
        if is_file_new_or_updated(f, processed_log)
    ]
    
    return new_files


def process_transactions(
    csv_path: str,
    start_date: Optional[str] = None,
    verbose: bool = True
) -> pd.DataFrame:
    """
    Complete transaction processing pipeline.
    
    Args:
        csv_path: Path to CSV file
        start_date: Start date for filtering (YYYY-MM-DD format)
        verbose: If True, print processing information
        
    Returns:
        Processed DataFrame
    """
    if verbose:
        print(f"Loading data from: {csv_path}")
    
    # Load and prepare data
    df = load_and_prepare_data(csv_path)
    
    if verbose:
        print(f"Loaded {len(df)} rows")
    
    # Clean data
    df = clean_data(df, start_date=start_date, verbose=verbose)
    
    if verbose:
        print(f"After cleaning: {len(df)} rows")
    
    # Apply cost allocation
    df = apply_cost_allocation(df)
    
    # Categorize data
    df = categorize_data(df, verbose=verbose)
    
    if verbose:
        print(f"Final dataset: {len(df)} rows")
        print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    
    return df


def process_dataframe(
    df: pd.DataFrame,
    start_date: Optional[str] = None,
    verbose: bool = True
) -> pd.DataFrame:
    """
    Process DataFrame through the complete pipeline (for uploaded files).
    
    This function processes a DataFrame that has already been loaded from CSV,
    applying the same transformations as process_transactions but without
    needing a file path.
    
    Args:
        df: Input DataFrame (already loaded from CSV, with original column names)
        start_date: Start date for filtering (YYYY-MM-DD format)
        verbose: If True, print processing information
        
    Returns:
        Processed DataFrame
    """
    if verbose:
        print(f"Processing DataFrame with {len(df)} rows")
    
    # Apply the same transformations as load_and_prepare_data
    # 1. Initial cleanup
    df = initial_cleanup(df)
    
    if verbose:
        print(f"After initial cleanup: {len(df)} rows")
    
    # 2. Standardize column names
    df = standardize_column_names(df)
    
    # 3. Process card numbers
    df = process_card_numbers(df)
    
    # 4. Clean data (remove duplicates, filter dates, etc.)
    df = clean_data(df, start_date=start_date, verbose=verbose)
    
    if verbose:
        print(f"After cleaning: {len(df)} rows")
    
    # 5. Apply cost allocation
    df = apply_cost_allocation(df)
    
    # 6. Categorize data
    df = categorize_data(df, verbose=verbose)
    
    if verbose:
        print(f"Final dataset: {len(df)} rows")
        if 'date' in df.columns and not df.empty:
            print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    
    return df


def save_to_excel(df: pd.DataFrame, excel_path: Optional[str] = None):
    """
    Save DataFrame to Excel file (deprecated - data now stored in session state).
    
    Args:
        df: DataFrame to save
        excel_path: Path to Excel file (ignored)
    """
    # No-op: data is now stored in Streamlit session state
    pass


def process_file(
    csv_path: str,
    start_date: Optional[str] = None,
    verbose: bool = True
) -> pd.DataFrame:
    """
    Process a single CSV file.
    
    Args:
        csv_path: Path to CSV file
        start_date: Start date for filtering (YYYY-MM-DD format)
        verbose: If True, print processing information
        
    Returns:
        Processed DataFrame
    """
    csv_file = Path(csv_path)
    
    # Process the file
    df = process_transactions(csv_path, start_date=start_date, verbose=verbose)
    
    # Update processed files log
    processed_log = load_processed_files_log()
    processed_log[_make_processed_log_key(csv_file)] = get_file_info(csv_file)
    save_processed_files_log(processed_log)
    
    return df


def process_new_files(
    directory: Optional[Path] = None,
    start_date: Optional[str] = None,
    verbose: bool = True
) -> pd.DataFrame:
    """
    Detect and process all new or updated CSV files.
    
    Args:
        directory: Directory to search for CSV files. If None, uses RAW_DATA_DIR
        start_date: Start date for filtering (YYYY-MM-DD format)
        verbose: If True, print processing information
        
    Returns:
        Combined processed DataFrame from all new files
    """
    new_files = detect_new_files(directory)
    
    if not new_files:
        if verbose:
            print("No new or updated files found.")
        return pd.DataFrame()
    
    if verbose:
        print(f"Found {len(new_files)} new/updated file(s):")
        for f in new_files:
            print(f"  - {f}")
    
    # Process all new files
    dfs = []
    for csv_file in new_files:
        df = process_file(
            str(csv_file),
            start_date=start_date,
            verbose=verbose
        )
        dfs.append(df)
    
    # Combine all dataframes
    if dfs:
        combined_df = pd.concat(dfs, ignore_index=True)
        
        # Remove duplicates across files
        combined_df = combined_df.sort_values(by=['date', 'time'])
        combined_df = combined_df.drop_duplicates(
            subset=['merchant', 'date', 'amount'],
            keep='last'
        ).reset_index(drop=True)
        
        return combined_df
    
    return pd.DataFrame()


def load_processed_data(excel_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load processed data from Excel file (deprecated - data now stored in session state).
    
    Args:
        excel_path: Path to Excel file (ignored)
        
    Returns:
        Empty DataFrame (data is now stored in Streamlit session state)
    """
    # Return empty DataFrame - data is now stored in Streamlit session state
    return pd.DataFrame()

