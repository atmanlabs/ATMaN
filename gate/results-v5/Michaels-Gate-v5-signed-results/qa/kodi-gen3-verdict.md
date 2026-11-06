# Kodi — gen3 independent cap audit (local synthetic research only)
Date: 2026-11-06, approximately 01:42–01:48 EST.

## Separate verdicts
- **Packaging integrity: PASS.** No unresolved package-integrity blocker found.
- **Retained R3 replay evidence: PASS, independently compared against actual retained bytes.** This is not a claim that I personally reran the full v3/v4/F1/F2 evaluations in this audit.
- **Empirical acceptance: DESIGN WALL, NOT GREEN.** F1 still fails A4/A6; F2 still fails A4 only. Production/security claims remain GAP. No pilot, publication, distribution, deployment or activation approval.

## Identity, coverage, archive
- Sealed tree: `/workspace/michaels-gate-v5-candidate-gen3/`.
- Tar: `/workspace/michaels-gate-v5-candidate-gen3.tar`, 385,832,960 bytes; SHA256 **e353e9bc3bcfe5d40b36f0c8837ef6b180d28ce4e450ac76d46aef8d456088aa**.
- Its external `.tar.sha256` names the actual tar basename and matches the actual bytes. An impossible self-hash inside the tar was neither required nor claimed.
- `FILES.sha256`: exactly **347 unique entries**, all independently hash-checked; all **350 delivered files** covered except the expected envelope (`FILES.sha256`, `FILES.sha256.sig`, `PACKET.sig`). Both signatures verify with distinct synthetic test-log/packet public keys. Reports, HANDOFFs, full source/corpora/protocol/logs and R3 evidence are covered.
- Tar: 396 entries = 348 regular files, 46 directories, 2 hardlinks. No absolute/traversal/duplicate member paths, symlinks or special devices. Both disclosed hardlinks are inherited `q8_corpora.npz` copies targeting the in-package regular corpus file.
- Full extraction retained under receipts `tar-extract/`; all file bytes and directory paths equal the original. Independent hash comparison and literal `diff --recursive --no-dereference` both pass (diff exit 0, empty stdout). All three delivered NPZ/ZIP containers pass CRC checks; no separate ZIP is shipped inside the candidate.
- Full reference-model evidence is **199,147,262 logical bytes (~189.92 MiB)**; inherited frozen corpus copies are present and identical. History bundle additionally carries 185,370,055 bytes. Logical whole-tree size is larger because hardlinked corpus paths are counted repeatedly.
- No delivered `*.key`/private PEM blocks; static raw-key checks pass; no `.key` paths in any of the 10 bundled commits. Synthetic/nonproduction public-key notices are present; these signatures establish local artifact consistency, not external trust or production key custody.
- Historical absolute manifests were checked through their actual signed basenames, including `owner-v4-ruling.md`, `owner-v4-oryn-trace.md`, and `distribution-proposal.md`; no invented basename patterns. Verbatim R3 scripts retain historical absolute paths as provenance, not portable entry points. The original v3 attachment ZIP is expressly omitted; its six shipped documents verify against `verification.json`.

## History and preexecution ordering
Own packaged checks plus a separate local-only bundle clone and `git fsck --full` verified:
`ed03799` prereg → `e125422` F1 FREEZE → `572a4fe` F1 IMPL → `9f4845a` F1 eval → `921708a` F2 IMPL → `daf5430` F2 eval → `fa55512` gen2 packaging → **75addf80c1c39db7923c0dc65c718f86048dfc6b** R3 preexec → **33eb5e3447e966796b7113af126f800db98353e9** R3 execution/tip.
- Repository root commit is ed0379914bd56b33da97be00820b40893fb71143. F1 freeze tree is 90682e75709ddfc84ca388c69e6e7faf3fc09bcb.
- Shipped tip tree **3fe99a99b6938c626342a3380ecf5bdd8f01969b** equals SEAL.json and all 225 shipped reference-model blobs.
- Actual freeze hashes match the freeze tree; implementation registrations match their committed trees; results are absent at implementation locks and equal the shipped originals at evaluation commits. Inherited frozen files are byte-identical at prereg, freeze and final tip.
- `REPRO-STAGE-R3.md` exists unchanged at 75addf8; fresh F1/F2 results are absent there and committed at 33eb5e3. Every retained R3 artifact equals its execution-commit blob; `artifacts/R3.sha256` checks all 14 actual paths.
- R3 changes are receipts/crew snapshot plus append-only report/HANDOFF addenda, not algorithm/spec/corpus/threshold/original-result changes. F1/F2 original JSON bytes and implementation locks remain unchanged.
- Limits: ancestry/content establish ordering, not trusted wall-clock chronology. The disclosed F1 spec/gate changes occurred after corpus FREEZE but before F1 IMPL/evaluation; 26 historical pyc paths remain in old history, not the shipped tip.

## Actual retained replay comparison (not report prose)
I read `run_r3.sh`, `compare_r3.py`, both inherited `verify.sh` scripts, logs and retained payloads. I did **not** execute the old comparator with its stale absolute paths. Own new `compare_retained.py` rejects duplicate JSON keys, checks complete type-sensitive JSON, and excludes **only top-level measured `runtime_s`**. Its only detected differing field in each pair is `$.runtime_s`; every other field, including `registered_at`, is exact. Both embedded `frozen`/`impl` objects and every registered source hash match the shipped registrations.

| Payload | Original SHA256 | Retained fresh SHA256 |
|---|---|---|
| F1 | `3c4365d61042053f9835e05a9e6ad4baecb7fb4223e9ffbc570fca2571b29f90` | `dd64238dc5a323f19447d1726ddbb9fb99308df8b4f03143198dde17c75b3c1b` |
| F2 | `3d2c90d9fd4b2435850d452938481aa4cb1436e47b7dab65eae66ef667474bc0` | `6c7a2572fc34e9e3a7bd310a639b6b33d0e06e5f42099b4052e4b88577afa9c9` |

F1 registered_at is 2026-11-05 23:38:59 EST; F2 is 23:47:11 EST, exactly equal across original/fresh/registration. `runtime_s` was declared at gen2 packaging and before R3 execution, not preregistered for the original F1/F2 experiments.

Retained R3 logs record these commands on a disposable gen2 extraction, 00:51:22–01:20:07 EST, all exit 0:
- v3 `./verify.sh`: battery 20/20, regressions 11/11, Q8 results equality and bundle signatures.
- v4 `./verify.sh`: 20 battery + 12 regressions + 7 trace regressions, D/E equality, both GREEN false, bundle signatures. Its old E comparator excludes `cost_resolve_us_mean_mean`; **this exclusion is not applied to F1/F2**.
- `python3 -m unittest discover -s tests -t .`: 79 OK; `python3 q8F.py`; `python3 q8F2.py`.
I additionally compared retained v3/v4 fresh payloads against originals using the precise comparison scopes in their shipped verify.sh scripts. All match. Logs are retained synthetic evidence, not independent proof that every historical command occurred as stated.

Own limited dynamic checks on the extracted disposable copy: **79 tests OK (6.520s)** plus actual v3 and v4 `verify-bundle` commands exit 0. Full old batteries and F1/F2 generation were **not personally rerun** in this incremental audit.

## Acceptance read directly from original and retained JSON
- F1: A4 and A6 fail (A6 bulk<=0.30 false); all other listed acceptance criteria pass.
- F2: only A4 fails. Drift5 FRR **0.0685725922**, CI **[0.0671916634, 0.0698901418]**, exceeds 0.05. Holdout FRR 0.0426672046, CI [0.0414803380, 0.0438003359], passes. DESIGN WALL remains; reproducible failure is not safety success.

## Exact execution receipts and honest harness notes
Unique receipt root: `/workspace/michaels-gate-v5/crew/kodi-scratch/kodi-gen3-independent/`.
Every check has its own `.command.json` (argv/cwd/start EST/environment/exit/stdout hash) and full stdout, with full before/after manifests of sealed tree, tar, external tar digest, and both prior verdicts. Source scripts are retained there. All commands ran locally; checks used `unshare -rn`, Python `-B`, `PYTHONDONTWRITEBYTECODE=1`, and scratch TMPDIR. Actual namespace interface check shows only loopback; host-mounted sysfs interface names are not namespace state. Versions: Python 3.13.5, numpy 2.5.4, cryptography 43.0.0, git 2.47.3; no installs/fetches.

Principal actual commands: `unshare -rn python3 -B verify_static.py`; `unshare -rn python3 -B verify_history.py`; own comparator/history/archive supplement scripts; `unshare -rn diff --recursive --no-dereference TREE EXTRACTED`; disposable `unshare -rn python3 -B -m unittest discover -s tests -t .`; `unshare -rn python3 -B run_battery.py verify-bundle`; `unshare -rn python3 -B run_v4.py verify-bundle`. Exact absolute argv/cwd are in the command receipts.

| Stdout receipt | Exit | SHA256 |
|---|---:|---|
| `static.stdout` | 0 | `4084c5ee38206bb36ffb6e2831d49cb26237c0f134f7df72f10070f9962a7a53` |
| `history.stdout` | 0 | `9188a4f731c58e73efd0850c47c6bed347be03ffc5deba855c212c8a79d665f2` |
| `independent-retained-compare.stdout` | 0 | `e2bad43bc8fab456bdcc62f80e6c5e6f16b76d1b506f0c22dab95acc97d985c2` |
| `history-clarification.stdout` | 0 | `1fb85d6753f0aa520aceda1da13263dc542b53c95756530a0cd3981a7090ebb5` |
| `supplement-v2.stdout` | 0 | `f7d3537d743906e662d82c0acf092b282b74adc92b7412b0e525c408467c3495` |
| `final-supplement.stdout` | 0 | `dcad9f44b7aa6f86bfc77c6b5b124a859c6ad6128d4e3332c0dbbce272802f65` |
| `tar-diff.stdout` | 0 | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `disposable-unit.stdout` | 0 | `ee5f3fd26acf95ff33a76e6e73a284a00a4386c2564fa257e407e4b75324e70c` |
| `disposable-v3-bundle.stdout` | 0 | `832ad3f689285e784314da6bf7f080192fef255d2be182450106feb8be9c5d9d` |
| `disposable-v4-bundle.stdout` | 0 | `c6e0197541bad996362442f36ecc21cc863a354fa201ed0b0234d0d11518364e` |

Preserved unsuccessful **audit-harness** checks, not hidden or mistaken for package failures:
1. `archive` exit 1: Python safe extraction strips group-write from six inherited documents (0660→0640). Supplemental inspection proves actual archived modes equal sealed source; content comparison and literal diff pass. No artifact fix needed.
2. `independent-r3-history` exit 1: my initial predicate allowed only `artifacts/R3/`, wrongly rejecting disclosed crew receipts and append-only documentation. Full diff retained; `history-clarification` verifies the actual allowed changes, unchanged implementations/results and append-only addenda. No source edits or failed results were waived.
3. `supplement` exit 1: my environment probe unnecessarily imported absent scipy, which is **not a declared dependency**. `supplement-v2` uses only declared numpy/cryptography and passes; nothing installed.
Outer harness scripts print results without propagating inner exit codes; the `.command.json` inner exit values above are authoritative, not their outer Shell status.

## Preservation, receipt seal, residual scope
- Original 353 records (350 candidate files + tar + two previous reports) remain exactly identical. External digest was added to the monitored set before verification, giving 354 final records. All 26 per-command manifests are identical, including that sidecar.
- `before.json` SHA256 f789e8194e18c42c3a5b8368593c5f1b104754d97c369d5eeaf3068769d29c2e.
- `final-originals.json` SHA256 ba78633ae1ddb50e3c1047b44cc73936fa1a392323e176e2719c9328df3f5636. `preservation.json` records comparisons.
- `RECEIPTS.sha256` indexes 74 new top-level receipt/script files; SHA256 **e15c8a2c3f5463da1a938790aee917ff89b3e1c75c39d34ce86591fa19f0935f**. Disposable extraction/local bundle clone are supplemental scratch, not independently sealed originals. `REPORT.sha256` separately hashes this report, avoiding recursive self-hashing.
- Earlier Kodi verdicts/receipts and sealed generations were not edited. The earlier `kodi-final-verdict.md` is Weeboh-authored per its own header; no authorship or prior-verdict correction was written over it.
- No production crypto assurance, live network/hardware validation, outside review or operator/deployment readiness is established. Existing legal/consent/no-release restrictions remain intact.
