# Michael's Gate v5: candidate GENERATION 4 (LOCAL SYNTHETIC REFERENCE MODEL · RESEARCH/REVIEW ONLY)
**Private Byrne Ventures research; no government, national-security or external endorsement or authority claimed; no current network/nationwide coverage. Local authorized review only. No outside access, publication, deployment, pilot, federation, activation or sharing is authorized. Not certified, not production-ready, not audited by an arms-length reviewer; no security, prevention, anonymity or flawlessness guarantee. Acknowledging receipt or limitations is not consent to install/deploy/join/federate. See the complete `LIMITATIONS.md` and report before using this candidate.**

- **Technical verdict:** DESIGN WALL at A4 (drift5 FRR 0.0686 [0.0672, 0.0699] > 0.05). F2 passes 8 of 9 criteria. This is a local synthetic model. Not flawless, not production; no real network, hardware, or external review.
- **Packaging status:**
  - gen1 FAIL (Kodi).
  - gen2 PASS (Kodi, independent, with its stated GAPs: `reference-model/crew-evidence/round3-full-20261106T0052/kodi-gen2-verdict.md`).
  - gen3 PASS (Kodi, independent: `reference-model/crew-evidence/round5-kodi-gen3/kodi-gen3-verdict.md`, sha256 12c32e85…). This is the current sealed technical-parity packaging, i.e. a PRE-FINAL-TEXT PASS. Caveat: it covers packaging integrity plus retained R3 evidence compared against the actual bytes; Kodi did not personally rerun v3/v4/F1/F2.
  - **gen4 (this package) PENDING its own fresh Kodi verification.** No earlier verdict carries over. Gen4 is not independently replayed.
- **Counsel:** WATCH (local only), per review 16fce854….
- **What gen4 is:** gen3 plus Counsel's five text corrections only (`reference-model/crew-evidence/round4-counsel-gen3/counsel-gen3-review.md`, sha256 16fce854…). No model, protocol, corpus, or result change, so no new evaluation was needed. The R3 receipts still apply (`R3-RECEIPT.md`).
- **Scope:** this packet is NOT an operational consent charter, exit implementation, or threat model. It promises none of them as present features (see `LIMITATIONS.md`).
- **No reactor or root-ownership document:** none was asserted or included. Counsel found none, and none is cleared.
- **`ruling/distribution-proposal.md`:** a HISTORICAL/SUPERSEDED draft with a caption. Its exact original bytes are in `ruling/history-original/distribution-proposal.md` (sha256 52593825…).
- **Filename collision:** `kodi-final-verdict.md` (05aa5f16…) is Weeboh's text, not Kodi's, and not a gen1 pass. Weeboh's corrected QA file is `weeboh-delegated-qa.md` (dea366c9…).

**Verify:**
- `python3 verify_static.py`: read-only.
- `python3 verify_history.py`: needs git. The git bundle proves ordering and content, not wall-clock time.
- `./replay.sh`: runs in a temporary copy. Set `INHERITED_FULL=1` to also run the full v3/v4 batteries.
