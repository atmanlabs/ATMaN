# V5 F2: implementation revision. Pre-registered BEFORE any F2 evaluation.
F1 (commit 9f4845a) is immutable: DESIGN WALL, failing A4 and A6. F2 changes implementation only.
Unchanged: frozen corpora (F1_FROZEN), thresholds, anchor/path/residual hull, reimprint cadence, and acceptance A1–A9 (q8F.acceptance, imported unchanged).
A4 is expected to fail again. It is a wall in the inherited residual and reference model: arms A and C show the same drift5 false-reject rate.
F2 does NOT attempt A4. In particular, it neither drops nor relabels rare samples and does not change the hull, the residual, or the cadence.

## 1. Lineage-scoped non-imprint memory cap (fix for A6)
- At admission, a resolved unit whose ancestry is not fully imprint (iota < 1) is not admitted if live memory's non-imprint fraction would then exceed NI_CAP = 0.25.
- Rationale for 0.25: it sits below the test bound of 0.30 and well above the declared legitimate external share (drift5 8%, holdout5 5%). It was chosen from the spec, not from results.
- A unit over the cap goes to the bounded park queue. It is not admitted, it expires to refusal (T_EXP), and per-origin caps apply.
- There is no write-budget charge and no purge. Existing memory is never evicted to make room; the cap only gates new admissions.
- Clean items parked by the cap count as false rejects in the harness, as F1 already does.

## 2. Onix integration (crew/onix-findings.md, sha256 c596e7b1…)
1. **Roots:**
   - Roots are admitted only from the contiguous verified chain followed from a pinned genesis (the genesis entry also pins the single genesis imprint root).
   - Root ids are derived as H(lineage, nonce, principals).
   - Duplicates, overwrites, principal rebinds, and lineage="imprint" are refused.
   - Malformed input fails closed.
2. **Reimprint authority:** reimprint needs a separate RECOVERY t-of-n Guardian ACK certificate bound to the profile hash, notice epoch, reimprint epoch, and objective. The boolean flag is no longer enough.
3. **Independence:** counted by bipartite maximum matching of seats (org↔custody). Labels are DECLARED facts, not verified facts.
4. **Catch-up:**
   - Requires a fresh RECOVERY-certified checkpoint plus a contiguous verified entry list that reaches exactly the certified (epoch, hash).
   - Anything else stays STALE. There is no manual caught_up().
   - Real gossip, clock skew, and partition remain GAP.
5. **Staging:**
   - Staging is bounded at STAGED_MAX = 16.
   - Identities are composite (tenant, class, cid). Replays collapse, and the same cid from another tenant never overwrites.
   - Malformed staging requests are refused.
6. **Persistence:** a sealed snapshot of authority and lineage state is restored across a restart. Revocations persist, and a tampered snapshot is rejected. This is in-memory JSON, not a durable authenticated store (GAP).
7. **Capacity arithmetic (literal):**
   - Recall latency ≤ 1 epoch only if R ≥ recall_rate.
   - backlog = (rate − R) × epochs. Onix's negative control gives 1200.
   - Finalization ≤ available × ack_cap / k.
   - No liveness is claimed without the stated guardian capacity.
   - Guardian ack in this model is a synthetic certificate. It is non-admission staging, not real human review.

## 3. Evaluation
- q8F2.py runs arm F (= GateF2) on every family. A–E comparators are the immutable F1 file.
- The acceptance function is q8F.acceptance, unchanged.
- The test suite runs all of: v3 battery, v4 imprint/trace, v5 union, v5 gateF, and v5 F2.
- Any later change is F3, registered first.
