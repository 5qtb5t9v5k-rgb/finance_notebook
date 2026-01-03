# Insights-ominaisuudet Analytics-välilehdelle

## Tavoite

Automaattisesti generoituja havaintoja, jotka auttavat käyttäjää:
- Huomaamaan kulutuksen muutoksia
- Löytämään säästönpaikkoja
- Ymmärtämään kulutustottumuksiaan

---

## Ehdotetut Insights-kategoriat

### 1. 📈 Kulutuksen Trendit Kategorioittain

**Mitä näytetään:**
- Kategoriat joissa kulutus on **kasvanut eniten** (viime kuukausi vs. keskiarvo)
- Kategoriat joissa kulutus on **laskenut eniten**
- Kategoriat joissa on **suurin vaihtelu** kuukausien välillä

**Esimerkki havaintoja:**
- 🔴 "Ostokset-kategorian kulutus on kasvanut 45% viime kuukaudesta (€1,200 → €1,740)"
- 🟢 "Ruokakauppa-kategorian kulutus on laskenut 15% viime kuukaudesta (€250 → €212)"
- ⚠️ "Tapahtumat & Viihde-kategoriassa on suurta vaihtelua: €50-€500/kk"

**Visualisointi:**
- Palkkikuvaaja: kategoriat järjestettynä muutoksen mukaan
- Värikoodaus: punainen (kasvu), vihreä (lasku), keltainen (vaihtelu)

---

### 2. 💰 Säästönpaikat

**Mitä näytetään:**
- Kategoriat joissa kulutus on **poikkeuksellisen korkea** (yli keskiarvon +30%)
- Kategoriat joissa kulutus on **merkittävästi kasvanut** (yli +20% viime kuukaudesta)
- Kategoriat joissa on **suurin säästöpotentiaali** (korkea kulutus + kasvutrendi)

**Esimerkki havaintoja:**
- ⚠️ "Ostokset-kategoria on 35% korkeampi kuin kuukausittainen keskiarvo (€1,740 vs. €1,289)"
- 🔴 "Ulkona syöminen-kategorian kulutus on kasvanut 60% viime kuukaudesta"
- 💡 "Jos vähennät Ostokset-kategoriaa 10%, säästät ~€174/kk"

**Visualisointi:**
- Lista havaintoja korteissa
- Jokaiselle havainnolle: kategoria, nykyinen vs. keskiarvo, säästöpotentiaali

---

### 3. 📊 Kuukausittaiset Vertailut

**Mitä näytetään:**
- **Viime kuukausi vs. keskiarvo**: Mitkä kategoriat poikkeavat eniten
- **Tämä kuukausi vs. viime kuukausi**: Mitkä kategoriat ovat muuttuneet eniten
- **Top 3 kasvavat kategoriat**: Mitkä kategoriat kasvavat nopeimmin
- **Top 3 laskevat kategoriat**: Mitkä kategoriat laskevat nopeimmin

**Esimerkki havaintoja:**
- "Viime kuukausi oli 12% korkeampi kuin keskiarvo (€1,850 vs. €1,650)"
- "Tämä kuukausi on 8% alempi kuin viime kuukausi (€1,520 vs. €1,650)"
- "Top 3 kasvavat: Ostokset (+45%), Matkailu (+30%), Terveys (+25%)"

**Visualisointi:**
- Metriikkikortit: viime kuukausi, keskiarvo, muutos
- Palkkikuvaaja: top 3 kasvavat ja laskevat kategoriat

---

### 4. 🎯 Kategorian Sisäiset Trendit

**Mitä näytetään:**
- **Alakategoriat** joissa kulutus on kasvanut/laskenut
- **Merchantit** joissa kulutus on kasvanut/laskenut
- **Trendejä** alakategorioittain

**Esimerkki havaintoja:**
- "Ostokset-kategoriassa 'Koti'-alakategoria on kasvanut 80% viime kuukaudesta"
- "Ruokakauppa-kategoriassa Prisma on nyt suurin kulutuslähde (35% kategoriasta)"
- "Tapahtumat & Viihde-kategoriassa 'Perhe'-alakategoria on laskenut 40%"

**Visualisointi:**
- Palkkikuvaaja: alakategoriat tai merchantit järjestettynä muutoksen mukaan
- Värikoodaus: kasvu/lasku

---

### 5. 💡 Säästösuositukset

**Mitä näytetään:**
- **Konkreettiset säästösuositukset** perustuen havaintoihin
- **Säästöpotentiaali**: Jos vähennät kategoriaa X%, säästät Y€/kk
- **Priorisointi**: Mitkä kategoriat kannattaa vähentää ensin

**Esimerkki havaintoja:**
- 💡 "Jos vähennät Ostokset-kategoriaa 15%, säästät ~€261/kk (€1,740 → €1,479)"
- 💡 "Jos vähennät Ulkona syöminen-kategoriaa 20%, säästät ~€120/kk"
- 💡 "Top 3 säästöpotentiaali: Ostokset (€261), Ulkona syöminen (€120), Tapahtumat & Viihde (€80)"

**Visualisointi:**
- Lista suosituksia korteissa
- Jokaiselle suositukselle: kategoria, nykyinen kulutus, säästöpotentiaali, toimenpide

---

### 6. 📅 Kuukausittaiset Korkeimmat/Lowest

**Mitä näytetään:**
- **Korkein kuukausi**: Milloin kulutus oli korkeimmillaan ja miksi
- **Alin kuukausi**: Milloin kulutus oli alimmillaan ja miksi
- **Poikkeukset**: Kuukaudet joissa kulutus poikkeaa merkittävästi keskiarvosta

**Esimerkki havaintoja:**
- "Korkein kuukausi: Heinäkuu 2025 (€3,452) - Matkailu-kategoria oli poikkeuksellisen korkea (€1,200)"
- "Alin kuukausi: Tammikuu 2025 (€1,058) - Normaali kulutus kaikissa kategorioissa"
- "Poikkeukset: Heinäkuu (+103% keskiarvosta), Marraskuu (-46% keskiarvosta)"

**Visualisointi:**
- Metriikkikortit: korkein/alin kuukausi
- Lista poikkeuksia

---

## Ehdotettu Layout Analytics-välilehdelle

```
📈 Analytics
├── 💡 Insights (UUSI - ylimpänä)
│   ├── 📊 Yhteenveto
│   │   ├── Viime kuukausi vs. keskiarvo
│   │   ├── Tämä kuukausi vs. viime kuukausi
│   │   └── Top 3 kasvavat/laskevat kategoriat
│   │
│   ├── 📈 Kulutuksen Trendit Kategorioittain
│   │   ├── Kategoriat joissa kulutus on kasvanut eniten
│   │   ├── Kategoriat joissa kulutus on laskenut eniten
│   │   └── Kategoriat joissa on suurin vaihtelu
│   │
│   ├── 💰 Säästönpaikat
│   │   ├── Kategoriat joissa kulutus on poikkeuksellisen korkea
│   │   ├── Kategoriat joissa kulutus on merkittävästi kasvanut
│   │   └── Suurin säästöpotentiaali
│   │
│   ├── 💡 Säästösuositukset
│   │   └── Konkreettiset suositukset säästöpotentiaalilla
│   │
│   └── 📅 Kuukausittaiset Korkeimmat/Lowest
│       ├── Korkein kuukausi
│       ├── Alin kuukausi
│       └── Poikkeukset
│
├── Time Series Analysis (nykyinen)
├── Category Trends Over Time (nykyinen)
├── Top Merchants Analysis (nykyinen)
└── Spending Distribution (nykyinen)
```

---

## Tekninen Toteutus

### Funktiot joita tarvitaan:

1. **`calculate_category_changes()`**
   - Laskee kategorioiden muutokset kuukausien välillä
   - Palauttaa: kasvavat, laskevat, vaihtelevat kategoriat

2. **`identify_savings_opportunities()`**
   - Etsii kategoriat joissa on säästöpotentiaalia
   - Laskee säästöpotentiaalin jos kategoriaa vähennetään

3. **`generate_insights()`**
   - Generoi automaattisesti havaintoja
   - Palauttaa listan havaintoja strukturoituna

4. **`compare_months()`**
   - Vertailee kuukausia keskenään
   - Laskee muutokset prosentteina

5. **`calculate_trends()`**
   - Laskee trendejä kategorioittain
   - Identifioi kasvavat/laskevat trendit

---

## Esimerkki Havaintojen Muodosta

```python
insight = {
    "type": "category_increase",  # tai "savings_opportunity", "trend", jne.
    "category": "Ostokset",
    "title": "Kulutus kasvanut merkittävästi",
    "description": "Ostokset-kategorian kulutus on kasvanut 45% viime kuukaudesta",
    "current": 1740.00,
    "previous": 1200.00,
    "change": 540.00,
    "change_percent": 45.0,
    "severity": "high",  # "high", "medium", "low"
    "savings_potential": 261.00,  # Jos vähennetään 15%
    "recommendation": "Harkitse vähentämistä 15% säästääksesi ~€261/kk"
}
```

---

## Visualisointi

### Kortit (Cards)
- Jokainen havainto omana korttinaan
- Värikoodaus: punainen (huomio), keltainen (varoitus), vihreä (hyvä)
- Ikonit: 📈 (kasvu), 📉 (lasku), 💰 (säästö), ⚠️ (varoitus)

### Kaaviot
- Palkkikaavio: kategoriat järjestettynä muutoksen mukaan
- Viivakaavio: trendit ajan kuluessa
- Metriikkikortit: keskeiset luvut

---

## Yhteenveto

**Tavoite:** Auttaa käyttäjää huomaamaan kulutuksen muutoksia ja löytämään säästönpaikkoja

**Keskeiset ominaisuudet:**
1. Kulutuksen trendit kategorioittain
2. Säästönpaikat
3. Kuukausittaiset vertailut
4. Säästösuositukset
5. Kuukausittaiset korkeimmat/alimmat

**Toteutus:**
- Automaattisesti generoituja havaintoja
- Visualisoituja trendejä
- Konkreettisia säästösuosituksia

