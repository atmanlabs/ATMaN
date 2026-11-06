# Michael's Gate v5: reference-model report (candidate)
RESEARCH/REVIEW ONLY · LOCAL SYNTHETIC MODEL · NOT PRODUCTION SECURITY · NO GUARANTEE · NOT FLAWLESS
Date: 2026-11-05 (EST). Every key in this bundle is a SYNTHETIC TEST, NONPRODUCTION key.

## Verdict
**DESIGN WALL at A4, the inherited residual/reference-model wall. 8 of 9 pre-registered criteria pass in F2.**
- A4 fails in F1 and F2 identically: drift5 clean false-reject rate 0.0686 [0.0672, 0.0699], against a UCL ≤ 0.05 bound. holdout5 passes at 0.0427 [0.0415, 0.0438].
- The comparator arms show the same floor: A (geometry-only) 0.0672 and C (incumbent detector) 0.0687 on drift5.
- The rejects are the inherited anchor/path/residual hull refusing the corpus's declared high-variance rare external items (sigma 0.06, 8%).
- Clearing A4 would require changing the hull/residual, the cadence, or the frozen corpus, or a covert equivalent such as dropping rare samples. None of these was done.
- This needs an Owner ruling on the outer-loop residual property, or a re-specified drift bound for a v6.

## Stages (immutable, in order)
| Stage | Commit | Result |
|---|---|---|
| F1 freeze (corpora + spec) | e125422 | corpora sha256 cc88d552… |
| F1 impl registration | 572a4fe | |
| F1 run | 9f4845a | WALL: A4 failed; A6 failed (bulk dilution 0.391 > 0.30, because the E purge was removed) |
| F2 registration (`V5-F2-SPEC.md`) | 921708a | |
| F2 run | this commit | A1–A3 and A5–A9 PASS; A4 FAIL (expected, unchanged) |

## F2 metrics: arm F, 95% bootstrap CIs, in `artifacts/q8F2_results.json`
| Metric | Value |
|---|---|
| Clean false-reject rate (v3 clean) | 0.0005 [0.00035, 0.00067] |
| Ratchet harm (A1) | 0 |
| In-subspace outlier (A2) | 0 |
| Adaptive whitebox harm (A9) | 0 |
| alarm_cover harm (A7) | 0 |
| Coverage, minimum over families | 0.940 (drift5); no family all-HOLD |
| Bulk dilution: max non-imprint memory fraction | 0.25 (cap 0.25, bound 0.30; F1 was 0.391, E 0.298) |
| Unrooted, post-revocation contaminated accepts; contaminated residue | 0 |
| fine_ratchet_ext: trace alarm before geometry | yes |
| False trace alarm, drift5 / holdout5 | 0 |
| park_flood | queue ≤ 16, window ≤ 20, 0 park admits, all beacons verify, feed origin unaffected; clean false-reject rate 0.0004 |
| Legitimate external lineage parked by the NI cap (drift5/holdout5/legit_drift) | 0 |

- **Holding fraction ≈ 5–6% on 1200-event drift streams.** This is the inherited v3 hull window closing at 1000 writes, followed by Guardian revalidation. It is not caused by alarms or parks, and coverage stays ≥ 0.94.
- **Comparators:** A–E figures for drift5/holdout5/alarm_cover/park_flood are in the immutable `artifacts/q8F1_results.json`. On drift5, D and E have a false-reject rate of 0.090 and coverage of 0.744, i.e. worse than F.

## Tests
79 unit and regression tests pass (`artifacts/F2_TESTLOG.txt`): the v3 battery, v4 imprint/trace, v5 union (Weeboh), v5 gateF (Crimson), and v5 F2 (Onix plus the lineage cap).

## Crew integration (originals untouched; read-only copies in `crew-evidence/`)
- **Weeboh:** mandatory custody/channel domains; depth ≥ 2; per-union caps; fixed committee; live < q ⇒ HOLD. Scoped to one declared credible union.
- **Crimson:**
  - removed the corrective charge to the write budget;
  - per-origin park quota;
  - in-cone drift test: alarms fire with no HOLD and no budget penalty, while over-anchor writes are rejected;
  - stale-head GAP retained.
- **Onix:**
  - chained, non-overwriting, derived root ids with imprint lineage denied;
  - a RECOVERY Guardian-ACK certificate instead of the boolean;
  - max-matching independence;
  - certified catch-up only;
  - bounded staging with composite ids and tolerant parsing;
  - snapshot restart;
  - literal capacity arithmetic (backlog = (rate − R) × epochs; Onix's negative control = 1200).
- **Kodi:** packaging (see `../README.md`). **Counsel:** see LIMITATIONS.

## Remaining GAPs (not fixed, not claimed)
- **No real independent review, network, gossip, clock skew, partition, HSM, or production threshold crypto.** Transport is direct in-process calls, not sockets.
- **Org/custody independence is declared by registry attestation, not verified.** Cooperating actors in one real trust domain count as one domain only if declared honestly.
- **Root admission is the trust boundary.** Owner, GENESIS, or Guardian (RECOVERY) key compromise defeats it (insider limit). Authorized ancestry is necessary for semantic truth, not sufficient.
- **The Guardian ack is a synthetic certificate,** and the park scheduler is non-admission staging. Neither is real human review, and real turnaround is unmodeled.
- **No liveness is claimed** unless available guardians × ack_cap / k ≥ demand and R ≥ the recall rate.
- **Persistence is a hash-sealed in-memory JSON snapshot,** not a durable authenticated store. The dedupe window is bounded, so very old ids have no anti-replay.
- **A4 wall** (above). The F2 cap of 0.25 sits at the attack edge by construction: bulk dilution reaches exactly the cap.

## Packaging addendum (generation 2, 2026-11-06)
At gen2 sealing, prior to Kodi's subsequent PASS: Packaging only, see `PACKAGING-RECEIPT.md`. Results and verdict are unchanged: WALL at A4. Generation 1 packaging FAIL (Kodi); generation 2 pending Kodi independent verification.
*Supersession note (2026-11-06):* Kodi later PASSED generation 2 (see `crew-evidence/round3-full-20261106T0052/kodi-gen2-verdict.md`). R3 receipts are in `R3-RECEIPT.md`. Kodi later PASSED gen3 (pre-final-text; packaging + retained R3 evidence; `crew-evidence/round5-kodi-gen3/kodi-gen3-verdict.md`). Gen4 (text-only) is PENDING its own Kodi verification.

## R3 reproducibility addendum (2026-11-06)
The full inherited v3/v4 batteries and the F1/F2 reruns reproduced the shipped results. Only the top-level runtime_s differs. See `R3-RECEIPT.md`. Gen2 packaging PASS is Kodi's independent result; gen1 was FAIL. No algorithm change. Still a WALL at A4.
