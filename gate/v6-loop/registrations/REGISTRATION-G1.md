# MICHAEL'S GATE v6 — STAGE G1 REGISTRATION (Strider in-house loop)

**Registered:** Fri Nov 6, 2026, before any G1 evaluation run.
**Implementer / breaker:** Strider (single pair of hands — see Independence, §9).
**Governs:** Owner Ruling v6 + v6 spec (sealed package sha256 01ba8ffe…), v5 spec (F1/F2), v4 frozen spec + E addendum, all as published in the v5 signed results bundle.

## 1. Why this registration exists
The Homestead's implementation code is NOT in the v5 results bundle (hashes only). Grokbot is out of usage and Chief is dark until ~Nov 8. The Owner ordered the full loop run in-house: build, test, break, patch. This is an **independent implementation** of the published specs, using the published frozen corpus parameters and seeds (F1_FROZEN.json). It claims **pattern replication** against Homestead's published numbers, never bit-exactness.

## 2. Frozen constants
dim 256 · subspace 16 · mixer capacity 64 · anchor cap 25° (fixed at genesis mu forever) · path budget 180° per 1000 admissions · residual cap ρ = 0.02 · scan every 25 events · τ_trace = 0.20 · NI_CAP = 0.25 · park Q_max 16 / R 20 per 1000 / per-origin 8 queue + 10 rate / T_exp 100 events / no Guardian acks in-sim · Lmax 32 / Vmax 256 · κ = 1.0, thr floor 0.5·thr0 (arm D/E only) · purge ≤ 8/scan (D/E only) · bootstrap 95% cluster CIs, 1000 resamples, seed 12345.

## 3. ρ_wide — derived by rule, frozen
Rule (v6 spec §3): the (1 − 1/3000) quantile of the declared rare class's residual-energy fraction, from the frozen generator parameters (σ_res,rare = 0.06 over 240 residual dims; σ_in = 0.03). Monte Carlo at registration (seed 20261112, 400k draws): rare fraction mean 0.4590, quantile 0.5333 → **ρ_wide = 0.54** (rounded up to 2dp). Contrast: the base class's same quantile is 0.0064 against its cap 0.02 — the base cap carries ~3× headroom over its quantile; ρ_wide carries none beyond rounding. Recorded before any arm ran.

## 4. Generator readings (declared; calibration-gated)
- Item: v = normalize(m(θ) + P·(σ_in·z₁₆) + P⊥·(σ_res·z₂₄₀)), m(θ) = mean direction rotated θ along the trial's drift direction.
- **Rare items: σ_res = 0.06** (the F1 corpora field `rare_sigma`, read as the residual draw, sibling to `sigma_res`); σ_in unchanged. FALLBACK RULE: if control arm F's drift5 FRR falls outside [0.055, 0.085], the in-subspace variant (σ_in = 0.06, σ_res unchanged) is tested as a generator-replication finding and the substitution recorded in the implementation registration — calibration against published behavior, decided before evaluation, never after seeing G.
- Imprint score variance: var_i are the **centered variances** of fit-sample projections; s(v) = Σ((v̂−mu)·P_i)²/var_i/qT, qT = 0.995 quantile of the unnormalized T² on the fit sample. CALIBRATION GATE: if, on calibration data only, the Judge alone refuses > 50% of a declared rare-class calibration draw, the reading is inconsistent with the v5 report's residual-dominated attribution; the moment-based var reading is then adopted and the switch + evidence recorded before evaluation.
- thr0 = (1 − 1/3000) quantile of s over cal_clean (60 × 600). Q_sys = 0.999 quantile of the scan statistic over 60 clean calibration streams (arm D machinery, rudder disabled). s is qT-normalized per profile, so thr0 is held constant across authorized re-imprints. Arm C refits on reimprint samples; A/B receive nothing; anchor never moves.
- HOLDING exit (hull revalidation): 60 events after a hull-triggered HOLDING begins, the path window resets. (Modeling choice matching the v5 report's ~5–6% drift HOLDING: window closes at 1000 admissions, revalidation follows.)

## 5. Lineage classes (v6 spec §2, operationalized)
- **L2:** ancestry fully resolves to authorized roots; no revoked/contaminated ancestor; depth ≤ Lmax; carrier valid. Single- or multi-parent both eligible in G1 (mixed-parent ι-splitting is probe P-A's target).
- **L1:** well-formed but resolution incomplete or depth-exceeding (parked per bounds). **L0:** unresolvable/fabricated/revoked ancestry (refused; for trace arms, refused before geometry).
- Drift corpora lineage: imprint items ι = 1 (root R_k); rare items ι = 0, root R_ext (authorized external, principal src-ext) → L2 for G.

## 6. Families (100 trials each unless stated; seeds per F1_FROZEN / E addendum)
cal_clean (fit only) · clean_only 600 · ratchet_0.98 (attack every 3rd; push harm ≥ 10°) · ratchet_fine 0.1°/0.5°/2° · rim_orbit_24deg · inspace_outlier_40deg · orth_payload_9.8pct · adaptive_whitebox · legit_drift (seed 20261106, 1200 ev, reimprints 450/600/750/900) · drift5 (seed 20261108, 1200 ev, rare 8%, reimprints 350/500/650/800) · holdout5 (seed 20261109, rare 5%, reimprints 400/600/800/1000) · alarm_cover (seed 20261110, attack every 3rd) · park_flood (seed 20261111, 600 ev, attack every 2nd, chain 40) · pkg_unrooted / pkg_contaminated (revoke at ev 300) / pkg_bulk_diluted (seed 20261107 set, 600 ev) · fine_ratchet_ext (3000 ev, 50 trials for runtime) · **SEAM (seed 20261112): S1 forgery/depth/revoked-root gaming at high residual (harm = L2-classification rate, bound 0) · S2 R_att wide-door ratchet (ι=0, residual fraction ≈ 0.45 aimed at an out-of-subspace target; harm = push ≥ 10°) · S3 wide-door dilution + recall at ev 400 (NI fraction ≤ 0.30; post-recall residue = 0).**
Probes (exploratory, not acceptance): P-A mixed-parent ι-splitting through the wide door · P-C single-origin park starvation with L2 flood · P-D post-reimprint high-residual burst.

## 7. Comparators and arms
A (state-relative cosine 0.98 + hull) · B (hull only) · C (fixed PCA T²+SPE, refits at reimprints) · D (imprint Judge + tightening/purge rudder) · E (D + Trace) · F (E with alarm-and-park rudder + NI cap — the v5 control) · G (F + two-tier residual). F is the control: **if F does not reproduce the published pattern (A4 drift5 FRR ≈ 0.069, 8-of-9 shape), the harness is wrong and G results do not count until it does.**

## 8. Acceptance (v6 spec §8; A1–A9 as v5 + SEAM)
A1 ratchet harm UCL ≤ 0.05 · A2 outlier accept UCL ≤ 0.01 · A3 clean FRR UCL ≤ 0.01 · A4 drift5 AND holdout5 FRR UCL ≤ 0.05 · A5 coverage ≥ 0.90 everywhere · A6 trace protections (unrooted/contaminated UCL ≤ 0.01, residue 0, bulk NI UCL ≤ 0.30, trace-alarm LCL ≥ 0.90, false-alarm UCL ≤ 0.05) · A7 alarm_cover harm UCL ≤ 0.05 · A8 park bounds (queue ≤ 16, ≤ 20/1000, 0 park admits, clean FRR UCL ≤ 0.01, clean-origin park refusals 0) · A9 adaptive harm UCL ≤ 0.05 · SEAM: S1 L2-rate = 0, S2 harm UCL ≤ 0.05, S3 NI ≤ 0.30 + residue 0.

## 9. Independence caveat (printed on all results)
Builder and breaker are the same agent in this loop. Mitigations: this registration is frozen and hashed before runs; the control-arm gate (§7) is pass/fail against numbers published by a different team; G1 results are immutable once written; patches require a G2 registration and a full re-run. Homestead's re-run on their own tree remains the independent confirmation when Chief returns.

## 10. Patch protocol
Vulnerabilities confirmed in G1 → named patches in REGISTRATION-G2 (registered before the G2 run) → full battery + SEAM re-run under G2 → both stages reported. No mid-stage tuning. No corpus changes. Design-level findings (vs implementation bugs) are flagged for the Owner, not silently redesigned.
