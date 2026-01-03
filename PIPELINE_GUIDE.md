# Pipeline-ajon Vaiheittainen Ohje

Tämä ohje näyttää, miten ajaa koko pipeline-prosessin itsenäisesti alusta loppuun.

## Vaihtoehdot

Voit ajaa pipeline-prosessin kolmella tavalla:
1. **Python-skriptinä** (suositus)
2. **Jupyter Notebookissa**
3. **Komentoriviltä suoraan**

---

## Vaihtoehto 1: Python-skriptinä (Suositus)

### Vaihe 1: Varmista että virtuaaliympäristö on aktivoitu

```bash
source venv/bin/activate
```

Tai käytä aktivointiskriptiä:
```bash
./activate.sh
```

### Vaihe 2: Luo Python-skripti

Luo tiedosto `run_pipeline.py` projektin juureen:

```python
#!/usr/bin/env python3
"""Run the complete pipeline process."""

from src.pipeline import process_file
from src.config import DEFAULT_CSV_PATH

# Vaihtoehto A: Käsittele tietty CSV-tiedosto
print("🔄 Aloitetaan pipeline-prosessi...")
print(f"📂 CSV-tiedosto: {DEFAULT_CSV_PATH}")

df = process_file(
    csv_path=DEFAULT_CSV_PATH,
    start_date='2025-01-01',  # Suodata tapahtumat tämän päivämäärän jälkeen
    save_excel=True,          # Tallenna Exceliin
    verbose=True              # Näytä yksityiskohtaiset viestit
)

print(f"\n✅ Pipeline valmis!")
print(f"📊 Käsiteltyjä rivejä: {len(df)}")
print(f"📅 Aikaväli: {df['date'].min()} - {df['date'].max()}")
print(f"💰 Kokonaissumma: €{df['adjusted_amount'].sum():,.2f}")
```

### Vaihe 3: Aja skripti

```bash
python run_pipeline.py
```

---

## Vaihtoehto 2: Automaattinen uusien tiedostojen käsittely

Jos haluat käsitellä automaattisesti kaikki uudet CSV-tiedostot `data/raw/` -hakemistosta:

```python
#!/usr/bin/env python3
"""Auto-detect and process new CSV files."""

from src.pipeline import process_new_files

print("🔍 Etsitään uusia CSV-tiedostoja...")

df = process_new_files(
    save_excel=True,  # Tallenna Exceliin
    verbose=True      # Näytä yksityiskohtaiset viestit
)

if df is not None and not df.empty:
    print(f"\n✅ Käsittely valmis!")
    print(f"📊 Käsiteltyjä rivejä: {len(df)}")
    print(f"💰 Kokonaissumma: €{df['adjusted_amount'].sum():,.2f}")
else:
    print("\nℹ️ Ei uusia tiedostoja käsiteltäväksi.")
```

---

## Vaihtoehto 3: Jupyter Notebookissa

### Vaihe 1: Avaa Jupyter Notebook

```bash
jupyter notebook notebooks/exploration.ipynb
```

### Vaihe 2: Suorita solu

```python
from src.pipeline import process_file
from src.config import DEFAULT_CSV_PATH

# Käsittele CSV-tiedosto
df = process_file(
    csv_path=DEFAULT_CSV_PATH,
    start_date='2025-01-01',
    save_excel=True,
    verbose=True
)

# Näytä tulokset
print(f"✅ Käsiteltyjä rivejä: {len(df)}")
print(f"📅 Aikaväli: {df['date'].min()} - {df['date'].max()}")
df.head()
```

---

## Vaihtoehto 4: Komentoriviltä suoraan

### Vaihe 1: Aktivoi virtuaaliympäristö

```bash
source venv/bin/activate
```

### Vaihe 2: Aja Python-komento

```bash
python -c "
from src.pipeline import process_file
from src.config import DEFAULT_CSV_PATH
df = process_file(DEFAULT_CSV_PATH, start_date='2025-01-01', save_excel=True, verbose=True)
print(f'✅ Valmis! Käsitelty {len(df)} riviä.')
"
```

---

## Mitä pipeline tekee vaihe vaiheelta?

Kun ajat `process_file()`-funktion, se suorittaa seuraavat vaiheet automaattisesti:

### Vaihe 1: CSV-tiedoston lataus
```python
# src/data_loader.py
df = load_and_prepare_data(file_path)
```
- Lataa CSV-tiedoston
- Poistaa lainausmerkit
- Standardoi sarakkeiden nimet

### Vaihe 2: Datan siivous
```python
# src/data_cleaner.py
df = clean_data(df, start_date='2025-01-01')
```
- Muuntaa päivämäärät
- Suodattaa päivämäärän mukaan
- Poistaa duplikaatit
- Lisää vuosi/kuukausi-sarakkeet

### Vaihe 3: Kustannusjakojen käsittely
```python
# src/cost_allocator.py
df = apply_cost_allocation(df)
```
- Etsii "/50%" -tyyppisiä merkintöjä notes-sarakkeesta
- Laskee adjusted_amount

### Vaihe 4: Kategorisointi
```python
# src/categorizer.py
df = categorize_data(df)
```
- Lisää 2nd category -sarakkeen
- Kääntää kategoriat suomeksi
- Täyttää tyhjät kategoriat säännöillä
- Muuttaa alakategorian nimet

### Vaihe 5: Tallennus Exceliin
```python
# src/pipeline.py
save_to_excel(df, DEFAULT_EXCEL_PATH)
```
- Tallentaa käsitellyn datan Exceliin

---

## Parametrit

### `process_file()` -funktion parametrit:

- **`csv_path`** (pakollinen): Polku CSV-tiedostoon
  ```python
  csv_path = "/Users/juhorissanen/Desktop/Transactions.csv"
  ```

- **`start_date`** (valinnainen): Suodata tapahtumat tämän päivämäärän jälkeen
  ```python
  start_date = '2025-01-01'  # Oletusarvo
  ```

- **`save_excel`** (valinnainen): Tallenna Exceliin
  ```python
  save_excel = True  # Oletusarvo: True
  ```

- **`verbose`** (valinnainen): Näytä yksityiskohtaiset viestit
  ```python
  verbose = True  # Oletusarvo: False
  ```

### Esimerkki kaikilla parametreilla:

```python
df = process_file(
    csv_path="/Users/juhorissanen/Desktop/Transactions.csv",
    start_date='2025-01-01',
    save_excel=True,
    verbose=True
)
```

---

## Tarkistus: Onnistuiko prosessi?

### 1. Tarkista konsoliviestit

Jos `verbose=True`, näet yksityiskohtaiset viestit:
```
🔄 Processing file: /Users/juhorissanen/Desktop/Transactions.csv
📊 Loaded 987 rows
🧹 Cleaned data: 987 rows
💰 Applied cost allocation
🏷️ Categorized data
💾 Saved to Excel: /Users/juhorissanen/OneDrive/kulutus.xlsx
✅ Processing complete!
```

### 2. Tarkista Excel-tiedosto

Avaa Excel-tiedosto ja tarkista:
- Onko dataa?
- Näkyvätkö kategoriat oikein?
- Onko adjusted_amount-sarake oikein?

### 3. Tarkista Python-muuttuja

```python
# Tarkista että DataFrame ei ole tyhjä
print(f"Rivejä: {len(df)}")
print(f"Sarakkeita: {len(df.columns)}")
print(f"Kategoriat: {df['category'].unique()}")
```

---

## Yleisimmät ongelmat ja ratkaisut

### Ongelma: "FileNotFoundError"

**Syy:** CSV-tiedosto ei löydy

**Ratkaisu:**
```python
from src.config import DEFAULT_CSV_PATH
import os

# Tarkista että tiedosto on olemassa
if os.path.exists(DEFAULT_CSV_PATH):
    print("✅ Tiedosto löytyy")
else:
    print(f"❌ Tiedosto ei löydy: {DEFAULT_CSV_PATH}")
    print("Muokkaa polkua src/config.py -tiedostossa")
```

### Ongelma: "KeyError: 'date'"

**Syy:** CSV-tiedoston rakenne ei vastaa odotettua

**Ratkaisu:**
- Tarkista että CSV-tiedosto on Curve-vienti
- Tarkista että sarakkeet ovat oikein (Date, Merchant, Amount, jne.)

### Ongelma: Excel-tiedosto ei tallennu

**Syy:** Polku Excel-tiedostoon on virheellinen tai ei ole kirjoitusoikeuksia

**Ratkaisu:**
```python
from src.config import DEFAULT_EXCEL_PATH
import os

# Tarkista että hakemisto on olemassa
excel_dir = os.path.dirname(DEFAULT_EXCEL_PATH)
if not os.path.exists(excel_dir):
    os.makedirs(excel_dir)
    print(f"✅ Luotiin hakemisto: {excel_dir}")
```

---

## Esimerkki: Täydellinen skripti

Luo tiedosto `run_pipeline.py`:

```python
#!/usr/bin/env python3
"""Complete pipeline runner with error handling."""

import sys
from pathlib import Path

# Lisää src-hakemisto polkuun
sys.path.insert(0, str(Path(__file__).parent))

from src.pipeline import process_file
from src.config import DEFAULT_CSV_PATH, DEFAULT_EXCEL_PATH
import os

def main():
    """Run the complete pipeline."""
    
    print("=" * 60)
    print("💰 Finance Transaction Pipeline")
    print("=" * 60)
    
    # Tarkista että CSV-tiedosto on olemassa
    if not os.path.exists(DEFAULT_CSV_PATH):
        print(f"❌ Virhe: CSV-tiedosto ei löydy!")
        print(f"   Polku: {DEFAULT_CSV_PATH}")
        print(f"\n💡 Vinkki: Muokkaa polkua src/config.py -tiedostossa")
        return 1
    
    print(f"\n📂 CSV-tiedosto: {DEFAULT_CSV_PATH}")
    print(f"💾 Excel-tiedosto: {DEFAULT_EXCEL_PATH}")
    
    try:
        # Aja pipeline
        print("\n🔄 Aloitetaan prosessointi...")
        df = process_file(
            csv_path=DEFAULT_CSV_PATH,
            start_date='2025-01-01',
            save_excel=True,
            verbose=True
        )
        
        # Näytä tulokset
        print("\n" + "=" * 60)
        print("✅ Pipeline valmis!")
        print("=" * 60)
        print(f"📊 Käsiteltyjä rivejä: {len(df)}")
        print(f"📅 Aikaväli: {df['date'].min()} - {df['date'].max()}")
        print(f"💰 Kokonaissumma: €{df['adjusted_amount'].sum():,.2f}")
        print(f"📈 Kategorioita: {df['category'].nunique()}")
        print(f"🏪 Kauppoja: {df['merchant'].nunique()}")
        print(f"💾 Tallennettu: {DEFAULT_EXCEL_PATH}")
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Virhe prosessoinnissa: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

Aja skripti:
```bash
python run_pipeline.py
```

---

## Yhteenveto

**Nopein tapa ajaa pipeline:**

**Vaihtoehto 1: Käytä shell-skriptiä (helpoin)**
```bash
./run_pipeline.sh
```

**Vaihtoehto 2: Aktivoi virtuaaliympäristö ja aja Python-skripti**
```bash
source venv/bin/activate
python run_pipeline.py
```

**Vaihtoehto 3: Python-komento suoraan**
```python
from src.pipeline import process_file
from src.config import DEFAULT_CSV_PATH
df = process_file(DEFAULT_CSV_PATH, save_excel=True, verbose=True)
```

**Täydellinen prosessi:**
1. CSV-tiedosto → Lataus
2. → Siivous
3. → Kustannusjakojen käsittely
4. → Kategorisointi
5. → Tallennus Exceliin
6. ✅ Valmis!

**Seuraava askel:**
- Avaa Streamlit-sovellus: `streamlit run app/main.py`
- Tai käytä Jupyter Notebookia analysoimaan dataa

