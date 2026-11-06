# SPEAK-MOVE

Updated: speak-surface filter + comedy dream-backwards (Mike 2026-09-25)

## Rule
- Keep `speech_render` decide->render (llm_calls=0).
- **Internal thought / receipts**: may keep practice-lesson / Chosen move narration for the crate verifier.
- **Spoken / reply (`answer`, `say`, `show`)**: ONLY the natural realization of the chosen move — never hyp-prefix lesson rehash.

## Mechanism
- Module: `speak_move.py` (`apply_speak_surface`, `realize_spoken_move`).
- `speech_render.compose` still builds decide clauses + receipts, then splits:
  - `internal_thought` = hyp-wrapped lesson/decide text
  - `answer` = spoken move (greeting line, honest refuse, or **joke `spoken` field**)
- Passive skip-web imprints are gated off the spoken lead.

## Comedy (dream backwards)
- `comedy_dream.py` seeds **speech-shaped** joke imprints: primary field is `spoken` (setup/punchline).
- Sleep: `run_comedy_sleep.py` — timed sleep, dense cycles, held-out probes.
- Invent/gap asks still honest-refuse; no LLM comedy writer.

## Smoke
- `hey buddy…` → natural hello (not "A hypothetical practice lesson…")
- `tell me a joke` → real short joke from bank OR honest "I don't have a joke queued up…"

## Before -> after (screenshot utterances)

### 1) hey buddy hows it going? how was the dreams?
- Before (spoken): A hypothetical practice lesson suggests: when I hold the active topic... Chosen move: offer a clean hello and wait for substance.
- After (spoken): Hey — how were the dreams? I'm here if you want to share.
- After (internal): lesson/decide verbose retained for verifier.

### 2) tell me a joke
- Before (spoken): A hypothetical practice lesson suggests: ... decline inventing a joke... Chosen move: admit the gap...
- After (spoken): I invent elevators for a living. It's an uplifting job. (supported joke_delivery imprint)
- Invent-from-nothing still honest refuse.



## Identity + memory (2026-09-25)
- Sealed TSC.iam + PSC profile fuel speak-move via spoken on identity candidates.
- See IDENTITY-WIRE.md / MIKE-HANDOFF.md.
- llm_calls=0; no model fallback.

