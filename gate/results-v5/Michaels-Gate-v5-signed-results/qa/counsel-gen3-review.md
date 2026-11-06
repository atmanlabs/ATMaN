# Michael's Gate v5 generation 3 — Counsel final local text review

**Prepared:** 2026-11-06, approximately 02:00 ET. Internal legal issue spotting only; not a signed or outside legal opinion.
**Candidate read:** `/workspace/michaels-gate-v5-candidate-gen3/`; sibling tar receipt SHA-256 `e353e9bc3bcfe5d40b36f0c8837ef6b180d28ce4e450ac76d46aef8d456088aa` (receipt recorded, not an independent replay by Counsel).
**Status: WATCH, local packet only. No outside access, publication, deployment, pilot or activation.**
This is a text/disclosure review of gen3, not a modification or technical verification. Kodi's gen3 independent verification remains pending; gen2 PASS does not automatically migrate to gen3. The previous Counsel no-privilege, consent and release boundaries remain in force. No government endorsement or authority, security certification or national coverage is established by this review.

## Bottom line

The **core internal-packet boundary is coherent**, subject to the targeted text corrections below. `LIMITATIONS.md` preserves Mike's owner rights: it makes **no Apache or other code license grant**, keeps research/review access separate from publication, and reveals no actual deployment or operator consent. The current README distinguishes the local A4 wall and the pending gen3 packaging check.

The R3 receipt reports full inherited v3/v4 verification and fresh F1/F2 comparison, while `reference-model/report.md` correctly retains the failed A4: drift5 clean FRR **0.0686 [0.0672, 0.0699]** against the required UCL ≤ 0.05. The report also states that F2 passed A1–A3 and A5–A9; that is not perfection, flawlessness or production success. HOLDING remains about 5–6%; root/key capture, declared rather than verified independence, synthetic Guardian review, persistence/replay, liveness, real networks and external arms-length review remain open.

Nothing in Kodi's packaging PASS or R3 reproduction authorizes activation or cures these walls. No current operator consent exists or is claimed in the present packet. A necessary consent charter and exit implementation remain conditions before deployment, not completed features.

## Targeted corrections to complete the local packet text

These are fixes for the local record, not requests to open external access. Each needs the authorized integrator, with hashes/signatures regenerated as applicable; Counsel has not edited the candidate.

### 1. WATCH: absolute privacy wording is broader than the packet supports

**Location:** `LIMITATIONS.md`, bullet **“Keys”**, line 10: **“No real or personal data was used.”**

That sentence reaches every document and byte, not just test data, and conflicts with the actual text. `ruling/distribution-proposal.md`, §2 **“Where the concept lives in the record”**, quotes “Owner's own discussions,” names private memory/path sources in its closing source note, and identifies a time for the 21:57 instruction. `inherited/v3/sealed-package-sha256.txt` retains an absolute agent-ID attachment filename; the local Kodi history notes that identifier/path. These are not basis-evidence that any account secret was included, but they mean an across-the-board “no personal data” guarantee needs a complete artifact/history determination rather than a schema assertion.

The root SBOM records package dependency metadata and a minimal inventory; it does not settle PII, provenance or full-history rights.

**Recommended exact replacement for the entire line 10 bullet:**

> - **Keys and data:** All shipped packet and test-log keys are synthetic and nonproduction; see `keys/NOTICE.md`. Experiment inputs and generated metrics are synthetic. The local static/file-key check found no shipped private key. Prose provenance includes owner-attributed discussion and local path identifiers; this packet is not a blanket personal-data or privacy-clearance claim. Local restricted package only: no real account tokens or vaults are authorized for inclusion; actual artifacts, including history, require separate privacy and rights review before any later disclosure.

Retain as a bounded footnote if wanted: **“The earlier source/history heuristic reported no real account credentials or grown-state files, but it was not a complete privacy audit of the present bundle or its expanded history.”** That is not permission to release history.

### 2. Date or correct stale gen2 packaging status in gen3

**Locations:** root `PACKAGING-RECEIPT.md`, **§ Status**, line 6: **“Generation 2 is PENDING Kodi's independent verification. Our own QA is not independent verification.”** Identical `reference-model/PACKAGING-RECEIPT.md` line 6; `reference-model/report.md` line 71 historical **“Packaging addendum (generation 2)”** also says **“generation 2 pending Kodi independent verification.”** `reference-model/HANDOFF.md` line 14 carries the same wording.

That was accurate at gen2 sealing but is stale if read as a current status in gen3. A later sentence in the report correctly records PASS; do not leave historical and current labels without chronology. Root `README.md`, `R3-RECEIPT.md`, and `reference-model/report.md` § “R3 reproducibility addendum” record gen2 PASS; the corresponding independent text is `reference-model/crew-evidence/round3-full-20261106T0052/kodi-gen2-verdict.md`.

**Recommended exact replacement:**

> - Packaging: **generation 1 FAIL**; **generation 2 PASS** per Kodi's local independent verdict (copy in `reference-model/crew-evidence/round3-full-20261106T0052/kodi-gen2-verdict.md`), with its stated GAPs. **Generation 3 is PENDING Kodi's separate independent verification.** R3 full inherited-battery and fresh-comparison receipts are recorded in `R3-RECEIPT.md`; they do not substitute for gen3 review and do not change the technical WALL at A4.

Chronology (`README.md` line 6) already correctly says gen3 is pending. Do not promote gen3 on that line. For frozen/historical report and handoff prose, prefix the old status **“At gen2 sealing, prior to Kodi's subsequent PASS:”** and add the same final R3 pointer; alternatively carry an explicit dated supersession note. Do not recreate a contradictory current status.

### 3. Keep historical proposal claims subordinate on their face

The **draft historical proposal** `ruling/distribution-proposal.md` remains more expansive than gen3 and must not be treated as the current consent charter or public description:

- §1 **“What this is,”** line 14: **“A kill switch that outranks everything … cannot be vetoed …”**
- §5 step 5: **“metadata-only schema — the formats have no fields capable of carrying memory, personal data, or secrets”**
- §3 item 3: **“Reference implementation, Apache-2.0,”** without an owner election/provenance qualification.
- §7: **“the current model”** with 69.2% coverage and ~31% HOLDING (historical v4, not gen3 F2's about 5–6% HOLDING).
- §6 exit is right to be unilateral, but the proposal must read with the revised current exit language below—not forced rejoining.

The latest `README.md`, `LIMITATIONS.md` and `reference-model/report.md` qualify these globally, but the **internal-only audience** does not remove the need to prevent a historical draft being read as a present claim or license grant.

**Recommended exact caption at the top of `ruling/distribution-proposal.md`, before its title:**

> HISTORICAL DRAFT / SUPERSEDED TEXT FOR LOCAL RECORD ONLY. Preserved for provenance; do not use as the current charter, license, announcement or claims source. Current controlling texts are root `README.md`, `LIMITATIONS.md`, and `reference-model/report.md`. No Apache grant has been elected, no independent external review exists, and gen3 F2 retains the A4 WALL. §1's kill-switch language lacks signer-capture/recovery limits; §5's schema language has no actual-content audit; §7 reports v4 historical values (69.2% coverage / about 31% HOLDING), not F2 values (0.940 coverage / about 5–6% HOLDING on tested drift streams). All publication, federation, deployment and pilot actions remain separately unauthorized.

If broad claims are retained for design history, prefix them inline: **“Proposed design objective, not established by this implementation:”**. For §1 replace rather than repeat: **“Proposed local recall/freeze design subject to signer-capture, recovery, availability and real-network limitations; no blanket outranks-all kill-switch claim.”** Do not prescribe an operative license/consent from the superseded plan.

### 4. Exit/change text must give usable choice, not a forced rejoin

**Location:** `LIMITATIONS.md`, bullet **“Operator charter”**, line 8: **“usable decline/export path before any material change … Neither is implemented …”**

The boundary is directionally correct, but with the A4 residual false rejects, approximately 5–6% HOLDING, signer/recovery GAPs and no implemented operator interface, no usable consent choice exists in this packet. ROOT-admission or Guardian ACK is not deployment authorization or owner consent. The charter should not confuse **unilateral participation exit** with a technical unfreeze/rejoin from a HOLDING/quarantine.

**Recommended exact replacement for that entire bullet:**

> - **Operator consent and usable exit (none implemented in this packet):** before any material change takes effect, the operator must receive clear notice and fresh affirmative consent to that change, with a genuinely usable ability before the effective time to decline, leave future federation participation, stop local operation safely, and retain/export their own data. Disclose the limited epoch-history exception before joining. Exit from participation does not undo an already accepted revocation or a local HOLDING freeze; technical unfreeze/rejoin, a remote guardian's acknowledgment and any periodic membership step are separate and cannot be a substitute for exit or deployment consent. State retention, beacon recipients, polling/revocation interval and stale-head/failure behavior. These controls are not implemented and remain prerequisites before any deployment or pilot. A receipt, signature acknowledgment or static-verification PASS is not consent to install, deploy, join or federate.

“Remote Guardian ACK is not consent” also addresses the synthetic certificate stated in F2 spec §2 and report GAPs; those are not actual owner authorization. Existing `LIMITATIONS.md` separately preserves informed remote-revocation opt-in and stale-head cost; keep it. No forced periodic join/rejoin is authorized.

### 5. Carry the full caveats explicitly on the cover

**Location:** `README.md`, first three lines: technical wall, nonproduction and gen2/gen3 status are clear, but it lacks the explicit no-publication/outside-access/deployment/federation, no-government/national-authority/coverage, private-research attribution and no-certification/prevention-guarantee statements expected by the earlier Counsel §7 review.

**Recommended exact addition immediately below title/before packaging history:**

> **Private Byrne Ventures research; no government, national-security or external endorsement or authority claimed; no current network/nationwide coverage. Local authorized review only. No outside access, publication, deployment, pilot, federation, activation or sharing is authorized. Not certified, not production-ready, not audited by an arms-length reviewer; no security, prevention, anonymity or flawlessness guarantee. Acknowledging receipt or limitations is not consent to install/deploy/join/federate. See the complete `LIMITATIONS.md` and report before using this candidate.**

This correction addresses the actual page-one standalone statement; the linked current report keeps A4 prominent. Do not claim a certification or “independent security review” from crew QA. Read root/consent text together.

## Confirmed fixes / not false positives

- **License / owner rights:** `LIMITATIONS.md` line 2 says no license “is granted or presumed”; SBOM note denies a package-own-source license. No LICENSE headers or present public grant override that. The historical Apache-2.0 future proposal needs the caption above, not a new grant. The dependency list is incomplete as a full provenance audit: AI/crew ownership, upstream notices, files, history and corpora remain a rights check before any release. Current local restricted handling remains owner/private-rights, not automatic open source; “non-private crew snapshot” in README means snapshot-of-local-crew-material, not a permission grant.
- **No asserted privilege misuse found in current control texts.** The packet's Counsel review expressly says internal issue-spotting and not attorney-client privilege. That remains an accurate characterization. Prior frozen historical QA is not transformed into gen3 inspection; historical key/corpus/package FAILs and filename-collision corrections must remain preserved as history.
- **Key custody labels:** `keys/NOTICE.md` line 3 identifies separate synthetic packet and test-log public keys; its private halves are recorded off-package. `LIMITATIONS.md` says synthetic/nonproduction. The earlier gen1 private test key disclosure and gen2 removal remain appropriate corrections. Counsel inspected the static file/key receipt and did not independently replay the code or certify public/private handling in repository history: the 185-MiB `history.bundle` still needs a full privacy/rights/security audit before later disclosure. A focused inspection of its Git history exposed no `*.key` paths or matching PEM private-key blocks. That narrows the key concern but is not a complete privacy, credentials or rights clearance.
- **Consent vs deploy:** previous Counsel §1 (access ≠ activation; acknowledgment ≠ consent) is present; current README should make it stand on its own as above. No “one step silently activates” behavior was found in these current texts. Operator document signatures are future actions, not this packet's permission. Any remote/revocation feature remains an operator opt-in, with loss-of-freshness and availability tradeoffs disclosed.
- **Exit:** correct distinction is between unilateral refusal/future-participation exit and a gated safe resumption/unfreeze after compromised or frozen state. `LIMITATIONS.md`'s nonimplementation correctly prevents treating this future right as functional now.
- **Claims:** current root/report carry the observed .0686 A4 FAIL and real-network / external-review / production-crypto / insider-key GAPs. R3 fresh-comparison values (F1 158.866→161.724 seconds; F2 138.851→506.494 seconds) are reported as exact-comparison exclusions for top-level runtime, not concealed experimental wins. Although F2 reports coverage 0.940 on drift5, that does not cure the A4 upper bound or ground “all green.” Do not infer general effectiveness, causal production protection, uniqueness or live-federation operation.
- **Reactor/root-ownership supporting document gap:** a text search of the gen3 tree did not locate any separate reactor / root-ownership consent package under that description. The supplied `V5-CREW-HANDOFF.md`, root/report GAPs, F2 spec §2 and my operational consent constraints were reviewed. If another reactor document was intended, it was not included in the candidate path and receives no textual clearance in this report.
- **No real agent credential clearance:** no actual account credential was observed in the local text audit; no value was sought or copied from any outside account. Static verification states no private key files ship, and gen2's copies identify only synthetic keys, and the subsequent focused gen3 Git-history scan found no `.key` path or matching private-key PEM. That observation is not a full archival/history/privacy certification or an authorization to deploy. No outside contact occurred in this review.

## Standing remaining flags

| Priority | Current state | Consequence |
|---|---|---|
| P0 | gen3 F2 A4 fails: drift5 FRR 0.0686, upper CI 0.0699 > 0.05 | Technical WALL continues; no production/pilot claim or coercion can proceed. |
| P0 | Root/key-capture and independent operator governance remain unrealized | Root/Owner/GENESIS/Guardian key compromise or collusion may poison authorization; local labels alone do not fix it. |
| P0 | Arms-length external reviewer/security review absent; gen3 independent QA pending | Crew QA and R3 reproducibility are not outside independent review or a gen3 PASS. |
| P0 | Full-history privacy/secrets review and actual artifact scan not certified | No general PII/no-history-private-key guarantee, public-source eligibility, trade-secret/security-assessment conclusion or public archive decision. |
| P0 | Consent/exit interface, notice/retention and production key controls not implemented | Charter proposal, not operational consent; no deployment or pilot. |
| P1 | Historical distribution language and v4 numbers remain unmodified | Current overlay above required; preserve original as history, not erase evidence. |
| P1 | Rights/provenance/SBOM and named crew contributions incomplete | Private owner rights retained; no license grant automatically, Apache recommendation remains future owner choice/audit. |
| P1 | Correct root receipt copy and date reproduction limitations explicitly | Misleading stale “gen2 pending” should not survive a new seal. |

Items calling for counsel/professional review mean appropriately qualified review, not that this issue-spotting note supplies a privilege, export, patent, authentication or licensed-legal clearance. Any future foreign-person/foreign-hosting recipient requires separate facts and export assessment; future public disclosure also raises separate patent, secrecy, privacy and copyright questions. Current act is local internal handling only.

## Final call

Counsel leaves **WATCH** as the local legal/disclosure classification. After the authorized integrator makes the five text-only corrections and files new manifests, local handling of a candidate can be reconsidered for text coherence, but **no later outside access, publication, review sharing, pilot, operation or federation follows from this review** without Mike's own specific approval, satisfied technical/security requirements and appropriate qualified professional reviews. Nothing here greenlights those actions.

### Source hashes reviewed

| File | SHA-256 |
|---|---|
| `README.md` | `703e07fd003ea16477effa16e51edc517094269004aac4724e6e1e94c15f9db7` |
| `LIMITATIONS.md` | `794bcc55ec902788efbc623d54e319400a452c7ec79da959f1deb2112144574c` |
| `PACKAGING-RECEIPT.md` | `0d149b5ef64c32827fd2bfcc90f5ee72226c0b4ea4a7e6059710fa856785d97b` |
| `R3-RECEIPT.md` | `ec376c762d7090a9ef691bfbe5fc2445a8d43d8cc56d2dcfe99c0c69e302c92d` |
| `reference-model/report.md` | `1cbdd1d7c350351e2164a4da90801c4a84d118593ebbed9af67fd21aaafa6529` |
| `ruling/distribution-proposal.md` | `5259382552a9ca6616c17b842ad359d675e07f240c1fd212348a9312b03cfa21` |
