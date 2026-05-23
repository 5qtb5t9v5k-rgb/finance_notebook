"""
Gmail Watcher — hakee uusimman Curve CSV:n Gmailista.

Etsii emailin "Your Curve Export is Ready" → lataa CSV-liitteen
→ merkitsee prosessoiduksi (label: curve-processed) → palauttaa polun stdout:iin.

Ympäristömuuttujat:
  GMAIL_CLIENT_ID
  GMAIL_CLIENT_SECRET
  GMAIL_REFRESH_TOKEN

Ajo lokaalisti:
  python scripts/gmail_watcher.py --output /tmp/transactions.csv

Exit code:
  0 = uusi CSV löytyi ja ladattu
  1 = ei uusia emaileja (normaali tilanne, Action skippaa migraation)
"""

import os
import sys
import base64
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


GMAIL_CLIENT_ID     = os.environ["GMAIL_CLIENT_ID"]
GMAIL_CLIENT_SECRET = os.environ["GMAIL_CLIENT_SECRET"]
GMAIL_REFRESH_TOKEN = os.environ["GMAIL_REFRESH_TOKEN"]

CURVE_SUBJECT    = "Your Curve Export is Ready"
PROCESSED_LABEL  = "curve-processed"
SCOPES           = ["https://www.googleapis.com/auth/gmail.modify"]


# ─── Gmail client ─────────────────────────────────────────────────────────────

def get_service():
    creds = Credentials(
        token=None,
        refresh_token=GMAIL_REFRESH_TOKEN,
        client_id=GMAIL_CLIENT_ID,
        client_secret=GMAIL_CLIENT_SECRET,
        token_uri="https://oauth2.googleapis.com/token",
        scopes=SCOPES,
    )
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


# ─── Label helpers ────────────────────────────────────────────────────────────

def get_or_create_label(service, name: str) -> str:
    """Palauta label_id, luo label jos ei ole olemassa."""
    labels = service.users().labels().list(userId="me").execute().get("labels", [])
    for lbl in labels:
        if lbl["name"] == name:
            return lbl["id"]
    created = service.users().labels().create(
        userId="me",
        body={
            "name": name,
            "labelListVisibility": "labelShow",
            "messageListVisibility": "show",
        },
    ).execute()
    print(f"  📌 Luotiin Gmail-label: {name}")
    return created["id"]


# ─── Email search & download ──────────────────────────────────────────────────

def find_unprocessed(service, processed_label_id: str) -> list[dict]:
    """Etsi Curve-exportit joita ei ole vielä prosessoitu."""
    query = f'subject:"{CURVE_SUBJECT}" has:attachment -label:{PROCESSED_LABEL}'
    result = (
        service.users()
        .messages()
        .list(userId="me", q=query, maxResults=10)
        .execute()
    )
    return result.get("messages", [])


def download_csv(service, message_id: str, output_path: str) -> bool:
    """Lataa CSV-liite. Palauttaa True jos onnistui."""
    msg = (
        service.users()
        .messages()
        .get(userId="me", id=message_id, format="full")
        .execute()
    )

    # Rekursiivinen osien läpikäynti (multipart-sähköpostit)
    def walk_parts(parts):
        for part in parts:
            fname = part.get("filename", "")
            if fname.lower().endswith(".csv"):
                body = part.get("body", {})
                att_id = body.get("attachmentId")
                if att_id:
                    att = (
                        service.users()
                        .messages()
                        .attachments()
                        .get(userId="me", messageId=message_id, id=att_id)
                        .execute()
                    )
                    data = base64.urlsafe_b64decode(att["data"])
                    with open(output_path, "wb") as f:
                        f.write(data)
                    print(f"  ✅ CSV ladattu: {output_path} ({len(data):,} B)")
                    return True
            # Nested parts
            sub = part.get("parts", [])
            if sub and walk_parts(sub):
                return True
        return False

    payload = msg.get("payload", {})
    parts = payload.get("parts", [])

    # Joskus liite on suoraan payloadissa
    if not parts:
        parts = [payload]

    return walk_parts(parts)


def mark_processed(service, message_id: str, processed_label_id: str):
    """Lisää 'curve-processed' label — ei ladata uudelleen."""
    service.users().messages().modify(
        userId="me",
        id=message_id,
        body={
            "addLabelIds": [processed_label_id],
            "removeLabelIds": ["UNREAD"],
        },
    ).execute()
    print(f"  📬 Merkitty prosessoiduksi (msg {message_id[:12]}...)")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Lataa uusin Curve CSV Gmailista")
    parser.add_argument(
        "--output",
        default="/tmp/curve_transactions.csv",
        help="Mihin CSV tallennetaan",
    )
    args = parser.parse_args()

    print("📧 Gmail Watcher käynnistetty...")

    try:
        service = get_service()
    except Exception as e:
        print(f"  ❌ Gmail-autentikaatio epäonnistui: {e}")
        sys.exit(1)

    processed_label_id = get_or_create_label(service, PROCESSED_LABEL)
    messages = find_unprocessed(service, processed_label_id)

    if not messages:
        print("  ℹ️  Ei uusia Curve-exporteja — ohitetaan.")
        sys.exit(1)

    print(f"  📨 {len(messages)} uutta Curve-exportia löytyi")

    # Ota uusin (listan ensimmäinen = uusin)
    message_id = messages[0]["id"]

    if download_csv(service, message_id, args.output):
        mark_processed(service, message_id, processed_label_id)
        # Tulosta polku stdout:iin → GitHub Action lukee sen
        print(args.output)
        sys.exit(0)
    else:
        print("  ⚠️  CSV-liitettä ei löydy viestistä")
        sys.exit(1)


if __name__ == "__main__":
    main()
