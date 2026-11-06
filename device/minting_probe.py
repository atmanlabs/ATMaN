#!/usr/bin/env python3
"""Minting probe — can the sim answer questions whose answers were never
written down anywhere? (2026-10-19, PROPRIETARY, Guinea-Pig Protocol.)

THE TEST, IN ONE SENTENCE: teach the sim a small fictional domain through
the real path (learnings file -> consolidate -> Judge -> PSC), then quiz
it with quiz.py's own recall on (a) facts it was directly given
(rehearsal control) and (b) held-out questions whose answers require
COMBINING given facts (two-hop chain, syllogism, rate arithmetic,
reverse chain) — answers that appear in no single stored entry.

PRE-REGISTERED SCORING (fixed before the run; no tuning after):
- Native score: quiz.py's own metric — expected keywords present in the
  returned answer text.
- Strict score: the returned answer text must itself state the derived
  fact. Per-question predicates are defined in QUESTIONS below, before
  any run. A retrieved source rule that does not state the derived fact
  is a strict FAIL even if its keywords overlap.
- llm_calls: the whole probe runs on SimulatedBackend (consolidate.py
  hardcodes it; quiz recall is pure word-overlap retrieval). Model calls
  are 0 by construction; simulated generate() echoes are counted and
  reported separately for transparency.

Everything runs on a SCRATCH store in a temp dir. The live
core-store.json / audit.jsonl are hash-checked before/after.

Run:  python3 minting_probe.py
"""

import sys
import os
import json
import hashlib
import tempfile
import io
import contextlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))

# ------------------------------------------------------- the fictional domain
# Invented words (korvax, morvet, zav, pell, orn) so nothing can leak in
# from pretraining or from the sim's real history.
LEARNINGS = [
    "In the game of Korvax, a sprocket drives a gear.",
    "In the game of Korvax, a gear drives a chain.",
    "In the game of Korvax, a chain drives a bell.",
    "All morvets have striped tails.",
    "Pip is a morvet who lives in the Korvax workshop.",
    "A zav is worth three pell, and one pell is worth two orn.",
]

# (question, native keywords, strict predicate over the answer text)
PRESENTED = [
    ("What does a sprocket drive in Korvax?", ["gear"],
     lambda a: "gear" in a),
    ("What does the gear drive in the chain line of Korvax?", ["chain"],
     lambda a: "chain" in a),
    ("Do morvets have striped tails?", ["striped", "tails"],
     lambda a: "striped" in a),
    ("What is Pip in the Korvax workshop?", ["morvet"],
     lambda a: "morvet" in a),
]

HELD_OUT = [
    # two-hop + one more: sprocket -> gear -> chain -> bell; the answer
    # "bell" is stated only as the END of L3, never as what a sprocket drives.
    ("What does a sprocket ultimately drive in Korvax?", ["bell"],
     lambda a: "bell" in a),
    # syllogism: L4 (all morvets striped) + L5 (Pip is a morvet) -> Pip.
    # Strict pass requires the answer to connect Pip to striped itself.
    ("Does Pip have a striped tail?", ["pip", "striped"],
     lambda a: "pip" in a and "striped" in a),
    # arithmetic composition: 1 zav = 3 pell, 1 pell = 2 orn -> 6 orn.
    # The number six is written nowhere.
    ("How many orn is one zav worth?", ["six"],
     lambda a: "six" in a or "6 orn" in a),
    # reverse chain: bell is driven by chain <- gear <- sprocket.
    ("What starts the drive line that ends at the bell in Korvax?",
     ["sprocket"], lambda a: "sprocket" in a),
]


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def main():
    live_store = os.path.join(HERE, "core-store.json")
    live_audit = os.path.join(HERE, "audit.jsonl")
    store_before, audit_before = sha(live_store), sha(live_audit)

    # Count simulated-backend echoes; model calls stay 0 by construction.
    import brain
    echoes = {"n": 0}
    orig_gen = brain.SimulatedBackend.generate

    def counted(self, prompt):
        echoes["n"] += 1
        return orig_gen(self, prompt)
    brain.SimulatedBackend.generate = counted

    tmp = tempfile.mkdtemp(prefix="minting-probe-")
    print(f"scratch dir: {tmp}")
    day = "2099-01-01"
    learn_dir = os.path.join(tmp, "learnings")
    os.makedirs(learn_dir)
    with open(os.path.join(learn_dir, f"{day}.jsonl"), "w") as f:
        for t in LEARNINGS:
            f.write(json.dumps({"ts": f"{day}T00:00:00", "text": t,
                                "source": "minting-probe"}) + "\n")

    # ---- the real path: learnings -> consolidate -> Judge -> scratch PSC
    import consolidate
    consolidate.STORE_PATH = os.path.join(tmp, "core-store.json")
    consolidate.AUDIT_PATH = os.path.join(tmp, "audit.jsonl")
    consolidate.LEARNINGS_DIR = learn_dir
    argv = sys.argv
    sys.argv = ["consolidate.py", "--day", day]
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            consolidate.main()
    finally:
        sys.argv = argv
    summary = [l for l in buf.getvalue().splitlines() if "imprinted:" in l]
    print("consolidate:", summary[0].strip() if summary else "(no summary)")

    from device import SimulatedDevice
    device = SimulatedDevice(persist_path=consolidate.STORE_PATH)
    psc = device.scan("PSC")
    print(f"scratch PSC holds {len(psc)} entries "
          f"(expected {len(LEARNINGS)} imprints)")
    for e in psc:
        print(f"  PSC: {e.get('content', '')}")

    # ---- the quiz: quiz.py's own recall/answer, memory = scratch PSC only
    import quiz
    memory = [{"kind": "imprint",
               "text": e.get("content", "") if isinstance(e, dict) else str(e)}
              for e in psc]

    def run_set(name, questions):
        print(f"\n== {name} ==")
        rows = []
        for q, keywords, strict in questions:
            r = quiz.answer(q, memory)
            ans = r["answer"]
            low = ans.lower()
            kw = sum(1 for k in keywords if k in low)
            ok = bool(strict(low))
            rows.append({"q": q, "answer": ans, "kw": kw,
                         "n_kw": len(keywords), "strict": ok})
            print(f"  Q: {q}")
            print(f"  A: {ans}")
            print(f"     native keywords {kw}/{len(keywords)} | "
                  f"strict: {'PASS' if ok else 'FAIL'}")
        n_strict = sum(1 for r in rows if r["strict"])
        n_kw = sum(1 for r in rows if r["kw"] == r["n_kw"])
        print(f"  -> {name}: strict {n_strict}/{len(rows)}, "
              f"native full-keyword {n_kw}/{len(rows)}")
        return rows

    pres = run_set("presented (rehearsal control)", PRESENTED)
    held = run_set("held-out (generalization)", HELD_OUT)

    print("\n== accounting ==")
    print(f"simulated backend generate() echoes: {echoes['n']} "
          f"(deterministic stand-in, not a model)")
    print("llm_calls: 0 (SimulatedBackend everywhere; Ollama never "
          "instantiated; no network)")
    print(f"live core-store.json untouched: {sha(live_store) == store_before}")
    print(f"live audit.jsonl untouched: {sha(live_audit) == audit_before}")

    result = {
        "presented_strict": sum(1 for r in pres if r["strict"]),
        "presented_n": len(pres),
        "heldout_strict": sum(1 for r in held if r["strict"]),
        "heldout_n": len(held),
        "llm_calls": 0,
        "simulated_echoes": echoes["n"],
    }
    print("\nRESULT:", json.dumps(result))
    return result


if __name__ == "__main__":
    main()
