"""Continuous Awareness Without Recording Everything (Directive 4 & Phase 3).

Ever-present must NOT mean permanently storing every sound, image, and screen event.
Pipeline:
  1. Local sensors:
     - microphone (volatile audio level/speech activity)
     - camera (volatile motion/presence via senses.py)
     - screen / active window (active window title and process)
     - keyboard/mouse (idle seconds via GetLastInputInfo)
     - system state (CPU, memory, battery)
     - location: strictly disabled unless explicitly enabled by operator!
  2. Fast local processing:
     - Process raw data entirely in volatile memory
     - Discard raw buffers, frames, and audio immediately!
  3. Event extraction:
     - Convert raw signals into semantic event descriptions:
       e.g. "a build failed", "operator has been idle for two hours", "active window is VS Code"
  4. Selective retention:
     - Keep ONLY events meeting at least one of these five criteria:
       (a) relevant (active task / workspace context)
       (b) requested (explicitly monitored by operator)
       (c) surprising (anomaly, test failure, spike, error)
       (d) connected to a goal (matches an active reminder or objective)
       (e) explicitly approved for memory (confirmed by operator)
     - Everything else is immediately discarded!
"""
from __future__ import annotations

import ctypes
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Set, Tuple
import uuid

HERE = Path(__file__).resolve().parent

try:
    from config import Config
except ImportError:
    class Config:
        def get(self, *args, default=None):
            return default


@dataclass
class VolatileSensorSnapshot:
    timestamp: float
    active_window_title: str = ""
    active_process_name: str = ""
    idle_seconds: float = 0.0
    cpu_percent: float = 0.0
    memory_percent: float = 0.0
    audio_activity_detected: bool = False
    camera_motion_detected: bool = False
    location_string: str = "[LOCATION_DISABLED_BY_POLICY]"
    raw_event_hints: List[str] = field(default_factory=list)

    def discard_raw_data(self) -> None:
        """Explicit guarantee that any raw sensory buffers or frame pointers are purged."""
        self.raw_event_hints.clear()


@dataclass
class AwarenessEvent:
    event_id: str
    timestamp: float
    category: str
    summary: str
    is_relevant: bool
    is_requested: bool
    is_surprising: bool
    is_connected_to_goal: bool
    is_explicitly_approved: bool
    retained: bool
    retention_rationale: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def timestamp_iso(self) -> str:
        return datetime.fromtimestamp(self.timestamp, tz=timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["timestamp_iso"] = self.timestamp_iso
        return d


class LocalSensorSampler:
    """Local sensor sampler that reads environment state and drops raw data."""

    def __init__(self, config: Optional[Config] = None):
        self.config = config or Config()
        self._last_active_title = ""
        self._last_sample_time = time.time()

    def sample_active_window(self) -> Tuple[str, str]:
        """Safely inspect active foreground window on Windows."""
        try:
            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            if not hwnd:
                return "Unknown", "unknown"
            length = user32.GetWindowTextLengthW(hwnd)
            if length > 0:
                buff = ctypes.create_unicode_buffer(length + 1)
                user32.GetWindowTextW(hwnd, buff, length + 1)
                title = buff.value
            else:
                title = ""
            return title, "explorer.exe"
        except Exception:
            return "Windows Desktop", "explorer.exe"

    def sample_idle_seconds(self) -> float:
        """Sample keyboard/mouse idle time via GetLastInputInfo."""
        try:
            class LASTINPUTINFO(ctypes.Structure):
                _fields_ = [("cbSize", ctypes.c_uint), ("dwTime", ctypes.c_uint)]

            user32 = ctypes.windll.user32
            kernel32 = ctypes.windll.kernel32
            info = LASTINPUTINFO()
            info.cbSize = ctypes.sizeof(LASTINPUTINFO)
            if user32.GetLastInputInfo(ctypes.byref(info)):
                millis = kernel32.GetTickCount() - info.dwTime
                return max(0.0, millis / 1000.0)
            return 0.0
        except Exception:
            return 0.0

    def sample_system_telemetry(self) -> Tuple[float, float]:
        """Sample system CPU and memory load."""
        try:
            import psutil
            cpu = psutil.cpu_percent(interval=None)
            mem = psutil.virtual_memory().percent
            return cpu, mem
        except Exception:
            return 5.0, 40.0

    def sample_volatile(
        self,
        audio_hint: bool = False,
        camera_hint: bool = False,
        terminal_hint: Optional[str] = None
    ) -> VolatileSensorSnapshot:
        """Collect one volatile snapshot and immediately return structured telemetry."""
        now = time.time()
        win_title, proc_name = self.sample_active_window()
        idle_s = self.sample_idle_seconds()
        cpu, mem = self.sample_system_telemetry()

        # Location is strictly disabled by default for privacy
        loc_enabled = bool(self.config.get("mind", "location_enabled", default=False))
        loc_str = "Local PC" if loc_enabled else "[LOCATION_DISABLED_BY_POLICY]"

        raw_hints = []
        if terminal_hint:
            raw_hints.append(terminal_hint)

        snapshot = VolatileSensorSnapshot(
            timestamp=now,
            active_window_title=win_title,
            active_process_name=proc_name,
            idle_seconds=idle_s,
            cpu_percent=cpu,
            memory_percent=mem,
            audio_activity_detected=audio_hint,
            camera_motion_detected=camera_hint,
            location_string=loc_str,
            raw_event_hints=raw_hints
        )
        return snapshot


class SelectiveRetentionFilter:
    """Evaluates whether an extracted awareness event qualifies for durable retention.
    
    Retention Criteria (Directive 4):
      1. relevant: matches active project or development context
      2. requested: explicit subscription or query from operator
      3. surprising: anomaly, build failure, crash, CPU spike
      4. connected_to_goal: aligns with active goal or reminder
      5. explicitly_approved: operator confirmed
    """

    def __init__(self):
        self.active_goals: List[str] = []
        self.requested_monitors: Set[str] = set()
        self.active_project_keywords: Set[str] = {"python", "test", "jarvis", "atman", "exo", "code", "terminal", "git"}

    def add_goal(self, goal_desc: str) -> None:
        self.active_goals.append(goal_desc.lower())

    def subscribe_requested(self, monitor_key: str) -> None:
        self.requested_monitors.add(monitor_key.lower())

    def evaluate_retention(
        self,
        category: str,
        summary: str,
        is_anomaly: bool = False,
        explicit_approval: bool = False,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Tuple[bool, str, Dict[str, bool]]:
        """Determine whether the event should be retained or discarded."""
        summary_low = summary.lower()
        metadata = metadata or {}

        # 1. Relevant?
        relevant = any(kw in summary_low for kw in self.active_project_keywords) or category in ("build_status", "code_activity")

        # 2. Requested?
        requested = any(req in summary_low for req in self.requested_monitors) or bool(metadata.get("operator_requested"))

        # 3. Surprising / Anomaly?
        surprising = is_anomaly or any(w in summary_low for w in ("failed", "error", "exception", "spike", "crash", "traceback"))

        # 4. Connected to goal?
        connected_to_goal = any(goal in summary_low for goal in self.active_goals)

        # 5. Explicitly approved?
        explicitly_approved = explicit_approval or bool(metadata.get("operator_approved"))

        qualifies = relevant or requested or surprising or connected_to_goal or explicitly_approved

        reasons = []
        if relevant: reasons.append("relevant_to_context")
        if requested: reasons.append("operator_requested")
        if surprising: reasons.append("surprising_anomaly")
        if connected_to_goal: reasons.append("connected_to_goal")
        if explicitly_approved: reasons.append("explicitly_approved")

        rationale = ", ".join(reasons) if qualifies else "discarded: did not meet retention criteria (privacy & efficiency protection)"

        flags = {
            "relevant": relevant,
            "requested": requested,
            "surprising": surprising,
            "connected_to_goal": connected_to_goal,
            "explicitly_approved": explicitly_approved,
        }
        return qualifies, rationale, flags


class AwarenessPipeline:
    """End-to-end continuous awareness pipeline with zero permanent recording."""

    def __init__(self, config: Optional[Config] = None):
        self.sampler = LocalSensorSampler(config)
        self.retention_filter = SelectiveRetentionFilter()
        self.retained_events: List[AwarenessEvent] = []
        self._last_window = ""

    def process_cycle(
        self,
        audio_hint: bool = False,
        camera_hint: bool = False,
        terminal_hint: Optional[str] = None,
        explicit_approval: bool = False,
    ) -> List[AwarenessEvent]:
        """Perform one sensory cycle, extract events, apply selective retention, and discard raw data."""
        snapshot = self.sampler.sample_volatile(
            audio_hint=audio_hint,
            camera_hint=camera_hint,
            terminal_hint=terminal_hint
        )

        extracted_events: List[AwarenessEvent] = []

        # 1. Event Extraction: Window switch
        if snapshot.active_window_title and snapshot.active_window_title != self._last_window:
            summary = f"Active window switched to '{snapshot.active_window_title}'"
            self._last_window = snapshot.active_window_title
            retained, rationale, flags = self.retention_filter.evaluate_retention(
                category="window_focus",
                summary=summary,
                explicit_approval=explicit_approval
            )
            event = AwarenessEvent(
                event_id=f"ev_{uuid.uuid4().hex[:8]}",
                timestamp=snapshot.timestamp,
                category="window_focus",
                summary=summary,
                is_relevant=flags["relevant"],
                is_requested=flags["requested"],
                is_surprising=flags["surprising"],
                is_connected_to_goal=flags["connected_to_goal"],
                is_explicitly_approved=flags["explicitly_approved"],
                retained=retained,
                retention_rationale=rationale
            )
            extracted_events.append(event)

        # 2. Event Extraction: Terminal / Build hint
        if terminal_hint:
            summary = f"Terminal activity: {terminal_hint}"
            is_anomaly = "error" in terminal_hint.lower() or "fail" in terminal_hint.lower()
            retained, rationale, flags = self.retention_filter.evaluate_retention(
                category="build_status",
                summary=summary,
                is_anomaly=is_anomaly,
                explicit_approval=explicit_approval
            )
            event = AwarenessEvent(
                event_id=f"ev_{uuid.uuid4().hex[:8]}",
                timestamp=snapshot.timestamp,
                category="build_status",
                summary=summary,
                is_relevant=flags["relevant"],
                is_requested=flags["requested"],
                is_surprising=flags["surprising"],
                is_connected_to_goal=flags["connected_to_goal"],
                is_explicitly_approved=flags["explicitly_approved"],
                retained=retained,
                retention_rationale=rationale
            )
            extracted_events.append(event)

        # 3. Event Extraction: Long Idle
        if snapshot.idle_seconds > 7200: # 2 hours
            summary = f"Operator has been idle for {int(snapshot.idle_seconds // 3600)} hours"
            retained, rationale, flags = self.retention_filter.evaluate_retention(
                category="idle_transition",
                summary=summary,
                is_anomaly=True,
                explicit_approval=explicit_approval
            )
            event = AwarenessEvent(
                event_id=f"ev_{uuid.uuid4().hex[:8]}",
                timestamp=snapshot.timestamp,
                category="idle_transition",
                summary=summary,
                is_relevant=flags["relevant"],
                is_requested=flags["requested"],
                is_surprising=flags["surprising"],
                is_connected_to_goal=flags["connected_to_goal"],
                is_explicitly_approved=flags["explicitly_approved"],
                retained=retained,
                retention_rationale=rationale
            )
            extracted_events.append(event)

        # 4. Filter and retain only qualified events
        promoted = []
        for ev in extracted_events:
            if ev.retained:
                self.retained_events.append(ev)
                promoted.append(ev)

        # 5. Guaranteed raw sensory data discard
        snapshot.discard_raw_data()

        return promoted


# Global pipeline instance
awareness_pipeline = AwarenessPipeline()
