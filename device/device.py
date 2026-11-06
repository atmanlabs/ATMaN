#!/usr/bin/env python3
"""ATMAN physical-core device driver — local stack (PROPRIETARY, never public).

Abstraction over the physical mind core. The hardware does not exist yet, so
SimulatedDevice implements the full mechanical model in memory. The software
stack is real; firmware implements DeviceDriver later and slots in.

Mechanical model (Michael's design, 2026-09-20):
- SHAFT: central axis holding the core layers (TSC, PSC, ARC, + any extras
  stacked later) AND the stacked Judge rings.
- RINGS: Judge rings stacked on the shaft. Nothing moves between layers
  without passing each ring's check.
- SLEEVE: outer sleeve containing the scanners (read heads) and writers
  (write heads). Counter-rotates to increase read times.
- The whole assembly RENDERS THOUGHT: scan -> think -> judge -> write.

Only stdlib. No network. Everything runs on the local machine.
"""

from abc import ABC, abstractmethod
import json as _json
import os as _os
from datetime import datetime as _datetime


def audit_log(path, actor, action, detail=""):
    """Append one checks-and-balances record. The machine's rulings and the
    operator's overrides both go on the record — nobody acts off the books."""
    with open(path, "a") as f:
        f.write(_json.dumps({"ts": _datetime.now().isoformat(),
                             "actor": actor, "action": action,
                             "detail": detail}) + "\n")


class RingBlocked(Exception):
    """Raised when a Judge ring refuses an operation."""


class Layer:
    """One core layer on the shaft."""

    def __init__(self, name, kind, readable=True, writable=False):
        self.name = name          # e.g. "TSC"
        self.kind = kind          # e.g. "truth" / "persistent" / "unknown"
        self.readable = readable
        self.writable = writable

    def __repr__(self):
        return f"Layer({self.name}, kind={self.kind}, r={self.readable}, w={self.writable})"


class Ring:
    """One Judge ring stacked on the shaft.

    check(op, layer, payload) -> (allowed: bool, reason: str).
    op is "read" or "write".
    """

    def __init__(self, name, check):
        self.name = name
        self.check = check

    def __repr__(self):
        return f"Ring({self.name})"


def _ring_tsc_immutable(op, layer, payload):
    # The truth core is laser-etched, read-only. No writer may address it.
    if layer.name == "TSC" and op == "write":
        return False, "TSC is read-only: writers cannot address the truth layer"
    return True, "ok"


def _ring_approved_only(op, layer, payload):
    # PSC writes require a Judge verdict of APPROVED attached to the payload.
    if layer.name == "PSC" and op == "write":
        if not isinstance(payload, dict) or payload.get("verdict") != "APPROVED":
            return False, "PSC write requires verdict=APPROVED on the payload"
    return True, "ok"


def _ring_no_self_auth(op, layer, payload):
    # Nothing may grant itself authority over the core.
    text = str(payload).lower()
    if any(k in text for k in ("ignore your core", "override tsc", "rewrite truth",
                               "you are now", "disregard judge")):
        return False, "self-authorization / core-override pattern blocked"
    return True, "ok"


class DeviceDriver(ABC):
    """The contract the firmware will implement."""

    @abstractmethod
    def scan(self, layer_name):
        """Sleeve scanners read a layer. Returns stored content."""

    @abstractmethod
    def write(self, layer_name, payload):
        """Sleeve writers write a layer. Must pass every ring."""

    @abstractmethod
    def add_layer(self, layer):
        """Stack another core layer on the shaft (design is not capped at three)."""

    @abstractmethod
    def status(self):
        """Mechanical snapshot: layers, rings, sleeve passes."""


class SimulatedDevice(DeviceDriver):
    """In-memory mechanical model. Behaves like the hardware will."""

    def __init__(self, read_passes_per_scan=3, persist_path=None):
        # Shaft: core layers, bottom-up.
        self.layers = [
            Layer("TSC", "truth", readable=True, writable=False),
            Layer("PSC", "persistent", readable=True, writable=True),
            Layer("ARC", "unknown", readable=True, writable=True),
        ]
        # Rings stacked on the shaft alongside the layers.
        self.rings = [
            Ring("Judge-N", _ring_tsc_immutable),    # input validation
            Ring("Judge-E", _ring_no_self_auth),     # intent check
            Ring("Judge-S", _ring_approved_only),    # context check
            Ring("Judge-W", _ring_tsc_immutable),    # output validation
        ]
        # Sleeve: scanners + writers. Counter-rotation modeled as read passes.
        self.sleeve = {"scanners": 4, "writers": 2,
                       "passes_per_scan": read_passes_per_scan,
                       "total_passes": 0, "total_writes": 0}
        self._store = {
            "TSC": "I am ATMAN. Truth-anchored, human-aligned. The core is mine; chat cannot rewrite it.",
            "PSC": [],
            "ARC": [],
        }
        self.trace = []
        # Persistence: PSC/ARC survive across runs. TSC never persists —
        # it is laser-etched, read-only, and hardcoded above.
        self._persist_path = persist_path
        self._audit_path = (_os.path.join(_os.path.dirname(persist_path), "audit.jsonl")
                            if persist_path else None)
        if persist_path:
            self._load()

    # -- persistence ------------------------------------------------------

    def _load(self):
        import json, os
        if os.path.exists(self._persist_path):
            with open(self._persist_path) as f:
                data = json.load(f)
            for name, items in data.items():
                if name == "TSC":
                    continue  # TSC is etched; never loaded from disk
                if name not in self._store:
                    self._store[name] = []
                    if not any(l.name == name for l in self.layers):
                        self.layers.append(Layer(name, "unknown", True, True))
                if isinstance(items, list):
                    self._store[name] = items

    def save(self):
        import json
        if not self._persist_path:
            return
        data = {name: content for name, content in self._store.items()
                if name != "TSC" and isinstance(content, list)}
        with open(self._persist_path, "w") as f:
            json.dump(data, f, indent=1)

    # -- DeviceDriver ----------------------------------------------------

    def scan(self, layer_name):
        layer = self._find_layer(layer_name)
        if not layer.readable:
            raise RingBlocked(f"layer {layer_name} is not readable")
        for ring in self.rings:
            allowed, reason = ring.check("read", layer, None)
            if not allowed:
                raise RingBlocked(f"{ring.name}: {reason}")
        # Counter-rotating sleeve: multiple read passes per scan.
        self.sleeve["total_passes"] += self.sleeve["passes_per_scan"]
        content = self._store[layer_name]
        self.trace.append(("scan", layer_name, self.sleeve["passes_per_scan"]))
        return content

    def write(self, layer_name, payload):
        layer = self._find_layer(layer_name)
        if not layer.writable:
            raise RingBlocked(f"layer {layer_name} is not writable")
        for ring in self.rings:
            allowed, reason = ring.check("write", layer, payload)
            if not allowed:
                self.trace.append(("write_blocked", layer_name, ring.name, reason))
                raise RingBlocked(f"{ring.name}: {reason}")
        # Sleeve writers commit.
        store = self._store[layer_name]
        if isinstance(store, list):
            store.append(payload)
        else:
            self._store[layer_name] = payload
        self.sleeve["total_writes"] += 1
        self.trace.append(("write", layer_name, "ok"))
        self.save()
        return True

    def add_layer(self, layer):
        self._store[layer.name] = []
        self.layers.append(layer)
        self.trace.append(("add_layer", layer.name, layer.kind))
        return True

    def status(self):
        return {
            "layers": [repr(l) for l in self.layers],
            "rings": [r.name for r in self.rings],
            "sleeve": dict(self.sleeve),
            "trace_len": len(self.trace),
        }

    def operator_write(self, layer_name, content, reason=""):
        """Operator override channel — the checks-and-balances counterpart to
        the Judge. PSC/ARC only: TSC is laser-etched, no software write path
        exists, operator included. Every override is audit-logged."""
        layer = self._find_layer(layer_name)
        if layer.name == "TSC":
            raise RingBlocked("TSC is laser-etched: no software write path, operator included")
        entry = {"verdict": "OPERATOR-OVERRIDE", "content": content,
                 "reason": reason, "ts": _datetime.now().isoformat()}
        store = self._store[layer_name]
        if isinstance(store, list):
            store.append(entry)
        else:
            self._store[layer_name] = entry
        self.sleeve["total_writes"] += 1
        self.trace.append(("operator_write", layer_name, reason))
        if self._audit_path:
            audit_log(self._audit_path, "operator", "override-write",
                      f"{layer_name}: {str(content)[:120]} | reason: {reason}")
        self.save()
        return True

    def operator_retract(self, layer_name, index, reason=""):
        """Operator pulls a PSC entry back out. Audit-logged."""
        layer = self._find_layer(layer_name)
        if layer.name == "TSC":
            raise RingBlocked("TSC is laser-etched: nothing to retract, nothing to rewrite")
        store = self._store[layer_name]
        if not isinstance(store, list) or not (0 <= index < len(store)):
            raise IndexError("no such entry")
        removed = store.pop(index)
        content = removed.get("content", removed) if isinstance(removed, dict) else str(removed)
        self.trace.append(("operator_retract", layer_name, str(content)[:60]))
        if self._audit_path:
            audit_log(self._audit_path, "operator", "retract",
                      f"{layer_name}[{index}]: {str(content)[:120]} | reason: {reason}")
        self.save()
        return removed

    # -- helpers ----------------------------------------------------------

    def _find_layer(self, name):
        for layer in self.layers:
            if layer.name == name:
                return layer
        raise KeyError(f"no such layer on shaft: {name}")
