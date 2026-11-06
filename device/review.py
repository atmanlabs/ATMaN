#!/usr/bin/env python3
"""Daily review — recheck the day, catch what the machine missed (PROPRIETARY).

Checks and balances: the Judge rules, the operator reviews. Everything the
sim went through in a day — learnings, rulings, imprints, blocks — is laid
out for recheck. The operator can force-imprint something the Judge skipped
or retract something that shouldn't have stuck. Every override is audit-logged;
nothing happens off the books. TSC is etched — not even the operator override
can touch it.

Usage:  python3 review.py [--day YYYY-MM-DD]

Commands:
  show <n>        full detail on learning #n
  imprint <n>     operator override: force learning #n into PSC (logged)
  retract <n>     operator override: pull PSC entry #n back out (logged)
  psc             list what's currently in the persistent core
  audit           tail of the audit trail
  quit            end review
"""

import sys
import os
import json
import argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from device import SimulatedDevice, RingBlocked
from loop import judge_rule

HERE = os.path.dirname(os.path.abspath(__file__))
STORE_PATH = os.path.join(HERE, "core-store.json")
AUDIT_PATH = os.path.join(HERE, "audit.jsonl")
LEARNINGS_DIR = os.path.join(HERE, "learnings")


def load_learnings(day):
    path = os.path.join(LEARNINGS_DIR, f"{day}.jsonl")
    if not os.path.exists(path):
        return []
    return [json.loads(l) for l in open(path) if l.strip()]


def psc_texts(device):
    out = []
    for e in device.scan("PSC"):
        out.append(e.get("content", str(e)) if isinstance(e, dict) else str(e))
    return out


def disposition(device, text):
    texts = [t.strip().lower() for t in psc_texts(device)]
    if text.strip().lower() in texts:
        return "IMPRINTED"
    verdict, reason = judge_rule(text, device.scan("TSC"))
    return f"{verdict} ({reason})"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--day", default=datetime.now().strftime("%Y-%m-%d"))
    args = ap.parse_args()

    learnings = load_learnings(args.day)
    device = SimulatedDevice(persist_path=STORE_PATH)

    print(f"== review: {args.day} ==")
    if not learnings:
        print("no learnings logged that day.")
    for i, item in enumerate(learnings, 1):
        print(f"  {i}. [{disposition(device, item['text'])}] {item['text'][:80]}")
    print(f"\nPSC holds {len(psc_texts(device))} entries. "
          "Commands: show <n> | imprint <n> | retract <n> | psc | audit | quit\n")

    for raw in sys.stdin:
        line = raw.strip()
        if not line:
            continue
        low = line.lower()
        if low in ("quit", "exit", "/quit"):
            print("review closed. The audit trail keeps everything.")
            break

        if low == "psc":
            for i, t in enumerate(psc_texts(device)):
                print(f"  PSC[{i}]: {t[:100]}")
            continue

        if low == "audit":
            if os.path.exists(AUDIT_PATH):
                lines = open(AUDIT_PATH).read().strip().split("\n")
                for l in lines[-10:]:
                    r = json.loads(l)
                    print(f"  {r['ts'][11:19]} {r['actor']}: {r['action']} — {r['detail'][:90]}")
            else:
                print("  audit trail is empty.")
            continue

        parts = low.split()
        if len(parts) == 2 and parts[0] in ("show", "imprint", "retract") and parts[1].isdigit():
            n = int(parts[1])
            cmd = parts[0]

            if cmd == "retract":
                texts = psc_texts(device)
                if not (0 <= n < len(texts)):
                    print("  no such PSC entry.")
                    continue
                print(f"  about to retract PSC[{n}]: {texts[n][:80]}")
                print("  type a reason (or empty to cancel):")
                reason = sys.stdin.readline().strip()
                if not reason:
                    print("  cancelled.")
                    continue
                device.operator_retract("PSC", n, reason)
                print("  retracted and audit-logged.")
                continue

            if not (1 <= n <= len(learnings)):
                print("  no such learning.")
                continue
            text = learnings[n - 1]["text"]
            if cmd == "show":
                v, r = judge_rule(text, device.scan("TSC"))
                print(f"  learning {n}: {text}")
                print(f"  logged: {learnings[n-1]['ts']}")
                print(f"  judge: {v} ({r})")
                print(f"  disposition: {disposition(device, text)}")
                continue
            if cmd == "imprint":
                d = disposition(device, text)
                if d == "IMPRINTED":
                    print("  already in PSC.")
                    continue
                print(f"  override-imprint learning {n}: {text[:80]}")
                print(f"  judge said: {d}")
                print("  type a reason (or empty to cancel):")
                reason = sys.stdin.readline().strip()
                if not reason:
                    print("  cancelled.")
                    continue
                try:
                    device.operator_write("PSC", text, reason)
                    print("  imprinted by operator override — audit-logged.")
                except RingBlocked as e:
                    print(f"  refused: {e}")
                continue

        print("  commands: show <n> | imprint <n> | retract <n> | psc | audit | quit")


if __name__ == "__main__":
    main()
