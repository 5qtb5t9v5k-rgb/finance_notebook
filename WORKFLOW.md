# Työnkulku: Pipeline ja Streamlit

## Yleiskuvaus

Pipeline ja Streamlit-sovellus ovat **erillisiä** mutta **yhdessä toimivia** osia:

1. **Pipeline** käsittelee CSV-tiedoston ja tallentaa Exceliin
2. **Streamlit** lukee Excel-tiedoston ja näyttää datan web-käyttöliittymässä

---

## Normaali työnkulku

### Vaihe 1: Aja pipeline (käsittele data)

```bash
./run_pipeline.sh
```

**Mitä tapahtuu:**
- CSV-tiedosto käsitellään
- Data siivotaan, luokitellaan ja käsitellään
- Lopputulos tallennetaan Exceliin

### Vaihe 2: Käynnistä Streamlit (näytä data)

**Uudessa terminaalissa:**
```bash
./run_app.sh
```

tai

```bash
source venv/bin/activate
streamlit run app/main.py
```

**Mitä tapahtuu:**
- Streamlit käynnistyy
- Se lukee Excel-tiedoston
- Näyttää datan web-käyttöliittymässä
- Avautuu selaimessa automaattisesti (yleensä `http://localhost:8501`)

---

## Yhdistetty työnkulku (Pipeline + Streamlit)

Jos haluat ajaa pipeline-prosessin ja käynnistää Streamlit-sovelluksen **yhdellä komennolla**:

```bash
./run_all.sh
```

**Mitä tapahtuu:**
1. Pipeline ajaa ensin (käsittelee CSV:n ja tallentaa Exceliin)
2. Jos pipeline onnistuu, Streamlit käynnistyy automaattisesti
3. Streamlit avautuu selaimessa

**Huom:** Tämä pitää Streamlit-sovelluksen käynnissä, joten terminaali on varattu. Lopeta painamalla `Ctrl+C`.

---

## Miten ne liittyvät toisiinsa?

```
┌─────────────────┐
│  CSV-tiedosto   │
│  (Curve-vienti) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│    Pipeline     │  ← Aja: ./run_pipeline.sh
│  (käsittelee)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Excel-tiedosto │  ← Tallennetaan tähän
│  (käsitelty)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Streamlit     │  ← Käynnistä: ./run_app.sh
│  (näyttää)      │
└─────────────────┘
```

---

## Kysymykset ja vastaukset

### Q: Pitääkö ajaa pipeline aina ennen Streamlitia?

**A:** Ei välttämättä. Streamlit lukee Excel-tiedoston, joten:
- Jos Excel-tiedosto on jo olemassa ja ajantasainen, voit käynnistää Streamlitin suoraan
- Jos CSV-tiedosto on päivittynyt, aja pipeline ensin

### Q: Voiko Streamlit käynnistyä ilman pipelinea?

**A:** Kyllä, jos Excel-tiedosto on jo olemassa. Streamlit yrittää myös automaattisesti käsitellä CSV-tiedoston, jos Excel on tyhjä tai korruptoitunut.

### Q: Mitä tapahtuu jos ajan pipelinea uudelleen?

**A:** Pipeline korvaa Excel-tiedoston uudella datalla. Streamlit-sovelluksessa klikkaa "Refresh Data" -nappia nähdäksesi päivitetyt tiedot (tai päivitä sivu).

### Q: Voiko käyttää molempia samaan aikaan?

**A:** Kyllä! Voit:
1. Ajaa pipeline-prosessin (käsittelee datan)
2. Käynnistää Streamlit-sovelluksen erillisessä terminaalissa
3. Molemmat toimivat samaan aikaan

---

## Käytännön esimerkit

### Esimerkki 1: Ensimmäinen käyttö

```bash
# 1. Aja pipeline (käsittele CSV)
./run_pipeline.sh

# 2. Uudessa terminaalissa: Käynnistä Streamlit
./run_app.sh
```

### Esimerkki 2: Päivitä data ja näytä

```bash
# 1. Aja pipeline uudelleen (päivitetty CSV)
./run_pipeline.sh

# 2. Streamlit-sovelluksessa: Klikkaa "Refresh Data" -nappia
# (tai päivitä sivu)
```

### Esimerkki 3: Yhdistetty (helpoin)

```bash
# Aja pipeline ja käynnistä Streamlit yhdellä komennolla
./run_all.sh
```

---

## Yhteenveto

| Toiminto | Komento | Mitä tekee |
|----------|---------|------------|
| **Pipeline** | `./run_pipeline.sh` | Käsittelee CSV:n → Excel |
| **Streamlit** | `./run_app.sh` | Näyttää Excel-datan webissä |
| **Molemmat** | `./run_all.sh` | Pipeline + Streamlit peräkkäin |

**Muista:**
- Pipeline = datan käsittely
- Streamlit = datan näyttäminen
- Ne ovat erillisiä mutta yhdessä toimivia

