"""
Historiallisen Curve CSV-datan migraatio Supabaseen.

Mitä tämä tekee:
  1. Lukee CSV:n ja ajaa sen olemassaolevan pipeline:n läpi
  2. Rakentaa merchant_rules-taulun opitusta historiasta
  3. Inseroi kaikki 1000+ tapahtumaa transactions-tauluun

Ajo:
  pip install supabase python-dotenv
  SUPABASE_URL=... SUPABASE_SERVICE_KEY=... python scripts/migrate_to_supabase.py <csv_path>

  TAI lisää .env:iin SUPABASE_URL ja SUPABASE_SERVICE_KEY ja aja ilman env-muuttujia.
"""

import sys
import os
import hashlib
import re
from collections import defaultdict
from pathlib import Path

# Lisää src/ polkuun jotta voidaan importoida olemassaolevia moduuleja
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

import pandas as pd
from supabase import create_client, Client

from src.pipeline import process_transactions
from src.config import CATEGORY_EN_TO_FI, SUBCATEGORY_EN_TO_FI


# ─── Config ───────────────────────────────────────────────────────────────────

CSV_PATH = sys.argv[1] if len(sys.argv) > 1 else None

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]  # service role key, ei anon

BATCH_SIZE = 100   # Supabase upsert per batch


# ─── Helpers ──────────────────────────────────────────────────────────────────

def make_tx_id(date, merchant, amount, time="") -> str:
    """Deterministinen ID — sama rivi tuottaa aina saman ID:n."""
    raw = f"{date}|{merchant}|{amount:.4f}|{time}"
    return hashlib.md5(raw.encode()).hexdigest()


def parse_note_and_allocation(raw_note: str) -> tuple[str, float]:
    """
    Erottaa note-koodista cost allocation -prosentin.
    'F/50%' → ('F', 0.5)
    'RT'    → ('RT', 1.0)
    ''      → ('', 1.0)
    """
    raw = str(raw_note).strip().strip('"')
    match = re.search(r'/(\d+)%', raw)
    if match:
        pct = float(match.group(1)) / 100
        code = re.sub(r'/\d+%$', '', raw).strip()
        return code, pct
    return raw, 1.0


def batched(lst: list, n: int):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


# ─── Merchant rules -ekstraki raa'asta CSV:stä ────────────────────────────────

def extract_merchant_rules(csv_path: str) -> list[dict]:
    """
    Rakentaa merchant_rules-listan CSV:n historiasta.

    Logiikka:
    - Ryhmittelee (merchant, note_code) → {(category_en, category_fi, second_cat_fi): count}
    - Korkein count voittaa → dominant rule
    - confidence = dominant_count / total_for_combination
    """
    import csv as csv_module
    from src.categorizer import categorize_data
    from src.data_loader import load_and_prepare_data
    from src.data_cleaner import clean_data
    from src.cost_allocator import apply_cost_allocation

    df = load_and_prepare_data(csv_path)
    df = clean_data(df, verbose=False)
    df = apply_cost_allocation(df)
    df = categorize_data(df, verbose=False)

    # (merchant, note_code) → {(cat_en, cat_fi, second_fi): count}
    combos: dict[tuple, dict] = defaultdict(lambda: defaultdict(int))
    last_seen: dict[tuple, str] = {}

    # Lue raaka CSV uudelleen note_code:ta varten (pipeline muuttaa notes-kentän)
    raw_notes: dict[tuple, list] = defaultdict(list)
    with open(csv_path, encoding='utf-8') as f:
        reader = csv_module.DictReader(f)
        for row in reader:
            m = row.get('Merchant', '').strip().strip('"')
            n = row.get('Notes', '').strip().strip('"')
            d = row.get('Date (YYYY-MM-DD as UTC)', '').strip()
            amt_raw = row.get('Txn Amount (Funding Card)', '0').strip()
            try:
                amt = float(amt_raw)
            except ValueError:
                amt = 0.0
            note_code, _ = parse_note_and_allocation(n)
            raw_notes[(m, amt, d)].append(note_code)

    # Yhdistä pipeline-output + raaka note_code
    for _, row in df.iterrows():
        merchant = str(row.get('merchant', '')).strip()
        date_val = str(row.get('date', ''))[:10]
        amount = float(row.get('amount', 0))
        cat_fi = str(row.get('category', ''))
        second_fi = str(row.get('2nd category', ''))

        # Hae alkuperäinen note_code
        note_candidates = raw_notes.get((merchant, amount, date_val), [''])
        note_code = note_candidates[0] if note_candidates else ''

        # Käänteinen käännös fi → en kategorioille
        cat_en = next(
            (k for k, v in CATEGORY_EN_TO_FI.items() if v == cat_fi),
            cat_fi
        )

        key = (merchant, note_code)
        combo_key = (cat_en, cat_fi, second_fi)
        combos[key][combo_key] += 1
        last_seen[key] = date_val

    rules = []
    for (merchant, note_code), combo_counts in combos.items():
        total = sum(combo_counts.values())
        (cat_en, cat_fi, second_fi), dominant_count = max(
            combo_counts.items(), key=lambda x: x[1]
        )
        confidence = round(dominant_count / total, 3)
        rules.append({
            'merchant':       merchant,
            'note_code':      note_code,
            'category_en':    cat_en,
            'category_fi':    cat_fi,
            'second_cat_fi':  second_fi,
            'confidence':     confidence,
            'source':         'historical',
            'hit_count':      total,
            'last_seen':      last_seen.get((merchant, note_code)),
        })

    return rules


# ─── Transaktioiden muodostus ──────────────────────────────────────────────────

def build_transactions(csv_path: str) -> list[dict]:
    """
    Ajaa CSV:n pipeline:n läpi ja muodostaa transactions-listan.
    Merkitsee needs_review=True tapahtumat joissa on useita mahdollisia
    kategorioita (ambiguous merchant + tyhjä note).
    """
    import csv as csv_module

    from src.data_loader import load_and_prepare_data
    from src.data_cleaner import clean_data
    from src.cost_allocator import apply_cost_allocation
    from src.categorizer import categorize_data

    df = load_and_prepare_data(csv_path)
    df = clean_data(df, verbose=False)
    df = apply_cost_allocation(df)
    df = categorize_data(df, verbose=False)

    # Raaka notes alkuperäisestä CSV:stä (ennen pipeline-muutoksia)
    raw_notes_map: dict[tuple, str] = {}
    with open(csv_path, encoding='utf-8') as f:
        reader = csv_module.DictReader(f)
        for row in reader:
            m = row.get('Merchant', '').strip().strip('"')
            d = row.get('Date (YYYY-MM-DD as UTC)', '').strip()
            amt_raw = row.get('Txn Amount (Funding Card)', '0').strip()
            try:
                amt = float(amt_raw)
            except ValueError:
                amt = 0.0
            n = row.get('Notes', '').strip().strip('"')
            raw_notes_map[(m, d, amt)] = n

    txns = []
    for _, row in df.iterrows():
        merchant  = str(row.get('merchant', '')).strip()
        date_val  = str(row.get('date', ''))[:10]
        time_val  = str(row.get('time', ''))
        amount    = float(row.get('amount', 0))
        adj_amt   = float(row.get('adjusted_amount', amount))
        alloc     = float(row.get('cost_allocation', 1.0))
        cat_fi    = str(row.get('category', ''))
        second_fi = str(row.get('2nd category', ''))
        card_last4 = row.get('card_last4')
        card_name  = str(row.get('card', '')) if row.get('card') else None

        cat_en = next(
            (k for k, v in CATEGORY_EN_TO_FI.items() if v == cat_fi),
            cat_fi
        )

        raw_note = raw_notes_map.get((merchant, date_val, amount), '')
        note_code, _ = parse_note_and_allocation(raw_note)

        tx_id = make_tx_id(date_val, merchant, amount, time_val)

        txns.append({
            'id':             tx_id,
            'date':           date_val,
            'time':           time_val,
            'merchant':       merchant,
            'amount':         amount,
            'adjusted_amount': adj_amt,
            'cost_allocation': alloc,
            'currency':       'EUR',
            'category_en':    cat_en,
            'category_fi':    cat_fi,
            'second_cat_fi':  second_fi,
            'note_code':      note_code,
            'note_raw':       raw_note,
            'card_last4':     int(card_last4) if card_last4 and card_last4 != -1 else None,
            'card_name':      card_name,
            'rule_source':    'historical',
            'needs_review':   False,
        })

    return txns


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    if not CSV_PATH:
        print("Käyttö: python scripts/migrate_to_supabase.py <polku/Transactions.csv>")
        sys.exit(1)

    if not Path(CSV_PATH).exists():
        print(f"Tiedostoa ei löydy: {CSV_PATH}")
        sys.exit(1)

    print(f"Yhdistetään Supabaseen...")
    sb: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Yhteys OK\n")

    # ── 1. Merchant rules ──────────────────────────────────────────────────────
    print("Extraktoidaan merchant rules...")
    rules = extract_merchant_rules(CSV_PATH)
    print(f"  {len(rules)} sääntöä löydetty")

    print("  Upsertoidaan merchant_rules...")
    ok = err = 0
    for batch in batched(rules, BATCH_SIZE):
        try:
            sb.table('merchant_rules').upsert(
                batch,
                on_conflict='merchant,note_code'
            ).execute()
            ok += len(batch)
        except Exception as e:
            print(f"  ⚠️  Batch-virhe: {e}")
            err += len(batch)
    print(f"  ✅ {ok} sääntöä insertoitu, {err} virheitä\n")

    # ── 2. Transaktiot ────────────────────────────────────────────────────────
    print("Rakennetaan tapahtumat...")
    txns = build_transactions(CSV_PATH)
    print(f"  {len(txns)} tapahtumaa")

    print("  Upsertoidaan transactions...")
    ok = err = 0
    for batch in batched(txns, BATCH_SIZE):
        try:
            sb.table('transactions').upsert(
                batch,
                on_conflict='id'
            ).execute()
            ok += len(batch)
        except Exception as e:
            print(f"  ⚠️  Batch-virhe: {e}")
            err += len(batch)
    print(f"  ✅ {ok} tapahtumaa insertoitu, {err} virheitä\n")

    # ── 3. Yhteenveto ─────────────────────────────────────────────────────────
    rule_count  = sb.table('merchant_rules').select('id', count='exact').execute().count
    txn_count   = sb.table('transactions').select('id', count='exact').execute().count
    review_count = sb.table('transactions').select('id', count='exact').eq('needs_review', True).execute().count

    print("═" * 50)
    print(f"✅ Migraatio valmis")
    print(f"   merchant_rules:  {rule_count}")
    print(f"   transactions:    {txn_count}")
    print(f"   needs_review:    {review_count}")
    print("═" * 50)


if __name__ == '__main__':
    main()
