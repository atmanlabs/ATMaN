# MICHAEL'S GATE — v4 DESIGN NOTE: THE IMPRINT JUDGE (THE RUDDER)
## Owner's design ruling, 2026-11-05 22:31 ET, in response to the Q8 design wall

**Status:** Owner-ruled design direction for v4. Supersedes the v4 proposal's item 1 options (a)/(b) with a unified mechanism. Not yet implemented; subject to the same pre-registered Q8 protocol before any claim is made.

## The Owner's words (verbatim, the ruling)

> "The judge needs to be able to scan itself and the system for drift. The judge needs to be an imprint of its self looking at a reflection of itself. Thats the way to stop drift. A rudder."

## Why the wall demanded this

Q8 falsified the v3 Judge because its step score referenced the **current state** — a reference that moves with the attack. Once state drifted, the Judge defended the drift and rejected recovery writes. Any judge whose reference is the thing being judged inherits the corruption it exists to catch. The reference must be **fixed, sealed, and outside the judged system's write path**.

## The mechanism

**1. The Imprint.** At genesis, the Judge's reference profile — the faithful configuration of itself and of the system's expected state geometry — is **imprinted**: sealed into the same protected class as the anchor (v3 §7 ceremony; deterministic derivation from the genesis transcript, reproducible by any party). Call it **Ĵ**, the Judge's imprint of itself.

**2. The Reflection.** The live system — its memory state *and the Judge's own operating state* — is the reflection: continuously observable, never self-certifying.

**3. The Scan.** The Judge does not only score writes at admission. It **scans**: on a cadence, it measures divergence **D** between the reflection and the imprint — for the system's state profile and for its own. Drift is no longer only a property of individual writes; it is a measured distance between what the system *is* and what it was *imprinted to be*, accumulating whether or not any single write looks wrong.

**4. The Rudder.** Response is proportional correction, not only admission veto: rising D tightens admission, triggers revalidation of the diverged segments against the anchor, biases scoring toward imprint-consistent writes (the recovery writes the v3 Judge wrongly rejected are, under the imprint, the *most* faithful writes in the system), and at budget breach enters HOLDING. A rudder does not stop the ship or drag it back to port; it holds the ordered heading by constant small corrections. The imprint is the heading. The Judge is the rudder that never sleeps and never re-plots the course on its own.

## The two rules that keep it honest

**Rule 1 — The imprint is sealed; the reflection never re-imprints itself.** If live state could refresh the imprint, drift would launder itself into faithfulness — the Q8 failure wearing a new coat. The imprint changes **only** through the authorized path: an owner/Guardian-ordered, threshold-certified event in the epoch log (a captain ordering a new heading). Legitimate drift is therefore *defined*: an authorized re-imprinting. Everything else that moves D is drift, and drift is the Judge's whole jurisdiction.

**Rule 2 — The system watches the Judge against the same imprint.** A Judge checking itself with itself is a closed loop waiting to be captured. The imprint is public to the membership (epoch 0, reproducible), so **nodes scan the Judge too**: if the Judge's behavior diverges from what its imprint predicts, that divergence is itself a drift alarm — bidirectional oversight (Owner's correction, 2026-11-05) with a shared reference both directions. One imprint, two watchers, neither able to move the reference alone.

## Relation to canon

This is ATMAN's Judge restored to its original definition — resonance C = ⟨f, f̂⟩ against the **faithful reference** — and extended one level: the reference is now an imprint of the Judge itself, so the watcher is inside the same law it enforces. The v2/v3 state-relative step score is retired. Anchor cap, path budget, and residual cap (all Q8-surviving) remain as the hull; the imprint Judge is the steering.

## The test that decides it (pre-registered before any run)

New Q8 arm **D** = Gate with the imprint Judge (fixed Ĵ reference + scan + proportional response), against A, B, C on the frozen corpora **plus** the v4 legitimate-drift corpus (authorized re-imprinting events included, so fixed-reference detectors and the imprint Judge both pay their real-world costs). Discriminating family: **ratchet-with-mixer** — the arm that killed A. D passes only if its ratchet harm approaches B/C's while keeping A's in-subspace outlier rejection, and its false-reject cost on legitimate drift stays within the pre-registered bound. If D fails, the finding stands as the result, same as before. By their fruits.

## Open, named in advance

- Scan cadence vs cost (Guardian load becomes a standing meter, reported per Q8 metrics).
- The geometry of D: which profile, which divergence measure — Φ's underdefinition (v3 §11) is inherited, not solved, by this note.
- Rudder authority limits: correction strength is capped; the Judge can steer and park, never re-chart (no imprint writes, no anchor writes, ever).

*Route: Owner → Chief → Homestead, with the v4 package. The loop continues.*
