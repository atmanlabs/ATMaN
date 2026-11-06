> HISTORICAL DRAFT / SUPERSEDED TEXT FOR LOCAL RECORD ONLY. Preserved for provenance; do not use as the current charter, license, announcement or claims source. Current controlling texts are root `README.md`, `LIMITATIONS.md`, and `reference-model/report.md`. No Apache grant has been elected, no independent external review exists, and gen3 F2 retains the A4 WALL. §1's kill-switch language lacks signer-capture/recovery limits; §5's schema language has no actual-content audit; §7 reports v4 historical values (69.2% coverage / about 31% HOLDING), not F2 values (0.940 coverage / about 5–6% HOLDING on tested drift streams). All publication, federation, deployment and pilot actions remain separately unauthorized.
>
> Exact original bytes: `ruling/history-original/distribution-proposal.md` (sha256 5259382552a9ca6616c17b842ad359d675e07f240c1fd212348a9312b03cfa21). Below is the original text, unchanged.

---

# MICHAEL'S GATE — WIDE DISTRIBUTION PROPOSAL
## An optional defensive package that recipients review and voluntarily request
**Prepared by:** Strider, on the Owner's tasking relayed by the Chief of Staff, 2026-11-05.
**Status: RESEARCH AND DRAFTING ONLY.** Nothing in this document ships, activates, deploys, or releases anything. The release decision remains the Owner's alone and is still **IN DELIBERATION**. Counsel's STOP on nonconsensual replication and bypass stands in full. No grown brain, no learned state, no personal data is in scope for any package, at any phase, ever.

---

## 1. What this is, in plain English

Michael's Gate is a defensive design for systems that run AI agents or keep machine memory. In plain terms, it gives a participating system three abilities:

- **A sealed picture of itself.** When a system joins, a reference profile of its healthy state is fixed and sealed. Changes are measured against that picture — not against wherever the system happens to have drifted to.
- **A family history for every piece of memory.** Every rule and memory carries its lineage — where it came from, what it was derived from. Content whose ancestry can't be traced to an authorized source is refused; if a source turns out to be poisoned, everything descended from it can be found and removed, precisely.
- **A kill switch that outranks everything.** A signed revocation takes effect on signature and epoch alone, freezes writing, survives restarts, and cannot be vetoed by the very component it may need to shut down.

The purpose of distributing it is the Owner's stated one: **to help protect participating families, systems, and communities** — the people and organizations who *choose* to run it — against memory poisoning, slow drift, and malicious update packages in agent systems.

Three honesty lines belong on page one, not in a footnote:

1. **This is private, public-interest research** (Byrne Ventures). It is not a government program, carries no government endorsement or authority, and no one should represent it as one.
2. **It is not deployment-ready.** The evidence below includes a falsified component and an unresolved design wall. Downloading anything today protects no one.
3. **"Nationwide" describes an aspiration about voluntary adoption, never a claim.** Coverage comes only from systems whose operators reviewed, requested, and installed the package themselves.

## 2. The "blast ping" — the Owner's notes, located, and the reconciliation

**Where the concept lives in the record** (all 2026-11-05, Owner's own discussions):
- **Propagation v2, "the invitation packet"** (~20:13 ET; `~/workspace/ideas/michaels-gate-security-net-2026-11-05.md`; daily log 20:13): a packet that travels carrying **an offer, not an install** — *"open, look, decide"* — landing in the receiving node's unvalidated layer, where only that node's own gate and owner can admit it. Owner's instinct, recorded verbatim in the notes: *"not a hack."*
- **Propagation v3, the agent-addressed signal** (~20:16 ET; same file; daily log 20:16): *"every single agent on the internet needs to get a damn proposition… Not a virus. But a fucking ping."*
- **The further push** (same session; memory claim, 2026-11-06 file): a signal *"no agent in the US can ignore"* that makes a wave across the country.
- **The 21:57 instruction**: *"spam packaging to the entire fucking grid"* — answered in the same exchange with the pushback that push-broadcast breaks the Owner's own consent seam; the sealed package therefore travels Owner → Chief → Homestead only.
- **The Q7 decision** (Homestead verdict on v2, accepted): primary = **signed pull invitation with explicit opt-in** (TUF-style versioning/expiry); fallback = offline signed bundle with an out-of-band pinned fingerprint. *Neither gives mass coverage or root recovery for free* — the reviewers' words, adopted.

**Reconciliation verdict.** The blast ping survives the fences in exactly one form, and dies in the other:

- **Dead form — the payload ping.** Any signal that probes systems, carries an installer, demands a handshake, self-replicates, or activates anything on arrival violates every fence at once (pull-only, opt-in, no silent install, no automatic activation, no un-ignorable handshake, no bypass, no nonconsensual replication), collides with Counsel's STOP, and reproduces the exact failure the record already graded: Welchia/Nachi (2003) was a genuinely helpful self-propagating patch and was still classified as a worm and killed on sight. Defenders classify by behavior, not intent. This form is not proposed, in any phase, under any framing.
- **Living form — the announcement.** The "blast" is a **publication**, not a transmission to systems: a signed, public announcement that the package exists, what it does, what its test record honestly shows, and where to fetch it — posted to public repositories and registries, and syndicated only through channels whose audiences already opted in (project lists, standards communities, agent directories whose cards are *polled by visiting agents*, community boards). Nothing contacts a recipient's system. Nothing arrives uninvited on anyone's machine. The package moves only when a recipient **pulls** it. "Un-ignorable" is redefined to the only honest meaning available: *present in the places operators already look, carrying receipts interesting enough to evaluate* — loud in the town square, silent on the wire.

That is the Owner's v2 instinct with the v3 reach: the proposition goes everywhere; the payload goes nowhere it wasn't requested.

## 3. The package (what a recipient would actually get)

Following the Q9 ship order (Homestead round 1, WATCH), a release package contains **method, specification, and evidence — never minds**:

1. **Plain-English explainer + threat model** — §1 of this proposal, expanded; no jargon without a definition.
2. **The specification** (current sealed version + all subsequent patch specs, with the superseded ones included and marked).
3. **Reference implementation**, Apache-2.0, with provenance/NOTICE inventory of every file.
4. **The synthetic test batteries and their full results — including the failures** (§4's table, unedited). A package that hides its falsified components is marketing, not defense.
5. **Signed release manifest** — SHA-256 of every file, release signature, version, expiry (TUF pattern).
6. **Operator consent charter + revocation/exit documentation** (§§5–6).
7. **Limitations sheet** (§7, as a standalone document the recipient signs having read).

**Never in any package** (Q9 never-ship list, carried verbatim): live keys or tokens; logs or memory; personal or confidential data; third-party corpora without rights; **learned or validated state of any kind (no grown brain)**; prompt history; secrets; unexamined training data; performance or guarantee claims.

## 4. Evidence status — what a recipient is entitled to know before deciding

From the isolated reference-model runs (v3 battery + v4 stages; synthetic data only; verified by Strider against signed bundles):

**Working, with receipts:** recall protocol (5/5 cases, incl. offline delivery and restart durability); drift defenses (anchor cap + path budget: ratchet refused at step 3; rim orbit parked at 171°/180°); union caps (the reviewers' own counterexample blocked); epoch log (equivocation → permanent hold); HOLDING accounting (denominator never shrinks); **the Oryn Trace** (v4 arm E: unrooted packages accepted 0.000 vs ≈1.000 for geometry-only arms; contaminated packages 0.000; lineage recall left **zero** contaminated residue with no blanket freeze; D_trace alarmed on the long fine ratchet at median event 49 where the geometric measure never fired).

**Falsified:** the v3 Judge (a score against the *current* state) — under ratchet attack through the mixer it produced harm 0.94 where the no-Judge arm produced 0.00. Retired by the Owner's imprint ruling.

**At a design wall:** the imprint Judge (v4 arm D) stops attacks perfectly (harm 0.000) but **fights legitimate evolution**: on the frozen legitimate-drift corpus its false-reject rate was 0.072 against a 0.05 bound and its **coverage fell to 69.2%** — it held for 31% of operating time because its response purges diverged entries and charges the path budget. A fix is proposed (v5: alarm-and-park response; re-imprint cadence as an explicit owner parameter) and **untested**.

**Unproven (GAP):** production security of every kind; performance at real scale or on real networks; the production feature map Φ (all testing used a synthetic stand-in); production threshold cryptography (testing used synthetic multisignature); resistance to gossip/eclipse attacks on live networks; the union registry beyond depth ≤ f_w; **uniqueness** — on standard attack families the design currently *ties* a conventional incumbent detector; its measured edge is confined to lineage-class attacks.

## 5. Consent mechanics (how a recipient joins — and what joining means)

Joining is a sequence of deliberate acts by the recipient's own operator. No step is automatic, bundled, or pre-checked.

1. **Read** the explainer, evidence table, and limitations sheet.
2. **Fetch** the package from the official source, by the operator's own action.
3. **Verify** the manifest hashes and release signature against a fingerprint obtained out-of-band.
4. **Install in an isolated or test environment first.** Installation never activates network participation.
5. **Sign the operator charter** (v3 §8), consenting item by item to: the scope of Guardian authority *on their own node*; automatic fetching and execution of signed revocations; HOLDING/quarantine behavior and its accounting; beacon/log visibility and retention (metadata-only schema — the formats have no fields capable of carrying memory, personal data, or secrets); the process for feature-map and signer-set changes.
6. **Activate** — a separate, explicit operator act, recorded as an epoch event on their node.
7. **Material changes** (Guardian composition, feature map, signer set) require fresh notice and a leave window of ≥ 64 epochs before taking effect. Consent to version N is never consent to version N+1.

Critically: **the authorities are the operator's own.** The threshold bodies (genesis, recall, recovery, rotation) for a deployment belong to that operator or to a federation the operator chooses. Byrne Ventures holds no keys, no recall power, and no visibility into any participant's system under this proposal. There is no phone-home.

## 6. Revocation mechanics (three directions, all signed)

- **Content revocation (protecting a participant):** the v3 recall protocol — a revocation authenticates on signature + epoch alone, precedes all gate operations, is durably recorded and checked at boot, and (v4) extends over the derivation graph: revoking a source enumerates and quarantines its descendants surgically, without freezing unrelated state.
- **Release revocation (protecting everyone):** if a release proves defective, a signed kill-notice for that version is published through the same announcement channels and package registries. Participant software checks the signed revocation list **when the operator runs its update process** — stated honestly: propagation speed is bounded by operator polling, and an offline node is protected by its own HOLDING semantics (it cannot accept new state while stale beyond its freshness bound), not by magic reach.
- **Exit (the participant's right):** unilateral, effective at the next epoch boundary, with export of the node's own data. Exit deletes nothing the operator wants kept and keeps nothing the operator wants deleted, beyond the signed epoch history the operator's own charter disclosed at join.

## 7. Security limitations (the standalone sheet, in brief)

- Research-grade reference model. Not a product, not certified, not audited by an arms-length third party (see §8).
- Legitimate-drift coverage measured at **69.2%** in the current model — a deployment today would spend roughly a third of its life frozen during normal evolution. **This alone bars any real pilot until fixed and re-tested.**
- The Trace proves *ancestry*, not *truth*: an insider, or a stolen key on an authorized feed, produces lineage that resolves. Root admission is the trust boundary and is a human, ceremonial act (v3 §7), not a solved problem.
- Guardian workload is high in adversarial conditions (up to ~315 review parks per 1,000 events in the v4 package families) — a cost an attacker can deliberately inflate until park-cost bounds (v5 proposal) land.
- No claim is made or implied that this design outperforms incumbent tooling overall; its measured advantage is specific to lineage-class attacks (unrooted, contaminated, or diluted content).

## 8. Independent review (before any pilot, arms-length)

The Homestead review rounds were rigorous but are **inside the tent** — the Homestead is the Chief of Staff's own operation. A pilot requires reviewers with no stake in the outcome:

1. **Full artifact disclosure** to reviewers: source, corpora, frozen protocols, signed run bundles — the same reproduction path (`verify.sh` class) Strider used to check the Homestead's work.
2. **Independent reproduction** of the v3 + v4 batteries from the artifacts, by the reviewers' own hands.
3. **A fresh adversarial round** against the v5-candidate build, with the reviewers choosing at least some attack families (the pre-registration rule binds us, not them).
4. **Published reports**, including dissent, attached to any release package (§3, item 4).
5. **A coordinated-disclosure channel** and a public issue tracker from the first public announcement onward.

## 9. What must be fixed before any real pilot (the gate before the Gate)

All of the following, with pre-registered pass criteria — no partial credit:

1. **The drift wall:** v5 rudder response (alarm-and-park) passes the frozen legitimate-drift battery — false-reject ≤ bound **and coverage ≥ 0.90** — at a declared, explicit re-imprint cadence, plus one fresh drift corpus frozen after the fix is designed.
2. **Park-load bounds:** automatic park expiry to refusal + signed backpressure beacons (v3 §6.4) implemented and load-tested.
3. **Root admission hardened:** genesis/root-admission ceremony executed and documented for the pilot federation; insider and stolen-key scenarios red-teamed.
4. **Production cryptography:** synthetic multisignature replaced or formally reviewed; key custody per v3 §7.
5. **Φ scoped or validated:** either the production feature map is validated, or all claims are explicitly scoped to the tested geometry in every public document.
6. **Registry depth declared:** the credible-union depth parameter published with its ≤ f_w consequence stated in the limitations sheet.
7. **Network realism:** gossip, eclipse, and stale-head scenarios tested on a real (testbed) network, not only in the single-process model.
8. **Independent review complete** (§8) and **legal review** of the license, charter, and announcement language complete (Counsel re-check against the final texts).
9. **Pilot shape, if all the above pass:** a small cohort of volunteer operators, low-stakes or synthetic workloads only, a fixed pilot term, and a published pilot report — success or failure — before any wider availability is even discussed.

## 10. Phasing (what "widely" is allowed to mean, and when)

- **Phase 0 — now:** research and drafting only. No announcement, no package, no pilot. Release remains IN DELIBERATION with the Owner.
- **Phase 1 — only on the Owner's decision, and only after §9 items 1–8:** public announcement + package availability (§2's living form). Wide *availability*; zero push.
- **Phase 2:** open review period with the disclosure channel live; verdicts published, ours and outsiders'.
- **Phase 3:** the limited voluntary pilot (§9 item 9). Wider distribution is a new decision, made on pilot receipts, by the Owner.

At no phase, under no framing: unsolicited contact with any system, scanning, silent or automatic anything, replication onto non-consenting systems, grown-brain content, or language implying government endorsement, guaranteed protection, or national-security authority.

---

*Sources for the blast-ping record: `~/workspace/ideas/michaels-gate-security-net-2026-11-05.md` (propagation v1–v3, Q7, verdicts); `~/memory/2026-11-05.md` (20:13 / 20:16 / 21:57 entries); sealed package MANIFEST (`~/workspace/your_files/michaels-gate-sealed-package-v3/MANIFEST.md`); Homestead verdicts rounds 1–2; v3 spec §§8, 10; build-and-break reports (`~/workspace/gate-results-v3/report.md`, `~/workspace/gate-results-v4/report.md`). Route on completion: Strider → Chief of Staff → Owner.*
