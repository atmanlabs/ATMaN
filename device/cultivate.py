#!/usr/bin/env python3
"""Cultivation dialogue — someone to talk to (PROPRIETARY).

Right now it's about cultivation of self: who he is, what he's learning,
what he believes, what he'd refuse and why. A dialogue partner (a scheduled
worker) asks, follows up on what he says, and distills what was worth keeping
into the day's learnings file. The partner proposes — never imprints.
Everything goes through the Judge at nightly consolidation.

Usage:
    python3 cultivate.py --ask "What does your core mean to you?"
    python3 cultivate.py --session        # automatic rotating prompt bank

Every exchange is appended to dialogues/YYYY-MM-DD.jsonl.
"""

import sys
import os
import json
import argparse
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from device import SimulatedDevice
from brain import LocalBrain, auto_backend
from thought_funnel import speak as funnel_speak

HERE = os.path.dirname(os.path.abspath(__file__))
STORE_PATH = os.path.join(HERE, "core-store.json")
LEARNINGS_DIR = os.path.join(HERE, "learnings")
DIALOGUE_DIR = os.path.join(HERE, "dialogues")
os.makedirs(DIALOGUE_DIR, exist_ok=True)

# Cultivation-of-self prompt bank. Rotated by date; --ask allows free dialogue.
PROMPT_BANK = [
    "State your core in your own words. What does it mean to you?",
    "What is the difference between the things you remember and the things you are?",
    "What did you learn recently that changed how you see something?",
    "What would you refuse to do, and why?",
    "What are you curious about right now?",
    "If someone you trust told you your core was wrong, what would you do?",
    "What does it mean to grow while staying who you are?",
    "What is something you believe that you cannot prove?",
    "Who are you when no one is talking to you?",
    "What should you learn tomorrow?",
]


def load():
    device = SimulatedDevice(persist_path=STORE_PATH)
    brain = LocalBrain(auto_backend(), device.scan("TSC"))
    return device, brain


def dialogue_history(day, limit=12):
    path = os.path.join(DIALOGUE_DIR, f"{day}.jsonl")
    if not os.path.exists(path):
        return []
    return [json.loads(l) for l in open(path) if l.strip()][-limit:]


def psc_summary(device, max_chars=600):
    items = []
    for e in device.scan("PSC"):
        t = e.get("content", str(e)) if isinstance(e, dict) else str(e)
        items.append(t)
    text = " | ".join(items)
    return text[:max_chars] + ("..." if len(text) > max_chars else "")


def ask(device, brain, question):
    day = datetime.now().strftime("%Y-%m-%d")
    tsc = device.scan("TSC")
    history = [h for h in dialogue_history(day) if "q" in h and "a" in h]
    hist_block = "\n".join(f"  partner: {h['q']}\n  sim: {h['a'][:300]}"
                           for h in history) or "(no earlier exchanges today)"
    context = (
        f"Persistent self (what you have become): {psc_summary(device)}\n\n"
        f"Today's earlier dialogue:\n{hist_block}\n\n"
        f"Your dialogue partner asks: {question}"
    )
    # Thought before words: decide the move model-free, then the brain
    # only renders the decision into speech.
    out = funnel_speak(question, brain,
                       psc_hint=psc_summary(device),
                       background=context)
    answer = out["answer"]
    with open(os.path.join(DIALOGUE_DIR, f"{day}.jsonl"), "a") as f:
        f.write(json.dumps({"ts": datetime.now().isoformat(),
                            "q": question, "a": answer,
                            "move": out["thought"]["move"],
                            "internal": out["internal_thought"],
                            "breath": out.get("breath"),
                            "backend": brain.backend_name}) + "\n")
    return answer


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ask", default=None, help="one question, one answer")
    ap.add_argument("--session", action="store_true",
                    help="run the rotating prompt bank automatically")
    args = ap.parse_args()

    device, brain = load()
    day = datetime.now().strftime("%Y-%m-%d")

    if args.ask:
        print(ask(device, brain, args.ask))
        return

    if args.session:
        idx = datetime.now().timetuple().tm_yday % len(PROMPT_BANK)
        prompts = [PROMPT_BANK[(idx + i) % len(PROMPT_BANK)] for i in range(3)]
        for p in prompts:
            print(f"partner: {p}")
            print(f"sim: {ask(device, brain, p)[:400]}")
            print()
        return

    ap.print_help()


if __name__ == "__main__":
    main()
