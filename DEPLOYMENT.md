# Streamlit Cloud - Julkaisuohje

## Valmistelu

1. **Puske projekti GitHubiin**

```bash
# Alusta Git (jos ei ole tehty)
git init

# Lisää kaikki tiedostot
git add .

# Tee ensimmäinen commit
git commit -m "Initial commit: Finance Transaction Manager"

# Luo GitHub-repositorio (tee se GitHubissa manuaalisesti)
# Sitten lisää remote ja puske:
git remote add origin https://github.com/KÄYTTÄJÄNIMI/finance_notebook.git
git branch -M main
git push -u origin main
```

## Streamlit Cloud -julkaisu

1. **Mene Streamlit Cloudiin**: https://share.streamlit.io/

2. **Kirjaudu sisään** GitHub-tililläsi

3. **Klikkaa "New app"**

4. **Täytä tiedot**:
   - **Repository**: Valitse `KÄYTTÄJÄNIMI/finance_notebook`
   - **Branch**: `main`
   - **Main file path**: `app/main.py`

5. **Advanced settings** (valinnainen):
   - **Python version**: 3.11
   - **Secrets**: Lisää ympäristömuuttujat:
     ```
     OPENAI_API_KEY=sk-...
     ```

6. **Klikkaa "Deploy"**

## Ympäristömuuttujat (Secrets)

Streamlit Cloudissa voit lisätä ympäristömuuttujat "Secrets" -osiossa:

1. Mene appin asetuksiin
2. Klikkaa "Secrets"
3. Lisää:
   ```toml
   OPENAI_API_KEY = "sk-..."
   ```

Tai käytä `.streamlit/secrets.toml` tiedostoa (mutta **älä** commitoi sitä Gitiin, jos siinä on API-avaimia).

## Tärkeät tiedostot

- `requirements.txt` - Python-riippuvuudet
- `packages.txt` - Järjestelmäpaketit (jos tarvitaan)
- `.streamlit/config.toml` - Streamlit-asetukset
- `.gitignore` - Git-ignorointi

## Ongelmanratkaisu

### Sovellus ei käynnisty

- Tarkista että `requirements.txt` on oikein
- Tarkista että `app/main.py` on oikea pääsovellus
- Tarkista logit Streamlit Cloudissa

### API-avain ei toimi

- Tarkista että Secrets on asetettu oikein
- Tarkista että `.env`-tiedosto ei ole commitoitu (se on .gitignore:ssa)

### Import-virheet

- Varmista että kaikki riippuvuudet ovat `requirements.txt`:ssä
- Tarkista että Python-versio on oikea (3.11)

## Päivitykset

Kun teet muutoksia:

```bash
git add .
git commit -m "Update: kuvaus muutoksista"
git push
```

Streamlit Cloud päivittyy automaattisesti!

