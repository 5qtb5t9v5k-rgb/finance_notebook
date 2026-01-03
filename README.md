# Finance Transaction Pipeline & App

Modulaarinen pipeline Curve-sovelluksen tapahtumatietojen käsittelyyn, jossa on Streamlit-sovellus tapahtumien katseluun, muokkaamiseen ja visualisointiin.

## 📚 Dokumentaatio

- **⭐ Kattava dokumentaatio**: [`COMPREHENSIVE_DOCUMENTATION.md`](COMPREHENSIVE_DOCUMENTATION.md) - **Aloita tästä!** Kattava opas kaikesta
- **Perusidea ja arkkitehtuuri**: [`ARCHITECTURE.md`](ARCHITECTURE.md) - Yleiskuvaus, perusidea ja rakenne
- **Täydellinen dokumentaatio**: [`DOCUMENTATION.md`](DOCUMENTATION.md) - Yksityiskohtainen selitys kaikesta
- **Pipeline-ajon ohje**: [`PIPELINE_GUIDE.md`](PIPELINE_GUIDE.md) - Vaiheittainen ohje pipeline-prosessin ajamiseen
- **Työnkulku**: [`WORKFLOW.md`](WORKFLOW.md) - Miten pipeline ja Streamlit liittyvät toisiinsa
- **AI Assistant -asetus**: [`AI_ASSISTANT_SETUP.md`](AI_ASSISTANT_SETUP.md) - AI Assistant -ominaisuuden asennus ja käyttö

## Features

- **Modular Pipeline**: Clean, reusable functions for data processing
- **Auto-detection**: Automatically detects and processes new CSV files
- **Streamlit App**: Interactive web app for viewing, filtering, and editing transactions
- **Jupyter Notebook**: For interactive exploration and ad-hoc analysis
- **Category Management**: Automatic categorization with Finnish translations
- **Cost Allocation**: Support for percentage-based cost allocation in notes
- **AI Assistant**: Ask questions about your finances (optional, requires OpenAI API key - see [AI_ASSISTANT_SETUP.md](AI_ASSISTANT_SETUP.md))

## Quick Start

1. **Install dependencies:**
```bash
pip install -r requirements.txt
source venv/bin/activate  # If using virtual environment
```

2. **Run Streamlit app:**
```bash
streamlit run app/main.py
```

3. **Process your CSV file:**
   - The app will automatically detect and process CSV files
   - Or click "Process CSV File" button if needed

## Project Structure

```
finance_notebook/
├── src/                    # Pipeline modules
│   ├── config.py          # Configuration and mappings
│   ├── data_loader.py     # CSV loading
│   ├── data_cleaner.py     # Data cleaning
│   ├── categorizer.py      # Category assignment
│   ├── cost_allocator.py   # Cost allocation extraction
│   └── pipeline.py         # Main orchestrator
├── app/                    # Streamlit app
│   └── main.py            # App entry point
├── notebooks/             # Jupyter notebooks
│   └── exploration.ipynb  # Analysis notebook
└── data/                  # Data files
    ├── raw/              # Original CSV files
    └── processed/        # Processed Excel files
```

## Usage

### Process Data via Python

```python
from src.pipeline import process_file, process_new_files

# Process a specific file
df = process_file('path/to/transactions.csv', save_excel=True)

# Auto-detect and process new files
df = process_new_files(save_excel=True)
```

### Run Streamlit App

```bash
streamlit run app/main.py
```

The app will:
- Auto-detect new CSV files
- Display dashboard with spending statistics
- Allow filtering and searching transactions
- Enable editing categories and notes
- Save changes back to Excel

### Use Jupyter Notebook

Open `notebooks/exploration.ipynb` and run the cells. The notebook uses the pipeline modules for data processing.

## Configuration

Edit `src/config.py` to:
- Update category mappings
- Change file paths
- Modify card mappings
- Adjust filtering rules

## Data Flow

1. CSV files are placed in `data/raw/` (or use default path)
2. Pipeline detects new/updated files
3. Data is cleaned, categorized, and processed
4. Results are saved to Excel (`data/processed/` or configured path)
5. Streamlit app loads from Excel for viewing/editing

## Notes Format

- Use notes like `"F"` for subcategory codes
- Use `"/50%"` suffix for cost allocation (e.g., `"Restaurant/50%"` means 50% allocation)
- Categories are automatically translated to Finnish

## Documentation

- **⭐ Kattava dokumentaatio**: [`COMPREHENSIVE_DOCUMENTATION.md`](COMPREHENSIVE_DOCUMENTATION.md) - **Aloita tästä!** Kattava opas kaikesta
- **Täydellinen dokumentaatio**: [`DOCUMENTATION.md`](DOCUMENTATION.md)
- **Pipeline-ajon ohje**: [`PIPELINE_GUIDE.md`](PIPELINE_GUIDE.md) - Vaiheittainen ohje pipeline-prosessin ajamiseen
- **AI Assistant -asetus**: [`AI_ASSISTANT_SETUP.md`](AI_ASSISTANT_SETUP.md) - AI Assistant -ominaisuuden asennus ja käyttö (vapaaehtoinen)

