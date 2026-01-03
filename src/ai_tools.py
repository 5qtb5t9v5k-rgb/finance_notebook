"""Pandas-based tools for deterministic transaction analysis."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, date
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd


# -------------------------
# Helpers
# -------------------------

def ensure_dt(df: pd.DataFrame) -> pd.DataFrame:
    """Create a reliable datetime column 'dt' from date (+ optional time)."""
    df = df.copy()

    d = pd.to_datetime(df.get("date"), errors="coerce")
    if "time" in df.columns:
        # time might be 'HH:MM:SS' or missing; safe parse to timedelta
        t = pd.to_timedelta(df["time"].astype(str), errors="coerce").fillna(pd.Timedelta(0))
        df["dt"] = d + t
    else:
        df["dt"] = d

    return df


def pick_amount_col(df: pd.DataFrame) -> str:
    return "adjusted_amount" if "adjusted_amount" in df.columns else "amount"


def parse_ymd(s: Optional[str]) -> Optional[pd.Timestamp]:
    if not s:
        return None
    # accept YYYY-MM-DD only
    return pd.to_datetime(s, errors="coerce", format="%Y-%m-%d")


def filter_by_date(df: pd.DataFrame, start_date: Optional[str], end_date: Optional[str]) -> pd.DataFrame:
    """Filter by dt date range. end_date is inclusive (YYYY-MM-DD)."""
    df = ensure_dt(df)
    start = parse_ymd(start_date)
    end = parse_ymd(end_date)

    out = df
    if start is not None and not pd.isna(start):
        out = out[out["dt"] >= start]
    if end is not None and not pd.isna(end):
        # inclusive end -> add 1 day at midnight
        out = out[out["dt"] < (end + pd.Timedelta(days=1))]
    return out


def tx_rows(df: pd.DataFrame, limit: int = 50) -> List[Dict[str, Any]]:
    """Return JSON-serializable rows."""
    amount_col = pick_amount_col(df)
    cols = ["dt", "merchant", amount_col, "category", "2nd category", "card", "notes"]
    cols = [c for c in cols if c in df.columns]

    out = []
    for _, r in df.head(limit).iterrows():
        item = {}
        for c in cols:
            v = r.get(c, None)
            if c == "dt" and pd.notna(v):
                item[c] = pd.Timestamp(v).strftime("%Y-%m-%d %H:%M:%S")
            elif isinstance(v, (pd.Timestamp, datetime)):
                item[c] = v.isoformat()
            elif pd.isna(v):
                item[c] = None
            else:
                # float formatting only for amount-ish
                if c == amount_col:
                    try:
                        item[c] = float(v)
                    except Exception:
                        item[c] = v
                else:
                    item[c] = v
        out.append(item)
    return out


def basic_stats(df: pd.DataFrame) -> Dict[str, Any]:
    amount_col = pick_amount_col(df)
    s = df[amount_col] if amount_col in df.columns else pd.Series(dtype=float)
    return {
        "count": int(len(df)),
        "sum_eur": float(s.sum()) if len(s) else 0.0,
        "avg_eur": float(s.mean()) if len(s) else 0.0,
        "median_eur": float(s.median()) if len(s) else 0.0,
        "max_eur": float(s.max()) if len(s) else 0.0,
    }


# -------------------------
# Tools (10 kpl)
# Each returns {"summary":..., "rows":[...], "meta":...}
# -------------------------

def tool_get_latest(df: pd.DataFrame, n: int = 1, offset: int = 0) -> Dict[str, Any]:
    df = ensure_dt(df).sort_values("dt", ascending=False, na_position="last")
    amount_col = pick_amount_col(df)
    slice_df = df.iloc[offset: offset + n]
    return {
        "summary": {
            "label": "latest",
            "n": int(n),
            "offset": int(offset),
            **basic_stats(slice_df),
        },
        "rows": tx_rows(slice_df, limit=n),
        "meta": {"amount_col": amount_col},
    }


def tool_sum_by_merchant(df: pd.DataFrame, merchant_substr: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
    df = filter_by_date(df, start_date, end_date)
    amount_col = pick_amount_col(df)
    m = df["merchant"].astype(str).str.contains(merchant_substr, case=False, na=False)
    sub = df[m].sort_values("dt", ascending=False)
    return {
        "summary": {
            "label": "sum_by_merchant",
            "merchant_substr": merchant_substr,
            "start_date": start_date,
            "end_date": end_date,
            **basic_stats(sub),
        },
        "rows": tx_rows(sub, limit=50),
        "meta": {"amount_col": amount_col},
    }


def tool_sum_by_category(df: pd.DataFrame, category: str, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
    df = filter_by_date(df, start_date, end_date)
    amount_col = pick_amount_col(df)
    m = df["category"].astype(str).str.lower().eq(category.lower())
    sub = df[m].sort_values("dt", ascending=False)
    return {
        "summary": {
            "label": "sum_by_category",
            "category": category,
            "start_date": start_date,
            "end_date": end_date,
            **basic_stats(sub),
        },
        "rows": tx_rows(sub, limit=50),
        "meta": {"amount_col": amount_col},
    }


def tool_top_transactions(df: pd.DataFrame, n: int = 10, start_date: Optional[str] = None, end_date: Optional[str] = None,
                          category: Optional[str] = None, merchant_substr: Optional[str] = None) -> Dict[str, Any]:
    df = filter_by_date(df, start_date, end_date)
    amount_col = pick_amount_col(df)

    out = df.copy()
    if category:
        out = out[out["category"].astype(str).str.lower().eq(category.lower())]
    if merchant_substr:
        out = out[out["merchant"].astype(str).str.contains(merchant_substr, case=False, na=False)]

    out = out.sort_values(amount_col, ascending=False).head(n)
    return {
        "summary": {
            "label": "top_transactions",
            "n": int(n),
            "filters": {"start_date": start_date, "end_date": end_date, "category": category, "merchant_substr": merchant_substr},
            **basic_stats(out),
        },
        "rows": tx_rows(out, limit=n),
        "meta": {"amount_col": amount_col},
    }


def tool_group_by_month(df: pd.DataFrame, start_date: Optional[str] = None, end_date: Optional[str] = None,
                        field: str = "category", top_k: int = 5) -> Dict[str, Any]:
    df = filter_by_date(df, start_date, end_date)
    df = ensure_dt(df)
    amount_col = pick_amount_col(df)

    if field not in df.columns:
        field = "category"

    df["ym"] = df["dt"].dt.to_period("M").astype(str)
    grp = df.groupby(["ym", field], dropna=False)[amount_col].sum().reset_index()
    # per month take top_k
    rows = []
    for ym, g in grp.groupby("ym"):
        top = g.sort_values(amount_col, ascending=False).head(top_k)
        for _, r in top.iterrows():
            rows.append({
                "month": ym,
                "field": field,
                "value": r[field],
                "sum_eur": float(r[amount_col]),
            })
    return {
        "summary": {"label": "group_by_month", "field": field, "top_k": int(top_k), "start_date": start_date, "end_date": end_date},
        "rows": rows[: 12 * top_k],  # cap
        "meta": {"amount_col": amount_col},
    }


def tool_outliers_large(df: pd.DataFrame, min_amount: float = 100.0, start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
    df = filter_by_date(df, start_date, end_date)
    amount_col = pick_amount_col(df)
    out = df[df[amount_col] >= float(min_amount)].sort_values(amount_col, ascending=False)
    return {
        "summary": {"label": "outliers_large", "min_amount": float(min_amount), "start_date": start_date, "end_date": end_date, **basic_stats(out)},
        "rows": tx_rows(out, limit=50),
        "meta": {"amount_col": amount_col},
    }


def tool_recurring_merchants(df: pd.DataFrame, months: int = 6, min_count: int = 3) -> Dict[str, Any]:
    df = ensure_dt(df)
    amount_col = pick_amount_col(df)

    max_dt = df["dt"].max()
    if pd.isna(max_dt):
        return {"summary": {"label": "recurring_merchants", "months": months, "min_count": min_count, "count": 0}, "rows": [], "meta": {"amount_col": amount_col}}

    start = max_dt - pd.DateOffset(months=int(months))
    sub = df[df["dt"] >= start].copy()
    sub["ym"] = sub["dt"].dt.to_period("M").astype(str)

    g = sub.groupby(["merchant"], dropna=False).agg(
        txn_count=(amount_col, "count"),
        sum_eur=(amount_col, "sum"),
        months_active=("ym", "nunique"),
    ).reset_index()

    g = g[(g["txn_count"] >= int(min_count)) & (g["months_active"] >= 2)].sort_values(["months_active", "sum_eur"], ascending=False)
    rows = []
    for _, r in g.head(30).iterrows():
        rows.append({
            "merchant": r["merchant"],
            "txn_count": int(r["txn_count"]),
            "months_active": int(r["months_active"]),
            "sum_eur": float(r["sum_eur"]),
        })

    return {
        "summary": {"label": "recurring_merchants", "months": int(months), "min_count": int(min_count), "found": len(rows)},
        "rows": rows,
        "meta": {"amount_col": amount_col},
    }


def tool_merchant_breakdown(df: pd.DataFrame, merchant_substr: str, by: str = "category",
                            start_date: Optional[str] = None, end_date: Optional[str] = None) -> Dict[str, Any]:
    df = filter_by_date(df, start_date, end_date)
    amount_col = pick_amount_col(df)

    if by not in df.columns:
        by = "category"

    m = df["merchant"].astype(str).str.contains(merchant_substr, case=False, na=False)
    sub = df[m].copy()

    g = sub.groupby(by, dropna=False)[amount_col].sum().reset_index().sort_values(amount_col, ascending=False)
    rows = [{"by": by, "value": r[by], "sum_eur": float(r[amount_col])} for _, r in g.head(20).iterrows()]
    return {
        "summary": {"label": "merchant_breakdown", "merchant_substr": merchant_substr, "by": by, "start_date": start_date, "end_date": end_date, **basic_stats(sub)},
        "rows": rows,
        "meta": {"amount_col": amount_col},
    }


def tool_category_trend(df: pd.DataFrame, category: str, months: int = 6) -> Dict[str, Any]:
    df = ensure_dt(df)
    amount_col = pick_amount_col(df)

    max_dt = df["dt"].max()
    if pd.isna(max_dt):
        return {"summary": {"label": "category_trend", "category": category, "months": months, "count": 0}, "rows": [], "meta": {"amount_col": amount_col}}

    start = max_dt - pd.DateOffset(months=int(months))
    sub = df[(df["dt"] >= start) & (df["category"].astype(str).str.lower().eq(category.lower()))].copy()
    sub["ym"] = sub["dt"].dt.to_period("M").astype(str)

    g = sub.groupby("ym")[amount_col].sum().reset_index().sort_values("ym")
    rows = [{"month": r["ym"], "sum_eur": float(r[amount_col])} for _, r in g.iterrows()]
    return {
        "summary": {"label": "category_trend", "category": category, "months": int(months), "start_from": str(start.date())},
        "rows": rows,
        "meta": {"amount_col": amount_col},
    }


# Registry
TOOL_REGISTRY = {
    "get_latest": tool_get_latest,
    "sum_by_merchant": tool_sum_by_merchant,
    "sum_by_category": tool_sum_by_category,
    "top_transactions": tool_top_transactions,
    "group_by_month": tool_group_by_month,
    "outliers_large": tool_outliers_large,
    "recurring_merchants": tool_recurring_merchants,
    "merchant_breakdown": tool_merchant_breakdown,
    "category_trend": tool_category_trend,
}

