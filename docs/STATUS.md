# Finance Coach — Nykytila

**Päivätty: 2026-08-13.** Tämä on nykytilan yksi totuuslähde. Ristiriitatilanteessa
tämä voittaa — myös suhteessa `README.md`:hen, `ROADMAP.md`:hen ja
`PROJECT_STATE.md`:hen (jälkimmäinen on merkitty historialliseksi, ks.
dokumenttikartta alla). Historia: [`CHANGELOG.md`](CHANGELOG.md).

---

## Tilannetaulukko

| Alue | Tila | Selitys |
|---|---|---|
| Pipeline (CSV → puhdas, luokiteltu data) | ✅ | `src/`-moduulit toimivat ja on testattu käytännössä useilla korjauskierroksilla (valuutta-, del-rivi- ja korttibugit korjattu 05/2026). |
| Supabase-schema ja koodi | ✅ | `scripts/schema.sql` on suunniteltu ja ajettu, `src/supabase_sync.py` toimii koodina. |
| **Supabase-kanta, ajossa** | ❌ | Hostname `lqrejnebswjuaenkecmf.supabase.co` ei resolvoidu DNS:ssä (todennettu 2026-08-13). Koko datapolku on poikki. Ks. Kriittinen polku. |
| Streamlit-dashboard (7 välilehteä) | 🟡 | Koodi on olemassa ja kattava (Dashboard, Analytics, Transactions, Edit, Budget, Review, Coach), mutta ei voida käyttää oikealla datalla ennen kuin Supabase palaa. |
| Finance MCP (Fly.io) | 🟡 | Palvelin itse vastaa (`finance-mcp-jr.fly.dev` resolvoituu, tools kutsuttavissa), mutta jokainen data-kysely paitsi status epäonnistuu `fetch failed`:iin koska Supabase ei vastaa. |
| Gmail → CSV → Supabase -automaatio | 🟡 | Koodi ja GitHub Actions -workflow (`curve_sync.yml`, tunneittain) ovat olemassa, mutta jokainen ajo on epäonnistunut migraatiovaiheessa siitä lähtien kun Supabase pausettui. |
| Budget Coach + Telegram | 🟡 | Sama tilanne — logiikka on rakennettu ja ajastettu, mutta ei voi lukea dataa. |
| mcp-inventory HTTP-auth-patch | ⬜ | Valmis patch (`mcp-inventory-patches/`) odottaa soveltamista toiseen repoon — ei vielä tehty. |
| LLM-fallback uusille kauppiaille (M4) | ⬜ | Ei rakennettu. |
| Telegram-chat kysymyksille (M1) | ⬜ | Ei rakennettu. |
| Testit | ⬜ | Nolla testiä koko koodipohjassa. |

---

## Kriittinen polku

```
[SINÄ]                          [ULKOPUOLINEN]                    [SINÄ / AGENTTI]
   │                                   │                                  │
   │  1. Kirjaudu supabase.com    ┌────▼────────────────┐                │
   │─────────────────────────────▶│ Supabase-projekti    │                │
   │     ja herätä/palauta        │ pausella tai poistettu│                │
   │     projekti                 └────┬──────────────────┘                │
   │                                   │                                  │
   │                              2a. JOS herää: data (942 tx / 757       │
   │                                  sääntöä) palautuu ennalleen         │
   │                                  → tarkista finance_db_status         │
   │                                                                       │
   │                              2b. JOS EI herää / on poistettu:        │
   │                                  ┌──────────────────────────────┐    │
   │                                  │ Onko käsin luokiteltu         │    │
   │                                  │ historia-CSV tallessa jossain?│    │
   │                                  └──────┬───────────────┬────────┘    │
   │                                     KYLLÄ│           EI │              │
   │                                         │               │            │
   │                          3. Uusi Supabase-projekti      │            │
   │                             + schema.sql + migrate_to_  │  ⚠️ Vuoden  │
   │                             supabase.py <historia.csv>  │  manuaali- │
   │                             → rakentaa transactions +   │  työ olisi │
   │                             merchant_rules uudelleen    │  poissa    │
   │                                         │               │            │
   └─────────────────────────────────────────┘               │            │
                                                               │            │
   4. Päivitä SUPABASE_URL + SUPABASE_SERVICE_KEY neljään paikkaan:       │
      .env (lokaali), GitHub repo secrets, Fly.io secrets, Streamlit      │
      Cloud secrets                                    ──────────────────▶│
                                                                            │
   5. Korjaa finance_db_status (mcp-inventory-repo) niin ettei se         │
      enää naamioi Supabase-yhteysvirhettä nollina                       │
                                                                            │
   6. Vasta tästä eteenpäin: M4 LLM-fallback, write-toolit MCP:hen,       │
      Telegram-chat (M1)                                                  │
```

**Omissa käsissä juuri nyt:** Supabase-projektin herättäminen (askel 1) —
tämä ei vaadi mitään koodia, vain kirjautumisen supabase.com-hallintapaneeliin.
**Kaikki muu tässä repossa on koodattu valmiiksi** ja alkaa toimia heti kun
askel 1 on tehty. Ei siis odoteta ketään ulkopuolista tahoa (ei viranomaista,
ei kolmatta osapuolta joka vastaisi hitaasti) — kyse on vain siitä että joku
avaa selaimen ja painaa "Resume".

---

## Avoimet päätökset

Nämä estävät etenemisen ja vaativat sinun päätöksesi — agentti ei voi arvata
näitä oikein.

1. **Onko käsin luokiteltu historia-CSV varmuuskopioitu jonnekin Supabasen
   ulkopuolelle?** Tämä on koko systeemin arvokkain yksittäinen tiedosto —
   vuoden verran manuaalista luokittelutyötä. Jos Supabase-projekti on
   pelkästään pausella, tämä ei ole akuutti. Jos projekti on poistettu, tämän
   olemassaolo ratkaisee voiko dataa palauttaa ollenkaan. **Suositus: vahvista
   tämä heti, riippumatta siitä herääkö Supabase.**

2. **playbook.yaml:n budjettiluvuissa on kaksi selittämätöntä aukkoa** jotka
   löytyivät tässä tarkastuksessa eivätkä ole minkään dokumentin kirjoitusvirhe
   vaan itse konfiguraation sisäinen epäjohdonmukaisuus:
   - Kategoriakohtaisten kattojen summa on 1 610 €/kk, mutta `total_monthly`
     on 2 500 €/kk. **890 €/kk kuuluu kokonaisbudjettiin ilman että mikään
     seurattu kategoria kattaa sitä** — todennäköisesti asuminen, lainat tai
     muut kiinteät kulut joita ei seurata kategoriakohtaisesti, mutta tätä ei
     ole kirjattu mihinkään.
   - `total_monthly` (2 500) + `savings_target` (800) = 3 300 €/kk, mutta
     `monthly_net` (palkka) on 3 500 €/kk. **200 €/kk jää selittämättä** —
     puskuri, pyöristys, vai unohdettu erä?

   Kumpikaan ei ole koodivirhe eikä agentti voi päättää oikeaa lukua puolestasi.
   Jos näihin on looginen selitys (esim. asuntolaina hoidetaan kokonaan
   kategorian ulkopuolella), kannattaa se kirjata `playbook.yaml`:n
   kommentteihin ettei sama kysymys nouse esiin uudelleen kolmen kuukauden
   päästä.

3. **Sovelletaanko `mcp-inventory-patches/`-patch nyt vai myöhemmin?**
   Patch on valmis mutta ei sovellettu — agentin GitHub-pääsy ei ylety
   `mcp-inventory`-repoon tästä sessiosta. Vaatii joko manuaalisen kopioinnin
   tai uuden agenttisession joka on scopattu sinne.

4. **Onko `mcp-inventory/servers/finance/src/sources/curve/categorizer-config.ts`
   yhä käytössä?** Se on käsin tehty TS-käännös `src/config.py`:stä ja on jo
   ehtinyt jäädä jälkeen (puuttuu kortti `8834` ja kategoria `Food & Drink`).
   Jos MCP lukee nykyään suoraan Supabasesta (mikä `finance_db_status`
   vahvistaa: `"source": "supabase"`), tämä tiedosto on todennäköisesti
   kuollutta koodia ja voidaan poistaa — mutta tätä ei ole varmistettu, ja
   päätös (poista vs. synkkaa) vaatii käynnin toisessa repossa.

---

## Mittarit

Kaikki alla olevat luvut ovat **viimeisin tunnettu tila ennen Supabasen
pausetusta** — ei tämän hetken vahvistettua tilaa, koska kanta ei vastaa.

| Mittari | Arvo | Lähde | Tuoreus |
|---|---|---|---|
| Tapahtumia kannassa | 942 | ROADMAP.md, migraatiokirjaus | 2026-05-23, ei uudelleentodennettu |
| Merchant-sääntöjä | 757 | ROADMAP.md, migraatiokirjaus | 2026-05-23, ei uudelleentodennettu |
| Palkka (netto) | 3 500 €/kk | `config/playbook.yaml` | Käyttäjän itse asettama, ei aikaleimaa |
| Kulubudjetti (kokonais) | 2 500 €/kk | `config/playbook.yaml` | ks. Avoin päätös #2 |
| Säästötavoite | 800 €/kk | `config/playbook.yaml` | ks. Avoin päätös #2 |
| Palkkapäivä | kuun 13., tai edellinen arkipäivä | `config/playbook.yaml` | |

---

## Dokumenttikartta

| Tarvitset... | Löydät sen... |
|---|---|
| Mikä on totta juuri nyt | `docs/STATUS.md` (tämä dokumentti) |
| Miten tähän tultiin, mitä on tehty milloinkin | `docs/CHANGELOG.md` |
| Mihin suuntaan ollaan menossa, mitä milestonet tarkoittavat | `ROADMAP.md` |
| Priorisoimattomat ideat ja pienet tehtävät | `BACKLOG.md` |
| Arkkitehtuuri, komponentit, tunnetut koodiongelmat yksityiskohtaisesti | `PROJECT_STATE.md` *(HISTORIALLINEN — sisältö on siirretty/tiivistetty tänne ja ROADMAP/BACKLOG:iin, mutta yksityiskohtaisemmat tekniset selitykset ja koodiviitteet ovat siellä yhä ajantasaisia)* |
| Miten aja pipeline paikallisesti | `README.md` |
| mcp-inventory-HTTP-auth-patch | `mcp-inventory-patches/README.md` |
| Supabase-schema | `scripts/schema.sql` |
| Budjettitavoitteet muokattavassa muodossa | `config/playbook.yaml` |
