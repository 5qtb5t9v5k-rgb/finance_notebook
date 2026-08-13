# Finance Coach

Henkilökohtainen talousseuranta Curve-korttisovelluksen tapahtumille. Curve
lähettää CSV-exportin sähköpostilla → Gmail-watcher poimii sen automaattisesti
→ pipeline luokittelee tapahtumat suomalaisiin kategorioihin → data päätyy
Supabaseen, josta sekä Streamlit-dashboard että Claude (MCP:n kautta) lukevat.

## 📍 Aloita tästä

**[`docs/STATUS.md`](docs/STATUS.md)** — mikä on totta juuri nyt: mikä toimii,
mikä on rikki, mitä päätöksiä odotetaan sinulta. **Lue tämä ensin**, varsinkin
jos et ole koskenut repoon vähään aikaan. Ristiriitatilanteessa tämä voittaa
kaikki muut dokumentit.

**[`docs/CHANGELOG.md`](docs/CHANGELOG.md)** — miten tähän tultiin,
kuukausittain ryhmiteltynä. Vain lisätään, ei koskaan muokata jälkikäteen.

Muut dokumentit:
- [`ROADMAP.md`](ROADMAP.md) — milestonet ja visio (mihin ollaan menossa)
- [`BACKLOG.md`](BACKLOG.md) — priorisoimattomat ideat ja tehtävät
- [`PROJECT_STATE.md`](PROJECT_STATE.md) — *historiallinen*, syvemmät
  tekniset selitykset arkkitehtuurista ja komponenteista

## Arkkitehtuuri lyhyesti

```
Curve (mobiili) → Gmail → gmail_watcher.py → migrate_to_supabase.py
                                                      │
                                                      ▼
                                              Supabase (PostgreSQL)
                                                      │
                                    ┌─────────────────┴─────────────────┐
                                    ▼                                   ▼
                          Finance MCP (Fly.io)                 Streamlit-dashboard
                          → Claude iOS/web/Code                → selain, Budget Coach
```

Katso `PROJECT_STATE.md` §2 täydelliselle kaaviolle ja komponenttien
selityksille.

## Pikakäynnistys

```bash
pip install -r requirements.txt
cp .env.example .env   # täytä SUPABASE_URL, SUPABASE_SERVICE_KEY, ym.
streamlit run app/main.py
```

Data ladataan automaattisesti Supabasesta. Uuden CSV:n voi ladata joko
sidebarin upload-napista tai antaa `curve_sync.yml`-workflown hoitaa sen
tunnin viiveellä Gmailista.

## Projektirakenne

```
finance_notebook/
├── src/                    # Pipeline + Supabase-kerros + coach
│   ├── config.py           # Kategoria-, kortti- ja suodatinmäärittelyt
│   ├── data_loader.py       # CSV-lataus
│   ├── data_cleaner.py      # Puhdistus
│   ├── cost_allocator.py    # /50%-kustannusjako
│   ├── categorizer.py       # Kategorisointi + suomennokset
│   ├── pipeline.py          # Orkestrointi
│   ├── supabase_sync.py     # Supabase-luku/kirjoitus
│   └── budget_coach.py      # Palkkapäivä- ja budjettilogiikka
├── scripts/
│   ├── gmail_watcher.py         # Curve-CSV:n haku Gmailista
│   ├── migrate_to_supabase.py   # CSV → Supabase
│   ├── budget_notify.py         # Telegram-lähetys
│   └── schema.sql               # Supabase-schema
├── config/playbook.yaml    # Budjettitavoitteet
├── .github/workflows/      # Automaatio (sync tunneittain, coach cronilla)
└── app/main.py             # Streamlit-sovellus (7 välilehteä)
```

## Kategorisointi

- Curve-kategoria käännetään suomeksi (`src/config.py`)
- Notes-kentän lyhennekoodi (esim. `G`, `F`, `RT`) tarkentaa alakategorian
- Historiasta opittu `merchant_rules`-taulu luokittelee tutut kauppiaat
  automaattisesti jatkossa
- `/50%`-suffiksi notesissa jakaa kustannuksen (`Restaurant/50%` = puolet sinulle)

Täydellinen selitys: `PROJECT_STATE.md` §5.
