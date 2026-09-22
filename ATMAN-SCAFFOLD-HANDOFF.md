# ATMAN public scaffold — GitHub patch handoff

Built: 2026-09-22 09:37 Eastern Daylight Time
Source: live atman-live on OPERATOR-PC (project ATMAN, relay 127.0.0.1:18790)
Artifact: atman-scaffold-public.zip + Desktop atman-scaffold-public\

## For the maintainer
Drop this pack onto the public GitHub scaffold and patch forward.
**Do not** commit private soul / seal / PSC / .env / atman-private.

OpenClaw note: gateway 18789 is OpenClaw-Worker (tools). Conversational ATMAN person = ATMAN/atman-live on **18790**.

## What is new since prior public zip

### Phase 2 — latency / working context
- working_context.py — TSC flat + capped WFC snapshot
- WFC depoison (2026-09-22): search/evolve/camera blobs redacted in prompt so chat is not derailed into fake Windows-upgrade tool calls
- Docs: SOUP-PHASE0-ARCHITECTURE.md, SOUP-PHASE1-PROFILE.md, SOUP-PHASE2-*.md

### Phase 3 — self-improve (alive + rolling)
- self_improve/ — engine, safety fence, freeplay_proposer, **rolling_evolve**
- Cockpit tool self_improve + config permissions
- Idle hooks: relay /initiative/pending, MindLoop ambient
- Safe skills auto-apply; hack/credential/core-bypass REFUSED
- GitHub self-upgrade orders **execute** (web_search → ingest → apply skills + extension stubs)
- **Rolling evolve** (~10 min): rotate scout topics, apply new leads, advance stubs — continuous, not one-shot
- Allowlisted patch_file for non-sealed soup (never gate_policy/core/seal/psc)
- Docs: SOUP-PHASE3-*.md, SOUP-SELF-UPGRADE.md

### Chat / conversation guards (2026-09-22)
- Natural short replies (
aturalize_reply, SPEAK v4)
- Conversation guard: normal talk (how are you / interfaces / upgrade status) must not become web_search
- Reject hallucinated Windows 11/12 searches Operator never asked for
- Identity regex: what are you thinking is chat, not identity dump
- Post-scout evolve no longer orce=True mid-chat (was flooding WFC)

### Hard locks (unchanged)
Sealed: core.py, atman_core.py, gate_policy.json, crate.py, wake.py, seal.py
Never ship: atman-private/, 	sc.atman.private*, stage1-seal.json, psc.json, secrets

## Rebuild
`ash
python pack_public_scaffold.py
`
