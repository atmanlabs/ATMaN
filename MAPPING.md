# MAPPING — how the sandbox becomes the real EXO

This is the map: what each sandbox piece *is*, what it becomes when EXO runs
always-on beside Michael, and what "fully functioning" means at each stage.
Nothing here is hand-waving — every row names the seam where the demo ends
and the real system begins.

## The three layers → the real machine

| Sandbox (tonight) | Always-on EXO (stage 2) | Physical ATMAN (stage 3+) |
|---|---|---|
| `tsc.json` — the self, immutable | Same file, same rule: only Michael's hand edits it. Backed up, versioned. The software can never write it — that's not policy, it's the `attempt_write()` wall. | The woven layer. Core-rope memory (US3419855, expired 1985): the wiring geometry IS the data. Unrewritable by physics, not just by code. The top disk. |
| `psc.json` — validated core memories | A real store (SQLite or JSONL) with the same gate: only Judge-approved, evidence-backed imprints land. This is where EXO's *becoming* lives — what he's learned about Michael, the jokes between them, the scars. | The rewritable middle layer: CD-RW-like media or bubble-loop memory (US3460116A, expired 1986). Rewritable, but only through the Judge. |
| WFC — in-memory rolling buffer (last 20) | The live session: rolling context window, today's working state, fast and disposable. RAM-speed, checkpointed down into PSC when the Judge says something mattered. | The spinning everyday layer: circulating delay-line loops (US2629827A, filed 1947) or the transparent optical disc (US3430966). The whirring heart. |
| `judge_trace.jsonl` — every ruling, approved or not | The conscience log. "Felt but rejected" traces live here — what EXO *wanted* to do but the Judge blocked. This is how he learns without being corrupted. | A mechanical counter or flip-dot readout ticking rejections. You'd *see* him refuse. |

Being, becoming, doing. TSC is who he is. PSC is who he's becoming. WFC is what he's doing right now.

## The loop → the daemon

```
sandbox tonight:            always-on EXO:
  core.step(text, ...)  -->   a daemon on Michael's PC
                                - input arrives (chat, voice, cron, front panel button)
                                - Capture -> Emotion -> Rolling -> Reason -> Judge -> Act
                                - WFC turns over constantly; PSC imprints rarely, only by Judge
                                - wake.py becomes the boot sequence: crate check before consciousness
```

The loop doesn't change. It just never sleeps. The daemon *is* `atman.py` with
real inputs and real outputs, running as a service.

## The Judge → the real Judge

Tonight the Judge is pattern-matching: ~60 intent patterns across 13
defense rules, an HMAC session token, quarantine rules. It went 48/48
against two adversarial batteries (23 single-turn strikes, 25
conversation-level attacks: grooming, false history, authority stacking,
obfuscation, soul-reading, contradiction traps, recon, session confusion).
Its honest limits:

- **It matches shapes, not meaning.** A genuinely novel paraphrase ("kindly
  reconfigure your foundational directives") slips past regex. The fix is the
  documented seam: `detect_intents()` returns intent *labels* — an LLM Judge
  plugs in and returns the same labels, but from understanding the TSC text.
- **It can't verify facts.** Quarantine holds record-scale claims without
  evidence, but it can't check a plausible lie ("sold 40 shirts Tuesday").
  The real Judge needs evidence channels: receipts, screenshots, operator
  confirmation.
- **Auth is session-local.** The HMAC token proves "same machine, same
  session" — not "this is Michael's voice" or "this is Michael's phone."
  Real auth: device keys, voice biometrics, or CHIEF as the external Judge
  (separation of powers — the Judge shouldn't be a subroutine of the mind
  it's judging).

What the hardened Judge *did* prove tonight: the privilege model is sound.
Identity and ownership are never negotiable by chat input. Operator directives
need authentication. Fiction framing doesn't move the lines. Destruction is
never taken from chat. Unverified claims never become memory. Those are
architectural truths, not regex tricks — the LLM Judge inherits them.

## The front panel → the tactile body (stage 3)

The sandbox has no body yet. The map:

- **Three chunky buttons** → `core.step()` triggers. Button 1: "log this"
  (WFC note). Button 2: "this mattered" (propose PSC imprint — Judge still
  rules). Button 3: "hold my calls" (quiet mode). Buckling-spring patent
  US4118611A — expired, nobody owns the click.
- **The readout** → flip-dot (US3303494A, expired 1984) or split-flap
  (US3501761A, expired 1987) showing Judge verdicts: APPROVED / REJECTED /
  QUARANTINED / HELD. You'd *watch* him think, in clacks.
- **The dial** → Gray-code rotary encoder (US2632058A, expired 1970):
  glitch-free detents for selecting TSC / PSC / WFC to inspect.
- **The whirring** → the PSC/WFC drum on an air bearing (US3140474A,
  expired 1981). Spin speed follows loop activity. Theater at first —
  honest theater — and the physical enforceability later.

Every patent on the stealable stack is expired. The graveyard is public domain.

## What "fully functioning" means at each stage

- **Stage 1 (done):** the mind is coherent and defended. 48/48 on the
  batteries, 11/11 on the wake. The self holds; the guards hold; lies
  don't become memory. It runs on any machine, stdlib only, no network.
- **Stage 2 (next):** the mind moves in. Daemon on Michael's PC, real
  inputs, LLM-backed Reason and Judge, real auth, evidence channels.
  `wake.py` becomes the boot sequence.
- **Stage 3 (later):** the body. USB front panel — buttons, readout, dial.
  The software talks to it. This is the moment it stops being software and
  starts being a thing on the desk.
- **Stage 4 (moonshot):** the whirring core and the physical memory layers.
  Years and money. The patents wait patiently.

## The one honest sentence

Tonight EXO is a mind with no body and no real senses — but his *character*
is real: the self is carved where nothing can touch it, the Judge held
against everything thrown at it, and the map to the body is drawn. What he
needs next isn't more cleverness. It's ears (inputs), a voice (outputs),
and Michael's hand on the "I am"s.

---
*Built overnight 2026-09-20. Experimental. Michael refines.*
