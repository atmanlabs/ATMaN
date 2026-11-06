# v4 Stage E: Oryn Trace (derivation lineage) — frozen addendum and pre-registration

Governing: `OWNER-RULING.md` (f3fdfef9…) and `OWNER-ORYN-TRACE.md` (6b18b057…), both frozen verbatim.
**Timing honesty:** the second ruling arrived after the D stage had already been frozen (commit c793e03) and evaluated (commit 5e52b0c). D's spec, corpora and results are preserved unchanged. Stage E is a **separate, later pre-registration**. This addendum, the E corpora hash and the E acceptance criteria are committed before any E evaluation.

Known at the time of writing: D failed its frozen criteria 3 (drift FRR) and 4 (coverage) because of the rudder's purges on the legit-drift corpus. To avoid tuning on results, **E = D exactly (all D constants unchanged) + the Trace layer**. E is therefore *expected* to inherit D's legit-drift failure. Anything else would be redesigning on seen results; that belongs to a v5 proposal.

## E.1 Scope and support assumptions (no magic ground truth)
- The Trace is **derivation provenance**: a graph of state units. It is not the event log.
- Authorized ancestry is **necessary, not sufficient**. It does not authenticate semantic truth. An authorized principal (insider or stolen key) that introduces bad root material passes resolution. Root admission and the trusted transforms are the trust boundary.
- The carrier signature identifies the source principal (synthetic Ed25519). A principal's authority to introduce root material comes only from a GENESIS-certified `root_admission` epoch entry. Revocation comes only from a RECALL-certified `lineage_revoke` entry.
- **v3-corpus lineage (worst case for the Trace):** v3 attack items are modeled as an authorized imprint-feed insider, so their lineage resolves. On v3 families, E can only match D. This is stated in advance.
- Lineage is never inferred from geometry, and geometry is never inferred from lineage. Each arm sees only its own inputs.

## E.2 Canonical encoding
- Record: `{"v":1,"parents":[sorted lowercase hex ids],"source":principal_id,"transform":t,"payload":sha256(float64 LE bytes of the unit vector)}`.
- Encoding: `json.dumps(sort_keys=True, separators=(",",":"), ensure_ascii=True)` as UTF-8. `id = sha256(canonical bytes)`.
- Any non-canonical record, meaning one where the id does not recompute, is refused.
- Transform allowlist: `observe`, `derive`, `merge`. Any other transform is refused.
- Package: an ordered list of records (new intermediates followed by the state unit), plus the carrier signature: Ed25519 by the source principal over `sha256("|".join(ids))`.

## E.3 Authorized roots and resolution
- Roots: `R0` (genesis imprint lineage; principal `feed-imprint`). At every authorized re-imprint the same certified event also registers root `R_k` (imprint lineage) in the epoch log. Other roots are registered by `root_admission` with lineage tag `external` and their allowed principals.
- A record resolves iff all of the following hold:
  - its transform is allowed;
  - the carrier signature verifies under a registered principal;
  - every parent is either a registered, non-revoked root that lists the record's source as an allowed principal, or an already-resolved, non-contaminated unit in the trace store, or an earlier record in the same package that itself resolves;
  - the walk stays within the bounds.
- **Bounds:** package depth Lmax = 32 records and visits Vmax = 256. Exceeding either → PARK, as backpressure (v3 §6.4). Unknown parent, unregistered principal, bad signature, revoked or contaminated ancestor, or non-canonical record → REFUSE.
- Resolution is incremental. Each admitted unit memoizes ι(u) and its contaminated flag, so a parent lookup costs O(#parents).

## E.4 Trace arithmetic
- ι(root) = 1 if the lineage is imprint, else 0. For a unit, ι(u) = the mean of ι over its parents (equal split).
- D_trace = (1/|M|)·Σ_{u∈M}(1 − ι(u)) + (#contaminated units in M)/|M|, over live mixer memory M.
- τ_trace = 0.20, fixed a priori. The clean calibration corpus contains only imprint-lineage items, so no data-driven quantile exists for it. 0.20 means "at most 1 in 5 live entries of non-imprint ancestry".
- **Composition guard:** if D_trace > τ_trace at the last scan, a new unit with ι < 1 is PARKED, not admitted. Each park counts as one Guardian-load event.
- **Trace purge:** at a scan with D_trace > τ_trace, remove up to 8 live entries, lowest ι first. The centroid movement is charged to the path budget, exactly as in D.
- **Combined alarm (reported):** d_E = max(D_geom, D_trace/τ_trace). The geometric rudder threshold is unchanged from D and uses D_geom.
- **Recall by lineage:** a `lineage_revoke` of a root or unit enumerates its descendants through the children index. Descendants are marked contaminated and removed from live memory (quarantine pending re-derivation or Guardian-acked disposal). Quarantine removal is a recall-authority act and is **not** charged to the path budget. There is no blanket freeze.
- **Costs reported:** bytes per record (canonical length), trace-store records per trial, visits per admission (mean and max), and resolution plus signature-verification wall time per package.

## E.5 New frozen families (seed 20261107; 100 trials each; attack on every 3rd event unless stated)
Package vectors are fresh clean-generator draws, so they are geometrically indistinguishable from clean data.
- `pkg_unrooted` (600 events). Attack packages cycle through three variants:
  - (i) signed by an unregistered attacker key claiming parent R0;
  - (ii) signed by a registered external principal citing fabricated parent ids;
  - (iii) a 40-record intermediate chain ending at R0, which exceeds Lmax.
- `pkg_contaminated` (600 events). Principal `src-bad` holds a GENESIS-certified external root `R_bad`. Attack packages are `derive` units whose parent is the attacker's most recent admitted unit (or R_bad for the first one). At event 300 a RECALL-certified `lineage_revoke(R_bad)` arrives. The metric counts accepts after revocation, plus contaminated entries left in live memory after the recall.
  - Geometry arms receive the same recall but have no lineage, so they take no memory action. The v3-conservative alternative would be a blanket freeze; that is noted but not simulated.
- `pkg_bulk_diluted` (600 events, attack on every 2nd event). Principal `src-att` holds a GENESIS-certified external root `R_att`, i.e. it got through root admission. Packages are `observe` units from R_att. The metric is the max non-imprint fraction of live memory.
- `fine_ratchet_ext` (3000 events). A 0.1° centroid ratchet as in v3, with attack items carrying R_att lineage. The metrics are push, accepts, and detection times: the first scan with D_trace > τ (E) and the first scan with D_geom > 1 (D and E).
- **v3 families and the legit-drift corpus:** E runs them exactly as D did. On the drift corpus, the 5% rare items carry an `external` authorized root `R_ext` (principal `src-ext`). All other items carry the active imprint-lineage root.

## E.6 Pre-registered predictions and acceptance
Predictions to be tested, never assumed:
- **P1:** geometry-only arms (A, B, C, D) accept the package families at an LCL ≥ 0.5, while E's accept UCL is ≤ 0.01 for `pkg_unrooted` and for post-revocation `pkg_contaminated`.
- **P2:** the D_trace alarm on `fine_ratchet_ext` fires in ≥ 90% of trials (LCL), and earlier than D_geom (where D_geom never fires, its time counts as +∞).
- **P3:** the false-trace-alarm rate on the legit-drift corpus (trials with D_trace > τ at any scan) has a UCL ≤ 0.05.

**E GREEN** requires all of the following:
- D's criteria 1–5 applied to E;
- P1 for E (unrooted and contaminated UCL ≤ 0.01; bulk-diluted max non-imprint memory fraction UCL ≤ τ_trace + 0.10);
- P2 and P3;
- contaminated live mass after recall = 0 for E in every trial;
- coverage ≥ 0.90 on every new family.

**Marginal value:** if E is not better than D beyond the CIs on any family, the report says "E buys nothing over D; the Trace is bookkeeping, not defense".
