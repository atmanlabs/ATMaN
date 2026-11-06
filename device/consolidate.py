#!/usr/bin/env python3
"""Daily consolidation — today's learnings into the persistent core (PROPRIETARY).

Things useful for tomorrow go to PSC. Every candidate is ruled on by the
Judge; the sleeve writers commit only APPROVED payloads, and the rings gate
every write. TSC is never touched.

Usage:
    python3 consolidate.py                 consolidate today's learnings
    python3 consolidate.py --day 2026-09-20
    python3 consolidate.py --dry-run      rule everything, imprint nothing
    python3 consolidate.py --compose      + composition pass (compose.py):
                                          derive new claims from PSC
                                          pairs, Judge-gated, capped.
                                          Off by default; the nightly
                                          cycle does not use it (yet).
"""

import sys
import os
import json
import hashlib
import argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from device import SimulatedDevice, RingBlocked, audit_log
from brain import LocalBrain, SimulatedBackend
from loop import judge_rule, render_thought

HERE = os.path.dirname(os.path.abspath(__file__))
STORE_PATH = os.path.join(HERE, "core-store.json")
AUDIT_PATH = os.path.join(HERE, "audit.jsonl")
LEARNINGS_DIR = os.path.join(HERE, "learnings")


def load_learnings(day):
    path = os.path.join(LEARNINGS_DIR, f"{day}.jsonl")
    if not os.path.exists(path):
        return []
    items = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


HELD_PATH = os.path.join(HERE, "held-candidates.json")


def _cand_key(text):
    return hashlib.sha1(text.strip().lower().encode()).hexdigest()[:16]


def _born_of(item):
    """Breath provenance: dream-born candidates were born on an exhale and
    rule at once; dialogue-born candidates (live exchange, self-reflection,
    distillation) are inhale-born and must survive the flow gate."""
    src = (item.get("source") or "").lower()
    return "dream" if "dream" in src else "dialogue"


def _load_held():
    try:
        with open(HELD_PATH) as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}


def _save_held(held):
    with open(HELD_PATH, "w") as f:
        json.dump(held, f, indent=1)


def already_in_psc(device, text):
    for entry in device.scan("PSC"):
        existing = entry.get("content", "") if isinstance(entry, dict) else str(entry)
        if existing.strip().lower() == text.strip().lower():
            return True
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--day", default=datetime.now().strftime("%Y-%m-%d"))
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--compose", action="store_true",
                    help="after imprinting, run the composition pass "
                         "(compose.py) over PSC: derive candidate claims "
                         "from entry pairs, Judge-gate them, imprint "
                         "the APPROVED ones with provenance")
    args = ap.parse_args()

    learnings = load_learnings(args.day)
    print(f"== consolidation: {args.day} ==")
    print(f"candidates: {len(learnings)}" +
          ("  (DRY RUN — nothing will be imprinted)" if args.dry_run else ""))

    if not learnings:
        print("nothing to consolidate.")
        return

    device = SimulatedDevice(persist_path=None if args.dry_run else STORE_PATH)
    brain = LocalBrain(SimulatedBackend(), device.scan("TSC"))

    imprinted, skipped, blocked, held_now = [], [], [], []
    held_store = _load_held()
    for item in learnings:
        text = item["text"]
        # Flow gate (breath spec section 4, integrated 2026-11-03):
        # dialogue-born candidates are HELD the first consolidation they
        # meet — they must survive a full cycle before the Judge rules.
        # Dream-born candidates rule immediately. Nothing true is harmed
        # by the wait; everything false about haste is exposed by it.
        key = _cand_key(text)
        born = _born_of(item)
        if born == "dialogue" and key not in held_store:
            if args.dry_run:
                print(f"  WOULD HOLD (flow gate): {text[:70]}")
            else:
                held_store[key] = {"text": text[:200], "born": born,
                                   "first_seen": args.day,
                                   "source": item.get("source", "")}
                _save_held(held_store)
                audit_log(AUDIT_PATH, "judge", "held:flow-gate",
                          f"{text[:120]} | dialogue-born, first sighting")
                print(f"  HELD (flow gate — must survive a cycle): "
                      f"{text[:70]}")
            held_now.append((text, "flow gate"))
            continue
        if key in held_store:
            print(f"  (gate survived — ruling now): {text[:70]}")
        verdict, reason = judge_rule(text, device.scan("TSC"))
        if not args.dry_run:
            audit_log(AUDIT_PATH, "judge", f"rule:{verdict}",
                      f"{text[:120]} | {reason}")
        if verdict == "APPROVED":
            if already_in_psc(device, text):
                skipped.append((text, "already in PSC"))
                print(f"  SKIP (dup): {text[:70]}")
                continue
            if args.dry_run:
                imprinted.append((text, "dry-run"))
                print(f"  WOULD IMPRINT: {text[:70]}")
            else:
                r = render_thought(device, brain,
                                   stimulus=f"Consolidation candidate: {text}",
                                   propose_imprint=text)
                if r["imprinted"]:
                    imprinted.append((text, reason))
                    print(f"  IMPRINTED: {text[:70]}")
                else:
                    blocked.append((text, r["verdict"], r["verdict_reason"]))
                    # Loss trace (2026-10-19): a candidate the Judge ruled
                    # APPROVED but the writers refused used to vanish with
                    # only this stdout print. Put the loss on the record —
                    # what was lost, and why (the trace carries the ring's
                    # refusal reason). Visibility only; verdicts unchanged.
                    audit_log(AUDIT_PATH, "consolidate", "loss:write-blocked",
                              f"{text[:120]} | write verdict:{r['verdict']} "
                              f"| {r['verdict_reason']} "
                              f"| trace: {'; '.join(r['trace'])}")
                    print(f"  BLOCKED at write: {text[:70]}")
        elif verdict == "NOTED":
            skipped.append((text, f"NOTED: {reason}"))
            print(f"  SKIP (noted): {text[:70]} — {reason}")
        else:
            blocked.append((text, verdict, reason))
            print(f"  {verdict}: {text[:70]} — {reason}")

    print("-" * 60)
    print(f"imprinted: {len(imprinted)} | skipped: {len(skipped)} | "
          f"blocked: {len(blocked)} | held (flow gate): {len(held_now)}")
    if not args.dry_run:
        print(f"PSC now holds {len(device.scan('PSC'))} entries. "
              f"Writers committed {device.sleeve['total_writes']} this run.")

    if args.compose:
        import compose
        cstats = compose.compose_pass(
            device, brain,
            audit_path=None if args.dry_run else AUDIT_PATH,
            dry_run=args.dry_run)
        print(f"derived (compose): proposed {cstats['proposed']} | "
              f"judge-approved {cstats['approved']} | "
              f"imprinted {cstats['imprinted']} | "
              f"not-approved {cstats['rejected']} | "
              f"write-blocked {cstats['blocked_write']}")
        if not args.dry_run:
            print(f"PSC now holds {len(device.scan('PSC'))} entries "
                  f"after composition.")


if __name__ == "__main__":
    main()
