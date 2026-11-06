# Coherence Sweep — Experiment Report

**Date:** 2026-09-26 (night) · **Sandbox only** · **Status: ITERATE — pending Mike's blind judging**

## What was tested, in one sentence

Whether the sim daydream generator's idea coherence (proxy-scored, deterministic, no LLM) varies systematically with three fuel axes — pool mix ratios, sampler serendipity, and repo chunk-type emphasis — across 404 generated ideas in 19 cells.

## Pre-registered design

- **Grid A** (16 cells): target_mode {repo-heavy, event-heavy, goal-heavy, balanced} × chunk_type_filter {procedural, narrative, philosophy, unfiltered} at serendipity=0.4, ~25 ideas/cell.
- **Grid B** (3 cells): serendipity {0.1, 0.25, 0.5} × (balanced, unfiltered), ~20 ideas/cell.
- Target-mode definitions (exact): repo-heavy = goal-only target, no event content {p1:0.80, p2:0.00, p3:0.20}; event-heavy = event + goal {0.30, 0.50, 0.20}; goal-heavy = two goals combined, no event {0.30, 0.00, 0.70}; balanced = event + goal, daydream.py's default composition {0.34, 0.33, 0.33}.
- Type filters applied post-draw on `repo.sample()` output (draw counts logged; filtering is expensive — see skip section).
- Fresh pool: `runtime/daydream/sweep/idea_pool_sweep.jsonl` (404 ideas). The original `idea_pool.jsonl` was not touched (still 7 lines).
- Judge: `daydream.judge_hypothesis()` wrapping `loop.judge_rule` — **404/404 HYPOTHESIS, 0 REJECTED** (no core-override patterns in generator output; the judge path never fires on this content).
- No PSC writes. No LLM. `loop.py`, `device.py`, `dream.py`, `consolidate.py`, judge thresholds/verdicts untouched. Skip discipline kept: chunks with no extractable mechanism are skipped, never saladized.

## N generated / N skipped

- **404 ideas generated, 242 skipped → 37.5% overall skip rate.** The skip discipline is doing heavy lifting: more than a third of draws yield no idea rather than a fabricated one.
- Skip rate by target mode: repo-heavy 26.5% · event-heavy 35.3% · goal-heavy 36.8% · **balanced 45.4%**.
- Skip rate by type filter: narrative 25.7% · procedural 35.3% · philosophy 38.2% · **unfiltered 45.0%**.
- Type-filter draw cost (drawn → kept): philosophy cells needed up to 517 draws for ~20 keeps; the sampler's directed portion is narrative/Art-of-War heavy, so minority-type cells burn draws.

## Proxy score distribution (0–6)

| total | n |
|---|---|
| 1 | 9 |
| 2 | 245 |
| 3 | 136 |
| 4 | 14 |
| 5–6 | **0** |

Per-dimension: specificity {0:252, 1:137, 2:15} · non-circularity {0:404 — zero variance, see below} · groundedness {2:392, 1:12}. Template-phrase penalty never triggered (generator doesn't emit those phrases).

**Scorer sanity check (10 hand-read ideas): 9/10 agreement.** The one disagreement: DD-0006, where carryover of a proper name ("confucius") earned specificity=1 though the idea was salad — name carryover over-credits. Scorer kept as-is; disagreement logged, not tuned away.

## Correlation table — score ≥ 3 rate vs baseline 37.1% (score=4 baseline 3.5%)

| condition | n | ≥3 rate | Δ vs baseline | =4 rate |
|---|---|---|---|---|
| **target_mode: repo-heavy** | 100 | 38.0% | +0.9pp | 1.0% |
| **target_mode: event-heavy** | 88 | 36.4% | −0.8pp | 3.4% |
| **target_mode: goal-heavy** | 86 | 38.4% | +1.2pp | 5.8% |
| **target_mode: balanced** | 130 | 36.2% | −1.0pp | 3.8% |
| **type: procedural** | 88 | 37.5% | +0.4pp | 3.4% |
| **type: narrative** | 101 | 33.7% | −3.5pp | 2.0% |
| **type: philosophy** | 84 | **48.8%** | **+11.7pp** | 2.4% |
| **type: unfiltered** | 131 | 32.1% | −5.1pp | 5.3% |
| serendipity 0.1 (bal/unfilt) | 18 | 44.4% | +7.3pp | 5.6% |
| serendipity 0.25 (bal/unfilt) | 16 | 25.0% | −12.1pp | 6.2% |
| serendipity 0.4 (bal/unfilt) | 17 | 23.5% | −13.6pp | 0.0% |
| serendipity 0.5 (bal/unfilt) | 20 | 20.0% | −17.1pp | 5.0% |

Read it straight: **pool-mix ratios show no effect** (all modes within ±1.2pp of baseline). **Philosophy-leaning draws are the one clear positive** (+11.7pp, n=84 — philosophy chunks carry causal connectors the mechanism picker prefers). Lower serendipity trends better but the serendipity cells are small-n and confounded (ran last on leftover chunk pools — see Honesty).

## Sampler-weight recommendation (what the evidence supports)

1. **Emphasize philosophy-typed chunks** in the fuel mix (weight ~1.5–2× vs uniform): the only condition that beats baseline by a real margin. Procedural is neutral; narrative and unfiltered drag.
2. **Do not rebalance pool ratios on this evidence** — mode had no measurable effect; the production default (balanced) is neither better nor worse than the alternatives.
3. **Keep the skip discipline exactly as is.** 37.5% skip rate is the honesty tax; weakening it to inflate idea counts would trade the one thing the generator does right.
4. **Serendipity: weakly favor 0.1–0.25 over 0.4–0.5**, but treat as provisional — needs a clean re-run with chunk pools controlled before it becomes a recommendation.

## Negative leak test

`idea_pool.leak_check` (sweep pool, 404 ideas) against the sim's real PSC (`core-store.json`, 14 records): **leaked: false, 0 matches.** Quarantine holds; trap check confirmed (`promote()` still raises `IdeaQuarantineViolation`).

## One surprising failure

The first analysis of this very sweep produced a spectacular, publishable result — **balanced mode at 3.85% top-quartile vs repo-heavy at 38%** — that was **entirely an artifact**: rank-based quartiles with ties (136 ideas scored 3) broken by idea-id order, which correlates with cell run order. Under score-based tiers the mode effect collapsed to ±1.2pp — zero. Caught before it left the lab. The lesson is filed: with discrete proxy scores, always use score tiers, never rank quartiles with id tie-breaks.

A second, smaller one: the non-circularity dimension scored **0 on all 404 ideas** — the transferred sentence adds ~0–1 content words beyond its inputs + the template (the only novel word is usually the junk chunk-noun, e.g. "used on its *kung*"). The dimension has a floor effect: it measures something the generator structurally almost never produces. Effective proxy variance came only from specificity (mechanism carryover: 62% of ideas carry zero mechanism nouns into the transfer) plus saturated groundedness.

## HONESTY SECTION (mandatory)

- **Proxy scores are NOT coherence.** They are cheap deterministic correlates: noun carryover + verbatim grounding. Mike's blind keep/kill judging (`corpus-dreams/BLIND-JUDGING-SHEET.md`, 50 ideas, sealed key at `runtime/daydream/sweep/judging-key.json`) is the real verdict and **has not happened yet**.
- The scorer was calibrated on 3 pilot ideas and sanity-checked on 10; one known over-credit (proper-name carryover) was logged, not fixed — the proxy is admittedly crude.
- Serendipity cells are confounded with chunk-pool leftovers and small-n; the trend is suggestive, not evidence.
- Groundedness is saturated by construction (the rationale is a verbatim chunk quote) — it cannot discriminate and inflates every total by ~2.
- Sim scale ≠ PC scale. The sim's pool2/pool3 are 6 events + 3 drives; the PC's fuel is richer. A green sim result is evidence, not proof.
- All 404 ideas are quarantined HYPOTHESIS, validated:false. Nothing here is a belief.

## Verdict

**ITERATE — pending Mike's blind judging.** Mike decides promote/kill. If his keep/kill labels correlate with the proxy's specificity dimension, the philosophy-emphasis recommendation graduates from suggestive to actionable.

## Provenance

- Sweep script (pre-registered grid + scorer): `runtime/daydream/sweep/sweep.py`
- Per-idea log (id, hypothesis, chunk/event/goal ids, exact mix params, judge verdict, proxy scores): `runtime/daydream/sweep/ideas_log.jsonl`
- Cell stats: `runtime/daydream/sweep/cell_stats.json`
- Fresh pool: `runtime/daydream/sweep/idea_pool_sweep.jsonl` (original pool untouched)
- Blind sheet: `corpus-dreams/BLIND-JUDGING-SHEET.md` · sealed key: `runtime/daydream/sweep/judging-key.json`
- External text used: public-domain repo chunks (Holmes, Art of War, Meditations, Time Machine) — study material only, never autobiography. No PSC writes.
