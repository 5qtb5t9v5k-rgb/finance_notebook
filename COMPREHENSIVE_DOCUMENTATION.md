# Finance Transaction Manager - Kattava Dokumentaatio

## Sisällys

1. [Yleiskuvaus](#yleiskuvaus)
2. [Asennus ja Käyttöönotto](#asennus-ja-käyttöönotto)
3. [Projektin Rakenne](#projektin-rakenne)
4. [Arkkitehtuuri](#arkkitehtuuri)
5. [Käyttöohjeet](#käyttöohjeet)
6. [API ja Moduulit](#api-ja-moduulit)
7. [Konfiguraatio](#konfiguraatio)
8. [AI Assistant](#ai-assistant)
9. [Ongelmanratkaisu](#ongelmanratkaisu)
10. [Kehitysohjeet](#kehitysohjeet)

---

## Yleiskuvaus

**Finance Transaction Manager** on kattava järjestelmä rahoitustapahtumien käsittelyyn, analysointiin ja visualisointiin. Se on suunniteltu käsittelemään Curve-sovelluksesta vietäviä CSV-tiedostoja, mutta se tukee myös muita CSV-muotoisia tapahtumatietoja.

### Pääominaisuudet

- 📊 **Automaattinen datan käsittely**: Pipeline käsittelee CSV-tiedostot alusta loppuun
- 🧹 **Datan siivous**: Poistaa duplikaatit, validoi ja korjaa virheet
- 📂 **Automaattinen luokittelu**: Luokittelee tapahtumat kategorioihin ja alakategorioihin
- 💰 **Kustannusjako**: Tukee prosenttiosuus-pohjaista kustannusjakoa
- 📈 **Interaktiivinen dashboard**: Streamlit-pohjainen web-käyttöliittymä
- 🤖 **AI Assistant**: Kysy kysymyksiä rahoitustapahtumistasi (vapaaehtoinen)
- 📉 **Analytiikka**: Syvällinen kulutusanalyysi ja trendit
- 💾 **Budjetointi**: Aseta ja seuraa budjetteja
- 🔄 **Toistuvat kulut**: Automaattinen tunnistus toistuvista tapahtumista
- 📊 **Ennusteet**: Trendipohjaiset kulutusennusteet

---

## Asennus ja Käyttöönotto

### Vaatimukset

- Python 3.11 tai uudempi
- pip (Python package manager)
- Virtual environment (suositeltu)

### Asennusvaiheet

1. **Kloonaa tai lataa projekti**

```bash
cd /path/to/finance_notebook
```

2. **Luo virtuaaliympäristö**

```bash
python3 -m venv venv
```

3. **Aktivoi virtuaaliympäristö**

```bash
# macOS/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

4. **Asenna riippuvuudet**

```bash
pip install -r requirements.txt
```

5. **Konfiguroi ympäristömuuttujat (vapaaehtoinen)**

Luo `.env`-tiedosto projektin juureen:

```env
OPENAI_API_KEY=your_api_key_here
```

**Huomio**: AI Assistant -ominaisuus vaatii OpenAI API-avaimen. Ilman sitä muut ominaisuudet toimivat normaalisti.

### Käynnistys

#### Tapa 1: Käynnistä kaikki yhdellä komennolla (suositeltu)

```bash
./run_all.sh
```

Tämä:
- Aktivoi virtuaaliympäristön
- Ajaa pipeline-tiedostot
- Käynnistää Streamlit-sovelluksen

#### Tapa 2: Käynnistä manuaalisesti

```bash
# Aktivoi virtuaaliympäristö
source venv/bin/activate

# Aja pipeline (valinnainen)
python run_pipeline.py

# Käynnistä Streamlit
streamlit run app/main.py
```

Sovellus avautuu automaattisesti selaimessa osoitteessa `http://localhost:8501`

---

## Projektin Rakenne

```
finance_notebook/
├── app/                          # Streamlit-sovellus
│   ├── main.py                  # Pääsovellus (Dashboard, Analytics, jne.)
│   ├── ai_assistant.py          # AI Assistant -välilehti
│   └── components/              # Uudelleenkäytettävät komponentit
├── src/                         # Pipeline-moduulit
│   ├── config.py                # Konfiguraatio ja määritykset
│   ├── data_loader.py           # CSV-tiedostojen lataus
│   ├── data_cleaner.py          # Datan siivous ja validointi
│   ├── categorizer.py           # Automaattinen luokittelu
│   ├── cost_allocator.py        # Kustannusjako
│   ├── pipeline.py              # Pääorchestrator
│   ├── data_formatter.py        # LLM:lle datan muotoilu
│   ├── llm_client.py            # OpenAI API -asiakas
│   ├── vector_store.py          # ChromaDB vektoritietokanta
│   ├── ai_router.py             # AI-kysymysten reititin
│   ├── ai_tools.py              # AI-työkalut
│   └── ai_assistant_agent.py    # AI-agentti
├── data/                        # Datatiedostot
│   ├── raw/                     # Alkuperäiset CSV-tiedostot
│   └── processed/               # Käsitellyt tiedostot
│       └── vector_db/           # ChromaDB vektoritietokanta
├── notebooks/                   # Jupyter-notebookit
│   └── exploration.ipynb        # Datan tutkiminen
├── run_all.sh                   # Käynnistysskripti
├── run_pipeline.py              # Pipeline-ajoscripti
├── requirements.txt             # Python-riippuvuudet
├── .env                         # Ympäristömuuttujat (luo itse)
└── README.md                    # Projektin README
```

---

## Arkkitehtuuri

### Pipeline-malli

Järjestelmä käyttää **pipeline-mallia**, jossa data käsitellään vaihe vaiheelta:

```
CSV-tiedosto
    ↓
[Data Loader]     → Lataa CSV-tiedosto
    ↓
[Data Cleaner]    → Siivoaa ja validoi
    ↓
[Cost Allocator]  → Laske kustannusjako
    ↓
[Categorizer]     → Luokittele kategoriat
    ↓
[Data Formatter]  → Muotoile LLM:lle (vapaaehtoinen)
    ↓
[Vector Store]    → Tallenna vektoreihin (vapaaehtoinen)
    ↓
Valmis DataFrame
```

### Streamlit-sovellus

Sovellus on jaettu välilehtiin:

1. **📊 Dashboard**: Yleiskuva kulutuksesta, metriikat, kuvaajat
2. **📈 Analytics**: Syvällinen analyysi, trendit, vertailut
3. **📋 Transactions**: Tapahtumalista, suodatus, muokkaus
4. **✏️ Edit Categories**: Kategorioiden muokkaus
5. **💰 Budget**: Budjettien asetus ja seuranta
6. **🤖 AI Assistant**: Kysy kysymyksiä rahoitustapahtumistasi

### Data Flow

1. **CSV Upload**: Käyttäjä lataa CSV-tiedoston Streamlit-sovellukseen
2. **Processing**: Pipeline käsittelee datan
3. **Session State**: Data tallennetaan Streamlitin session stateen
4. **Visualization**: Data näytetään dashboardissa ja analytiikassa
5. **AI Analysis**: Vapaaehtoisesti data voidaan analysoida AI:lla

---

## Käyttöohjeet

### CSV-tiedoston lataus

1. Avaa Streamlit-sovellus
2. Siirry sidebariin
3. Klikkaa "Upload CSV File"
4. Valitse CSV-tiedosto
5. Data käsitellään automaattisesti

### Dashboard-välilehti

Dashboard näyttää:
- **Kokonaiskulutus**: Yhteensä kulutettu raha
- **Keskimääräinen/Mediaanikulutus**: Kuukausittaiset tilastot
- **Kuukausittainen kulutuskuvaaja**: Trendit ajan kuluessa
- **Kategoriajako**: Kulutus kategorioittain
- **Kuukausittaiset yksityiskohdat**: Yksityiskohtaiset tiedot kuukausittain
- **Kulutusyhteenveto**: Taulukko kategorioista ja kuukausista
- **Kulutusennuste**: Trendipohjainen ennuste

### Analytics-välilehti

Analytics tarjoaa:

#### Period Comparison
- **Previous Month**: Vertaa edelliseen kuukauteen
- **Select Months**: Valitse kaksi kuukautta vertailuun
- **Same Period Last Year**: Vertaa samaan ajanjaksoon vuosi sitten

#### Category Spending Trends
- Kategoriajako kuukausittain
- Trendit ajan kuluessa
- Vertailut eri ajanjaksojen välillä

#### Waterfall Chart
- Näyttää kulutusmuutokset kategorioittain
- Positiiviset ja negatiiviset muutokset

#### Savings Opportunities
- Automaattinen tunnistus säästömahdollisuuksista
- Kategoriat, joissa kulutus on poikkeuksellisen korkea

#### Recurring Expenses
- Automaattinen tunnistus toistuvista tapahtumista
- Suodatus kategorioittain
- Top 15 toistuvinta kulutusta

#### AI-Powered Insights
- Generoi älykkäitä oivalluksia valitusta ajanjaksosta
- Sisältää merchantit, jotka selittävät kulutuksen nousua

### Transactions-välilehti

- **Suodatus**: Suodata päivämäärän, kategorian, merchantin tai summan mukaan
- **Haku**: Etsi tapahtumia tekstillä
- **Muokkaus**: Muokkaa kategorioita ja muistiinpanoja
- **Näytä sarakkeet**: Valitse näytettävät sarakkeet

### Edit Categories-välilehti

- Muokkaa kategorioita ja alakategorioita
- Muutokset tallennetaan session stateen

### Budget-välilehti

- Aseta budjetteja kategorioittain
- Seuraa budjettien toteutumista
- Saat hälytyksiä, jos budjetti ylittyy

### AI Assistant-välilehti

Kysy kysymyksiä rahoitustapahtumistasi suomeksi tai englanniksi:

- "Mikä on viimeisin tapahtuma?"
- "Paljonko käytin Prismassa viime kuussa?"
- "Mitä kategorioita käytin eniten?"
- "Näytä kaikki tapahtumat viime kuusta"

**Huomio**: AI Assistant vaatii OpenAI API-avaimen. Katso [AI_ASSISTANT_SETUP.md](AI_ASSISTANT_SETUP.md) lisätietoja.

---

## API ja Moduulit

### Pipeline-moduulit

#### `src/config.py`

Konfiguraatiotiedosto, joka sisältää:
- Kategoriamääritykset
- Käännökset (EN → FI)
- Tiedostopolut
- Korttimääritykset

**Käyttö**:
```python
from src.config import CATEGORY_EN_TO_FI, DEFAULT_CSV_PATH
```

#### `src/data_loader.py`

CSV-tiedostojen lataus ja alustava käsittely.

**Pääfunktiot**:
- `load_transactions_csv(path)`: Lataa CSV-tiedosto
- `initial_cleanup(df)`: Alustava siivous
- `standardize_column_names(df)`: Standardisoi sarakkeiden nimet

#### `src/data_cleaner.py`

Datan siivous ja validointi.

**Pääfunktiot**:
- `clean_data(df, start_date=None)`: Siivoaa datan
  - Poistaa duplikaatit
  - Validoi päivämäärät
  - Suodattaa virheelliset rivit

#### `src/cost_allocator.py`

Kustannusjako-prosentin erottaminen muistiinpanoista.

**Pääfunktiot**:
- `apply_cost_allocation(df)`: Soveltaa kustannusjakoa
  - Etsii muistiinpanoista `"/XX%"` muotoa
  - Laskee `adjusted_amount` = `amount * (percentage / 100)`

**Muistiinpanomuoto**: `"F/50%"` → 50% kustannusjako

#### `src/categorizer.py`

Automaattinen luokittelu kategorioihin ja alakategorioihin.

**Pääfunktiot**:
- `categorize_data(df, verbose=False)`: Luokittelee datan
  - Käyttää merchant-nimeä ja muistiinpanoja
  - Määrittää kategorian ja alakategorian

#### `src/pipeline.py`

Pääorchestrator, joka yhdistää kaikki moduulit.

**Pääfunktiot**:
- `process_file(csv_path, start_date=None, verbose=True)`: Käsittelee yhden tiedoston
- `process_new_files(directory=None, verbose=True)`: Automaattisesti käsittelee uudet tiedostot
- `process_dataframe(df, start_date=None, verbose=True)`: Käsittelee DataFramein suoraan

**Esimerkki**:
```python
from src.pipeline import process_file

df = process_file('path/to/transactions.csv', start_date='2025-01-01')
```

### AI-moduulit

#### `src/llm_client.py`

OpenAI API -asiakas.

**Pääfunktiot**:
- `get_llm_response(messages, api_key, model="gpt-4o-mini")`: Lähettää viestin LLM:lle

#### `src/vector_store.py`

ChromaDB vektoritietokanta RAG:lle.

**Pääfunktiot**:
- `initialize_vector_store()`: Alustaa vektoritietokannan
- `add_transactions(df)`: Lisää tapahtumat vektoreihin
- `search_transactions(query, n_results=5)`: Etsii tapahtumia semanttisesti

#### `src/ai_router.py`

Reitittää AI-kysymykset oikeille työkaluille.

**Pääfunktiot**:
- `route_query(query, df)`: Reitittää kysymyksen

#### `src/ai_tools.py`

AI-työkalut tapahtumien analysointiin.

**Pääfunktiot**:
- `tool_sum_by_merchant(df, merchant_substr, ...)`: Summaa merchantin mukaan
- `tool_sum_by_category(df, category, ...)`: Summaa kategorian mukaan
- `tool_top_transactions(df, n=10, ...)`: Top N tapahtumaa

#### `app/ai_assistant.py`

AI Assistant -välilehden toteutus.

**Pääfunktiot**:
- `render_ai_assistant_tab(df)`: Renderöi AI Assistant -välilehden

---

## Konfiguraatio

### Ympäristömuuttujat

Luo `.env`-tiedosto projektin juureen:

```env
OPENAI_API_KEY=sk-...
```

### Tiedostopolut

Muokkaa `src/config.py` tiedostoa:

```python
DEFAULT_CSV_PATH = "/path/to/your/transactions.csv"
DEFAULT_EXCEL_PATH = "/path/to/your/output.xlsx"
```

### Kategoriat

Muokkaa `src/config.py` tiedostoa:

```python
CATEGORY_EN_TO_FI = {
    "Groceries": "Ruokakauppa",
    "Shopping": "Ostokset",
    # ... lisää kategorioita
}
```

### Korttimääritykset

Muokkaa `src/config.py` tiedostoa:

```python
CARD_MAPPINGS = {
    "crypto.com": "crypto.com",
    "norwegian": "norwegian",
    # ... lisää kortteja
}
```

---

## AI Assistant

### Asennus

1. Hae OpenAI API-avain: https://platform.openai.com/api-keys
2. Lisää `.env`-tiedostoon:
   ```env
   OPENAI_API_KEY=sk-...
   ```
3. Käynnistä sovellus uudelleen

### Käyttö

AI Assistant tukee monenlaisia kysymyksiä:

#### Tarkat kysymykset (deterministiset)
- "Mikä on viimeisin tapahtuma?"
- "Toiseksi viimeinen tapahtuma?"
- "Paljonko käytin Prismassa viime kuussa?"

#### Analyysikysymykset
- "Mitä kategorioita käytin eniten?"
- "Näytä kaikki tapahtumat viime kuusta"
- "Mikä on suurin yksittäinen ostos?"

#### Suhteelliset ajanjaksot
- "Viime kuukausi"
- "Viime 30 päivää"
- "Tänä vuonna"

### RAG (Retrieval-Augmented Generation)

AI Assistant käyttää RAG-tekniikkaa:
1. Kysymys muunnetaan vektoreiksi
2. Etsitään relevantit tapahtumat vektoritietokannasta
3. Lähetetään relevantit tapahtumat LLM:lle
4. LLM generoi vastauksen

### Router-Executor-Narrator -arkkitehtuuri

1. **Router**: Määrittää, mitä työkalua käytetään
2. **Executor**: Suorittaa työkalun (Pandas)
3. **Narrator**: LLM selittää tulokset

Tämä varmistaa tarkkuuden tarkkojen kysymysten kohdalla.

### Kustannukset

AI Assistant käyttää `gpt-4o-mini` mallia oletuksena (halvin vaihtoehto). Katso [AI_ASSISTANT_SETUP.md](AI_ASSISTANT_SETUP.md) lisätietoja kustannuksista.

---

## Ongelmanratkaisu

### Streamlit ei käynnisty

**Ongelma**: `streamlit run app/main.py` ei toimi

**Ratkaisu**:
```bash
# Varmista, että virtuaaliympäristö on aktivoitu
source venv/bin/activate

# Käytä run_all.sh skriptiä
./run_all.sh
```

### OpenAI-paketti ei löydy

**Ongelma**: `Error: OpenAI package is not installed`

**Ratkaisu**:
```bash
# Varmista, että virtuaaliympäristö on aktivoitu
source venv/bin/activate

# Asenna OpenAI
pip install openai

# Käynnistä Streamlit uudelleen käyttäen venv:n Pythonia
./run_all.sh
```

### CSV-tiedosto ei lataudu

**Ongelma**: CSV-tiedosto ei näy sovelluksessa

**Ratkaisu**:
1. Tarkista, että tiedosto on CSV-muodossa
2. Tarkista, että tiedostossa on oikeat sarakkeet
3. Kokeile ladata tiedosto suoraan Streamlit-sovellukseen

### AI Assistant ei vastaa

**Ongelma**: AI Assistant ei vastaa kysymyksiin

**Ratkaisu**:
1. Tarkista, että `.env`-tiedosto sisältää `OPENAI_API_KEY`
2. Tarkista, että API-avain on voimassa
3. Tarkista debug-tiedot (laajenna "🔍 Debug Info")

### Data ei näy Dashboardissa

**Ongelma**: Dashboard on tyhjä

**Ratkaisu**:
1. Lataa CSV-tiedosto ensin
2. Tarkista, että data on käsitelty (tarkista Transactions-välilehti)
3. Päivitä sivu (F5)

---

## Kehitysohjeet

### Uusien kategorioiden lisääminen

1. Avaa `src/config.py`
2. Lisää kategoria `CATEGORY_EN_TO_FI` sanakirjaan:
   ```python
   CATEGORY_EN_TO_FI = {
       # ... olemassa olevat
       "New Category": "Uusi Kategoria",
   }
   ```
3. Lisää luokittelu `src/categorizer.py` tiedostoon

### Uusien visualisointien lisääminen

1. Avaa `app/main.py`
2. Etsi sopiva välilehti (esim. Analytics)
3. Lisää uusi visualisointi käyttäen Plotlyä:
   ```python
   import plotly.express as px
   
   fig = px.bar(df, x='category', y='amount')
   st.plotly_chart(fig)
   ```

### Uusien AI-työkalujen lisääminen

1. Avaa `src/ai_tools.py`
2. Lisää uusi työkalu:
   ```python
   def tool_new_tool(df: pd.DataFrame, param: str) -> Dict[str, Any]:
       # Toteuta työkalu
       return {"result": "..."}
   ```
3. Lisää työkalu `src/ai_router.py` tiedostoon

### Testaus

Testaa uudet ominaisuudet:

```python
# Testaa pipeline-moduulia
from src.pipeline import process_file
df = process_file('test.csv')

# Testaa Streamlit-sovellusta
streamlit run app/main.py
```

---

## Lisätietoja

- **README.md**: Projektin peruskuvaus
- **ARCHITECTURE.md**: Arkkitehtuurin yksityiskohdat
- **DOCUMENTATION.md**: Yksityiskohtainen dokumentaatio
- **PIPELINE_GUIDE.md**: Pipeline-ajon ohje
- **AI_ASSISTANT_SETUP.md**: AI Assistant -asetusohje
- **WORKFLOW.md**: Työnkulku

---

## Tuki ja Kontribuutio

Jos kohtaat ongelmia tai sinulla on kysymyksiä:

1. Tarkista tämä dokumentaatio
2. Tarkista muut dokumentaatiotiedostot
3. Tarkista debug-tiedot sovelluksessa

---

**Viimeksi päivitetty**: 2025-01-XX
**Versio**: 1.0.0

