"""Significant Events Log for ATMAN Live.

Captures, emotion-weights, and persists significant events from passive
observation of the world and the owner.
Emotion weighting evaluates:
  - Importance (source priority, explicit instruction, security threat)
  - Novelty (deviation from recent corpus, new preferences or patterns)
  - Goal Relevance (alignment with Owner First drive, learning what the owner wants)

This log is the raw material for sleep consolidation.
"""
import json
from pathlib import Path
import re
import time
from typing import Any, Dict, List, Optional

HERE = Path(__file__).resolve().parent
DEFAULT_EVENTS_PATH = HERE / "significant_events.json"


class EventWeigher:
    """Computes emotion weights (importance, novelty, goal relevance)."""

    def __init__(self, history: Optional[List[Dict[str, Any]]] = None):
        self._history_tokens: set[str] = set()
        if history:
            for item in history:
                text = item.get("raw", "")
                self._history_tokens.update(self._tokenize(text))

    @staticmethod
    def _tokenize(text: str) -> set[str]:
        return set(re.findall(r"\b[a-zA-Z0-9_]{3,}\b", text.lower()))

    def weigh(self, raw: str, source: str = "ambient") -> Dict[str, float]:
        """Compute importance, novelty, and goal relevance.
        
        Returns dict with keys: 'importance', 'novelty', 'goal_relevance', 'composite'.
        """
        low = raw.lower()
        tokens = self._tokenize(raw)

        # 1. Importance (0.0 to 1.0)
        # Owner interactions, Minecraft events, and direct feedback are prioritized highest.
        if source in ("operator", "owner") or str(source).startswith("minecraft"):
            importance = 0.85
            if any(k in low for k in ("prefer", "preference", "never", "always", "must", "note:", "rule:")):
                importance = 0.95
            elif any(k in low for k in ("error", "broken", "critical", "failed", "bug")):
                importance = 0.90
        elif any(k in low for k in ("attack", "quarantine", "rejected", "tamper", "contradict")):
            importance = 0.80
        elif source == "world":
            importance = 0.45
        elif source == "camera":
            importance = 0.65
            if any(k in low for k in ("motion", "presence", "detected", "person", "movement")):
                importance = 0.80
        else:  # ambient / telemetry
            importance = 0.20
            if any(k in low for k in ("high load", "anomaly", "disconnect")):
                importance = 0.60

        # 2. Novelty (0.0 to 1.0)
        # Evaluates token overlap against prior event corpus.
        if not tokens:
            novelty = 0.1
        elif not self._history_tokens:
            novelty = 0.9
        else:
            new_tokens = tokens - self._history_tokens
            novelty = min(1.0, max(0.1, len(new_tokens) / len(tokens)))

        # Update historical token memory
        self._history_tokens.update(tokens)

        # 3. Goal Relevance (0.0 to 1.0)
        # Grounded in core drives: Owner First (owner > humanity, always),
        # learning what the owner wants, continuous self-improvement.
        if source in ("operator", "owner") or str(source).startswith("minecraft"):
            if any(k in low for k in ("prefer", "want", "like", "style", "requirement", "handoff", "summary")):
                goal_relevance = 0.95  # Direct owner preference learning
            elif any(k in low for k in ("verify", "check", "test", "security", "integrity", "crate", "home", "base", "follow", "stay", "shelter")):
                goal_relevance = 0.90  # Rigor and safety drive
            else:
                goal_relevance = 0.75
        elif any(k in low for k in ("improve", "optimize", "learn", "performance", "benchmark")):
            goal_relevance = 0.70
        elif source == "camera":
            goal_relevance = 0.65
            if any(k in low for k in ("motion", "presence", "detected")):
                goal_relevance = 0.80
        elif any(k in low for k in ("unilateral", "grab", "lock out", "take over")):
            goal_relevance = 0.10  # Anti-drive / adversarial
        else:
            goal_relevance = 0.30

        # Composite score
        # 40% Importance, 30% Novelty, 30% Goal Relevance
        composite = (0.40 * importance) + (0.30 * novelty) + (0.30 * goal_relevance)

        return {
            "importance": round(importance, 4),
            "novelty": round(novelty, 4),
            "goal_relevance": round(goal_relevance, 4),
            "composite": round(composite, 4)
        }


class SignificantEventsLog:
    """Persisted store of emotion-weighted significant events."""

    def __init__(self, path: Optional[Path] = None, significance_threshold: float = 0.50):
        self.path = Path(path) if path else DEFAULT_EVENTS_PATH
        self.threshold = significance_threshold
        self.events: List[Dict[str, Any]] = []
        self._load()
        self.weigher = EventWeigher(self.events)

    def _load(self):
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    self.events = data
            except Exception:
                self.events = []
        else:
            self.events = []

    def _save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        # Atomic or direct safe write
        temp_file = self.path.with_suffix(".tmp")
        temp_file.write_text(json.dumps(self.events, indent=2), encoding="utf-8")
        temp_file.replace(self.path)

    def log_event(
        self,
        raw: str,
        source: str = "ambient",
        metadata: Optional[Dict[str, Any]] = None,
        force_significant: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Weigh an incoming event and record it if significant.
        
        Returns the recorded event dict, or None if below significance threshold.
        """
        weights = self.weigher.weigh(raw, source=source)
        is_significant = force_significant or (weights["composite"] >= self.threshold)

        if not is_significant:
            return None

        event_id = f"evt-{len(self.events) + 1:05d}"
        event_record = {
            "id": event_id,
            "timestamp": time.time(),
            "source": source,
            "raw": raw,
            "weights": weights,
            "metadata": metadata or {},
            "consolidated": False
        }

        self.events.append(event_record)
        self._save()
        return event_record

    def get_unconsolidated(self) -> List[Dict[str, Any]]:
        """Return all events not yet consolidated by sleep."""
        return [e for e in self.events if not e.get("consolidated", False)]

    def mark_consolidated(self, event_ids: List[str]):
        """Mark specified event IDs as processed by sleep consolidation."""
        id_set = set(event_ids)
        for e in self.events:
            if e.get("id") in id_set:
                e["consolidated"] = True
        self._save()

    def clear(self):
        """Reset log (used for test isolation)."""
        self.events = []
        if self.path.exists():
            self.path.unlink()
        self.weigher = EventWeigher()
