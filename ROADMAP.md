# Finance Coach — Roadmap

Päivitetty: 2026-08-13

> 🔴 **Nykytila (mitä toimii juuri nyt) asuu [`docs/STATUS.md`](docs/STATUS.md):ssä,
> ei tässä.** Supabase-projekti on tätä kirjoitettaessa alhaalla — kaikki
> alla oleva DONE-status koskee rakennettua koodia, ei nykyistä ajotilaa.
> Historia: [`docs/CHANGELOG.md`](docs/CHANGELOG.md).

## Visio

Henkilökohtainen talouskouksi joka toimii automaattisesti: luokittelee tapahtumat,
muistaa tavoitteet, lähettää viikoittaisen yhteenvedon Telegramiin ja vastaa
kysymyksiin puhelimella suomeksi.

## Arkkitehtuuri

```
Curve CSV (mobiili / desktop)
        │
        ▼
Streamlit upload-flow
        │
        ▼ upsert
┌───────────────────────────────────┐
│  Supabase                         │
│  ├── transactions                 │
│  ├── merchant_rules               │
│  ├── note_codes  (lyhennekirjasto)│
│  └── categories                   │
└───────┬───────────────────────────┘
        │
        ├──→ Finance MCP (Fly.io)  ──→  Claude / Claude Code
        └──→ Streamlit Dashboard   ──→  Selain
```

## Milestonet

### M0 — Data Foundation `[DONE ✅]`

**Tavoite:** Kaikki historia Supabaseen, merchant rules opittu, MCP lukee kannasta.

- [x] Schema suunniteltu (`scripts/schema.sql`)
- [x] Migraatioskripti kirjoitettu (`scripts/migrate_to_supabase.py`)
- [x] Schema ajettu Supabasessa
- [x] Migraatio ajettu — 942 tapahtumaa + 757 merchant-sääntöä sisään
- [x] Finance MCP (mcp-inventory/servers/finance) päivitetty lukemaan Supabasesta
- [x] Upload-flow Streamlitissä: CSV → parse → upsert Supabaseen
- [x] Review-näkymä: tapahtumat joissa `needs_review = true`
- [x] Datalaatu: ALL-valuuttakorjaus, del-filtteri, nollasuodatus, note_code-parser, OP Debit -kortti

**Valmis kun:** Uusi CSV ladataan → tapahtumat näkyvät Supabasessa alle 30s,
merchant lookup osuu >85% tutuille.

✅ **Valmistui 2026-05-23.** MCP toimii Claude iOS -sovelluksessa osoitteessa
`https://finance-mcp-jr.fly.dev/uu_POATzZhcA0XYwamgbXQ97I1dp7w0s/`

---

### M1 — Chat `[TODO]`

**Tavoite:** Voi kysyä kulutuksesta Telegramissa suomeksi.

- [ ] Finance ChatWorker (Router → Executor → Narrator, smarthome-pattern)
- [ ] Telegram-botti (kopio smarthome/home_io_agent/infra/telegram.py)
- [ ] `/luokittele K-Market → Ruokakauppa` -komento päivittää merchant_rules
- [ ] Chat-tab Streamlitissä (MCP-pohjainen, ei OpenAI suoraan)

**Valmis kun:** Telegram-viesti "paljonko ruokakauppa teki tässä kuussa" → oikea
vastaus alle 15s.

---

### M2 — Coach `[DONE ✅]`

**Tavoite:** Proaktiivinen viikoittainen briefing, budjettiseuranta.

- [x] `config/playbook.yaml` — budjettitavoitteet, kategoriarajat, konteksti
- [x] `src/budget_coach.py` — palkkapäivä-, viikko- ja hälytyslogiikka
- [x] `scripts/budget_notify.py` + Telegram-lähetys
- [x] `.github/workflows/budget_coach.yml` — palkkapäivä, viikkoraportti (su),
      päivittäinen hälytyscheck
- [x] Coach-tab Streamlitissä (`app/main.py` tab7)
- [ ] MonthlyReviewWorker (kuun 1. päivä) — ei vielä

**Valmis kun:** Sunnuntaina tulee Telegram-yhteenveto ilman että teen mitään.

✅ **Perusversio valmistui 2026-05-23** (commit `434286a`). Ei ole voitu
todentaa toimivaksi tuotannossa 2026-08-13 asti, koska Supabase on ollut
alhaalla — katso `PROJECT_STATE.md` §0.

---

### M4 — Automaatio `[TODO]`

**Tavoite:** Uusien merchantien automaattinen luokittelu LLM:llä.

- [ ] LLM-fallback tuntemattomille merchanteille (Claude/Gemini)
- [ ] Ehdotus tallennetaan merchant_rules-tauluun (source='llm', confidence<1.0)
- [ ] GitHub Actions / Fly cron proaktiivisille workereille
- [ ] Luokittelutarkkuusraportti Streamlitissä

**Valmis kun:** Uusi CSV sisään → 0 manuaalista luokittelua tutuille, <5 reviewia
uusille merchanteille.

---

## Out of scope

- ❌ Health × Finance -korrelaatiot (M3 hylätty)
- ❌ Oikea ML-malli (merchant lookup + LLM kattaa käytännön tarpeen)
- ❌ Multi-user / perheenjäsenten jako
- ✅ Gmail-automatisointi (`scripts/gmail_watcher.py` + GitHub Actions cron) — tehty M0:n yhteydessä
- ❌ Pankkiintegraatiot / automaattinen CSV-haku
- ❌ Sijoitusten seuranta (eri projekti)
