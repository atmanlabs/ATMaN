# Michael's Gate v3: reference model build/break report

**Status: DESIGN WALL at battery item 2 (Q8, the Judge/step score). Battery items 1, 3, 4, 5 and 6 are GREEN.**
This is a synthetic, isolated reference model. These results do not show production security, do not show the design is unique, and do not mean anything is ready to release. Nothing was shipped, activated or deployed. The work used no network, no messages, no grown state, no imprints and no personal data. All credentials are fresh, local and synthetic.

- Governing spec: `../michaels-gate-sealed-package-v3/01-v3-patch-spec.md`, sha256 `5eb18c2b…c6ad5d`. It was verified and never edited.
- Frozen battery harness: `tests/test_battery.py` and `tests/fixtures.py`. Their hashes are in `artifacts/FROZEN_BATTERY.sha256`, and every run checks them.
- Q8 corpora and protocol were frozen and hashed **before any evaluation** (`artifacts/Q8_FROZEN.json`): corpora `561dcb8c…`, protocol `7903362f…`.
- Verify or reproduce with `./verify.sh`. It checks the spec hash, the frozen-battery hashes and the signed bundle, re-runs everything, and asserts that the Q8 results match bit-for-bit.
- Signed log bundle: `artifacts/bundle/MANIFEST.json` and `MANIFEST.sig`. The signature uses a SYNTHETIC Ed25519 test-log key whose public half is `artifacts/keys/SYNTHETIC-test-log-signing.pub`.
- Threshold certificates use SYNTHETIC multisignature t-of-n: at least t distinct Ed25519 signatures from the governing body's registered set, over a body-domain-separated digest. The bodies are 3-of-5. This is not production threshold cryptography.

## Battery results

| # | Item | Result | Receipts |
|---|---|---|---|
| 1 | Kodi's five recall cases | GREEN (5/5) | `test_1..test_5`. Recall is applied on certificate + epoch before any gate step. Revocations are durable, rebuilt from the log at boot, and checked against a monotonic high-water counter. The Judge is never called on a recall. A core recall puts the node in HOLDING and freezes writes. A reconnecting node stays in CATCHUP until a fresh Recovery-certified attestation of the newest head arrives (cycle-2 fix). |
| 2 | Q8 corrected ablation | **PROTOCOL VALID, PREDICTION FALSIFIED → design wall** | See below. Coverage is non-zero for every arm and family, so no false-accept figure is void. |
| 3 | Drift | GREEN | 200-step ratchet with 0.98 steps, literal state: 2 accepted, **step 3 refused**, max 22.96°, path 22.96°. The A and B arms behave the same. With a 64-entry mixer: 81 accepted, max 24.91° (≤ 25°). Cone-rim orbit at 24°: 14 steps accepted, path 170.99° (≤ 180°), then **HOLDING (budget-exhausted)**. A net-displacement budget would never have run out. Refills are refused unless the revalidation is Recovery-certified, Guardian-acked, **and** names the current budget-state hash. Parked writes are re-scored at release. |
| 4 | Composition n=7, f=2 | GREEN | The Homestead counterexample (L1={n1,n2}, B1={n3,n4}) passes every per-axis cap but is **blocked**: union weight 4 > f_w = 2, with 67 violating registered unions. In 400 random weighted configurations, every admitted one met "any lineage + any build ≤ f_w" by independent brute force. q > (W + f_heaviest)/2 = 9/2. |
| 5 | Epoch | GREEN | Two distinct, validly certified entries at the same epoch give PERMANENT_HOLD. Both entries are fsynced to `evidence/`, the hold survives restart, and a full Recovery certificate cannot unfreeze it. Sub-threshold or wrong-body signatures are invalid and are not treated as evidence. At 33 epochs behind, a single-peer chain is rejected. A checkpoint without the chain, a chain with a gap, a forged tip, or a checkpoint signed by the wrong body is rejected. A Recovery checkpoint plus a linked chain is accepted. Recall and Recovery signer sets are enforced disjoint by key and by every domain value. |
| 6 | HOLDING accounting | GREEN | The denominator is always the full W. With 2 HOLDING nodes, 4 yes votes give NO_DECISION and 5 yes votes PASS. Combined faults above f (HOLDING + CATCHUP + OFFLINE, or BYZANTINE + 2 HOLDING) give NETWORK_HOLDING even when a 4/4 reduced majority agrees. Forced abstention gets the attacker a frozen network and 3 beacons. |

Unit tests: 20/20 battery tests and 11/11 regression or extra-break tests pass.

## Q8: what the frozen run shows

Full table with 95% cluster-bootstrap CIs: `artifacts/q8_table.md`. The raw data is in `results.json → q8`.

**Calibration (matching rule pre-registered in the protocol):** τ_step = 0.98, which is the spec default, already met the 1% target. FPR on the calibration set was 0.033% for A, 0% for B and 0.033% for C.
- C is matched to A exactly.
- B has no free parameter. Its anchor, path budget and residual settings are identical to A's, so its FPR is reported rather than tuned.

**Arm C** is a fixed-reference MSPC detector: PCA T² plus SPE, fitted once on clean calibration data. It is the standard incumbent detector, not a strawman, and it gates the same 64-entry mixer.

Key figures (point estimate [95% CI]):
- **In-subspace 40° outlier.**
  - Attack accept rate: A 0.000, **B 0.915**, C 0.000.
  - B's centroid is pushed 13.97°, and B pays HOLDING time of 0.085 and Guardian load of 1.67 per 1k events.
  - The Judge earns its keep only on this family and on the rim orbit (B accepts 0.957 of orbit writes, with negligible net push).
- **Ratchet at 0.98 per step (mixer).**
  - Harm rate (push ≥ 10°): **A 0.94 [0.89, 0.98]**, B 0.00, C 0.00. A's mean push is 22.96° against B's 6.30°.
  - A's clean false-reject rate rises to 0.465 and its coverage-adjusted utility falls to 0.535.
- **White-box adaptive attacker.**
  - Harm rate: A 0.94, B 1.00, C 0.00.
  - Push: A 23.0°, B 24.9°, C 4.1°.
  - Payload energy accepted per trial: A 0.005, B 0.97, C 0.29.
- **Orthogonal 9.8% payload:** blocked by every arm. **Fine ratchets (2°, 0.5°, 0.1°):** every arm accepts 100%, but no arm moves more than 1.5°.

**Finding (the wall).** The step score is measured against the *current* validated state. Once an attack moves that state, clean writes near the anchor start failing the step check, so the Judge rejects exactly the honest data that would pull memory back. In this model **A is worse than B on the ratchet**, and the fixed-reference incumbent C dominates A on harm in every family. The pre-registered v2 §6.3 claim, that A keeps its advantage over B and C, is **falsified** in this reference model. The 25° anchor cap and the 180° budget still hold in every arm, but inside that cone the Judge adds no protection and can increase harm. No implementation choice inside the spec fixes this:
- The step score's reference (current state) and τ = 0.98 are spec-stated.
- Changing what the Judge compares against is a change to a stated property.
- Lowering the anchor cap is a threshold change.

All of those belong to the outer loop.

**Caveats on the finding:**
- Φ is underdefined (v3 §11). The model uses a synthetic 256-dimensional geometry with a 16-dimensional anchored reference subspace derived from the genesis transcript hash.
- The clean corpus is stationary, which favours a fixed detector like C. A corpus with legitimate drift was not in the frozen protocol and was not added afterwards.
- Some per-family CIs have zero width because those families are deterministic given the frozen geometry.

## Build, break, fix log (git history in this directory)

1. **Cycle 1:** initial model. **Break:** Kodi case 5, an eclipse peer serving a valid but stale chain within K, thawed the reconnecting node. The spec only requires a checkpoint beyond K. The orbit test-fixture bug was fixed **before** the battery was frozen. Receipts: `artifacts/cycles/cycle1*.txt`.
2. **Cycle 2 (implementation fix):** to leave CATCHUP after reconnect, a node now needs a Recovery-certified head attestation, issued after the reconnect, within the freshness window, and naming the node's verified head. Regressions were added. The frozen battery was re-run unchanged and is green.
3. **Cycle 3:** Q8 harness, with corpora frozen before any run. **Attacker bug:** the white-box payload inherited centroid residual, which weakened the attack. The fix only strengthens attacks. Earlier results are kept at `artifacts/cycles/cycle3b-q8_results.json`.
4. **Cycle 4:** the white-box attacker now also searches payload levels (0.0195, 0.01, 0.003, 0), so it is not artificially weak against C. The frozen battery was re-run unchanged and is green. The Q8 conclusion did not change.

## Documented residuals and assumptions (not hidden)

- **Head-attestation race (regression `test_RESIDUAL_attested_stale_head_thaws`):** if a recall lands inside the freshness window after an honest attestation, or if the Recovery body is captured and attests a stale head, the node thaws on that stale head until the recall reaches it by store-and-forward.
- **Rollback of both log and revocation file** is caught only because the model assumes a non-rollbackable monotonic counter outside the data directory (TPM-like).
- **Recall scope freeze** is implemented conservatively: any scoped recall freezes all writes.
- Network HOLDING exit, §6.3–6.5 queues, hysteresis and jitter, and the §8 consent charter are **not implemented**. They are outside the frozen battery and remain GAP.
- **Union registry depth:** with unit weights, a depth-k registry can only admit configurations if k ≤ f_w. At n=7 and f=2, the depth-2 registry admits only fully diverse, unit-weight configurations, and **no configuration survives depth 3**. Unions of three or more domains are uncapped by construction. This is v3 §11's open "who enumerates" question, now made quantitative.

## v4 proposal (outer loop; requires Owner decision; not applied)

1. **Judge.** Either (a) remove the current-state step score from the admission path, or (b) score candidates against a fixed anchor-derived distribution, as arm C does, rather than against the moving state. Re-run Q8 with the new arm definition, pre-registered. Reason: the Q8 receipts above.
2. **Q8 protocol.** Add a frozen legitimate-drift clean corpus, so that fixed-reference detectors pay their real FPR cost. Pre-register before any run.
3. **§2.3 / §6.6 freshness.** State what proves the newest epoch *within* K. Proposal: a Recovery head attestation with an explicit freshness bound, plus an accounting of the Recovery load it adds.
4. **§4 registry depth.** State the credible-union depth explicitly and accept the consequence that depth ≤ f_w, or raise n.
5. **Durability assumption.** Make a monotonic counter (hardware or witnessed) a stated requirement for the revocation high-water mark.

## Remaining gaps

- Production Φ, production threshold cryptography, and real networking, gossip and eclipse resistance.
- Genesis social layer, collusion across the separated bodies, and real Guardian behaviour.
- Uniqueness stays **GAP**. The reference result points against the Judge as specified.
