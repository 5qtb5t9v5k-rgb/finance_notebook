"""
Kertaluonteinen Gmail OAuth2 -kirjautuminen.

Ajo KERRAN lokaalisti → saat refresh_token:n → kopioi GitHub Secretsiin.

Vaatii:
  1. Google Cloud Console → OAuth 2.0 Client ID (Desktop app)
  2. Lataa credentials.json projektin juureen

Ajo:
  python scripts/gmail_auth_setup.py

Tulostaa:
  GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, GMAIL_REFRESH_TOKEN
  → lisää nämä GitHub Secrets -sivulle
"""

import json
from pathlib import Path

try:
    from google_auth_oauthlib.flow import InstalledAppFlow
except ImportError:
    print("Asenna ensin: pip install google-auth-oauthlib")
    raise

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]
CREDENTIALS_FILE = Path(__file__).parent.parent / "credentials.json"


def main():
    if not CREDENTIALS_FILE.exists():
        print(f"""
❌ Tiedostoa ei löydy: {CREDENTIALS_FILE}

Tee näin:
  1. Mene https://console.cloud.google.com/
  2. Luo projekti tai valitse olemassa oleva
  3. APIs & Services → Enable APIs → Gmail API → Enable
  4. APIs & Services → Credentials → Create Credentials → OAuth 2.0 Client ID
  5. Application type: Desktop app
  6. Lataa JSON → tallenna nimellä 'credentials.json' projektin juureen
  7. Aja tämä skripti uudelleen
""")
        return

    print("🌐 Avataan selain Gmail-kirjautumista varten...")
    print("   (kirjaudu Google-tilillä juho.v.rissanen@gmail.com)\n")

    flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
    creds = flow.run_local_server(port=0)

    print("\n" + "═" * 60)
    print("✅ Kirjautuminen onnistui!")
    print("   Kopioi nämä arvot GitHub → Settings → Secrets → Actions:\n")
    print(f"GMAIL_CLIENT_ID     = {creds.client_id}")
    print(f"GMAIL_CLIENT_SECRET = {creds.client_secret}")
    print(f"GMAIL_REFRESH_TOKEN = {creds.refresh_token}")
    print("═" * 60)

    # Tallenna myös .gmail_token.json:iin varmuuden vuoksi
    token_file = Path(__file__).parent.parent / ".gmail_token.json"
    with open(token_file, "w") as f:
        json.dump(
            {
                "client_id": creds.client_id,
                "client_secret": creds.client_secret,
                "refresh_token": creds.refresh_token,
            },
            f,
            indent=2,
        )
    print(f"\n💾 Tallennettu myös: {token_file}")
    print("   (älä committaa tätä tiedostoa — .gitignore suojaa sen)\n")


if __name__ == "__main__":
    main()
