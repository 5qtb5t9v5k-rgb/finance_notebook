"""
Budget coaching logic.

Funktiot:
  load_playbook()              → dict          (lukee config/playbook.yaml)
  get_payday(year, month)      → date          (13. tai edell. arkipäivä)
  is_payday()                  → bool
  get_budget_status(pb, df)    → dict          (kuukauden tilanne)
  format_payday_message(...)   → str
  format_weekly_message(...)   → str
  format_alert_message(...)    → str | None    (None = ei hälytystä)
"""

import calendar
from datetime import date
from pathlib import Path
from typing import Optional

import pandas as pd
import yaml

PLAYBOOK_PATH = Path(__file__).parent.parent / "config" / "playbook.yaml"


# ─── Config ───────────────────────────────────────────────────────────────────

def load_playbook() -> dict:
    with open(PLAYBOOK_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


# ─── Payday helpers ───────────────────────────────────────────────────────────

def get_payday(year: int, month: int, salary_day: int = 13) -> date:
    """Return actual payday: salary_day or previous business day if weekend."""
    # Cap to last day of month (e.g. Feb)
    last_day = calendar.monthrange(year, month)[1]
    day = min(salary_day, last_day)
    d = date(year, month, day)
    # Walk back over Saturday (5) and Sunday (6)
    while d.weekday() >= 5:
        d = d.replace(day=d.day - 1)
    return d


def is_payday(salary_day: int = 13) -> bool:
    today = date.today()
    return today == get_payday(today.year, today.month, salary_day)


# ─── Budget status ────────────────────────────────────────────────────────────

def get_budget_status(playbook: dict, df: pd.DataFrame) -> dict:
    """
    Calculate current month budget status from df.
    df must have columns: date, category, adjusted_amount.
    """
    today = date.today()
    days_in_month = calendar.monthrange(today.year, today.month)[1]

    # Filter to current month
    month_df = pd.DataFrame()
    if not df.empty and "date" in df.columns:
        tmp = df.copy()
        tmp["date"] = pd.to_datetime(tmp["date"], errors="coerce")
        mask = (tmp["date"].dt.year == today.year) & (tmp["date"].dt.month == today.month)
        month_df = tmp[mask]

    # Total spending
    amt_col = "adjusted_amount" if "adjusted_amount" in month_df.columns else "amount"
    total_spent = float(month_df[amt_col].sum()) if not month_df.empty else 0.0

    total_budget = playbook["budget"]["total_monthly"]

    # Per-category
    cat_budgets: dict = playbook["budget"].get("categories", {})
    cat_status: dict = {}

    if not month_df.empty and "category" in month_df.columns:
        cat_spending = month_df.groupby("category")[amt_col].sum()
        for cat, budget in cat_budgets.items():
            if budget <= 0:
                continue
            spent = float(cat_spending.get(cat, 0.0))
            cat_status[cat] = {
                "spent": spent,
                "budget": budget,
                "pct": spent / budget,
                "remaining": budget - spent,
            }

    return {
        "total_spent": total_spent,
        "total_budget": total_budget,
        "total_pct": total_spent / total_budget if total_budget else 0.0,
        "total_remaining": total_budget - total_spent,
        "categories": cat_status,
        "days_passed": today.day,
        "days_in_month": days_in_month,
        "today": today,
    }


# ─── Message formatters ───────────────────────────────────────────────────────

def _bar(pct: float, width: int = 8) -> str:
    filled = min(int(pct * width), width)
    return "█" * filled + "░" * (width - filled)


def format_payday_message(playbook: dict, status: dict) -> str:
    today: date = status["today"]
    salary     = playbook["salary"]["monthly_net"]
    total_bud  = status["total_budget"]
    savings    = playbook["budget"].get("savings_target", 0)
    days_left  = status["days_in_month"] - today.day
    daily_bud  = total_bud / status["days_in_month"]

    lines = [
        f"💰 *Palkkapäivä {today.day}.{today.month}.* — budjetti käynnissä!",
        f"",
        f"Netto: *{salary:,.0f} €*",
        f"Kulubudjetti: *{total_bud:,.0f} €*",
        f"Säästötavoite: *{savings:,.0f} €*",
        f"",
        f"📅 Kuussa jäljellä *{days_left} pv* — päiväbudjetti *{daily_bud:.0f} €/pv*",
    ]

    if status["total_spent"] > 0:
        lines += [
            f"",
            f"Kulunut tässä kuussa jo: *{status['total_spent']:.0f} €*",
            f"Jäljellä: *{status['total_remaining']:.0f} €*",
        ]

    if status["categories"]:
        lines += ["", "*Kategoriarajat:*"]
        for cat, info in status["categories"].items():
            bar = _bar(info["pct"])
            lines.append(f"  `{bar}` {cat}: {info['spent']:.0f} / {info['budget']:.0f} €")

    return "\n".join(lines)


def format_weekly_message(playbook: dict, status: dict) -> str:
    today: date   = status["today"]
    days_passed   = status["days_passed"]
    days_in_month = status["days_in_month"]
    days_left     = days_in_month - days_passed
    total_pct     = status["total_pct"]
    expected_pct  = days_passed / days_in_month

    if total_pct > 1.0:
        pace_emoji = "🔴"
    elif total_pct > expected_pct * 1.10:
        pace_emoji = "🟡"
    else:
        pace_emoji = "🟢"

    lines = [
        f"📊 *Viikkoraportti — {today.day}.{today.month}.*",
        f"",
        f"{pace_emoji} Kulutettu: *{status['total_spent']:.0f} € / {status['total_budget']:.0f} €*"
        f" ({total_pct*100:.0f}%)",
        f"⏱ Kuusta kulunut {days_passed}/{days_in_month} pv"
        f" ({expected_pct*100:.0f}%) — jäljellä *{days_left} pv*",
    ]

    if status["categories"]:
        lines += ["", "*Kategoriat:*"]
        sorted_cats = sorted(
            status["categories"].items(), key=lambda x: x[1]["pct"], reverse=True
        )
        for cat, info in sorted_cats:
            bar = _bar(info["pct"])
            flag = " 🔴" if info["pct"] >= 1.0 else (" ⚠️" if info["pct"] >= 0.8 else "")
            lines.append(
                f"  `{bar}` {cat}: {info['spent']:.0f}/{info['budget']:.0f} €{flag}"
            )

    remaining = status["total_remaining"]
    if remaining >= 0:
        lines.append(f"\n💚 Jäljellä: *{remaining:.0f} €* ({days_left} pvää)")
    else:
        lines.append(f"\n🔴 Budjetti ylitetty *{abs(remaining):.0f} €*!")

    return "\n".join(lines)


def format_alert_message(playbook: dict, status: dict) -> Optional[str]:
    """Returns alert message if any category is near/over budget, else None."""
    warn = playbook["alerts"]["warning_threshold"]
    crit = playbook["alerts"]["critical_threshold"]

    alerts = []
    for cat, info in status["categories"].items():
        if info["pct"] >= crit:
            alerts.append(
                f"🔴 *{cat}*: {info['spent']:.0f}/{info['budget']:.0f} € — YLITETTY!"
            )
        elif info["pct"] >= warn:
            alerts.append(
                f"🟡 *{cat}*: {info['spent']:.0f}/{info['budget']:.0f} € ({info['pct']*100:.0f}%)"
            )

    if not alerts:
        return None

    return "⚠️ *Budjettihälytys*\n\n" + "\n".join(alerts)
