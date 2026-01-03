# Finance Transaction Pipeline - Täydellinen Dokumentaatio

## Sisällys

1. [Yleiskuvaus](#yleiskuvaus)
2. [Selkokielinen Rakennuskuvaus](#selkokielinen-rakennuskuvaus)
3. [Arkkitehtuuri](#arkkitehtuuri)
4. [Data Flow - Miten data liikkuu](#data-flow)
5. [Moduulien Yksityiskohtainen Selitys](#moduulien-yksityiskohtainen-selitys)
6. [Streamlit-sovelluksen Toiminta](#streamlit-sovelluksen-toiminta)
7. [Käyttöohjeet](#käyttöohjeet)
8. [Visualisointien Selitys](#visualisointien-selitys)

---

## Yleiskuvaus

Tämä järjestelmä käsittelee Curve-sovelluksesta viedyt tapahtumatiedot. Se:
- Lataa CSV-tiedoston
- Siivoaa ja validoi datan
- Luokittelee tapahtumat kategorioihin ja alakategorioihin
- Kääntää kategoriat suomeksi
- Laskee kustannusjakoja (jos käytössä)
- Tallentaa lopputuloksen Exceliin
- Tarjoaa Streamlit-sovelluksen datan katseluun, muokkaamiseen ja visualisointiin

---

## Selkokielinen Rakennuskuvaus

### Miten järjestelmä on rakennettu?

Järjestelmä on rakennettu **modulaarisesti**, eli se on jaettu selkeisiin osiin, joista jokainen tekee oman työnsä. Tämä tekee järjestelmästä helpon ymmärtää, ylläpitää ja laajentaa.

### Ydinajatus: Pipeline-malli

Järjestelmä toimii kuin **tehdaspipeline**:
1. **Sisään tulee** raaka CSV-tiedosto (Curve-vienti)
2. **Jokainen vaihe käsittelee** dataa hieman lisää
3. **Lopulta ulos tulee** valmis, luokiteltu ja analysoitu data

### Kolme pääosaa

#### 1. **Pipeline-moduulit** (`src/`-hakemisto)
Nämä ovat "työntekijöitä", jotka käsittelevät dataa:

- **`config.py`** - "Asetukset-arkisto"
  - Sisältää kaikki määritykset: kategoriat, käännökset, tiedostopolut
  - Keskus, josta kaikki muut moduulit lukevat asetukset

- **`data_loader.py`** - "Lataaja"
  - Lataa CSV-tiedoston koneelle
  - Siivoaa alustavasti (poistaa lainausmerkit, ylimääräiset sarakkeet)

- **`data_cleaner.py`** - "Siivooja"
  - Poistaa duplikaatit
  - Suodattaa pois turhat tapahtumat (esim. palautukset)
  - Lisää vuosi- ja kuukausisarakkeet

- **`cost_allocator.py`** - "Kustannusjakolaskuri"
  - Etsii notes-sarakkeesta merkinnät kuten "/50%"
  - Laskee kuinka paljon tapahtumasta kuuluu sinulle
  - Esim. jos merkitset "Restaurant/50%", se laskee että puolet on sinun

- **`categorizer.py`** - "Luokittelija"
  - Katsoo notes-saraketta ja pääkategoriaa
  - Määrittää alakategorian (esim. "F" + "Entertainment" → "Perhe")
  - Kääntää kaiken suomeksi
  - Täyttää automaattisesti tyhjät kategoriat

- **`pipeline.py`** - "Orkestraattori"
  - Koordinoi kaikkia yllä olevia moduuleja
  - Kutsuu niitä oikeassa järjestyksessä
  - Hoitaa tiedostojen automaattisen tunnistuksen

#### 2. **Streamlit-sovellus** (`app/main.py`)
Tämä on "käyttöliittymä", jota käytät selaimessa:

- **Dashboard-välilehti**
  - Näyttää yleiskuvan: kokonaissummat, keskiarvot, top-kategoriat
  - Interaktiiviset kaaviot, joihin voi klikata
  - Kuukausittainen kulutustrendi keskiarvoviivalla
  - Kategorian valinta näyttää sen detaljit

- **Transactions-välilehti**
  - Taulukko kaikista tapahtumista
  - Suodattimet: kategoria, kauppa, päivämäärä

- **Edit Categories-välilehti**
  - Mahdollistaa kategorioiden ja notes-sarakkeen muokkaamisen
  - Laskee kustannusjakot automaattisesti uudelleen

- **Analytics-välilehti**
  - Syvällisempiä analyysejä: trendit, vertailut, jakaumat

#### 3. **Jupyter Notebook** (`notebooks/exploration.ipynb`)
Tämä on "tutkimuslaboratorio":
- Käytät sitä kun haluat tehdä nopeita kokeiluja
- Voit testata uusia ideoita ilman että muutat pääkoodia
- Käyttää samoja pipeline-moduuleja kuin Streamlit-sovellus

### Miten data liikkuu?

```
1. CSV-tiedosto (työpöytä)
   ↓
2. data_loader.py → Lataa ja alustava siivous
   ↓
3. data_cleaner.py → Poistaa duplikaatit, suodattaa
   ↓
4. cost_allocator.py → Laskee kustannusjakot
   ↓
5. categorizer.py → Luokittelee ja kääntää
   ↓
6. pipeline.py → Tallentaa Exceliin
   ↓
7. Streamlit-sovellus → Näyttää ja mahdollistaa muokkauksen
```

### Miksi modulaarinen rakenne?

**Hyödyt:**
- **Helppo ymmärtää**: Jokainen moduuli tekee yhden asian hyvin
- **Helppo testata**: Voit testata jokaisen moduulin erikseen
- **Helppo muokata**: Muutat vain yhtä moduulia kerrallaan
- **Helppo laajentaa**: Lisäät uuden moduulin ilman että muutat vanhoja

**Esimerkki:**
Jos haluat muuttaa kategoriamäärityksiä, muokkaat vain `config.py`-tiedostoa. Muut moduulit käyttävät automaattisesti uusia määrityksiä.

---

## Arkkitehtuuri

```
finance_notebook/
├── src/                    # Pipeline-moduulit (ydinlogiikka)
│   ├── config.py          # Asetukset ja määritykset
│   ├── data_loader.py     # CSV-tiedoston lataus
│   ├── data_cleaner.py    # Datan siivous
│   ├── categorizer.py     # Kategorisointi
│   ├── cost_allocator.py  # Kustannusjakojen käsittely
│   └── pipeline.py        # Orchestrator (koordinoi kaiken)
├── app/                    # Streamlit-sovellus
│   └── main.py           # Web-käyttöliittymä
├── notebooks/              # Jupyter-notebookit
│   └── exploration.ipynb # Interaktiivinen analyysi
└── data/                   # Data-tiedostot
    ├── raw/              # Alkuperäiset CSV-tiedostot
    └── processed/        # Käsitellyt Excel-tiedostot
```

---

## Data Flow

### 1. CSV-tiedoston Lataus
```
CSV-tiedosto (työpöytä tai data/raw/)
    ↓
data_loader.py
    ↓
Alustava siivous (poistaa lainausmerkit, ylimääräiset sarakkeet)
```

### 2. Datan Siivous
```
Siivomaton data
    ↓
data_cleaner.py
    ├─→ Päivämäärän muunnos
    ├─→ Päivämääräsuodatus (alkaen 2025-01-01)
    ├─→ Duplikaattien poisto
    ├─→ Ylimääräisten rivien poisto
    └─→ Vuosi/kuukausi-sarakkeiden lisäys
```

### 3. Kustannusjakojen Käsittely
```
Siivottu data
    ↓
cost_allocator.py
    ├─→ Etsii notes-sarakkeesta "/50%" -tyyppisiä merkintöjä
    ├─→ Poimii prosenttiosuuden (esim. 50% → 0.5)
    ├─→ Poistaa prosenttiosuuden notes-sarakkeesta
    └─→ Laskee adjusted_amount = amount × cost_allocation
```

### 4. Kategorisointi
```
Data kustannusjakojen kanssa
    ↓
categorizer.py
    ├─→ Lisää 2nd category notes-sarakkeen perusteella
    ├─→ Kääntää kategoriat englanniksi → suomeksi
    ├─→ Täyttää tyhjät 2nd category -arvot säännöillä
    ├─→ Muuttaa alakategorian nimet muotoon "Pääkategoria: Alakategoria"
    └─→ Validoi että kaikki kategoriat on täytetty
```

### 5. Tallennus
```
Valmis data
    ↓
pipeline.py → save_to_excel()
    ↓
Excel-tiedosto (OneDrive/kulutus.xlsx)
```

### 6. Näyttäminen
```
Excel-tiedosto
    ↓
Streamlit-sovellus
    ├─→ Dashboard (tilastot ja kaaviot)
    ├─→ Transactions (taulukko)
    ├─→ Edit Categories (muokkaus)
    └─→ Analytics (analyysit)
```

---

## Moduulien Yksityiskohtainen Selitys

### `src/config.py` - Asetukset ja Määritykset

**Mitä se tekee:**
- Määrittelee kaikki polut (CSV, Excel)
- Sisältää korttien määritykset (card_last4 → kortin nimi)
- Sisältää kategoriamääritykset (pääkategoria → alakategoria)
- Sisältää käännökset (englanti → suomi)
- Sisältää säännöt tyhjien kategorioiden täyttämiseen

**Tärkeimmät muuttujat:**
- `DEFAULT_CSV_PATH`: Missä CSV-tiedosto sijaitsee
- `DEFAULT_EXCEL_PATH`: Minne Excel-tiedosto tallennetaan
- `CARD_MAPPING`: Korttinumeroiden määritykset
- `CATEGORY_MAPPING`: Kategoriamääritykset (esim. 'Entertainment' → {'F': 'Family'})
- `CATEGORY_EN_TO_FI`: Käännökset suomeksi
- `EMPTY_2ND_CATEGORY_RULES`: Säännöt tyhjien kategorioiden täyttämiseen
- `GENERAL_2ND_CATEGORIES`: Kategoriat, jotka saavat "Yleinen" -alakategorian

**Esimerkki:**
```python
# Jos notes-sarakkeessa on "F" ja category on "Entertainment"
# → 2nd category = "Perhe"
```

---

### `src/data_loader.py` - CSV-tiedoston Lataus

**Mitä se tekee:**
1. Lataa CSV-tiedoston pandasilla
2. Poistaa lainausmerkit Merchant- ja Notes-sarakkeista
3. Poistaa ylimääräiset sarakkeet
4. Nimeää sarakkeet uudelleen (standardoi)
5. Käsittelee korttinumerot ja mappaa ne korttien nimiin

**Funktiot:**
- `load_transactions_csv()`: Lataa CSV-tiedoston
- `initial_cleanup()`: Alustava siivous
- `standardize_column_names()`: Standardoi sarakkeiden nimet
- `process_card_numbers()`: Käsittelee korttinumerot
- `load_and_prepare_data()`: Suorittaa kaikki yllä olevat vaiheet

**Esimerkki muunnoksesta:**
```
"Date (YYYY-MM-DD as UTC)" → "date"
"Txn Amount (Funding Card)" → "amount"
"Card Last 4 Digits" → "card_last4"
```

---

### `src/data_cleaner.py` - Datan Siivous

**Mitä se tekee:**
1. Muuntaa päivämääräsarakkeen datetime-muotoon
2. Suodattaa tapahtumat päivämäärän mukaan (alkaen 2025-01-01)
3. Poistaa duplikaatit (sama merchant, päivämäärä ja summa)
4. Poistaa ylimääräisiä rivejä (REFUNDED, " del", tiettyjä valuuttoja)
5. Lisää vuosi- ja kuukausisarakkeet

**Funktiot:**
- `convert_date_column()`: Muuntaa päivämäärän
- `filter_by_date()`: Suodattaa päivämäärän mukaan
- `remove_duplicates()`: Poistaa duplikaatit (pitää viimeisen)
- `apply_filters()`: Poistaa ylimääräisiä rivejä
- `add_date_columns()`: Lisää vuosi/kuukausi-sarakkeet
- `clean_data()`: Suorittaa kaikki vaiheet

**Duplikaattien poisto:**
- Etsii rivejä, joilla on sama merchant, date ja amount
- Pitää viimeisen esiintymän (ajan mukaan järjestettynä)
- Tulostaa poistetut rivit konsoliin

---

### `src/cost_allocator.py` - Kustannusjakojen Käsittely

**Mitä se tekee:**
1. Etsii notes-sarakkeesta "/50%" -tyyppisiä merkintöjä
2. Poimii prosenttiosuuden (esim. "Restaurant/50%" → 0.5)
3. Poistaa prosenttiosuuden notes-sarakkeesta
4. Laskee adjusted_amount = amount × cost_allocation

**Funktiot:**
- `extract_cost_allocation()`: Poimii prosenttiosuuden notes-sarakkeesta
- `apply_cost_allocation()`: Soveltaa kustannusjakoa kaikille riveille

**Esimerkki:**
```
Ennen: notes = "Restaurant/50%", amount = 100€
Jälkeen: notes = "Restaurant", cost_allocation = 0.5, adjusted_amount = 50€
```

**Käyttötapaus:**
Jos jaat kulut puoliksi, merkitset notes-sarakkeeseen "/50%". 
Systeemi laskee automaattisesti oikean summan adjusted_amount-sarakkeeseen.

---

### `src/categorizer.py` - Kategorisointi

**Mitä se tekee:**
1. Lisää 2nd category -sarakkeen notes-sarakkeen perusteella
2. Kääntää kategoriat englanniksi suomeksi
3. Täyttää tyhjät 2nd category -arvot säännöillä
4. Muuttaa alakategorian nimet muotoon "Pääkategoria: Alakategoria" (paitsi Autoilu & Liikkuminen)

**Vaihe 1: 2nd category -sarakkeen lisäys**
- Katsoo notes-saraketta (esim. "F", "P", "H")
- Katsoo category-saraketta (esim. "Entertainment", "Shopping")
- Etsii määrityksistä vastaavan alakategorian
- Esimerkki: notes="F", category="Entertainment" → 2nd category="Family"

**Vaihe 2: Käännös**
- Kääntää category-sarakkeen suomeksi
- Kääntää 2nd category -sarakkeen suomeksi
- Esimerkki: "Entertainment" → "Tapahtumat & Viihde"

**Vaihe 3: Tyhjien kategorioiden täyttäminen**
- Jos 2nd category on tyhjä, käytetään sääntöjä:
  - "Autoilu & Liikkuminen" → "Julkinen liikenne"
  - "Ostokset" → "Henkilökohtainen"
  - "Tapahtumat & Viihde" → "Henkilökohtainen"
  - Jne.
- Tietyt kategoriat saavat aina "Yleinen":
  - "Harrastukset" → "Harrastukset: Yleinen"
  - "Ruokakauppa" → "Ruokakauppa: Yleinen"
  - "Striimaus & Palvelut" → "Striimaus & Palvelut: Yleinen"
  - Jne.

**Vaihe 4: Alakategorian nimien muokkaus**
- Muuttaa "Perhe" → "Pääkategoria: Perhe" (esim. "Ostokset: Perhe")
- Muuttaa "Henkilökohtainen" → "Pääkategoria: Henkilökohtainen" (esim. "Terveys: Henkilökohtainen")
- Muuttaa "Yleinen" → "Pääkategoria: Yleinen" tietyissä kategorioissa
- Autoilu & Liikkuminen -kategorian alakategoriat pysyvät muuttumattomina

**Vaihe 5: Validointi**
- Tarkistaa että kaikilla tärkeillä kategorioilla on 2nd category
- Tulostaa varoituksen jos jokin puuttuu

**Funktiot:**
- `get_second_category()`: Hakee 2nd category -arvon
- `add_second_category()`: Lisää 2nd category -sarakkeen
- `translate_category()`: Kääntää kategorian suomeksi
- `translate_categories()`: Kääntää kaikki kategoriat
- `apply_empty_2nd_category_rules()`: Täyttää tyhjät kategoriat
- `customize_general_subcategory_names()`: Muuttaa alakategorian nimet
- `validate_categories()`: Validoi kategoriat
- `categorize_data()`: Suorittaa kaikki vaiheet

---

### `src/pipeline.py` - Orchestrator (Koordinoija)

**Mitä se tekee:**
- Koordinoi kaikkia moduuleja
- Käsittelee automaattisen tiedostojen tunnistuksen
- Tallentaa käsiteltyjä tiedostoja Exceliin
- Pitää kirjaa käsitellyistä tiedostoista

**Automaattinen tiedostojen tunnistus:**
1. Etsii CSV-tiedostoja `data/raw/` -hakemistosta
2. Tarkistaa `.processed_files.json` -tiedostosta, mitkä on jo käsitelty
3. Vertaa tiedostojen muokkausaikoja
4. Käsittelee vain uudet tai päivitetyt tiedostot

**Funktiot:**
- `process_transactions()`: Suorittaa koko pipeline-prosessin
- `process_file()`: Käsittelee yhden tiedoston
- `process_new_files()`: Käsittelee automaattisesti uudet tiedostot
- `load_processed_data()`: Lataa käsiteltyä dataa Excelistä
- `detect_new_files()`: Tunnistaa uudet tiedostot
- `save_to_excel()`: Tallentaa Exceliin

**Prosessin vaiheet:**
```
1. load_and_prepare_data()     # Lataa CSV
2. clean_data()                # Siivoaa datan
3. apply_cost_allocation()     # Käsittelee kustannusjakot
4. categorize_data()           # Luokittelee
5. save_to_excel()             # Tallentaa Exceliin
```

---

## Streamlit-sovelluksen Toiminta

### Yleisrakenne

Sovellus koostuu neljästä välilehdestä:
1. **Dashboard** - Yleiskuva, tilastot ja interaktiiviset kaaviot
2. **Transactions** - Tapahtumataulukko suodattimilla
3. **Edit Categories** - Kategorioiden ja notes-sarakkeen muokkaus
4. **Analytics** - Syvällisempiä analyysejä ja trendejä

### Käynnistyksen Vaiheet

1. **Lataa data**
   - Yrittää ladata Excel-tiedostosta
   - Jos Excel on tyhjä tai korruptoitunut, käsittelee CSV-tiedoston automaattisesti
   - Tallennaa datan session_stateen

2. **Tarkistaa uudet tiedostot**
   - Etsii uusia CSV-tiedostoja `data/raw/` -hakemistosta
   - Näyttää varoituksen jos löytyy uusia tiedostoja

3. **Näyttää dashboardin**
   - Laskee tilastot (kokonaissumma, kuukausikeskiarvo, mediaani, jne.)
   - Piirtää kaaviot

### Dashboard-välilehti

**Yläosa - Metriikit:**
- **Total Spending**: Kaikkien tapahtumien summa (adjusted_amount)
- **Avg Monthly**: Kuukausittainen keskiarvo
- **Median Monthly**: Kuukausittainen mediaani
- **Unique Merchants**: Eri kauppojen määrä
- **Top Card**: Eniten käytetty kortti

**Kuukausittainen kulutus:**
- Palkkikaavio joka kuukaudelle
- Punainen katkoviiva näyttää keskiarvokulutuksen
- Klikkaamalla kuukautta näet sen detaljit

**Kategorian valinta:**
- **Total Spending By Category**: Donut-tyyppinen piirakkakuvaaja
- **Subcategories**: Palkkikuvaaja kaikista subcategorioista (järjestetty suurimmasta pienimpään)
- **Monthly Average by Subcategory**: Koko sivun leveä palkkikuvaaja kuukausittaisista keskiarvoista
- **Select category for details**: Valitse kategoria nähdäksesi sen detaljit

**Kategorian detaljit (kun kategoria on valittu):**
- **Subcategories in [Category]**: Donut-tyyppinen piirakkakuvaaja alakategorioista
- **Top 10 Merchants**: Palkkikuvaaja top merchanneista
- **Metriikit**: Category Total, % of Total, Transactions, Monthly Average, Monthly Median
- **Monthly Trend**: Viivakaavio kuukausittaisesta trendistä
- **Monthly Average per Subcategory**: Palkkikuvaaja kuukausittaisista keskiarvoista subcategorioittain
- **Monthly Average per Merchant**: Palkkikuvaaja kuukausittaisista keskiarvoista merchantittain (sivun alimmaisena)

**Miten se laskee:**
```python
# Kokonaissumma
total = df['adjusted_amount'].sum()

# Kuukausikeskiarvo
avg_monthly = df.groupby(['year', 'month'])['adjusted_amount'].sum().mean()

# Kuukausimediaani
median_monthly = df.groupby(['year', 'month'])['adjusted_amount'].sum().median()

# Eri kaupat
unique_merchants = df['merchant'].nunique()
```

### Transactions-välilehti

**Mitä se näyttää:**
- Taulukon kaikista tapahtumista
- Suodattimet:
  - Kategoria
  - Kaupan haku
  - Päivämääräväli

**Miten se toimii:**
1. Lataa datan session_statestä
2. Soveltaa suodattimia
3. Näyttää suodatetun taulukon
4. Järjestää päivämäärän mukaan (uusimmat ensin)

### Edit Categories-välilehti

**Mitä se tekee:**
- Mahdollistaa kategorioiden muokkaamisen
- Mahdollistaa notes-sarakkeen muokkaamisen
- Laskee kustannusjakot automaattisesti uudelleen

**Miten se toimii:**
1. Näyttää listan kaikista tapahtumista
2. Valitsee yhden tapahtuman
3. Näyttää nykyiset arvot
4. Mahdollistaa muokkauksen
5. Tallentaa muutokset session_stateen
6. Laskee kustannusjakot uudelleen jos notes muuttui
7. Tallentaa Exceliin kun käyttäjä klikkaa "Save All Changes"

**Kustannusjakojen uudelleenlaskenta:**
```python
# Jos notes muuttuu "Restaurant/50%" → "Restaurant/75%"
# Systeemi laskee automaattisesti:
# cost_allocation = 0.75
# adjusted_amount = amount × 0.75
```

### Analytics-välilehti

**Mitä se näyttää:**
- Viikoittainen, kuukausittainen tai päivittäinen kulutustrendi (viivakaavio)
- Liukuva keskiarvo trendikaavioon
- Kategorioiden vertailu
- Top merchants -analyysi
- Kulutuksen jakauma

**Miten se laskee:**
```python
# Viikoittainen trendi
df['week'] = df['date'].dt.to_period('W')
weekly = df.groupby('week')['adjusted_amount'].sum()

# Top kauppat
top_merchants = df.groupby('merchant')['adjusted_amount'].sum().sort_values(ascending=False).head(15)
```

### Automaattinen Päivitys

**Miten se toimii:**
1. Käyttäjä klikkaa "Refresh Data" -nappia
2. Sovellus kutsuu `process_new_files()`
3. Pipeline käsittelee uudet CSV-tiedostot
4. Lataa päivitetyn datan Excelistä
5. Päivittää dashboardin automaattisesti

---

## Visualisointien Selitys

### Dashboard-välilehti

#### 1. Monthly Spending - Palkkikaavio
- **Mitä näyttää**: Kuukausittainen kokonaiskulutus
- **Interaktiivisuus**: Klikkaamalla kuukautta näet sen detaljit
- **Keskiarvoviiva**: Tummanharmaa katkoviiva näyttää kuukausittaisen keskiarvon
- **Korkeus**: 500px

#### 2. Total Spending By Category - Donut-kaavio
- **Mitä näyttää**: Kategorioiden jakautuma prosentteina
- **Interaktiivisuus**: Klikkaamalla kategoriaa näet sen detaljit
- **Teksti**: Näyttää prosenttiosuuden ja kategorian nimen viipaleissa
- **Hover**: Näyttää kategorian nimen, summan ja prosenttiosuuden

#### 3. Subcategories - Palkkikuvaaja
- **Mitä näyttää**: Kaikkien subcategorioiden kokonaissummat
- **Järjestys**: Suurimmasta pienimpään (ylhäällä suurin)
- **Korkeus**: 600px
- **Fontit**: Isommat fontit (title 18px, y-axis 13px, x-axis 14px, text 14px)

#### 4. Monthly Average by Subcategory - Palkkikuvaaja
- **Mitä näyttää**: Kuukausittaiset keskiarvot kaikille subcategorioille
- **Laskenta**: (subcategoryn kokonaissumma) / (kuukausien määrä)
- **Järjestys**: Suurimmasta pienimpään
- **Koko**: Koko sivun leveä
- **Korkeus**: 600px
- **Fontit**: Isommat fontit (title 18px, y-axis 13px, x-axis 14px, text 14px)

#### 5. Kategorian detaljit (kun kategoria on valittu)

**Subcategories in [Category] - Donut-kaavio:**
- **Mitä näyttää**: Valitun kategorian alakategorioiden jakautuma
- **Teksti**: Näyttää prosenttiosuuden ja alakategorian nimen
- **Korkeus**: 600px

**Top 10 Merchants - Palkkikuvaaja:**
- **Mitä näyttää**: Top 10 merchantia valitussa kategoriassa
- **Järjestys**: Suurimmasta pienimpään (ylhäällä suurin)
- **Korkeus**: 600px

**Monthly Trend - Viivakaavio:**
- **Mitä näyttää**: Kuukausittainen trendi valitussa kategoriassa
- **Väri**: Punainen
- **Korkeus**: 300px

**Monthly Average per Subcategory - Palkkikuvaaja:**
- **Mitä näyttää**: Kuukausittaiset keskiarvot subcategorioittain valitussa kategoriassa
- **Laskenta**: (subcategoryn kokonaissumma) / (kuukausien määrä kategoriassa)
- **Korkeus**: 350px

**Monthly Average per Merchant - Palkkikuvaaja:**
- **Mitä näyttää**: Kuukausittaiset keskiarvot merchantittain valitussa kategoriassa
- **Laskenta**: (merchantin kokonaissumma) / (kuukausien määrä kategoriassa)
- **Top 20**: Näyttää top 20 merchantia
- **Sijainti**: Sivun alimmaisena
- **Korkeus**: 600px
- **Fontit**: Isommat fontit (title 18px, y-axis 13px, x-axis 14px, text 14px)

### Kuukausitason detaljit (kun kuukausi on valittu)

#### 1. Categories in [Month] - Donut-kaavio
- **Mitä näyttää**: Kategorioiden jakautuma valitussa kuukaudessa
- **Teksti**: Näyttää prosenttiosuuden ja kategorian nimen
- **Korkeus**: 500px

#### 2. Top Subcategories in [Month] - Stackattu palkkikuvaaja
- **Mitä näyttää**: Top 10 subcategoriaa valitussa kuukaudessa
- **Stackaus**: Jokainen palkki koostuu merchant-osista (stackattu)
- **Teksti**: Näyttää subcategoryn kokonaissumman palkin perässä
- **Järjestys**: Suurimmasta pienimpään (ylhäällä suurin)
- **Korkeus**: 500px

#### 3. Top Merchants in [Month] - Palkkikuvaaja
- **Mitä näyttää**: Top 10 merchantia valitussa kuukaudessa
- **Järjestys**: Suurimmasta pienimpään (ylhäällä suurin)
- **Korkeus**: 400px

#### 4. Daily Spending Trend - Viivakaavio
- **Mitä näyttää**: Päivittäinen kulutus valitussa kuukaudessa
- **Väri**: Vihreä
- **Korkeus**: 300px

---

## Käyttöohjeet

### 1. Ensimmäinen Käyttö

**Vaihe 1: Asenna riippuvuudet**
```bash
pip install -r requirements.txt
```

**Vaihe 2: Aktivoi virtuaaliympäristö**
```bash
source venv/bin/activate
```

**Vaihe 3: Käynnistä Streamlit-sovellus**
```bash
streamlit run app/main.py
```

**Vaihe 4: Käsittele CSV-tiedosto**
- Sovellus tunnistaa automaattisesti jos Excel-tiedosto puuttuu
- Tai klikkaa "Process CSV File" -nappia
- CSV-tiedosto käsitellään ja tallennetaan Exceliin

### 2. Päivittäminen Uusilla Tiedostoilla

**Vaihe 1: Kopioi uusi CSV-tiedosto**
```bash
cp /polku/uuteen/tiedostoon.csv data/raw/
```

**Vaihe 2: Päivitä sovellus**
- Klikkaa "Refresh Data" -nappia Streamlit-sovelluksessa
- Tai klikkaa "Process New Files" jos näkyy varoitus

**Vaihe 3: Tarkista tulokset**
- Dashboard päivittyy automaattisesti
- Uudet tapahtumat näkyvät taulukossa

### 3. Kategorioiden Muokkaus

**Vaihe 1: Avaa "Edit Categories" -välilehti**
- Valitse tapahtuma listasta
- Näet nykyiset arvot

**Vaihe 2: Muokkaa arvoja**
- Valitse uusi kategoria
- Valitse uusi 2nd category
- Muokkaa notes-saraketta (esim. lisää "/50%")

**Vaihe 3: Tallenna muutokset**
- Klikkaa "Save Changes" tallentaaksesi sessioniin
- Klikkaa "Save All Changes to Excel" tallentaaksesi Exceliin

### 4. Jupyter Notebookin Käyttö

**Vaihe 1: Avaa notebook**
```bash
jupyter notebook notebooks/exploration.ipynb
```

**Vaihe 2: Suorita solu**
```python
from src.pipeline import process_file
df = process_file('/Users/juhorissanen/Desktop/Transactions.csv')
```

**Vaihe 3: Analysoi dataa**
- Käytä pandas-funktioita analysoimaan dataa
- Piirrä kaavioita plotlyllä
- Tee mukautettuja laskelmia

### 5. Konfiguraation Muokkaus

**Muokkaa `src/config.py` -tiedostoa:**

**Kategoriamääritykset:**
```python
CATEGORY_MAPPING = {
    'Shopping': {
        'H': 'Home / House',  # Lisää uusi määritys
        'P': 'Personal',
    }
}
```

**Käännökset:**
```python
CATEGORY_EN_TO_FI = {
    'Shopping': 'Ostokset',  # Muuta käännöstä
}
```

**Tiedostopolut:**
```python
DEFAULT_CSV_PATH = "/polku/uuteen/csv-tiedostoon.csv"
DEFAULT_EXCEL_PATH = "/polku/uuteen/excel-tiedostoon.xlsx"
```

---

## Tärkeät Huomiot

### Datan Rakenne

**Pakolliset sarakkeet CSV-tiedostossa:**
- Date (YYYY-MM-DD as UTC)
- Merchant
- Txn Amount (Funding Card)
- Category
- Notes (vapaaehtoinen, mutta suositeltava)

**Lopputuloksessa olevat sarakkeet:**
- `date`: Päivämäärä
- `merchant`: Kauppa
- `amount`: Alkuperäinen summa
- `adjusted_amount`: Summa kustannusjakojen jälkeen
- `category`: Pääkategoria (suomeksi)
- `2nd category`: Alakategoria (suomeksi, muodossa "Pääkategoria: Alakategoria")
- `notes`: Muistiinpanot (ilman kustannusjakoprosenttia)
- `cost_allocation`: Kustannusjakokerroin (0.0-1.0)
- `year`, `month`: Vuosi ja kuukausi

### Kustannusjakojen Muoto

**Oikea muoto:**
- `"Restaurant/50%"` → 50% kustannusjako
- `"Hotel/75%"` → 75% kustannusjako

**Väärä muoto:**
- `"Restaurant 50%"` → Ei tunnisteta
- `"Restaurant/50"` → Ei tunnisteta (pitää olla %)

### Kategoriamääritysten Muoto

**Notes-sarakkeen merkinnät:**
- `"F"` → Family (kun category on Entertainment, Shopping, Health, Travel)
- `"P"` → Personal (kun category on Entertainment, Shopping, Health, Travel)
- `"H"` → Home / House (kun category on Shopping)
- `"G"` → Car Gas (kun category on Transport)
- Jne.

**Täydet määritykset löytyvät `src/config.py` -tiedostosta.**

### Alakategorian Nimet

**Muoto:**
- Useimmat alakategoriat ovat muodossa "Pääkategoria: Alakategoria"
- Esimerkkejä:
  - "Ostokset: Koti"
  - "Terveys: Henkilökohtainen"
  - "Matkailu: Perhe"
  - "Ruokakauppa: Yleinen"
  - "Striimaus & Palvelut: Yleinen"
  - "Koul.,Kirj.&Keh:Yleinen"

**Poikkeukset:**
- Autoilu & Liikkuminen -kategorian alakategoriat pysyvät muuttumattomina:
  - "Auton Polttoaine"
  - "Auton Huollot & Ylläpito"
  - "Julkinen liikenne"

---

## Vianetsintä

### Ongelma: Dashboard näyttää 0€

**Syy:** Excel-tiedosto on tyhjä tai korruptoitunut

**Ratkaisu:**
1. Klikkaa "Refresh Data" -nappia
2. Tai klikkaa "Process CSV File" -nappia
3. Sovellus käsittelee CSV-tiedoston automaattisesti

### Ongelma: Kategoriat eivät näy oikein

**Syy:** Notes-sarakkeen merkintä ei vastaa määrityksiä

**Ratkaisu:**
1. Tarkista `src/config.py` -tiedostosta oikeat merkinnät
2. Muokkaa notes-saraketta Streamlit-sovelluksessa
3. Tallenna muutokset

### Ongelma: Uudet tiedostot eivät käsitellä

**Syy:** Tiedosto on jo käsitelty tai väärässä hakemistossa

**Ratkaisu:**
1. Tarkista että CSV-tiedosto on `data/raw/` -hakemistossa
2. Poista `.processed_files.json` -tiedosto pakottaaksesi uudelleenkäsittelyn
3. Klikkaa "Refresh Data" -nappia

### Ongelma: Import-virheet

**Syy:** Virtuaaliympäristö ei ole aktivoitu

**Ratkaisu:**
```bash
source venv/bin/activate
```

---

## Yhteenveto

Tämä järjestelmä on modulaarinen pipeline, joka:
1. **Lataa** CSV-tiedoston
2. **Siivoaa** datan (poistaa duplikaatit, suodattaa)
3. **Käsittelee** kustannusjakot
4. **Luokittelee** tapahtumat
5. **Kääntää** kategoriat suomeksi
6. **Muokkaa** alakategorian nimet selkeämmiksi
7. **Tallentaa** Exceliin
8. **Näyttää** Streamlit-sovelluksessa interaktiivisilla visualisoinneilla

Jokainen vaihe on erillisessä moduulissa, mikä tekee järjestelmästä:
- **Ylläpidettävän** - Helppo muokata yksittäisiä osia
- **Testattavan** - Jokainen moduuli voidaan testata erikseen
- **Laajennettavan** - Helppo lisätä uusia ominaisuuksia
- **Ymmärrettävän** - Selkeä rakenne ja dokumentaatio

### Visualisointien Yhteenveto

**Dashboard-välilehti:**
- Metriikit: Total Spending, Avg/Median Monthly, Unique Merchants, Top Card
- Monthly Spending: Palkkikaavio keskiarvoviivalla
- Total Spending By Category: Donut-kaavio (klikattava)
- Subcategories: Palkkikuvaaja kaikista subcategorioista
- Monthly Average by Subcategory: Koko sivun leveä palkkikuvaaja
- Kategorian detaljit: Subcategories donut, Top Merchants, Monthly Trend, Monthly Average per Subcategory/Merchant

**Kuukausitason detaljit:**
- Categories donut-kaavio
- Top Subcategories stackattu palkkikuvaaja (merchantit stackattuna)
- Top Merchants palkkikuvaaja
- Daily Spending Trend viivakaavio

Kaikki kaaviot ovat interaktiivisia ja käyttävät isompia fonteja paremman luettavuuden vuoksi.
