# Streamlit Cloud - Deployment Guide

## Quick Start

Your app is ready to deploy! Just follow these steps:

### Step 1: Deploy to Streamlit Cloud

1. **Go to Streamlit Cloud**: https://share.streamlit.io/

2. **Sign in** with your GitHub account

3. **Click "New app"**

4. **Fill in the details**:
   - **Repository**: `5qtb5t9v5k-rgb/finance_notebook`
   - **Branch**: `main`
   - **Main file path**: `app/main.py`

5. **Click "Deploy"**

### Step 2: Configure Secrets (Required for AI Features)

After deployment, configure your OpenAI API key:

1. Go to your app's **Settings** (⚙️ icon)
2. Click **Secrets**
3. Add the following (TOML format):

```toml
OPENAI_API_KEY = "sk-your-api-key-here"
```

4. Click **Save**

The app will automatically reload with the new secrets.

---

## Detailed Instructions

### Prerequisites

- GitHub account
- Streamlit Cloud account (free)
- OpenAI API key (for AI features)

### Important Files

| File | Purpose |
|------|---------|
| `requirements.txt` | Python dependencies |
| `packages.txt` | System packages (if needed) |
| `.streamlit/config.toml` | Streamlit configuration |
| `.streamlit/secrets.toml.example` | Example secrets format |

### Secrets Format

Streamlit Cloud uses TOML format for secrets:

```toml
# Required for AI Assistant and AI-Powered Insights
OPENAI_API_KEY = "sk-your-api-key-here"

# Optional settings
# DEFAULT_CSV_PATH = "/path/to/file.csv"
# DEFAULT_EXCEL_PATH = "/path/to/output.xlsx"
```

**Important**: Never commit your actual secrets to Git!

---

## Troubleshooting

### App doesn't start

1. Check the logs: App Settings → Logs
2. Verify `requirements.txt` has all dependencies
3. Ensure `app/main.py` is the correct entry point
4. Check Python version (recommended: 3.11)

### AI features don't work

1. Verify OPENAI_API_KEY is set in Secrets
2. Check the format (must be TOML with quotes)
3. Ensure the API key is valid and has credits

### Import errors

1. Add missing packages to `requirements.txt`
2. Redeploy the app

---

## Updates

When you push changes to GitHub, Streamlit Cloud automatically redeploys:

```bash
git add .
git commit -m "Your update message"
git push
```

The app updates within 1-2 minutes.

---

## Local Development

For local testing before deployment:

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file with your API key
echo 'OPENAI_API_KEY=sk-...' > .env

# Run the app
streamlit run app/main.py
```

---

## Support

- Streamlit Cloud Docs: https://docs.streamlit.io/streamlit-community-cloud
- OpenAI API Docs: https://platform.openai.com/docs