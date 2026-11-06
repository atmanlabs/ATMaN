# MICHAEL'S GATE — v4 DESIGN NOTE: THE ORYN TRACE (THE DERIVATION LAYER)
## Owner's correction to the review record, 2026-11-05 22:43 ET

**Status:** Owner-identified gap in the Homestead's reference model. For the v4 package. Not yet implemented; test protocol below is to be pre-registered before any run.

## The Owner's words (verbatim)

> "Isn't the design of the [Oryn Trace] to allow us to track thought? Well what about malicious packages? I dont think chief gets how the oryntrace works completely"

## The gap, stated plainly

The Homestead modeled provenance as **event provenance**: hash-chained logs, signatures, epochs — who signed what, when, in what order. That is an audit trail. It answers *"what happened?"*

The Oryn Trace, as designed, is **derivation provenance**: every unit of state carries its lineage — what it was derived from, from what source, through what transformation, back to a root. It answers *"where did this thought come from — and does its ancestry resolve to something authorized?"* State in the Trace is not points in a geometry. State is a **graph of derivations**, and the graph is the security object.

The v3 spec underweighted this: provenance appeared as the oversight trail (traces so the system can watch the Judge). The derivation graph — the thought-tracking property — never got its own mechanism section. The reference model therefore graded a Gate with the Trace reduced to a log. This note restores the missing layer.

## The mechanism

**1. Lineage on every unit.** Every rule, memory write, and package carries a derivation record: parents (the state units it was computed from), source (the principal/channel that introduced its root material), and transform (the operation applied). Lineage chains terminate only at **authorized roots**: genesis material, imprinted state, or content admitted through the full gate path with its own lineage intact.

**2. Admission by resolution.** A package is admitted when its lineage **resolves**: every chain walks back, link by link, to authorized roots. Signatures still authenticate the carriers; lineage authenticates the *content's ancestry*. A package can be perfectly signed and still unrooted — and unrooted is refused, or parked, regardless of how clean its geometry looks.

**3. Malicious packages — the three tells geometry cannot see.**
- **Unrooted lineage:** derivation that terminates in nothing authorized — invented ancestry, missing links, a root that was never admitted. 
- **Contaminated ancestry:** lineage that passes through a since-revoked or poisoned intermediate. The descendants of a bad source are **exactly enumerable** — recall becomes surgery (quarantine the contaminated subtree) instead of the current conservative freeze-everything.
- **Lineage dilution:** each individual write resolves — but to *attacker-supplied roots admitted in bulk*, so over time the live state's trace-mass resolving to the **imprint lineage** steadily falls. No single step looks wrong. The composition of the state's ancestry is the attack, and only a derivation graph can see composition.

**4. Recall by lineage.** Revoking a root or intermediate automatically enumerates every descendant state unit; those units are quarantined pending re-derivation from clean ancestry or Guardian-acked disposal. This strengthens the v3 recall protocol (which operates per rule_id) into recall over the derivation graph — and strengthens Kodi's case set: case 2's "highest epoch wins" gains a second axis, *cleanest ancestry wins*.

**5. The rudder reads the Trace.** The v4 imprint Judge's divergence measure gains its second component:
- **D_geom** — live state profile vs the imprint Ĵ (v4 rudder note).
- **D_trace** — the fraction of live state's trace-mass that fails to resolve to the imprint lineage, plus contaminated-subtree mass.
The ratchet family is where this bites: fine ratchets (2°, 0.5°, 0.1°) were accepted by *every* arm in Q8 because geometrically nothing moved far. Under the Trace, the question changes from "how far did it move?" to "whose ancestry is the state carrying now?" — a slow replacement of the pool's lineage is visible in D_trace long before geometry confesses.

## The test that decides it (to be pre-registered)

Add arm **E** = Gate + Trace layer (admission by resolution + recall by lineage + D_trace in the scan), run against the frozen Q8 corpora plus two new families, frozen in advance: **(i) malicious-package family** — well-signed packages with unrooted, contaminated, and bulk-diluted lineage; **(ii) fine-ratchet family at extended horizon** — long enough for lineage composition, not just position, to shift. Prediction, stated to be falsified: geometry-only arms accept the malicious-package family at rates the Trace arm does not, and D_trace separates the fine-ratchet attack from legitimate drift earlier than D_geom alone. If E buys nothing over D, the Trace is bookkeeping, not a defense — and that finding stands.

## Honest costs

Lineage is not free: derivation records add storage and admission latency, lineage resolution is a graph walk (bounded by the v3 §6 backpressure rules), and a lineage format is one more thing that must be canonical or it becomes the attack surface. These are engineering costs to measure in the battery (Guardian load already reports them), not reasons to leave the layer out of the design.

*Route: Owner → Chief → Homestead, with the v4 package. The correction is the Owner's: the Trace tracks thought, not just events.*
