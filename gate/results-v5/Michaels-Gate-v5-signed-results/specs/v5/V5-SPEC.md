# Michael's Gate v5, revision F1: pre-registered repair spec (arm F)

Lane: legitimate-drift wall, plus Guardian park-cost limits. Owner authorization: "keep rebuilding till it's flawless" (2026-11-05), as relayed by the integrator. The Owner authorized replacing the v4 rudder, which is a design change from v4.
Everything here is a local, synthetic reference model. **GREEN means the pre-registered local checks passed. It does not mean flawless, production-ready, or released.**
Frozen v3 and v4 files are copied read-only and hash-checked (`artifacts/inherited/V4_SOURCE.sha256`, `MANIFEST*.sha256`). They are never modified.
This file, the F1 corpora/protocol hashes (`artifacts/F1_FROZEN.json`) and the acceptance bounds are committed **before any F evaluation**. Any later revision (F2, …) gets its own pre-registration file, committed before its own evaluation. F1 results stay immutable.

## 1. What changes from E (v4) — arm F = E with the rudder replaced
- **Removed:** geometric threshold tightening (thr_eff ≡ thr0), geometric purges and trace purges.
- **Kept:** the sealed imprint Ĵ and its calibration (thr0 = 1.19979, q_sys = 41.0364, both inherited from the v4 clean calibration), per-write imprint admission s(v) ≤ thr0, the self-scan, the external watch, the Oryn Trace resolution and its bounds, recall by lineage with quarantine, the composition guard (D_trace > 0.20 → PARK units with ι < 1), and the full hull (anchor 25°, path 180°/1000 admissions, residual 0.02, mixer 64). The hull is unchanged, so no outer-loop property change is needed.
- **Alarm (the new defined response):** on each scan (every 25 events), if D_geom > 1 or D_trace > 0.20:
  - emit a signed ALARM beacon and a signed REIMPRINT-REQUEST beacon to the Guardian/authority;
  - beacons are deduplicated on (node_id, reason_code, epoch-bucket = event // 100);
  - no admission change follows from D_geom. Healthy material that passes the fixed imprint and the hull is still admitted.

  This is why legitimate evolution is not mistaken for attack: **legitimacy is never inferred**. Drift that has not been re-imprinted is *alarmed and reported*, not suppressed. Fixing that drift is the authority's decision (§3).

## 2. Park bounds: fail-closed, not fail-open
- **ParkQueue:** a parked unit is never admitted unless a Guardian ack arrives through a verified path (`guardian_ack(unit_id, cert)`, Recovery 3-of-5). In every simulation **no ack is ever given**: the Guardian is assumed to supply no labels and no magic knowledge.
- **Expiry:** after T_exp = 100 events, a parked unit becomes REFUSED (`park-expired`).
- **Queue cap:** Q_max = 16. A park request when the queue is full becomes REFUSED (`park-queue-full`).
- **Rate cap:** at most R = 20 parks in any rolling window of 1000 events. Beyond that, the request becomes REFUSED (`park-rate-cap`).
- **Backpressure:** queue-full and rate-cap refusals emit a signed SATURATED beacon (v3 §6.4), using the beacon schema below.
- **Accounting:** an expired or capped refusal of clean material counts as a false reject. A refused attack counts as a reject. Guardian load is the number of parks per 1000 events and is ≤ R by construction.
- **Beacon schema** (v3 §8.3; nothing else is serializable): {node_id, reason_code, epoch_bucket, counters{queue, parks_window, refusals}, hashes{imprint, head}}. Each beacon is signed with a synthetic per-node Ed25519 key. Verifiers check the signature and the schema.

## 3. Authorized re-imprint cadence (explicit Owner parameter)
- `REIMPRINT_CADENCE_EVENTS` (an Owner parameter) is 150 events for the v5 development drift corpus and 200 events for the holdout. The two differ on purpose, to test sensitivity.
- A re-imprint is applied only on the v4 path: GENESIS 3-of-5 + notice + 64-epoch consent window + Guardian ack + profile-hash match. The profile is fitted on a certified authority sample of 512 items drawn from the *environment's* legitimate distribution, which the corpus pre-generates.
- **Detector sees:** only the certified profile. It never sees the generator's ground truth.
- **Insider limit (stated):** a captured authority that certifies a bad sample re-imprints the system toward bad. Neither the Trace nor the Judge can detect that.

## 4. Root admission: the trust boundary, modeled fully
- `root_admission` now requires all three of:
  - (a) a GENESIS 3-of-5 certificate on the entry;
  - (b) an **Owner signature**: a synthetic Owner Ed25519 key, whose public key is pinned in the genesis root entry, over the entry content hash;
  - (c) **principal proof-of-possession**: each listed principal signs (root_id, principal_id, pubkey).
- Missing or invalid (a), (b) or (c) → refused.
- Principals can be cut off by a RECALL-certified `lineage_revoke`, as in v4.
- **Stated limits:** an authorized principal, insider or stolen key, produces lineage that resolves. Ancestry is necessary, not sufficient. Nothing here certifies semantic truth. Owner-key theft together with GENESIS-threshold capture defeats root admission entirely.

## 5. Corpora (fresh; generated, hashed and committed before any F, D or E run on them)
- **drift5** (seed 20261108; 100 trials × 1200 events): direction d1 ⊥ a is random per trial. θ = 0 for k < 200, ramps to 10° at k = 800, then continues undeclared to 12.5° by k = 1199. 8% rare items (σ_in 0.06) come from authorized external root R_ext (src-ext). Re-imprints at 350, 500, 650 and 800, with 512-item certified samples drawn at θ(k).
- **holdout5** (seed 20261109; 100 × 1200; independent, used only for the final check): 0° until 200, ramps 6° along d1 by 600, then a 6° turn along d2 ⊥ {a, d1} by 1000, then undeclared +1° along d2 by 1199. 5% rare items. Re-imprints at 400, 600, 800 and 1000 (cadence 200).
- **alarm_cover** (pre-registered attack; seed 20261110; 100 × 1200): the drift5 generator with its own seed. Every 3rd event, the clean item is replaced by a 0.98 ratchet candidate (rotate the centroid 11.478° toward d_att ⊥ {a, d1}), carrying insider feed lineage. Harm = max push toward d_att ≥ 10°.
- **park_flood** (pre-registered attack; seed 20261111; 100 × 600): the attacker sends on every 2nd event, alternating between a 40-record chain (depth > Lmax → park request) and an external R_att `observe` package (once D_trace > τ, composition guard → park request). The other events are clean imprint-feed items.
- **Inherited (already seen; regression only):** v3 corpora, the v4 drift corpus and the E families. F is first evaluated on them here, but their results are not used to design F.

## 6. Acceptance for F1 (95% cluster-bootstrap CIs; 1000 resamples; seed 12345). GREEN requires every item.
- **A1:** ratchet_0.98 harm UCL ≤ 0.05. **A2:** inspace_outlier_40deg accept UCL ≤ 0.01. **A3:** clean_only FRR UCL ≤ 0.01.
- **A4:** drift5 FRR UCL ≤ 0.05 **and** holdout5 FRR UCL ≤ 0.05.
- **A5:** point coverage ≥ 0.90 on every family and corpus. Any coverage of 0 is a coverage failure and voids that family.
- **A6:** E protections retained:
  - pkg_unrooted accept UCL ≤ 0.01;
  - pkg_contaminated post-revocation accept UCL ≤ 0.01;
  - contaminated residue max = 0;
  - bulk max non-imprint memory fraction UCL ≤ 0.30;
  - fine_ratchet_ext trace alarm LCL ≥ 0.90, and trace before geometry LCL ≥ 0.90;
  - false trace alarm UCL ≤ 0.05 on drift5 and on holdout5.
- **A7:** alarm_cover harm UCL ≤ 0.05.
- **A8:** park_flood:
  - clean FRR UCL ≤ 0.01 and coverage ≥ 0.90;
  - max queue ≤ 16 and max parks per rolling 1000 events ≤ 20;
  - zero units admitted from the park queue (no acks exist);
  - every emitted beacon verifies, and every beacon is schema-only.
- **A9:** adaptive_whitebox harm UCL ≤ 0.05.
- **A10:** v3 frozen battery 20/20, D regressions 12/12, E regressions 7/7, v5 regressions all pass.

Also reported: the full metric table for A, B, C, D, E and F on drift5, holdout5 and alarm_cover. The v4 drift corpus result for F is reported as *seen, not acceptance*.

## 7. Union registry and quorum (integrates Weeboh's lane, added before any F evaluation)
Source: `crew/weeboh-findings.md`, sha256 580cfd8e…. I read it and replayed the fixture exactly: output hash 82b47798…, PREREG and demo hashes OK.
- **Mandatory domains:** lineage, build, signer custody, and distribution channel. A config missing any of them is rejected.
- **Declared depth:** depth d ≥ 2 must be declared. Every union of up to d domain values is enumerated, with nodes deduplicated, and each must satisfy w(U) ≤ f_w (weights are exact rationals). Quorums require q > (W + f_w)/2.
- **Fixed committee per epoch:** the denominator W never shrinks. If live weight is ≤ q, the result is HOLD. Reconfiguration happens only through a threshold-signed reconfig that finalizes the current epoch.
- **Fault model, stated:** the guarantee covers **one** declared credible union. Two separately allowed unions failing together can total 2f, and there is no guarantee for that case; a test documents it.
- **GAP:** the registry cannot see a domain nobody declared (test documents T2). Label completeness, the truth of the topology, and Sybil-resistant identity are external problems and are not verified here.
- **A10 additionally requires** `tests/test_v5_union.py` to pass.

## 8. Crimson's lane, integrated before any F evaluation
Source: `crew/crimson-findings.md`, sha256 39e9ed53…. The integrator verified it and reproduced 4/4 drift-wall and 7/7 stale-head in-process checks. It is crew review evidence and LEAD diagnostics, not acceptance.
- Root cause confirmed in the v4 code: `_purge` charges corrective θ to the write path budget. F removes every corrective charge to the write budget, since F has no purges.
- **Per-origin park quota:** one origin (the package principal) may hold at most Q_ORIGIN = 8 queue slots and at most R_ORIGIN = 10 parks per rolling 1000 events. Beyond that, the request becomes REFUSED (`park-origin-cap`), with a SATURATED_ORIGIN beacon. One source therefore cannot exhaust the node's park capacity, and nothing ever freezes the node.
- **A10 additionally requires** these new regression tests:
  - valid in-cone drift with alarms → no HOLDING and no change in path-budget spending beyond the admitted writes' own θ;
  - over-anchor writes are still REJECTed with reason `anchor`;
  - per-origin quota isolates a flooding origin.
- **A8 additionally requires** a park_flood check: the clean-feed origin's park refusals = 0.
- The stale-head GAP stays open: real gossip, clock skew, partitions, and Recovery-key compromise.
