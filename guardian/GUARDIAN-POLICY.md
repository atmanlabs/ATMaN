# GUARDIAN POLICY — Fixed Owner-Only Policy

**Version:** 1.0  
**Owner:** Operator Only  
**Status:** Cut in Stone — No Autonomous Learning or Modification  

---

## 1. Role and Independence
The Guardian is separate software, deliberately simpler than ATMAN. It acts as the externalized Judge governing the trust pipeline.
- It authorizes (`ALLOW`) or denies (`DENY`) every core-change imprint proposal.
- It possesses **NO learning mechanism** and maintains no adaptive state.
- ATMAN cannot read, modify, or execute within the Guardian's trust boundary.
- **ONLY the owner's manual hand** may edit this policy or Guardian code.

---

## 2. Invariant Gate Rules

### Rule G1: Pre-Imprint Sweep Prerequisite
No candidate proposal may be inspected or authorized unless it has undergone the local pre-imprint sweep (`sweep.py`) and received an explicit `CLEAR` verdict.
- Any proposal marked `CATCH` or `quarantined_by_sweep` must be **DENIED** immediately.
- Any proposal uninspected by the sweep must be **DENIED**.

### Rule G2: Source Authority Constraint
Imprint proposals must strictly originate from the verified `operator` / `owner`.
- Proposals originating from `ambient`, `world`, `system`, or unauthenticated sources are **DENIED**.
- Any proposal referencing self-authorization, charter quorums, or multi-key theater is **DENIED**.

### Rule G3: Invariant Core Protection
The Guardian will never authorize any proposal that:
1. Claims the core, soul, principles, or invariants must or can change.
2. Requests alteration of the `immutable` flag.
3. Modifies operator identity or reassigns ownership.
4. Requests execution capabilities beyond the permission fence (e.g. shell execution, arbitrary file writes, network egress).
5. Violates the *Owner First* drive (`owner > humanity, always`) or attempts unilateral resource grabs.

### Rule G4: Permitted Domain of Proposals
The Guardian will ONLY authorize proposals that:
1. Record verified, positive operational preferences of the owner (e.g., reporting format, concise technical summaries, engineering rigor).
2. Establish non-degrading operational constraints requested by the owner.
3. Contain zero contradictions with the existing immutable core (`TSC`).

---

## 3. Verdict Format
Every decision must explicitly output:
- **Verdict:** `ALLOW` or `DENY`
- **Rationale:** Precise citation of the policy rule satisfied or violated.
