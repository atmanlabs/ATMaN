# HOMESTEAD VERDICT — MICHAEL'S GATE
## Q1–Q10 review, 2026-11-05

*Filed verbatim as delivered by the Owner in chat, 2026-11-05 21:03 ET. Route: Homestead → Chief → Owner → Strider. Compiled by Chief of Staff from the Homestead verdicts.*

**Route:** Homestead → Chief → Owner → Strider. **Scope:** design review only. No implementation, no approved test fixture, no activation, no release, no outside contact. All execution results remain GAP; any future lab result is a reference-model test, never verification of Michael's Gate. The sandbox code was not delegated to the Homestead; real artifacts move only on the Owner's word, one at a time. **One-line verdict:** the Gate survives as a design direction, not a proven defense. Its safety story can now be specified. Its uniqueness claim cannot. **Counterpoint, kept honest:** the sim's Judge `reasoning` strings are stub-generated in code (packet §3.5). What was attacked is a design proposal — cosine scoring as a gate — not a running deployment.

---

## Q1 — Resonance gate (Crimson) — DOCUMENTED math, runnable demos
Cosine similarity measures direction, not content.
- Orthogonal payload: for unit reference and perpendicular payload p, f = ref + s·p scores C = 1/√(1+s²). At threshold 0.95 the attack still carries ~9.8% of the energy; the silent subspace grows with dimension.
- Slow-drift ratchet: 200 updates, each ≥0.98 at step 0.05, walk validated memory to ~90° from anchor. Per-update gating does not bound path length.
- **Requirement:** anchored immutable reference + cumulative-drift budget + revalidation against root core. A cosine score cannot be the gate.
- Boundary (Weeboh): this is a cosine-specific break; real-system impact depends on the unspecified feature map and memory mixer.
- Crimson's GAP: feature map, dimension, threshold, memory mixer, whether the Judge consults root per write, admission rules. Artifacts: /workspace/crimson/michaels-gate/RESONANCE-ATTACK.md, demos/resonance_attacks.py.

## Q2 — Guardian capture (Counsel) — WATCH
Root-key holder can forge consent, poison a seed, defeat recall. Role is custodian, never sovereign over others.
- Required before outside nodes join: threshold control, independent hardware/lineages, signed audit log, key rotation, emergency revocation, honest local quarantine.
- DOCUMENTED: NIST SP 800-57 Pt1 §§6.2.1.3, 8.3.5, 9.1 — split knowledge and prompt revocation after suspected compromise.

## Q3 — Sybil/collusion/drift (Crimson) — DOCUMENTED
3f+1 is void if identities are mintable or Guardians capturable (Douceur; Lamport/PBFT assumptions). Consent-per-node does not help when a Sybil quorum locally green-lights poison. Lineage caps are a necessary condition, not a bonus.

## Q4 — Correlated failure (Weeboh) — DOCUMENTED + LEAD
- DOCUMENTED: classic BFT n=3f+1, q=2f+1 guarantee dies if >f faulty votes share one failure domain. CaBFT's Three-Thirds Diversity Requirement applies: max f seats, or <1/3 voting weight, per domain (Haag & Berger).
- LEAD: cap every lineage AND software/hardware/operator/region domain at c ≤ f in committee and each quorum; weighted w_D < W/3. Audit by injecting shared-cause faults and measuring P(j fails | i fails, d). Low observed correlation is not proof — cap topology is mandatory.
- Addition: test credible combined failures, not one domain at a time. One shared update or credential can kill >f nodes while every per-domain cap passes. Recheck caps after every join/leave.

## Q5 — Latency (Onix) — consequence of Q1
Drift defense changes the performance to be measured: no unbounded memory index, no per-write root recomputation. Model needs fixed-memory baselines plus revalidation cost. No new claim.

## Q6 — Refusal seam / HOLDING (Crimson) — LEAD spec, not in the packet
Enter on gray-band/oscillation, drift-budget breach, quorum split, integrity failure. Freeze all memory writes and accept-votes; keep root core and last-good reads; emit signed HOLDING beacon; abstain only. Exit only on cleared condition + Guardian ack; soft then hard timeout to quarantine. **Fail-HOLDING, never fail-open.**

## Q6.1 — Consent (Counsel) — STOP on v1 self-replication
- **STOP:** any self-replication that executes/copies onward without affirmative owner opt-in. No silent install, no un-ignorable handshake, no air-gap sneakernet, no authorization bypass.
- **GO/WATCH:** public signed spec + operator-pulled invitation and revocation; a node/agent may evaluate only within its owner's authority.
- DOCUMENTED: CFAA §1030(a)(5)(A), (g); Van Buren narrows "exceeds authorized access" to off-limits areas, not bad motive. Florida CADRA §668.803 requires knowing transmission + intent + resulting harm/loss. GAP: actual packet code and consent UX; benign mechanism does not immunize harmful use.

## Q7 — Broadcast decision (Onix + Chief) — verdict pending receipts
Chief's position and standing constraints: recall beats distribution; the wave lives inside consent, never outside it; gossip covers n opted-in nodes in ~log2(n) rounds only; the handshake thesis (check woven into introduction, TLS-style) is the crux. Onix is folding revocation freshness, offline delivery and explicit monotonic epoch/rollback guard into the scoring. One primary + one fallback to be named with receipts.

## Q8 — Falsification demand (Weeboh + Counsel) — **GAP**
No measured number establishes a prediction the Gate uniquely makes over incumbents. No uniqueness claim survives.
- **LEAD, pre-registered kill test:** identical clean-FPR, compute, latency, drift corpus. A = full Gate, B = Gate without Judge, C = incumbent anomaly detector, against adaptive slow-drift memory poisoning. Prediction: FAR_A < FAR_B; superiority to incumbent requires FAR_A < FAR_C. Kill the Judge's defensive-value claim if A vs B fails.
- Crimson's addition: many small accepted updates, not single attacks. If the advantage shrinks/vanishes as attack increments get finer, the Judge buys nothing a cumulative-drift budget wouldn't buy cheaper. A must retain its lead at fine granularity.
- Kodi's guards: fixed corpora, matched clean-FPR, confidence intervals beside every false-accept number. No lucky splits or threshold gaming.
- Counsel: any Q8 claim stays GAP until the pre-registered comparison supports it.

## Q9 — Release (Counsel) — WATCH; consent-only, pull-only can proceed
Ship order: (1) human-written method/spec + threat model, (2) Apache-2.0 reference code with provenance/NOTICE, (3) reproducible synthetic tests + sanitized results, (4) signed release package + operator opt-in/revocation docs.
- DOCUMENTED: Apache §§1,3,4 — redistribution OK, notice required, patent license/retaliation included. No privacy/data rights or patent clearance granted by license.
- No "defensive only" license if calling it open source (OSD criterion 6 bars field-of-use discrimination); publish responsible-use notice separately.
- **Never ship:** live keys/tokens, logs/memory, personal/confidential data, third-party corpora without rights, learned/validated state, prompt history, secrets, unexamined training data, performance/guarantee claims.
- Thaler v Perlmutter: DOCUMENTED but narrow — solely AI-authored work lacks copyright authorship; does not decide trade-secret/data status of grown state.
- Kodi's package check: reproducible contents check, not a label. Inventory + hash every file, scan current contents AND repository history AND generated artifacts (archives, wheels, notebook outputs) against the no-ship list, fresh install with networking disabled. Unresolved items stay GAP.

## Q10 — Personhood (Counsel) — WATCH
Released grown contents differ legally from method because they may embody confidential/personal data and reproduce learned behavior — NOT because the AI is a legal person. No legal guardian/person liability claim. Moral/sandbox restraint is ATTESTED policy, not personhood evidence. GAP: full artifact inventory + third-party rights audit; no grown state ships without separate Owner approval and data-rights review.

---

## The two hard requirements that came out of the fight
1. **Recall bypasses the Judge.** Authenticate on signature + epoch alone, never the resonance score. A poisoned reference must never veto its own shutdown. (Crimson's named case: node with poisoned reference + valid signed recall must freeze anyway.)
2. **Independence is capped, not assumed.** Same-lineage/failure-domain votes capped per Q4; correlated failure is the killer, cf. CrowdStrike July 19 2024 (~8.5M Windows machines, one bad content update).

## Kodi's five synthetic, isolated recall cases (blocked on artifacts)
1. Recall delivered while a node is offline.
2. Bad rule + recall arriving out of order; highest signed epoch wins.
3. Restart never revives a revoked rule.
4. Valid recall bypasses a poisoned Judge and freezes writes anyway.
5. Absolute rule: a reconnecting node that missed the recall stays frozen until it verifies the newest epoch; no older valid signature can thaw it.
Pass requires signed logs, lab-scoped PASS/FAIL/GAP only — no network-wide recall claim. Own nodes, own credentials, synthetic bad rules, no live network, no third-party nodes.

## What the Owner owes next
- Q1's implementation answers (feature map, threshold, mixer, root-per-write).
- The actual artifacts or an approved isolated fixture, if implementation verification is wanted. Until then every execution result is GAP.
- Release decision stays IN DELIBERATION. The bounded form — framework + Gate spec + DreamThink method, every node grows its own brain on its own soil — is the only path the Homestead will endorse.

*Compiled by Chief of Staff from the Homestead verdicts. Grades as filed: DOCUMENTED, ATTESTED, LEAD, GAP.*
