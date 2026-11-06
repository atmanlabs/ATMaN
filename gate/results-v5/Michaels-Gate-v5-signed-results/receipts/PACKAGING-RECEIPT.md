# Packaging receipt: candidate generation 2 (packaging only; no protocol, hull, threshold, corpus, algorithm, or experiment change)
Date: 2026-11-06 EST. F1 (9f4845a) and F2 (daf5430) result bytes are unchanged. No F3 is needed because no algorithm changed.

## Status
- Overall: **DESIGN WALL at A4** (unchanged).
- At gen2 sealing, prior to Kodi's subsequent PASS: Packaging: **FAIL for generation 1** (Kodi receipts: inherited v4 verify-bundle exits 1 because 3 signed files are missing). **Generation 2 is PENDING Kodi's independent verification.** Our own QA is not independent verification.
- **Current status (superseding the line above, 2026-11-06):** Packaging: **generation 1 FAIL**; **generation 2 PASS** per Kodi's local independent verdict (copy in `reference-model/crew-evidence/round3-full-20261106T0052/kodi-gen2-verdict.md`), with its stated GAPs. **Generation 3 (pre-final-text): gen3 PASS per Kodi's independent audit (`crew-evidence/round5-kodi-gen3/kodi-gen3-verdict.md`, sha256 12c32e85…): packaging integrity PASS, and retained R3 replay evidence PASS when compared against the actual retained bytes. This was not a personal rerun of v3/v4/F1/F2, and it covers the PRE-FINAL-TEXT gen3 only. Empirical result: DESIGN WALL, not GREEN.** R3 full inherited-battery and fresh-comparison receipts are recorded in `R3-RECEIPT.md`; they do not substitute for gen3 review and do not change the technical WALL at A4. Generation 4 (Counsel's five text corrections only; no model, protocol, corpus or result change) is PENDING its own fresh Kodi verification. No earlier verdict carries over to it, and gen4 is not independently replayed.
- `crew/kodi-final-verdict.md` is byte-identical to `crew/weeboh-delegated-qa.md`. Its author is Weeboh, and it did not run the inherited verifier. Its "PASS" does not qualify the FAIL. Both are preserved read-only in crew-evidence/round2-*.

## Fixes in generation 2
1. **Inherited v4 bundle:** `inherited/v4/reference-model/artifacts/v3_inherited/` now ships all 5 v4 originals, byte-identical (FROZEN_BATTERY.sha256, Q8_FROZEN.json, q8_corpora.npz; the other two were already there in v4). The v4 originals are unchanged.
2. **History:** `history.bundle` carries the full git history; `verify_history.py` proves ancestry, lock ordering, and tree identity.
   - **Exposed difference:** the F1 FREEZE commit e125422 pinned V5-SPEC.md sha256 6737e7d3… and gate5.py ddb17e1f…. Both changed before any evaluation, in F1 IMPL 572a4fe (Crimson §8 per-origin quota), and F1_IMPL.json pins the new bytes. The corpora did not change.
   - **History defect, genuine but benign:** commits up to daf5430 tracked 26 `__pycache__/*.pyc` blobs. They were untracked in a later commit; nothing was rewritten.
   - Commit dates come from a local synthetic identity and do not prove wall-clock time.
3. **Keys:** generation 1's NOTICE said "only public keys ship". That was **inaccurate**: `inherited/v4/.../keys/SYNTHETIC-v4-test-log-signing.key` (a synthetic v4 test key) was shipped.
   - Generation 2 ships no private keys, and the static verifier checks this.
   - The v3/v4 synthetic test private keys stay only at their original isolated v3/v4 locations.
   - Their sealed evidence is still checked through public keys and signed manifests.
4. **Paths:** `PATHS.md` maps the original absolute paths to package paths and hashes. The frozen manifests still contain their absolute paths unchanged; those are provenance only, and verification maps them by basename at boundaries.
5. **Replay:** the only field excluded is `runtime_s`, a measured wall-clock timing. That exclusion is declared here at packaging, and F1/F2 did not pre-register it. `registered_at` and every other field must match exactly.
   - Replay covers F1 and F2, the full test suite, the inherited v4 and v3 `verify-bundle`, the static check, and the history check.
6. **Static verification:**
   - It is read-only and writes no bytecode.
   - ResourceWarnings from the frozen modules are silenced, both in static verification and in replay's test run (`PYTHONWARNINGS`).
   - It regenerates the v3 and v5 corpora from their frozen generators and compares them exactly to the frozen arrays and hashes.
7. **Crew evidence:** Kodi's and Weeboh's final files are copied read-only. The crew originals are untouched.
