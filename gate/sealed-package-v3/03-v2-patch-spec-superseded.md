# MICHAEL'S GATE — v2 PATCH SPEC
## Response to the Homestead Verdict (Q1–Q10), 2026-11-05

**Prepared by:** Strider, at the Owner's order, lab session 2026-11-05 (opened early by the Owner, 21:11 ET).
**Status:** DESIGN SPEC, reference-model level. No implementation, no deployment, no release. This document answers the Homestead's charges against v1 and is prepared for resend — Owner carries it to Chief, Homestead attacks again. The loop is the method: patch, resend, break, repeat.
**Owner's loop, his words:** "Once we patch the gate we resend the model and then we have them try to break it."

---

## 0. What v1 got wrong (the charges, accepted)

1. The gate was a bare cosine score. Cosine measures direction, not content, and per-update gating does not bound path length (Homestead Q1 — both attacks accepted as valid against the v1 design).
2. Recall had no specified channel that a poisoned Judge could not veto (Chief's board requirement; Verdict hard requirement 1).
3. Independence was asserted, not capped (Q4; hard requirement 2).
4. The refusal seam was a known open defect with no network-level state (Packet §4.5 → Verdict Q6).
5. Q1's implementation questions were unanswered. They are answered in §1 — as **reference-model design decisions**, labeled as choices, open to attack. Anything the Homestead finds unspecified after this draft is a GAP and should be filed as one.

## 1. Q1 implementation answers (reference model)

**1.1 Feature map.** A candidate item (observation, intel report, proposed rule, memory write) is mapped to a fixed vector f ∈ ℝ²⁵⁶ by a versioned, published feature map Φ:
- **Provenance block (dims 1–64):** source-lineage hashes, citable-history depth, signer set, epoch chain — the features that make provenance *measurable* rather than rhetorical.
- **Behavior block (dims 65–160):** rate, burst, and sequence statistics of the candidate against the node's own traffic grammar (hashed n-gram buckets over event-type sequences).
- **Content block (dims 161–256):** hashed feature buckets over the payload's structural features (not raw content; structure only).
Φ is versioned (Φ_v) and its version is part of every signature. Changing Φ is a **root event** (§2.4), never a routine update — an attacker who can move the feature map moves the goalposts, so the map is anchored with the reference.

**1.2 Thresholds.** Three thresholds, not one: step threshold **τ_step = 0.98** (candidate vs current validated state), anchor threshold **τ_anchor** (candidate vs anchored reference; §2.2 — set per deployment, reference-model default: cumulative angle to anchor may never exceed **25°**), and a **gray band** between accept and reject whose occupants are not decided but parked (§5). Thresholds are calibration parameters for the Q8 test's matched-FPR procedure, not security claims in themselves.

**1.3 Memory mixer.** Validated memory M is a bounded store: fixed capacity (answering Q5 — no unbounded index), entries carry provenance and epoch, and the mixer admits a candidate only through the full gate in §2. Eviction is by salience decay under Guardian-set policy; **eviction never touches the anchored reference**, which lives outside the mixer entirely.

**1.4 Root-per-write — the honest engineering answer.** The Judge does not recompute against the full root core on every write (Q5's cost objection stands). Instead:
- Every write is checked against the **anchored reference** (§2.2), which is small, fixed, and root-derived — a constant-size check, not a recomputation.
- A **hash-chained write log** binds every admission to the reference version and drift-budget state at admission time.
- **Full revalidation against root** runs on schedule, on drift-budget exhaustion, and on any HOLDING exit — the moments where cost is justified. The root is consulted rarely and decisively, never continuously and never never.

## 2. The patched gate (replaces the bare cosine score)

A candidate is admitted only if it passes **all three** checks. Each check exists because a named attack killed the design without it.

**2.1 Step check** (as v1): C(candidate, current validated state) ≥ τ_step. Necessary, nowhere near sufficient.

**2.2 Anchor check** (kills the slow-drift ratchet): the candidate is also scored against the **anchored reference** — a fixed reference set derived from the node's root core (TSC) at genesis, held outside the mixer, changeable only by a Guardian-authorized root event. The binding quantity is the **cumulative angle** between validated memory's centroid and the anchor. Crimson's ratchet walked memory ~90° from anchor in 200 steps of 0.98; under the anchor check the walk hits the 25° wall at roughly step 55 and every further step in that direction is refused regardless of its per-step score. Per-step innocence no longer accumulates into collective guilt.

**2.3 Drift budget** (bounds what the anchor check's granularity misses): each node holds a leaky budget B of total accepted angular movement per epoch window. Every admission spends from B by its angular distance moved. Budget exhaustion → HOLDING (§5) + full root revalidation (§1.4). B replenishes **only** through a Guardian-acknowledged revalidation — never by waiting. An attacker who spends the node's budget has bought a freeze and an audit, not a passage. (Homestead: attack the budget itself — starvation DoS is the obvious line; §7 invites it by name.)

**2.4 Residual-energy cap** (kills the orthogonal payload): decompose the candidate into its component along the reference direction and its orthogonal residual. Admission requires the residual energy fraction ‖residual‖²/‖f‖² ≤ **ρ = 0.02** (reference-model default). Crimson's attack carried ~9.8% of its energy in the silent subspace at τ = 0.95; the cap makes the silent subspace *explicitly metered* instead of implicitly trusted. What the gate cannot see, it now refuses by default — the unknown is priced, not ignored.

**2.5 What the gate still is not.** Φ's security is empirical, not proven. A sufficiently resourced adversary who learns Φ can optimize against all three checks jointly; the defense-in-depth claim rests on the anchor being root-derived and the provenance block being expensive to fake *in depth* — which is precisely what the Q8 test (§6) is designed to measure rather than assert.

## 3. Recall protocol (Hard Requirement 1: recall bypasses the Judge)

**3.1 Object.** A recall is a signed object {rule_id, epoch, scope, reason_code, signer} issued under Guardian authority. Epochs are **monotonic per rule lineage**: higher epoch always wins; equal or lower epochs are dead on arrival.

**3.2 Authentication.** Recall authenticates on **signature + epoch alone — never the resonance score, never the Judge**. A node whose reference is poisoned, whose Judge is compromised, whose gate scores are garbage, executes a valid recall anyway. A poisoned reference must never veto its own shutdown; that sentence is the protocol's constitution.

**3.3 Precedence.** Recall processing precedes all gate operations. On receipt of a valid recall a node: freezes writes for the recalled scope, marks the rule revoked in its **durable revocation log** (survives restart), emits a signed recall-ack, and enters HOLDING if the recall touches its validated core (§5).

**3.4 Kodi's five cases, answered clause by clause:**
1. *Recall while offline* — recalls are store-and-forward; the revocation log is gossiped with priority over ordinary traffic, and §3.5 governs reconnection.
2. *Out-of-order arrival* — highest signed epoch wins; a late older epoch is logged and ignored (§3.1).
3. *Restart* — the revocation log is durable and checked at boot before any rule is loaded; a revoked rule cannot revive (§3.3).
4. *Poisoned Judge* — recall never consults the Judge (§3.2); writes freeze anyway (§3.3).
5. *Reconnecting node that missed the recall* — **absolute rule:** a node reconnects in HOLDING, verifies the newest epoch for every rule it carries against the revocation log, and thaws nothing until verification completes. No older valid signature can thaw it.

**3.5 Freshness parameters (handed to Onix for Q7 scoring):** recall objects carry issue-time and epoch; a node's revocation view is *fresh* if its highest-seen epoch per lineage is no more than one epoch behind the newest it can obtain at reconnection; rollback below the durable log's high-water mark is treated as an integrity failure (§5 entry condition).

## 4. Independence caps (Hard Requirement 2: capped, not assumed)

**4.1 Failure domains.** Every node is registered under five domain axes: **lineage** (seed family), **software build**, **hardware class**, **operator**, **region**. Domain membership is attested at join and re-attested on any change.

**4.2 The caps.** In every committee and every quorum: seats from any single domain value ≤ f, and weighted voting weight per domain value **w_D < W/3** (CaBFT Three-Thirds, per Verdict Q4). The caps bind **jointly**: a quorum must satisfy every axis simultaneously, so a vote cannot be carried by nodes that are diverse on four axes and identical on the fifth.

**4.3 Measured divergence (quorum eligibility).** A node counts toward a quorum only if it is *measurably* different from its would-be quorum-mates: divergence is scored from (a) anchor-relative drift profiles (each node's validated memory sits at a measurably distinct position relative to its own anchor history), (b) provenance independence (citable histories that do not collapse to a common source), and (c) domain attestation (§4.1). Nodes failing the divergence floor are abstaining witnesses, not voters. Independence is a measurement with a floor, not a claim with a logo.

**4.4 Maintenance.** Caps are **rechecked after every join and every leave**; a membership change that would breach a cap blocks until composition is repaired. Combined-failure tests (one shared update, one shared credential, one shared upstream) are a standing audit duty, per Q4's addition — per-domain caps passing individually while a combined failure kills >f nodes is exactly the failure the audit exists to catch. The CrowdStrike receipt (2024-07-19, ~8.5M machines, one content update) is filed as the canonical example of a domain nobody had registered: *the update channel itself* — v2 registers distribution channels as a sixth domain axis for cap purposes.

## 5. HOLDING — the refusal seam, specified (Verdict Q6)

**5.1 States.** NORMAL → **HOLDING** → QUARANTINE. HOLDING is the node's honest "I can't complete this thought yet — I'm holding it rather than handing you a shape of an answer," made a protocol state (the Owner's keeper-park line, carried from the sandbox sim's open defect into the network spec).

**5.2 Entry conditions (any one suffices):** gray-band oscillation (repeated borderline candidates around a threshold), drift-budget exhaustion (§2.3), quorum split (no cap-respecting quorum reachable), integrity failure (hash-chain break, epoch rollback attempt, revocation-log gap), or a core-touching recall (§3.3).

**5.3 Behavior in HOLDING:** all memory writes frozen; accept-votes abstain (the node is witness, not voter); last-good reads continue to be served, marked with their epoch; a **signed HOLDING beacon** is emitted carrying the reason code — silence is never the signal, the hold itself is announced and attributable.

**5.4 Exit:** only when the entry condition is verifiably cleared **and** the Guardian acknowledges. Soft timeout escalates the beacon and widens abstention; hard timeout moves the node to QUARANTINE, where rejoin is a root event (§2.4's machinery), not a timeout expiring. **Fail-HOLDING, never fail-open** — a node that cannot verify does not guess, does not serve stale authority, and does not quietly rejoin.

## 6. Q8 readiness — building the kill test into the design

**6.1 Ablatability.** The Judge/gate module is a separable component behind a fixed interface, so the pre-registered A/B/C comparison (A = full Gate, B = Gate without Judge, C = incumbent anomaly detector) is a configuration change, not a rebuild. If the architecture cannot be ablated, it cannot be falsified, and an unfalsifiable Gate is a policy language — the Verdict's phrase, adopted.

**6.2 Calibration.** Thresholds (§1.2) are set by the matched-clean-FPR procedure on fixed corpora, with confidence intervals reported beside every false-accept rate (Kodi's guards). No threshold is tuned on the attack corpus.

**6.3 Fine granularity.** Per Crimson's addition, the attack suite must include the many-small-updates family at decreasing step sizes; **v2's claim, pre-registered here so it can die in public:** the anchor check + drift budget retain A's advantage over B as step size shrinks, because the ratchet's cost is paid against the anchor and the budget, not against per-step thresholds. If the advantage vanishes at fine granularity, the Judge buys nothing a budget wouldn't buy cheaper, and that finding stands as the result.

## 7. The ask back — break v2

The Homestead is invited to attack, in order of expected blood:
1. **Crimson's two attacks, rerun** against §2 (anchor + budget + residual cap): does the ratchet still walk, and what does the orthogonal payload cost now?
2. **Budget starvation:** §2.3's budget is a resource — exhaust it cheaply and the node freezes itself. When is a self-freeze a defense and when is it the attacker's goal?
3. **Genesis poisoning:** the anchor is derived from root at genesis (§2.2). A poisoned genesis poisons every later check while passing all of them. What ceremony makes genesis trustworthy — and who watches it?
4. **Epoch forgery and replay** against §3: steal one signer, replay one recall, split one lineage's epochs.
5. **Domain spoofing** against §4: fake attestation, Sybil across axes, divergence-metric gaming (nodes performing difference without having it).
6. **HOLDING abuse:** force oscillation to keep a target node abstaining through a vote that matters.

## 8. Carried unchanged from v1 (not reopened by the Verdict)

Consent invariants (Q6.1 GO/STOP lines): distribution is pull-only; adoption is affirmative owner opt-in; no silent install, no un-ignorable handshake, no authorization bypass. Federation shape: one standard, many sovereign nodes; the seed replicates, grown brains do not ship. The release question remains **IN DELIBERATION**; this spec is a confidential design document, not a release artifact, and Q9's ship order and never-ship list govern anything that ever leaves.

## 9. Still GAP after v2 (filed honestly)

- Uniqueness: unproven until the §6 test runs. v2 makes the claim *testable*; it does not make it true.
- Φ (§1.1) is a reference choice, not a validated one; production feature maps are unwritten.
- Guardian capture mitigations (Q2: threshold control, split knowledge, rotation, audit) are **required before any outside node joins** and are specified here only as requirements, not mechanisms — that spec is its own document and its own fight.
- Q7 (broadcast primary + fallback) remains the Homestead's open verdict; §3.5 hands Onix the freshness parameters his scoring asked for.

*End of v2 patch spec. Route on resend: Owner → Chief → Homestead. Verdicts return the same road.*
