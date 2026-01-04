# Finance Transaction Pipeline - Perusidea ja Arkkitehtuuri

## Perusidea

### Ongelma

Curve-sovelluksesta voi viedä tapahtumatiedot CSV-muodossa, mutta:
- Data on raakaa ja vaatii siivousta (duplikaatit, virheelliset rivit)
- Kategoriat ovat englanniksi ja vaativat käännöksen
- Alakategoriat pitää määritellä manuaalisesti
- Kustannusjakot (esim. "50% minun") pitää laskea erikseen
- Datan analysointi ja visualisointi vaatii oman koodin

### Ratkaisu

Tämä projekti tarjoaa **automaattisen pipeline-prosessin**, joka:
1. **Käsittelee** CSV-tiedoston alusta loppuun
2. **Siivoaa** datan (poistaa duplikaatit, suodattaa virheet)
3. **Luokittelee** tapahtumat automaattisesti kategorioihin ja alakategorioihin
4. **Kääntää** kategoriat suomeksi
5. **Laskee** kustannusjakot automaattisesti
6. **Tallentaa** valmiin datan Exceliin
7. **Näyttää** datan interaktiivisessa web-käyttöliittymässä

### Hyödyt

- **Automaattinen**: Yksi komento käsittelee koko CSV-tiedoston
- **Johdonmukainen**: Sama logiikka aina, ei manuaalisia virheitä
- **Nopea**: Prosessi kestää sekunneissa
- **Laajennettava**: Helppo lisätä uusia kategorioita tai sääntöjä
- **Visualisoitu**: Streamlit-sovellus näyttää datan kauniisti

---

## Arkkitehtuuri

### Yleisrakenne

Järjestelmä on rakennettu **modulaarisesti** - se on jaettu selkeisiin osiin, joista jokainen tekee oman työnsä. Tämä tekee järjestelmästä:
- **Ylläpidettävän**: Helppo muokata yksittäisiä osia
- **Testattavan**: Jokainen moduuli voidaan testata erikseen
- **Laajennettavan**: Helppo lisätä uusia ominaisuuksia
- **Ymmärrettävän**: Selkeä rakenne ja dokumentaatio

### Pipeline-malli

Järjestelmä toimii kuin **tehdaspipeline**:

```
┌─────────────┐
│ CSV-tiedosto│  ← Sisään tuleva data (Curve-vienti)
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────────┐
│         PIPELINE-PROSESSI               │
│                                         │
│  ┌──────────────┐  ┌──────────────┐   │
│  │ Data Loader  │→ │ Data Cleaner │   │
│  └──────────────┘  └──────┬───────┘   │
│                            │           │
│  ┌──────────────┐  ┌──────▼───────┐   │
│  │Cost Allocator │→ │ Categorizer  │   │
│  └──────────────┘  └──────┬───────┘   │
│                            │           │
│                    ┌───────▼───────┐   │
│                    │   Pipeline    │   │
│                    │ (Orchestrator)│   │
│                    └───────┬───────┘   │
└────────────────────────────┼───────────┘
                             │
                             ▼
                    ┌─────────────┐
                    │Excel-tiedosto│  ← Ulos tuleva data (käsitelty)
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  Streamlit   │  ← Web-käyttöliittymä
                    │   (Näyttää)  │
                    └─────────────┘
```

### Kolme pääosaa

#### 1. Pipeline-moduulit (`src/`)

Nämä ovat "työntekijöitä", jotka käsittelevät dataa:

**`config.py`** - Asetukset-arkisto
- Sisältää kaikki määritykset: kategoriat, käännökset, tiedostopolut
- Keskus, josta kaikki muut moduulit lukevat asetukset

**`data_loader.py`** - Lataaja
- Lataa CSV-tiedoston koneelle
- Siivoaa alustavasti (poistaa lainausmerkit, ylimääräiset sarakkeet)

**`data_cleaner.py`** - Siivooja
- Poistaa duplikaatit
- Suodattaa pois turhat tapahtumat (esim. palautukset)
- Lisää vuosi- ja kuukausisarakkeet

**`cost_allocator.py`** - Kustannusjakolaskuri
- Etsii notes-sarakkeesta merkinnät kuten "/50%"
- Laskee kuinka paljon tapahtumasta kuuluu sinulle

**`categorizer.py`** - Luokittelija
- Katsoo notes-saraketta ja pääkategoriaa
- Määrittää alakategorian (esim. "F" + "Entertainment" → "Perhe")
- Kääntää kaiken suomeksi
- Täyttää automaattisesti tyhjät kategoriat

**`pipeline.py`** - Orkestraattori
- Koordinoi kaikkia yllä olevia moduuleja
- Kutsuu niitä oikeassa järjestyksessä
- Hoitaa tiedostojen automaattisen tunnistuksen

#### 2. Streamlit-sovellus (`app/`)

Tämä on "käyttöliittymä", jota käytät selaimessa:

**`main.py`** - Web-käyttöliittymä
- **Dashboard**: Näyttää yleiskuvan, tilastot, interaktiiviset kaaviot
- **Transactions**: Taulukko kaikista tapahtumista suodattimilla
- **Edit Categories**: Mahdollistaa kategorioiden ja notes-sarakkeen muokkaamisen
- **Analytics**: Syvällisempiä analyysejä ja trendejä


---

## Data Flow - Miten data liikkuu

### Vaihe 1: CSV-tiedoston Lataus
```
CSV-tiedosto (työpöytä tai data/raw/)
    ↓
data_loader.py
    ↓
Alustava siivous (poistaa lainausmerkit, ylimääräiset sarakkeet)
```

### Vaihe 2: Datan Siivous
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

### Vaihe 3: Kustannusjakojen Käsittely
```
Siivottu data
    ↓
cost_allocator.py
    ├─→ Etsii notes-sarakkeesta "/50%" -tyyppisiä merkintöjä
    ├─→ Poimii prosenttiosuuden (esim. 50% → 0.5)
    ├─→ Poistaa prosenttiosuuden notes-sarakkeesta
    └─→ Laskee adjusted_amount = amount × cost_allocation
```

### Vaihe 4: Kategorisointi
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

### Vaihe 5: Tallennus
```
Valmis data
    ↓
pipeline.py → save_to_excel()
    ↓
Excel-tiedosto (data/processed/ tai DEFAULT_EXCEL_PATH)
```

### Vaihe 6: Näyttäminen
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

## Modulaarinen Rakenne - Miksi?

### Hyödyt

**1. Ylläpidettävyys**
- Jos haluat muuttaa kategoriamäärityksiä, muokkaat vain `config.py`-tiedostoa
- Jos haluat muuttaa siivouslogiikkaa, muokkaat vain `data_cleaner.py`-tiedostoa
- Muutokset eivät vaikuta muihin moduuleihin

**2. Testattavuus**
- Voit testata jokaisen moduulin erikseen
- Esimerkki: Testaa `categorizer.py` antamalla sille testidataa

**3. Laajennettavuus**
- Lisää uusi moduuli ilman että muutat vanhoja
- Esimerkki: Lisää `data_validator.py` tarkistamaan datan laadun

**4. Ymmärrettävyys**
- Jokainen moduuli tekee yhden asian hyvin
- Helppo ymmärtää mitä kukin moduuli tekee
- Selkeä rakenne ja dokumentaatio

### Esimerkki: Kategoriamääritysten muutos

**Ilman modulaarista rakennetta:**
- Pitäisi etsiä koodista kaikki kohdat missä kategoriat määritellään
- Riski että jokin kohta jää muuttamatta
- Vaikea ylläpitää

**Modulaarisella rakenteella:**
- Muokkaat vain `config.py`-tiedostoa
- Kaikki muut moduulit käyttävät automaattisesti uusia määrityksiä
- Helppo ja turvallinen

---

## Teknologiat

### Python-kirjastot

- **pandas**: Datan käsittely ja manipulointi
- **plotly**: Interaktiiviset visualisoinnit
- **streamlit**: Web-käyttöliittymä
- **openpyxl**: Excel-tiedostojen käsittely

### Rakenne

- **Modulaarinen**: Jokainen osa on erillisessä moduulissa
- **Funktioperustainen**: Jokainen moduuli sisältää funktioita
- **Konfiguroitava**: Asetukset keskitetty `config.py`-tiedostoon
- **Dokumentoitu**: Kattava dokumentaatio kaikesta

---

## Koodimäärät

### Python-koodi: 2,274 riviä

**Pipeline-moduulit (`src/`): 1,068 riviä**
- `pipeline.py` - 311 riviä (orchestrator)
- `categorizer.py` - 256 riviä (kategorisointi)
- `data_cleaner.py` - 164 riviä (datan siivous)
- `data_loader.py` - 156 riviä (CSV-lataus)
- `config.py` - 124 riviä (asetukset)
- `cost_allocator.py` - 55 riviä (kustannusjakojen käsittely)

**Streamlit-sovellus (`app/`): 1,126 riviä**
- `main.py` - 1,124 riviä (web-käyttöliittymä)

**Muut Python-tiedostot: 80 riviä**
- `run_pipeline.py` - 80 riviä (pipeline-ajoskripti)

### Muut tiedostot

- **Shell-skriptit**: 84 riviä
- **Dokumentaatio**: 1,644 riviä

**Yhteensä: ~4,000 riviä** koodia ja dokumentaatiota

---

## Yhteenveto

Tämä projekti on **modulaarinen pipeline-järjestelmä**, joka:
1. **Käsittelee** CSV-tiedostoja automaattisesti
2. **Siivoaa** datan ja poistaa virheet
3. **Luokittelee** tapahtumat kategorioihin
4. **Kääntää** kategoriat suomeksi
5. **Laskee** kustannusjakot
6. **Tallentaa** valmiin datan Exceliin
7. **Näyttää** datan interaktiivisessa web-käyttöliittymässä

**Modulaarinen rakenne** tekee järjestelmästä:
- Ylläpidettävän
- Testattavan
- Laajennettavan
- Ymmärrettävän

**Teknologiat**: Python, pandas, plotly, streamlit

**Koodimäärä**: ~4,000 riviä (koodi + dokumentaatio)

**Rakenne**: 6 pipeline-moduulia + Streamlit-sovellus

