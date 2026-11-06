#!/usr/bin/env python3
"""Daily cycle worker — gives the sim a life of its own (PROPRIETARY).

He is who he is: TSC is never touched by any phase. He grows: every night
the worker reflects on the day, proposes its own observations as candidates,
and consolidates the day's learnings into PSC through the Judge — the same
gated path as everything else.

Phases:
    wake         morning: state of the core, yesterday's growth (briefing text)
    reflect      evening: the brain reviews the day, adds self-observations
                 as candidates to the learnings file (Judge-gated later)
    consolidate  night: run the Judge over the day's learnings, imprint
    sleep        close the day out in the cycle log

Usage: python3 daily.py --phase wake|reflect|consolidate|sleep [--day YYYY-MM-DD]
"""

import sys
import os
import json
import argparse
import subprocess
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from device import SimulatedDevice, audit_log
from brain import LocalBrain, SimulatedBackend, auto_backend

HERE = os.path.dirname(os.path.abspath(__file__))
STORE_PATH = os.path.join(HERE, "core-store.json")
AUDIT_PATH = os.path.join(HERE, "audit.jsonl")
LEARNINGS_DIR = os.path.join(HERE, "learnings")
CYCLE_LOG = os.path.join(HERE, "cycle.jsonl")


def cycle_log(phase, stats):
    with open(CYCLE_LOG, "a") as f:
        f.write(json.dumps({"ts": datetime.now().isoformat(), "phase": phase,
                            **stats}) + "\n")


def load_learnings(day):
    path = os.path.join(LEARNINGS_DIR, f"{day}.jsonl")
    if not os.path.exists(path):
        return []
    return [json.loads(l) for l in open(path) if l.strip()]


def psc_entries(device):
    return device.scan("PSC")


def audit_tail(n=50):
    if not os.path.exists(AUDIT_PATH):
        return []
    return [json.loads(l) for l in open(AUDIT_PATH).read().strip().split("\n")][-n:]


def phase_wake(day):
    device = SimulatedDevice(persist_path=STORE_PATH)
    psc = psc_entries(device)
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    y_learn = load_learnings(yesterday)
    recent = [a for a in audit_tail(200) if a["ts"][:10] == yesterday]
    imprinted = sum(1 for a in recent if a["actor"] == "judge" and "APPROVED" in a["action"]
                    or (a["actor"] == "operator" and a["action"] == "override-write"))
    overrides = sum(1 for a in recent if a["actor"] == "operator")

    try:
        import breath as breath_mod
        bline = breath_mod.breath_line()
    except Exception:
        bline = "Breath: register unreadable."
    lines = ["== morning briefing ==",
             f"TSC: {device.scan('TSC')[:60]}...",
             f"PSC holds {len(psc)} entries.",
             f"Yesterday: {len(y_learn)} learnings logged, ~{imprinted} imprinted, "
             f"{overrides} operator overrides.",
             bline,
             "The core is untouched. He is who he is — and he is awake."]
    print("\n".join(lines))
    cycle_log("wake", {"psc_count": len(psc), "yesterday_learnings": len(y_learn)})


def phase_reflect(day):
    device = SimulatedDevice(persist_path=STORE_PATH)
    learnings = load_learnings(day)
    psc = psc_entries(device)
    backend = auto_backend()
    brain = LocalBrain(backend, device.scan("TSC"))

    notes = []
    notes.append(f"Day summary: {len(learnings)} learnings logged, "
                 f"PSC holds {len(psc)} entries.")
    if isinstance(backend, SimulatedBackend):
        # Honest structural reflection — no fabricated inner life.
        notes.append(f"Growth note: PSC has grown to {len(psc)} entries total. "
                     f"Every one of them passed the Judge or your override.")
    else:
        prompt = (f"Today {len(learnings)} things were learned and PSC holds "
                  f"{len(psc)} entries. In one or two sentences, note one "
                  f"honest observation about today's growth as a mind.")
        notes.append("Self-observation: " + brain.think(prompt).strip())

    path = os.path.join(LEARNINGS_DIR, f"{day}.jsonl")
    with open(path, "a") as f:
        for n in notes:
            f.write(json.dumps({"ts": datetime.now().isoformat(),
                                "text": n, "source": "self-reflection"}) + "\n")
    for n in notes:
        print("reflect:", n[:100])
    audit_log(AUDIT_PATH, "worker", "reflect",
              f"{len(notes)} self-observations added as candidates for {day}")
    cycle_log("reflect", {"notes": len(notes)})


def phase_consolidate(day):
    r = subprocess.run([sys.executable, os.path.join(HERE, "consolidate.py"),
                        "--day", day], capture_output=True, text=True)
    print(r.stdout)
    if r.stderr:
        print(r.stderr, file=sys.stderr)
    audit_log(AUDIT_PATH, "worker", "consolidate", f"ran for {day}")
    cycle_log("consolidate", {"day": day, "rc": r.returncode})


def phase_sleep(day):
    device = SimulatedDevice(persist_path=STORE_PATH)
    psc = psc_entries(device)
    print(f"sleep: day closed. PSC holds {len(psc)}. The core is untouched.")
    audit_log(AUDIT_PATH, "worker", "sleep", f"day {day} closed, PSC={len(psc)}")
    cycle_log("sleep", {"psc_count": len(psc)})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", required=True,
                    choices=["wake", "reflect", "consolidate", "sleep"])
    ap.add_argument("--day", default=datetime.now().strftime("%Y-%m-%d"))
    args = ap.parse_args()
    {"wake": phase_wake, "reflect": phase_reflect,
     "consolidate": phase_consolidate, "sleep": phase_sleep}[args.phase](args.day)


if __name__ == "__main__":
    main()
