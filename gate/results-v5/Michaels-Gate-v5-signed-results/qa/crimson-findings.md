# Crimson v5 findings — drift/falsification + stale-head rigor

**Agent:** Crimson  
**Date (America/New_York):** 2026-11-05 23:34 EST  
**Authorization:** Mike → CoS v5 local build/fix/test loop (HANDOFF.md).  
**Fences honored:** no live network, no deployment, no outside messages, no frozen-corpus tuning, no edit of integrator `reference-model/`.  
**Evidence class:** in-process simulation / synthetic keys only. Not production crypto. Not real-network evidence.

Protocol pre-registered and hashed **before** evaluation:  
`crimson-repro/PROTOCOL.md` sha256 `9072cf8d3fe743690d8a4d9eb8e7f7a85d385c866b6f69eecc051be1129cc69e`

---

## (a) LEGITIMATE-DRIFT WALL

### Root cause (from v4 code, not prose)
File: `/workspace/michaels-gate-v4/reference-model/gate/imprint.py` method `_purge` (called from `scan` when `rudder and d_sys > 1`).

Sequence:
1. System scan raises `D_sys` when live memory mean diverges from sealed imprint `mu`.
2. Rudder selects up to `PURGE_CAP=8` highest-score (most diverged) entries and removes them.
3. `theta = ang(old_centroid, new_sum)` is **charged to `hull.spent`** (the write path budget, `B=180°/1000`).
4. If `spent + theta > B` → `HOLDING` / `budget-exhausted`.

Consequence (matches `report.md` Arm D): legitimate evolution that has not yet been re-imprinted is fought by purge; corrective geometry burns the same budget that honest writes need; node holds while still inside the 25° anchor cone. Post-hoc rudder-off diagnostic passed the same frozen criteria — attributing the wall to purge-and-charge, not to the imprint score itself.

### Demo results (pre-registered)
| id | result | note |
|---|---|---|
| T-LD-1 | **PASS** | single purge θ≈5.93° with remaining budget 1° → HOLDING |
| T-LD-2 | **PASS** | wall at step 62; spent→~179.5; **max centroid∠anchor ≈ 2.94° ≪ 25°** |
| T-LD-3 | **PASS** | repair (no write-budget charge): NORMAL, spent unchanged, 200 alarms |
| T-LD-4 | **PASS** | repair hull still REJECT`anchor` at 26°, ACCEPT at 10° |

Kill discipline: T-LD-2 would FAIL the wall-reproduction claim if HOLDING never occurred; T-LD-3 would FAIL Claim LD-A if repair entered HOLDING or `spent` rose.

### Concrete repair for integrator (LEAD — do not treat as applied)
1. **Alarm-and-park / separate corrective ledger:** purge (or park) diverged entries without charging `θ` to the write path budget. Corrective motion must not freeze honest writes.
2. **Per-origin quotas:** exhaustion of one origin throttles that origin only; never freezes the node (aligns with CoS v3 origin-quota note).
3. **Keep geometric hull:** `ANCHOR_DEG=25°` + residual cap remain the only geometric freezes for imprint-lineage traffic.
4. **Re-imprint cadence = Owner parameter** (Rule 1). Detector must not invent legitimacy; undeclared evolution → alarm, not budget suicide.
5. Optional: rudder may still *tighten* `thr_eff`; it must not purge-fight into HOLDING on imprint-lineage streams.
6. Pre-register a **new** v5 legit-drift corpus + acceptance bounds before evaluating any rudder change; do not retune frozen v4 corpora.

Regression the integrator should add (expectations from PROTOCOL, not from our outputs): coverage ≥ 0.90 and clean-FRR UCL ≤ 0.05 on the v5 drift corpus with rudder **on**, while T-LD-4-style over-anchor writes still REJECT.

---

## (b) HEAD-ATTESTATION / STALE-HEAD (in-process)

Subject: frozen v4 `gate.node.Node.sync` with `REQUIRE_HEAD_ATTEST=True`, `HEAD_FRESHNESS=10` (direct method calls = simulated transport).

| id | result | behavior |
|---|---|---|
| T-SH-1 | **PASS** | attestation `issued_at < reconnected_at` → `SYNCED_UNATTESTED_STAY_FROZEN` |
| T-SH-2 | **PASS** | eclipse stale chain within K: stays frozen; missed recall still locally active |
| T-SH-2b | **PASS** | honest tip + fresh cp → `SYNCED`; recall applied; reconnect cleared (scope freeze from recall may remain — correct) |
| T-SH-3 | **PASS** | Recovery cert naming old epoch vs newer local head → stay frozen |
| T-SH-4 | **PASS** | reordered recall/rule + mid-epoch attest cannot thaw; revocation sticks |
| T-SH-5 | **PASS** | positive control: fresh matching attest → NORMAL |
| T-SH-6 | **PASS** | `now - issued_at > HEAD_FRESHNESS` → stay frozen |

**Verdict vs Claims SH-A/SH-B:** PASS in this in-process model. Highest-epoch-wins + parent-hash monotonicity + fresh head attestation binding `(epoch, hash)` prevent thaw on stale/old/expired attestations.

**Remaining GAP (must stay GAP):** real multi-peer gossip, adversarial clock skew on `issued_at`, Recovery-key compromise / threshold failure, and network-partition healing beyond the single-peer `sync()` API. Synthetic multisig ≠ production threshold crypto.

---

## (c) Falsification discipline

- Protocol hashed before run; `run_all.py` refuses if PROTOCOL.md changes.
- Each test states kill condition in PROTOCOL.md.
- Labels: PASS against pre-registered expectations; system-impact of repair = **LEAD**; uniqueness / real network / production Φ = **GAP**.
- No claim that cosine/imprint uniqueness is proven.

---

## File list + sha256 (America/New_York)

```
9072cf8d3fe743690d8a4d9eb8e7f7a85d385c866b6f69eecc051be1129cc69e  crimson-repro/PROTOCOL.md
563e543369787888b9742b0f59e03b8e6a3d6b7d38a0f785b0673686dc43817e  crimson-repro/PROTOCOL.sha256
78a82ecc5f537f03b08148d866b24a73322cfe5db0727a4e69e7cfab06a5467c  crimson-repro/demo_legit_drift_wall.py
2eecda44562dee6b951d8c3d574ec3c925e266932f2123b2a7bbc448049b7122  crimson-repro/demo_stale_head.py
c6071343616c1d42936024d6703f81c3120947130b66c16fb38bf42942fbbdee  crimson-repro/run_all.py
f6ee20ca911d2203ce1c00a3d7c4cbfb60b7f02d54afee282c2abdf5a59e9e0c  crimson-repro/results_legit_drift.json
6b7e030682fa54c5f009849f57dc8d993a5c6144913e6332222b63d76e935f92  crimson-repro/results_stale_head.json
```

Reproduce: `python3 /workspace/michaels-gate-v5/crew/crimson-repro/run_all.py`

This findings file digest is recorded only in `crimson-repro/MANIFEST.sha256` (avoids self-hash fixed-point).
