# Reference model: HANDOFF
- State: **DESIGN WALL at Q8 (Judge)**. Battery items 1, 3, 4, 5 and 6 are GREEN. See report.md.
- Verify: `cd /workspace/michaels-gate-v3/reference-model && ./verify.sh`
- Resume: read `git log`, then report.md. The frozen battery is `tests/test_battery.py` and `tests/fixtures.py`; its hashes are in `artifacts/FROZEN_BATTERY.sha256`. Do not edit those files. Q8 corpora and protocol are frozen in `artifacts/Q8_FROZEN.json`.
- After any implementation fix: add a regression to `tests/test_regressions.py`, run `python3 run_battery.py`, and commit.
- Spec-level changes (Judge reference, thresholds, registry depth) go only through the v4 proposal in report.md.
- All keys are synthetic: `artifacts/keys/` (test-log signer). The authority keys are regenerated fresh in each test run.
