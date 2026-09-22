"""Working-context snapshot for ATMAN reason stage.

Architecture (Operator soup-up Phase 2):
- TSC system prefix: injected once, cached forever (soul is immutable).
- PSC text: rebuilt only after a Judge-gated imprint (dirty flag).
- WFC: capped rolling window, slim serialization.
- Reason reads a snapshot — it does not rebuild the world.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Deque, Dict, List, Optional


@dataclass
class ContextSnapshot:
    tsc_system: str
    psc_text: str
    wfc_text: str
    wfc_depth: int
    wfc_entries: List[Dict[str, Any]]
    system_chars: int
    user_context_chars: int


class WorkingContext:
    def __init__(self, wfc_prompt_window: int = 5, wfc_raw_chars: int = 120, wfc_reply_chars: int = 120):
        self.wfc_prompt_window = max(1, int(wfc_prompt_window))
        self.wfc_raw_chars = max(40, int(wfc_raw_chars))
        self.wfc_reply_chars = max(40, int(wfc_reply_chars))
        self._tsc_system: Optional[str] = None
        self._psc_text: str = "  (No persistent memories yet)"
        self._psc_dirty: bool = True
        self._psc_count: int = -1

    def ensure_tsc(self, tsc: Any, builder) -> str:
        """Inject TSC once. builder(tsc) -> static system prefix string."""
        if self._tsc_system is None:
            self._tsc_system = builder(tsc)
        return self._tsc_system

    def mark_psc_dirty(self) -> None:
        self._psc_dirty = True

    def ensure_psc(self, psc: Any) -> str:
        """Refresh PSC slice only when dirty (after imprint) or first use."""
        count = len(getattr(psc, "memories", []) or []) if psc else 0
        if self._psc_dirty or count != self._psc_count:
            memories = list(getattr(psc, "memories", []) or [])[-5:] if psc else []
            if memories:
                self._psc_text = "\n".join(f"  - {m.get('memory', '')[:200]}" for m in memories)
            else:
                self._psc_text = "  (No persistent memories yet)"
            self._psc_count = count
            self._psc_dirty = False
        return self._psc_text

    def _slim_wfc_entries(self, wfc: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        window = list(wfc[-self.wfc_prompt_window :]) if wfc else []
        slim: List[Dict[str, Any]] = []
        for entry in window:
            ar = entry.get("action_result") or {}
            intent = str(entry.get("intent") or "")
            raw = str(entry.get("raw") or "")
            content = ""
            if isinstance(ar, dict):
                content = str(ar.get("content") or "")[: self.wfc_reply_chars]
                tool = str(ar.get("tool") or "")
                # Never let evolve/search SERP poison normal conversation context
                if tool in ("web_search", "fetch_web") or intent in (
                    "github_self_upgrade_scout",
                    "inferred_world_knowledge",
                    "cockpit_web_search",
                ):
                    raw = "[self-evolve/search tick]"
                    content = (content[:80] if content else "searched") 
                    if re.search(r"windows\s*1[12]|windows\s*update", content, re.I):
                        content = "upgrade scout ran"
            # Camera dumps are huge and derail chat — keep tiny
            if str(entry.get("source") or "") == "camera" or raw.lower().startswith("visual observation"):
                raw = "[camera note]"
                content = content[:60]
            slim.append(
                {
                    "raw": raw[: self.wfc_raw_chars],
                    "reply": content,
                    "outcome": entry.get("outcome"),
                }
            )
        return slim

    def format_wfc_text(self, slim_entries: List[Dict[str, Any]]) -> str:
        if not slim_entries:
            return "  (No prior history)"
        lines = []
        for e in slim_entries:
            lines.append(
                f"  - Event: {e.get('raw')} | Reply: {e.get('reply')} | Outcome: {e.get('outcome')}"
            )
        return "\n".join(lines)

    def assemble(
        self,
        tsc: Any,
        psc: Any,
        wfc: Any,
        tsc_builder,
    ) -> ContextSnapshot:
        """Assemble once per cycle. Reason must only read the returned snapshot."""
        tsc_system = self.ensure_tsc(tsc, tsc_builder)
        psc_text = self.ensure_psc(psc)
        wfc_list = list(wfc) if wfc is not None else []
        slim = self._slim_wfc_entries(wfc_list)
        wfc_text = self.format_wfc_text(slim)
        return ContextSnapshot(
            tsc_system=tsc_system,
            psc_text=psc_text,
            wfc_text=wfc_text,
            wfc_depth=len(wfc_list),
            wfc_entries=slim,
            system_chars=len(tsc_system),
            user_context_chars=len(psc_text) + len(wfc_text),
        )
