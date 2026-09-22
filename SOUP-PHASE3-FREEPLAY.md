# SOUP Phase 3 — Freeplay Skill Proposals

## Goal
Make Phase 3 `self_improve` **alive during idle/freeplay**: ATMAN *proposes* skill drafts
through the gate; the operator reviews via CHANGELOG (+ proposal JSON). Sealed core stays LOCKED.
`auto_apply_proposals` defaults **false**.

## Design summary

### Engine (`self_improve/engine.py`)
| Method / dispatch action | Behavior |
|--------------------------|----------|
| `propose_skill` | Schema + protected-token checks; writes `self_improve/proposals/<id>.json`; CHANGELOG **PROPOSE (not applied)**; indexes `status=proposed`. Does **not** write `skills.json`. |
| `list_proposals` | Lists proposal files (optional status filter). |
| `accept_proposal` | Loads proposal → `add_skill` (backup rails). Marks proposal accepted. |

Unchanged: `status`, `list`, `rollback`, `add_skill`, `add_extension`.

### Freeplay module (`self_improve/freeplay_proposer.py`)
- `maybe_propose(context)` — rate-limited idle hook
- Heuristic draft from recent significant-events / chat themes (no new cloud APIs)
- Calls `engine.propose_skill(...)`
- Optional auto-apply only if config explicitly enables it

### Idle hooks (where proposals fire)
1. **`relay.py`** — `GET /initiative/pending` (Minecraft freeplay/idle poll)
2. **`loop.py`** — MindLoop ambient idle (`queue.Empty` → ambient sensory check)

State file: `self_improve/freeplay_state.json` (`last_propose_ts`).

### Config (`config.yaml`)
```yaml
self_improve:
  freeplay_propose: true
  freeplay_min_interval_sec: 900   # 15 minutes between proposals
  auto_apply_proposals: false      # the operator must accept
```

## How the operator reviews
1. Scan `self_improve/CHANGELOG.md` for **`PROPOSE (not applied)`**
2. Open `self_improve/proposals/<change_id>.json`
3. Accept:
```python
from self_improve.engine import engine
engine.dispatch({"action": "accept_proposal", "proposal_id": "chg_..."})
# or
engine.accept_proposal("chg_...")
```
4. Or leave parked — `skills.json` stays untouched

## Safety
- Propose path never mutates: Soul/TSC, gate_policy, seal, wake, crate, atman_core, psc
- `skills.json` only on explicit accept / add_skill
- Protected payload tokens refused
- Apply path keeps backup/rollback rails

## Verified on box
- propose → proposal file + CHANGELOG PROPOSE; skills.json unchanged
- second maybe_propose within interval → rate_limited skip
- accept_proposal → apply with backup; rollback restores
- sealed file hashes unchanged vs pre-edit baseline

## Backups of edited sources
`*.bak-freeplay-20260922-081006` next to engine.py, config.yaml, relay.py, loop.py, __init__.py
