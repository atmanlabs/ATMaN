"""Always-on voice barge-in scaffold. Does not alter TSC; wraps Stage 9 voice."""
from __future__ import annotations
from typing import Any, Dict, Optional

_ENABLED = False


def configure(enabled: bool = True) -> Dict[str, Any]:
    global _ENABLED
    _ENABLED = bool(enabled)
    return {
        "barge_in": _ENABLED,
        "mode": "always_on" if _ENABLED else "push_to_talk",
        "note": "Requires local Whisper mic loop; core identity untouched",
    }


def should_interrupt(is_speaking: bool, user_voice_active: bool) -> bool:
    return bool(_ENABLED and is_speaking and user_voice_active)


def status() -> Dict[str, Any]:
    return {"barge_in": _ENABLED, "mode": "always_on" if _ENABLED else "push_to_talk"}
