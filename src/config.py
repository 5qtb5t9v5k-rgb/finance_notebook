"""Configuration file for category mappings, card mappings, and file paths."""

import os
from pathlib import Path

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv is optional

# Base paths
BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
VECTOR_DB_PATH = PROCESSED_DATA_DIR / "vector_db"

# Default file paths (loaded from environment variables or None)
# Set these in .env file or as environment variables
DEFAULT_CSV_PATH = os.getenv("DEFAULT_CSV_PATH", None)
DEFAULT_EXCEL_PATH = os.getenv("DEFAULT_EXCEL_PATH", None)

# Card mappings (card_last4 -> card name)
CARD_MAPPING = {
    6334: "crypto.com",
    9264: "norwegian",
    8529: "norwegian",
    829: "OP"
}

# Category mappings (main category -> subcategory abbreviations)
CATEGORY_MAPPING = {
    'General': {},  # Renamed to "Hobbies", no subcategories
    'Bills': {},
    'Business Services': {},
    'Entertainment': {
        'F': 'Family',
        'P': 'Personal'
    },
    'Transport': {
        'G': 'Car Gas',
        'M': 'Car Maintenance',
        'P': 'Public'
    },
    'Shopping': {
        'H': 'Home / House',
        'P': 'Personal',
        'RT': 'Renovating & Tools',
        'F': 'Family',
        'G': 'Gifts',
        'K': 'Kids'
    },
    'Eating Out': {
        'S': 'Snacks & Soda',
        'R': 'Restaurants'
    },
    'Groceries': {},
    'Health': {
        'F': 'Family',
        'P': 'Personal'
    },
    'Travel': {
        'F': 'Family',
        'P': 'Personal'
    }
}

# English to Finnish category translations
CATEGORY_EN_TO_FI = {
    'General': 'Harrastukset',
    'Business Services': 'Koulutus, Kirjallisuus & Kehittäminen',
    'Entertainment': 'Tapahtumat & Viihde',
    'Transport': 'Autoilu & Liikkuminen',
    'Shopping': 'Ostokset',
    'Eating Out': 'Ulkona syöminen',
    'Groceries': 'Ruokakauppa',
    'Subscriptions': 'Striimaus & Palvelut',
    'Health': 'Terveys',
    'Travel': 'Matkailu',
    'Bills': 'Striimaus & Palvelut',
}

# English to Finnish subcategory translations
SUBCATEGORY_EN_TO_FI = {
    'Family': 'Perhe',
    'Renovating & Tools': 'Remontointi',
    'Gifts': 'Lahjat',
    'Personal': 'Henkilökohtainen',
    'Car Gas': 'Auton Polttoaine',
    'Car Maintenance': 'Auton Huollot & Ylläpito',
    'Public': 'Julkinen liikenne',
    'Home / House': 'Koti',
    'Kids': 'Lapset',
    'Snacks & Soda': 'Välipalat & Virvoikkeet',
    'Restaurants': 'Ravintolat'
}

# Rules for filling empty 2nd categories
EMPTY_2ND_CATEGORY_RULES = {
    "Autoilu & Liikkuminen": "Julkinen liikenne",
    "Ostokset": "Henkilökohtainen",
    "Tapahtumat & Viihde": "Henkilökohtainen",
    "Terveys": "Henkilökohtainen",
    "Matkailu": "Henkilökohtainen",
}

# Categories that should have "Yleinen" as 2nd category when empty
GENERAL_2ND_CATEGORIES = [
    "Harrastukset",
    "Koulutus, Kirjallisuus & Kehittäminen",
    "Remontointi",
    "Ruokakauppa",
    "Striimaus & Palvelut",
]

# Categories to check for empty 2nd category
CHECK_CATEGORIES = [
    "Autoilu & Liikkuminen",
    "Ostokset",
    "Tapahtumat & Viihde",
    "Terveys",
]

# Date filtering
DEFAULT_START_DATE = '2025-01-01'

# Data cleaning filters
EXCLUDE_TYPES = ["REFUNDED"]
EXCLUDE_NOTES = [" del"]
EXCLUDE_CURRENCIES = [" CPT"]
EXCLUDE_CARD_LAST4 = [2033]

