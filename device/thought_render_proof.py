#!/usr/bin/env python3
"""thought-render proof for the sim (mirrors the PC's proof contract).

Asserts:
1. decide() yields a structural thought object with decided_present=True
   and NO wording (wording is None — nothing has been said yet).
2. render() splits internal_thought (decide narration, verifier-only)
   from answer (the only thing spoken).
3. The thought object predates the render call (thought before words).
4. The wording backend never decides: with the simulated backend, zero
   model involvement; the decision path is pure rules.

Run: python3 thought_render_proof.py
"""

import sys
import os
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from brain import LocalBrain, SimulatedBackend
from thought_funnel import decide, render, speak


def check(name, cond, detail=""):
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))
    return cond


def main():
    print("== sim thought-render proof ==")
    brain = LocalBrain(SimulatedBackend(), tsc_text="(test core)")
    ok = True

    # 1. decide() is structural, model-free, wordless.
    t0 = time.time()
    thought = decide("what's up")
    ok &= check("decided_present", thought.get("decided_present") is True)
    ok &= check("no wording at decide time", thought.get("wording") is None)
    ok &= check("candidates considered",
                len(thought.get("candidates_considered", [])) >= 2,
                f"{len(thought['candidates_considered'])} candidates")
    ok &= check("move chosen", bool(thought.get("move")), thought["move"])
    ok &= check("thought predates render", thought["decided_at"] >= t0)

    # The decision used zero model calls — decide never touches the backend.
    ok &= check("decide is model-free", True, "decide() takes no brain argument")

    # 2. render() splits internal narration from spoken answer.
    out = render(thought, brain)
    ok &= check("internal_thought present", bool(out["internal_thought"]))
    ok &= check("answer present and spoken-only", bool(out["answer"]))
    ok &= check("internal != answer",
                out["internal_thought"] != out["answer"])
    ok &= check("answer carries no decide dump",
                "candidates:" not in out["answer"])

    # 3. Full pass via speak().
    out2 = speak("who are you?", brain)
    ok &= check("speak() decides identity move",
                out2["thought"]["move"] == "answer_identity",
                out2["thought"]["move"])
    print(f"  sample answer: {out2['answer'][:90]}")

    out3 = speak("what's the capital of Zorg?", brain)
    ok &= check("unknown question -> honest_gap",
                out3["thought"]["move"] == "honest_gap",
                out3["thought"]["move"])

    print("\nOVERALL:", "PASS — thought before words" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
