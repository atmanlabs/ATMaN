# PATHS: original absolute locations → package paths (provenance; NOT executable contract)
The frozen manifests (for example `inherited/v4/ruling/SHA256SUMS` and `inherited/v3/sealed-package-sha256.txt`) still contain their historical absolute paths byte-for-byte. Those paths are not rewritten. `verify_static.py` checks the same bytes through the relative package paths below, mapping by basename.

## Directory mapping
| original | package |
|---|---|
| `/workspace/michaels-gate-v5/reference-model/` | `reference-model/` |
| `/workspace/michaels-gate-v5/ruling/` | `ruling/` |
| `/workspace/michaels-gate-v4/reference-model/` | `inherited/v4/reference-model/` |
| `/workspace/michaels-gate-v4/ruling/` | `inherited/v4/ruling/` |
| `/workspace/michaels-gate-v3/reference-model/` | `inherited/v3/reference-model/` |
| `/workspace/michaels-gate-v3/` | `inherited/v3/` |
| `/workspace/michaels-gate-v5/crew/` (originals untouched) | `reference-model/crew-evidence/` (read-only copies; round2-* = Kodi receipts + Weeboh QA) |
| `/workspace/michaels-gate-v5/HANDOFF.md` | `V5-CREW-HANDOFF.md` |
| original v3 attachment ZIP `/home/box/agent-data/.../adaa7244….zip` (sha256 7fa6011c…) | NOT shipped; provenance only. Its 6 documents ship in `inherited/v3/michaels-gate-sealed-package-v3/` and are checked against `verification.json` |

## Omissions from inherited copies (disclosed)
- `.git`, `__pycache__`, and synthetic private `*.key` files: not shipped. The keys stay isolated at their original v3/v4 locations.
- Inherited trees ship `q8_corpora.npz` as hard links to the single byte-identical copy at `reference-model/artifacts/v3_inherited/q8_corpora.npz` (sha256 823d07b9…).
- v4 `artifacts/q8E_results.partial.json` is shipped unchanged: it is an original v4 byte, not v5 output.

## Key files (sha256)
| package path | sha256 |
|---|---|
| `inherited/v4/ruling/owner-v4-ruling.md` | `f3fdfef970a5d544560151819847d9b0b84a58fb04113c5342d92d752c0e8027` |
| `inherited/v4/ruling/owner-v4-oryn-trace.md` | `6b18b0574588e0f31d764c0656b2ab82ab208829d193b70be1b27cf979af298d` |
| `ruling/distribution-proposal.md` | `5259382552a9ca6616c17b842ad359d675e07f240c1fd212348a9312b03cfa21` |
| `inherited/v4/reference-model/artifacts/v3_inherited/FROZEN_BATTERY.sha256` | `73b318e612b0424905ffb2dccbb39f804f40fa8e55577f163c628e4cb93e63a5` |
| `inherited/v4/reference-model/artifacts/v3_inherited/Q8_FROZEN.json` | `d271ed9edfaeb6c204ea8ec0c46b6e5aca56fce8c87c9846c69b3cef1fdef397` |
| `reference-model/artifacts/v3_inherited/q8_corpora.npz` | `823d07b920c67fb429cdd7583f95a927f401b7c67ae2b943f2b1ee4bdc38ed59` |
| `inherited/v3/michaels-gate-sealed-package-v3/01-v3-patch-spec.md` | `5eb18c2bfa92abfd73b09a44d62c8161ec39598ebbae8c053ac0d0d260c6ad5d` |
| `reference-model/artifacts/F1_FROZEN.json` | `b91714a7fe3ed930fbdf4a2d9cb54384a34c0125e085768ab09716ff45e55c8e` |
| `reference-model/artifacts/F1_IMPL.json` | `791a6f4db781589477afb61249042239f5ba0c0a6796f6ad1630beeeb87065b4` |
| `reference-model/artifacts/F2_IMPL.json` | `82950a70def842e991a1f2f88b959a46f7c56449487b99fbaef62f5f77c2cbf9` |
| `reference-model/artifacts/q8F1_results.json` | `3c4365d61042053f9835e05a9e6ad4baecb7fb4223e9ffbc570fca2571b29f90` |
| `reference-model/artifacts/q8F2_results.json` | `3d2c90d9fd4b2435850d452938481aa4cb1436e47b7dab65eae66ef667474bc0` |
| `history.bundle` | `fb64a8fbe7281b85f13a693f8bbd8b608d3ef5e71bad48cbacee0cd484b409bc` |
- gen4: `/workspace/michaels-gate-v5/ruling/distribution-proposal.md` (original, unchanged) maps to `ruling/history-original/distribution-proposal.md`. `ruling/distribution-proposal.md` is the SUPERSEDED-captioned wrapper (caption + exact original bytes).
