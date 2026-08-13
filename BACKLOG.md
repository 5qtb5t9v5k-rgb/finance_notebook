# Finance Coach — Backlog

Päivitetty: 2026-08-13

Ideat ja tulevat tehtävät priorisoimattomana. Isommat kokonaisuudet löytyy
ROADMAP.md:stä. Nykytila: [`docs/STATUS.md`](docs/STATUS.md). Tunnetut bugit
ja niiden korjausehdotukset: `PROJECT_STATE.md` §7 (historiallinen, mutta
tekniset yksityiskohdat pätevät yhä).

---

## Data & kategorisointi

- **Duplikaattien tunnistus CSV-latauksessa** — hash-pohjainen, jo osin tehty
  pipeline.py:ssä mutta ei Supabase-flowssa
- **Kustannusjaon UI** — `/50%`-notaatio pitää selittää käyttäjälle ja tehdä
  helpoksi syöttää Streamlitissä
- **Merchant-nimen normalisointi** — "K-Market Vuorela" ja "K-Market VUORELA"
  pitää matchata samaan sääntöön (lowercase + strip ennen lookuppia)
- **Uuden note-koodin lisääminen** — UI jossa voi lisätä uuden lyhenteet
  note_codes-tauluun ilman SQL:ää
- **Confidence-threshold review-jonoon** — merchant_rules joissa confidence < 0.8
  flagataan automaattisesti needs_review = true

## MCP-palvelin

- **Write-toolit finance MCP:hen** — tällä hetkellä vain luku; tarvitaan
  `add_transaction`, `update_category`, `update_merchant_rule`
- ~~**Supabase-migraatio finance MCP:ssä**~~ — tehty, `finance_db_status`
  vahvistaa `"source": "supabase"`
- ~~**finance_csv_status → finance_db_status**~~ — nimi vaihdettu, mutta MCP:n
  julkinen tool-kuvaus ("Reads a Curve CSV export...") on jäänyt vanhaksi —
  päivitä `mcp-inventory`-repossa
- **`finance_db_status` naamioi virheen nollina** — jos Supabase ei vastaa,
  status palauttaa `{transaction_count: 0, ...}` sen sijaan että kertoisi
  yhteysvirheestä. Ks. `PROJECT_STATE.md` §7 (P0).
- **`categorizer-config.ts` synkassa `config.py`:n kanssa** — tarkista onko
  vielä käytössä (MCP lukee nyt Supabasesta); jos ei, poista kuolleena koodina,
  jos on, portaa `8834: "OP Debit"` ja `Food & Drink` -lisäykset

## Streamlit Dashboard

- ~~**Review-näkymä**~~ — tehty (`app/main.py` tab6)
- **Merchant rules -hallinta** — näytä kaikki säännöt, salli muokkaus
  (Review-näkymä kattaa vain yksittäiset tapahtumat, ei sääntötaulua)
- ~~**Upload-flow**~~ — tehty, `upsert_csv_to_supabase()` sidebarista
- ~~**Budjetti vs. toteuma**~~ — tehty (`get_budget_vs_actual`, Budget-tab)
- **Exportti** — Excel / CSV lataus Supabasesta — ei vielä

## Coach & agentit

- **playbook.yaml-editori** — Streamlit-UI jossa voi muokata budjettitavoitteita
  ilman tiedoston suoraa muokkausta
- **Telegram-komentojen laajentaminen** — `/budjetti`, `/top10`, `/kuukausi`
- **Muisti conversation across sessions** — smarthome pelikirja-pattern
- **Säästötavoitteiden seuranta** — Todoist-integraatio: tavoite Todoistissa,
  progress finance-datasta
- **`get_payday`-korjaus** — `d.replace(day=d.day - 1)` kaatuu jos palkkapäivä
  osuisi kuun 1.–2. päivälle viikonlopun kanssa; käytä `timedelta`. Ei laukea
  nykyisellä `salary_day=13`, mutta on aikapommi jos arvoa muutetaan.

## Tekninen velka

- **main.py refaktorointi** — 2 965 riviä on liikaa; jako pages/-rakenteeseen
  (Streamlit multi-page app)
- **requirements.txt** — pinnaus vanhoihin versioihin (streamlit==1.28.0,
  pandas==2.0.0, openai==1.0.0); päivitä `>=`-versioihin tai uusiin pinneihin
- **Testit** — ei yhtään testiä; ainakin kategorisointilogiikalle ja
  `_parse_note()`-funktiolle
- **`SUPABASE_ANON_KEY` käyttämätön** — Streamlit ajaa `SUPABASE_SERVICE_KEY`:llä
  vastoin `.env.example`:n omaa ohjetta, mikä ohittaa RLS:n kokonaan
- **Hiljaiset upsert-virheet** `supabase_sync.py`:ssä — `except Exception:
  rules_err += 1` ei koskaan logaa syytä
- **Valuutta ja rule_source kovakoodattu** upsertissa (`'EUR'`, `'historical'`)
  riippumatta todellisesta arvosta

## Hylätyt / ei nyt

- ~~AI_ASSISTANT_SETUP.md ja vector_store.py~~ — poistettu 2026-05-23
- ~~save_to_excel() / load_processed_data()~~ — poistettu 2026-05-23
- Health × Finance -korrelaatiot — hylätty scope creepinä
