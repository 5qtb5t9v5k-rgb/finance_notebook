"""Agent that orchestrates router -> executor -> narrator flow."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Dict, Optional

import pandas as pd

from src.ai_tools import TOOL_REGISTRY, ensure_dt
from src.ai_router import router_system_prompt, parse_router_output, validate_plan


NARRATOR_SYSTEM_PROMPT = """Olet rahoitustapahtumien analysointiapuri. Vastaat suomeksi.

SÄÄNNÖT:
- Saat "FACTS" JSONin. Käytä VAIN sitä. Älä keksi numeroita tai tapahtumia.
- Vastauksen pitää sisältää:
  1) selkeä vastaus kysymykseen
  2) lyhyt analyysi (miksi näin / mitä se tarkoittaa)
  3) 2–4 konkreettista säästö- tai optimointiehdotusta (sopii annetuille faktoille)
- Jos FACTSissa ei ole tarpeeksi tietoa: kerro mitä puuttuu, mutta älä arvaa.
"""


def run_router(user_input: str, api_key: str, get_llm_response, model: str) -> Dict[str, Any]:
    """Run router to select tool and parameters."""
    messages = [
        {"role": "system", "content": router_system_prompt()},
        {"role": "user", "content": user_input},
    ]
    text = get_llm_response(messages, api_key, model=model)
    plan = parse_router_output(text or "")
    _, cleaned, _errors = validate_plan(plan)
    return cleaned


def execute_plan(df: pd.DataFrame, plan: Dict[str, Any]) -> Dict[str, Any]:
    """Execute plan using Pandas tools deterministically."""
    tool = plan.get("tool", "none")
    args = plan.get("args", {}) or {}

    if tool == "none":
        return {"tool": "none", "result": None}

    fn = TOOL_REGISTRY.get(tool)
    if not fn:
        return {"tool": "none", "result": None}

    # execute tool deterministically
    result = fn(df, **args)
    return {"tool": tool, "args": args, "result": result}


def run_narrator(user_input: str, execution: Dict[str, Any], api_key: str, get_llm_response, model: str) -> str:
    """Run narrator to format answer based on facts."""
    facts = {
        "user_query": user_input,
        "tool": execution.get("tool"),
        "args": execution.get("args"),
        "result": execution.get("result"),
    }

    messages = [
        {"role": "system", "content": NARRATOR_SYSTEM_PROMPT},
        {"role": "user", "content": "FACTS:\n" + json.dumps(facts, ensure_ascii=False, indent=2)},
    ]
    return get_llm_response(messages, api_key, model=model)


def answer_with_tools(
    df: pd.DataFrame,
    user_input: str,
    api_key: str,
    get_llm_response,
    router_model: str = "gpt-4o-mini",
    narrator_model: str = "gpt-4o-mini",
) -> Dict[str, Any]:
    """
    Main entry point: router -> executor -> narrator.
    
    Returns dict:
      {
        "mode": "tools" or "fallback",
        "plan": {...},
        "execution": {...},
        "answer": "..."
      }
    """
    plan = run_router(user_input, api_key, get_llm_response, model=router_model)

    # validate again (safety)
    ok, plan2, errors = validate_plan(plan)
    if plan2.get("tool") == "none":
        return {"mode": "fallback", "plan": plan2, "errors": errors, "answer": ""}

    execution = execute_plan(df, plan2)
    answer = run_narrator(user_input, execution, api_key, get_llm_response, model=narrator_model)

    return {"mode": "tools", "plan": plan2, "execution": execution, "answer": answer}

