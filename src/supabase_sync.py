"""
Supabase sync — kaksi toimintoa:

  load_from_supabase()        → pd.DataFrame (kaikki tapahtumat kannasta)
  upsert_csv_to_supabase(f)   → dict (yhteenveto, kutsuu migrate-logiikkaa)

Käyttö Streamlitissä:
  from src.supabase_sync import load_from_supabase, upsert_csv_to_supabase
"""

import os
import tempfile
import hashlib
import re
import csv as csv_module
from collections import defaultdict
from pathlib import Path

import pandas as pd
from supabase import create_client, Client

from src.config import CATEGORY_EN_TO_FI


# ─── Client ───────────────────────────────────────────────────────────────────

def _get_client() -> Client:
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_SERVICE_KEY", "")
    if not url or not key:
        raise RuntimeError("SUPABASE_URL ja SUPABASE_SERVICE_KEY puuttuvat .env:stä")
    return create_client(url, key)


# ─── Load ──────────────────────────────────────────────────────────────────────

def load_from_supabase() -> pd.DataFrame:
    """
    Lataa kaikki tapahtumat Supabasesta → pd.DataFrame.
    Sarakkeet vastaavat pipeline-tulosteen rakennetta.
    """
    sb = _get_client()
    res = sb.table("transactions").select("*").order("date", desc=True).execute()
    rows = res.data or []

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows)

    # Nimeä sarakkeet vastaamaan pipeline-rakennetta
    rename = {
        "category_fi":   "category",
        "second_cat_fi": "2nd category",
        "note_raw":      "notes",
        "card_last4":    "card_last4",
        "card_name":     "card",
        "adjusted_amount": "adjusted_amount",
    }
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})

    # Varmista oikeat tyypit
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"]).dt.date

    return df


# ─── Helpers (kopio migrate_to_supabase.py:stä, DRY myöhemmin) ───────────────

def _make_tx_id(date: str, merchant: str, amount: float, time: str = "") -> str:
    raw = f"{date}|{merchant}|{amount:.4f}|{time}"
    return hashlib.md5(raw.encode()).hexdigest()


def _parse_note(raw: str) -> tuple[str, float]:
    raw = str(raw).strip().strip('"')
    m = re.search(r'/(\d+)%', raw)
    if m:
        pct = float(m.group(1)) / 100
        code = re.sub(r'/\d+%$', '', raw).strip()
        return code, pct
    return raw, 1.0


def _resolve_eur(row: dict) -> tuple[float, bool]:
    # CSV-eksporteissa sarakkeen nimi voi olla välilyönnillä tai ilman
    funding_cur = (row.get('Txn Currency (Funding Card)') or row.get(' Txn Currency (Funding Card)') or '').strip()
    funding_raw = (row.get('Txn Amount (Funding Card)') or row.get(' Txn Amount (Funding Card)') or '0').strip()
    foreign_cur = (row.get('Txn Currency (Foreign Spend)') or row.get(' Txn Currency (Foreign Spend)') or '').strip()
    foreign_raw = (row.get('Txn Amount (Foreign Spend)') or row.get(' Txn Amount (Foreign Spend)') or '0').strip()
    try:
        funding_amt = float(funding_raw)
    except ValueError:
        funding_amt = 0.0
    try:
        foreign_amt = float(foreign_raw)
    except ValueError:
        foreign_amt = 0.0
    if funding_cur == 'EUR' or not funding_cur:
        return funding_amt, False
    if foreign_cur == 'EUR' and foreign_amt > 0:
        return foreign_amt, True
    return funding_amt, True


def _should_exclude(row: dict) -> bool:
    txn_type = row.get(' Type', row.get('Type', '')).strip().upper()
    notes    = row.get(' Notes', row.get('Notes', '')).strip().strip('"')
    return txn_type == 'REFUNDED' or notes in ('del', ' del')


def _batched(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


# ─── Upsert ───────────────────────────────────────────────────────────────────

def upsert_csv_to_supabase(csv_source, batch_size: int = 100) -> dict:
    """
    csv_source: tiedostopolku (str/Path) tai Streamlit UploadedFile.
    Ajaa pipeline:n ja upsertaa Supabaseen.
    Palauttaa yhteenvetodictin.
    """
    from src.data_loader import load_and_prepare_data
    from src.data_cleaner import clean_data
    from src.cost_allocator import apply_cost_allocation
    from src.categorizer import categorize_data

    sb = _get_client()

    # Jos UploadedFile → tallenna temp-tiedostoon
    tmp = None
    if hasattr(csv_source, 'read'):
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
        tmp.write(csv_source.read())
        tmp.flush()
        csv_path = tmp.name
    else:
        csv_path = str(csv_source)

    try:
        # ── Pipeline ──────────────────────────────────────────────────────────
        df = load_and_prepare_data(csv_path)
        df = clean_data(df, verbose=False)
        df = apply_cost_allocation(df)
        df = categorize_data(df, verbose=False)

        # ── Raaka CSV note_code + valuuttakorjaus ─────────────────────────────
        with open(csv_path, encoding='utf-8') as f:
            raw_rows = list(csv_module.DictReader(f))

        raw_map: dict[tuple, dict] = {}
        for r in raw_rows:
            if _should_exclude(r):
                continue
            m   = r.get(' Merchant', r.get('Merchant', '')).strip().strip('"')
            d   = r.get(' Date (YYYY-MM-DD as UTC)', r.get('Date (YYYY-MM-DD as UTC)', '')).strip()
            amt, corrected = _resolve_eur(r)
            n   = r.get(' Notes', r.get('Notes', '')).strip().strip('"')
            raw_map[(m, d, round(amt, 4))] = {'note': n, 'corrected': corrected}

        # ── Merchant rules ────────────────────────────────────────────────────
        note_lookup: dict[tuple, str] = {
            (k[0], k[1], k[2]): v['note'] for k, v in raw_map.items()
        }
        combos:    dict[tuple, dict] = defaultdict(lambda: defaultdict(int))
        last_seen: dict[tuple, str]  = {}

        for _, row in df.iterrows():
            merchant  = str(row.get('merchant', '')).strip()
            date_val  = str(row.get('date', ''))[:10]
            amount    = float(row.get('amount', 0))
            cat_fi    = str(row.get('category', ''))
            second_fi = str(row.get('2nd category', ''))
            cat_en    = next((k for k, v in CATEGORY_EN_TO_FI.items() if v == cat_fi), cat_fi)
            raw_note  = note_lookup.get((merchant, date_val, round(amount, 4)), '')
            note_code, _ = _parse_note(raw_note)
            key = (merchant, note_code)
            combos[key][(cat_en, cat_fi, second_fi)] += 1
            last_seen[key] = date_val

        rules = []
        for (merchant, note_code), combo_counts in combos.items():
            total = sum(combo_counts.values())
            (cat_en, cat_fi, second_fi), dominant = max(combo_counts.items(), key=lambda x: x[1])
            rules.append({
                'merchant':      merchant,
                'note_code':     note_code,
                'category_en':   cat_en,
                'category_fi':   cat_fi,
                'second_cat_fi': second_fi,
                'confidence':    round(dominant / total, 3),
                'source':        'historical',
                'hit_count':     total,
                'last_seen':     last_seen.get((merchant, note_code)),
            })

        rules_ok = rules_err = 0
        for batch in _batched(rules, batch_size):
            try:
                sb.table('merchant_rules').upsert(batch, on_conflict='merchant,note_code').execute()
                rules_ok += len(batch)
            except Exception:
                rules_err += len(batch)

        # ── Transactions ──────────────────────────────────────────────────────
        # Hae locked-rivit
        locked_res = sb.table('transactions').select('id').eq('locked', True).execute()
        locked_ids = {r['id'] for r in (locked_res.data or [])}

        txns = []
        seen_ids: set[str] = set()

        for _, row in df.iterrows():
            merchant   = str(row.get('merchant', '')).strip()
            date_val   = str(row.get('date', ''))[:10]
            time_val   = str(row.get('time', ''))
            amount     = float(row.get('amount', 0))
            adj_amt    = float(row.get('adjusted_amount', amount))
            alloc      = float(row.get('cost_allocation', 1.0))
            cat_fi     = str(row.get('category', ''))
            second_fi  = str(row.get('2nd category', ''))
            card_last4 = row.get('card_last4')
            card_name  = str(row.get('card', '')) if row.get('card') else None
            cat_en     = next((k for k, v in CATEGORY_EN_TO_FI.items() if v == cat_fi), cat_fi)

            raw        = raw_map.get((merchant, date_val, round(amount, 4)), {})
            raw_note   = raw.get('note', '')
            corrected  = raw.get('corrected', False)
            note_code, _ = _parse_note(raw_note)

            tx_id = _make_tx_id(date_val, merchant, amount, time_val)
            if tx_id in locked_ids or tx_id in seen_ids:
                continue
            seen_ids.add(tx_id)

            txns.append({
                'id':              tx_id,
                'date':            date_val,
                'time':            time_val,
                'merchant':        merchant,
                'amount':          amount,
                'adjusted_amount': adj_amt,
                'cost_allocation': alloc,
                'currency':        'EUR',
                'category_en':     cat_en,
                'category_fi':     cat_fi,
                'second_cat_fi':   second_fi,
                'note_code':       note_code,
                'note_raw':        raw_note,
                'card_last4':      int(card_last4) if card_last4 and card_last4 != -1 else None,
                'card_name':       card_name,
                'rule_source':     'historical',
                'needs_review':    corrected,
                'locked':          False,
            })

        txns_ok = txns_err = 0
        for batch in _batched(txns, batch_size):
            try:
                sb.table('transactions').upsert(batch, on_conflict='id').execute()
                txns_ok += len(batch)
            except Exception:
                txns_err += len(batch)

        return {
            'rules_upserted':  rules_ok,
            'rules_errors':    rules_err,
            'txns_upserted':   txns_ok,
            'txns_errors':     txns_err,
            'txns_skipped':    len(locked_ids),
            'needs_review':    sum(1 for t in txns if t['needs_review']),
        }

    finally:
        if tmp:
            Path(tmp.name).unlink(missing_ok=True)


# ─── DB status ────────────────────────────────────────────────────────────────

def get_db_status() -> dict:
    """Nopea yhteenvetotieto kannasta."""
    sb = _get_client()
    txn_res  = sb.table('transactions').select('id', count='exact').execute()
    rev_res  = sb.table('transactions').select('id', count='exact').eq('needs_review', True).execute()
    rule_res = sb.table('merchant_rules').select('id', count='exact').execute()
    return {
        'transactions':   txn_res.count  or 0,
        'needs_review':   rev_res.count  or 0,
        'merchant_rules': rule_res.count or 0,
    }
