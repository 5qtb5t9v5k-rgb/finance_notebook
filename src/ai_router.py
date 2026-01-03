"""Router for selecting tools and parameters based on user queries."""

from __future__ import annotations

import json
import re
from datetime import datetime, date, timedelta
from typing import Any, Dict, List, Optional, Tuple

try:
    from zoneinfo import ZoneInfo
except ImportError:
    # Python < 3.9 fallback
    try:
        from backports.zoneinfo import ZoneInfo
    except ImportError:
        # Ultimate fallback - use UTC
        ZoneInfo = None

ALLOWED_TOOLS = {
    "none",
    "get_latest",
    "sum_by_merchant",
    "sum_by_category",
    "top_transactions",
    "group_by_month",
    "outliers_large",
    "recurring_merchants",
    "merchant_breakdown",
    "category_trend",
}

PERIODS = {
    "last_7_days",
    "last_30_days",
    "last_90_days",
    "this_month",
    "last_month",
    "this_year",
    "last_year",
}

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _today_hel() -> date:
    """Get today's date in Helsinki timezone."""
    if ZoneInfo:
        return datetime.now(ZoneInfo("Europe/Helsinki")).date()
    else:
        # Fallback to UTC
        return datetime.now().date()


def _month_start(d: date) -> date:
    """Get first day of month for given date."""
    return date(d.year, d.month, 1)


def _prev_month_range(d: date) -> tuple[date, date]:
    """Get previous month start and end dates."""
    first_this = _month_start(d)
    last_prev = first_this - timedelta(days=1)
    first_prev = date(last_prev.year, last_prev.month, 1)
    return first_prev, last_prev


def expand_period(args: dict, today: date | None = None) -> dict:
    """If args contains 'period', deterministically set start_date/end_date."""
    if today is None:
        today = _today_hel()

    period = args.get("period")
    if not period:
        return args

    if period not in PERIODS:
        args["period"] = None
        return args

    if period == "last_7_days":
        start, end = today - timedelta(days=6), today
    elif period == "last_30_days":
        start, end = today - timedelta(days=29), today
    elif period == "last_90_days":
        start, end = today - timedelta(days=89), today
    elif period == "this_month":
        start, end = _month_start(today), today
    elif period == "last_month":
        start, end = _prev_month_range(today)
    elif period == "this_year":
        start, end = date(today.year, 1, 1), today
    elif period == "last_year":
        start, end = date(today.year - 1, 1, 1), date(today.year - 1, 12, 31)
    else:
        args["period"] = None
        return args

    # store as YYYY-MM-DD
    args["start_date"] = start.strftime("%Y-%m-%d")
    args["end_date"] = end.strftime("%Y-%m-%d")
    # Remove period after expansion
    args.pop("period", None)
    return args


def router_system_prompt() -> str:
    """Generate router system prompt with current date."""
    today = _today_hel().strftime("%Y-%m-%d")
    return f"""Olet reititin (router) rahoitustapahtumabotille.
Palauta AINOASTAAN JSON: {{"tool":"...","args":{{...}}}}.

TÄNÄÄN ON {today} (Europe/Helsinki). Älä arvaa päivämääriä käsin.

KUN KÄYTTÄJÄ PYYTÄÄ SUHTEELLISTA AIKAA, KÄYTÄ 'period' ARVOA:
- last_7_days, last_30_days, last_90_days
- this_month, last_month
- this_year, last_year

Esimerkki:
{{"tool":"sum_by_merchant","args":{{"merchant_substr":"Prisma","period":"last_month"}}}}

SALLITUT TYÖKALUT:
- none
- get_latest (n, offset)
- sum_by_merchant (merchant_substr, period?, start_date?, end_date?)
- sum_by_category (category, period?, start_date?, end_date?)
- top_transactions (n, period?, start_date?, end_date?, category?, merchant_substr?)
- group_by_month (period?, start_date?, end_date?, field?, top_k?)
- outliers_large (min_amount, period?, start_date?, end_date?)
- recurring_merchants (months, min_count)
- merchant_breakdown (merchant_substr, by?, period?, start_date?, end_date?)
- category_trend (category, months)

SÄÄNNÖT:
- Palauta JSON, ei markdownia, ei selityksiä.
- Jos kysymys on "viimeisin / edellinen" -> get_latest.
- Jos et pysty valitsemaan turvallisesti parametreja -> tool="none".
"""


def _extract_json(text: str) -> Optional[str]:
    """Extract first JSON object from text if model leaked extra tokens."""
    if not text:
        return None
    text = text.strip()
    if text.startswith("{") and text.endswith("}"):
        return text
    # find first {...} block
    m = re.search(r"\{.*\}", text, flags=re.DOTALL)
    return m.group(0) if m else None


def parse_router_output(text: str) -> Dict[str, Any]:
    """Parse router output text to JSON dict."""
    raw = _extract_json(text) or "{}"
    try:
        return json.loads(raw)
    except Exception:
        return {"tool": "none", "args": {}}


def validate_plan(plan: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], List[str]]:
    """Validate and clean router plan."""
    errors: List[str] = []
    tool = (plan.get("tool") or "none").strip()
    args = plan.get("args") or {}

    if tool not in ALLOWED_TOOLS:
        errors.append(f"Unknown tool: {tool}")
        tool = "none"
        args = {}

    if not isinstance(args, dict):
        errors.append("args must be an object")
        args = {}

    # Period normalisointi (kaikille työkaluille joissa on date range)
    if "period" in args:
        v = args.get("period")
        args["period"] = str(v).strip() if v is not None else None
        args = expand_period(args)  # Deterministic expansion

    def clamp_int(name: str, default: int, lo: int, hi: int):
        v = args.get(name, default)
        try:
            v = int(v)
        except Exception:
            errors.append(f"{name} must be int")
            v = default
        v = max(lo, min(hi, v))
        args[name] = v

    def clamp_float(name: str, default: float, lo: float, hi: float):
        v = args.get(name, default)
        try:
            v = float(v)
        except Exception:
            errors.append(f"{name} must be number")
            v = default
        v = max(lo, min(hi, v))
        args[name] = v

    def norm_str(name: str, max_len: int = 80):
        v = args.get(name, "")
        if v is None:
            v = ""
        v = str(v).strip()
        if len(v) > max_len:
            v = v[:max_len]
        args[name] = v

    def date_field(name: str):
        v = args.get(name, None)
        if v in (None, ""):
            args[name] = None
            return
        v = str(v).strip()
        if not DATE_RE.match(v):
            errors.append(f"{name} must be YYYY-MM-DD")
            args[name] = None
        else:
            args[name] = v

    # Tool-specific validation
    if tool == "get_latest":
        clamp_int("n", default=1, lo=1, hi=10)
        clamp_int("offset", default=0, lo=0, hi=50)

    elif tool == "sum_by_merchant":
        norm_str("merchant_substr", max_len=60)
        if not args["merchant_substr"]:
            errors.append("merchant_substr required")
            tool = "none"
            args = {}
        else:
            date_field("start_date")
            date_field("end_date")

    elif tool == "sum_by_category":
        norm_str("category", max_len=60)
        if not args["category"]:
            errors.append("category required")
            tool = "none"
            args = {}
        else:
            date_field("start_date")
            date_field("end_date")

    elif tool == "top_transactions":
        clamp_int("n", default=10, lo=1, hi=50)
        date_field("start_date")
        date_field("end_date")
        if "category" in args:
            norm_str("category", max_len=60)
            if args["category"] == "":
                args["category"] = None
        if "merchant_substr" in args:
            norm_str("merchant_substr", max_len=60)
            if args["merchant_substr"] == "":
                args["merchant_substr"] = None

    elif tool == "group_by_month":
        date_field("start_date")
        date_field("end_date")
        norm_str("field", max_len=30)
        clamp_int("top_k", default=5, lo=1, hi=10)
        if args.get("field") in ("", None):
            args["field"] = "category"

    elif tool == "outliers_large":
        clamp_float("min_amount", default=100.0, lo=0.0, hi=1_000_000.0)
        date_field("start_date")
        date_field("end_date")

    elif tool == "recurring_merchants":
        clamp_int("months", default=6, lo=1, hi=24)
        clamp_int("min_count", default=3, lo=2, hi=20)

    elif tool == "merchant_breakdown":
        norm_str("merchant_substr", max_len=60)
        norm_str("by", max_len=30)
        if not args["merchant_substr"]:
            errors.append("merchant_substr required")
            tool = "none"
            args = {}
        else:
            if args.get("by") in ("", None):
                args["by"] = "category"
            date_field("start_date")
            date_field("end_date")

    elif tool == "category_trend":
        norm_str("category", max_len=60)
        clamp_int("months", default=6, lo=1, hi=24)
        if not args["category"]:
            errors.append("category required")
            tool = "none"
            args = {}

    ok = (tool != "none") and not errors
    cleaned = {"tool": tool, "args": args}
    return ok, cleaned, errors

