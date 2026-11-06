# Kodi findings — Michael's Gate v5 artifact / collation QA
**Lane:** Kodi (local artifact packaging, replay verification, hashes, prohibited-content audit)  
**When:** 2026-11-05 23:33 America/New_York (ET)  
**Authorization:** Mike → CoS v5 build/fix/batter/check/seal/rerun; HANDOFF + COLLATION.  
**Scope obeyed:** read-only on frozen v3/v4 trees; wrote only this file and `crew/kodi-scratch/*`. No invented fixtures, no network, no new keys, no replacement reports, no implementation edits.

## Verdict (personally verified)
| Claim | Grade | Basis |
|---|---|---|
| v3 sealed design package document hashes match `verification.json` / `MANIFEST.md` | **PASS** | `sha256sum` + JSON cross-check |
| v4 ruling / frozen-spec / addendum hashes match `MANIFEST*.sha256` and `ruling/SHA256SUMS` | **PASS** | `sha256sum -c` |
| v5 ruling `distribution-proposal.md` hash | **PASS** | `sha256sum -c ruling/SHA256SUMS` |
| v5 copied v4 source digest list `artifacts/inherited/V4_SOURCE.sha256` | **PASS** | matches both v4 and v5 trees |
| v3/v4 inherited Q8 corpora identity (`q8_corpora.npz`) | **PASS** | identical sha256 `823d07b9…ed59` across v3, v4, v5 |
| Current worktree signed bundle (v3 and v4) | **PASS** | `python3 run_battery.py verify-bundle` / `python3 run_v4.py verify-bundle` |
| HEAD commit signed bundle internal consistency (v3 and v4) | **PASS** | every MANIFEST file hash at HEAD matches `git show HEAD:<file>`; HEAD sig verifies HEAD MANIFEST |
| Acceptance numbers HEAD vs dirty worktree (v3 Q8 results; v4 D/E acceptance) | **PASS** (semantic) | results payloads equal after excluding wall-clock `runtime_s` / `cost_resolve_us_mean_mean` (as `verify.sh` already strips for E) |
| Independent compact package ready for third-party fresh-location replay of v5 | **FAIL / GAP** | v5 missing runner, verify, keys, bundle, F1 freeze, report — see §Gaps |
| Dirty uncommitted re-sign of v3/v4 after final commit | **GAP** (packaging hygiene) | worktrees dirty; two valid signed generations; HEAD ≠ WT bytes |
| Prohibited grown-state / personal / credential content in trees | **PASS** (scan) with **WATCH** on synthetic private keys present + world-readable | see §Prohibited |
| Production crypto / live network / uniqueness / release readiness | **GAP** (by design; not claimed) | HANDOFF fences |

**Not graded as replay:** reading `report.md` prose or log text alone. Those are cited only as pointers. Personal verification below is limited to hash/signature checks actually executed.

---

## Methods run (exact)
Working directory checks used absolute paths under `/workspace`. Scratch receipts: `crew/kodi-scratch/`.

1. Read `/workspace/michaels-gate-v5/HANDOFF.md`, `crew/COLLATION.md`, then identified prior evidence:
   - `/workspace/michaels-gate-v3/HANDOFF.md`, `reference-model/{HANDOFF.md,HANDOFF.json,report.md,verify.sh}`
   - `/workspace/michaels-gate-v3/michaels-gate-sealed-package-v3/*`, `sealed-package-sha256.txt`, `verification.json`
   - `/workspace/michaels-gate-v4/HANDOFF.md`, `ruling/*`, `reference-model/{HANDOFF.md,report.md,verify.sh,MANIFEST*.sha256,...}`
2. Full inventory via `find` (no symlinks found under v3/v4/v5 package trees).
3. Hash checks:
   - v3 sealed docs vs `verification.json` → ALL PASS
   - `cd .../v4/reference-model && sha256sum -c MANIFEST.sha256 MANIFEST-E.sha256 artifacts/v3_inherited/FROZEN_BATTERY.sha256` + ruling lines → OK
   - v5 `MANIFEST*.sha256`, `ruling/SHA256SUMS`, `artifacts/inherited/V4_SOURCE.sha256`, weeboh `PREREG.sha256` → OK
   - corpora: `sha256sum` on three `q8_corpora.npz` copies → identical
4. Signature checks (**no battery rerun**; full `./verify.sh` would rewrite results and was **not** run):
   - `cd /workspace/michaels-gate-v3/reference-model && python3 run_battery.py verify-bundle` → `signature OK; all file hashes match`
   - `cd /workspace/michaels-gate-v4/reference-model && python3 run_v4.py verify-bundle` → `signature OK; all hashes match`
5. MANIFEST↔tree: 20/20 v3 files OK; 37/37 v4 files OK. Private keys **not** listed in MANIFEST (verify loads `.pub` from `artifacts/keys/`).
6. Dirty-tree analysis: `git status --porcelain` + HEAD vs WT hashes; q8E diffs are **only** `cost_resolve_us_mean_mean` (+ `runtime_s`); acceptance_D/E and stripped results match.
7. Prohibited-content heuristic scan of 152 text-ish files (skipped `.npz` bodies / `.pyc`); git history name scan for `*key*`.
8. Fresh-location / path audit of `verify.sh` sibling dependencies and absolute path records.
9. Deps probe: Python 3.13.5; `numpy 2.5.4`; `cryptography 43.0.0`. **No** `requirements.txt` / lockfile in any reference-model.

**Explicitly not run (would mutate frozen/result artifacts):** `./verify.sh`, `python3 run_battery.py`, `python3 run_v4.py` (full), any F1 evaluation.

---

## Compact reproducible package checklist (exact)
A compact package that supports **independent** hash+signature verify **and** bit-exact offline replay must include all of the following. Items marked **PRESENT** exist today in the cited tree; **MISSING** blocks fresh replay.

### A. Design / ruling freeze (read-only)
| Item | Path | Status |
|---|---|---|
| v3 sealed design docs + MANIFEST | `/workspace/michaels-gate-v3/michaels-gate-sealed-package-v3/{01..05,MANIFEST}.md` | PRESENT; hashes PASS |
| v3 verification map | `/workspace/michaels-gate-v3/verification.json` | PRESENT |
| v4 owner rulings | `/workspace/michaels-gate-v4/ruling/owner-v4-ruling.md`, `owner-v4-oryn-trace.md` + `SHA256SUMS` | PRESENT; hashes PASS |
| v4 frozen specs | `.../v4/reference-model/{OWNER-RULING,OWNER-ORYN-TRACE,V4-FROZEN-SPEC,V4-E-ADDENDUM}.md` + `MANIFEST*.sha256` | PRESENT |
| v5 F1 pre-reg spec | `/workspace/michaels-gate-v5/reference-model/V5-SPEC.md` | PRESENT (untracked in v5 git); **F1_FROZEN.json MISSING** |
| v5 distribution proposal | `/workspace/michaels-gate-v5/ruling/distribution-proposal.md` | PRESENT; hash PASS |

### B. Full code (reference-model)
| Item | v3 | v4 | v5 |
|---|---|---|---|
| `gate/*.py` | PRESENT | PRESENT | PRESENT (hash-locked via V4_SOURCE) |
| tests (`test_battery`, fixtures, regressions / v4 imprint+trace) | PRESENT | PRESENT | PRESENT |
| Q8 harnesses | `q8.py` | `v3_q8.py`,`q8v4.py`,`q8E.py` | same as v4 copy |
| Runner | `run_battery.py` | `run_v4.py` | **MISSING** (`run_v5.py` / `run_v4.py` absent) |
| `verify.sh` | PRESENT | PRESENT | **MISSING** |
| `report.md` / `results.json` / model `HANDOFF.md` | PRESENT | PRESENT | **MISSING** |
| `diag_posthoc.py` | n/a | PRESENT | **MISSING** |

### C. Actual synthetic corpora + protocols (hashed before results)
| Item | Path / digest | Status |
|---|---|---|
| v3 Q8 corpora blob | `artifacts/q8_corpora.npz` / inherited copy; file sha `823d07b9…`; logical corpora id in `Q8_FROZEN.json` = `561dcb8c…` | PRESENT (~189 MiB) — **must copy**; omission breaks replay |
| v3 Q8 protocol freeze | `artifacts/Q8_FROZEN.json` (protocol sha `7903362f…`) | PRESENT |
| Frozen battery harness digests | `artifacts/FROZEN_BATTERY.sha256` → `tests/test_battery.py`, `tests/fixtures.py` | PRESENT |
| v4 D freeze | `artifacts/V4_FROZEN.json` (drift corpus sha `19229dd9…`, proto4 `87b59fcb…`) | PRESENT in v4 & v5 |
| v4 E freeze | `artifacts/E_FROZEN.json` (E corpus `9024cdec…`, proto_E `464dd0f1…`) | PRESENT in v4 & v5 |
| v5 F1 corpora/protocol freeze | `artifacts/F1_FROZEN.json` (+ generated corpora blobs named therein) | **MISSING** — V5-SPEC §5 requires commit-before-eval |

### D. Logs, signatures, hashes
| Item | Requirement | Status |
|---|---|---|
| Signed MANIFEST | `artifacts/bundle/MANIFEST.json` + `MANIFEST.sig` | v3/v4 PRESENT (WT and HEAD each self-consistent); **v5 MISSING** |
| Bundle logs | v3: `battery.log`,`q8.log`,`regressions.log`; v4: `v3_battery.log`,`v4_regressions.log`,`v4_trace_regressions.log`,`q8v4.log`,`q8E.log` | v3/v4 PRESENT; v5 MISSING |
| Result JSONs | `artifacts/q8*_results.json`, top-level `results.json` | v3/v4 PRESENT; v5 has q8v4/q8E result copies only (no signed bundle wrapping them) |
| Cycle receipts | `artifacts/cycles/*` | v3/v4 PRESENT; optional for minimal replay but required for audit trail |
| Leftover partial | `artifacts/q8E_results.partial.json` | PRESENT in v4 WT; **not** in MANIFEST — exclude from ship or delete before seal |

### E. Environment / dependencies / commands / expected outputs
**Environment (observed here, not pinned in-repo):**
- OS: Linux; Python `3.13.5`
- Third-party: `numpy==2.5.4`, `cryptography==43.0.0`
- Stdlib: `multiprocessing`, `unittest`, `json`, `hashlib`, …
- **GAP:** no `requirements.txt` / lockfile / `pyproject.toml` in v3/v4/v5 reference-model → fresh machine may drift.

**Commands (offline; from package root after layout fix in §Fixes):**

```bash
# v3 — signature+hash only (non-mutating)
cd reference-model && python3 run_battery.py verify-bundle
# expected stdout: signature OK; all file hashes match
# expected exit: 0

# v3 — full bit-exact replay (MUTATES logs/results/signature in place)
./verify.sh
# expected: sha256 checks OK; battery+Q8 rerun; "Q8 results reproduced exactly"; verify-bundle OK
# expected wall time: several minutes; needs ../michaels-gate-sealed-package-v3/01-v3-patch-spec.md

# v4 — signature+hash only
cd reference-model && python3 run_v4.py verify-bundle
# expected: signature OK; all hashes match ; exit 0

# v4 — full replay (MUTATES)
./verify.sh
# expected: MANIFEST*.sha256 + ruling hashes OK; D/E reproduced (E timing field stripped);
#           prints GREEN D = False GREEN E = False (DESIGN WALL)
# needs sibling ../ruling/owner-v4-*.md
```

**Expected acceptance (from signed results; DESIGN WALL, not green):**
- v3: battery 1,3,4,5,6 GREEN; Q8 prediction falsified (design wall).
- v4: D criteria 3 & 4 fail (legit-drift FRR ≈ 0.072, coverage ≈ 0.692); E inherits that wall; Trace P1–P3 pass; verdict DESIGN WALL for D and E.

### F. TEST ONLY / NON-PRODUCTION key labels (conspicuous)
| File | Labels in filename | MANIFEST note | Mode | Issues |
|---|---|---|---|---|
| `.../v3/.../SYNTHETIC-test-log-signing.{key,pub}` | SYNTHETIC + test | `"SYNTHETIC test-log signature; not production crypto"` | `0644` | Private PEM present; world-readable; tracked in git history |
| `.../v4/.../SYNTHETIC-v4-test-log-signing.{key,pub}` | SYNTHETIC + test + v4 | same note | `0644` | same |
| v5 keys | — | — | — | **MISSING** (needed for any new signed v5 bundle) |

**Required packaging text (checklist item for integrator):** every key path and README/NOTICE must say **TEST ONLY / NON-PRODUCTION / SYNTHETIC** in the filename **and** in a top-level `NOTICE` or `KEYS.md`. Prefer shipping **public** half only for verify-only packages; keep private half in a clearly separated `test-keys/` with mode `0600`, or omit private key when only `verify-bundle` is required (verify uses `.pub` only).

---

## Path / access / symlink / copy / fresh-location issues
| Issue | Severity | Detail |
|---|---|---|
| No symlinks in package trees | OK | `find -type l` empty |
| v3 `verify.sh` requires sibling sealed package | HIGH for partial copy | Relative `../michaels-gate-sealed-package-v3/01-v3-patch-spec.md` — copying only `reference-model/` breaks verify |
| v4 `verify.sh` requires sibling `../ruling/owner-v4-*.md` | HIGH for partial copy | Same class of layout coupling |
| `sealed-package-sha256.txt` absolute CoS attachment path | HIGH portability | Records `/home/box/agent-data/agents/7ee04ca8-…/attachments/….zip` — useless on fresh host; zip itself not in tree |
| Ruling `SHA256SUMS` uses absolute `/workspace/...` paths | MED | Works on this box; breaks if checked out elsewhere unless paths rewritten or made relative |
| v3 sealed dir mode `770` / files `660` | MED | Fine for same-group local; may block other UIDs on shared hosts |
| Synthetic private keys mode `644` | MED | Readable by all local users |
| 189 MiB corpora | HIGH copy risk | Easy to drop in incomplete archives; MANIFEST will then FAIL — good, but must be called out in ship instructions |
| Dirty v3/v4 worktrees after verify | HIGH for “which seal?” | Two self-consistent signed generations (HEAD commit vs WT). Independent auditor must pin **commit id or WT digest**, not “the folder” |
| v5 git: 0 commits, all untracked | HIGH | Not a sealed repo yet; `V5-SPEC.md` exists but F1 freeze/runner/bundle absent |
| `__pycache__` / `.partial.json` | LOW | Exclude from compact ship; not in MANIFEST |

---

## Prohibited-content audit
Counsel/no-ship list: grown state, memory snapshots, prompt logs, private keys, credentials, personal/confidential data; include generated outputs and history.

| Class | Result |
|---|---|
| Grown brain / learned weights / memory snapshot **files** | None found by name or payload |
| Prompt logs / chat transcripts as artifacts | None found |
| Real account credentials / cloud keys | None found |
| Personal emails / home paths inside code | None in scanned bodies except the one absolute attachment path in `sealed-package-sha256.txt` |
| Mentions of “grown brain / memory snapshot” in **policy docs** | Present in sealed package / HANDOFF text as **prohibitions** — not data |
| Synthetic test private keys | **Present** in v3/v4 `artifacts/keys/*.key` and **in git history**; labeled SYNTHETIC/test; **not** in MANIFEST file list; required today only for **re-signing**, not for verify |
| Generated outputs | Q8 results/logs are synthetic metrics — OK to ship as lab evidence; must stay labeled non-production |
| History risk | `git log --name-only` shows key files committed; any future public mirror must strip or rotate and document TEST ONLY |

**Grade:** no evidence of real personal data or grown state in these trees (**PASS** for that bar). **WATCH:** private keys in-tree + history; absolute agent path; incomplete v5 seal.

---

## Highest-priority gaps (before independent replay)
1. **v5 is not replayable yet:** missing `run_*.py`, `verify.sh`, `artifacts/keys/`, `artifacts/bundle/{MANIFEST.json,MANIFEST.sig,*.log}`, `artifacts/F1_FROZEN.json` (+ corpora), `report.md`, `results.json`, model `HANDOFF.md`. Copied v4 sources/results alone are **not** a v5 sealed package. → **Integrator** must finish F1 freeze-before-eval, implement, run, sign; **CoS** must not treat current v5 tree as sealed.
2. **Pin the seal generation for v3/v4:** dirty WT vs HEAD both verify but differ in bytes (timing fields + re-sign). → **Integrator/CoS:** either commit the post-verify tree **or** reset WT to HEAD and document the commit hash as the only seal; add `SEALed_COMMIT.txt` with `git rev-parse HEAD` after a clean tree.
3. **Layout for fresh copy:** ship a single archive with fixed relative layout:
   ```
   michaels-gate-vN/
     HANDOFF.md
     ruling/ ...
     michaels-gate-sealed-package-v3/ ...   # when N>=3 verify needs it
     reference-model/ ...
   ```
   Replace absolute paths in `SHA256SUMS` / `sealed-package-sha256.txt` with paths relative to package root. Include the 189 MiB corpora.
4. **Dependency pin:** add `requirements.txt` (at least `numpy`, `cryptography`) with versions; record Python minor.
5. **Key packaging:** conspicuous `TEST ONLY / NON-PRODUCTION / SYNTHETIC` NOTICE; mode `0600` on `.key`; consider verify-only tarball without private key; never call multisignature “production threshold crypto” (already noted in MANIFEST — keep it).
6. **Exclude junk from seal:** `q8E_results.partial.json`, `__pycache__`, dirty uncommitted churn; optionally add `report.md` / `HANDOFF.md` into signed FILES list (currently **unsigned** in v4 `run_v4.py` FILES — report can be swapped without failing verify-bundle).
7. **F1 process gate:** V5-SPEC requires `F1_FROZEN.json` committed **before** any F evaluation. As of this QA, freeze file absent → any F numbers produced without it are automatically **GAP**, not PASS.

---

## Proposed independent replay protocol (for CoS / external auditor)
**Label every result lab-scoped. No network.**

### Phase 0 — receive & inventory
1. Obtain the compact archive + published sha256 of the archive itself (relative path manifest).
2. Extract to a clean directory; confirm relative layout in §Gaps.3.
3. Record: host Python version, `pip freeze` for numpy/cryptography, date ET, archive digest.

### Phase 1 — static (non-mutating) — required before trusting any GREEN/WALL claim
1. `sha256sum -c` on sealed design MANIFEST / `verification.json` / `MANIFEST*.sha256` / ruling SUMS / `F*_FROZEN.json` / corpora digests listed therein.
2. Confirm key filenames contain `SYNTHETIC` and `test` (or read NOTICE). **Do not print private key material.**
3. `python3 run_*.py verify-bundle` (or v5 equivalent). Expect signature OK + all hashes match.
4. Confirm `report.md` / HANDOFF verdict text is either inside the signed MANIFEST or separately hashed; if unsigned, treat prose as **unauthenticated commentary**.
5. Scan for prohibited paths (keys outside `artifacts/keys/`, `*.pem` unnamed, prompt logs, memory snapshots). Fail ship on hits.

### Phase 2 — dynamic replay (optional but required to upgrade from “signed log inspection” to “reproduced”)
1. Copy tree to a disposable workdir (preserve original seal pristine).
2. Run `./verify.sh` once offline.
3. Expect bit-exact match on acceptance payloads (v4 already excludes wall-clock resolve timing).
4. Record PASS/FAIL per criterion; do **not** retune corpora/protocol after seeing output.
5. If replay mutates files, re-run `verify-bundle` on the workdir; compare acceptance to the sealed original.

### Phase 3 — what this protocol does *not* prove
- Production Φ, real threshold crypto, real network/gossip, hardware roots of trust, uniqueness vs incumbents beyond the frozen A/B/C design, or release readiness. Those remain **GAP** even on local GREEN.

---

## Actionable fixes (owner by role)
**Integrator**
- Complete v5 F1: write/hash `artifacts/F1_FROZEN.json` + corpora **before** eval; implement runner/`verify.sh`; produce `report.md`/`results.json`; sign bundle with new `SYNTHETIC-v5-test-log-signing.*` labeled keys.
- Clean or commit v3/v4 dirty verify outputs; pin seal commit; add relative-path SUMS; add `requirements.txt`; drop `.partial.json` from ship; put `report.md` under signature or companion hash file.
- Fix key file modes; add top-level NOTICE for TEST ONLY keys.

**CoS**
- Do not bundle a “v5 sealed” claim until Phase 1 passes on a complete tree.
- When collecting crew receipts, require Kodi Phase-1 checklist IDs (paths + commands + digests), not report quotes alone.
- Keep Counsel no-ship list intact: no grown state, no live network, no publication from this lab.

**Kodi (this lane)**
- Re-run Phase 1 after integrator drops a candidate seal; only then attempt Phase 2 on a copy.
- Still will not invent fixtures or grade design prose as execution PASS.

---

## Scratch receipts (supporting)
All under `/workspace/michaels-gate-v5/crew/kodi-scratch/`:
- `v3-verify-bundle.txt`, `v4-verify-bundle.txt`
- `manifest-tree-check.txt`, `dirty-vs-head.txt`, `q8E-head-wt-diff.txt`, `head-bundle-consistency.txt`
- `v5-gap-inventory.txt`, `fresh-location-issues.txt`
- `prohibited-scan.txt`, `git-history-scan.txt`

---

## Bottom line for CoS
Personally verified: **v3 design package hashes**, **v4 ruling/spec hashes**, **current and HEAD signed bundles**, and **corpora identity** are solid.  
Blocking independent replay of **v5**: incomplete tree (no runner/verify/keys/bundle/F1 freeze).  
Blocking clean audit of **v3/v4**: uncommitted re-sign dirty trees and absolute/sibling path fragility in the ship layout.  
No prohibited grown/personal payload found; synthetic private keys need tighter labeling/permissions before any wider share.
