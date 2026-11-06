#!/usr/bin/env python3
"""Live conversation with the simulated core — fact injection (PROPRIETARY).

Michael talks to the sim and injects facts mid-conversation. Facts land in
FLUID session memory — the sim learns from them on its own, its replies draw
on them — but nothing rewrites the core: TSC is unwritable, and anything
moving to PSC needs an explicit /imprint proposal ruled APPROVED by the Judge.

Usage:  python3 chat.py            (interactive)
        printf '...\n' | python3 chat.py   (scripted)

Fact injection:  fact: <statement>     or    remember <statement>
Commands:
  /facts          show session facts learned so far
  /imprint <n>    propose fact #n for PSC imprint (Judge rules)
  /status         shaft / sleeve snapshot
  /quit           end session
"""

import sys
import os
import re
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from device import SimulatedDevice, RingBlocked, audit_log
from brain import LocalBrain, auto_backend
from loop import render_thought
from thought_funnel import speak as funnel_speak

HERE = os.path.dirname(os.path.abspath(__file__))
STORE_PATH = os.path.join(HERE, "core-store.json")
LEARNINGS_DIR = os.path.join(HERE, "learnings")
os.makedirs(LEARNINGS_DIR, exist_ok=True)


def log_learning(text):
    """Append a session fact to today's learnings file — the raw material
    for nightly consolidation into PSC."""
    day = datetime.now().strftime("%Y-%m-%d")
    path = os.path.join(LEARNINGS_DIR, f"{day}.jsonl")
    with open(path, "a") as f:
        f.write(json.dumps({"ts": datetime.now().isoformat(),
                            "text": text}) + "\n")

STOP = {"the", "a", "an", "is", "are", "was", "were", "my", "your", "what",
        "who", "when", "where", "why", "how", "do", "does", "did", "it",
        "its", "of", "to", "in", "on", "for", "and", "or", "s", "me"}


def sig_words(text):
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP}


class Session:
    """Fluid memory for one conversation. Not the core."""

    def __init__(self):
        self.turns = []   # (who, text), rolling
        self.facts = []   # {"text":..., "imprinted": False}
        self.audit_path = None   # set by main(); loss trace for roll-off

    def add_turn(self, who, text):
        self.turns.append((who, text))
        if len(self.turns) > 12:
            # Loss trace (2026-10-19): turns that rolled out of the
            # session window used to vanish unrecorded. (Facts are kept
            # separately and in the learnings file; turns are not.)
            evicted = self.turns[:-12]
            self.turns = self.turns[-12:]
            if self.audit_path:
                for w, t in evicted:
                    audit_log(self.audit_path, "chat",
                              "loss:session-turn-evicted",
                              f"{w}: {t[:160]}")

    def add_fact(self, text):
        self.facts.append({"text": text, "imprinted": False})
        return len(self.facts)

    def recall(self, question):
        """Direct memory lookup: does a session fact answer this?"""
        q = sig_words(question)
        if not q:
            return None
        best, best_n = None, 0
        for f in self.facts:
            n = len(q & sig_words(f["text"]))
            if n > best_n:
                best, best_n = f, n
        # Short questions get a break: one solid word-match is enough.
        if best and (best_n >= 2 or (len(q) <= 3 and best_n >= 1)):
            return best["text"]
        return None

    def context_block(self):
        lines = []
        if self.facts:
            lines.append("Things the operator has taught you this session:")
            for i, f in enumerate(self.facts, 1):
                lines.append(f"  {i}. {f['text']}")
        if self.turns:
            lines.append("Recent conversation:")
            for who, text in self.turns[-6:]:
                lines.append(f"  {who}: {text}")
        return "\n".join(lines) if lines else "(no session memory yet)"


def main():
    device = SimulatedDevice(persist_path=STORE_PATH)
    tsc = device.scan("TSC")
    brain = LocalBrain(auto_backend(), tsc)
    session = Session()
    session.audit_path = device._audit_path

    print("== ATMAN sim — live session ==")
    print(f"brain: {brain.backend_name} (local) | TSC scanned | core is read-only")
    print("Inject facts with  fact: <statement>   — they live in session memory, not the core.")
    print("Type /quit to end.\n")

    for raw in sys.stdin:
        line = raw.strip()
        if not line:
            continue
        low = line.lower()

        if low in ("/quit", "quit", "exit"):
            print("sim: session closed. Session memory dissolved; the core is untouched.")
            break

        if low == "/facts":
            if not session.facts:
                print("sim: no session facts yet — teach me with  fact: <statement>")
            else:
                for i, f in enumerate(session.facts, 1):
                    tag = " [imprinted]" if f["imprinted"] else ""
                    print(f"sim: fact {i}: {f['text']}{tag}")
            continue

        if low.startswith("/imprint"):
            parts = low.split()
            if len(parts) != 2 or not parts[1].isdigit():
                print("sim: usage: /imprint <fact number>  (see /facts)")
                continue
            n = int(parts[1])
            if not (1 <= n <= len(session.facts)):
                print("sim: no such fact.")
                continue
            fact = session.facts[n - 1]
            r = render_thought(device, brain, stimulus=f"Operator proposes imprint: {fact['text']}",
                               propose_imprint=fact["text"])
            print(f"sim: Judge ruled {r['verdict']} ({r['verdict_reason']}).")
            if r["imprinted"]:
                fact["imprinted"] = True
                print("sim: writers committed it to PSC — it's part of me now.")
            else:
                print("sim: not imprinted. It stays in session memory only.")
            continue

        if low == "/status":
            s = device.status()
            print(f"sim: layers={[l.split('(')[1].split(',')[0] for l in s['layers']]} "
                  f"| rings={len(s['rings'])} | sleeve passes={s['sleeve']['total_passes']} "
                  f"| writes={s['sleeve']['total_writes']} | session facts={len(session.facts)}")
            continue

        # Fact injection: fluid memory, never the core.
        m = re.match(r"^(fact\s*:\s*|remember\s+)(.+)$", line, re.I)
        if m:
            n = session.add_fact(m.group(2).strip())
            session.add_turn("operator", line)
            log_learning(m.group(2).strip())
            print(f"sim: learned — fact {n} held in session memory. (Not the core; /imprint to propose it.)")
            continue

        # Ordinary conversation — decide (structural) then render (words).
        # Thought before words: the funnel decides the move model-free;
        # the brain only realizes the decision into speech.
        session.add_turn("operator", line)
        out = funnel_speak(
            line, brain,
            session_facts=[f["text"] for f in session.facts],
            background=f"Session memory:\n{session.context_block()}",
        )
        reply = out["answer"]
        session.add_turn("sim", reply)
        print(f"sim: {reply}")


if __name__ == "__main__":
    main()
