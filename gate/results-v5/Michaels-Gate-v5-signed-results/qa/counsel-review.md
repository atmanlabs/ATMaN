# Michael's Gate v5: Counsel review of the sealed internal review packet

**Status:** Counsel draft for Chief of Staff. This is internal legal issue spotting, not an external legal opinion. Prepared 2026-11-05, about 23:45 ET, before v5 local results are final.
**Scope:** Legal issue spotting for a sealed internal review packet. The packet holds authorized source and evidence for review only. Mike authorized local technical repair and collation (HANDOFF.md; COLLATION.md lane 5). He did not authorize outside disclosure, publication, sales or a pilot. This draft grants no permission to publish.
**Standing STOP:** No nonconsensual replication, bypass, push or self-propagation, in any phase or under any framing.

## 1. Bottom line: WATCH

The only package covered here is a local, authorized source and evidence packet. A pilot is not supported. The record shows why:

- **v4 drift wall.** Arm D and arm E both fail frozen criteria 3 and 4. Legit-drift clean FRR is 0.072 [0.069, 0.074] against a UCL bound of 0.05. Coverage on legit drift is 0.692 against a bound of 0.90, with HOLDING for 31% of the time and a Guardian load of 12.1 per 1k events (v4 report). The distribution proposal's own §7 says this "alone bars any real pilot."
- **Park load.** Arm E produces 110–315 parks per 1k events on the package families and 180 per 1k on fine_ratchet_ext. An attacker can inflate this cost until the park-cost bounds proposed in v5 are implemented and tested.
- **Bounds on any claim.** Uniqueness remains GAP. D ties C on every v3 attack family and is worse on legit drift (FRR 0.072 vs 0.043) and on adaptive white-box FRR (0.175 vs 0.000). E adds measured value only on lineage-class attacks. "Authorized ancestry is necessary, not sufficient." Also GAP: production Φ, production threshold cryptography, real networks and gossip, the genesis social layer and union-registry depth.
- **Diagnostic is not evidence.** The rudder-off run (`artifacts/diag_posthoc_rudder_off.json`) is exploratory. It cannot count as acceptance evidence.
- **No early upgrade.** v5 results need their own separate receipts: pre-registered protocol hashes, a fresh drift corpus frozen before testing, and a signed bundle. They must not upgrade any packet statement until they exist and verify. If a v5 result is missing, it is listed as GAP, not PASS.
- **Access is not activation.** Authorizing someone to see the packet does not authorize deployment, installation on a participating node, or activation.
- **Acknowledgment is not consent.** A reviewer's signed acknowledgment confirms receipt and the limits on use. It is not consent to join, operate or federate.

## 2. Contents of the sealed packet

1. **Cover sheet.** It carries the page-1 caveats (§7). It claims no public, government or national authority, names the authorized recipients and a packet ID, and states that review access is not permission to deploy.
2. **Method and spec versions.** Include `OWNER-RULING.md` (f3fdfef9…), `OWNER-ORYN-TRACE.md` (6b18b057…), `V4-FROZEN-SPEC.md` (fee23ddf…), `V4-E-ADDENDUM.md` (4ace3375…), the v3 spec, and the v5 pre-registration once frozen. Superseded versions stay in, marked as superseded.
3. **THREAT-MODEL.** It must cover:
   - root-admission trust (insider and stolen-key lineage are outside the Trace's reach);
   - Guardian capture;
   - signer compromise and the recovery path;
   - liveness and park-load abuse;
   - epoch forgery and replay;
   - domain spoofing;
   - HOLDING abuse.
4. **Synthetic reference source and build reproducer.**
   - Include `verify.sh` and a statement of what it asserts: hashes, signed bundle, v3 battery, D and E regressions, Q8 stages and bit-exact reproduction.
   - State the isolation status: in-process simulated transport only, and no external networking during build or test. If no network-disabled run has been recorded, that is GAP.
5. **Frozen protocols and an ordered change log.**
   - Show pre-registration before evaluation, with commits 4e9eb88, c793e03, 5e52b0c, e7cd87e and 593fbe7, plus the v5 equivalents.
   - Record the two E implementation fixes (the BODY_FOR_TYPE mapping and the aggregation crash) and their receipts in `artifacts/cycles/`.
   - Disclose the v3 timestamp-only diffs.
6. **Full evidence, failures included.**
   - Include the falsified v3 Judge (harm 0.94 vs 0.00 for the no-Judge arm), both v4 failures, and the narrow P1d pass (0.298 vs a 0.30 bound).
   - Include the raw local signed bundles: `artifacts/bundle/MANIFEST.json` and `MANIFEST.sig`.
7. **LIMITATIONS.md** (see §4).
8. **Inventories.**
   - A file inventory that covers repository history and generated artifacts, not just the current tree. That includes `.git`, archives, wheels and notebook outputs.
   - A dependency SBOM with licenses.
   - A third-party and data provenance map.
   - A clean-room note stating who wrote what and from which sources.
   - NIST SSDF (SP 800-218) is a reasonable frame for these, not a certification.
9. **Hashes and signatures.**
   - SHA-256 of every file and detached packet signatures.
   - The packet-signing key must be distinct from the SYNTHETIC test-log key in `artifacts/keys/`, and both must be labeled so neither can be mistaken for a production key.
10. **Provenance without privacy leakage.** The provenance records must not reveal personal data, Owner conversations, memory files or account identifiers.
11. **Key handling.**
    - Synthetic test keys live in an isolated namespace and are never reused elsewhere.
    - No real credentials, tokens or account keys appear anywhere in the packet.
    - Reviewers receive no copy of any secret or real data.
12. **Code status label.** This is reference code. Its multisignature is "synthetic multisignature (t-of-n), not production threshold cryptography." It is not production security code.
13. **Reproducibility receipt.** Append the local packager's `verify.sh` result with date ET, environment and outcome; a reviewer-side result belongs only if obtained during an authorized review. A failure is recorded as a failure.
14. **Logs.** Include only the minimum the data map justifies. No log is called "metadata-only" until an inventory shows what its fields and values can actually carry.

## 3. Sealed packet vs. a future open-source release

- **Apache-2.0** ([Apache License 2.0](https://www.apache.org/licenses/LICENSE-2.0))
  - It works only as a grant by the actual copyright owner, over material that owner actually wrote. It cannot override an upstream license on any dependency or copied code.
  - Privately supplying source does not automatically place it under Apache-2.0 or make it open source. If Mike elects to apply the license to identified owner-authored files, that grant permits recipients to redistribute those files under its terms; an NDA cannot revoke those license rights. State explicitly which files are licensed and which are confidential.
  - License §4 (redistribution conditions, including carrying NOTICE) and §6 (no trademark grant) need a correct NOTICE file. Attribution must not imply endorsement by any project, agency or reviewer.
  - Keep applicable license and NOTICE notices with already-licensed files, including during review. New license grants attach only to the identified material; keys, logs, corpora and generated outputs need separate rights decisions, not a blanket statement that they automatically share the code license.
- **Trade secret** ([18 U.S.C. §1839](https://www.law.cornell.edu/uscode/text/18/1839))
  - Protection under the federal definition requires "reasonable measures" to keep the material secret. A "sealed" label alone does not meet that.
  - Recommended measures are named authorized reviewers, written limited-use/confidentiality terms where disclosure permits them, least-privilege tracked access, and return or destruction rules for confidential material. These terms do not eliminate existing open-source license rights.
  - Do not claim attorney-client privilege over the whole packet. Calling this internal review “Counsel” does not itself establish that privilege.
- **Export, before any non-team review** ([EAR §734.3(b)(3)](https://www.ecfr.gov/current/title-15/subtitle-B/chapter-VII/subchapter-C/part-734/section-734.3), [§734.7](https://www.ecfr.gov/current/title-15/subtitle-B/chapter-VII/subchapter-C/part-734/section-734.7), [§742.15](https://www.ecfr.gov/current/title-15/subtitle-B/chapter-VII/subchapter-C/part-742/section-742.15))
  - The packet contains signature and verification code. A restricted packet does not ordinarily establish public availability under §734.7, but publication, encryption exclusions, classification and authorization are distinct questions. Do not assume either that sealing is a violation or that an exemption applies.
  - An NDA is not an export classification.
  - Before any foreign-person, cross-border or foreign-hosted reviewer gets access, record functionality, recipients, destinations, access and storage arrangements and obtain a qualified export check against the then-current eCFR. The cited rules were read 2026-11-05; no EAR clearance is given here.
  - Screen recipient location, nationality where legally relevant, sanctions and hosting route without collecting unnecessary personal data.
- **Patent** ([35 U.S.C. §102](https://www.law.cornell.edu/uscode/text/35/102); [MPEP §2152](https://www.uspto.gov/web/offices/pac/mpep/s2152.html))
  - Confidential review is not automatically a public disclosure, but confidentiality alone does not settle public-use, offer-for-sale or other public-availability questions under §102(a)(1). The one-year inventor-disclosure exception is conditional, not a general permission to wait.
  - If Mike wants to keep patent options open, registered patent counsel must be consulted before any standards submission or public package.
  - No patent is claimed now, and no packet text should say "patent pending."
- **Privacy.** Logs, beacons and epoch histories can be linkable through timing, identifiers or hashes even when no field is labeled personal. No "no personal data" guarantee is made without an audit of the actual artifacts.
- **Later publication of NDA-reviewed material.** If material shown privately under an NDA is published later, the release must state its license and data rights, cover reviewer-contributed derivatives (reviewers' findings stay theirs unless they assign them), and lift NDA restrictions only by a written act.

## 4. Required packet files

| File | Must say |
|---|---|
| LICENSE | For a later licensed package: Apache-2.0 only for identified owner-authored files after Mike elects the grant; existing upstream notices preserved. For a confidential review packet: distinctive limited-use review terms, not a false Apache grant |
| NOTICE | Attribution, third-party notices, no endorsement |
| LIMITATIONS | §1 numbers, GAPs, ancestry ≠ truth, park load, not pilot-ready |
| THREAT-MODEL | §2 item 3 |
| CONSENT-CHARTER | §5 conditions |
| REVOCATION-EXIT | Content, release and exit revocation; polling-bounded reach; signer capture and recovery limits |
| SECURITY | Research status; no guarantee; known failure modes |
| SECURITY-RESPONSE | Internal-only intake. No external channel is opened or contacted under the current authorization. |
| Provenance / data-dependency inventory | §2 item 8 |
| Hashes / reproduction / signed results | §2 items 9 and 13 |

- **Defective fixes.** For an authorized later release, issue a fix as a new version, signed by the currently active signer set. Nothing is published under current authorization; retired or compromised signers authorize no new fixes, and key rotation/compromise recovery remains a P0 design gate.
- **No guarantees.** No packet file states a guarantee of any kind.
- **Reviewer findings.** Reviewers may attach independent findings and dissent unedited (proposal §8.4).

## 5. Consent charter conditions (each operator individually)

1. **Who signs.** An operator with actual authority and capacity over the node signs. A reviewer, vendor or agent cannot sign for them.
2. **Guardian scope.** Guardian authority covers the operator's own node only. Joining a federation is a separate, optional and separately signed act.
3. **No Byrne powers.** The proposal assigns Byrne Ventures no participant-node revocation authority, keys, access or visibility and no phone-home. Retained release-signing or public update-notice responsibilities must be described separately if kept.
4. **Fetch and install.** The operator deliberately fetches the package and verifies its hashes against a fingerprint obtained out-of-band. Installation goes to an isolated environment first. Install, charter signature and activation are each separate acts.
5. **Separate choices.** Each optional disclosure, federation or data-sharing feature requires an affirmative choice. Nothing automatically installs, activates or replicates the package; security functions the operator expressly enables may then run only within their documented scope.
6. **Revocation source.** Revocations come only through the operator-selected mechanism and endpoints. The consent charter must distinguish manual fetching from an operator-enabled automated polling/security service, its interval, reach and failure behavior. An enabled background process is not an unsanctioned transmission, but it must never be secretly enabled.
7. **Beacons and logs.** The charter states the scope, recipients and retention period, and sets an exclusion requirement for memory, personal or secret content that must be verified under item 14 of §2.
8. **HOLDING.**
   - It freezes writes and accept-votes and serves last-good reads.
   - Its liveness cost needs a demonstrable bound; that bound is unknown until v5 park-load tests pass and therefore blocks outside activation.
   - The operator is provided a signed, intelligible reason record for any HOLDING through an operator interface. Unreadable or unavailable diagnostics are GAP, not silently waived.
   - Quarantine and timeout rules are disclosed.
9. **The operator's own rights.** The charter explains the operator's rights and the design's autonomy constraints. The operator can export their own data before exit.
10. **Material changes.** Changes to scope, the feature map, Guardian composition or the signer set require fresh notice and fresh acceptance before activation.
    - The 64-epoch leave window opens only after notice is given, never by advance commitment.
    - The window must give a genuinely usable exit before the change takes effect. A notice window or exit does not undo an accepted revocation or freeze, but the operator must be able to decline future federation participation, retain/export their own data and disable the local system safely.
    - The charter must distinguish an operator who left before a change took effect from the immutable epoch-history record. That record is the one retention exception and is disclosed at join.
11. **Automated authorities.** Every automated root, key, Guardian and recall authority is disclosed.
12. **Remote revocation.** Receiving and applying remote revocations needs separate, informed opt-in. Default to local/manual review until the signer hierarchy, compromise recovery and replay behavior pass their gates. If automatic revocation remains disabled, the resulting exposure and loss of revocation freshness must be stated plainly, not called the most protective configuration.
13. **Emergency security.** An emergency security path acts only on consenting nodes. No one can consent on behalf of strangers, and there is no scanning.
14. **Signing terms.** No blanket waiver of all liability or of all rights. The operator signs only after reading the documents.
15. **Research use.** No signing is mandatory for research evaluation, and no decision about a third party's system is made for them.

## 6. Future review-only source/evidence distribution

- **No date set.** This draft does not schedule publication.
- **License.**
  - Recommended: Apache-2.0 for human-authored original files only, after the SBOM and rights audit.
  - Document the research status, the risks and the excluded uses: no high-stakes deployment.
  - A "defensive use only" field restriction would not be open source ([OSD §6](https://opensource.org/osd)). If such a restriction is wanted, do not call the release open source.
- **Warnings and claims.** Include a responsible-use warning and the Apache no-warranty disclaimer. Make no commercial or protection claim without adequate evidence.
- **Public release** needs a distinct, later written approval from Mike as owner, plus a terms review and a review of the final artifacts. Proposal §9.8 also requires Counsel to re-check the final texts.
- **Sealed access under a later authorization.**
  - Limit access to specifically authorized reviewers under appropriate confidentiality/limited-use terms, with tracked access and no forwarding beyond those permissions. No outside access is approved by this draft.
  - Under the current assignment, no outside messages, uploads or invitations.
- **Permanently excluded:**
  - grown-brain contents, learned or validated state, logs and memory;
  - personal data, including unnecessary dates and names; no obituary or family research details belong in this packet;
  - credentials;
  - third-party corpora or training data of unknown origin;
  - secret root or Guardian keys;
  - real production fingerprints or network configuration;
  - attack scaffolding or exploit code targeting live or third-party systems; keep defensive regression tests synthetic, local and scoped to the reference implementation;
  - raw outputs containing personal data, secrets or linkable identifiers; if an authorized packet truly needs identifiers, document the purpose, retention and safeguards instead of promising that a schema makes them anonymous.
- **Attack tests** are defensive only: synthetic, and never against a user's or a third party's system.
- **No outward dialing.** No production configuration that dials outward.
- **No invented privacy guarantee.** Never state "no personal data" without an audit.

## 7. Required caveats on the packet cover and prominently in standalone public-facing summaries

1. Private, unendorsed research by Byrne Ventures.
2. No government, national-authority or national-security claim, and no nationwide reach or coverage claim.
3. Not audited or certified. No security or prevention guarantee.
4. Not deployment- or pilot-ready.
5. All tests are synthetic reference-model tests run locally. Results do not generalize to production or real networks.
6. The v3 Judge was falsified (harm 0.94). The v4 drift wall (FRR 0.072, coverage 0.692) is unresolved until separate v5 receipts verify.
7. No current measured production coverage, and nothing is shipping.
8. Language changes:
   - Replace "a kill switch that outranks everything" and "cannot be vetoed" (proposal §1) with: "proposed local design; signer capture and recovery remain security limitations."
   - Also qualify the §5.5 phrase "metadata-only schema … no fields capable of carrying …"
9. Never describe a draft package as safe.
10. Any license or review is not an endorsement.
11. Nothing here is public, and nothing here grants permission to publish.

## 8. Unresolved flags

| # | Flag | Type |
|---|---|---|
| P0 | Single-signer revocation can freeze the system permanently. Threshold recall and signer-compromise recovery are not specified or tested. | Owner design decision + counsel check of the charter wording |
| P0 | Do not provide outside access under current authorization. Before any later foreign-person or foreign-hosted review, record functionality/recipient/access facts and obtain qualified export review | Authorization gate + qualified export check |
| P0 | Rights/provenance/SBOM audit, including repository history, before Apache-2.0 headers go on files | Owner/copyright holder decision + qualified rights review |
| P0 | Proposal §1 and §5.5 language (§7 item 8) | Owner decision |
| P1 | Patent-preservation choice before any outside disclosure | Owner decision + registered patent counsel |
| P1 | NDA terms, reviewer list, trade-secret measures | Owner decision + counsel check |
| P1 | Privacy audit of actual logs and beacons for linkability | Counsel check |
| P1 | Park-load and HOLDING liveness bound to state in the charter (v5 pending) | Owner decision on the re-imprint cadence parameter |
| P2 | Trademark/name use; NOTICE endorsement wording | Counsel check |
| P2 | Reviewer dissent attachment procedure | Owner decision |

These are gates before the relevant act, not tasks for Mike now. Items marked “counsel check” are flags for appropriate qualified review, not claims that this draft supplies it.

## 9. Checklists

**Before the sealed handoff (internal):**
- [ ] Final v5 receipts verified separately, or marked GAP
- [ ] SHA-256 for every file, detached signature, signing key ≠ test key
- [ ] Rights map, SBOM and clean-room notes complete
- [ ] History, generated artifacts, logs, keys and private material excluded; scan receipt attached
- [ ] Packet-cover caveats and prominent limitations on standalone summaries; §7 item 8 language fixed
- [ ] Authorized reviewer, applicable confidentiality/review terms and access logging arranged only after outside-access authorization. Nothing in this draft states that any of this has happened.

**Before any public release or pilot (later, separate owner approval):**
- [ ] Every item in proposal §9, items 1–8, passed with pre-registered criteria
- [ ] Arms-length independent review complete (proposal §8), with dissent attached
- [ ] Export, patent, privacy and license reviews scoped to the actual recipients and artifacts by appropriate qualified professionals
- [ ] Final charter, announcement and terms re-checked
- [ ] Written owner approval for that specific act

No third-party contact has occurred, no signature has been obtained, and no independently verified v5 fixture result is yet claimed here. The STOP stands.
