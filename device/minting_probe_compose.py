#!/usr/bin/env python3
"""Minting probe, composition variant (2026-10-20, PROPRIETARY,
Guinea-Pig Protocol).

Same test as minting_probe.py — SAME learnings, SAME questions, SAME
pre-registered strict predicates and native keyword scoring, imported
verbatim from minting_probe (LEARNINGS / PRESENTED / HELD_OUT). The
ONLY change: consolidation runs with --compose, so the composition
step (compose.py) derives Judge-gated claims from the freshly
imprinted PSC before the quiz. minting_probe.py itself is untouched.

Everything runs on a SCRATCH store in a temp dir. The live
core-store.json / audit.jsonl are hash-checked before/after.

Run:  python3 minting_probe_compose.py
"""

import sys
import os
import json
import tempfile
import io
import contextlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))

import minting_probe as mp  # data + scoring, verbatim


def main():
    live_store = os.path.join(HERE, "core-store.json")
    live_audit = os.path.join(HERE, "audit.jsonl")
    store_before, audit_before = mp.sha(live_store), mp.sha(live_audit)

    import brain
    echoes = {"n": 0}
    orig_gen = brain.SimulatedBackend.generate

    def counted(self, prompt):
        echoes["n"] += 1
        return orig_gen(self, prompt)
    brain.SimulatedBackend.generate = counted

    tmp = tempfile.mkdtemp(prefix="minting-probe-compose-")
    print(f"scratch dir: {tmp}")
    day = "2099-01-01"
    learn_dir = os.path.join(tmp, "learnings")
    os.makedirs(learn_dir)
    with open(os.path.join(learn_dir, f"{day}.jsonl"), "w") as f:
        for t in mp.LEARNINGS:
            f.write(json.dumps({"ts": f"{day}T00:00:00", "text": t,
                                "source": "minting-probe"}) + "\n")

    # ---- the real path + composition: learnings -> consolidate
    #      --compose -> Judge -> scratch PSC (originals + derived)
    import consolidate
    consolidate.STORE_PATH = os.path.join(tmp, "core-store.json")
    consolidate.AUDIT_PATH = os.path.join(tmp, "audit.jsonl")
    consolidate.LEARNINGS_DIR = learn_dir
    argv = sys.argv
    sys.argv = ["consolidate.py", "--day", day, "--compose"]
    buf = io.StringIO()
    try:
        with contextlib.redirect_stdout(buf):
            consolidate.main()
    finally:
        sys.argv = argv
    out = buf.getvalue()
    for line in out.splitlines():
        if "imprinted:" in line or "derived (compose):" in line \
                or "DERIVED" in line or "after composition" in line:
            print("consolidate:", line.strip())

    # ---- derived-claim receipts: store diff + scratch audit tallies
    from device import SimulatedDevice
    device = SimulatedDevice(persist_path=consolidate.STORE_PATH)
    psc = device.scan("PSC")
    print(f"scratch PSC holds {len(psc)} entries "
          f"({len(mp.LEARNINGS)} originals + derived)")
    for e in psc:
        print(f"  PSC: {e.get('content', '')}")
    derived = [e.get("content", "") for e in psc
               if e.get("content", "") not in mp.LEARNINGS]
    print(f"derived claims imprinted ({len(derived)}):")
    for d in derived:
        print(f"  DERIVED: {d}")

    audit = []
    if os.path.exists(consolidate.AUDIT_PATH):
        with open(consolidate.AUDIT_PATH) as f:
            audit = [json.loads(l) for l in f if l.strip()]
    c_rules = [a for a in audit
               if a.get("actor") == "compose"
               and str(a.get("action", "")).startswith("rule:")]
    c_imp = [a for a in audit if a.get("action") == "derived:imprinted"]
    print(f"compose audit: proposed {len(c_rules)} | "
          f"approved {sum(1 for a in c_rules if a['action'] == 'rule:APPROVED')} | "
          f"imprinted {len(c_imp)}")
    for a in c_rules:
        print(f"  JUDGE {a['action']}: {a['detail']}")

    # ---- the quiz: identical to minting_probe.py (quiz.py recall,
    #      memory = scratch PSC only, same scoring)
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

    pres = run_set("presented (rehearsal control)", mp.PRESENTED)
    held = run_set("held-out (generalization)", mp.HELD_OUT)

    print("\n== accounting ==")
    print(f"simulated backend generate() echoes: {echoes['n']} "
          f"(deterministic stand-in, not a model)")
    print("llm_calls: 0 (SimulatedBackend everywhere; Ollama never "
          "instantiated; no network)")
    print(f"live core-store.json untouched: {mp.sha(live_store) == store_before}")
    print(f"live audit.jsonl untouched: {mp.sha(live_audit) == audit_before}")

    result = {
        "presented_strict": sum(1 for r in pres if r["strict"]),
        "presented_n": len(pres),
        "heldout_strict": sum(1 for r in held if r["strict"]),
        "heldout_n": len(held),
        "llm_calls": 0,
        "simulated_echoes": echoes["n"],
        "derived_proposed": len(c_rules),
        "derived_approved": sum(1 for a in c_rules
                                if a["action"] == "rule:APPROVED"),
        "derived_imprinted": len(c_imp),
        "derived_claims": derived,
    }
    print("\nRESULT:", json.dumps(result))
    return result


if __name__ == "__main__":
    main()
