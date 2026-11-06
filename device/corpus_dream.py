#!/usr/bin/env python3
"""corpus_dream.py — load a book into him overnight.

Two dream modes over the same external corpus, on ISOLATED devices
(separate PSCs, separate logs):

  Mode A (generated): the existing attractor machinery — AttractorDreamer
  proposes gists from sampled corpus chunks.

  Mode B (rendered — Mike's thesis): the sim DECIDES the dream first.
  decide_dream() builds a structural thought object (intent, chosen braid
  of sources, the question the dream turns over, candidates considered)
  with wording=None by construction. render_dream() then realizes ONLY
  that decision into a scenario, deterministically. Same downstream gates
  as Mode A: reconciler -> guardian -> Judge -> ring-gated PSC imprint.

Corpus chunks are external published text under study. They are never
merged into learnings/ as autobiography. Imprinted gists keep the
existing "DREAM GIST — speculative lesson" label.
"""

import json
import os
import random
import sys
import time
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
DEVICE_DIR = os.path.dirname(HERE)
sys.path.insert(0, DEVICE_DIR)

from dream import DreamCycle
from device import SimulatedDevice, RingBlocked
from loop import judge_rule
from thought_funnel import sig_words

CORPUS_DIR = os.path.join(HERE, "corpus-dreams")
CORPUS_PATH = os.path.join(HERE, "runtime", "corpus",
                           "holmes-corpus.jsonl")


# ---------------------------------------------------------------- pool

class CorpusDreamCycle(DreamCycle):
    """DreamCycle whose pool is the external corpus, not the dream feed."""

    def __init__(self, corpus, *args, **kwargs):
        self._corpus = corpus
        super().__init__(*args, **kwargs)

    def _pool(self):
        self._pool_stats = {"corpus": True, "chunks": len(self._corpus)}
        return self._corpus


def load_corpus(path=CORPUS_PATH):
    items = []
    with open(path) as f:
        for line in f:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    # Shuffle once (seeded): the sampler walks weight order, so without
    # this it would consume the corpus front-to-back and starve later books.
    rnd = random.Random(20260926)
    rnd.shuffle(items)
    return items


# ---------------------------------------------------------------- Mode B
# decide -> render for dreams. The decision exists before any wording.

# Harder stopwords for dream overlap: dialogue verbs and glue words that
# dominate fiction but carry no theme. sig_words() alone is too permissive.
DREAM_STOP_EXTRA = {
    "as", "at", "be", "been", "being", "after", "before", "while",
    "there", "their", "then", "than", "also", "just", "more", "most",
    "such", "only", "very", "much", "many", "well", "even", "still",
    "back", "down", "over", "under", "between", "through", "during",
    "again", "once", "here", "now", "out", "off", "had", "has", "have",
    "will", "would", "could", "should", "shall", "may", "might", "must",
    "cannot", "however", "though", "although", "upon", "within",
    "without", "along", "among", "every", "each", "both", "either",
    "neither", "same", "own", "too", "quite", "rather", "around",
    "into", "onto", "whose", "whom", "said", "says", "say", "told",
    "tell", "asked", "ask", "answered", "answer", "replied", "reply",
    "cried", "exclaimed", "remarked", "observed", "continued", "added",
    "murmured", "whispered", "returned", "began", "went", "came",
    "got", "get", "made", "make", "took", "take", "saw", "see", "look",
    "looked", "seemed", "seem", "knew", "know", "thought", "think",
    "felt", "feel", "turned", "turn", "put", "set", "stood", "stand",
}


def dream_sig_words(text):
    return {w for w in sig_words(text)
            if len(w) > 3 and w not in DREAM_STOP_EXTRA}


def _braid_score(braid):
    sigs = [dream_sig_words(s["text"]) for s in braid]
    score, shared = 0, set()
    for i in range(len(sigs)):
        for j in range(i + 1, len(sigs)):
            ov = sigs[i] & sigs[j]
            score += len(ov)
            shared |= ov
    return score, sorted(shared)


def decide_dream(sources, pool, sample_counts):
    """Model-free structural dream decision. No wording is produced."""
    t0 = time.time()

    # Candidate braids: the sampled set + 3 single-swap alternatives.
    candidates = [{"braid": [s["id"] for s in sources],
                   "why": "as sampled"}]
    used = {s["id"] for s in sources}
    alts = [p for p in pool if p["id"] not in used]
    alts.sort(key=lambda p: -(float(p.get("weight", 1.0))
                              * 0.5 ** sample_counts.get(p["id"], 0)))
    for k in range(min(3, len(alts))):
        swap = list(sources)
        swap[k % len(swap)] = alts[k]
        candidates.append({"braid": [s["id"] for s in swap],
                           "why": f"swap in {alts[k]['id']}"})

    by_id = {s["id"]: s for s in sources}
    by_id.update({p["id"]: p for p in alts[:3]})
    scored = []
    for c in candidates:
        braid = [by_id[i] for i in c["braid"]]
        score, shared = _braid_score(braid)
        scored.append({"braid": c["braid"], "why": c["why"],
                       "score": score, "shared": shared[:12]})
    scored.sort(key=lambda c: -c["score"])
    chosen = scored[0]

    shared = chosen["shared"]
    if shared:
        question = ("what connects " + ", ".join(shared[:5]) +
                    " across these threads?")
    else:
        question = "what endures across these threads?"

    thought = {
        "stimulus": "dream: consolidate tonight's material",
        "intent": "consolidate",
        "move": "dream",
        "braid": chosen["braid"],
        "dream_question": question,
        "overlap_evidence": chosen["shared"],
        "candidates_considered": [
            {"braid": c["braid"], "score": c["score"], "why": c["why"]}
            for c in scored],
        "decided_present": True,
        "decided_at": t0,
        "wording": None,  # no wording exists yet — by construction
    }
    return thought


def render_dream(thought, by_id):
    """Realize the ALREADY-DECIDED dream into a scenario. Deterministic."""
    assert thought.get("decided_present") and thought.get("wording") is None, \
        "render requires a decided, unworded thought"
    threads = []
    for sid in thought["braid"]:
        t = by_id[sid]["text"][:140].replace("\n", " ")
        threads.append(t)
    narrative = (
        "I dreamed I was turning over a question: "
        f"{thought['dream_question']} "
        f"One thread: {threads[0]} "
        f"Another: {threads[1] if len(threads) > 1 else '—'} "
        f"A third: {threads[2] if len(threads) > 2 else '—'} "
        f"What held them together: "
        f"{', '.join(thought['overlap_evidence'][:8]) or 'nothing I could name'}.")
    gist = (f"DREAM THREAD — speculative: {thought['dream_question']} "
            f"| threads: {' // '.join(t[:90] for t in threads)}")
    internal = ("decided braid=" + ",".join(thought["braid"]) +
                f" | question={thought['dream_question']} | candidates=" +
                ",".join(f"{c['braid'][0]}..({c['score']})"
                          for c in thought["candidates_considered"]))
    return {"thought": thought, "internal_thought": internal,
            "narrative": narrative[:900], "gist": gist[:600]}


def run_one_rendered(cyc):
    """Mode B dream: decide -> render, then the standard gates."""
    dream_id = uuid.uuid4().hex[:16]
    t0 = time.time()
    cycle = {"id": dream_id, "ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
             "provenance": "DREAM", "mode": "rendered",
             "quality_gate": "decide->render + reconciler+guardian (model-free)"}
    try:
        sources = cyc.sample(3)
        if len(sources) < 2:
            cycle.update(status="skipped", reason="not enough sources",
                         duration_s=round(time.time() - t0, 1))
            cyc._log_cycle(cycle)
            return cycle
        cycle["sources"] = [s["id"] for s in sources]
        pool = cyc._pool()
        by_id = {p["id"]: p for p in pool}

        # 1. DECIDE (structural, model-free, no wording)
        thought = decide_dream(sources, pool, cyc._sample_counts)
        # 2. RENDER (realize only the decision)
        ren = render_dream(thought, by_id)
        cycle["dream_question"] = thought["dream_question"]
        cycle["decided_braid"] = thought["braid"]
        cycle["candidates"] = len(thought["candidates_considered"])
        cycle["narrative"] = ren["narrative"]
        cycle["gist"] = ren["gist"]
        cycle["internal_thought"] = ren["internal_thought"]

        # 3-5. Same gates as Mode A.
        m = cyc.reconciler.measure(ren["gist"], sources,
                                   cyc._recent_gist_texts)
        cycle["reconciler"] = m
        action, greason = cyc.guardian.review(m)
        cycle["guardian_action"] = action
        cycle["guardian_reason"] = greason
        cycle["critic_passed"] = (action == "pass")

        with open(cyc.dreams_log, "a") as f:
            f.write(json.dumps({
                "id": dream_id, "ts": cycle["ts"], "provenance": "DREAM",
                "mode": "rendered", "sources": cycle["sources"],
                "dream_question": thought["dream_question"],
                "decided_braid": thought["braid"],
                "internal_thought": ren["internal_thought"],
                "narrative": ren["narrative"], "gist": ren["gist"],
                "reconciler": m, "guardian_action": action,
                "guardian_reason": greason}) + "\n")

        cyc._recent_gist_texts.append(ren["gist"])
        cyc._recent_gist_texts = cyc._recent_gist_texts[-5:]

        if action == "hold":
            cycle.update(status="held-by-guardian",
                         duration_s=round(time.time() - t0, 1))
            cyc._log_cycle(cycle)
            return cycle

        labelled = ("DREAM GIST — speculative lesson, NOT an observed "
                    "event: " + ren["gist"])
        verdict, vreason = judge_rule(labelled, cyc.tsc_text)
        cycle["judge_verdict"] = verdict
        cycle["judge_reason"] = vreason
        if verdict == "APPROVED":
            payload = {"verdict": "APPROVED", "content": labelled,
                       "category": "dream_hypothesis", "source": "DREAM",
                       "dream_id": dream_id}
            try:
                cyc.device.write("PSC", payload)
                cycle["imprinted"] = True
            except RingBlocked as e:
                cycle["imprinted"] = False
                cycle["write_refused"] = str(e)
        else:
            cycle["imprinted"] = False
        cycle.update(status="complete",
                     duration_s=round(time.time() - t0, 1))
    except Exception as e:
        cycle.update(status="error", error=str(e)[:200],
                     duration_s=round(time.time() - t0, 1))
    cyc._log_cycle(cycle)
    return cycle


# ---------------------------------------------------------------- runner

def run_mode(mode, n_dreams, corpus):
    os.makedirs(os.path.join(CORPUS_DIR, mode), exist_ok=True)
    psc_path = os.path.join(CORPUS_DIR, mode, "psc.json")
    for p in (psc_path,):
        if os.path.exists(p):
            os.remove(p)  # fresh device per mode — no cross-contamination
    device = SimulatedDevice(persist_path=psc_path)
    log_dir = os.path.join(CORPUS_DIR, mode)
    cyc = CorpusDreamCycle(corpus, backend=None, device=device,
                           log_dir=log_dir, mode="attractor")
    sampled_ids = set()
    imprinted = held = errors = 0
    t_start = time.time()
    for i in range(n_dreams):
        if mode == "mode-a":
            c = cyc.run_one_attractor()
        else:
            c = run_one_rendered(cyc)
        sampled_ids.update(c.get("sources", []))
        if c.get("imprinted"):
            imprinted += 1
        if c.get("status") in ("held-by-guardian", "rejected-by-critic"):
            held += 1
        if c.get("status") == "error":
            errors += 1
        if (i + 1) % 25 == 0:
            print(f"[{mode}] {i + 1}/{n_dreams} dreams, "
                  f"{imprinted} imprinted, {held} held, {errors} errors",
                  flush=True)
    summary = {
        "mode": mode, "dreams": n_dreams, "imprinted": imprinted,
        "held": held, "errors": errors,
        "unique_chunks_sampled": len(sampled_ids),
        "corpus_chunks": len(corpus),
        "coverage": round(len(sampled_ids) / len(corpus), 3),
        "elapsed_s": round(time.time() - t_start, 1),
    }
    with open(os.path.join(log_dir, "summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print(json.dumps(summary, indent=2), flush=True)
    return summary


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    corpus = load_corpus()
    print(f"corpus: {len(corpus)} chunks", flush=True)
    random.seed(20260926)
    a = run_mode("mode-a", n, corpus)
    b = run_mode("mode-b", n, corpus)
    with open(os.path.join(CORPUS_DIR, "experiment-summary.json"), "w") as f:
        json.dump({"mode_a_generated": a, "mode_b_rendered": b}, f, indent=2)


if __name__ == "__main__":
    main()
