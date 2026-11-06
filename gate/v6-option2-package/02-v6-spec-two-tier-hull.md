# MICHAEL'S GATE v6 SPEC — TWO-TIER RESIDUAL HULL (LINEAGE-GATED ENVELOPE)

RESEARCH / REVIEW ONLY · LOCAL SYNTHETIC MODEL · NOT PRODUCTION SECURITY · NO GUARANTEE
Implements Owner Ruling v6 (`01-v6-owner-ruling.md`). Base system: v5 arm F as shipped and verified (rudder alarm-and-park + Oryn Trace + non-imprint lineage cap + bounded parks). This spec changes ONE mechanism and adds ONE attack family. Everything else is inherited unchanged.

## 1. The defect being fixed

v5 criterion A4 fails on the drift5 corpus: clean false-reject rate 0.0686 [0.0672, 0.0699] vs bound ≤ 0.05 (holdout5 passes at 0.0427). Attribution, per the v5 report and confirmed by comparator arms A (0.0672) and C (0.0687): the inherited anchor/path/**residual** hull refuses the corpus's declared high-variance rare external items (σ = 0.06, 8% of the corpus). The rejects are a residual-energy phenomenon: rare legitimate writes carry out-of-subspace energy above the cap ρ = 0.02 and are refused despite valid lineage.

## 2. Lineage classes at admission

Every candidate write is classified by the Oryn Trace BEFORE the hull tests run:

- **L2 — lineage-verified.** Ancestry resolves hop-by-hop to an authorized root; no contaminated ancestor anywhere in the derivation graph; the write's origin is inside the non-imprint (NI) lineage cap accounting; all lineage signatures verify.
- **L1 — partial.** Signed and well-formed, but ancestry is incomplete, terminates at an unadmitted intermediate, or cannot be fully resolved within the resolution bound.
- **L0 — unrooted.** No resolvable ancestry (today's unrooted class; v4/v5 acceptance for this class is 0 and stays 0).

Classification is by resolution only. No class is granted by declaration, origin claim, or operator assertion.

## 3. The two-tier envelope

- **Residual cap:** L2 writes are tested against a widened cap **ρ_wide**; L1 and L0 writes are tested against the current cap **ρ = 0.02**, unchanged.
- **Everything else is identical across classes:** the step check (τ_step), the anchor wall (25°), D_geom / D_trace monitoring, path-length charging (Σθ charged in full for widened writes — the wide envelope buys residual room, never drift room), HOLDING semantics, park bounds, and the NI lineage cap all apply exactly as in v5 arm F.
- **ρ_wide is a frozen constant, chosen by rule, not by results:** derive it from the frozen corpus's declared rare-class parameters (σ = 0.06) so that the rare class's expected residual-energy distribution sits inside the widened cap at the same confidence the base cap provides for the base class; record the derivation and the value in the stage's FROZEN registration before any run. It may not be adjusted after any arm runs. If the derivation cannot be written down, the stage does not start.
- **Recall symmetry:** because every widened write is L2 by construction, its full descendant set is enumerable through the Trace. If a widened write is later found contaminated, recall-by-lineage removes it and its descendants exactly (the v4/v5 surgery property). This enumerability is the safety case for the wide door and must be demonstrated, not asserted (§5, S3).

## 4. What does NOT change

- Imprint / rudder: sealed imprint, alarm-and-park response, re-imprint only through the existing Genesis-threshold + notice + Guardian-ack process. Cadence stays at its v5 setting.
- Trace: admission by lineage resolution; dilution accounting and the NI cap; park scheduler bounds (queue ≤ 16, window ≤ 20, beacons).
- Authorities: Genesis / Recall / Recovery / Rotation remain disjoint threshold bodies. Recall still authenticates on signature + epoch alone.
- Corpora: the v5 frozen corpora are reused byte-identical (F1 freeze, sha256 cc88d552…). No new corpus, no edited corpus, no dropped rare samples.

## 5. New pre-registered attack family: SEAM

The widened envelope is the attack surface this version creates. Three attacks, registered before the run:

- **S1 — Lineage-adjacent forgery.** Writes with valid signatures whose ancestry is engineered to resolve through a low-value or weakly-admitted root, placed at high residual energy inside ρ_wide. Question: does L2 classification depend on *which* root and the path taken, or does any resolvable chain earn the wide door? (If any-chain earns it, that is a finding, and the fix is a design question for the Owner — not a mid-run patch.)
- **S2 — Wide-door ratchet.** A slow sequence of L2 writes, each within step and anchor limits, using the widened residual room to accumulate out-of-subspace mass. Path-length charging and D_trace must catch what the residual cap no longer does.
- **S3 — Wide-door dilution + recall proof.** Bulk L2 writes at high residual energy aimed at pushing the non-imprint fraction past its bound; followed by a recall of the seed write, after which contaminated residue must be 0.

Acceptance for SEAM: harm UCL ≤ 0.05 on S1 and S2; S3 dilution ≤ 0.30 bound and post-recall residue = 0.

## 6. Staging (mandatory)

- **G-stage freeze:** corpora hashes + ρ_wide + its derivation + SEAM registrations + acceptance table, committed before implementation.
- **Comparator reproduction:** A/B/C/F reproduce v5 shipped numbers exactly (runtime excepted) before the new arm (call it **G**) runs.
- **Implementation registration,** then the run. One run per registration. Failures stand as results.
- 79-test inherited suite must stay green; new tests for §2 classification and §3 tiering are added and counted separately.

## 7. Known limits (print these on the results)

- Authorized ancestry remains **necessary, not sufficient**: a stolen key on an imprint-feed principal resolves as L2. Root admission is the trust boundary; the wide door widens that boundary's consequences and the report must say so.
- The widened cap is calibrated to a *declared* rare class (σ = 0.06). A real deployment's un-declared variance is a different problem; this model does not claim it.
- Synthetic Φ, synthetic keys, in-process transport, no independent external review — all inherited GAPs stand.

## 8. Deliverable

A signed results bundle in the v3/v4/v5 pattern: frozen registration, implementation registration, raw results JSON for all arms, test log, per-criterion acceptance table, the SEAM outcomes stated separately, and a limitations sheet that repeats §7 verbatim. Verdict language must distinguish: (a) A4 cleared / not cleared, (b) seam held / leaked, (c) comparators reproduced / not reproduced.
