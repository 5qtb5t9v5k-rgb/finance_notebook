# AI Assistant - Asennus- ja Käyttöohjeet

## Yleiskuvaus

AI Assistant on vapaaehtoinen ominaisuus, joka käyttää OpenAI:n GPT-3.5-turbo -mallia analysoimaan rahoitustapahtumadataa ja vastaamaan käyttäjän kysymyksiin suomeksi.

**RAG-ratkaisu:** Apuri käyttää RAG (Retrieval-Augmented Generation) -tekniikkaa Chroma-vektoritietokannan avulla. Tämä tarkoittaa, että kun kysyt jotain, järjestelmä hakee automaattisesti relevantit tapahtumat kysymyksesi perusteella ja lähettää vain ne LLM:lle. Tämä on paljon tehokkaampaa ja halvempaa kuin koko datasetin lähettäminen.

## Hinnoittelu

**GPT-3.5-turbo (oletusmalli):**
- Input: $0.50 per miljoona tokenia
- Output: $1.50 per miljoona tokenia
- Esimerkki: 1000 tokenia = **$0.0035 per kysymys**

**GPT-4.1 (vaihtoehto):**
- Input: $2.00 per miljoona tokenia
- Output: $8.00 per miljoona tokenia
- Esimerkki: 1000 tokenia = **$0.01 per kysymys**

**Suositus:** Käytä GPT-3.5-turbo -mallia (noin 3x halvempi ja riittävän hyvä analysointiin).

### Embedding-kustannukset (RAG)

**text-embedding-3-small:**
- Hinta: $0.02 per miljoona tokenia
- Dimensiot: 1536

**Kustannukset:**
- 1000 tapahtumaa ≈ 10,000 tokenia ≈ **$0.0002** (kerran, kun vektoritietokanta luodaan)
- Query-embedding ≈ 10 tokenia ≈ **$0.0000002** per kysymys

**Yhteensä:** RAG-ratkaisu on paljon halvempi kuin koko datasetin lähettäminen, koska:
- Vain relevantit tapahtumat (top 10-15) lähetetään LLM:lle
- Vähemmän tokeneita = halvempi
- Nopeampi vastaus

## Asennus

### 1. Asenna paketit

```bash
pip install openai>=1.0.0 chromadb>=0.4.0 python-dotenv>=1.0.0
```

Tai asenna kaikki riippuvuudet:

```bash
pip install -r requirements.txt
```

### 2. Hanki OpenAI API-avain

1. Mene osoitteeseen: https://platform.openai.com/api-keys
2. Kirjaudu sisään (tai luo tili)
3. Klikkaa "Create new secret key"
4. Kopioi API-avain (alkaa `sk-...`)
5. **Tärkeää:** Tallenna avain turvalliseen paikkaan - et näe sitä uudelleen!

### 3. Aseta API-avain ympäristömuuttujaksi

#### Vaihtoehto A: .env-tiedosto (suositus)

1. Luo `.env`-tiedosto projektin juureen:

```bash
touch .env
```

2. Lisää rivi tiedostoon:

```
OPENAI_API_KEY=sk-tuo-api-avain-tähän
```

3. Varmista, että `.env` on `.gitignore`-tiedostossa (ei commitoida GitHubiin!)

#### Vaihtoehto B: Ympäristömuuttuja suoraan

**macOS/Linux:**
```bash
export OPENAI_API_KEY=sk-tuo-api-avain-tähän
```

**Windows (PowerShell):**
```powershell
$env:OPENAI_API_KEY="sk-tuo-api-avain-tähän"
```

**Windows (CMD):**
```cmd
set OPENAI_API_KEY=sk-tuo-api-avain-tähän
```

### 4. Käynnistä sovellus uudelleen

Jos käytät `.env`-tiedostoa, varmista että Streamlit lukee sen. Voit käyttää `python-dotenv` -pakettia:

```bash
pip install python-dotenv
```

Ja lisää `app/main.py` -tiedoston alkuun:

```python
from dotenv import load_dotenv
load_dotenv()
```

**Huomio:** Jos et aseta API-avainta, AI Assistant -välilehti näyttää ohjeet sen asettamisesta.

## Käyttö

1. Avaa Streamlit-sovellus
2. Siirry "🤖 AI Assistant" -välilehdelle
3. **Ensimmäisellä käyttökerralla:** Vektoritietokanta luodaan automaattisesti (voi kestää hetken)
4. Kysy kysymyksiä rahoitustapahtumistasi, esimerkiksi:
   - "Mikä on suurin kulutuskategoria?"
   - "Kuinka paljon olen kuluttanut tässä kuussa?"
   - "Mitkä ovat top 5 merchantit?"
   - "Mitä olen kuluttanut Prismassa?" (RAG hakee automaattisesti Prisma-tapahtumat)
   - "Anna suosituksia säästämiseen"
   - "Vertaile kulutusta kuukausien välillä"

5. AI Assistant vastaa suomeksi ja antaa konkreettisia analyyseja

## RAG-ratkaisu (Retrieval-Augmented Generation)

### Miten se toimii?

1. **Vektoritietokanta:** Kaikki tapahtumat vektorisoidaan ja tallennetaan Chroma-tietokantaan
2. **Kysymys:** Kun kysyt jotain, järjestelmä luo kysymyksestäsi embedding-vektorin
3. **Haku:** Etsitään top 10-15 relevanttia tapahtumaa vektoritietokannasta
4. **Vastaus:** Vain relevantit tapahtumat lähetetään LLM:lle analysoitavaksi

### Edut

- **Tehokkuus:** Vain relevantit tapahtumat lähetetään (ei koko datasetia)
- **Kustannukset:** Vähemmän tokeneita = halvempi
- **Nopeus:** Nopeampi vastaus
- **Tarkkuus:** LLM saa vain kysymykseen liittyvät tapahtumat

### Vektoritietokanta

- **Sijainti:** `data/processed/vector_db/`
- **Päivitys:** Päivittyy automaattisesti kun Excel-tiedosto muuttuu
- **Ensimmäinen käyttö:** Voi kestää hetken (luodaan embedding-vektorit)

## Ominaisuudet

- **RAG-ratkaisu:** Automaattinen haku relevanttien tapahtumien perusteella
- **Chat-historia:** Keskusteluhistoria säilyy session state:ssa (katoaa sivun päivityksessä)
- **Data-yhteenveto:** Näet datan yhteenvedon laajennettavassa osiossa
- **Tyhjennä historia:** Voit tyhjentää keskusteluhistorian milloin tahansa
- **Automaattinen päivitys:** Vektoritietokanta päivittyy automaattisesti kun data muuttuu

## Vianetsintä

### "OpenAI package is not installed"

**Ratkaisu:**
```bash
pip install openai>=1.0.0
```

### "API key is required" tai "Invalid API key"

**Ratkaisu:**
1. Tarkista, että `.env`-tiedosto on projektin juuressa
2. Tarkista, että `OPENAI_API_KEY` on oikein kirjoitettu
3. Varmista, että et ole commitoinut `.env`-tiedostoa GitHubiin
4. Käynnistä sovellus uudelleen

### "API rate limit exceeded"

**Ratkaisu:**
- Odota hetki ja yritä uudelleen
- Tarkista OpenAI-tilisi käyttörajoitukset: https://platform.openai.com/usage

### "Request timed out"

**Ratkaisu:**
- Yritä uudelleen
- Tarkista internetyhteytesi

## Turvallisuus

- **Älä koskaan commitoi API-avainta GitHubiin!**
- Varmista, että `.env` on `.gitignore`-tiedostossa
- Älä jaa API-avaintasi kenellekään
- Jos avain vuotaa, poista se välittömästi OpenAI-palvelusta ja luo uusi

## Modulaarisuus

AI Assistant on täysin modulaarinen:
- `app/ai_assistant.py` - Chat-UI komponentti
- `src/llm_client.py` - OpenAI API -integraatio
- `src/data_formatter.py` - Datan formatointi
- `src/vector_store.py` - Vektoritietokanta ja RAG-logiikka

Jos et asenna `openai` tai `chromadb` -paketteja, nykyinen koodi toimii normaalisti ilman AI Assistant -ominaisuutta.

## Lisätietoja

- OpenAI API -dokumentaatio: https://platform.openai.com/docs
- Hinnoittelu: https://openai.com/api/pricing
- GPT-3.5-turbo -mallin tiedot: https://platform.openai.com/docs/models/gpt-3-5

