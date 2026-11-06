#!/usr/bin/env python3
"""Minting probe, recall-synthesis variant (2026-10-20, PROPRIETARY,
Guinea-Pig Protocol).

Same test as minting_probe_compose.py — SAME learnings, SAME questions,
SAME pre-registered strict predicates and native keyword scoring,
imported verbatim from minting_probe (LEARNINGS / PRESENTED /
HELD_OUT), SAME consolidate --compose scratch flow. The ONLY change
is on the ANSWER side: quiz.py's single-best-verbatim selection is
replaced by the synthesis selection below, over the IDENTICAL
candidate set (quiz.recall with quiz.answer's own defaults:
top_n=3, min_overlap=2). The composer, the Judge, and the store are
untouched.

PRE-REGISTERED SYNTHESIS RULE (fixed before the run; one mechanism):
  Among the top-3 recall hits, answer with the single hit of highest
  question-term DENSITY = (sig-words shared with the question) /
  (the hit's own sig-word count) — a specificity measure: an atomic
  fact that is mostly about the question beats a longer entry that
  merely mentions it. Ties break by (1) provenance: a derived entry
  (imprinted by the compose pass) beats an original at equal density,
  because the closure is the more composed statement of the pair; then
  (2) recency: the later-imprinted entry wins.
  The answer is that ONE hit's text — never a join, never a dump of
  the top-k — so the strict predicate cannot be passed by a fact
  string merely appearing somewhere in a concatenation. The
  "first-stated fact" reading of every answer is therefore identical
  to its strict reading by construction.

DIAGNOSTIC (measurement only; never consulted by the answer path):
  For each held-out question, EXPECTED_DERIVED below names the derived
  fact a correct answer needs (or None where no derived fact can
  answer). After answering, we check whether that fact's text was
  present anywhere in the top-3 raw recall hits — separating
  "fact absent from the candidate set" from "fact present in the
  candidate set but not surfaced by the selection rule."

Everything runs on a SCRATCH store in a temp dir. The live
core-store.json / audit.jsonl are hash-checked before/after.

Run:  python3 minting_probe_synth.py
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

from thought_funnel import sig_words

K = 3            # candidate set size — quiz.recall/quiz.answer default
MIN_OVERLAP = 2  # quiz.recall/quiz.answer default

# Diagnostic only (see docstring). Parallel to mp.HELD_OUT.
EXPECTED_DERIVED = [
    "ultimately drives a bell",   # 3-hop chain closure
    "pip has a striped tail",     # syllogism closure
    "worth six orn",              # rate-product closure
    None,                         # reverse chain: no derived fact exists
]


def is_derived(entry, originals):
    """Provenance tag: imprinted by the compose pass — identified by
    the composition marker render_thought stored in the entry's
    reasoning field, or by not being one of the source learnings."""
    reasoning = str(entry.get("reasoning", "")).lower() \
        if isinstance(entry, dict) else ""
    content = entry.get("content", "") if isinstance(entry, dict) \
        else str(entry)
    return "composition derivation" in reasoning or content not in originals


def synthesize(question, memory):
    """The synthesis selection: quiz.recall's own top-k, re-selected
    by the pre-registered density/provenance/recency rule."""
    import quiz
    hits = quiz.recall(question, memory, top_n=K, min_overlap=MIN_OVERLAP)
    if not hits:
        return {"answer": ("I don't have anything solid on that — my "
                           "dreams didn't consolidate it."),
                "hits": [], "selected": None, "scored": []}
    scored = []
    for ov_count, ov_words, m in hits:
        n_terms = len(sig_words(m["text"]))
        density = (ov_count / n_terms) if n_terms else 0.0
        scored.append({"ov": ov_count, "density": density,
                       "derived": bool(m.get("derived")),
                       "index": m["index"], "text": m["text"]})
    best = max(scored, key=lambda s: (s["density"], s["derived"],
                                      s["index"]))
    return {"answer": f"From what I dreamed on the canon: "
                      f"{best['text'][:400]}",
            "hits": [{"score": s["ov"]} for s in scored],
            "selected": best, "scored": scored}


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

    tmp = tempfile.mkdtemp(prefix="minting-probe-synth-")
    print(f"scratch dir: {tmp}")
    day = "2099-01-01"
    learn_dir = os.path.join(tmp, "learnings")
    os.makedirs(learn_dir)
    with open(os.path.join(learn_dir, f"{day}.jsonl"), "w") as f:
        for t in mp.LEARNINGS:
            f.write(json.dumps({"ts": f"{day}T00:00:00", "text": t,
                                "source": "minting-probe"}) + "\n")

    # ---- identical store flow to minting_probe_compose.py:
    #      learnings -> consolidate --compose -> Judge -> scratch PSC
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

    # ---- the quiz: same memory, same scoring; ONLY the selection
    #      rule changes (synthesize instead of quiz.answer)
    import quiz
    memory = [{"kind": "imprint",
               "text": e.get("content", "") if isinstance(e, dict) else str(e),
               "derived": is_derived(e, mp.LEARNINGS),
               "index": i}
              for i, e in enumerate(psc)]

    def run_set(name, questions, expected=None):
        print(f"\n== {name} ==")
        rows = []
        for qi, (q, keywords, strict) in enumerate(questions):
            r = synthesize(q, memory)
            ans = r["answer"]
            low = ans.lower()
            kw = sum(1 for k in keywords if k in low)
            ok = bool(strict(low))
            row = {"q": q, "answer": ans, "kw": kw,
                   "n_kw": len(keywords), "strict": ok}
            print(f"  Q: {q}")
            for s in r["scored"]:
                mark = "  <- selected" if s is r["selected"] else ""
                print(f"     hit ov={s['ov']} density={s['density']:.3f} "
                      f"derived={s['derived']} psc_idx={s['index']}: "
                      f"{s['text'][:80]}{mark}")
            if expected is not None:
                fact = expected[qi]
                raw_hits = quiz.recall(q, memory, top_n=K,
                                       min_overlap=MIN_OVERLAP)
                if fact is None:
                    row["fact_in_topk"] = None
                    any_derived = any(h[2].get("derived") for h in raw_hits)
                    print(f"     diagnostic: no derived fact can answer "
                          f"this; derived entry in top-{K}: {any_derived}")
                else:
                    present = any(fact in h[2]["text"].lower()
                                  for h in raw_hits)
                    row["fact_in_topk"] = present
                    print(f"     diagnostic: needed fact '{fact}' in "
                          f"top-{K} raw hits: {present}")
            print(f"  A: {ans}")
            print(f"     native keywords {kw}/{len(keywords)} | "
                  f"strict: {'PASS' if ok else 'FAIL'}")
            rows.append(row)
        n_strict = sum(1 for r in rows if r["strict"])
        n_kw = sum(1 for r in rows if r["kw"] == r["n_kw"])
        print(f"  -> {name}: strict {n_strict}/{len(rows)}, "
              f"native full-keyword {n_kw}/{len(rows)}")
        return rows

    pres = run_set("presented (rehearsal control)", mp.PRESENTED)
    held = run_set("held-out (generalization)", mp.HELD_OUT,
                   expected=EXPECTED_DERIVED)

    print("\n== accounting ==")
    print(f"simulated backend generate() echoes: {echoes['n']} "
          f"(deterministic stand-in, not a model)")
    print("llm_calls: 0 (SimulatedBackend everywhere; Ollama never "
          "instantiated; no network)")
    print(f"live core-store.json untouched: {mp.sha(live_store) == store_before}")
    print(f"live audit.jsonl untouched: {mp.sha(live_audit) == audit_before}")

    result = {
        "condition": "compose+synthesis",
        "presented_strict": sum(1 for r in pres if r["strict"]),
        "presented_n": len(pres),
        "heldout_strict": sum(1 for r in held if r["strict"]),
        "heldout_n": len(held),
        "heldout_fact_in_topk": [r.get("fact_in_topk") for r in held],
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
