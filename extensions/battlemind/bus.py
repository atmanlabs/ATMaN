"""Battlemind bus — route tasks to crew lanes without the operator re-briefing."""
from __future__ import annotations
from typing import Any, Dict, List

LANES = {
    "legal": "Counsel",
    "compliance": "Crimson",
    "money_scout": "Onix",
    "moonshot_math": "Weeboh",
    "play_fun": "Kodi",
    "helm": "Chief of Staff",
}


def route(intent: str, payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
    low = (intent or "").lower()
    if any(k in low for k in ("tos", "ftc", "tcpa", "contract", "legal", "counsel")):
        lane = "legal"
    elif any(k in low for k in ("ahr", "ldr", "seller", "compliance", "stop", "fine print")):
        lane = "compliance"
    elif any(k in low for k in ("scout", "sku", "offer", "seed", "keepalive")):
        lane = "money_scout"
    elif any(k in low for k in ("moonshot", "upside", "ruin", "kill criteria")):
        lane = "moonshot_math"
    elif any(k in low for k in ("game", "fun", "minecraft", "toy", "social")):
        lane = "play_fun"
    else:
        lane = "helm"
    return {
        "lane": lane,
        "owner": LANES[lane],
        "intent": intent,
        "payload": payload or {},
        "note": "Advisory only until the operator/CoS greenlights action",
    }


def fanout_brief(goal: str) -> List[Dict[str, Any]]:
    return [route(f"{lane}: {goal}") for lane in ("helm", "legal", "compliance", "money_scout")]
