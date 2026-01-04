# Git-asetus ja Streamlit Cloud -julkaisu

## Vaihe 1: Git-repositorion alustus (TEHTY ✅)

Git-repositorio on jo alustettu. Seuraavat vaiheet:

## Vaihe 2: Tee ensimmäinen commit

```bash
# Siirry projektikansioon
cd /path/to/finance_notebook

# Tarkista mitä lisätään
git status

# Lisää kaikki tiedostot
git add .

# Tee ensimmäinen commit
git commit -m "Initial commit: Finance Transaction Manager with AI Assistant"
```

## Vaihe 3: Luo GitHub-repositorio

1. Mene GitHubiin: https://github.com
2. Klikkaa "New repository" (tai "+" → "New repository")
3. Täytä tiedot:
   - **Repository name**: `finance_notebook` (tai haluamasi nimi)
   - **Description**: "Finance Transaction Manager with Streamlit and AI Assistant"
   - **Visibility**: Private (suositus) tai Public
   - **Älä** valitse "Initialize with README" (koska sinulla on jo tiedostoja)
4. Klikkaa "Create repository"

## Vaihe 4: Yhdistä paikallinen repo GitHubiin

GitHub näyttää ohjeet, mutta tässä ne:

```bash
# Lisää remote (korvaa KÄYTTÄJÄNIMI omalla GitHub-käyttäjänimelläsi)
git remote add origin https://github.com/KÄYTTÄJÄNIMI/finance_notebook.git

# Nimeä päähaara main:ksi (jos ei ole jo)
git branch -M main

# Puske GitHubiin
git push -u origin main
```

## Vaihe 5: Julkaise Streamlit Cloudissa

1. **Mene Streamlit Cloudiin**: https://share.streamlit.io/

2. **Kirjaudu sisään** GitHub-tililläsi

3. **Klikkaa "New app"**

4. **Täytä tiedot**:
   - **Repository**: Valitse `KÄYTTÄJÄNIMI/finance_notebook`
   - **Branch**: `main`
   - **Main file path**: `app/main.py`
   - **App URL**: Valitse haluamasi URL (esim. `finance-notebook`)

5. **Advanced settings**:
   - **Python version**: 3.11
   - **Secrets**: Klikkaa "Secrets" ja lisää:
     ```
     OPENAI_API_KEY = "sk-..."
     ```
     (Korvaa `sk-...` oikealla API-avaimellasi)

6. **Klikkaa "Deploy"**

7. Odota muutama minuutti, kun sovellus käynnistyy

## Tärkeät tiedostot

- ✅ `.gitignore` - Estää turhien tiedostojen lisäämisen
- ✅ `.streamlit/config.toml` - Streamlit-asetukset
- ✅ `requirements.txt` - Python-riippuvuudet
- ✅ `packages.txt` - Järjestelmäpaketit (tyhjä, mutta valmis)
- ✅ `DEPLOYMENT.md` - Yksityiskohtaiset julkaisuohjeet

## Päivitykset

Kun teet muutoksia koodiin:

```bash
git add .
git commit -m "Kuvaus muutoksista"
git push
```

Streamlit Cloud päivittyy automaattisesti muutamassa minuutissa!

## Tärkeää

- **Älä** commitoi `.env`-tiedostoa (se on .gitignore:ssa)
- **Älä** commitoi `venv/`-kansiota (se on .gitignore:ssa)
- **Älä** commitoi `data/processed/vector_db/` (se on .gitignore:ssa)
- **Käytä** Streamlit Cloudin Secrets-ominaisuutta API-avaimille

## Ongelmanratkaisu

Jos Streamlit Cloud ei käynnisty:

1. Tarkista `requirements.txt` - kaikki riippuvuudet pitää olla siellä
2. Tarkista että `app/main.py` on oikea pääsovellus
3. Tarkista logit Streamlit Cloudissa (Settings → Logs)
4. Varmista että Python-versio on 3.11

Lisätietoja: Katso `DEPLOYMENT.md`

