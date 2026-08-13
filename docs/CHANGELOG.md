# Finance Coach — Changelog

Historiapäiväkirja. **Vain lisätään, ei koskaan muokata jälkikäteen.** Jos
jokin merkintä osoittautuu myöhemmin vääräksi, lisää uusi merkintä joka
korjaa sen — älä muokkaa vanhaa. Nykytila asuu erikseen: [`STATUS.md`](STATUS.md).

Rakennettu commit-historiasta (`git log --date=short --pretty="%ad %s"`) ja
ryhmitelty kuukausittain. Ei jokaista committia — vain tapahtumat joilla oli
merkitystä: mihin suuntaan projekti kääntyi, mitä ulkoista tapahtui, ja mitkä
löydökset kumosivat aiemman oletuksen.

---

## 2026-01 — Alkuperäinen julkaisu

**2026-01-03.** Ensimmäinen commit. Projekti syntyi Excel-pohjaisena
pipelinena Curve-korttisovelluksen CSV-exporttien käsittelyyn, ja
Streamlit-dashboardina jossa oli AI Assistant, analytiikka, budjetointi ja
ennustaminen mukana alusta asti.

**2026-01-04.** Henkilökohtaiset tiedostopolut siirrettiin `.env`-tiedostoon
ja dokumentaatiota päivitettiin julkaisua varten — repo tehtiin turvalliseksi
pitää GitHubissa ilman että omat polut tai tunnisteet vuotavat mukana.

**2026-01-17.** Kuuden committin sarja samana päivänä, kaikki saman tavoitteen
alla: saada sovellus toimimaan Streamlit Cloudissa. `chromadb` pudotettiin
riippuvuuksista (aiheutti asennusongelmia pilvessä), `requirements.txt`
kiinnitettiin tarkoilla versionumeroilla, `runtime.txt` ja devcontainer
lisättiin, Streamlit secrets -tuki rakennettiin deploymentia varten, ja
AI-Powered Insights -ominaisuuden jumiutumisbugi korjattiin.

## 2026-02

**2026-02-01.** `chromadb` kommentoitiin pois `requirements.txt`:stä pysyvästi
— sama Streamlit Cloud -yhteensopivuusongelma tammikuulta ei ratkennut
riippuvuusversioita säätämällä, joten koko ominaisuus (vector store / RAG)
jätettiin pois käytöstä.

## 2026-04

**2026-04-26.** Sisarprojektin `mcp-inventory` HTTP-endpointeista
(`health`- ja `todoist`-MCP-serverit) löydettiin auth-aukko koodikatselmuksessa:
`MCP_API_KEY`-ympäristömuuttuja luettiin mutta sitä ei koskaan verrattu
saapuvaan pyyntöön, ja CORS oli auki kaikille origineille. Koska agentin
GitHub-pääsy oli scopattu vain `finance_notebook`-repoon, korjauspatch
(bearer-auth + CORS-allowlist + rate limit) valmisteltiin tämän repon
`mcp-inventory-patches/`-kansioon vietäväksi manuaalisesti toiseen repoon.
Ei vielä sovellettu — ks. `STATUS.md` avoimet päätökset.

## 2026-05 — Supabase-migraatio ja automaatio

**2026-05-23.** Ison siivouksen ja arkkitehtuurin vaihdon päivä.
Kymmenkunta vanhaa dokumenttia (`COMPREHENSIVE_DOCUMENTATION.md`,
`DEPLOYMENT.md`, `DOCUMENTATION.md`, `GIT_SETUP.md`, `INSIGHTS_DESIGN.md`,
`PIPELINE_GUIDE.md`, `QUICKSTART.md`, `WORKFLOW.md`, `AI_ASSISTANT_SETUP.md`,
`ARCHITECTURE.md`) poistettiin repo-siivouksessa niiden käytyä vanhentuneiksi.
Samalla tehtiin projektin isoin arkkitehtuurimuutos: Excel-pohjainen
"totuuden lähde" korvattiin **Supabase**-kannalla (PostgreSQL). Schema
suunniteltiin neljälle taululle (`transactions`, `merchant_rules`,
`note_codes`, `categories`), Gmail-automaatio rakennettiin noutamaan Curven
sähköposti-exportit ilman käsityötä, ja MCP-palvelin (`mcp-inventory/servers/finance`)
päivitettiin lukemaan CSV:n sijaan suoraan Supabasesta. Migraatio ajettiin:
**942 tapahtumaa ja 757 merchant-sääntöä** siirtyi kantaan käsin luokitellusta
historiasta (2025 alusta ~2026 tammikuulle) — tämä luku on peräisin
ROADMAPin omasta kirjauksesta eikä ole tätä kirjoitettaessa (2026-08-13)
uudelleen todennettavissa, koska Supabase-projekti ei vastaa (ks. alla,
2026-08-13). Samana päivänä kaksi datalaatukorjausta: kortti `8834`
tunnistettiin "OP Debit" -kortiksi, ja `del`-suodatin sekä note_code-parseri
korjattiin poistamaan roskarivejä oikein.

**2026-05-24.** Budget Coach rakennettiin: `config/playbook.yaml`
(budjettitavoitteet), `src/budget_coach.py` (palkkapäivä- ja
budjettilogiikka), Streamlitin Coach-tab, ja GitHub Actions -workflow joka
lähettää Telegram-viestejä palkkapäivänä, sunnuntaisin ja kun kategoria
lähestyy rajaansa. Tämä oli ROADMAPin M2-milestone.

**2026-05-25.** Korjaus: `del`-merkityt rivit poistuivat aiemmin vain
uudesta CSV:stä, eivät jo Supabasessa olevasta rivistä jos tapahtuma oli
ehtinyt sinne ennen `del`-merkintää. Upsert-logiikkaa muutettiin poistamaan
myös kannassa jo olevat vastaavat rivit.

**2026-05-28.** Löydettiin ja korjattiin "ALL-valuuttabugi": Albanian
lekeissä (ALL) tehdyt maksut menivät läpi EUR-summana, koska
`Txn Amount (Foreign Spend)` -sarake poistettiin datasta ennen kuin
valuuttakorjauslogiikka ehti käyttää sitä. Korjaus tehtiin `data_loader.py`-
tasolla, ennen sarakkeen poistoa. Tämä osoitti että Curve-datassa esiintyy
muitakin valuuttoja kuin EUR/USD, ja aiempi oletus ("kaikki funding-valuutat
ovat joko EUR tai selkeästi ei-EUR") ei pitänyt paikkaansa täydellisesti.

## 2026-08 — Dokumentaation ajantasaistus ja Supabase-katko löytyi

**2026-08-13.** Kaksi git-branchia (`main` ja
`claude/mcp-inventory-automation-bT49C`) olivat eriytyneet toisistaan noin
kolmen kuukauden ajan — automaatio-branch ei sisältänyt mitään toukokuun
Supabase-migraatiotyöstä. Branchit yhdistettiin. Yhdistämisen jälkeen
tehdyssä tilannekatsauksessa löytyi, että **Supabase-projekti
(`lqrejnebswjuaenkecmf.supabase.co`) ei enää resolvoidu DNS:ssä** —
todennäköisin syy on ilmaistason projektin automaattinen pausetus
käyttämättömyydestä, koska ROADMAPia ei ollut päivitetty toukokuun 23. päivän
jälkeen. Koko datapolku (MCP-palvelimen kyselyt, Streamlit-dashboard,
molemmat GitHub Actions -workflowit) on siis ollut poikki tuntemattoman
pituisen ajan ilman että kukaan huomasi, koska `finance_db_status`-MCP-työkalu
nappaa Supabase-yhteysvirheen ja palauttaa siistit nollat sen sijaan että
kertoisi yhteyden olevan poikki. README, ROADMAP ja BACKLOG päivitettiin
ensimmäistä kertaa sitten toukokuun vastaamaan todellista tilannetta, ja
tämä `docs/STATUS.md` + `docs/CHANGELOG.md` -rakenne otettiin käyttöön ettei
sama drift toistu.

---

## Uudet merkinnät tähän

| Päivä | Mitä | Miksi sillä oli väliä |
|---|---|---|
| | | |
