# Quick Start Guide

Tämä on nopea käyttöohje. Täydellinen dokumentaatio löytyy [`DOCUMENTATION.md`](DOCUMENTATION.md) -tiedostosta.

## 1. Install Dependencies

```bash
pip install -r requirements.txt
```

## 2. Configure Environment Variables (Optional)

Create a `.env` file for personal configuration:

```bash
cp .env.example .env
```

Edit `.env` and set your paths (optional):
- `DEFAULT_CSV_PATH`: Path to your CSV file (or use `data/raw/` directory)
- `DEFAULT_EXCEL_PATH`: Path for Excel output (optional)
- `OPENAI_API_KEY`: Required for AI Assistant feature

## 3. Set Up Your Data

You have three options:

### Option A: Use data directory (recommended)
1. Copy your CSV files to `data/raw/` directory
2. The pipeline will auto-detect and process them

### Option B: Set DEFAULT_CSV_PATH in .env file
1. Edit `.env` file and set `DEFAULT_CSV_PATH=/path/to/your/transactions.csv`
2. The app will use this path automatically

### Option C: Upload via Streamlit app
1. Use the file upload feature in the Streamlit app

## 4. Process Your Data

### Using Python Script
```python
from src.pipeline import process_file

# Process a specific CSV file
df = process_file('path/to/transactions.csv', start_date='2025-01-01')
```


### Auto-detect New Files
```python
from src.pipeline import process_new_files

# Automatically find and process new CSV files in data/raw/
df = process_new_files()
```

## 5. Run Streamlit App

```bash
streamlit run app/main.py
```

Or use the convenience script:
```bash
./run_app.sh
```

The app will:
- ✅ Auto-detect new CSV files
- 📊 Show dashboard with spending statistics
- 📋 Display filterable transaction table
- ✏️ Allow editing categories and notes
- 💾 Save changes back to Excel

## 6. Next Steps

- **Explore data**: Use Streamlit app for custom analysis
- **Edit categories**: Use Streamlit app to quickly fix categorization
- **Add new CSV files**: Just drop them in `data/raw/` and refresh the app
- **Customize**: Edit `src/config.py` to modify category mappings

## Troubleshooting

- **Import errors**: Make sure you're in the project root directory
- **File not found**: Check paths in `.env` file or use `data/raw/` directory
- **Dependencies**: Run `pip install -r requirements.txt`
- **Environment variables not loading**: Make sure `.env` file exists in project root

