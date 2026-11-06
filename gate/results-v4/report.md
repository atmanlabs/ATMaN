# Michael's Gate v4: reference-model report (arm D, the imprint Judge; arm E, D + Oryn Trace)

**Verdict: DESIGN WALL for both D and E.** Every result here is a synthetic, isolated reference result. It does not show production security or uniqueness. Nothing was shipped, activated or deployed. No network, messages, real data or grown state were used. All keys are fresh, local and synthetic (multisignature t-of-n, not production threshold cryptography).

- Rulings, frozen verbatim:
  - `OWNER-RULING.md` (f3fdfef9…), the imprint Judge.
  - `OWNER-ORYN-TRACE.md` (6b18b057…), the Oryn Trace.
- Frozen specs and protocols:
  - `V4-FROZEN-SPEC.md` (fee23ddf…) for D.
  - `V4-E-ADDENDUM.md` (4ace3375…) for E.
  - `MANIFEST.sha256` and `MANIFEST-E.sha256`.
- Frozen corpora:
  - v3 corpora reused unchanged (561dcb8c…).
  - Legit-drift corpus (19229dd9…), in `artifacts/V4_FROZEN.json`.
  - E families (9024cdec…), in `artifacts/E_FROZEN.json`.
- Reproduce with `./verify.sh`. It checks all hashes and the signed bundle, re-runs the v3 battery, the D and E regressions and both Q8 stages, and asserts bit-exact reproduction.
- Signed bundle: `artifacts/bundle/MANIFEST.json` and `MANIFEST.sig`. The SYNTHETIC v4 test-log key is in `artifacts/keys/`.
- v3 was not modified. Note: `/workspace/michaels-gate-v3/reference-model` shows timestamp-only diffs from someone re-running its `verify.sh` after the final v3 commit. The Q8 numbers are identical, and I did not touch it.

## Order of events (honest timing)
1. The imprint ruling was frozen together with the D spec and protocol and the drift corpus with its acceptance bounds (commits 4e9eb88 and c793e03). This happened before any calibration or evaluation.
2. D was evaluated once on the frozen protocol (commit 5e52b0c). It failed criteria 3 and 4.
3. The Oryn Trace ruling arrived **after D had been run**. D was kept unchanged. E was pre-registered as a separate stage: addendum, E corpus and protocol frozen (commits e7cd87e and 593fbe7) before any E evaluation. **E = D with constants unchanged + Trace.** I did not redesign D's rudder after seeing D's results, because that would be tuning on results.
4. Implementation fixes during E were limited to two:
   - a missing BODY_FOR_TYPE mapping, found by a smoke test on out-of-corpus trial id 999;
   - a crash while aggregating acceptance, which produced no results.

   The receipts are in `artifacts/cycles/`.

## Arm D (imprint Judge): frozen acceptance results (95% cluster-bootstrap CIs)
| criterion | D result | pass |
|---|---|---|
| 1. ratchet_0.98 harm UCL ≤ 0.05 | 0.000 [0.000, 0.000] | ✅ |
| 2. in-subspace 40° outlier accept UCL ≤ 0.01 | 0.000 [0.000, 0.000] | ✅ |
| 3. legit-drift clean FRR UCL ≤ 0.05 | **0.072 [0.069, 0.074]** | ❌ |
| 4. coverage ≥ 0.90 on every family | **0.692 on legit drift** (HOLDING from path-budget exhaustion) | ❌ |
| 5. clean-only FRR UCL ≤ 0.01 | 0.0005 [0.0004, 0.0007] | ✅ |

- **Regressions:** self-scan catches a diverged scorer and config, external watch works, the imprint stays sealed against 8 unauthorized re-imprint paths, a valid re-imprint needs GENESIS 3-of-5 plus notice plus a 64-epoch window plus Guardian ack, and the rudder only tightens and cannot bypass the hull. 12/12 pass.
- **The wall.** The rudder purges memory entries that diverge from the imprint and charges that movement to the path budget. On legitimate evolution that has not yet been re-imprinted, it therefore fights the drift: max displacement 8.9° against the 13.9° that legitimate drift actually reached. It exhausts the budget, holds for 31% of the time, and has a Guardian load of 12.1 per 1k events.
- This follows from Rule 1 of the ruling: any movement that has not been re-imprinted is drift. A gap between authorized re-imprint cadence and real evolution therefore becomes a false alarm. **Legitimate drift relies on external governance (re-imprint cadence), not on detector inference.** That reliance is exactly what fails here at the pre-registered cadence (every 150 events, plus undeclared evolution after event 900).
- **Marginal value vs C:** none was measured.
  - D ties C on every v3 attack family: ratchet harm 0, outlier 0, orbit 0, payload 0.
  - D is worse than C on legit drift (FRR 0.072 vs 0.043, coverage 0.69 vs 1.00) and on adaptive white-box FRR (0.175 vs 0.000).
- **A, B and C** reproduce the v3 numbers bit-exactly.
- **Post-hoc diagnostic** (`artifacts/diag_posthoc_rudder_off.json`, exploratory, not acceptance evidence): with the rudder off, D passes all five numbers (drift FRR 0.043, coverage 0.94). At that point it is essentially C plus the hull. This points a v5 proposal at the rudder's purge-and-tighten response.

## Arm E (D + Oryn Trace): frozen acceptance results
| criterion | result | pass |
|---|---|---|
| D criteria 1, 2, 5 applied to E | same as D | ✅ |
| D criteria 3, 4 applied to E (inherited rudder) | FRR 0.072 [0.069, 0.074]; coverage 0.692 | ❌ |
| P1a: geometry arms A–D accept packages, LCL ≥ 0.5 | ≈ 1.000 for every arm and package family | ✅ |
| P1b: E accepts unrooted packages, UCL ≤ 0.01 | 0.000 [0.000, 0.000] (refusals: unregistered principal, unknown parent, depth > Lmax → park) | ✅ |
| P1c: E accepts contaminated packages after revocation, UCL ≤ 0.01 | 0.000 (geometry arms: 1.000) | ✅ |
| P1e: contaminated live residue after lineage recall = 0 | E: 0 in every trial (A–D: 22 entries/trial); no blanket freeze, coverage 1.00 | ✅ |
| P1d: bulk-diluted max non-imprint memory fraction, UCL ≤ 0.30 | E 0.298 (A–D ≈ 0.50) | ✅ (narrowly) |
| P2: D_trace alarm on fine_ratchet_ext, LCL ≥ 0.9, and before D_geom | 1.00; D_trace median at event 49; D_geom never fired | ✅ |
| P3: false trace alarms on legit drift, UCL ≤ 0.05 | 0.00 | ✅ |
| coverage ≥ 0.90 on new families | min 0.966 | ✅ |

- **Regressions:** canonical tamper, signed-but-unrooted variants, depth park, wrong-body root admission and revocation, recall enumerates descendants without freezing, D_trace arithmetic, composition guard, and the no-lineage refusal. 7/7 pass.
- **Costs** (mean per trial):
  - record size 146–148 bytes;
  - trace store 489 units / 72 kB (bulk family) and 2,484 units / 364 kB (3,000-event family);
  - resolution plus Ed25519 verification ≈ 102–105 µs per package;
  - 1 visit per admission, thanks to memoized resolution.
  - **Guardian load is very high:** 110 to 315 parks per 1k events on the package families, and 180 per 1k on fine_ratchet_ext.

**What E's passes mean, and what they don't.**
- **Lineage attacks:** E adds real, testable value over D against lineage-identifiable attacks: foreign or unregistered principals, revoked ancestry, and bulk composition by an external root. Here geometry-only arms are blind by construction.
- **Surgical recall:** recall by lineage removed every contaminated descendant without a blanket freeze.
- **P1 and P2 are partly true by construction.** The attacker's packages and ratchet items carry non-imprint lineage, and nothing else about them is anomalous. Fine-ratchet *harm* was negligible in every arm (push ≈ 0.64–0.66°), so D_trace detects foreign ancestry, not geometric damage.
- **Necessary, not sufficient:** an insider or a stolen key on an authorized imprint-feed principal yields lineage that resolves. On all v3 families, which were modeled this way, E = D exactly. **Authorized ancestry is necessary, not sufficient. It does not authenticate semantic truth.** Root admission and the trusted transforms are the trust boundary.
- **Composition guard:** it parks rather than refuses, and every park costs Guardian review. The bulk-dilution result passed by a margin of 0.002.

**Bottom line:** E is not bookkeeping on lineage-class attacks. It is not a defense against attacks that ride authorized lineage, and it does not fix D's legitimate-drift wall.

## v5 proposal (outer loop; not applied)
1. **Rudder response.** Replace purge-plus-tighten with alarm-and-park. Steering may tighten only for non-imprint-lineage writes, or for writes beyond a calibrated geometric bound. Pre-register and test this against the same frozen drift corpus plus a new one.
2. **Re-imprint governance cadence.** Make the gap between authorized re-imprints and legitimate evolution an explicit Owner parameter. It decides whether D is usable at all.
3. **Trace Guardian load.** Bound the cost of parks: auto-expire to refusal after a set window, with a signed backpressure beacon (v3 §6.4).
4. **Root admission.** Treat it as a §7-class trust event: insider and stolen-key lineage are out of the Trace's reach.

## Remaining gaps
- Production Φ; real threshold cryptography; real networks and gossip; the genesis social layer.
- Union-registry depth (from v3).
- A rudder without the drift wall.
- Uniqueness remains GAP.
