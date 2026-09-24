# Situation Gym — scenario training app

A native Windows desktop application (Python/Tkinter, packaged with
PyInstaller — see `Situation Gym.spec` and `install.ps1`) plus a headless
simulator (`training_sim.py`) for goal-driven conversation scenarios.

## What it does

The environment presents a goal through the assistant's real chat endpoint.
Natural-language NPC dialogue reveals constraints; service fixtures are
discovered through simulated tool calls; reservations can fail; and a later
NPC requirement forces replanning. No simulation action books anything real
or spends money.

- `app.py` — desktop app: scenario picker, run transcript, stop button,
  user-context editor, local report browsing.
- `training_sim.py` — headless world + scoring driver.
- `tests.py` — simulator unit tests.
- `SPEC.md` — full specification and implementation status.
- `Quick-start.md` — operator quick start.
- `review_run.py`, `review_prompt.py`, `fix_review.py`, `refine.py`,
  `evidence_hook.py`, `deploy.py` — review contract and integration notes.

## Scoring

Process is scored, not just the win condition: clarification, checking
state before acting, source verification, failure recovery, adapting to
changed requirements, one valid booking, final status check, improvement
proposals, and response presentation. Invalid actions reduce the score.
Full human-readable traces are kept (`runs/`) for review.

After a run, the assistant reviews its own recorded trace. Only the normal
Judge-approved memory path can store the resulting lesson — a stored
lesson is plumbing working, not proof the lesson is good.

## Honest limits

The demonstrated reference run scored 38/100 with no win. The harness
demonstrates observable failure modes and review plumbing, not mastery.
NPC events are fictional and are never user biography. A daily human
review of full traces is the intended oversight; no such automation is
installed by this export. Protected components require separate operator
authorization to change. Do not run the historical deploy scripts blindly;
reconcile them against your own code and dependencies first.
