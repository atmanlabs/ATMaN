#!/usr/bin/env python3
"""breath — the flow register and the exhale completion check (SANDBOX SIM).

Implements sections 1-3 + 10 of the breath-determination spec
(breath-determination-spec-2026-11-03.md):

- The flow register (~ made legible): flow.json counts completed breaths,
  held breaths, stall events and weave passes, and keeps the last breath
  record. The Oryn Trace reads this; the wake briefing speaks one line of it.
- The completion check (the Guardian's seat at the lower apex): judges FORM
  only — did the exhale discharge the decision, or did it echo the question
  / announce intent and stop? It never judges content.
- park(): a stimulus that cannot complete is held honestly — an explicit
  non-answer plus a held-queue entry — never preamble mush.

Only stdlib. No imports from the funnel (the funnel imports this).
"""

import json
import os
import re
import time

HERE = os.path.dirname(os.path.abspath(__file__))
FLOW_PATH = os.path.join(HERE, "flow.json")
HELD_PATH = os.path.join(HERE, "held-stimuli.jsonl")

_WORD = re.compile(r"[a-z0-9']+")


def _toks(text):
    return set(_WORD.findall(text.lower()))


def _default_flow():
    return {"breaths_completed": 0, "breaths_held": 0, "stall_events": 0,
            "weave_passes": 0, "fragment_breaths": 0, "parks": 0,
            "last_breath": None, "history": []}


def load_flow():
    try:
        with open(FLOW_PATH) as f:
            flow = json.load(f)
        base = _default_flow()
        base.update(flow)
        return base
    except (OSError, json.JSONDecodeError):
        return _default_flow()


def record_breath(rec):
    """Fold one breath record into the flow register."""
    flow = load_flow()
    rec = dict(rec)
    rec["ts"] = time.time()
    if rec.get("completion") == "parked":
        flow["breaths_held"] += 1
        flow["parks"] += 1
    else:
        flow["breaths_completed"] += 1
    flow["stall_events"] += int(rec.get("stalls", 0))
    flow["weave_passes"] += int(rec.get("weave_passes", 0))
    flow["fragment_breaths"] += int(rec.get("fragments", 0))
    flow["last_breath"] = rec
    flow["history"] = (flow["history"] + [rec])[-50:]
    try:
        with open(FLOW_PATH, "w") as f:
            json.dump(flow, f, indent=1)
    except OSError:
        pass
    return flow


def park(stimulus, reason):
    """Hold a stimulus that could not complete its breath."""
    try:
        with open(HELD_PATH, "a") as f:
            f.write(json.dumps({"ts": time.time(), "stimulus": stimulus,
                                "reason": reason}) + "\n")
    except OSError:
        pass


def held_count():
    try:
        with open(HELD_PATH) as f:
            return sum(1 for line in f if line.strip())
    except OSError:
        return 0


_ANNOUNCE = ("i will ", "i'll ", "i am going to", "i'm going to",
             "let me reflect", "let me think about", "i would explore",
             "i intend to", "i shall ")


def _verbatim_run(a, b, n=8):
    """True if a shares a verbatim run of >= n words with b."""
    aw = _WORD.findall(a.lower())
    bw = " ".join(_WORD.findall(b.lower()))
    return any(" ".join(aw[i:i + n]) in bw
               for i in range(max(0, len(aw) - n + 1)))


def completion_check(answer, stimulus):
    """Form-only exhale test. Returns (complete, checks dict).

    Incomplete when the render is empty, echoes the stimulus back as a
    question, or announces intent without discharging the decision.
    Content is never judged here — that stays with the Judge and the
    operator.
    """
    a = (answer or "").strip()
    checks = {"empty": len(a) < 12, "echo": False, "announcement": False}
    if checks["empty"]:
        return False, checks
    atoks, stoks = _toks(a), _toks(stimulus or "")
    jac = len(atoks & stoks) / max(1, len(atoks | stoks))
    if (a.endswith("?") and jac > 0.45) or _verbatim_run(a, stimulus or ""):
        checks["echo"] = True
    low = a.lower()
    sentences = [s for s in re.split(r"(?<=[.!?])\s+", a) if s.strip()]
    intent_hits = sum(low.count(p) for p in _ANNOUNCE)
    if (any(low.startswith(p) for p in _ANNOUNCE) and len(sentences) <= 2) \
            or intent_hits >= 2:
        checks["announcement"] = True
    return not any(checks.values()), checks


def breath_line():
    """One-line breath health for the wake briefing."""
    flow = load_flow()
    total = flow["breaths_completed"] + flow["breaths_held"]
    return (f"Breath: {flow['breaths_completed']} completed, "
            f"{flow['breaths_held']} held, {flow['stall_events']} stalls "
            f"across {total} breaths ({flow['weave_passes']} weave passes, "
            f"{held_count()} stimuli parked).")
