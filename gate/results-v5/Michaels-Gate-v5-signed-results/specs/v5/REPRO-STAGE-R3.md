# Stage R3: reproducibility only. Registered BEFORE execution.
No algorithm, protocol, threshold, hull, cadence, drift, corpus, or acceptance change. No new evaluation claims: results are reported as observed only.
Executed on a disposable copy of candidate gen2 (tar sha256 7d0264eb…). Gen1 and gen2 stay frozen.
1. Full inherited batteries: `INHERITED_FULL=1`, i.e. `inherited/v3/reference-model/verify.sh` and `inherited/v4/reference-model/verify.sh`.
   - Their own internal asserts are the criteria: v3 Q8 bit-exact; v4 D exact and E exact apart from its own pre-existing `cost_resolve_us_mean_mean` exclusion.
2. F1 (`q8F.py`) and F2 (`q8F2.py`) reruns. The fresh payloads are KEPT and compared independently against the shipped originals.
   - Equality must be exact JSON equality after removing ONLY the top-level `runtime_s` (declared at gen2 packaging, not pre-registered in F1/F2).
   - Nested embedded `frozen` and `impl` objects must be identical, and their hashes must still match the shipped files.
   - The byte-level difference (cmp count and first offsets) is printed and logged.
3. Full unit test suite.
Pass = all asserts hold. On failure: packaging-only remedies, no result edits.
