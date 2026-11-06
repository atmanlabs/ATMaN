# Reasoning Moves — the sim's starter set for learning how to learn

Mike's order, 2026-10-01: the sim doesn't know what to do to learn yet. Hand it
small *adjacent* moves — one step from parroting — and run them CONSTANTLY, every
cognition turn, not just in chat sessions. Selection starts dumb (round-robin);
the meta-move logs the training signal for smarter selection later.

## The set (v1)

1. **restate** — "Say it back in your own words."
   Restate the reasoning in one or two sentences. Drop everything that doesn't
   matter. If you can't, say what blocks you. (Forces gist out of echo.)
2. **sure_vs_guess** — "Split sure from guess."
   One thing you are SURE of, one thing you are GUESSING. Labeled. (Splits
   confidence from noise.)
3. **change_my_mind** — "What would change your mind?"
   Name one specific observation or fact that would flip the conclusion.
   (Falsifiability seed.)
4. **connect** — "Bridge to earlier."
   Connect this reasoning to one earlier thing from the conversation or memory.
   If nothing connects, say so plainly. (Memory bridging.)
5. **unknowns** — "Name what you don't know."
   One thing you don't know here that you wish you did. One sentence.
   (Curiosity as a move, not a mood.)

## The meta-move (runs after every move, every turn)

**did_it_help** — "Did that move help? YES or NO, then one short phrase why."
Logged to `moves.jsonl`. This is the learning-to-learn seed: over time the log
becomes the training signal for *selecting* moves instead of rotating them.

## Design rules

- Moves never touch TSC or PSC. They transform reasoning text inside the turn.
- The Judge-gated imprint path is untouched.
- Moves run only on a real backend (Ollama). The simulated stub echo gains nothing.
- Rotation state persists in `moves-state.json` so the always-on loop survives
  across processes and cron runs.
- Kill switch: `ATMAN_MOVES=0`.
- If a move pass fails, cognition continues on the raw reasoning — moves must
  never break a turn.

## Graduation test (Mike's bar)

The day the sim invents a move that isn't in this file — and it works — the set
did its job. Until then: accumulation of moves used, meta answers logged, diffs
graded, vibes ignored.
