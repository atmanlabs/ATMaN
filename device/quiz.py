#!/usr/bin/env python3
"""quiz.py — interrogate the sim on the canon he dreamed about.

Deterministic recall test: for each question, retrieve the top imprinted
dream gists by word overlap and answer WITH the retrieved evidence only.
No model, no invention. If nothing relevant was consolidated, the sim
says so (honest gap). Mike judges: correct, bullshit, or absent.

Usage:
  python3 quiz.py            # run the 12 auto-probes on both modes
  python3 quiz.py mode-a     # auto-probes on one mode
  python3 quiz.py ask mode-a # interactive: Mike asks anything
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from thought_funnel import sig_words

CORPUS_DIR = os.path.join(HERE, "corpus-dreams")

PROBES = [
    ("Who is Sherlock Holmes's brother?", ["mycroft"]),
    ("What is the name of Holmes's landlady?", ["hudson"]),
    ("In A Study in Scarlet, who is the murderer?", ["jefferson", "hope"]),
    ("What instrument does Sherlock Holmes play?", ["violin"]),
    ("Who is Professor Moriarty and where does he die?",
     ["moriarty", "reichenbach"]),
    ("What is the Hound of the Baskervilles really?",
     ["hound", "dog", "phosphorus"]),
    ("Who is Irene Adler and why does Holmes respect her?",
     ["irene", "adler"]),
    ("What is 221B Baker Street?", ["baker", "221b"]),
    ("In The Sign of the Four, what is the treasure?", ["agra"]),
    ("Who is Dr. Watson's wife?", ["mary", "morstan"]),
    ("What drug does Holmes use?", ["cocaine"]),
    ("Who is Inspector Lestrade?", ["lestrade"]),
]


def load_memory(mode):
    """Imprinted gists + dream log gists for one mode."""
    mem = []
    psc_path = os.path.join(CORPUS_DIR, mode, "psc.json")
    if os.path.exists(psc_path):
        with open(psc_path) as f:
            try:
                store = json.load(f)
            except json.JSONDecodeError:
                store = {}
        psc = store.get("PSC", store) if isinstance(store, dict) else store
        if isinstance(psc, list):
            for e in psc:
                c = e.get("content", "") if isinstance(e, dict) else str(e)
                if c:
                    mem.append({"kind": "imprint", "text": c})
    log_path = os.path.join(CORPUS_DIR, mode, "dreams.jsonl")
    if os.path.exists(log_path):
        with open(log_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    d = json.loads(line)
                except json.JSONDecodeError:
                    continue
                # Full narrative first (richest recall surface), then gist.
                for kind, key in (("narrative", "narrative"),
                                  ("gist", "gist")):
                    t = d.get(key, "")
                    if t:
                        mem.append({"kind": kind, "text": t,
                                    "id": d.get("id")})
    return mem


def recall(question, memory, top_n=3, min_overlap=2):
    q = sig_words(question)
    scored = []
    for m in memory:
        ov = q & sig_words(m["text"])
        if ov:
            scored.append((len(ov), sorted(ov), m))
    scored.sort(key=lambda s: -s[0])
    hits = [s for s in scored if s[0] >= min_overlap][:top_n]
    return hits


def answer(question, memory):
    """The sim's answer: retrieved evidence, or an honest gap."""
    hits = recall(question, memory)
    if not hits:
        return {
            "answer": ("I don't have anything solid on that — my dreams "
                       "didn't consolidate it."),
            "hits": [], "verdict_hint": "absent",
        }
    best = hits[0]
    evidence = best[2]["text"][:400]
    return {
        "answer": f"From what I dreamed on the canon: {evidence}",
        "hits": [{"score": h[0], "overlap": h[1],
                  "kind": h[2]["kind"]} for h in hits],
        "verdict_hint": "check",
    }


def auto_probe(mode):
    memory = load_memory(mode)
    print(f"\n### {mode}: {len(memory)} memory items")
    results = []
    for q, keywords in PROBES:
        r = answer(q, memory)
        text_low = r["answer"].lower()
        kw_hit = sum(1 for k in keywords if k in text_low)
        results.append({
            "question": q, "keywords": keywords,
            "keyword_hits": kw_hit, "n_keywords": len(keywords),
            "n_hits": len(r["hits"]),
            "top_score": r["hits"][0]["score"] if r["hits"] else 0,
            "answer": r["answer"][:300],
        })
        mark = "✓" if kw_hit else ("…" if r["hits"] else "✗")
        print(f"  [{mark}] {q}")
        print(f"      -> {r['answer'][:160]}")
    passed = sum(1 for r in results if r["keyword_hits"])
    print(f"  auto-score: {passed}/{len(results)} keyword hits")
    out = os.path.join(CORPUS_DIR, mode, "quiz-report.json")
    with open(out, "w") as f:
        json.dump(results, f, indent=2)
    return results


def interactive(mode):
    memory = load_memory(mode)
    print(f"[{mode}] {len(memory)} memory items. Ask anything (blank quits).")
    while True:
        try:
            q = input("you: ").strip()
        except EOFError:
            break
        if not q:
            break
        r = answer(q, memory)
        print(f"sim: {r['answer']}\n")


def main():
    args = sys.argv[1:]
    if args and args[0] == "ask":
        interactive(args[1] if len(args) > 1 else "mode-a")
        return
    modes = [args[0]] if args else ["mode-a", "mode-b"]
    for m in modes:
        auto_probe(m)


if __name__ == "__main__":
    main()
