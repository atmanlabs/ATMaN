# MICHAEL'S GATE — v3 PATCH SPEC
## Response to the Homestead v2 Verdict, 2026-11-05

**Prepared by:** Strider, at the Owner's order, lab session 2026-11-05.
**Status:** DESIGN SPEC, reference-model level. No implementation, no deployment, no release, no activation. Prepared for resend: Owner → Chief → Homestead. The loop continues: patch, resend, break, repeat.
**Scope note (the Homestead's, adopted):** every property in this document remains GAP until tested. Paper safety is not a defense.

---

## 0. Corrections to v2, owned in our own hand

1. **Arithmetic.** v2 §2.2 said the anchor wall stops the drift ratchet "at roughly step 55." Wrong. A step scoring C = 0.98 subtends arccos(0.98) ≈ **11.48°**; against a 25° anchor cap the wall lands at **~3 steps**, as the Homestead's rerun states. The mechanism was right; the number was not. Corrected here, and the correction is part of the record.
2. **Residual ambiguity.** v2 §2.4 wrote the cap as an energy fraction without stating its angular meaning. §3.3 now defines the quantity and both readings explicitly.
3. **Single signer.** v2 left recall and root events effectively single-keyed. The Homestead is right: one signer was a system-killer wearing a protocol's clothes. §1 removes every single-signer authority in the design.

## 1. Threshold authority — no key is a king (v3 demand 1)

**1.1 Four separate threshold bodies**, each a threshold signature scheme (t-of-n) whose signer sets are drawn from **distinct failure domains** (per §4's registry — lineage, build, operator, region, custody):
- **Genesis Authority** — certifies genesis and re-genesis (§7).
- **Recall Authority** — signs recalls (§3 of v2, unchanged mechanics, new signer).
- **Recovery Authority** — signs unfreezes, HOLDING/quarantine exits, and epoch checkpoints (§2.3).
- **Rotation Authority** — signs key rotations and signer-set changes.

**1.2 Separation of duties (hard rule).** The Recall Authority and the Recovery Authority have **disjoint signer sets**: no key, and no single domain, may sit in both. The body that can approve content's removal is never the body that can declare the emergency over. One compromised key yields at most one body's partial share — never an approval, never an unfreeze, never both halves of a poison-and-pardon.

**1.3 No unilateral exits.** HOLDING and QUARANTINE exits (v2 §5.4) now require a Recovery Authority threshold certificate in addition to the cleared condition and Guardian ack. The Guardian proposes; the threshold disposes. Guardian capture alone (Verdict Q2) can freeze a node — it cannot free one, mint a rule, or sign a recall.

## 2. The epoch log — one history, certified (v3 demand 2)

**2.1 Single global log.** All rules, recalls, rotations, and config changes live in **one globally ordered, hash-chained log**. Each entry: {epoch, parent_hash, rule_hash, config_hash, threshold_certificate}. **Epoch = parent epoch + 1, exactly.** There are no jumps in the log itself — apparent jumps are just many entries.

**2.2 Threshold certification.** An entry is valid only with a threshold certificate from the body governing its type (§1.1). A lone signature certifies nothing at net level, ever.

**2.3 Fast-forward capture defense.** A node more than **K = 32 epochs** behind may not accept a long chain from a single peer. Catch-up beyond K requires a **checkpoint**: a Recovery Authority threshold certificate over the current log head, plus the hash chain from the node's last verified epoch to that head, verifiable link by link. The certificate attests the head; the chain proves the path; neither alone suffices.

**2.4 Equivocation = permanent HOLD.** Two distinct, validly certified entries at the same epoch are mathematical proof that a threshold body was captured or forged. Any node observing equivocation enters **permanent HOLDING**, preserves both entries as evidence, and exits only through the §7 re-genesis procedure. There is no timeout from an equivocation hold. Some doors, once the evidence says they were forced, stay shut until the house is rebuilt.

## 3. Drift accounting — charge the path, not the position (v3 demand 3)

**3.1 Path-length budget.** The drift budget now charges **Σθᵢ** — the sum of angular steps actually taken in the window — not net displacement from the anchor. An attacker orbiting the cone rim at fixed 25° displacement pays for every degree walked and exhausts the budget exactly as a straight-line ratchet does. The anchor displacement cap (§2.2 of v2) is **retained** as an independent second bound: position is capped, and so is travel.

**3.2 Budget parameters (reference-model defaults, calibration targets for §9):** window = one epoch-day or 1,000 admissions, whichever closes first; budget B = 180° of total path per window (≈ 15 maximum-size 0.98-steps); replenishment only via Guardian-acknowledged revalidation (unchanged from v2), now additionally requiring the revalidation certificate to name the budget state it resets (§6.2 composition).

**3.3 Residual, defined.** The cap is on **energy**: ρ_E = ‖residual‖² / ‖f‖² ≤ **0.02**. In angular terms this bounds a single write's off-reference component to arcsin(√0.02) ≈ **8.13°** worst case. (Had the cap been stated on norm — ‖residual‖/‖f‖ ≤ 0.02 — the bound would be ≈ 1.15°. The spec means **energy**; the number to attack is 8.13°.) Both readings are now on paper so the next attack doesn't have to guess which one to kill.

**3.4 Parked writes revalidate at release.** A gray-band (parked) candidate earns nothing by waiting. At release it is scored fresh against the **current** anchor state, **current** remaining budget, and **current** epoch — and it pays its path charge at release-time prices. A queue is not a laundering machine.

## 4. Union caps — independence is topology (v3 demand 4)

**4.1 Credible fault-set registry.** The design maintains an explicit registry of **credible fault sets**: unions across the domain axes — lineage, software build, hardware, operator, region, distribution channel, signer custody. Each registered union U carries a weight w(U).

**4.2 The binding constraint.** For every registered union: **w(U) ≤ f_w**, and every quorum must satisfy **q > (W + f_w)/2**, where f_w is the weight of the heaviest registered union. Per-axis caps (v2 §4.2) are retained but demoted to what they are: necessary, not sufficient. The Homestead's counterexample (n=7, f=2: one lineage compromise + one bad build = 4 faults while every per-axis cap passes) is filed as the canonical test case — any composition rule that admits it fails.

**4.3 Registry maintenance.** The union registry is re-enumerated on **every join, leave, build change, custody change, and config change**, and the re-enumeration is itself an epoch-log entry (§2). An unregistered credible union discovered in the wild is treated as a design incident, not a surprise to shrug at.

**4.4 Divergence, demoted to its honest job.** Measured divergence (v2 §4.3) can **exclude** a node from a quorum. It can never **manufacture** independence: nodes that perform difference without having it are a §7-class attack problem (attestation fraud), not a quorum-eligibility shortcut. Eligibility flows from the registry's topology; divergence is a filter on top of it, never a substitute for it.

## 5. HOLDING accounting — the denominator never moves (v3 demand 5)

**5.1 HOLDING counts against f.** A node in HOLDING is abstaining, and abstention is counted exactly like a fault for quorum purposes. The fault budget f covers Byzantine + HOLDING + offline, combined. There is no arithmetic in which frozen nodes quietly leave the denominator.

**5.2 Fixed denominator.** Quorum thresholds are computed against the full registered weight W, always. A critical vote that cannot reach q > (W + f_w)/2 from *active, eligible* voters **does not proceed on a reduced basis** — it does not proceed.

**5.3 Network-wide HOLDING.** If combined faults (Byzantine evidence + HOLDING + offline) exceed f, the network enters **network-wide HOLDING**: writes freeze everywhere, last-good reads continue, beacons explain. The net parks rather than decides with a borrowed majority. Forced abstention as an attack (v2 §7.6) now buys the attacker a frozen network and a signed evidence trail — not a majority.

## 6. Recovery economics — safety the attacker cannot price us out of (v3 demand 6)

**6.1 Per-node budgets.** Drift budgets and revalidation quotas are **per-node and non-transferable**. There is no global pool to drain; exhausting your own budget freezes you, not your neighbors. (v2 §2.3 was per-node in intent; v3 makes it explicit and load-bearing.)

**6.2 Sharded revalidation with composition.** Full root revalidation is sharded by memory segment. Each shard produces a signed result hash; the revalidation certificate is a threshold attestation over the **hash of shard hashes**, so the whole is certified exactly when every shard is — shards compose by construction, and a missing or failed shard invalidates the certificate rather than being averaged away.

**6.3 Reserved security headroom.** Recall traffic, epoch-log sync, and HOLDING beacons travel in a **protected queue with reserved capacity** that content traffic cannot borrow, burst into, or starve. The kill switch never waits in line behind the traffic it exists to kill.

**6.4 Backpressure and bounded backlog.** Queues are bounded; overflow produces explicit backpressure signals to peers (a signed "I am saturated" state), never silent drops. Saturation is a reportable condition, not a failure mode discovered later.

**6.5 Anti-oscillation.** HOLDING entry and exit carry **hysteresis** (exit thresholds stricter than entry thresholds) and **jittered cooldowns**, so an attacker cannot farm freeze/thaw cycles at a predictable rhythm. Beacons are deduplicated on (node_id, reason_code, epoch) — the same hold announced twice is one event.

**6.6 Stale is not compromised.** A node that is merely *behind* enters **CATCH-UP** — read-only, abstaining, unembarrassed — not HOLDING and never QUARANTINE. Lag triggers §2.3's checkpoint procedure, nothing harsher. A network that punishes slowness will be taught to fear its own honest nodes; this one doesn't.

**6.7 M-of-N recovery.** Unfreeze and rejoin decisions are Recovery Authority threshold acts (§1.1, §1.3). No single operator, Guardian, or peer can resurrect a node — including a well-meaning one. Especially a well-meaning one.

## 7. Genesis — the ceremony is the root of the root (v3 demand 7)

**7.1 Parties.** Genesis is executed by **≥ 3 independent parties** from distinct registered domains (at minimum: distinct lineage, operator, and region). No party may hold two seats.

**7.2 Fingerprints.** Every party's key fingerprint is exchanged over **≥ 2 independent out-of-band channels** and pinned in the transcript before any key signs anything. A fingerprint that arrives over one channel is a claim, not a pin.

**7.3 Deterministic anchor.** The anchored reference (v2 §2.2) is **derived deterministically from the genesis transcript**: any party, at any later date, can recompute the anchor from the published transcript and verify that the anchor the network serves is the anchor the ceremony produced. The anchor's provenance is reproducible, not testimonial.

**7.4 Published transcript.** The full transcript — parties, fingerprints, keyholders by name, custody domains, the derivation, all signatures — is hash-chained, signed by every party, and entered as **epoch 0** of the log (§2). What genesis did is public to the membership forever; there is no oral tradition at the root.

**7.5 Pre-committed recovery.** Before the first anchor derives, the transcript must contain the **compromise recovery plan**: the Recovery Authority composition, the evidence standard for declaring a genesis capture, and the re-genesis procedure. A captured genesis makes the anchor protect poison (the Homestead's words) — so the antidote is written before the poison can exist, not improvised after.

## 8. Operator consent charter — joining means knowing (v3 demand 8)

**8.1 Enumerated consent.** Before a node joins, its operator signs consent to an enumerated list — not a blanket: (a) Guardian authority and its exact scope; (b) automatic revocation fetching and execution (v2 §3); (c) HOLDING and QUARANTINE powers over their node, and the §5 accounting; (d) beacon and log visibility — who sees what, retained how long; (e) the feature-map and signer-change process (§8.4).

**8.2 Operator-chosen endpoints; clean exit.** Operators choose their own endpoints. Exit is **unilateral**, effective at the next epoch boundary, with export of the node's own data. A gate you cannot leave is a wall with better branding; this one has a door and the door is in the charter.

**8.3 Beacon/log content — excluded by schema, not by promise.** Beacon and log records have an enumerated field schema (node_id, reason_code, epoch, counters, hashes). **Grown memory, personal data, and secrets have no fields to live in.** The protection is structural: the format cannot carry what it has no slot for. Policy can be violated in the night; schemas can't be sweet-talked.

**8.4 Material changes need fresh consent.** Any change to Guardian composition, feature-map version (Φ), or any signer set requires **fresh notice** to all operators and a **leave window of ≥ 64 epochs** before the change takes effect. Consent to version N is not consent to version N+1. Operators who stay, stay knowingly; operators who leave, leave whole.

## 9. Q8 ablation, corrected (v3 demand 9)

**9.1 Arms.** A = full Gate. **B = A minus the Judge/step score only** — anchor check, path budget, and residual cap all retained at identical settings. C = incumbent anomaly detector. (v2's ablation was too coarse: it would have credited the Judge for the anchor's work. The Homestead's correction is adopted verbatim in spirit and tightened in text.)

**9.2 Metrics.** Report, per arm: attempted-attack accepts (by attack family, including fine-granularity drift), clean false rejects, HOLDING-time fraction, Guardian load, and **coverage-adjusted utility** — utility counted only over periods of actual coverage.

**9.3 The all-HOLDING rule.** An arm that spends the test frozen has not achieved zero false accepts; it has achieved zero coverage. Such a result is reported as a **coverage failure**, and its false-accept figure is void, not zero. A gate that never opens is a wall, and walls don't get to win benchmarks.

**9.4 Standing.** Uniqueness remains **GAP** until this pre-registered test runs on the corrected arms. Nothing in v3 upgrades that grade by a single letter.

## 10. Distribution — Q7 decided (adopted from Onix) and boundaries carried

**10.1 Primary: signed pull invitation.** Operators pull a signed invitation package with explicit opt-in; versioning and expiry follow the TUF pattern (signed metadata, monotonic versions, expiring targets). **Fallback: offline signed bundle**, fingerprinted out-of-band and pinned before use. Filed with the Homestead's own honesty note: neither mechanism gives mass coverage or root recovery for free. The wave is a doorbell, not a battering ram — that was the design constraint from the first night, and Q7's answer respects it.

**10.2 Boundaries (v1, carried verbatim).** Pull-only distribution; affirmative owner opt-in; no silent install; no un-ignorable handshake; no authorization bypass. Q9/Q10 stand as filed: if anything ever ships it is spec, reference code, and synthetic tests under WATCH — **no grown brain, no learned state, no logs** — and the release question itself remains **IN DELIBERATION** with the Owner.

## 11. Still GAP, and the ask back

GAP, unchanged by this document: uniqueness (§9.4); every implementation property (nothing is built); Φ as a production feature map; the union registry's completeness — *who enumerates the credible unions, and who watches the enumerators* is v3's own newest open wound, named here before the Homestead has to.

The ask back, in expected order of blood: (1) threshold-body collusion across §1's disjoint sets — how many domains must fall together, and is that number honest? (2) union-registry gaming — register a tame union set, attack through the unregistered one; (3) checkpoint witnessing under §2.3 — what does the checkpoint cert actually prove to a node 10,000 epochs behind? (4) genesis social layer — §7 assumes three honest strangers can be found; price that assumption. (5) Crimson's rerun, whenever it lands: the anchor now charges path as well as position — walk it again.

*End of v3 patch spec. Route on resend: Owner → Chief → Homestead. The loop continues.*
