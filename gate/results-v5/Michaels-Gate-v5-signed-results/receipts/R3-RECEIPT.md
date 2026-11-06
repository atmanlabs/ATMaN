# R3 reproducibility receipt (observed only; no algorithm/protocol/corpus/threshold change)
- **Stage:** registered in `reference-model/REPRO-STAGE-R3.md` (commit 75addf8) BEFORE execution.
- **Where it ran:** a disposable extraction of the gen2 tar (sha256 7d0264eb…), 2026-11-06 00:51–01:20 EST. Logs are in `reference-model/artifacts/R3/logs/` and fresh payloads in `artifacts/R3/fresh/`.

| Step | Result |
|---|---|
| Inherited v3 `verify.sh` (full) | exit 0: battery 20/20, regressions 11/11, "Q8 results reproduced exactly", bundle signature OK |
| Inherited v4 `verify.sh` (full) | exit 0: "D and E stages reproduced exactly; GREEN D = False GREEN E = False" (E excludes its own pre-existing `cost_resolve_us_mean_mean`); bundle OK |
| v5 unit tests | 79 OK |
| F1 rerun vs shipped | JSON equal except top-level `runtime_s` (158.866 → 161.724 s). Same length; 15 differing bytes, all at offsets ≥ 47861 (the runtime_s value) |
| F2 rerun vs shipped | JSON equal except `runtime_s` (138.851 → 506.494 s; the box was loaded). Length −1; 18 differing bytes at offsets ≥ 32631 |
| Nested checks (F1 and F2) | embedded `frozen` == F1_FROZEN.json; embedded `impl` == F1_IMPL/F2_IMPL; every impl_sha256 matches the shipped sources |

- **Observed acceptance:** F1 fails A4 and A6. F2 fails A4 only. Unchanged.
- **The verdict is still a DESIGN WALL at A4.** R3 adds no new result claims.
- `artifacts/R3/run_r3.sh` and `compare_r3.py` are verbatim receipts containing the absolute paths they ran with (`/workspace/mg5-repro3/...` and `/workspace/michaels-gate-v5-candidate-gen2/...`). They are provenance, not package entry points; the package entry point is `replay.sh`.
