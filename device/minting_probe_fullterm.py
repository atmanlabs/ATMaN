#!/usr/bin/env python3
"""Minting probe, FULL-MEMORY terminality variant (2026-10-20,
PROPRIETARY, Guinea-Pig Protocol).

Same test as minting_probe_terminal.py — SAME learnings, SAME
questions, SAME pre-registered strict predicates and native keyword
scoring, imported verbatim from minting_probe, SAME consolidate
--compose scratch flow, SAME candidate set (quiz.recall, top_n=3,
min_overlap=2), SAME staged ordering (density -> terminality ->
provenance -> recency). Exactly ONE thing changes vs the terminal
runner: THE SCOPE OF THE TERMINALITY SUBJECT SET.

PRE-REGISTERED SELECTION RULE (fixed before the run):
  Staged lexicographic filter over the top-3 recall hits:
    1. DENSITY      highest question-term density wins
                    (sig-words shared with the question / the hit's
                    own sig-word count) — the synth rule, unchanged.
    2. TERMINALITY  a hit is TERMINAL iff compose.py's generic SVO
                    extraction parses at least one subject-verb-object
                    statement from it AND none of its (singularized)
                    object terms appears as a (singularized) subject
                    term of ANY OTHER ENTRY IN THE FULL MEMORY (the
                    whole scratch PSC), not merely of the other
                    top-3 candidate hits — the chain-end fact, not a
                    middle link, judged against everything the sim
                    holds. A hit with no parseable SVO is NEUTRAL
                    (criterion does not apply to it). The stage
                    discriminates only when the surviving pool
                    contains BOTH a terminal and a non-terminal hit;
                    otherwise the pool passes through unchanged.
    3. PROVENANCE   a compose-derived entry beats an original.
    4. RECENCY      the later-imprinted entry wins.
  Motivation (from the terminal run's own diagnostic): in-set
  terminality was vacuous on held-out Q1 — all three candidate hits
  shared subject "sprocket", so the 2-hop closure read terminal
  inside the set and recency decided. At memory scope the same
  diagnostic showed the 2-hop closure terminal=False ("chain" is
  the subject of "a chain drives a bell", a non-candidate entry)
  and the 3-hop closure terminal=True. This run tests whether that
  wider scope makes Q1's win structural (decided AT the terminality
  stage) instead of order-based.
  Known risk, pre-registered: full-memory scope makes MORE hits
  non-terminal (more subjects exist), so the presented control set
  is watched for regressions.
  The answer is the ONE selected hit's text — same as synth.

DECIDER INSTRUMENTATION (measurement only): the staged filter
records the pool size after each stage; the DECIDER for a question
is the stage at which the pool first reached size 1.

DIAGNOSTICS (measurement only; never consulted by the answer path):
  - Per held-out question, whether the needed derived fact (from
    minting_probe_synth.EXPECTED_DERIVED) is present in the top-3
    raw recall hits — as in the synth runner.
  - Per hit, the IN-SET terminality flag (the terminal runner's
    operative value, here demoted to a diagnostic) so the two
    scopes can be compared hit by hit.

Store side must reproduce the synth/terminal runs exactly
(5 derived proposed -> 5 Judge-APPROVED -> 5 imprinted); a banner
prints otherwise.

Everything runs on a SCRATCH store in a temp dir. The live
core-store.json / audit.jsonl are hash-checked before/after.

Run:  python3 minting_probe_fullterm.py
"""

import sys
import os
import json
import tempfile
import io
import contextlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))

import minting_probe as mp            # data + scoring, verbatim
import minting_probe_synth as mps     # flow constants + helpers, reused
import compose                        # generic SVO parsing, reused

from thought_funnel import sig_words

K = mps.K
MIN_OVERLAP = mps.MIN_OVERLAP
EXPECTED_DERIVED = mps.EXPECTED_DERIVED


def _parse_relations(text):
    """(subject_terms, object_terms), singularized, from compose.py's
    generic SVO extraction. Empty sets when nothing parses."""
    subs, objs = set(), set()
    for s in compose._extract(text)["svo"]:
        subs.add(compose._singular(s["subj"]))
        objs.add(compose._singular(s["obj"]))
    return subs, objs


def select_fullterm(question, memory):
    """The full-memory terminality selection: quiz.recall's own
    top-k, filtered by the pre-registered density -> terminality ->
    provenance -> recency stages. Terminality's subject set is the
    FULL memory (every PSC entry), not the candidate set. Returns
    the answer plus full instrumentation."""
    import quiz
    hits = quiz.recall(question, memory, top_n=K, min_overlap=MIN_OVERLAP)
    if not hits:
        return {"answer": ("I don't have anything solid on that — my "
                           "dreams didn't consolidate it."),
                "hits": [], "selected": None, "scored": [],
                "decider": None, "stages": []}

    parsed = {m["index"]: _parse_relations(m["text"])
              for _c, _w, m in hits}
    # OPERATIVE in this variant: subject terms across the WHOLE memory
    full_parsed = {m["index"]: _parse_relations(m["text"]) for m in memory}

    recs = []
    for ov_count, _ov_words, m in hits:
        subs, objs = parsed[m["index"]]
        # THE one change vs minting_probe_terminal.py: the operative
        # terminal flag draws its subject set from full_parsed (the
        # whole store), not from parsed (the candidate set).
        full_other = set()
        for idx2, (s2, _o2) in full_parsed.items():
            if idx2 != m["index"]:
                full_other |= s2
        if not subs and not objs:
            terminal = None            # no parseable SVO: neutral
        else:
            terminal = not (objs & full_other)
        # diagnostic only: the terminal runner's in-set value
        inset_other = set()
        for idx2, (s2, _o2) in parsed.items():
            if idx2 != m["index"]:
                inset_other |= s2
        terminal_inset = None if (not subs and not objs) \
            else not (objs & inset_other)
        n_terms = len(sig_words(m["text"]))
        recs.append({"ov": ov_count,
                     "density": (ov_count / n_terms) if n_terms else 0.0,
                     "terminal": terminal,
                     "terminal_inset": terminal_inset,
                     "derived": bool(m.get("derived")),
                     "index": m["index"], "text": m["text"]})

    def stage_density(pool):
        mx = max(r["density"] for r in pool)
        return [r for r in pool if r["density"] == mx]

    def stage_terminality(pool):
        # discriminates only when the pool holds both kinds
        if any(r["terminal"] is True for r in pool) and \
                any(r["terminal"] is False for r in pool):
            return [r for r in pool if r["terminal"] is True]
        return pool

    def stage_provenance(pool):
        if any(r["derived"] for r in pool):
            return [r for r in pool if r["derived"]]
        return pool

    def stage_recency(pool):
        mx = max(r["index"] for r in pool)
        return [r for r in pool if r["index"] == mx]

    pool = recs[:]
    stages, decider = [], None
    for name, fn in (("density", stage_density),
                     ("terminality", stage_terminality),
                     ("provenance", stage_provenance),
                     ("recency", stage_recency)):
        new = fn(pool)
        stages.append((name, len(pool), len(new)))
        pool = new
        if len(pool) == 1 and decider is None:
            decider = name
    best = pool[0]
    return {"answer": f"From what I dreamed on the canon: "
                      f"{best['text'][:400]}",
            "hits": [{"score": r["ov"]} for r in recs],
            "selected": best, "scored": recs,
            "decider": decider, "stages": stages}


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

    tmp = tempfile.mkdtemp(prefix="minting-probe-fullterm-")
    print(f"scratch dir: {tmp}")
    day = "2099-01-01"
    learn_dir = os.path.join(tmp, "learnings")
    os.makedirs(learn_dir)
    with open(os.path.join(learn_dir, f"{day}.jsonl"), "w") as f:
        for t in mp.LEARNINGS:
            f.write(json.dumps({"ts": f"{day}T00:00:00", "text": t,
                                "source": "minting-probe"}) + "\n")

    # ---- identical store flow to minting_probe_synth.py:
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
    n_appr = sum(1 for a in c_rules if a["action"] == "rule:APPROVED")
    print(f"compose audit: proposed {len(c_rules)} | "
          f"approved {n_appr} | imprinted {len(c_imp)}")
    store_ok = (len(c_rules), n_appr, len(c_imp)) == (5, 5, 5)
    if not store_ok:
        print("!!! STORE-SIDE MISMATCH: expected 5 proposed / 5 approved"
              " / 5 imprinted (synth/terminal-run reproduction) !!!")

    # ---- the quiz: same memory, same scoring; ONLY the terminality
    #      scope changes (full memory, vs the terminal runner's
    #      candidate-set scope; ordering otherwise identical)
    import quiz
    memory = [{"kind": "imprint",
               "text": e.get("content", "") if isinstance(e, dict) else str(e),
               "derived": mps.is_derived(e, mp.LEARNINGS),
               "index": i}
              for i, e in enumerate(psc)]

    def run_set(name, questions, expected=None):
        print(f"\n== {name} ==")
        rows = []
        for qi, (q, keywords, strict) in enumerate(questions):
            r = select_fullterm(q, memory)
            ans = r["answer"]
            low = ans.lower()
            kw = sum(1 for k in keywords if k in low)
            ok = bool(strict(low))
            row = {"q": q, "answer": ans, "kw": kw,
                   "n_kw": len(keywords), "strict": ok,
                   "decider": r["decider"]}
            print(f"  Q: {q}")
            for s in r["scored"]:
                mark = "  <- selected" if s is r["selected"] else ""
                print(f"     hit ov={s['ov']} density={s['density']:.3f} "
                      f"terminal(full-mem)={s['terminal']} "
                      f"(in-set: {s['terminal_inset']}) "
                      f"derived={s['derived']} psc_idx={s['index']}: "
                      f"{s['text'][:80]}{mark}")
            if r["stages"]:
                trace = " -> ".join(f"{n}:{a}->{b}"
                                    for n, a, b in r["stages"])
                print(f"     stages: {trace} | decider: {r['decider']}")
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
        "condition": "compose+density+terminality-full-memory",
        "terminality_scope": "full-memory (all scratch-PSC subjects)",
        "presented_strict": sum(1 for r in pres if r["strict"]),
        "presented_n": len(pres),
        "heldout_strict": sum(1 for r in held if r["strict"]),
        "heldout_n": len(held),
        "presented_deciders": [r["decider"] for r in pres],
        "heldout_deciders": [r["decider"] for r in held],
        "heldout_fact_in_topk": [r.get("fact_in_topk") for r in held],
        "llm_calls": 0,
        "simulated_echoes": echoes["n"],
        "store_side_ok": store_ok,
        "derived_proposed": len(c_rules),
        "derived_approved": n_appr,
        "derived_imprinted": len(c_imp),
        "derived_claims": derived,
    }
    print("\nRESULT:", json.dumps(result))
    return result


if __name__ == "__main__":
    main()
