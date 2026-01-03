# Quick Start Guide

Tämä on nopea käyttöohje. Täydellinen dokumentaatio löytyy [`DOCUMENTATION.md`](DOCUMENTATION.md) -tiedostosta.

## 1. Install Dependencies

```bash
pip install -r requirements.txt
```

## 2. Set Up Your Data

You have two options:

### Option A: Use existing CSV file
Your current CSV file path is configured in `src/config.py`:
- Default: `/Users/juhorissanen/Desktop/Transactions.csv`

### Option B: Use data directory (recommended)
1. Copy your CSV files to `data/raw/` directory
2. The pipeline will auto-detect and process them

## 3. Process Your Data

### Using Python Script
```python
from src.pipeline import process_file

# Process your CSV file
df = process_file('/Users/juhorissanen/Desktop/Transactions.csv', save_excel=True)
```

### Using Notebook
Open `notebooks/exploration.ipynb` and run the cells. The notebook will:
- Process your CSV file
- Save to Excel
- Display the results

### Auto-detect New Files
```python
from src.pipeline import process_new_files

# Automatically find and process new CSV files in data/raw/
df = process_new_files(save_excel=True)
```

## 4. Run Streamlit App

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

## 5. Next Steps

- **Explore data**: Use the notebook for custom analysis
- **Edit categories**: Use Streamlit app to quickly fix categorization
- **Add new CSV files**: Just drop them in `data/raw/` and refresh the app
- **Customize**: Edit `src/config.py` to modify category mappings

## Troubleshooting

- **Import errors**: Make sure you're in the project root directory
- **File not found**: Check paths in `src/config.py`
- **Dependencies**: Run `pip install -r requirements.txt`

