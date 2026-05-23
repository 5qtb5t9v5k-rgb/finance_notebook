# Finance Coach — Backlog

Päivitetty: 2026-05-23

Ideat ja tulevat tehtävät priorisoimattomana. Isommat kokonaisuudet löytyy
ROADMAP.md:stä.

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
- **Supabase-migraatio finance MCP:ssä** — mcp-inventory/servers/finance/src
  lukee nyt CSV:stä, pitää päivittää Supabase-clientiksi
- **finance_csv_status → finance_db_status** — tool-nimi vanhenee CSV-ajan myötä

## Streamlit Dashboard

- **Review-näkymä** — listaa `needs_review = true` -tapahtumat, quickfix-UI
- **Merchant rules -hallinta** — näytä kaikki säännöt, salli muokkaus
- **Upload-flow** — CSV ladataan → prosessoidaan → upsert Supabaseen
  (korvaa nykyisen in-memory -latauksen)
- **Budjetti vs. toteuma** — kuukausikohtainen, kategoriatasolla, trend-näkymä
- **Exportti** — Excel / CSV lataus Supabasesta

## Coach & agentit

- **playbook.md-editori** — Streamlit-UI jossa voi muokata budjettitavoitteita
  ilman tiedoston suoraa muokkausta
- **Telegram-komentojen laajentaminen** — `/budjetti`, `/top10`, `/kuukausi`
- **Muisti conversation across sessions** — smarthome pelikirja-pattern
- **Säästötavoitteiden seuranta** — Todoist-integraatio: tavoite Todoistissa,
  progress finance-datasta

## Tekninen velka

- **main.py refaktorointi** — 2 778 riviä on liikaa; jako pages/-rakenteeseen
  (Streamlit multi-page app)
- **requirements.txt** — pinnaus vanhoihin versioihin (streamlit==1.28.0,
  pandas==2.0.0); päivitä `>=`-versioihin tai uusiin pinneihin
- **Testit** — ei yhtään testiä; ainakin kategorisointilogiikalle

## Hylätyt / ei nyt

- ~~AI_ASSISTANT_SETUP.md ja vector_store.py~~ — poistettu 2026-05-23
- ~~save_to_excel() / load_processed_data()~~ — poistettu 2026-05-23
- Health × Finance -korrelaatiot — hylätty scope creepinä
