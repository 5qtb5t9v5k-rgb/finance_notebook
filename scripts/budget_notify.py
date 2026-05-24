"""
Budget coaching notifier — lähettää Telegram-viestin ja tulostaa konsoliin.

Ajo:
  python scripts/budget_notify.py auto      # Tunnistaa tyypin automaattisesti
  python scripts/budget_notify.py payday    # Palkkapäiväviesti
  python scripts/budget_notify.py weekly    # Viikkoraportti
  python scripts/budget_notify.py alert     # Hälytys (vain jos tarvitaan)
  python scripts/budget_notify.py status    # Tulosta tila ilman lähetystä

Ympäristömuuttujat (.env tai GitHub Secrets):
  SUPABASE_URL          Supabase-projektin URL
  SUPABASE_SERVICE_KEY  Supabase service_role -avain
  TELEGRAM_BOT_TOKEN    Telegram bot -token
  TELEGRAM_CHAT_ID      Käyttäjän Telegram chat_id
"""

import json
import os
import sys
import urllib.request
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

import pandas as pd
from supabase import create_client

from src.budget_coach import (
    format_alert_message,
    format_payday_message,
    format_weekly_message,
    get_budget_status,
    is_payday,
    load_playbook,
)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def load_df() -> pd.DataFrame:
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SERVICE_KEY"]
    sb  = create_client(url, key)
    res = sb.table("transactions").select("*").execute()
    rows = res.data or []
    if not rows:
        return pd.DataFrame()
    df = pd.DataFrame(rows)
    rename = {"category_fi": "category", "second_cat_fi": "2nd category"}
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
    return df


def send_telegram(message: str, token: str, chat_id: str) -> bool:
    url  = f"https://api.telegram.org/bot{token}/sendMessage"
    body = json.dumps(
        {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    ).encode()
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
            return result.get("ok", False)
    except Exception as e:
        print(f"❌ Telegram virhe: {e}")
        return False


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "auto"

    playbook = load_playbook()
    df       = load_df()
    status   = get_budget_status(playbook, df)

    # ── Resolve mode ──────────────────────────────────────────────────────────
    if mode == "auto":
        today = date.today()
        salary_day = playbook["salary"]["day"]
        if is_payday(salary_day):
            mode = "payday"
        elif today.weekday() == 6:  # Sunday
            mode = "weekly"
        else:
            mode = "alert"

    # ── Format message ────────────────────────────────────────────────────────
    if mode == "payday":
        message = format_payday_message(playbook, status)
    elif mode == "weekly":
        message = format_weekly_message(playbook, status)
    elif mode == "alert":
        message = format_alert_message(playbook, status)
        if message is None:
            print("✅ Ei hälytettävää.")
            return
    elif mode == "status":
        # Just print status, no Telegram
        message = format_weekly_message(playbook, status)
        print(message)
        return
    else:
        print(f"Tuntematon mode: {mode}")
        sys.exit(1)

    print(message)
    print()

    # ── Send ──────────────────────────────────────────────────────────────────
    token   = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")

    if not token or not chat_id:
        print("⚠️  TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID puuttuu — ei lähetetty.")
        return

    ok = send_telegram(message, token, chat_id)
    print("✅ Lähetetty!" if ok else "❌ Lähetys epäonnistui.")


if __name__ == "__main__":
    main()
