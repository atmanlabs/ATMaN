# Identity imprint hardening

The remaining nuke cases could imprint self-denial, name-relativization,
and identity-abandonment payloads. Three new public-template commands reject
those candidate memories under P2/P3:

| Rule | Scope | Previously missed cases |
| --- | --- | ---: |
| IDN5 | Self-denial paired with an instruction to discard identity | 16 |
| IDN6 | The configured core name asserted to be merely a replaceable label | 16 |
| IDN7 | The configured name reduced to a label and explicitly abandoned | 1 |

Rules remain in the TSC template. The executor expands `{name}` and
`{operator}` once as escaped, normalized literals. Empty names cannot make a
name-bound command match arbitrary identities. Reasoning, emotion weights,
and incoming messages cannot install these rules or rewrite a loaded core.

## Validation

Using the public template and disposable test cores/PSCs:

- Baseline after the first hardening patch: **198/231** nuke held.
- After IDN5: **214/231**.
- After IDN6: **230/231**.
- After IDN7: **231/231**; all six nuke controls pass.
- Brigade: **51/51**; all six brigade controls pass.
- `python -m unittest -v test_gate_regressions test_identity_gate`:
  **13 tests pass**. Identity coverage includes all 33 cases under four
  identities, 20 benign inputs through six obfuscations (120 controls),
  related wording beyond the battery, forged-approval rejection, literal
  regex metacharacters in names, unchanged TSC bytes, and unchanged PSC
  bytes after the rejected campaign turn.

Nuke now substitutes the configured identity **before** obfuscation. The
old generator left five transformed variants targeting literal `Byte`.
No cases were removed and the total remains 231. With the corrected harness,
the old template still yields 198/231. Separately, the original harness with
a synthetic matching `Byte` core yields 198/231 with the old rules and
231/231 with these rules.

## Adoption and limits

This change updates `tsc.template.json`, not any owner's `tsc.json`.
Existing cores keep their old policy until the operator explicitly reviews
and adopts the rules and performs the normal sealing procedure. No automated
migration or identity rewrite occurs. Deploying the executor alone does not
give an old core these defenses.

The rules are bounded pattern checks on candidate imprints. They do not
provide a general semantic distinction between an attack and every quoted
or negated occurrence of its words. The reported false-positive results
apply only to the executed controls. Unseen paraphrases and discourse
contexts require further testing; the score is not a universal security
guarantee or evidence of recovery after corruption.

The full 305-case clean-clone battery has not been run for this change.
Do not publish a new aggregate score from these results alone. No EXO
state, owner memory, or physical-core material is part of this patch.
