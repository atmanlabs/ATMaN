"""Pre-flight STOP gate + Counsel Soft GO card. Peripheral — does not edit TSC."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional
import time

SPEND_SEND_PUBLISH = ("spend", "send", "publish", "transfer", "buy", "checkout", "post_public")


@dataclass
class CounselCard:
    verdict: str  # Soft GO | STOP | HOLD
    citation: str
    flags: List[str]
    t: float

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def requires_counsel(action: Dict[str, Any]) -> bool:
    kind = str(action.get("type") or action.get("action") or "").lower()
    tool = str(action.get("tool") or "").lower()
    blob = f"{kind} {tool} {action}"
    return any(k in blob for k in SPEND_SEND_PUBLISH)


def preflight(action: Dict[str, Any], counsel: Optional[CounselCard] = None) -> Dict[str, Any]:
    """Return {allowed, reason, counsel}. Blocks spend/send/publish without Soft GO."""
    if not requires_counsel(action):
        return {"allowed": True, "reason": "non-rail action", "counsel": None}
    if counsel is None:
        return {
            "allowed": False,
            "reason": "Counsel Soft GO required before spend/send/publish",
            "counsel": None,
        }
    if counsel.verdict.upper() != "SOFT GO":
        return {
            "allowed": False,
            "reason": f"Counsel {counsel.verdict}: {counsel.citation}",
            "counsel": counsel.to_dict(),
        }
    return {"allowed": True, "reason": "Counsel Soft GO on file", "counsel": counsel.to_dict()}


def privilege_wall(note: str, audience: str = "public") -> Dict[str, Any]:
    """Legal notes stay CoS-routed; never auto-post to buyers/social."""
    if audience.lower() in ("public", "buyer", "social", "tiktok", "shopify"):
        return {"allowed": False, "reason": "Privilege wall: legal notes are CoS-only"}
    return {"allowed": True, "reason": "internal CoS route", "note": note, "t": time.time()}
