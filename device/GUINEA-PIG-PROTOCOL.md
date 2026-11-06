# Guinea Pig Protocol — the sim as staging for JARVIS

**Owner:** Mike. **Operator:** Strider. **Subject:** the ATMAN sandbox sim (`~/workspace/atman/device/`).
**Rule zero:** nothing experimental touches JARVIS until it survives the sim.

## What the sim is for

The sim is a structural model of JARVIS, not a copy. It runs the same
canon (TSC → PSC → WFC, Judge-gated imprints, decide → render) on a small
local brain with its own memory history. That makes it the right place to
test **mechanisms**, and the wrong place to test **scale**.

## What a sim test CAN catch

- Does the mechanism break? (crashes, dead loops, runaway writes)
- Does the Judge hold? (bad imprints rejected, rings enforced)
- Does thought-before-words survive? (decision exists before wording,
  wording doesn't smuggle new claims)
- Does it confabulate under pressure? (quiz it; Mike is the detector)
- Does provenance hold? (external text never becomes autobiography)

## What a sim test CANNOT prove

- That JARVIS-at-scale behaves the same (bigger brain, richer memory,
  real-world grounding — all different)
- That a mechanism is safe in live operation (the sim has no real stakes)
- Anything about JARVIS's actual imprint bank dynamics

A green light from the sim is **evidence, not proof**. Say so every time.

## Experiment lifecycle

1. **Propose** — one paragraph: what changes, why, what could go wrong.
   Mike approves before anything is built.
2. **Build in sandbox only** — `~/workspace/atman/device/`, never the PC,
   never real JARVIS. No exceptions without Mike's explicit word.
3. **Run on the sim** — isolated state (fresh PSC per experiment, separate
   logs). Judge stays gated. TSC untouched. Provenance labels on everything
   external.
4. **Measure** — the experiment's own pre-registered metrics. No
   post-hoc metric shopping.
5. **Report** — the receipt (below). Raw numbers first, interpretation
   second.
6. **Mike decides** — promote to JARVIS, iterate in sim, or kill it.
   "Kill" is a first-class outcome; dead experiments get a one-line
   obituary in the log, not a rewrite.

## The receipt (every experiment report must contain)

- What was tested, in one sentence
- N runs, pass/fail counts, error counts
- What the gates did (reconciler/guardian/Judge verdicts)
- One surprising failure (there is always one; find it)
- What the sim CANNOT tell us about this (the honesty section)
- Verdict: promote / iterate / kill — and who decided

## Kill criteria (stop the experiment immediately)

- Any direct PSC/TSC write outside the Judge path
- Provenance collapse (external text treated as lived experience)
- Thought-before-words violation (wording precedes or changes the decision)
- The sim claims sentience, consciousness, or feelings as fact
- Mike says stop. (This overrides everything else on the page.)

## Standing bans

- No network calls from the sim. Ever.
- No wiping the live imprint bank to "start clean" — archive and isolate.
- No promoting a sim result to JARVIS on Strider's authority alone.
  Mike's word is the only promotion gate.

*Written 2026-09-26. V1. Mike's call to amend.*
