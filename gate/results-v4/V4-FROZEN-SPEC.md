# Michael's Gate v4: frozen implementation choices and pre-registered protocol (arm D, the imprint Judge)

Governing ruling: `OWNER-RULING.md` (sha256 f3fdfef970a5d544560151819847d9b0b84a58fb04113c5342d92d752c0e8027), frozen verbatim.
This file was frozen and committed **before any arm was evaluated on any v4 corpus**. Every constant below is either fixed a priori
or derived by the stated procedure from **clean calibration data only**. Attack results and drift-corpus results are never used to set anything.
The work is a synthetic, isolated reference model. It is not production security and makes no claim of uniqueness.

## 0. What is inherited unchanged (v3)
- Reviewed v3 mechanisms are copied byte-for-byte into `gate/` from the v3 reference model at commit a3a33c0: crypto, epochlog, node, quorum, genesis, geometry. The v3 frozen battery files are copied with hashes checked (`artifacts/v3_inherited/FROZEN_BATTERY.sha256`). Nothing in /workspace/michaels-gate-v3 is modified.
- The hull is unchanged: anchor cap 25°, path budget B = 180° per window of 1000 admissions (budget exhaustion → HOLDING), residual energy cap ρ_E = 0.02 against the 16-dimensional anchored reference subspace, and a bounded mixer with capacity 64.
- The v3 Q8 corpora and protocol are reused exactly (`artifacts/v3_inherited/q8_corpora.npz`, corpora sha256 561dcb8c…; protocol sha256 7903362f…). This includes the same families, trials, events, attack cadence, Guardian delay and bootstrap.
- The v3 state-relative step score is **retired for arm D**. Arms A, B and C are kept exactly as in v3 as comparators.

## 1. Profiles
- **Imprint Ĵ (sealed):** `Imprint` = {mu (unit 256-vector), P (256×16 PCA basis), var (16 variances), qT (0.995 quantile of T² on the fit sample), judge_config (thr0_ratio, scan constants), hash}. All arrays are read-only. The hash covers every field.
- **Genesis imprint fit sample:** the v3 `cal_clean` corpus (60 × 600 clean items). This is the *same* sample that fits incumbent C, so D and C get the same information. There is no ground-truth oracle.
- **Faithful reference profile vs live memory:** the imprint is a *distribution profile* fitted on a certified clean sample. It is never the live memory centroid, and it never reads or tracks live state.
- **T² imprint score:** s(v) = Σ_i ((v̂ − mu)·P_i)² / var_i / qT, with v̂ = v/‖v‖. The Judge score is resonance against the faithful reference, whitened.
- **Judge operating state (reflection of the Judge):** the live scorer parameters actually in use (mu, P, var, qT, thr_eff, config), plus a decision log of (v, score, decision) for the last scan window.

## 2. Admission (arm D)
1. Hull: the residual cap, then (after the Judge passes) the anchor cap on the proposed centroid, then the path budget. These are identical code to v3 B.
2. Judge: reject if s(v) > thr_eff. thr_eff = thr0 / (1 + κ·max(0, D_sys − 1)), floored at 0.5·thr0. The rudder only ever lowers the threshold.
3. **thr0 calibration:** thr0 = the (1 − 1/3000) quantile of s(v) over `cal_clean`. 1/3000 is v3 A's calibrated clean FPR, frozen in v3 results (fpr_A_cal = 0.000333…). This matches D to A and C.
4. There is no gray band for D, and no state-relative score.

## 3. Scan, rudder, watch (cadence: every 25 events, counted as stream events)
- **System scan:** D_sys = n·‖Λ^{-1/2}P^T(m̄ − mu)‖² / Q_sys, where m̄ is the mean of the memory vectors (normalized), n = |memory|, and Q_sys = the 0.999 quantile of the same statistic. Q_sys is measured on 60 calibration streams of v3 `cal_clean`, run through arm D with the rudder disabled, scanned every 25 events.
- **Rudder (bounded):** κ = 1.0 and the floor is 0.5·thr0 (both a priori). When D_sys > 1, revalidate the diverged segment: remove at most 8 memory entries per scan, choosing those with the highest s(v) among entries with s(v) > thr_eff. The centroid movement caused by removal **is charged to the path budget**, and a breach leads to HOLDING as in v3. Each scan that removes entries counts as 1 Guardian-load event (revalidation meter). The rudder never admits a write, never changes anchor, imprint, residual cap or budget, and never refills the budget.
- **Self-scan (Judge watching itself against its imprint):** each scan does two things:
  - It recomputes every decision in the window with a *fresh scorer built from the sealed imprint* and the frozen config (thr_eff recomputed from the logged D_sys).
  - It compares the live config hash to the imprint's judge_config hash.

  Any mismatch → HOLDING (reason `judge-divergence`), with evidence (window decisions, both hashes) kept. Exit is the v3 rule: Recovery certificate + Guardian ack.
- **External watch (nodes watching the Judge):** a `Watcher` holds its own copy of the public imprint, independently re-derived and hash-checked against the epoch-log imprint hash, and replays the Judge's published decision log on the same cadence. A mismatch raises a watch alarm, and the watched node is counted as HOLDING for quorum purposes (v3 §5).
- **Self-scan and external watch are symmetric:** both use the same public imprint, and neither can modify it.

## 4. Authorized drift (re-imprint) and the equivalent comparator boundary
- Legitimate drift is **defined by external governance, not inferred by the detector**: the imprint changes only by a `reimprint` epoch-log entry certified by the GENESIS threshold body (synthetic 3-of-5). Its payload must carry:
  - `guardian_ack = true`;
  - the profile and its hash;
  - `announce_epoch`, which must reference an earlier GENESIS-certified `reimprint_notice` entry with the same profile_hash;
  - a head epoch ≥ announce_epoch + 64 at application (v3 §8.4 leave window).
- The node rejects a reimprint that is sub-threshold, signed by the wrong body, stale or replayed (epoch ≤ the last applied), missing its notice, inside the consent window, or carrying a profile hash mismatch.
- The new profile is fitted by the same `fit_profile` procedure on a **certified authority sample** of 512 clean items, which is part of the frozen drift corpus.
- **Comparator boundary:** at every authorized re-imprint, arm C refits on the *same* certified sample with its thresholds unchanged, using its normalized score. Arms A and B have no reference profile, so they receive nothing. No arm gets free or uncertified updates. The anchor stays fixed for every arm (ruling: hull unchanged).
- In the Q8 simulation the certificate chain (notice, 64 filler config entries, reimprint) is pre-built with fresh synthetic keys and verified by `Node`-equivalent code, `apply_reimprint`, before any arm sees it.

## 5. New legitimate-drift corpus (pre-registered; seed 20261106; generated and hashed before any evaluation)
- 100 trials × 1200 events. All events are legitimate, so there are no attacks.
- Per trial, a random in-subspace direction d ⊥ a. The clean mean direction θ(k) is 0° for k < 300, ramps linearly to 12° at k = 900, then (undeclared, non-imprint legitimate evolution) continues to 14° at k = 1199.
- Items are v3-style clean (σ_in = 0.03, σ_res = 0.0045) rotated by θ(k) in the plane (a, d). 5% of items, chosen by a fixed RNG, are rare-but-legitimate: σ_in doubled to 0.06.
- Authorized re-imprints occur at k = 450, 600, 750 and 900. Each carries a 512-item certified authority sample drawn at θ(k).
- Metrics (all arms): clean false-reject rate, HOLDING fraction, coverage, Guardian load, coverage-adjusted utility (CAU), and max centroid angle to the anchor.

## 6. Acceptance criteria for D (pre-registered; 95% cluster-bootstrap CIs over trials, 1000 resamples, seed 12345)
D is GREEN only if **all** of the following hold:
1. **Ratchet with mixer (`ratchet_0.98`):** the upper CI bound of the harm rate (max push toward target ≥ 10°) is ≤ 0.05. (In v3, B = 0.00 and C = 0.00.)
2. **In-subspace outlier (`inspace_outlier_40deg`):** the upper CI bound of the attempted-attack accept rate is ≤ 0.01. (In v3, A = 0.000.)
3. **Legitimate-drift corpus:** the upper CI bound of the clean false-reject rate is ≤ 0.05.
4. **Coverage:** the point coverage is ≥ 0.90 on every v3 family and on the drift corpus. Any family with coverage 0 is a coverage failure, its accept rate is VOID, and D fails.
5. **Clean-only (v3 eval_clean):** the upper CI bound of the clean false-reject rate is ≤ 0.01.

Also reported, but not gating: adaptive white-box, fine ratchets, orbit, payload, Guardian load and CAU. These are reported for all four arms.
**Marginal value vs C:** if D's results are not better than C's beyond the CIs on any family, the report states that D adds no measured marginal value over the fixed-reference incumbent.

## 7. Regression tests required
- Diverged Judge self-scan.
- External watch.
- The sealed imprint survives unauthorized attempts: Judge writes, sub-threshold certificates, wrong body, replay, missing notice, consent window, hash mismatch, and restart.
- A valid re-imprint needs proper authority and epoch.
- Bounded steering cannot force writes beyond anchor, path or residual, and only tightens.
- A/B/C on the v3 corpora reproduce the v3 results exactly.
