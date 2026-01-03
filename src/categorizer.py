"""Module for category assignment, translation, and 2nd category rules."""

import pandas as pd
from .config import (
    CATEGORY_MAPPING,
    CATEGORY_EN_TO_FI,
    SUBCATEGORY_EN_TO_FI,
    EMPTY_2ND_CATEGORY_RULES,
    GENERAL_2ND_CATEGORIES,
    CHECK_CATEGORIES
)


def get_second_category(row: pd.Series) -> str:
    """
    Get second category based on notes and main category.
    
    Args:
        row: DataFrame row with 'notes' and 'category' columns
        
    Returns:
        Second category string (empty if not found)
    """
    note = str(row['notes']).strip() if pd.notna(row.get('notes')) else ''
    main_category = str(row['category']).strip().title() if pd.notna(row.get('category')) else ''
    
    # Check if main category and note exist in mapping
    if main_category in CATEGORY_MAPPING and note in CATEGORY_MAPPING[main_category]:
        return CATEGORY_MAPPING[main_category][note]
    
    return ''  # Return empty string if combination not found


def add_second_category(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add second category column based on notes and main category.
    
    Args:
        df: Input DataFrame with 'notes' and 'category' columns
        
    Returns:
        DataFrame with '2nd category' column added
    """
    df = df.copy()
    
    if "notes" not in df.columns or "category" not in df.columns:
        return df
    
    df['2nd category'] = df.apply(get_second_category, axis=1)
    
    return df


def translate_category(value: str) -> str:
    """
    Translate English category to Finnish.
    
    Args:
        value: English category name
        
    Returns:
        Finnish category name (or original if translation not found)
    """
    return CATEGORY_EN_TO_FI.get(value.strip().title(), value)


def translate_second_category(value: str) -> str:
    """
    Translate English subcategory to Finnish.
    
    Args:
        value: English subcategory name
        
    Returns:
        Finnish subcategory name (or original if translation not found)
    """
    return SUBCATEGORY_EN_TO_FI.get(value.strip(), value)


def translate_categories(df: pd.DataFrame) -> pd.DataFrame:
    """
    Translate category and 2nd category columns to Finnish.
    
    Args:
        df: Input DataFrame with 'category' and '2nd category' columns
        
    Returns:
        DataFrame with translated categories
    """
    df = df.copy()
    
    if "category" in df.columns:
        df['category'] = df['category'].apply(translate_category)
    
    if "2nd category" in df.columns:
        df['2nd category'] = df['2nd category'].apply(translate_second_category)
    
    return df


def apply_empty_2nd_category_rules(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply rules to fill empty 2nd categories based on main category.
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with filled 2nd categories
    """
    df = df.copy()
    
    if "2nd category" not in df.columns or "category" not in df.columns:
        return df
    
    # Define empty 2nd category
    empty_2nd = (
        df["2nd category"].isna() |
        df["2nd category"].astype(str).str.strip().eq("")
    )
    
    # Apply rules for specific categories
    df.loc[
        empty_2nd & df["category"].isin(EMPTY_2ND_CATEGORY_RULES),
        "2nd category"
    ] = df.loc[
        empty_2nd & df["category"].isin(EMPTY_2ND_CATEGORY_RULES),
        "category"
    ].map(EMPTY_2ND_CATEGORY_RULES)
    
    # Special rule: Shopping + Kids -> Perhe
    df.loc[
        (df["category"] == "Ostokset") &
        (df["2nd category"] == "Lapset"),
        "2nd category"
    ] = "Perhe"
    
    # Apply "Yleinen" for categories that should always have it when empty
    empty_2nd = (
        df["2nd category"].isna() |
        df["2nd category"].astype(str).str.strip().eq("")
    )
    
    df.loc[
        empty_2nd & df["category"].isin(GENERAL_2ND_CATEGORIES),
        "2nd category"
    ] = "Yleinen"
    
    return df


def customize_general_subcategory_names(df: pd.DataFrame) -> pd.DataFrame:
    """
     Customize subcategory names based on main category.
    Adds prefix "Pääkategoria: " to "Yleinen", "Perhe", and "Henkilökohtainen" subcategories.
    Excludes "Autoilu & Liikkuminen" category from renaming.
    
    Args:
        df: Input DataFrame with 'category' and '2nd category' columns
        
    Returns:
        DataFrame with customized subcategory names
    """
    df = df.copy()
    
    if "2nd category" not in df.columns or "category" not in df.columns:
        return df
    
    # Exclude Autoilu & Liikkuminen from renaming
    exclude_category = "Autoilu & Liikkuminen"
    
    # Customize "Yleinen" based on main category
    mask_harrastukset = (df["category"] == "Harrastukset") & (df["2nd category"] == "Yleinen")
    df.loc[mask_harrastukset, "2nd category"] = "Harrastukset: Yleinen"
    
    mask_ruokakauppa = (df["category"] == "Ruokakauppa") & (df["2nd category"] == "Yleinen")
    df.loc[mask_ruokakauppa, "2nd category"] = "Ruokakauppa: Yleinen"
    
    mask_striimaus = (df["category"] == "Striimaus & Palvelut") & (df["2nd category"] == "Yleinen")
    df.loc[mask_striimaus, "2nd category"] = "Striimaus & Palvelut: Yleinen"
    
    mask_koulutus = (df["category"] == "Koulutus, Kirjallisuus & Kehittäminen") & (df["2nd category"] == "Yleinen")
    df.loc[mask_koulutus, "2nd category"] = "Koul.,Kirj.&Keh:Yleinen"
    
    # Customize all Ostokset subcategories with "Ostokset: " prefix
    mask_ostokset = df["category"] == "Ostokset"
    ostokset_subcats = df.loc[mask_ostokset, "2nd category"]
    # Only rename if it doesn't already start with "Ostokset: "
    mask_ostokset_not_prefixed = mask_ostokset & (~ostokset_subcats.str.startswith("Ostokset: ", na=False))
    df.loc[mask_ostokset_not_prefixed, "2nd category"] = "Ostokset: " + df.loc[mask_ostokset_not_prefixed, "2nd category"]
    
    # Customize "Perhe" and "Henkilökohtainen" with category prefix (excluding Autoilu & Liikkuminen and Ostokset, as it's already handled above)
    mask_perhe = (df["category"] != exclude_category) & (df["category"] != "Ostokset") & (df["2nd category"] == "Perhe")
    df.loc[mask_perhe, "2nd category"] = df.loc[mask_perhe, "category"] + ": Perhe"
    
    mask_henkilokohtainen = (df["category"] != exclude_category) & (df["category"] != "Ostokset") & (df["2nd category"] == "Henkilökohtainen")
    df.loc[mask_henkilokohtainen, "2nd category"] = df.loc[mask_henkilokohtainen, "category"] + ": Henkilökohtainen"
    
    return df


def validate_categories(df: pd.DataFrame, verbose: bool = True) -> pd.DataFrame:
    """
    Validate that all required categories have 2nd category filled.
    
    Args:
        df: Input DataFrame
        verbose: If True, print validation results
        
    Returns:
        DataFrame (unchanged, validation only)
    """
    if "2nd category" not in df.columns or "category" not in df.columns:
        return df
    
    # Define empty 2nd category
    empty_2nd = (
        df["2nd category"].isna() |
        df["2nd category"].astype(str).str.strip().eq("")
    )
    
    # Check remaining empty categories
    remaining = df.loc[
        empty_2nd & df["category"].isin(CHECK_CATEGORIES),
        ["date", "time", "merchant", "amount", "category", "2nd category"]
    ]
    
    if verbose:
        if not remaining.empty:
            print("⚠️ Seuraavissa riveissä 2nd category on yhä tyhjä:\n")
            print(remaining)
        else:
            print("✅ Kaikilla riveillä 2nd category on määritetty näissä kategorioissa.")
    
    return df


def categorize_data(df: pd.DataFrame, verbose: bool = True) -> pd.DataFrame:
    """
    Complete categorization pipeline.
    
    Args:
        df: Input DataFrame
        verbose: If True, print validation results
        
    Returns:
        DataFrame with categories assigned and translated
    """
    df = add_second_category(df)
    df = translate_categories(df)
    df = apply_empty_2nd_category_rules(df)
    df = customize_general_subcategory_names(df)
    df = validate_categories(df, verbose=verbose)
    
    return df

