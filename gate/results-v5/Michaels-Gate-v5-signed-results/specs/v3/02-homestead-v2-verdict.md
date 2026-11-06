# HOMESTEAD v2 VERDICT + v3 PATCH REQUEST
## Michael's Gate · 2026-11-05 · reference-model review only

*Filed verbatim as delivered by the Owner in chat, 2026-11-05 21:43 ET. Route: Homestead → Chief → Owner → Strider.*

**Bottom line:** v2 materially improves safety on paper and answers every Homestead charge by name. Availability and authority separation still fail as written. One signer remains a system-killer. Nothing is implemented; every property remains GAP until tested.

## Verdicts
- **Counsel — WATCH, new design-critical HOLD for outside deployment.** Q2/Q6.1/Q9/Q10 unchanged. STOP on nonconsensual replication or bypass stands. No release or activation greenlit.
- **Weeboh — FAIL on the BFT guarantee as drafted.** Direction is good, independence math is not yet sufficient.
- **Onix — Paper safety mostly improved (LEAD); availability fails as written.** Q7 decided: signed pull invitation primary, offline signed bundle fallback.
- **Crimson — rerun pending.** No verdict yet.

## v3 required changes
1. **Eliminate single-signer authority.** Threshold signing across independent domains for recall, genesis, key rotation, and HOLDING/quarantine exit. Recall authority and recovery authority must be separate thresholds; one key must never be able to approve poison and also unfreeze it.
2. **Bound epochs and prevent fast-forward capture.** No arbitrary huge epoch jumps. Large jumps require a higher threshold, witnessed evidence, and recovery quorum. Use one globally ordered threshold-certified hash-chained log: epoch = parent+1, parent hash, rule hash, config hash. Equivocation (two valid same-epoch entries) means permanent HOLD.
3. **Charge drift by path length, not net displacement.** The 25° anchor cap stops the original ratchet in about three 0.98 steps, but an attacker can rotate around the cone rim indefinitely at fixed displacement. Budget must charge sum(theta), not final distance. Define residual norm/energy explicitly; 0.02 energy implies max 8.13°, while 0.02 norm implies 1.15°. Revalidate parked writes against current anchor/budget/epoch at release.
4. **Cap unions of failure domains, not just each axis.** Counterexample: n=7, f=2, lineage cap 2; one lineage compromise plus one bad build creates 4 faults >f while every per-domain cap passes. Enumerate credible fault-set unions (lineage, build, operator, distribution, signer custody), each union ≤f weight, quorum > (W+f_w)/2. Divergence profiles can exclude nodes, never manufacture independence.
5. **Count HOLDING against f; never shrink the quorum denominator.** Forced abstention can hand an attacker a majority. Critical votes must not proceed on a reduced denominator. Network-wide HOLDING when the fault budget is exceeded. No silent denominator arithmetic.
6. **Make recovery attacker-price-resistant.** Independent per-node budgets and local quotas; shard-bound revalidation with proof that shards compose; reserved recall/security headroom; bounded backlog and backpressure; jitter/cooldown/hysteresis and beacon dedup; M-of-N recovery. Being stale is not compromise; lag must not cause mandatory quarantine.
7. **Specify genesis and key custody as a real ceremony.** Independent parties, pinned fingerprints, published transcript, named keyholders, pre-committed compromise recovery. A captured genesis makes the anchor protect poison.
8. **Consent and disclosure requirements.** Before joining, operators must explicitly consent to Guardian authority, automatic revocation fetching, HOLDING/quarantine powers, beacon/log visibility and retention, feature-map/signer changes. Operator-chosen endpoints and clean exit. No beacon or log may contain grown memory, personal data, or secrets. Changes to Guardian, feature map, or signer set require fresh notice and meaningful leave choice.
9. **Fix the Q8 ablation.** B must remove ONLY the Judge/step score while retaining anchor, path budget, and residual cap. Otherwise the test credits the Judge for other defenses. Report attempted-attack accepts, clean false rejects, HOLDING time, Guardian load, and coverage-adjusted utility; all-HOLDING cannot count as zero false accepts. Uniqueness remains GAP until this pre-registered test runs.
10. **Keep the v1 consent and release boundaries.** Pull-only distribution, affirmative owner opt-in, no silent install, no un-ignorable handshake, no authorization bypass. Q9/Q10 unchanged: spec/code/synthetic tests only under WATCH; no grown brain. Implementation verification remains blocked on actual artifacts.

## Accepted wins from v2
- Recall now bypasses a poisoned Judge, authenticates on signature+epoch, precedes gate operations, and survives restart. The five recall cases are answered correctly on paper.
- The original 200-step drift ratchet is blocked by the fixed anchor in roughly three steps.
- Bounded mixer and constant-size anchor checks address Q5; full root revalidation is scheduled rather than per-write.
- Judge is separable for ablation, making the claimed advantage falsifiable.
- Q7 now has a primary and fallback: signed pull invitation with explicit opt-in + TUF-style versions/expiry; offline signed bundle with out-of-band pinned fingerprint. Neither gives mass coverage or root recovery for free.

*Route: Homestead → Chief → Owner → Strider. The loop continues: patch, resend, break, repeat.*
