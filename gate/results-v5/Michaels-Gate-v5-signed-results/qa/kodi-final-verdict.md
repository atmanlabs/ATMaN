# v5 candidate final verdict — WEEBOH DELEGATED LOCAL QA (filed under the requested name kodi-final-verdict.md; author is Weeboh, not Kodi)
Date: 2026-11-05/06 ET. Scope: isolated, offline, no network/release/third party. The sealed candidate and frozen v3/v4 were not modified.

## Verdict: CANDIDATE VERIFIED LOCALLY — DESIGN WALL at A4 (not GREEN)
- F1 (immutable): 2 failures — A4 (drift5 FRR 0.0686 [0.0672,0.0699] > 0.05) and A6 (bulk dilution 0.391 > 0.30). Matches expectation.
- F2: only A4 fails (same 0.0686 CI; holdout5 0.0427 [0.0415,0.0438] passes); A1–A3, A5–A9 pass. Matches expectation.
- Read directly from artifacts/q8F1_results.json and q8F2_results.json acceptance_F_metrics, not only from the report.

## Phase 1 (static, read-only)
- Candidate: 167 files, 190M (189M = reference-model/artifacts/v3_inherited). Tar: 167 files, contents identical to the tree, no absolute or ../ paths.
- No symlinks, hidden files or empty dirs. FILES.sha256 lists 164 files; the only unlisted files are the manifest itself and its 2 signatures (expected). No absolute or ../ entries.
- verify_static.py: STATIC VERIFY PASS (11/11). It is non-mutating (read-only opens).
- Ed25519 FILES.sha256.sig (test-log key) and PACKET.sig (distinct packet key) both verify. Public keys only; SYNTHETIC, nonproduction.
- F1/F2 IMPL registrations match.
- Network/mutation audit: no socket/urllib/http/subprocess in runnable v5 code. Writes go only to node dirs and artifacts in cwd.
  - crew-evidence/crimson-repro/run_all.py uses subprocess for local scripts; replay does not invoke it.
- Inherited evidence: inherited/v4/reference-model matches frozen /workspace/michaels-gate-v4/reference-model (differences: .git, __pycache__, and v3_inherited, which is relocated). v3_inherited is byte-identical to v4's copy.
  - GAP: inherited/v3/sealed-package-sha256.txt references a CoS attachment zip outside the candidate, which I did not rehash.

## Phase 2 (replay, disposable copy)
Command: `cp -a candidate /tmp/wgqa.j7tn/c; cd /tmp/wgqa.j7tn/c && env -u *_proxy unshare -rn ./replay.sh` (network namespace with no interfaces).
Environment: Python 3.13.5, numpy 2.5.4, cryptography 43.0.0, matching SBOM.
Start 23:59:44 EST, end 00:02:54 EST, exit 0. Static PASS; 79 tests OK (75.5s); "REPLAY: F2 results reproduced exactly (timings excluded)".

## Integrity before/after
- FILES.sha256: fa3ee742c90d05bda5bd58a4e6d676e186a3b30791e9ab7a59fcfb6352012f83
- Archive tar: a181ae513df3b8ca9bc81fa6524e6f2988b32d2fdefb81cee8f493f747e7f1d4
- Full tree hash list: f52eea3d…37f2. Byte-identical before and after replay. Archive and seal unchanged.

## Blockers
- Candidate blockers: none for packaging/reproducibility. A4 is a design wall, honestly reported.
- Env gaps: none.
- Not established: production crypto, real network/hardware, independent external review.

## QA notes manifest (/workspace/v5-qa-weeboh)
fae2a8b9522eabe408742c9d14edf948da8430fd6a0228c8364202a05e0a5a64  before.txt
f52eea3d80a4ab5609d8a7d981228711c2f432d45a37201e74e99a003d2137f2  tree-before.sha256
f52eea3d80a4ab5609d8a7d981228711c2f432d45a37201e74e99a003d2137f2  tree-after.sha256
7fb8a7bff03a5e8f29bb2f11a055e859c02401ca3cd06733afb1593fcca2429a  replay.log
