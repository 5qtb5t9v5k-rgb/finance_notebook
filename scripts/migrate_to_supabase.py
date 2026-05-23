"""
Historiallisen Curve CSV-datan migraatio Supabaseen.

Mitä tämä tekee:
  1. Lukee CSV:n ja ajaa sen olemassaolevan pipeline:n läpi
  2. Rakentaa merchant_rules-taulun opitusta historiasta
  3. Inseroi tapahtumat transactions-tauluun

Korjaukset:
  - Food & Drink → Ulkona syöminen (Curven uudempi kategoria)
  - ALL/USD -valuutat: jos funding_currency != EUR mutta foreign_currency = EUR,
    käytetään foreign_amount EUR-summana
  - locked-kenttä: upsert ei ylikirjoita käsin korjattuja rivejä

Ajo:
  pip install supabase python-dotenv
  python scripts/migrate_to_supabase.py <polku/Transactions.csv>
  (SUPABASE_URL ja SUPABASE_SERVICE_KEY .env:ssä tai env-muuttujina)

Uudelleenajo on turvallista — hash-ID takaa idempotentin upsert-käyttäytymisen.
locked=true rivejä ei ylikirjoiteta.
"""

import sys
import os
import csv as csv_module
import hashlib
import re
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from supabase import create_client, Client
from src.config import CATEGORY_EN_TO_FI


SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
CSV_PATH     = sys.argv[1] if len(sys.argv) > 1 else None
BATCH_SIZE   = 100


# ─── Helpers ──────────────────────────────────────────────────────────────────

def make_tx_id(date: str, merchant: str, amount: float, time: str = "") -> str:
    raw = f"{date}|{merchant}|{amount:.4f}|{time}"
    return hashlib.md5(raw.encode()).hexdigest()


def parse_note_and_allocation(raw_note: str) -> tuple[str, float]:
    """
    'F/50%'      → ('F', 0.5)   kustannusjako
    'H/telkkari' → ('H', 1.0)   vapaa teksti suffixina
    'RT'         → ('RT', 1.0)
    ''           → ('', 1.0)
    """
    raw = str(raw_note).strip().strip('"')
    # Prosenttijako: F/50% → ('F', 0.5)
    match = re.search(r'/(\d+)%', raw)
    if match:
        pct = float(match.group(1)) / 100
        code = re.sub(r'/\d+%.*$', '', raw).strip()
        return code, pct
    # Vapaa teksti suffixina: H/telkkari → ('H', 1.0)
    if '/' in raw:
        code = raw.split('/')[0].strip()
        return code, 1.0
    return raw, 1.0


def resolve_eur_amount(row: dict) -> tuple[float, bool]:
    """
    Palauta (eur_amount, was_corrected).
    Jos funding-valuutta on EUR → käytä suoraan.
    Jos funding-valuutta on jotain muuta (ALL, USD...) mutta foreign = EUR
    → käytä foreign_amount (Curven valuuttabugi).
    """
    # CSV-eksporteissa sarakkeen nimi voi olla välilyönnillä tai ilman
    funding_cur = (row.get('Txn Currency (Funding Card)') or row.get(' Txn Currency (Funding Card)') or '').strip()
    funding_amt_raw = (row.get('Txn Amount (Funding Card)') or row.get(' Txn Amount (Funding Card)') or '0').strip()
    foreign_cur = (row.get('Txn Currency (Foreign Spend)') or row.get(' Txn Currency (Foreign Spend)') or '').strip()
    foreign_amt_raw = (row.get('Txn Amount (Foreign Spend)') or row.get(' Txn Amount (Foreign Spend)') or '0').strip()

    try:
        funding_amt = float(funding_amt_raw)
    except ValueError:
        funding_amt = 0.0
    try:
        foreign_amt = float(foreign_amt_raw)
    except ValueError:
        foreign_amt = 0.0

    if funding_cur == 'EUR' or not funding_cur:
        return funding_amt, False
    if foreign_cur == 'EUR' and foreign_amt > 0:
        return foreign_amt, True
    # Tuntematon tilanne — käytä funding-summaa ja merkitse reviewiin
    return funding_amt, True


def batched(lst: list, n: int):
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def read_raw_csv(csv_path: str) -> list[dict]:
    """Lue CSV säilyttäen alkuperäiset sarakeNimet."""
    with open(csv_path, encoding='utf-8') as f:
        return list(csv_module.DictReader(f))


# ─── Pipeline (kevyt, ilman pandas-riippuvuutta raaka-extraksissa) ────────────

def should_exclude(row: dict) -> bool:
    txn_type = (row.get('Type') or row.get(' Type') or '').strip().upper()
    notes    = (row.get('Notes') or row.get(' Notes') or '').strip().strip('"')
    if txn_type == 'REFUNDED':
        return True
    if notes in ('del', ' del'):
        return True
    return False


# ─── Merchant rules ────────────────────────────────────────────────────────────

def extract_merchant_rules(csv_path: str) -> list[dict]:
    """
    (merchant, note_code) → dominantti (category_en, category_fi, second_cat_fi).
    confidence = dominant_count / total_occurrences_for_this_pair.
    """
    from src.data_loader import load_and_prepare_data
    from src.data_cleaner import clean_data
    from src.cost_allocator import apply_cost_allocation
    from src.categorizer import categorize_data

    df = load_and_prepare_data(csv_path)
    df = clean_data(df, verbose=False)
    df = apply_cost_allocation(df)
    df = categorize_data(df, verbose=False)

    # Raaka note_code per (merchant, date, amount)
    raw_rows = read_raw_csv(csv_path)
    note_lookup: dict[tuple, str] = {}
    for r in raw_rows:
        if should_exclude(r):
            continue
        m   = r.get(' Merchant', r.get('Merchant', '')).strip().strip('"')
        d   = r.get(' Date (YYYY-MM-DD as UTC)', r.get('Date (YYYY-MM-DD as UTC)', '')).strip()
        amt, _ = resolve_eur_amount(r)
        n   = r.get(' Notes', r.get('Notes', '')).strip().strip('"')
        note_lookup[(m, d, round(amt, 4))] = n

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
        note_code, _ = parse_note_and_allocation(raw_note)

        key       = (merchant, note_code)
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
    return rules


# ─── Transactions ─────────────────────────────────────────────────────────────

def build_transactions(csv_path: str) -> list[dict]:
    from src.data_loader import load_and_prepare_data
    from src.data_cleaner import clean_data
    from src.cost_allocator import apply_cost_allocation
    from src.categorizer import categorize_data

    df = load_and_prepare_data(csv_path)
    df = clean_data(df, verbose=False)
    df = apply_cost_allocation(df)
    df = categorize_data(df, verbose=False)

    # Raaka data: note_code + valuuttakorjaus
    raw_rows = read_raw_csv(csv_path)
    raw_map: dict[tuple, dict] = {}
    for r in raw_rows:
        if should_exclude(r):
            continue
        m   = r.get(' Merchant', r.get('Merchant', '')).strip().strip('"')
        d   = r.get(' Date (YYYY-MM-DD as UTC)', r.get('Date (YYYY-MM-DD as UTC)', '')).strip()
        amt, corrected = resolve_eur_amount(r)
        n   = r.get(' Notes', r.get('Notes', '')).strip().strip('"')
        key = (m, d, round(amt, 4))
        raw_map[key] = {'note': n, 'currency_corrected': corrected}

    txns = []
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
        corrected  = raw.get('currency_corrected', False)
        note_code, _ = parse_note_and_allocation(raw_note)

        txns.append({
            'id':              make_tx_id(date_val, merchant, amount, time_val),
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
            'needs_review':    corrected,   # valuuttakorjatut → review
            'locked':          False,
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

    print("Yhdistetään Supabaseen...")
    sb: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✅ Yhteys OK\n")

    # ── 1. Merchant rules ──────────────────────────────────────────────────────
    print("Extraktoidaan merchant rules...")
    rules = extract_merchant_rules(CSV_PATH)
    print(f"  {len(rules)} sääntöä")

    ok = err = 0
    for batch in batched(rules, BATCH_SIZE):
        try:
            sb.table('merchant_rules').upsert(
                batch, on_conflict='merchant,note_code'
            ).execute()
            ok += len(batch)
        except Exception as e:
            print(f"  ⚠️  {e}")
            err += len(batch)
    print(f"  ✅ {ok} insertoitu, {err} virheitä\n")

    # ── 2. Transactions ───────────────────────────────────────────────────────
    print("Rakennetaan tapahtumat...")
    txns = build_transactions(CSV_PATH)
    currency_fixed = sum(1 for t in txns if t['needs_review'])
    print(f"  {len(txns)} tapahtumaa ({currency_fixed} valuuttakorjattua → needs_review)")

    # Hae locked-rivit etukäteen — näitä ei ylikirjoiteta
    locked_ids: set[str] = set()
    try:
        res = sb.table('transactions').select('id').eq('locked', True).execute()
        locked_ids = {r['id'] for r in (res.data or [])}
        if locked_ids:
            print(f"  ⚠️  {len(locked_ids)} lukittua riviä — ohitetaan")
    except Exception:
        pass

    # Deduploi saman hash-ID:n rivit (sama date+merchant+amount+time)
    seen_ids: set[str] = set()
    deduped = []
    for t in txns:
        if t['id'] not in locked_ids and t['id'] not in seen_ids:
            deduped.append(t)
            seen_ids.add(t['id'])
    dupes = len(txns) - len(deduped)
    if dupes:
        print(f"  ℹ️  {dupes} duplikaattia poistettu (sama hash)")
    to_upsert = deduped

    ok = err = 0
    for batch in batched(to_upsert, BATCH_SIZE):
        try:
            sb.table('transactions').upsert(
                batch, on_conflict='id'
            ).execute()
            ok += len(batch)
        except Exception as e:
            print(f"  ⚠️  {e}")
            err += len(batch)
    print(f"  ✅ {ok} insertoitu/päivitetty, {err} virheitä\n")

    # ── 3. Yhteenveto ─────────────────────────────────────────────────────────
    rule_count   = sb.table('merchant_rules').select('id', count='exact').execute().count
    txn_count    = sb.table('transactions').select('id', count='exact').execute().count
    review_count = sb.table('transactions').select('id', count='exact').eq('needs_review', True).execute().count
    locked_count = sb.table('transactions').select('id', count='exact').eq('locked', True).execute().count

    print("═" * 50)
    print("✅ Migraatio valmis")
    print(f"   merchant_rules : {rule_count}")
    print(f"   transactions   : {txn_count}")
    print(f"   needs_review   : {review_count}")
    print(f"   locked         : {locked_count}")
    print("═" * 50)


if __name__ == '__main__':
    main()
