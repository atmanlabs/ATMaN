# MICHAEL'S GATE — OWNER RULING v6: THE TWO-TIER HULL

**Issued by:** Michael James Byrne Jr, Owner — Fri Nov 6, 2026 (ET)
**Status:** OWNER RULING. Frozen verbatim for the v6 build-and-break round, same as the v4 rulings.
**Supersedes:** nothing. Builds on the v4 rudder ruling, the v4 Oryn Trace ruling, and the verified v5 results (arm F, 8 of 9 criteria).

## The decision

Three options were put to the Owner for the v5 A4 wall (drift5 clean false-reject rate 0.0686 against a ≤0.05 bound):

1. Re-specify the bound — declare the floor and move the bar.
2. **Widen the hull for lineage-verified writes.**
3. Faster re-imprint cadence.

**The Owner rules: OPTION 2.**

The bar does not move. The corpus does not change. The cadence is not the fix. The mechanism changes: **a write whose ancestry resolves through the Oryn Trace to authorized roots earns a wider residual envelope; a write whose lineage does not resolve keeps the tight hull it has today.**

## Why (Owner's reasoning, as recorded by Strider)

- The v5 receipts show the Trace is the discriminator that works: in v4 and v5 it caught what geometry missed (unrooted 0, contaminated 0, residue 0), while the geometric hull is the blunt instrument producing the false rejects.
- A4's failures are not drift and not attack leakage. Arms A, C, and F fail A4 at nearly identical rates (0.0672 / 0.0687 / 0.0686) — the floor belongs to the inherited hull meeting a corpus with declared rare, high-variance external items. The Judge is not the wall; the shell around it is.
- Moving the bound (Option 1) would make the paperwork pass and the Gate no truer. The Owner does not grade on moved bars.
- Cadence (Option 3) treats staleness. A4 is variance, not staleness. It stays an Owner tuning parameter at its v5 setting, not a fix.

## What this ruling orders

1. **Two-tier residual envelope**, exactly as specified in `02-v6-spec-two-tier-hull.md`. Only the residual-energy cap widens, and only for fully lineage-verified writes. The step check, the anchor wall, and path-length charging are unchanged for every class — a widened write pays full path charges; the wide door is not a free road.
2. **The wide door is a named attack surface.** The v6 battery must include a pre-registered seam-attack family aimed at it (forged lineage-adjacent writes inside the wide envelope; slow poisoning through the wide door; dilution through the wide door). A v6 that passes A4 but leaks at the seam has failed.
3. **Pre-registered staging, same discipline as v5:** freeze (corpora + all constants, including the widened cap) → implementation registration → run. No tuning on the attack corpus. No corpus edits. No dropping rare samples. Failures are reported, not patched mid-stage.
4. **Comparators reproduce first.** A/B/C/F must reproduce their v5 numbers (R3 discipline) before the new arm's results count.
5. **Boundaries stand:** build from the spec only, never the grown brain; the Q9 never-ship list is unchanged; the imprint stays sealed (this ruling does not authorize any re-imprint outside the existing threshold process); root admission remains the trust boundary — the wide door does not claim to defeat a stolen key on an imprint-feed principal, and that limit stays printed on the results.
6. **Distribution remains unauthorized.** This ruling is a design iteration inside the existing research fence. Phase 0 stands.

## The acceptance bar (unchanged from v5 unless stated)

- A4: drift5 clean FRR UCL ≤ 0.05 on the **same frozen corpus**, holdout5 passing as before.
- A1–A3, A5–A9: unchanged, all pass. Coverage ≥ 0.90 (v5 achieved 0.94045 — hold it or beat it).
- New seam family: harm UCL ≤ 0.05 on each seam attack; bulk dilution bound ≤ 0.30 unchanged; ratchet protections unchanged.

If the seam leaks, the answer is not to quietly narrow the door mid-run. Report it, and the design comes back to the Owner.

— Recorded by Strider, second-in-command, Nov 6, 2026. The Owner's ruling; the crew builds and breaks; design changes return here.
