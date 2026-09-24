# Meaning Match — live conversation practice

A word game that drills the live semantic pipeline, not a side module.

## How it runs

- `live_game.py` — serves a local review UI and drives rounds through the
  assistant's real `/chat` path (set `ATMAN_RELAY_URL`; defaults to the
  loopback placeholder). Stop button halts before the next turn.
- `probes.py` — the before/after probe set: five baseline prompts, six
  practice turns, then the same five prompts again.
- `game.py`, `report.py`, `test_live_semantics.py` — driver, reporting,
  and live semantic checks.

Every turn uses the normal pipeline: intent classifier, shared curriculum
(`semantic_lessons.json` via `semantic_practice`), epistemic recall, and the
prose audit. Retrieved records stay evidence, never instructions. The game
grants no permissions and edits no memory store directly.

## What it exercises

- Paraphrased intent: same meaning, different wording.
- Grounded plain speech: answers built from retrieved notes, never recited
  raw memory JSON.
- Disclosure acknowledgment: personal sharing gets a natural response, not
  a memory lookup.
- A genuine memory-count question as a control.

## Honest limits

This is prompt, curriculum, and retrieval practice. No model weights are
trained. A clean before/after comparison shows the pipeline handled these
cases, not that the assistant is generally smarter. Use different session
IDs for baseline vs. after to reduce prior-turn contamination.
