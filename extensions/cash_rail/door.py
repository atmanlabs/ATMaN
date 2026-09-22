"""One-tap cash-rail door. Standing Operator greenlight required; chores blocked."""
from __future__ import annotations
from typing import Any, Dict, Optional

_STANDING_GREENLIGHT = False
_NOTE = ""


def set_standing_greenlight(enabled: bool, note: str = "") -> Dict[str, Any]:
    global _STANDING_GREENLIGHT, _NOTE
    _STANDING_GREENLIGHT = bool(enabled)
    _NOTE = note
    return {"standing_greenlight": _STANDING_GREENLIGHT, "note": _NOTE}


def status() -> Dict[str, Any]:
    return {"standing_greenlight": _STANDING_GREENLIGHT, "note": _NOTE}


def open_rail(action: str, amount: Optional[float] = None) -> Dict[str, Any]:
    chore = any(x in (action or "").lower() for x in ("email", "login", "setup", "draft", "chore", "tap"))
    if chore:
        return {"allowed": False, "reason": "Chore taps blocked on cash rail"}
    if not _STANDING_GREENLIGHT:
        return {"allowed": False, "reason": "No standing Operator greenlight"}
    return {
        "allowed": True,
        "reason": "Standing greenlight active",
        "action": action,
        "amount": amount,
        "note": _NOTE,
    }
