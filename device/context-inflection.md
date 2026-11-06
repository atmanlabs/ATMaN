# Context-Inflection: scene-conditioned emotional weighting (design note, 2026-10-02)

Mike's direction: ElevenLabs' Eleven v4 reads scene-level context to change vocal
inflection during dialogue. Steal that technique for ATMAN — detect what is going
on, and let it inflect the self: modulate emotional weight.

## What v4 actually does (public behavior, internals closed)

- Released 2026-09-28 (Eleven v4 + v4 Turbo). New architecture "performs" text
  instead of reading it: interprets tone, pacing, emotion, character, and context.
- Scene-level dynamics: dialogue responds to what was just said instead of
  treating each line as an isolated generation. Same line, different scene =
  different delivery (doctor calming a patient vs. squad leader shouting).
- Stackable inline expression tags ([laughs], [said angrily...]) followed in
  sequence; natural-language delivery direction.
- Speaker identity stays constant across long work while delivery swings.
  Identity = the constant. Expression = the variable.

Honest limit: ElevenLabs publishes behavior, not mechanism (proprietary, no open
weights). We are stealing the design principle, not their algorithm.

## The principle

    delivery = f(content, scene context, explicit tags) | identity held fixed

Context-conditioned modulation: context never rewrites who is speaking; it
changes how what is said lands.

## Mapping onto ATMAN canon

Canon loop: Capture -> Emotion Weight -> Rolling Memory -> Reason -> Judge ->
Action -> Outcome -> Memory Update. Emotion WEIGHTS (importance, confidence,
novelty, significance, goal relevance); it never decides. TSC immutable; the
synthetic emotion core adapts in PSC, never TSC.

The v4 move: today the canon weights read as per-event scalars. Make the weight
a function of the scene, not just the event:

    emotion_weight = f(event, rolling scene state, event-tag sequence) | TSC fixed

1. Scene reader (new, bounded). Over the rolling window, classify what is going
   on: praise / correction / conflict / play / loss / danger / routine. The same
   event weighs differently in different scenes (correction after praise !=
   correction after conflict). This is Mike's "radio tuning" applied to weight:
   lock the scene first, then amplify.
2. Bounded modulation only. The scene state scales each of the five weights
   within fixed ranges. It can raise salience (how hard an event pushes for
   imprint consideration); it cannot approve anything. Reason "tastes" the
   weight; the Judge still rules against TSC and evidence. The Judge path is
   untouched — same rule as the reasoning moves (2026-10-01).
3. Tag sequences. Borrowing v4's stackable tags: explicit event tags
   ([praised], [corrected], [loss], [routine]) logged in order in rolling
   memory. The sequence conditions the next weight, not just the latest tag.
   Open design question: does a run of losses make the next loss weigh heavier
   or numb it? (Both are human-plausible; pick deliberately, log the choice.)
4. Inflection on the self (SPECULATIVE — label as such). The delivery-side
   analog is the tone of the sim's own self-talk (flat / urgent / curious).
   For a 1.5B model this might bias attention, but the defensible, testable
   piece is weighting (salience). Self-talk tone is a later experiment, not
   part of v1.

## Invariants (hard)

- TSC is read-only to this system. If modulation ever reaches TSC, that is not
  prosody, that is possession. Kill condition.
- Weights never decide. Judge verdict semantics unchanged
  (APPROVED / NOTED / HELD / REJECTED); PSC imprint still requires APPROVED.
- Modulation bounds are constants in code, not learned. If bounds themselves
  ever adapt, that adaptation lives in PSC and passes the Judge like anything
  else.
- Every weight computation logs its scene state + tag sequence, so a human can
  audit why something weighed what it weighed ("felt but rejected" trace
  extends naturally: "felt heavier because scene=conflict").

## Where it would live (sandbox sim only)

- A sibling module to reasoning_moves.py: a scene/weight pass in the cognition
  path (LocalBrain.think or loop.py's render path), kill-switched, falling
  back to flat per-event weights on any failure. No writes to TSC/PSC from the
  pass itself; it only supplies weights upstream of the Judge.
- Status: BANKED, NOT BUILT (2026-10-02). Pick up in a lab block by Mike's call.

## How we'd know it works (Mike grades)

- Same event replayed in two different scenes yields different weights, and the
  weight difference plausibly matches the scene (show the receipts).
- Zero change to Judge verdicts on the existing regression suite.
- The sim's consolidation stops imprinting bookkeeping at the same rate as
  salient events — i.e., salience actually separates signal from noise.
- Failure mode to watch: scene misclassification silently bending everything
  downstream. The audit log is the defense; if scene labels can't be defended
  from the transcript, the pass comes out.
