# Kodi: generation-2 independent verdict (local QA only, no network, no activation)
Date: 2026-11-06, 00:15–00:45 EST. Receipts: crew/kodi-scratch/gen2-verification/ (RECEIPTS.sha256 indexes them).

## Verdict
- **Packaging/reproducibility: PASS**, with the gaps listed below.
- **Technical result: DESIGN WALL, not GREEN.**
  - F1 fails A4 (drift5 FRR 0.0685726, CI [0.06719, 0.06989], above 0.05) and A6 (bulk ≤ 0.30 is false).
  - F2 fails only A4 (same drift5 value). holdout5 is 0.04267 and passes. A1–A3 and A5–A9 pass.
  - These values were read directly from the signed results JSON (p1-acceptance.txt).
- Generation 1's packaging FAIL stands for generation 1. Generation 2 clears its blockers: the 3 missing v4 corpus files now ship; a key file shipped in gen1 does not ship now; and history proving the freeze is included.

## Integrity
- Tar sha256: 7d0264ebc2b61b571b1e9963eee76a56647658cf957b8a3547c8ab99b5f4ac9c
- Tree hash list: pre-tree.sha256 (248 files), sha256 383372d1….
- Tree, metadata (mode/size/mtime/links), tar and kodi-final-verdict.md were all byte-identical before and after every step. The post-* files are identical to the pre-* files.
- The tar extracts with diff -r equal to the tree.
  - It has 246 regular files and 2 hard links (q8_corpora.npz, as disclosed).
  - It has no absolute or ../ entries and no symlinks or .pyc files.
- The package records no archive digest for itself. That is expected: a tar cannot contain its own hash. The digest above is the external receipt.
- FILES.sha256 has 245 entries and passes sha256 -c. The only unlisted files are FILES.sha256, its .sig and PACKET.sig.
  - The list covers report.md, both HANDOFFs, q8F1/q8F2 results, README, PACKAGING-RECEIPT, replay.sh and the verifiers.

## Phase 1 (pristine, read-only)
1. `PYTHONDONTWRITEBYTECODE=1 python3 -B verify_static.py`: exit 0, STATIC VERIFY: PASS (p1-verify_static.txt). It checked:
   - the signatures;
   - that no private keys ship;
   - the inherited v4 bundle (37 files) and v3 bundle (MANIFEST.sig, 20 files);
   - the manifests, with absolute historical paths mapped by actual basename;
   - that registered_at is embedded exactly in both results files;
   - that the v3 and v5 corpora regenerate exactly from their frozen generators.
2. `python3 -B verify_history.py`: exit 0, HISTORY VERIFY: PASS (p1-verify_history.txt). I also ran my own `git clone` and `git log` (p1-git-log.txt):
   - Commit chain: ed03799 prereg → e125422 F1 FREEZE (tree 90682e75) → 572a4fe F1 IMPL (registered_at 23:38:59) → 9f4845a F1 eval → 921708a F2 IMPL (23:47:11) → daf5430 F2 eval → tip fa55512.
   - The tip tree is 4c9f3974, which equals SEAL.json and the shipped reference-model/.
   - The results files are absent at their lock commits.
3. Key check:
   - No \*.key files and no PRIVATE KEY blocks anywhere.
   - keys/ holds 2 SYNTHETIC .pub files with a NONPRODUCTION NOTICE, and the gen1 key error is corrected.
   - report.md is labeled SYNTHETIC TEST, NONPRODUCTION.

## Phase 2 (disposable copy, offline)
- Copy: `cp -a gen2 kodi-scratch/gen2-verification/disposable` (deleted after the run).
- Command: `env -u *_proxy unshare -rn ./replay.sh`. Only the loopback interface existed. Ran 00:21–00:39 EST, exit 0 (p2-replay.txt).
- Environment: p2-env.txt.
- Steps executed, all passing:
  - static check;
  - history check;
  - inherited v4 `run_v4.py verify-bundle` ("signature OK; all hashes match");
  - inherited v3 `run_battery.py verify-bundle` (OK);
  - unittest: 79 tests OK;
  - F1 rerun (q8F.py) and F2 rerun (q8F2.py), each "reproduced exactly (incl. registered_at; runtime_s excluded)".
- I inspected the comparator: it checks full JSON equality after removing only the top-level `runtime_s`, and `registered_at` is compared exactly. `cost_resolve_us_mean_mean` does not appear in either results file, so nothing else is excluded.

## Gaps / not proven
- INHERITED_FULL=1 was **not run**, so the full old v3/v4 verify.sh batteries were not re-executed. Only their verify-bundle checks ran.
- The fresh F1/F2 payloads lived in replay's mktemp directory and were deleted on exit. Equality comes from replay's own comparator, which I inspected; I did not run a separate diff that kept the fresh bytes.
- Freeze-before-eval is proven by **commit ancestry and content hashes only**. The commit dates come from a synthetic local identity and do not prove wall-clock time.
- V5-SPEC.md, gate5.py, q8F.py and a test changed after F1 FREEZE but before the F1 IMPL lock. This is disclosed. The corpora did not change.
- 26 .pyc blobs are tracked in history up to daf5430. This is disclosed and benign.
- The original v3 attachment zip is not shipped and was not rehashed (provenance only).
- runtime_s was declared at packaging, not pre-registered in F1/F2.
- Not established: production crypto, real network/hardware, external review.
- Note: the earlier kodi-final-verdict.md was authored by Weeboh because of a filename collision. It was left unchanged (sha256 receipt in pre/post-orig-verdict.sha256).
