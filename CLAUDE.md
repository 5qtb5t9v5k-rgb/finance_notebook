# Finance Coach — ohjeet Claude Code -sessioille

Henkilökohtainen talousseuranta Curve-korttisovelluksen tapahtumille.
Curve → Gmail → automaattinen luokittelu → Supabase → Streamlit-dashboard
ja Finance MCP (Fly.io, jota Claude iOS/web/Code käyttää).

## Lue ensin — tässä järjestyksessä

1. **[`docs/STATUS.md`](docs/STATUS.md)** — mikä on totta juuri nyt. Aina
   ensimmäinen pysähdyspaikka uudessa sessiossa. Ristiriitatilanteessa tämä
   voittaa kaikki muut dokumentit repossa.
2. **[`docs/CHANGELOG.md`](docs/CHANGELOG.md)** — miten tähän tultiin.
   Kerro vasta tämän jälkeen tarvittaessa tarkempaa historiaa.
3. Muut: [`README.md`](README.md) (pikakäynnistys), [`ROADMAP.md`](ROADMAP.md)
   (mihin ollaan menossa), [`BACKLOG.md`](BACKLOG.md) (priorisoimattomat
   tehtävät), [`PROJECT_STATE.md`](PROJECT_STATE.md) (historiallinen, mutta
   sisältää yhä käyttökelpoisia teknisiä yksityiskohtia arkkitehtuurista).

## Dokumentaation ylläpito

- `docs/STATUS.md` = nykytila. Päivitä kun tila oikeasti muuttuu
  (päätös tehty, vaihe valmis, ulkoinen vastaus saapui). Ylikirjoita
  vanha teksti — älä kerrosta.
- `docs/CHANGELOG.md` = historia. Vain lisätään. Merkitse päivä ja
  miksi asialla oli väliä.
- Kun jokin dokumentti vanhenee, merkitse se historialliseksi ja
  osoita STATUS.md:hen — älä poista.
- Älä kirjoita status-päivityksiä muistista tai olettaen. Kaiva faktat:
  `git log --date=short --pretty="%ad %s"`, todelliset tiedostot, ja jos
  kyse on ulkoisesta palvelusta (Supabase, Fly.io, Gmail) — testaa oikeasti
  ennen kuin kirjaat sen toimivaksi tai rikki menneeksi.

## Repo-kohtaisia huomioita

- Kaksi repoa liittyy tähän projektiin: tämä (`finance_notebook`, Python —
  pipeline, Streamlit, automaatio) ja `mcp-inventory` (TypeScript — MCP-
  palvelimet, mukana `servers/finance`). Tämän session GitHub-pääsy on
  yleensä scopattu vain `finance_notebook`-repoon; `mcp-inventory`-muutokset
  pitää valmistella patch-tiedostoina (ks. `mcp-inventory-patches/`) tai
  tehdä toisessa sessiossa jolla on pääsy sinne.
- Supabase on datan totuuden lähde. Jos MCP-toolit tai Streamlit eivät saa
  dataa, tarkista ensin DNS-resolvoituvuus (`getent hosts <supabase-url>`)
  ennen kuin oletat koodivirheen — ilmaistason projektit pausettuvat
  käyttämättömyydestä.
