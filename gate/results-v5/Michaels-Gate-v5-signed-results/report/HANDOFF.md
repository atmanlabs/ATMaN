# v5 HANDOFF (reference-model)
Status (as first written, at F2 seal): **CANDIDATE, pending Kodi independent verification.** *Current (2026-11-06): gen1 FAIL; gen2 PASS (Kodi); gen3 PASS (Kodi, pre-final-text); gen4 PENDING its own Kodi verification.* WALL at A4 (inherited residual floor); 8 of 9 criteria pass at F2. Not flawless, not production.
- Report: `report.md`. Results: `artifacts/q8F1_results.json` (immutable F1) and `artifacts/q8F2_results.json`. Registrations: `artifacts/F1_FROZEN.json`, `F1_IMPL.json`, `F2_IMPL.json`. Verdicts: `artifacts/F1_VERDICT.md`.
- Specs: `V5-SPEC.md` (F1, §7 Weeboh, §8 Crimson) and `V5-F2-SPEC.md`.
- Runners: `q8F.py` (F1) and `q8F2.py` (F2). Implementation: `gate/gate5.py` (F1), `gate/gate6.py` (F2), `gate/union5.py`.
- Verify: `python3 verify_static.py` (read-only) and `./replay.sh` (replays in a temporary copy). Both are at the package root.
- **Next:** an Owner ruling on A4 (residual property or drift bound), then any v6. Every change requires a new pre-registered stage.
- Disclosed potholes:
  - Unit tests and harness smoke used out-of-corpus trial t=999 before each registration.
  - Both F1 and F2 ran the full suite concurrently with Q8, so the timing fields are noisy and excluded from replay.
  - Crew evidence copies retain the authors' absolute paths verbatim.

## Packaging addendum (generation 2, 2026-11-06)
At gen2 sealing, prior to Kodi's subsequent PASS: Packaging only, see `PACKAGING-RECEIPT.md`. Results and verdict are unchanged: WALL at A4. Generation 1 packaging FAIL (Kodi); generation 2 pending Kodi independent verification.
*Supersession note (2026-11-06):* Kodi later PASSED generation 2 (see `crew-evidence/round3-full-20261106T0052/kodi-gen2-verdict.md`). R3 receipts are in `R3-RECEIPT.md`. Kodi later PASSED gen3 (pre-final-text; packaging + retained R3 evidence; `crew-evidence/round5-kodi-gen3/kodi-gen3-verdict.md`). Gen4 (text-only) is PENDING its own Kodi verification.

## R3 reproducibility addendum (2026-11-06)
The full inherited v3/v4 batteries and the F1/F2 reruns reproduced the shipped results. Only the top-level runtime_s differs. See `R3-RECEIPT.md`. Gen2 packaging PASS is Kodi's independent result; gen1 was FAIL. No algorithm change. Still a WALL at A4.
