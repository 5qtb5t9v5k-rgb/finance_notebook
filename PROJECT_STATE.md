# Finance Coach — projektin tila

> ⚠️ **HISTORIALLINEN DOKUMENTTI.** Tämä kirjoitettiin 2026-08-13 kertaluontoisena
> tilannekatsauksena. Sisältö korvattiin samana päivänä myöhemmin
> `docs/STATUS.md` + `docs/CHANGELOG.md` -rakenteella (kaksi dokumenttia,
> eri elinkaari: STATUS ylikirjoitetaan aina, CHANGELOG vain kasvaa). **Ajantasainen
> tila: [`docs/STATUS.md`](docs/STATUS.md).** Tätä dokumenttia ei enää päivitetä,
> mutta sen tekniset selitykset (arkkitehtuuri, datamalli, komponenttien
> yksityiskohdat, koodiviitteet) ovat yhä käyttökelpoisia — vain
> "tila juuri nyt" -osiot (§0, §9) ovat vanhentuneet ja korvattu.

**Päivitetty:** 2026-08-13
**Tarkoitus:** Yksi dokumentti josta näkee mitä on rakennettu, miten se toimii, mikä on rikki ja mistä kannattaa jatkaa. Tämä korvaa aiemmat hajanaiset dokumentit (poistettu 2026-05-23 siivouksessa).

---

## 0. TL;DR — tilanne yhdellä silmäyksellä

| Osa-alue | Tila |
|---|---|
| Pipeline (CSV → puhdas data) | ✅ Toimii |
| Supabase-schema | ✅ Ajettu |
| Streamlit-dashboard (7 välilehteä) | ✅ Rakennettu |
| Finance MCP (Fly.io) | ✅ Deployattu, lukee Supabasesta |
| Gmail → CSV → Supabase -automaatio | ✅ Rakennettu (GitHub Actions, 1 h välein) |
| Budget Coach + Telegram | ✅ Rakennettu |
| **Supabase-kanta** | 🔴 **ALHAALLA — kaikki data pois käytöstä** |
| LLM-fallback uusille kauppiaille | ⬜ Ei rakennettu (M4) |
| Telegram-chat kysymyksille | ⬜ Ei rakennettu (M1) |
| Testit | ⬜ Ei yhtään |

> ### 🔴 Blokkeri: Supabase-projekti ei vastaa
>
> Hostname `lqrejnebswjuaenkecmf.supabase.co` **ei resolvoidu DNS:ssä** (todennettu 2026-08-13).
> Verkko itsessään toimii — `github.com`, `supabase.com` ja `finance-mcp-jr.fly.dev` resolvoituvat normaalisti, vain tämä projekti ei.
>
> **Todennäköisin syy:** Supabasen ilmaistason projekti pausettuu automaattisesti käyttämättömyydestä. ROADMAP päivitettiin viimeksi 2026-05-23, eli välissä on ~12 viikkoa.
>
> **Vaikutus:** Kaikki on kiinni tästä — MCP-toolit, Streamlit, molemmat GitHub Actions -workflowit. Migroidut **942 tapahtumaa ja 757 merchant-sääntöä** ovat joko pausen takana (palautuvat napin painalluksella) tai poistettu.
>
> **Ensimmäinen toimenpide:** Kirjaudu supabase.com → projekti → *Restore/Resume*. Jos projektia ei enää ole, katso [§9 Palautussuunnitelma](#9-palautussuunnitelma).

---

## 1. Mikä tämä on

Henkilökohtainen talousseuranta, joka lukee **Curve-korttisovelluksen** CSV-exportit, luokittelee tapahtumat suomalaisiin kategorioihin ja tarjoaa datan kahdella tavalla:

- **Streamlit-dashboard** selaimessa — visualisoinnit, muokkaus, budjettiseuranta
- **MCP-palvelin** — Claude (iOS / web / Code) voi kysyä kulutuksesta suoraan

Kantava idea: **käsin tehty luokittelutyö ei mene hukkaan.** Vuoden 2025 alusta ~2026 tammikuulle tapahtumat on luokiteltu manuaalisesti. Tästä historiasta on johdettu `merchant_rules`-taulu, joka luokittelee tutut kauppiaat automaattisesti jatkossa.

---

## 2. Arkkitehtuuri (as-built)

```
   Curve-sovellus
        │  (lähettää export-sähköpostin: "Your Curve Export is Ready")
        ▼
   Gmail ──────────────┐
        │              │  scripts/gmail_watcher.py
        │              │  (GitHub Actions, 1 h välein)
        │              ▼
        │      /tmp/curve_transactions.csv
        │              │
        │              ▼  scripts/migrate_to_supabase.py
        │      ┌───────────────────────────┐
        └─ TAI │  Supabase (PostgreSQL)    │
   käsin       │  ├── transactions         │  942 riviä (ennen pausea)
   Streamlitin │  ├── merchant_rules       │  757 sääntöä
   sidebarista │  ├── note_codes           │  17 lyhennettä
                │  └── categories           │  10 kategoriaa
                └───────┬───────────────────┘
                        │
          ┌─────────────┴──────────────┐
          ▼                            ▼
   Finance MCP (Fly.io)         Streamlit-dashboard
   finance-mcp-jr.fly.dev       app/main.py
          │                            │
          ▼                            ▼
   Claude iOS / web / Code        Selain
                                       │
                                       ▼
                            Budget Coach → Telegram
                            (GitHub Actions, cron)
```

**Kaksi repoa:**

| Repo | Kieli | Rooli |
|---|---|---|
| `finance_notebook` (tämä) | Python | Pipeline, Streamlit, Supabase-sync, coach, automaatio |
| `mcp-inventory/servers/finance` | TypeScript | MCP-palvelin joka lukee Supabasesta (Fly.io) |

---

## 3. Datamalli (`scripts/schema.sql`)

Neljä taulua. Ydinoivallus: **note_code on kontekstuaalinen** — sama kirjain tarkoittaa eri asiaa eri kategoriassa.

### `note_codes` — lyhennekirjasto
Avain on `(category_en, note_code)`, koska esim. `G` = *Car Gas* Transportissa mutta *Gifts* Shoppingissa. 17 riviä.

### `categories` — kategoriakäännökset
`category_en` → `category_fi`. 10 riviä, esim. `Groceries` → `Ruokakauppa`.

### `merchant_rules` — opittu muisti ⭐
Tämä on systeemin arvokkain taulu.

| Sarake | Merkitys |
|---|---|
| `merchant`, `note_code` | Uniikki avainpari |
| `category_en/fi`, `second_cat_fi` | Mihin luokitellaan |
| `confidence` | 0–1. Laskettu historiasta: jos K-Market meni 9/10 kertaa Ruokakauppaan → 0.9 |
| `source` | `historical` \| `manual` \| `llm` |
| `hit_count` | Montako kertaa nähty |
| `last_seen` | Viimeisin päivämäärä |

### `transactions` — tapahtumat
`id` on `md5(date|merchant|amount|time)` → sama tapahtuma ei duplikoidu uploadien välillä.

Kaksi lippua ohjaavat käyttäytymistä:
- **`locked`** — `TRUE` = käsin korjattu, CSV-upload **ei ylikirjoita**. Tämä suojaa manuaalisen työn.
- **`needs_review`** — `TRUE` = epävarma, näkyy Streamlitin Review-välilehdellä.

---

## 4. Komponentit

### Pipeline (`src/`)
Puhdas funktioketju, ei sivuvaikutuksia. Ajojärjestys:

| Tiedosto | Tehtävä |
|---|---|
| `data_loader.py` | CSV → DataFrame, sarakenimien standardointi, korttinumeroiden mappaus |
| `data_cleaner.py` | Duplikaatit, päivämääräsuodatus, REFUNDED- ja `del`-rivien poisto |
| `cost_allocator.py` | `/50%`-notaation purku → `cost_allocation`-kerroin |
| `categorizer.py` | Kategoriat + 2nd category + suomennokset |
| `config.py` | Kaikki mappaukset — kortit, kategoriat, käännökset, suodattimet |
| `pipeline.py` | Orkestrointi (`process_file`, `process_new_files`) |

**Huom:** `pipeline.py`:n `save_to_excel()` ja `load_processed_data()` ovat no-op-tynkiä. Excel-aikakausi on ohi, mutta funktiot jätettiin ettei importit hajoa.

### Supabase-kerros
| Tiedosto | Tehtävä |
|---|---|
| `src/supabase_sync.py` | `load_from_supabase()`, `upsert_csv_to_supabase()`, `get_db_status()` |
| `scripts/migrate_to_supabase.py` | Kertaluontoinen historia-migraatio, myös Actionsin käyttämä |
| `scripts/schema.sql` | Taulut + seed-data |

### Streamlit (`app/main.py`, 2 965 riviä)
Seitsemän välilehteä: **Dashboard · Analytics · Transactions · Edit Categories · Budget · Review · Coach**

Data ladataan `refresh_data()`:llä Supabasesta session stateen. Sidebarissa CSV-upload joka kutsuu `upsert_csv_to_supabase()`.

### Budget Coach
| Tiedosto | Tehtävä |
|---|---|
| `config/playbook.yaml` | Budjettitavoitteet — palkka 3 500 €/kk, kulukatto 2 500 €, säästötavoite 800 €, kategoriarajat |
| `src/budget_coach.py` | Palkkapäivälogiikka, budjettitilanne, viestiformatointi |
| `scripts/budget_notify.py` | Telegram-lähetys |

Palkkapäivä = kuun 13., tai edellinen arkipäivä jos viikonloppu.

### Automaatio (`.github/workflows/`)
| Workflow | Ajastus | Tekee |
|---|---|---|
| `curve_sync.yml` | `0 * * * *` (1 h välein) | Gmail → CSV → Supabase |
| `budget_coach.yml` | pv 11–14 klo 09, su klo 10, päivittäin klo 19 (Helsinki) | Telegram-viestit |

`gmail_watcher.py` etsii sähköpostin otsikolla *"Your Curve Export is Ready"*, lataa liitteen ja merkitsee viestin labelilla `curve-processed` ettei sitä käsitellä uudelleen. Exit code 1 = ei uusia → migraatio skipataan.

---

## 5. Miten luokittelu toimii

Kolme kerrosta, kaksi rakennettu:

**1. Curve antaa pääkategorian** (`Groceries`, `Transport`, …) → suomennetaan `CATEGORY_EN_TO_FI`:llä.

**2. Note-koodi tarkentaa alakategorian.** Kirjoitat Curven notes-kenttään esim. `G` → `(Transport, G)` → *Auton Polttoaine*.

**3. Merchant rules oppii historiasta.** Migraatio laski jokaiselle `(merchant, note_code)`-parille yleisimmän luokittelun ja confidencen. → 757 sääntöä.

Lisäksi **kustannusjako**: note `R/50%` tarkoittaa että puolet kuuluu sinulle. `adjusted_amount = amount × cost_allocation`. Raportoinnissa käytetään `adjusted_amount`ia.

**Puuttuu (M4):** LLM-fallback tuntemattomille kauppiaille. Tällä hetkellä uusi kauppias jää ilman alakategoriaa ja päätyy Review-jonoon.

---

## 6. Mikä muuttui alkuperäisestä suunnitelmasta

Suunnitteluvaiheessa harkittiin **SQLite Fly.io-volumella**. Toteutus meni **Supabaseen**. Perustelu: Streamlit Cloud ja GitHub Actions pääsevät molemmat samaan kantaan ilman että Fly-kone pitää olla hereillä, ja hallinta-UI tulee ilmaiseksi.

Toinen muutos: syöttötapa. Alun perin ajatus oli manuaalinen CSV-lataus puhelimelta. Toteutus on parempi — **Curve lähettää exportin sähköpostilla**, joten `gmail_watcher.py` + Actions hoitaa sen automaattisesti tunnin viiveellä. Manuaalinen upload jäi varakeinoksi.

Kolmas: ML-malli hylättiin. `merchant_rules` + (tuleva) LLM-fallback kattaa tarpeen ilman koulutusdataa ja mallin ylläpitoa.

---

## 7. Tunnetut ongelmat

Prioriteettijärjestyksessä.

### 🔴 P0 — Supabase alhaalla
Katso §0. Kaikki muu on tämän takana.

### 🔴 P0 — `finance_db_status` valehtelee virhetilanteessa
MCP-palvelimen ohje sanoo *"Always run finance_db_status first to verify the database is reachable"*. Juuri se työkalu palauttaa nyt siististi nollat:

```json
{ "transaction_count": 0, "merchant_rules_count": 0, "earliest_date": null }
```

…samaan aikaan kun `finance_categories` ja `finance_top_merchants` palauttavat `TypeError: fetch failed`. **Statustyökalu nappaa poikkeuksen ja palauttaa nollat**, mikä näyttää identtiseltä kuin tyhjä-mutta-toimiva kanta. Tämä on pahin mahdollinen paikka hiljaiselle virheelle.

**Korjaus:** `servers/finance` — anna virheen propagoida tai lisää `"reachable": false` -kenttä. (Repo on `mcp-inventory`, ei tässä.)

### 🟠 P1 — Streamlit ajaa service keyllä
`.env.example` sanoo eksplisiittisesti:

> `SUPABASE_SERVICE_KEY` — *"vain migraatioskripteissä ja MCP-palvelimessa, **EI koskaan frontendissä / Streamlitissä**"*
> `SUPABASE_ANON_KEY` — *"Streamlit-dashboardissa (rajoitetut oikeudet)"*

Mutta `src/supabase_sync.py::_get_client()` lukee `SUPABASE_SERVICE_KEY`, ja `app/main.py` importtaa sen. **`SUPABASE_ANON_KEY` ei ole käytössä missään** koko koodipohjassa.

Käytännössä: Streamlit ohittaa RLS:n täysin. Jos dashboard on julkisesti Streamlit Cloudissa, service key on siellä. Korjaus vaatii RLS-politiikat + anon key -polun lukuoperaatioille; kirjoitukset (upload) tarvitsevat edelleen service keyn tai erillisen endpointin.

### 🟠 P1 — Hiljaiset upsert-virheet
`supabase_sync.py`:ssä molemmat batch-loopit:

```python
except Exception:
    rules_err += len(batch)
```

Virhe lasketaan mutta **ei koskaan logata**. Schema-yhteensopimattomuus tai verkkokatko näkyy vain lukuna "errors: 100" ilman syytä. Lisää vähintään `print(e)`.

### 🟡 P2 — Dokumentaatiodrift (korjattu tässä commitissa)
- `README.md` linkitti seitsemään poistettuun dokumenttiin ja kuvasi Excel-pohjaista työnkulkua joka ei ole ollut olemassa sitten toukokuun.
- `ROADMAP.md` merkitsi M2 Coachin `[TODO]`:ksi vaikka se on rakennettu (commit `434286a`).
- `BACKLOG.md` listasi tehtyjä asioita tekemättöminä (MCP:n Supabase-migraatio, `finance_csv_status`-nimenmuutos, Review-näkymä, upload-flow).
- Deployatun MCP-palvelimen omat ohjeet sanovat yhä *"Reads a Curve CSV export... run finance_csv_status first"* — työkalua tuolla nimellä ei enää ole.

### 🟡 P2 — `get_payday` hajoaa kuun alussa
`src/budget_coach.py:41`:

```python
while d.weekday() >= 5:
    d = d.replace(day=d.day - 1)
```

Jos `salary_day` olisi 1 tai 2 ja osuisi viikonlopulle, `day` menisi nollaan tai negatiiviseksi → `ValueError`. Nykyisellä arvolla 13 ei laukea koskaan, mutta jos palkkapäivä muuttuu, tämä kaatuu. Korjaus: `d -= timedelta(days=1)`.

### 🟡 P2 — Valuutta hukataan
`upsert_csv_to_supabase()` kirjoittaa `'currency': 'EUR'` kovakoodattuna joka riville, vaikka `_resolve_eur()` juuri konvertoi summan toisesta valuutasta. Alkuperäinen valuutta katoaa. Sama koskee `'rule_source': 'historical'` — kaikki rivit merkitään historiallisiksi riippumatta siitä miten ne oikeasti luokiteltiin.

### 🟡 P2 — Kahden repon synkronointivelka
`mcp-inventory/servers/finance/src/sources/curve/categorizer-config.ts` on käsin tehty käännös `src/config.py`:stä. Tiedoston kommentti myöntää sen:

```ts
// Keep in sync with the source repo:
// https://github.com/.../finance_notebook/blob/main/src/config.py
```

**`config.py` on jo ehtinyt eteenpäin** — kortti `8834: "OP Debit"` ja kategoria `Food & Drink` lisättiin portin jälkeen. Jos TS-puoli yhä käyttää omaa konfiaan, se on vanhentunut.

Lieventävä seikka: MCP lukee nyt Supabasesta, joten TS-luokittelija saattaa olla kuollutta koodia. **Tämä pitää tarkistaa** — jos on, poista se; jos ei, siirrä konfiguraatio Supabasen `categories`/`note_codes`-tauluihin josta molemmat lukevat.

### ⬜ P3 — Tekninen velka
- `app/main.py` on 2 965 riviä → jako `pages/`-rakenteeseen
- `requirements.txt` pinnattu vanhaan (`streamlit==1.28.0`, `pandas==2.0.0`, `openai==1.0.0`)
- **Nolla testiä.** Vähintään `categorizer.py`:lle ja `_parse_note()`:lle
- Kauppiasnimien normalisointi puuttuu — "K-Market Vuorela" ≠ "K-Market VUORELA"

---

## 8. Mistä jatkaa

**Heti:**
1. Herätä Supabase-projekti. Aja `finance_db_status` uudestaan — pitäisi näyttää 942 / 757.
2. Jos data on mennyt: aja `scripts/schema.sql` ja sen jälkeen `migrate_to_supabase.py` alkuperäisellä historia-CSV:llä. **Tämä edellyttää että käsin luokiteltu CSV on yhä tallessa jossain** — varmista tämä ennen kuin muuta tehdään.
3. Korjaa `finance_db_status` `mcp-inventory`-repossa niin ettei se enää naamioi virhettä.
4. Tarkista `.github/workflows/curve_sync.yml`:n ajohistoria — se on yrittänyt ajaa tunnin välein koko pausen ajan ja epäonnistunut joka kerta.

**Sen jälkeen (arvojärjestyksessä):**
5. **M4 LLM-fallback** — suurin käytännön hyöty. Uusi kauppias → Claude ehdottaa kategoriaa → `merchant_rules` (`source='llm'`, `confidence<1.0`) → Review-jonoon vahvistettavaksi.
6. **Write-toolit MCP:hen** — `update_category`, `update_merchant_rule`. Nyt MCP on vain luku, eli korjaukset vaativat Streamlitin.
7. **Testit** kategorisointilogiikalle ennen kuin M1/M4 kasvattaa pintaa.
8. **M1 Telegram-chat** — kysymykset suomeksi puhelimella.

**Erillinen, valmiina odottamassa:** `mcp-inventory-patches/` tässä repossa sisältää bearer auth + CORS-allowlist + rate limit -patchin `mcp-inventory`-repon HTTP-endpointeille. Ne ovat tällä hetkellä autentikoimattomia. Katso `mcp-inventory-patches/README.md`.

---

## 9. Palautussuunnitelma

Jos Supabase-projekti on poistettu eikä palaudu:

1. Luo uusi Supabase-projekti
2. Aja `scripts/schema.sql` SQL Editorissa (luo taulut + seed-datan)
3. Aja `python scripts/migrate_to_supabase.py <historia.csv>` — tämä rakentaa sekä `transactions`- että `merchant_rules`-taulut uudelleen CSV:stä
4. Päivitä `SUPABASE_URL` + `SUPABASE_SERVICE_KEY`:
   - `.env` lokaalisti
   - GitHub repo secrets (molemmat workflowit)
   - Fly.io: `fly secrets set -a <finance-mcp-app>`
   - Streamlit Cloud secrets

**Kriittinen riippuvuus:** kohta 3 toimii vain jos käsin luokiteltu historia-CSV on tallessa. Se on korvaamaton — vuoden verran manuaalista työtä. Jos sitä ei ole varmuuskopioitu mihinkään, se kannattaa tehdä heti kun kanta on taas pystyssä (`finance_list_transactions` → CSV, tai Supabasen oma export).

---

## 10. Ympäristömuuttujat

| Muuttuja | Missä käytössä | Huom |
|---|---|---|
| `SUPABASE_URL` | Kaikki | |
| `SUPABASE_SERVICE_KEY` | `supabase_sync.py`, migraatio, coach, MCP | Ohittaa RLS:n — katso P1 |
| `SUPABASE_ANON_KEY` | **Ei missään** | Määritelty `.env.example`:ssa, ei käytössä |
| `OPENAI_API_KEY` | `llm_client.py` (Streamlitin insights) | |
| `GMAIL_CLIENT_ID/SECRET/REFRESH_TOKEN` | `gmail_watcher.py` | Setup: `scripts/gmail_auth_setup.py` |
| `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID` | `budget_notify.py` | |
| `DEFAULT_CSV_PATH` | `config.py` | Legacy, pipeline-suoraan-ajoon |

Salaisuudet asuvat neljässä paikassa: `.env` (lokaali), GitHub repo secrets (Actions), Fly.io secrets (MCP), Streamlit Cloud secrets (dashboard). **Kun avain vaihtuu, se pitää päivittää kaikkiin neljään.**
