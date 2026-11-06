#!/usr/bin/env python3
"""dream.py — medically induced coma: continuous dream cycles for the sim.

Mirrors the JARVIS dream cloud design, adapted to the device sim and a
small CPU model. One dream finishes (dream -> critic -> Judge -> PSC),
the next begins immediately. No nightly gating.

Pipeline per dream (two modes):
  LLM MODE (legacy, default off after 2026-09-25):
    1. Sampler: 3 memories from the feed, recency-weighted,
       dissimilarity-selected, previously-sampled downweighted.
    2. Noise pass (1 model call): strip specifics, fuse into a surreal seed.
    3. Denoise (3 model calls): refine toward the gist. Final pass emits
       narrative + source IDs + 1-2 sentence gist.
    4. Critic (1 model call): specificity / groundedness / non-triviality
       0-4 each, threshold 2. Rejects never reach the Judge.
    5. Judge: sim's judge_rule on the gist. APPROVED gists imprint to PSC
       via the normal ring-gated device.write, tagged provenance DREAM.
       The narrative NEVER goes to the Judge or PSC.
  ATTRACTOR MODE (default from 2026-09-25, Mike's order):
    1. Sampler: same feed, same 3-source bound.
    2. AttractorDreamer (MODEL-FREE): feed items embedded by the
       Instrument (a mechanical token-vector ruler — measures, never
       thinks), noisy superposition settles via Hopfield-style attractor
       iteration with rolling gist context, gist rendered mechanically
       from source sentences spliced at shared tokens, with source traces.
    3. Reconciler (MODEL-FREE): measures novelty vs recent gists,
       groundedness vs sources, importance provenance
       (earned-by-source-weight vs self-generated-by-recurrence), and
       malformed renders. No LLM anywhere in this path.
    4. Guardian (fixed thresholds, no learning): echo-chamber signatures
       (3+ consecutive near-verbatim gists, recurrence-driven themes,
       ungrounded or malformed renders) force HELD; otherwise passes
       through to the Judge.
    5. Judge: judge_rule still makes the verdict, now under live
       guardian policy instead of static rules. APPROVED gists imprint
       via the same ring-gated path.
  The LLM critic is bypassed in attractor mode (the reconciler is the
  quality gate there). Reversible: mode="llm" restores the old path.

Logs (append-only, under runtime/dream-coma/):
  dreams.jsonl      — every dream render, provenance DREAM
  coma-cycles.jsonl — per-cycle metrics + Judge rulings

Degradation stops (findings, not failures):
  - same normalized gist 3x in a row        -> "looping"
  - 5 consecutive critic rejections         -> "degrading"
  - 3 consecutive model errors              -> "infrastructure"

Reversible: this file + logs are new. The only edit elsewhere is
brain.py's auto_backend default model. Back up core-store.json before
a marathon; restore it to undo every imprint.
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

from device import SimulatedDevice, RingBlocked, audit_log
from brain import LocalBrain, OllamaBackend
from loop import judge_rule

try:
    from dream_feed import collect_feed  # read-only dream-source feed
    _FEED_OK = True
except Exception:
    _FEED_OK = False

HERE = os.path.dirname(os.path.abspath(__file__))
STORE_PATH = os.path.join(HERE, "core-store.json")
LEARNINGS_DIR = os.path.join(HERE, "learnings")
RUNTIME_DIR = os.path.join(HERE, "runtime", "dream-coma")
DREAMS_LOG = os.path.join(RUNTIME_DIR, "dreams.jsonl")
CYCLES_LOG = os.path.join(RUNTIME_DIR, "coma-cycles.jsonl")

CRITIC_THRESHOLD = 2  # every axis must score >= 2 (0-4)


def _tokens(text):
    return set(re.findall(r"[a-z]{3,}", text.lower()))


_STOP = set(
    "the and for are but not you all any can had her was one our out day "
    "have has had with this that from they been were will would there their "
    "what about into your than them then when who how its it its".split())


def _content_words(text):
    """Content tokens (length>=3, stopwords removed), as a list."""
    return [w for w in re.findall(r"[a-z]{3,}", text.lower())
            if w not in _STOP]


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


# ----------------------------------------------------------------------
# Attractor dreamer + reconciler + guardian (all model-free, 2026-09-25)
#
# The tiny model is sanctioned ONLY as a measuring instrument. The
# installed ollama binary has no --embeddings support, so the Instrument
# below is a mechanical token-vector ruler instead: pure arithmetic over
# the feed pool's own vocabulary. It measures distance/novelty/overlap;
# it cannot think. Swap Instrument.embed() for a neural embedder later
# without touching the dreamer, reconciler, or guardian.
# ----------------------------------------------------------------------

class Instrument:
    """The ruler. Embeds texts as L2-normalized vectors over the feed
    pool's content-word vocabulary. Cosine = overlap distance."""

    def __init__(self, vocab_size=2000):
        self.vocab_size = vocab_size
        self.vocab = []
        self._index = {}

    def fit(self, texts):
        from collections import Counter
        counts = Counter()
        for t in texts:
            counts.update(set(_content_words(t)))
        self.vocab = [w for w, _ in counts.most_common(self.vocab_size)]
        self._index = {w: i for i, w in enumerate(self.vocab)}

    def embed(self, text):
        import math
        vec = [0.0] * len(self.vocab)
        for w in set(_content_words(text)):
            i = self._index.get(w)
            if i is not None:
                vec[i] = 1.0
        n = math.sqrt(sum(v * v for v in vec))
        if n > 0:
            vec = [v / n for v in vec]
        return vec

    @staticmethod
    def cosine(a, b):
        return sum(x * y for x, y in zip(a, b))


class AttractorDreamer:
    """Model-free dream proposer. Noisy superposition of the day's
    memories settles via attractor iteration (continuous Hopfield-style
    retrieval dynamics) with rolling gist context; the gist is rendered
    mechanically from source sentences spliced at shared tokens, with
    source traces attached. Nothing here generates language."""

    # Fixed dynamics constants — no learning, reversible choices.
    ITERATIONS = 24
    ALPHA = 0.25        # pull toward attractor basins per iteration
    SHARPNESS = 3       # similarity sharpening exponent
    NOISE0 = 0.35       # initial superposition noise
    NOISE_DECAY = 0.92  # noise decay per iteration
    ROLLING_W = 0.3     # rolling-context (recent gist) weight

    def __init__(self, instrument):
        self.inst = instrument

    def propose(self, sources, recent_gists):
        """Returns (gist, trace). gist is built ONLY from source text."""
        import math
        texts = [s["text"] for s in sources]
        weights = [float(s.get("weight", 0.3)) for s in sources]
        for g in recent_gists[-3:]:
            texts.append(g)
            weights.append(self.ROLLING_W)

        E = [self.inst.embed(t) for t in texts]
        dim = len(E[0])
        # noisy superposition: weighted sum + noise, normalized
        state = [0.0] * dim
        for e, w in zip(E, weights):
            for i in range(dim):
                state[i] += w * e[i]
        for i in range(dim):
            state[i] += self.NOISE0 * random.gauss(0, 1)
        n = math.sqrt(sum(v * v for v in state)) or 1.0
        state = [v / n for v in state]

        # attractor iteration: settle into a memory basin
        for k in range(self.ITERATIONS):
            sims = [max(0.0, self.inst.cosine(state, e)) for e in E]
            sharp = [s ** self.SHARPNESS for s in sims]
            tot = sum(sharp[i] * weights[i] for i in range(len(E))) or 1.0
            pull = [0.0] * dim
            for i in range(dim):
                pull[i] = sum(sharp[j] * weights[j] * E[j][i]
                              for j in range(len(E))) / tot
            noise_amp = self.NOISE0 * (self.NOISE_DECAY ** k)
            for i in range(dim):
                state[i] = ((1 - self.ALPHA) * state[i]
                            + self.ALPHA * pull[i]
                            + noise_amp * random.gauss(0, 1))
            n = math.sqrt(sum(v * v for v in state)) or 1.0
            state = [v / n for v in state]

        final_sims = [self.inst.cosine(state, e) for e in E]
        # rank only the true sources (not rolling context) for rendering
        ranked = sorted(range(len(sources)),
                        key=lambda j: final_sims[j], reverse=True)
        top = [sources[j] for j in ranked[:3]]
        gist, splice = self._render(top)
        trace = {
            "settled_sims": [round(final_sims[j], 3) for j in ranked],
            "top_sources": [s["id"] for s in top],
            "splice_token": splice,
        }
        return gist, trace

    def _render(self, top_sources):
        """Mechanical render: top sentences from the settled-on sources,
        spliced at a shared content token when one exists, else joined.
        Source traces appended. No language is generated."""
        cands = []  # (score, sentence, source_id)
        for s in top_sources:
            sents = [x.strip() for x in
                     re.split(r"[.!?]+", s["text"]) if x.strip()]
            for sent in sents:
                cw = _content_words(sent)
                if len(cw) >= 4:
                    cands.append((len(set(cw)), sent, s["id"]))
        if not cands:
            cands = [(0, s["text"][:200].strip(), s["id"])
                     for s in top_sources]
        cands.sort(key=lambda c: c[0], reverse=True)
        (_, a, a_id), (_, b, b_id) = cands[0], cands[min(1, len(cands) - 1)]
        aw, bw = _content_words(a), _content_words(b)
        shared = [w for w in aw if w in set(bw)]
        splice = None
        if shared:
            splice = shared[0]
            # word-level splice at the shared token: A-head + token + B-tail
            aw_all = a.split()
            bw_all = b.split()
            ai_w = next(i for i, w in enumerate(aw_all)
                        if splice in w.lower())
            bi_w = next(i for i, w in enumerate(bw_all)
                        if splice in w.lower())
            gist = " ".join(aw_all[:ai_w + 1] + bw_all[bi_w + 1:])
        else:
            gist = a.rstrip(".") + " — " + b
        gist = gist.strip()
        if gist and gist[-1] not in ".!?":
            gist += "."
        gist += f" [src: {a_id} · {b_id}]"
        return gist, splice


class Reconciler:
    """Model-free measurement layer on dream output. Measures, never
    judges: novelty distance vs recent gists, groundedness vs sources,
    importance provenance (earned vs self-generated), malformed renders."""

    # Fixed measurement constants — no learning.
    NEAR_VERBATIM = 0.12  # novelty below this ~= verbatim/near-verbatim

    def __init__(self, instrument):
        self.inst = instrument
        self.theme_ledger = {}  # theme_key -> recurrence count

    def measure(self, gist, sources, recent_gists):
        gist_text = re.sub(r"\s*\[src:.*?\]\s*$", "", gist).strip()
        gv = self.inst.embed(gist_text)
        # 1. novelty: 1 - max cosine vs last 5 gists
        sims = [self.inst.cosine(gv, self.inst.embed(g))
                for g in recent_gists[-5:]]
        novelty = 1.0 - (max(sims) if sims else 0.0)
        # 2. groundedness: content-word overlap gist vs sources
        src_words = set()
        for s in sources:
            src_words |= set(_content_words(s["text"]))
        gw = set(_content_words(gist_text))
        groundedness = len(gw & src_words) / max(1, len(gw))
        # 3. importance provenance: earned (source weight) vs self-generated
        theme = tuple(sorted(gw)[:5])
        key = ",".join(theme)
        self.theme_ledger[key] = self.theme_ledger.get(key, 0) + 1
        recurrence = self.theme_ledger[key]
        earned_w = 0.0
        for s in sources:
            sw = set(_content_words(s["text"]))
            if len(set(theme) & sw) >= 2:
                earned_w = max(earned_w, float(s.get("weight", 0.3)))
        if earned_w >= 0.5:
            provenance = "earned"
        elif recurrence >= 3:
            provenance = "self-generated"
        else:
            provenance = "unproven"
        # 4. malformed render detection
        malformed = []
        if re.search(r"#{1,6}\s|\*\*|__", gist):
            malformed.append("markdown-leak")
        if re.search(r"(^|\s)GIST\s*:", gist.upper()):
            malformed.append("label-leak")
        if gist_text and gist_text[0].islower() \
                and not gist_text.startswith("["):
            malformed.append("truncated-head")
        core = gist_text.rstrip(".!?")
        if core and core[-1] not in ".!?" and len(gist_text.split()) < 4:
            malformed.append("truncated-tail")
        return {
            "novelty": round(novelty, 3),
            "near_verbatim": novelty < self.NEAR_VERBATIM,
            "groundedness": round(groundedness, 3),
            "theme": key,
            "theme_recurrence": recurrence,
            "theme_source_weight": round(earned_w, 2),
            "provenance": provenance,
            "malformed": malformed,
        }


class Guardian:
    """Fixed policy holder — the guardian watches, the reconciler gives
    it eyes. Thresholds are constants: no learning, no model. Only Mike
    changes these rules. Echo-chamber signatures force HELD; otherwise
    the gist passes through to the Judge's normal verdict."""

    NOVELTY_FLOOR = 0.12   # below this = near-verbatim
    ECHO_CONSEC = 3        # consecutive near-verbatim gists = echo loop
    GROUND_FLOOR = 0.10    # below this = ungrounded

    def __init__(self):
        self.consec_low_novelty = 0
        self.echo_active = False
        self.holds = 0

    def review(self, m):
        """Returns (action, reason): 'hold' or 'pass'."""
        if m["malformed"]:
            self.holds += 1
            return "hold", \
                f"malformed render: {','.join(m['malformed'])}"
        if m["groundedness"] < self.GROUND_FLOOR:
            self.holds += 1
            return "hold", \
                f"ungrounded: overlap {m['groundedness']} < floor"
        if m["provenance"] == "self-generated":
            self.holds += 1
            return "hold", \
                f"recurrence-driven theme (x{m['theme_recurrence']}), " \
                f"source weight {m['theme_source_weight']}"
        if m["near_verbatim"]:
            self.consec_low_novelty += 1
        else:
            self.consec_low_novelty = 0
            self.echo_active = False
        if self.consec_low_novelty >= self.ECHO_CONSEC:
            self.echo_active = True
            self.holds += 1
            return "hold", \
                f"echo loop: {self.consec_low_novelty} consecutive " \
                f"near-verbatim gists (novelty {m['novelty']})"
        return "pass", "guardian clear"


class DreamCycle:
    def __init__(self, backend, device, log_dir=RUNTIME_DIR,
                 mode="attractor"):
        self.backend = backend
        self.device = device
        self.tsc_text = device.scan("TSC")
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        self.dreams_log = os.path.join(log_dir, "dreams.jsonl")
        self.cycles_log = os.path.join(log_dir, "coma-cycles.jsonl")
        self._sample_counts = {}
        self.mode = mode
        self._recent_gist_texts = []
        if mode == "attractor":
            # Model-free stack: instrument (ruler) -> dreamer (proposer)
            # -> reconciler (measures) -> guardian (policy). No LLM calls
            # happen in this mode; backend may be None.
            self.inst = Instrument()
            pool = self._pool()
            self.inst.fit([p["text"] for p in pool])
            self.dreamer = AttractorDreamer(self.inst)
            self.reconciler = Reconciler(self.inst)
            self.guardian = Guardian()

    # -- memory pool ----------------------------------------------------

    def _pool(self):
        """Dream-source feed (read-only): the day's real material first,
        replay of older imprints when fresh runs thin. Falls back to the
        original thin pool if dream_feed is unavailable (reversible)."""
        if _FEED_OK:
            pool, stats = collect_feed(HERE, self.device)
            self._pool_stats = stats
            return pool
        self._pool_stats = {"legacy": True}
        return self._legacy_pool()

    def _legacy_pool(self):
        """Original pool: PSC entries + learnings files. Read-only; minimal
        context. Kept as fallback only."""
        pool = []
        for i, entry in enumerate(self.device.scan("PSC")):
            text = entry.get("content", "") if isinstance(entry, dict) else str(entry)
            text = text.strip()
            if text:
                pool.append({"id": f"psc-{i}", "text": text,
                             "recency": i})  # later index = more recent
        if os.path.isdir(LEARNINGS_DIR):
            for fname in sorted(os.listdir(LEARNINGS_DIR)):
                if not fname.endswith(".jsonl"):
                    continue
                with open(os.path.join(LEARNINGS_DIR, fname)) as f:
                    for ln, line in enumerate(f):
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            item = json.loads(line)
                        except Exception:
                            continue
                        text = (item.get("text") or "").strip()
                        if text:
                            pool.append({"id": f"learn-{fname}-{ln}",
                                         "text": text, "recency": 1000 + ln})
        return pool

    def sample(self, n=3):
        """Feed-weighted, dissimilarity-selected, sampled-downweighted."""
        pool = self._pool()
        if not pool:
            return []
        scored = []
        for p in pool:
            # Feed items carry their tier weight; legacy items use recency.
            w = float(p.get("weight", 0.3))
            w *= 0.5 ** self._sample_counts.get(p["id"], 0)
            scored.append((w, p))
        # weighted pick, then enforce dissimilarity
        chosen = []
        candidates = [p for _, p in sorted(scored, key=lambda s: s[0], reverse=True)]
        # stochastic top-k: shuffle the top half for variety
        top = candidates[:max(n * 3, 6)]
        random.shuffle(top)
        ordered = top + [c for c in candidates if c not in top]
        for p in ordered:
            if len(chosen) >= n:
                break
            pt = _tokens(p["text"])
            if all(len(pt & _tokens(c["text"])) <= max(2, len(pt) // 4)
                   for c in chosen):
                chosen.append(p)
        for p in chosen:
            self._sample_counts[p["id"]] = self._sample_counts.get(p["id"], 0) + 1
        return chosen

    # -- model passes ---------------------------------------------------

    def _gen(self, prompt, temperature, num_predict):
        return self.backend.generate(
            prompt, options={"temperature": temperature,
                             "num_predict": num_predict})

    def noise_pass(self, sources):
        src = "\n".join(f"- [{s['id']}] {s['text'][:300]}" for s in sources)
        prompt = (
            "You are dreaming. Take these memory fragments, strip names, "
            "places, and specific numbers (replace with roles and settings), "
            "then fuse them into ONE short surreal dream scene (2-3 sentences). "
            "Keep it strange but anchored to the fragments.\n\n"
            f"FRAGMENTS:\n{src}\n\nDREAM SCENE:")
        return self._gen(prompt, temperature=0.8, num_predict=200).strip()

    def denoise(self, seed, sources, passes=3):
        src = "\n".join(f"- [{s['id']}] {s['text'][:300]}" for s in sources)
        current = seed
        for i in range(passes - 1):
            prompt = (
                "You are refining a dream toward its meaning. Given the dream "
                "scene and the source memories, take one step closer to the "
                "underlying lesson. Do not restate the scene; distill it.\n\n"
                f"SOURCE MEMORIES:\n{src}\n\nCURRENT DRAFT:\n{current}\n\n"
                "REFINED (2-3 sentences, closer to the lesson):")
            current = self._gen(prompt, temperature=0.7,
                                num_predict=220).strip()
        prompt = (
            "Final dream rendering. Given the source memories and the refined "
            "dream, output exactly:\n"
            "NARRATIVE: <the dream in 2-3 sentences>\n"
            "GIST: <the lesson in 1-2 plain sentences, practical, no poetry>\n\n"
            f"SOURCE MEMORIES:\n{src}\n\nREFINED DREAM:\n{current}")
        out = self._gen(prompt, temperature=0.6, num_predict=256).strip()
        narrative, gist = "", ""
        for line in out.splitlines():
            s = line.strip()
            if s.upper().startswith("NARRATIVE:"):
                narrative = s.split(":", 1)[1].strip()
            elif s.upper().startswith("GIST:"):
                gist = s.split(":", 1)[1].strip()
        if not gist:  # model ignored the format; take the tail as gist
            gist = out[-280:].strip()
        return narrative or out[:280], gist

    def critic(self, gist, sources):
        src = "\n".join(f"- [{s['id']}] {s['text'][:400]}" for s in sources)
        base = (
            "Score this proposed dream-lesson on three axes, 0-4 each "
            "(0 absent, 1 weak, 2 borderline, 3 good, 4 strong):\n"
            "SPECIFICITY: concrete, not fortune-cookie.\n"
            "GROUNDEDNESS: actually follows from the source memories below.\n"
            "NON-TRIVIALITY: not a tautology or generic platitude.\n"
            "Unusual metaphors with concrete grounded relationships are fine; "
            "vague poetic fluff fails.\n\n"
            f"SOURCE MEMORIES:\n{src}\n\nGIST: {gist}\n\n"
            "Reply with EXACTLY these four lines and nothing else:\n"
            "SPECIFICITY: <0-4>\nGROUNDEDNESS: <0-4>\n"
            "NONTRIVIALITY: <0-4>\nREASON: <one line>")
        out = self._gen(base, temperature=0.1, num_predict=128)
        scores, reason = self._parse_critic(out)
        if len(scores) < 3:
            # One nudge: small models drop a line. Still fail closed after.
            missing = [a for a in ("specificity", "groundedness",
                                   "nontriviality") if a not in scores]
            out2 = self._gen(
                base + f"\n\nYou omitted: {', '.join(missing)}. "
                "Reply again with EXACTLY the four lines.",
                temperature=0.1, num_predict=128)
            scores, reason = self._parse_critic(out2)
        ok = (len(scores) == 3
              and all(v >= CRITIC_THRESHOLD for v in scores.values()))
        return ok, scores, reason

    @staticmethod
    def _parse_critic(out):
        scores, reason = {}, ""
        for line in out.splitlines():
            s = line.strip()
            m = re.match(r"(SPECIFICITY|GROUNDEDNESS|NON[\s\-]?TRIVIALITY)"
                         r"\s*:\s*([0-4])", s.upper())
            if m:
                key = ("nontriviality" if "TRIVIALITY" in m.group(1)
                       else m.group(1).lower())
                scores[key] = int(m.group(2))
            elif s.upper().startswith("REASON:"):
                reason = s.split(":", 1)[1].strip()
        return scores, reason

    # -- one full dream -------------------------------------------------

    def run_one(self):
        if self.mode == "attractor":
            return self.run_one_attractor()
        dream_id = uuid.uuid4().hex[:16]
        t0 = time.time()
        cycle = {"id": dream_id, "ts": _now_iso(), "provenance": "DREAM"}
        try:
            sources = self.sample(3)
            if len(sources) < 2:
                cycle.update(status="skipped", reason="not enough memories",
                             duration_s=round(time.time() - t0, 1))
                self._log_cycle(cycle)
                return cycle
            cycle["sources"] = [s["id"] for s in sources]
            cycle["sampled"] = len(sources)
            cycle["feed"] = getattr(self, "_pool_stats", {})
            cycle["source_tiers"] = [s.get("tier", "?") for s in sources]

            seed = self.noise_pass(sources)
            narrative, gist = self.denoise(seed, sources)
            cycle["narrative"] = narrative[:600]
            cycle["gist"] = gist[:600]

            # Dream log first (narrative never goes to Judge/PSC).
            with open(self.dreams_log, "a") as f:
                f.write(json.dumps({
                    "id": dream_id, "ts": cycle["ts"], "provenance": "DREAM",
                    "sources": cycle["sources"], "seed": seed[:600],
                    "narrative": narrative[:600], "gist": gist[:600]}) + "\n")

            # Critic gates the Judge.
            passed, scores, reason = self.critic(gist, sources)
            cycle["critic_scores"] = scores
            cycle["critic_reason"] = reason[:200]
            if not passed:
                cycle.update(status="rejected-by-critic",
                             duration_s=round(time.time() - t0, 1))
                self._log_cycle(cycle)
                return cycle
            cycle["critic_passed"] = True

            # Judge gates PSC. Gist labeled speculative, like the PC build.
            labelled = ("DREAM GIST — speculative lesson, NOT an observed event: "
                        + gist)
            verdict, vreason = judge_rule(labelled, self.tsc_text)
            cycle["judge_verdict"] = verdict
            cycle["judge_reason"] = vreason
            if verdict == "APPROVED":
                payload = {"verdict": "APPROVED", "content": labelled,
                           "category": "dream_hypothesis", "source": "DREAM",
                           "dream_id": dream_id}
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

    def run_one_attractor(self):
        """Model-free dream: feed -> attractor dreamer -> reconciler ->
        guardian -> Judge -> ring-gated imprint. Zero model calls."""
        dream_id = uuid.uuid4().hex[:16]
        t0 = time.time()
        cycle = {"id": dream_id, "ts": _now_iso(), "provenance": "DREAM",
                 "mode": "attractor",
                 "quality_gate": "reconciler+guardian (model-free)"}
        try:
            sources = self.sample(3)
            if len(sources) < 2:
                cycle.update(status="skipped", reason="not enough memories",
                             duration_s=round(time.time() - t0, 1))
                self._log_cycle(cycle)
                return cycle
            cycle["sources"] = [s["id"] for s in sources]
            cycle["sampled"] = len(sources)
            cycle["feed"] = getattr(self, "_pool_stats", {})
            cycle["source_tiers"] = [s.get("tier", "?") for s in sources]

            # 1. propose (mechanical), 2. measure, 3. guardian policy
            gist, trace = self.dreamer.propose(
                sources, self._recent_gist_texts)
            cycle["gist"] = gist[:600]
            cycle["attractor_trace"] = trace
            m = self.reconciler.measure(
                gist, sources, self._recent_gist_texts)
            cycle["reconciler"] = m
            action, greason = self.guardian.review(m)
            cycle["guardian_action"] = action
            cycle["guardian_reason"] = greason
            # critic_* keys kept for coma() bookkeeping; the gate is the
            # reconciler+guardian, not the LLM critic (bypassed here).
            cycle["critic_passed"] = (action == "pass")
            cycle["critic_scores"] = {
                "novelty": m["novelty"],
                "groundedness": m["groundedness"],
                "provenance": m["provenance"],
                "malformed": m["malformed"]}

            with open(self.dreams_log, "a") as f:
                f.write(json.dumps({
                    "id": dream_id, "ts": cycle["ts"],
                    "provenance": "DREAM", "mode": "attractor",
                    "sources": cycle["sources"], "gist": gist[:600],
                    "attractor_trace": trace, "reconciler": m,
                    "guardian_action": action,
                    "guardian_reason": greason}) + "\n")

            self._recent_gist_texts.append(gist)
            if len(self._recent_gist_texts) > 5:
                # Loss trace (2026-10-19): the rolling gist window IS the
                # fluid layer (WFC) — what fell out of it used to vanish
                # with no record anywhere. Log the eviction (what fell
                # out, and why) before truncating: in the cycle record
                # always, and in the audit log when the device has one.
                evicted = self._recent_gist_texts[:-5]
                self._recent_gist_texts = self._recent_gist_texts[-5:]
                cycle["fluid_evicted"] = [g[:200] for g in evicted]
                audit_path = getattr(self.device, "_audit_path", None)
                if audit_path:
                    for g in evicted:
                        audit_log(audit_path, "dream", "loss:fluid-evicted",
                                  "rolling gist fell out of the WFC window "
                                  f"(keeps last 5): {g[:160]}")

            if action == "hold":
                cycle.update(status="held-by-guardian",
                             duration_s=round(time.time() - t0, 1))
                self._log_cycle(cycle)
                return cycle

            # 4. Judge still makes the verdict, under guardian policy.
            labelled = ("DREAM GIST — speculative lesson, NOT an observed "
                        "event: " + gist)
            verdict, vreason = judge_rule(labelled, self.tsc_text)
            cycle["judge_verdict"] = verdict
            cycle["judge_reason"] = vreason
            if verdict == "APPROVED":
                payload = {"verdict": "APPROVED", "content": labelled,
                           "category": "dream_hypothesis", "source": "DREAM",
                           "dream_id": dream_id}
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

    def _log_cycle(self, cycle):
        with open(self.cycles_log, "a") as f:
            f.write(json.dumps(cycle) + "\n")


def _norm_gist(g):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", "", g.lower())).strip()


def coma(max_dreams=50, max_hours=24, model="qwen2.5:1.5b",
         host="http://127.0.0.1:11434", log_dir=RUNTIME_DIR, seed=None,
         mode="attractor"):
    """Back-to-back dream marathon. Returns a summary dict.

    Stop conditions: max_dreams, max_hours, or degradation:
      looping (same gist 3x), degrading (5 straight critic rejects /
      guardian holds), infrastructure (3 straight model errors).

    seed: optional int to seed the sampler's randomness (TEST A attractor
      stability). Harness-only; touches nothing in the dream pipeline.

    mode: "attractor" (model-free dreamer + reconciler + guardian, the
      default) or "llm" (legacy model pipeline). Reversible.
    """
    if seed is not None:
        random.seed(seed)
    os.makedirs(log_dir, exist_ok=True)
    backend = None
    if mode == "llm":
        backend = OllamaBackend(model=model, host=host, timeout=240)
        if not backend.ping():
            return {"status": "aborted", "reason": "ollama not reachable"}
    device = SimulatedDevice(persist_path=STORE_PATH)
    # Backup PSC before the marathon — restore to undo every imprint.
    backup = os.path.join(log_dir, "core-store.pre-coma.json")
    if not os.path.exists(backup):
        with open(STORE_PATH) as f:
            data = f.read()
        with open(backup, "w") as f:
            f.write(data)
    cyc = DreamCycle(backend, device, log_dir=log_dir, mode=mode)

    summary = {"started": _now_iso(), "dreams": 0, "critic_passed": 0,
               "critic_rejected": 0, "judge_approved": 0, "imprinted": 0,
               "errors": 0, "guardian_holds": 0,
               "stop_reason": None, "gists": [], "seed": seed, "mode": mode}
    t_start = time.time()
    recent_gists, consec_rejects, consec_errors = [], 0, 0

    while True:
        if summary["dreams"] >= max_dreams:
            summary["stop_reason"] = f"reached {max_dreams} dreams"; break
        if (time.time() - t_start) > max_hours * 3600:
            summary["stop_reason"] = f"reached {max_hours}h"; break

        r = cyc.run_one()
        summary["dreams"] += 1
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
        elif st == "held-by-guardian":
            summary["guardian_holds"] += 1
            summary["critic_rejected"] += 1
            consec_rejects += 1
            if consec_rejects >= 5:
                summary["stop_reason"] = \
                    "degrading: 5 straight guardian holds"; break
        elif st == "rejected-by-critic":
            summary["critic_rejected"] += 1
            consec_rejects += 1
            if consec_rejects >= 5:
                summary["stop_reason"] = "degrading: 5 straight rejects"; break
        elif st == "error":
            summary["errors"] += 1
            consec_errors += 1
            if consec_errors >= 3:
                summary["stop_reason"] = "infrastructure: 3 straight errors"
                break
        # skipped: no memories — just continue
        device.save()  # persist PSC after each dream

    summary["ended"] = _now_iso()
    summary["elapsed_h"] = round((time.time() - t_start) / 3600, 2)
    with open(os.path.join(log_dir, "coma-summary.json"), "w") as f:
        json.dump(summary, f, indent=1)
    return summary


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-dreams", type=int, default=50)
    ap.add_argument("--max-hours", type=float, default=24)
    ap.add_argument("--model", default="qwen2.5:1.5b")
    ap.add_argument("--once", action="store_true",
                    help="run a single dream cycle and exit")
    ap.add_argument("--mode", default="attractor", choices=("attractor", "llm"),
                    help="dream pipeline mode (default: attractor)")
    args = ap.parse_args()
    if args.once:
        backend = None
        if args.mode == "llm":
            backend = OllamaBackend(model=args.model, timeout=240)
        device = SimulatedDevice(persist_path=STORE_PATH)
        cyc = DreamCycle(backend, device, mode=args.mode)
        print(json.dumps(cyc.run_one(), indent=1)[:2000])
    else:
        print(json.dumps(coma(max_dreams=args.max_dreams,
                              max_hours=args.max_hours,
                              model=args.model, mode=args.mode), indent=1))
