"""Module for extracting cost allocation percentages from notes."""

import pandas as pd
import re
from typing import Tuple


def extract_cost_allocation(notes: str) -> Tuple[float, str]:
    """
    Extract cost allocation percentage from notes and return cleaned notes.
    
    Notes format: "text/50%" means 50% allocation.
    
    Args:
        notes: Notes string that may contain allocation percentage
        
    Returns:
        Tuple of (allocation_percentage, cleaned_notes)
        - allocation_percentage: Float between 0 and 1 (default 1.0)
        - cleaned_notes: Notes string with percentage removed
    """
    notes_str = str(notes)
    match = re.search(r'/(\d+)%', notes_str)  # Extract only the percentage
    
    if match:
        percentage = float(match.group(1)) / 100
        cleaned_notes = re.sub(r'/\d+%$', '', notes_str)  # Remove percentage from notes
        return percentage, cleaned_notes
    
    return 1.0, notes_str  # Default to 100% if no percentage found


def apply_cost_allocation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract cost allocation from notes and calculate adjusted_amount.
    
    Args:
        df: Input DataFrame with 'notes' and 'amount' columns
        
    Returns:
        DataFrame with 'cost_allocation' and 'adjusted_amount' columns added
    """
    df = df.copy()
    
    if "notes" not in df.columns or "amount" not in df.columns:
        return df
    
    # Apply extraction function
    df["cost_allocation"], df["notes"] = zip(*df["notes"].apply(extract_cost_allocation))
    
    # Calculate adjusted amount
    df["adjusted_amount"] = df["amount"] * df["cost_allocation"]
    
    return df

