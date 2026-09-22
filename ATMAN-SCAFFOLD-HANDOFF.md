# ATMAN public scaffold — GitHub patch handoff

Built: 2026-09-22 08:21 Eastern Daylight Time
Source: live atman-live on OPERATOR-PC
Artifact: atman-scaffold-public.zip (+ Desktop folder twin)

## For the maintainer
Apply this pack to the public GitHub repo and patch forward. **Do not** commit private soul / seal / PSC / .env.

## What is new since prior public zip (2026-09-21)
### Phase 2 — latency / working context
- working_context.py — TSC flat + capped WFC snapshot (no per-turn context leak)
- loop.py / 
eason.py wired for snapshot assembly
- Docs: SOUP-PHASE0-ARCHITECTURE.md, SOUP-PHASE1-PROFILE.md, SOUP-PHASE2-*.md

### Phase 3 — self-improve (alive)
- self_improve/ package: engine.py, safety.py, reeplay_proposer.py
- Cockpit tool self_improve + config.yaml permissions
- Idle hooks: 
elay.py /initiative/pending, loop.py ambient idle
- **Operator lock:** safe skills **auto-apply** (esp. Minecraft); safety fence **REFUSES** hack/exploit/credential/core-bypass
- Docs: SOUP-PHASE3-CHANGELOG.md, SOUP-PHASE3-FREEPLAY.md

### Hard locks (unchanged)
- Sealed core: core.py, atman_core.py, gate_policy.json, crate.py, wake.py, seal.py
- Private never shipped: atman-private/, 	sc.atman.private*, stage1-seal.json, psc.json, secrets

## How Operator reviews live self-improve
- Changelog: self_improve/CHANGELOG.md (AUTO-APPLY / REFUSED / PROPOSE lines)
- Accept path still exists for odd domains; routine Minecraft skills do not need approve

## Rebuild
`ash
python pack_public_scaffold.py
`
