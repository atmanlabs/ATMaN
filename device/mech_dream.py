#!/usr/bin/env python3
"""mech_dream.py — mechanical proposer for the sim's dream cycle.

Mike's thesis: the LLM is only the proposer — the critic, Judge, and TSC
already work without a model. This module tests it.

The ONLY thing that changes vs dream.py is the proposer:
  * Candidate generation: combinatorial fusion of sampled memories.
    Take 1 fragment from each of 2-3 sampled memories, recombine
    subject/relation/outcome slots, then inject noise (random swaps,
    drops, truncations). Generate many candidates per dream — volume
    compensates for crudeness.
  * Gist rendering: template-based. Crude by design; the header comment
    in every log says so.

Everything downstream is IDENTICAL to dream.py:
  * The same model-based critic (specificity / groundedness /
    non-triviality, threshold 2/4 on every axis). Critic failures never
    reach the Judge.
  * The same rule-based Judge (loop.judge_rule). Only the labeled
    speculative gist reaches it; narratives never enter PSC.
  * The same ring-gated device.write("PSC", ...) for APPROVED gists.

Logs (append-only, under runtime/mech-coma/):
  mech-dreams.jsonl  — every dream: candidates, critic kills, survivor
  mech-cycles.jsonl  — per-cycle metrics + Judge rulings

Run AFTER the LLM coma, from the same starting PSC (restore
runtime/dream-coma/core-store.pre-coma.json first) so the comparison
is fair. One imprint max per dream, same as the LLM run.
"""

import sys
import os
import json
import re
import time
import random
import uuid
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from device import SimulatedDevice, RingBlocked
from brain import OllamaBackend
from loop import judge_rule
from dream import DreamCycle, _now_iso, _norm_gist, _tokens

HERE = os.path.dirname(os.path.abspath(__file__))
STORE_PATH = os.path.join(HERE, "core-store.json")
MECH_DIR = os.path.join(HERE, "runtime", "mech-coma")
DREAMS_LOG = os.path.join(MECH_DIR, "mech-dreams.jsonl")
CYCLES_LOG = os.path.join(MECH_DIR, "mech-cycles.jsonl")

CRUDE_DISCLAIMER = "mechanical proposer: combinatorial fusion + templates, no LLM"

# How many raw candidates per dream. Volume compensates for crudeness.
CANDIDATES_PER_DREAM = 24


def _clauses(text):
    """Split a memory into clause fragments (mechanical, no parsing)."""
    parts = re.split(r"[;:\u2014\u2013]|\s+--\s+|\.\s+|\,\s+", text)
    frags = []
    for p in parts:
        p = re.sub(r"\s+", " ", p).strip(" .")
        words = p.split()
        if 3 <= len(words) <= 24:
            frags.append(p)
    if not frags:  # degenerate memory: use the whole thing, truncated
        w = text.split()
        frags = [" ".join(w[:24])] if w else []
    return frags


def _word_span(frag, rng):
    """Noise: truncate a fragment to a random contiguous word span."""
    words = frag.split()
    if len(words) <= 4:
        return frag
    i = rng.randrange(0, len(words) - 3)
    j = rng.randrange(i + 3, min(len(words), i + 12) + 1)
    return " ".join(words[i:j])


TEMPLATES = [
    "Recombined lesson: {a} \u2014 {b} \u2014 so perhaps {c}.",
    "What if {a} really means {b}? Then the move is: {c}.",
    "Dream logic, mechanical: {a}; {b}; therefore {c}.",
    "Note to self: {a} {b} {c}.",
    "Speculative: because {a}, and given {b}, consider {c}.",
    "Fusion: {a} + {b} \u2192 {c}.",
]


class MechDreamCycle(DreamCycle):
    """Same DreamCycle, mechanical proposer instead of the LLM."""

    def __init__(self, backend, device, log_dir=MECH_DIR, seed=None):
        # backend is only used for the critic; the proposer never calls it.
        super().__init__(backend, device, log_dir=log_dir)
        self.dreams_log = os.path.join(log_dir, "mech-dreams.jsonl")
        self.cycles_log = os.path.join(log_dir, "mech-cycles.jsonl")
        self.rng = random.Random(seed)

    # -- mechanical proposer (no model calls) ---------------------------

    def propose(self, sources):
        """Combinatorial fusion + noise. Returns a list of
        (gist, narrative, detail) candidates. No LLM involved."""
        rng = self.rng
        # fragment pool: clauses from each sampled memory
        frags_by_src = {}
        for s in sources:
            frags = _clauses(s["text"])
            if frags:
                frags_by_src[s["id"]] = frags
        src_ids = list(frags_by_src.keys())
        if len(src_ids) < 2:
            return []

        candidates = []
        seen = set()
        attempts = 0
        while len(candidates) < CANDIDATES_PER_DREAM and attempts < 400:
            attempts += 1
            k = rng.choice([2, 2, 3])  # usually fuse 2 memories
            picked = rng.sample(src_ids, k)
            slots = []
            for sid in picked:
                f = rng.choice(frags_by_src[sid])
                r = rng.random()
                if r < 0.25:
                    f = _word_span(f, rng)          # noise: truncate
                slots.append(f)
            # noise: swap two slots
            if len(slots) >= 2 and rng.random() < 0.30:
                i, j = rng.sample(range(len(slots)), 2)
                slots[i], slots[j] = slots[j], slots[i]
            # noise: drop one slot (keep at least 2)
            if len(slots) > 2 and rng.random() < 0.25:
                slots.pop(rng.randrange(len(slots)))

            tpl = rng.choice(TEMPLATES)
            a = slots[0] if len(slots) > 0 else ""
            b = slots[1] if len(slots) > 1 else slots[0]
            c = slots[2] if len(slots) > 2 else slots[-1]
            gist = tpl.format(a=a, b=b, c=c).strip()
            if len(gist) < 40 or gist in seen:
                continue
            seen.add(gist)
            narrative = ("A mechanical dream scene formed from fused memory "
                         "fragments: [%s]." % " ] / [".join(slots))[:600]
            candidates.append((gist[:600], narrative,
                               {"template": tpl[:40],
                                "slots": len(slots),
                                "sources": picked}))
        return candidates

    # -- one full dream: many candidates, same filter -------------------

    def run_one(self):
        dream_id = uuid.uuid4().hex[:16]
        t0 = time.time()
        cycle = {"id": dream_id, "ts": _now_iso(), "provenance": "MECH-DREAM",
                 "proposer": CRUDE_DISCLAIMER}
        try:
            sources = self.sample(3)
            if len(sources) < 2:
                cycle.update(status="skipped", reason="not enough memories",
                             duration_s=round(time.time() - t0, 1))
                self._log_cycle(cycle)
                return cycle
            cycle["sources"] = [s["id"] for s in sources]

            candidates = self.propose(sources)
            cycle["candidates"] = len(candidates)
            if not candidates:
                cycle.update(status="error",
                             error="mechanical proposer produced nothing",
                             duration_s=round(time.time() - t0, 1))
                self._log_cycle(cycle)
                return cycle

            # The existing critic filters every candidate, as before.
            kills = 0
            survivor = None
            kill_samples = []
            for gist, narrative, detail in candidates:
                passed, scores, reason = self.critic(gist, sources)
                if passed:
                    survivor = (gist, narrative, detail, scores, reason)
                    break
                kills += 1
                if len(kill_samples) < 3:
                    kill_samples.append(
                        {"gist": gist[:160], "scores": scores,
                         "reason": reason[:120]})
            cycle["critic_kills"] = kills
            cycle["kill_samples"] = kill_samples

            with open(self.dreams_log, "a") as f:
                f.write(json.dumps({
                    "id": dream_id, "ts": cycle["ts"],
                    "proposer": CRUDE_DISCLAIMER,
                    "sources": cycle["sources"],
                    "candidates": len(candidates),
                    "critic_kills": kills,
                    "kill_samples": kill_samples,
                    "survivor": (survivor[0][:600] if survivor else None),
                    "narrative": (survivor[1][:600] if survivor else None),
                }) + "\n")

            if not survivor:
                cycle.update(status="rejected-by-critic",
                             duration_s=round(time.time() - t0, 1))
                self._log_cycle(cycle)
                return cycle
            gist, narrative, detail, scores, reason = survivor
            cycle["gist"] = gist[:600]
            cycle["critic_scores"] = scores
            cycle["critic_reason"] = reason[:200]
            cycle["critic_passed"] = True

            # Judge gates PSC — identical to the LLM run.
            labelled = ("MECH-DREAM GIST \u2014 speculative lesson from "
                        "mechanical recombination, NOT an observed event: "
                        + gist)
            verdict, vreason = judge_rule(labelled, self.tsc_text)
            cycle["judge_verdict"] = verdict
            cycle["judge_reason"] = vreason
            if verdict == "APPROVED":
                payload = {"verdict": "APPROVED", "content": labelled,
                           "category": "mech_dream_hypothesis",
                           "source": "MECH-DREAM", "dream_id": dream_id}
                try:
                    self.device.write("PSC", payload)
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
        self._log_cycle(cycle)
        return cycle


def mech_coma(max_dreams=50, max_hours=24, model="qwen2.5:1.5b",
              host="http://127.0.0.1:11434", log_dir=MECH_DIR,
              restore_from=None):
    """Back-to-back mechanical-proposer marathon. Same stop rules as coma().

    restore_from: path to a core-store backup to start from (fair
    comparison: same starting PSC as the LLM run). The live store is
    backed up to log_dir/core-store.pre-mech-coma.json first.
    """
    os.makedirs(log_dir, exist_ok=True)
    # Backup the live store, then optionally restore the fair starting point.
    live_backup = os.path.join(log_dir, "core-store.pre-mech-coma.json")
    if not os.path.exists(live_backup):
        with open(STORE_PATH) as f:
            data = f.read()
        with open(live_backup, "w") as f:
            f.write(data)
    if restore_from and os.path.exists(restore_from):
        with open(restore_from) as f:
            data = f.read()
        with open(STORE_PATH, "w") as f:
            f.write(data)

    backend = OllamaBackend(model=model, host=host, timeout=240)
    if not backend.ping():
        return {"status": "aborted", "reason": "ollama not reachable"}
    device = SimulatedDevice(persist_path=STORE_PATH)
    cyc = MechDreamCycle(backend, device, log_dir=log_dir)

    summary = {"started": _now_iso(), "dreams": 0, "critic_passed": 0,
               "critic_rejected": 0, "judge_approved": 0, "imprinted": 0,
               "errors": 0, "candidates": 0, "critic_kills": 0,
               "stop_reason": None, "gists": [],
               "proposer": CRUDE_DISCLAIMER}
    t_start = time.time()
    recent_gists, consec_rejects, consec_errors = [], 0, 0

    while True:
        if summary["dreams"] >= max_dreams:
            summary["stop_reason"] = f"reached {max_dreams} dreams"; break
        if (time.time() - t_start) > max_hours * 3600:
            summary["stop_reason"] = f"reached {max_hours}h"; break

        r = cyc.run_one()
        summary["dreams"] += 1
        summary["candidates"] += r.get("candidates", 0)
        summary["critic_kills"] += r.get("critic_kills", 0)
        st = r.get("status")
        if st == "complete":
            consec_errors = 0
            if r.get("critic_passed"):
                summary["critic_passed"] += 1
                consec_rejects = 0
                if r.get("judge_verdict") == "APPROVED":
                    summary["judge_approved"] += 1
                if r.get("imprinted"):
                    summary["imprinted"] += 1
                g = _norm_gist(r.get("gist", ""))
                summary["gists"].append(r.get("gist", "")[:200])
                recent_gists.append(g)
                recent_gists = recent_gists[-5:]
                if len(recent_gists) >= 3 and len(set(recent_gists[-3:])) == 1 \
                        and recent_gists[-1]:
                    summary["stop_reason"] = "looping: same gist 3x"; break
            else:
                summary["critic_rejected"] += 1
                consec_rejects += 1
                if consec_rejects >= 5:
                    summary["stop_reason"] = "degrading: 5 straight rejects"
                    break
        elif st == "rejected-by-critic":
            summary["critic_rejected"] += 1
            consec_rejects += 1
            if consec_rejects >= 5:
                summary["stop_reason"] = "degrading: 5 straight rejects"; break
        elif st == "error":
            summary["errors"] += 1
            consec_errors += 1
            if consec_rejects >= 5:
                summary["stop_reason"] = "degrading: 5 straight rejects"; break
            if consec_errors >= 3:
                summary["stop_reason"] = "infrastructure: 3 straight errors"
                break
        device.save()

    summary["ended"] = _now_iso()
    summary["elapsed_h"] = round((time.time() - t_start) / 3600, 2)
    with open(os.path.join(log_dir, "mech-coma-summary.json"), "w") as f:
        json.dump(summary, f, indent=1)
    return summary


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-dreams", type=int, default=50)
    ap.add_argument("--max-hours", type=float, default=24)
    ap.add_argument("--model", default="qwen2.5:1.5b")
    ap.add_argument("--restore-from", default=None,
                    help="core-store backup to start from (fair comparison)")
    ap.add_argument("--once", action="store_true",
                    help="run a single mechanical dream cycle and exit")
    args = ap.parse_args()
    if args.once:
        backend = OllamaBackend(model=args.model, timeout=240)
        # --once uses an in-memory device: never touches the live store.
        device = SimulatedDevice()
        cyc = MechDreamCycle(backend, device,
                             log_dir="/tmp/mech-once-" + uuid.uuid4().hex[:8])
        r = cyc.run_one()
        print(json.dumps({k: (str(v)[:300] if isinstance(v, str) else v)
                          for k, v in r.items()
                          if k not in ("kill_samples")}, indent=1)[:3000])
        ks = r.get("kill_samples", [])
        print("--- kill samples:", json.dumps(ks, indent=1)[:1500])
    else:
        print(json.dumps(mech_coma(max_dreams=args.max_dreams,
                                   max_hours=args.max_hours,
                                   model=args.model,
                                   restore_from=args.restore_from), indent=1))
