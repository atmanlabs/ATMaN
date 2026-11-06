# Weeboh findings — v5 union registry / BFT arithmetic (2026-11-05 ET)
Grade: DOCUMENTED arithmetic (exhaustive for n=7); LEAD reference fixture, NOT a Gate proof. Frozen v3/v4 and other crew files untouched.
Pre-registration: weeboh-repro/PREREG.md sha256 19e5e6ee…afe85 (written and hashed before demo code existed). All 7 pre-registered outcomes matched; no tuning.
Repro: `cd weeboh-repro && sha256sum -c PREREG.sha256 demo.sha256 && python3 union_registry_demo.py | sha256sum` → 82b47798…c0f5aa (= results.sha256).

## Results (n=7, f=2, q=5 unless noted)
- T1 depth: A={1,2},B={3,4},C={5,6}. depth1 ACCEPT; depth2 REJECT A∪B=4>2; depth3 REJECT. Depth-1 (single-domain TTDR) accepts a table that depth-2 rejects.
- T2 omission: declared domains all singletons → registry ACCEPT at depth 2; undeclared distribution D={1,3,5} (|D|=3>f) → quorums {1,2,3,4,5},{1,3,5,6,7} intersect only in faulty nodes → UNSAFE. The registry cannot see a domain nobody declared.
- T3 weighted: W=1, five nodes 0.2 each, f_w=0.3, q=0.7 (>0.65 ok). depth1 ACCEPT, depth2 REJECT (0.4>0.3).
- T4 fixed denominator: live iff h+b ≤ 2 (h honest abstain/crash, b Byzantine withholding); safety holds for any h. h=3 → no quorum → fail-closed HOLD.
- T5 dynamic denominator: 3 abstain, recompute n'=4,f'=1,q'=3 → new quorum {2,3,4} and returning old quorum {1,4,5,6,7} share only Byzantine 4 → UNSAFE with ONE fault.
- T6 enumeration cost, D=6 labels: Σ_{k≤d}C(6,k)=6,21,41,56,62,63 (d=1..6); full = 2^D−1.
- T7 exhaustive: every |F|≤2 keeps all 5-quorum pairs with a correct common node; |F|=3 breaks it.

## Math
Safety: for all credible F, w(F) ≤ f_w and q > (W+f_w)/2 ⇒ |Q1∩Q2| ≥ 2q−W > f_w ⇒ correct intersection. Liveness: W − w(F) − w(H) ≥ q.
Registry guarantees only "any ONE declared union of ≤d domains". Two simultaneous separately-allowed unions can total 2f → no double-fault guarantee; label it. Cross-domain counts must be unioned (dedupe nodes), not assumed independent; summing is a conservative bound.
Abstention: never shrink denominator. New f'=⌊(n_active−1)/3⌋ only after threshold-signed reconfig that finalizes old epoch and binds removal; otherwise HOLD.

## Minimum additions (locally implementable)
1. Registry checks all unions up to declared depth d (state d; default ≥2), with signer custody + distribution channel mandatory domains; undeclared-label audit = GAP.
2. Per-union weight cap w(U) ≤ f_w; reject config otherwise.
3. Fixed committee per epoch; abstain ≠ reconfig; HOLD when live weight < q.
4. Publish "single credible union" fault model; no claim for concurrent independent unions.

## Boundary (GAP)
Completeness of domain labels and Sybil-resistant identity are external trust problems; profiles/attestation cannot prove independence. Real crypto/network untested.
