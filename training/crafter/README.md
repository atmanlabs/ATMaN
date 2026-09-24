# Crafter sandbox controller (example)

An isolated controller for the open-source Crafter survival environment
(https://github.com/danijar/crafter). Install the upstream Crafter package
separately; it is not bundled here.

## How it runs

- `play.py` — local game controller: the assistant's model chooses among
  exploration, gathering, crafting, and survival goals; a constrained
  controller carries out movement and interactions. Serves a local
  watch/pause/stop page.
- `verify.py` — outcome verification.
- `deadline_guard.py` — bounded-run enforcement.

Episode summaries enter the assistant's memory only through the existing
Judge-gated package path — the game cannot write memories directly.

## Honest limits

This is game-specific practice and persisted experience, not language-model
retraining and not proof of general improvement. Smoke-test achievements
(movement, gathering, crafting, defeating hostiles) are results of the
controller setup, not promised outcomes. Nothing here spends cloud credits,
publishes content, or touches protected core state.
