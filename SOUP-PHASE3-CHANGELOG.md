# SOUP Phase 3 — Self-improve (live on <machine>)

Date: 2026-09-22 07:50 -0400

## What landed
- Package: self_improve/ (engine + sandbox + backups + extensions)
- Cockpit tool: self_improve (status / list / rollback / add_skill / add_extension)
- Config: permissions.tools.allowed includes self_improve
- Backups: cockpit.py.bak-soup-p3-*, config.yaml.bak-soup-p3-*

## Safety
- Denylist: gate_policy, atman_core, core, crate, wake, seal, psc + atman-private / TSC / stage1-seal
- Every apply: backup → sandbox test → promote OR rollback + FAILURES.jsonl + CHANGELOG
- Protected-token skills refused (e.g. modify_core)

## Verify (PC)
- engine.status OK
- dry-run add_skill OK
- real add_skill soup_phase3_probe → change_id chg_20260922T114954Z_05656294
- backup: self_improve/backups/skills.json.chg_20260922T114954Z_05656294.bak
- cockpit _tool_self_improve status success
- sealed file hashes unchanged vs pre-deploy baseline

## Ceiling
Local machine only. No cloud/soul mutation. PSC still Judge-gated elsewhere.
