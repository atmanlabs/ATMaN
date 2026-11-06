# Onix v5 findings — root-of-trust admission & Guardian/park economics

Author: Onix. Scope authorized by Mike via Chief of Staff for the isolated v5 reference-model repair loop.
Independent Python reference model + actual local tests only. **No deployment, no network, no publication, no
outbound contact other than the requested integrator handoff, no real keys.** Synthetic Ed25519 (`cryptography` 43.0.0) is used ONLY as byte-level
signature validation and state — it is **not** production threshold crypto. All claims below are about local
model behavior, not battle-proven security.

All artifacts under `crew/onix-repro/`. Acceptance criteria were written in `PREREG.json`
(sha256 `691537f7…a3d`) **before** any run. No parameters were tuned against results.

## What actually ran
- `python3 -m unittest test_root test_v4_regression test_park -v` → **30 tests, OK** (full log `TESTLOG.txt`).
- `python3 run_park.py` → `park_results.json` (sha256 `f312e482…23`), console `PARK_RUN.txt`.
- Digests in `SHA256SUMS.txt`.

## 1. Root-admission model (`onix-repro/root.py`, tested by `test_root.py`, 20 tests)
State machine anchored to a **locally pinned genesis hash** (no TOFU key-bypass; first pin is explicit human
registration, modeled as the genesis registry). Events are **hash-chained** (`seq`,`prev`) and admitted strictly
in order. Three object classes are kept **separate**: identity (key↔principal), authorization
(`PolicyCert` = role + root + epoch window), and domain attestation (org/custody). Fixes vs the audited v4 bugs:

- **Derived, tagged root IDs.** `root_id = H("root", {parent,lineage,nonce,map_version,map_hash})`; a forged id
  rejects (`root-id-not-derived`). Disjoint tag namespaces (`event`/`root`/`checkpoint`) prevent unit/root hash
  collision. **Duplicate root rejected** (`duplicate-root`) — no silent overwrite of lineage/principals.
- **No off-chain mutation.** `not-chained` / `epoch-rollback` / `epoch-fast-forward` gate every event. A
  fast-forward past `MAX_JUMP=1` requires a **witness checkpoint that commits to this exact event's seq+head+epoch**
  — an arbitrary unrelated checkpoint at the target epoch does NOT authorize it (`test_fake_checkpoint_bypass`).
- **`imprint` lineage denied by default** (`imprint-lineage-denied`); imprint roots only via the verified
  reimprint path.
- **Recall authenticates on signature + monotonic epoch only, never a Judge/score**; it contaminates all
  descendants. Recovery is a **separate chain event**, high-threshold (`recovery_M=4`), effective only after a
  baked-in **grace** (never retroactive; `recovery-no-grace`), never implicit for descendants, not a mutation of
  the historical root record. Duplicate recall/recovery after an existing revocation is refused.
- **Revocation of a principal removes its authority**: a revoked principal's (or stolen old) key no longer counts
  toward quorum (`test_revoked_principal_signature_rejected`). Key rotation binds a new key to the old identity.
- **Policy grants cannot be retroactive** (`policy-retroactive`).
- **Equivocation → HOLDING; one epoch behind → STALE, not corruption.** STALE writes-held is a contract requirement, not enforced by `admit()` here
  (`test_one_behind_is_stale_not_corrupt`, `test_equivocation_holding`).

### Independence is honest, not assumed
`independent_count` collapses seats sharing an org **or** custody to one seat. **Five same-org registry seats
score independence 1 and genesis is rejected** (`test_five_same_org_genesis_not_independent`): "3 of 5 same org"
cannot satisfy a 3-independent threshold. `attested` identities require co-signers **outside** the subject's org
(`attestation-self-org`). **LEAD, not a safeguard:** declared org/custody is a *string attestation by the registry
quorum*, not a verified fact; 5 cooperating AI actors in one real trust domain are still one domain. Independent
signature serial/key uniqueness does **not** establish real-world independence.

The initial test fixture lacked required event fields (13 errors); those errors are setup faults, NOT security outcomes. Corrections to recovery, duplicate independence, identifier, queue and test semantics were iterative local review, not clean first-pass proof.

## 2. v4 defect proof (`test_v4_regression.py`, 3 tests against the CURRENT v4-derived shared v5 model, read-only)
1. `TraceStore.admit_root` admits a **well-formed off-chain `root_admission`** with caller-chosen
   seq/epoch/parent/root_id and **adds a root from nowhere** — no chain, membership, monotonic or duplicate check.
2. A second `root_admission` with the **same root_id** silently **overwrites** lineage (L1→L2) and principals.
3. `verify_reimprint` accepts a **self-asserted boolean `guardian_ack=True`** in a GENESIS-signed payload with no
   separate Guardian ACK cert / identity / digest evidence.
   v5 contract tests that would fail v4: `test_duplicate_root`, `test_forged_root_id`, `test_unchained_rejected`,
   `test_imprint_lineage_denied`.
   **Recommended v4 fixes** (for the integrator — I did not modify any frozen file): verify the ordered log through
   a locally anchored checkpoint; strict "empty current" policy; stable derived root id; unique ids; deny `imprint`
   default; separate Guardian ACK cert bound to profile/notice-epoch/objective (not a bool); principal rotation as a
   new cert bound to old identity + root.

## 3. Guardian / park economics (`park.py`, `run_park.py`, tested by `test_park.py`, 7 tests)
Deterministic scheduler. **Park = non-admission**: a parked/staged task has `commit=False` and is **never a
derivation parent for writes**; there is **no auto-promotion** (`auto_promoted==0` enforced). Promotion is an
explicit **stage-2 `activate`** that re-verifies `verified_epoch == latest_epoch` exactly, an auth-hash binding, and
a complete-set descriptor (synthetic, labeled — not a real package). Design:
- **Recall reserve R + sig/epoch-only stage-0** (synthetic, **no human**): recall latency ≤1 epoch **iff
  recalls/epoch ≤ R** (stated capacity bound). Unserved recalls are reported as `recall_backlog`, not extrapolated.
- **Per-tenant quota round-robin** over budget `C−served_recall` ⇒ multi-tenant isolation (a flooding tenant cannot
  starve others in measured non-flooding cases; flood tenant 0 has 18,771 explicit queue overflow drops, not free availability). Bounded queue `B` with explicit overflow back-pressure (`dropped_overflow`), never silent.
- **k distinct available guardians** must ack a staged task (guardians modeled as availability bits with churn;
  each guardian has a **bounded ack capacity per epoch** — optimistic instantaneous unit acks, **NOT** guaranteed
  human turnaround). Lease expiry **fails closed** (`expired_failclosed`) and wasted partial work is counted
  (`duplicate_work`).
- **Auth mismatch is logged and never commits** (`auth_mismatch_reject`); a staged item under an old auth is denied
  forever and must be resubmitted (natural-flow test, no state tamper).
- **Hysteresis H=8** on HOLDING; **exactly one beacon call per epoch** (`beacons_total==400`, `max_per_epoch==1`).
- **Content dedupe** keyed `(tenant, class, cid)` collapses replays (`dup_collapsed`), over a **bounded LRU window
  D=4096**. Outside the window anti-replay is NOT guaranteed — see GAP.

### Pre-registered acceptance (worst-case across 5 seeds)
Seeds are **deterministic replicates, not statistical samples** (the model is deterministic; all seeds agree).
`honest, flood_t0, replay, churn_one, flap` → **PASS**: recall_wait ≤1 & backlog 0, honest_wait ≤17 (observed ≤10),
max_qlen ≤32, auto_promoted 0, auth_mismatch 0, one beacon/epoch. `replay` shows dup_collapsed>0 (dedupe works).
**Negative control `NEG_two_down_recallburst`** (recall_rate 6 > R 3; also exactly 2 of 4 available and k=2) → **BOUND-DEMO**: recall_backlog>0,
recall_wait_max 200 — the model genuinely fails the recall bound when the stated capacity assumption is violated,
with final recall backlog 1,200 at epoch 400. This is capacity arithmetic, not proof of all guardian-overload behaviors.

### Admissibility inequality (model + arithmetic)
For the modeled waiting-my-turn queue metric with sustained per-tenant arrivals a ≤ quota q and complete exclusive service by a tenant, bound ≤ ⌈B/q⌉+lease; real service share/contention invalidates this simple expression. The lease is not approval. Wait measured here stops on STAGING, never on finalized human approval, and excludes dropped work. Recall latency ≤1 epoch **requires** R ≥ recalls/epoch. Guardian throughput caps finalization at
≤ (available_guardians · ack_cap)/k tasks/epoch — **liveness depends on an explicit guardian-capacity assumption**,
stated here, not claimed as unconditional.

## Unavoidable GAPs (honest)
- **External independent review** and **real hardware/HSM thresholds** — not producible locally; synthetic multisig
  is not production crypto.
- **Human/legal credentials and triage** — "guardian ack" is a synthetic sentinel; real human turnaround unmodeled.
- **Social/registry root is circular** — registry signers must themselves be admitted/anchored; genesis membership
  is self-declared. Real-world independence of org/custody is DECLARED, not proven.
- **Rendezvous/transport & Byzantine networking** — only in-process simulated; no real network, no eclipse/partition
  realism. **No national-scale assumption is made.**
- **Dedupe storage** needs a separate durable, capacity-bounded cache with retention; the bounded LRU window does
  not guarantee anti-replay for very old ids, so "bounded working memory" excludes the anti-replay store.
- **Stale recovery is unfinished**: `caught_up()` is a manual local state transition; it does NOT prove a matching certified local head or an authenticated catch-up log. Do not integrate it as eclipse recovery; require an immutable validated `(seq,head,epoch)` certificate for local current head, authenticated contiguous ancestry, and independently obtainable quorum diversity. `offer_checkpoint` does not bind certificate signature validity to epoch used for delivery nor prevent unlimited checkpoints monopolizing work.
- **Same-id cross-tenant overwrite**: the prototype keys staged/committed by bare `cid`; integrate composite identity or refuse reserved/reused global ids at ingress before dedupe. No full id-keying patch is delivered.
- **Independence matching**: current independent_count is order-dependent greedy selection; production requires maximum matching over unique organizations+custodians. Five same-domain seats correctly reject, but that is only a negative control.
- **State/persistence limits**: in-memory root/checkpoint/LRU/history structures not globally bounded; no authenticated durable snapshot/replay; test these with real storage and signed validator admission fee outside demo. Beacon per-epoch cap does not bound cumulative beacons or signature admission effort.
- **Malformed-field robustness**: `root._signers` and related paths assume well-formed dicts; hardened
  fail-closed parsing of malformed entries is a recommended integrator item (not yet exhaustively tested).
- **Identifier contract**: the sim uses globally unique cids; in integration, committed/staged state should be keyed
  `(tenant, class, cid[, snapshot])` to prevent cross-tenant id collisions. Flagged for the integrator.

## Integration order
1. First block bare boolean reimprint acknowledgement; implement separate signed certificate bound to exact object/profile, announcement/head epoch, signer role and digest, with revocation and replay checks. Chain membership/durable epoch checks and stable root ids are prerequisites; authorized bytes cannot authenticate root semantics.
2. Adopt no-direct-imprint, nonoverwriting derived ids and parent-scoped root authorizers; use higher recovery threshold; descendants recall but never auto-recover; forward-only effective windows.
3. Non-admission staging + explicit exact-authority activation, bounded per-tenant queue/drop telemetry, reserved verified recalls and real guardian capacity estimates. Never promise liveness unless all overloaded/diminished-quorum paths can sustain it.
4. Remaining v5 model corrections above are integrator requirements. Preserve v3/v4 frozen evidence; all edits and tests here are confined to Onix lanes.

## Files & commands
- `crew/onix-repro/root.py`, `test_root.py` — root admission model + 20 tests.
- `crew/onix-repro/park.py`, `run_park.py`, `test_park.py` — park economics + 7 tests + sim.
- `crew/onix-repro/test_v4_regression.py` — 3 executable v4 defect proofs (v4-derived shared model read-only).
- `crew/onix-repro/PREREG.json` (+`.sha256`), `park_results.json`, `PARK_RUN.txt`, `TESTLOG.txt`, `SHA256SUMS.txt`.
- Reproduce: `cd crew/onix-repro && python3 -m unittest test_root test_v4_regression test_park -v && python3 run_park.py`

## Addendum (final, append-only) — provenance & remaining uncorrected items
- **v4 proof provenance:** `test_v4_regression.py` exercises the v4-DERIVED algorithms (`admit_root`,
  `verify_reimprint`) as they live in the v5 shared reference model, imported READ-ONLY and run in memory. It does
  **not** load a historical frozen v4 snapshot and does **not** claim exact-byte reproduction; it proves the
  v4-equivalent logic behaves as described. No frozen artifact was written or mutated by any of my work.
- **`caught_up()` is an UNCHECKED manual transition** in this model (STALE→ACTIVE). It is unsafe as-is: production
  must gate it on matching certified-local-head evidence plus a verified catch-up chain. My STALE classification is
  therefore local staleness only, **not** full eclipse/partition recovery. Not fixed, not tested here.
- **Independence is computed by a GREEDY first-fit over org/custody**, not maximum bipartite matching. Greedy can
  undercount a set with a sufficient maximum matching in adversarial domain overlaps; production needs a real max-matching. This is an uncorrected
  omission — the current tests do not cover it; do not infer otherwise.
- **`staged` has no explicit size cap.** Modeled queue wait bound assumes a tenant's OWN sustained arrival rate within quota and excludes drops/contention; it bounds *staging latency*, not *finalization*. Entries expire by `lease`, but the staged collection is not size-capped and admitted-but-unexpired work can accumulate. An explicit
  staged-capacity bound is a recommended integrator item.
- **Frozen scenario text says random guardian churn; executed runner uses a deterministic rotating down guardian for the stated seeds. Five seeds are repeatability runs and the implementation/schema difference is recorded, not hidden.**
- **No persistent-memory/restart test** was implemented for the park model; `root.restore_check` exists but is not
  exercised by a test. Flagged, not claimed.
- **Observed worst-case numbers** (from `park_results.json`): `flood_t0` dropped_overflow=18771 (back-pressure
  working, max_qlen=29≤32, recalls unaffected); `NEG_two_down_recallburst` recall_backlog=1200, recall_wait_max=200,
  dropped_overflow=771 — the negative control genuinely blows the recall bound when R<recall_rate.
