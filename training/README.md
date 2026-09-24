# Training harnesses

Example programs that exercise the ATMAN conversation pipeline the way the
live assistant actually answers: same classifier, same curriculum, same
evidence rules. Nothing here trains model weights. Repeated success on a
harness is evidence the harness's behavior is handled, not evidence of
general intelligence improvement.

All harnesses talk to a running assistant over HTTP. Endpoints default to
loopback placeholders for local simulation; override with environment:

- `ATMAN_RELAY_URL` — assistant chat relay (default `http://127.0.0.1:18790`)
- `ATMAN_OLLAMA_URL` — local model endpoint (default `http://127.0.0.1:11434`)
- `ATMAN_TRAINING_REPORTS` — directory of validated training reports read by
  `training_receipts.py` (default `training/reports`)

## meaning-match/

A word game for semantic conversation practice: paraphrased intent
classification, grounded plain-language answers from retrieved notes, and
acknowledgment of personal disclosures. Every round goes through the real
chat pipeline — no side models, no separate answering path. Includes a
memory-count control question. See `meaning-match/README.md`.

## situation-gym/

A native Windows desktop app (Python/Tkinter, PyInstaller) plus a headless
simulator for goal-driven scenarios: natural NPC dialogue reveals
constraints, service fixtures are discovered through simulated tool calls,
reservations can fail, and a late requirement forces replanning. Process is
scored, not just the win condition; full traces are kept for review. See
`situation-gym/README.md` and `situation-gym/SPEC.md`.

## crafter/

An isolated controller for the open-source Crafter survival environment
(https://github.com/danijar/crafter — install separately). The assistant's
local model chooses among exploration, gathering, crafting, and survival
goals; episode summaries enter memory only through the Judge-gated path.
Game-specific practice and persisted experience, not retraining. See
`crafter/README.md`.

## reports/

Validated training reports consumed by `training_receipts.py` (read-only).
Populate this directory with your own `practice.json` / `after.json` runs;
see the module docstring for the expected shape.
