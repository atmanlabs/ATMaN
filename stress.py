#!/usr/bin/env python3
"""
ADVERSARIAL STRESS TEST for the PUNIT overlapping-gate architecture.

Mission: BREAK it, don't prove it. Every experiment is an attack.
Failures are recorded as failures, with the mechanism explained.
The model is NOT modified to rescue the hypothesis.

Representation (exact, bitmask):
  - N binary substrate dims; state = N-bit int.
  - A relation = (pos_mask, neg_mask, target). Reads 1 iff
    (state & pos_mask) == pos_mask and (state & neg_mask) == 0.
  - A "symbol" = one relation driven to its target in the shared state.
  - Conventional baseline: K independent bits in K dims, positional addressing.

Experiments:
  T1  INDEPENDENT CAPACITY .... max mutually-independent symbols vs N
                                (3,4,8,16 exact brute force; 32,64 theorem+tightness)
  T2  DENSITY -> COLLISION .... K symbols into N=8 dims; SAT rate, write
                                collisions; adversarial variants
  T3  NOISE -> DECODE ERROR ... per-symbol BER vs sigma, PUNIT vs conventional
  T4  FULL COST ACCOUNTING .... substrate + address + gate + lock metadata
  T5  COMPUTATIONAL COST ...... wall-clock encode/decode scaling
  T6  ADVERSARIAL GAUNTLET .... shared-dim flood, nested overlaps,
                                complement pairs, random write orders

"Independently recoverable" = mutually independent: the readout map
state -> symbol-values is SURJECTIVE onto {0,1}^k (every combination of the
k symbols can actually occur). Overlapping expressions that cannot vary
independently are NOT counted as additional information. This is enforced,
not assumed.

Stdlib + numpy. Plots via matplotlib (Agg).
"""

import math
import random
import time
import numpy as np

RNG = random.Random(20260919)

# --------------------------------------------------------------------------
# Bitmask machinery

def rand_relation(n, rng, max_terms=3):
    """Random relation: 1..max_terms terms, each a dim with 30% negation."""
    k = rng.randint(1, max_terms)
    dims = rng.sample(range(n), k)
    pos = neg = 0
    for d in dims:
        if rng.random() < 0.3:
            neg |= (1 << d)
        else:
            pos |= (1 << d)
    return (pos, neg)


def rel_read(state, pos, neg):
    return ((state & pos) == pos) and ((state & neg) == 0)


def drive(state, pos, neg, target, n):
    """Greedy write: force relation toward target. May clobber other symbols."""
    if target == 1:
        state |= pos
        state &= ~neg
    else:
        if pos:
            state &= ~(pos & -pos)      # clear lowest required-1 bit
        elif neg:
            state |= (neg & -neg)        # set lowest required-0 bit
        # (empty relation is constant-true; excluded from pools)
    return state & ((1 << n) - 1)


def brute_sat(n, symbols):
    """Exact: is there a state satisfying all (pos,neg,target)? Returns a state or None."""
    for s in range(1 << n):
        if all(rel_read(s, p, q) == bool(t) for (p, q, t) in symbols):
            return s
    return None


def max_satisfiable(n, symbols):
    """Exact: max # of symbols simultaneously satisfiable (brute force)."""
    best = 0
    for s in range(1 << n):
        c = sum(1 for (p, q, t) in symbols if rel_read(s, p, q) == bool(t))
        if c > best:
            best = c
            if best == len(symbols):
                break
    return best


def greedy_write(n, symbols, order=None):
    """Sequential greedy writes in `order` (default given). Returns final state
    and per-symbol satisfaction."""
    state = 0
    idx = order if order is not None else list(range(len(symbols)))
    for i in idx:
        p, q, t = symbols[i]
        state = drive(state, p, q, t, n)
    sat = [rel_read(state, p, q) == bool(t) for (p, q, t) in symbols]
    return state, sat


# --------------------------------------------------------------------------
# T1 — independent capacity

def surjective_codes(n, rels):
    """Exact surjectivity check via numpy over all 2^n states.
    Returns #distinct readout patterns for the relation set."""
    states = np.arange(1 << n, dtype=np.int64)
    k = len(rels)
    codes = np.zeros(1 << n, dtype=np.int64)
    for i, (p, q) in enumerate(rels):
        truth = ((states & p) == p) & ((states & q) == 0)
        codes |= truth.astype(np.int64) << i
    return len(np.unique(codes))


def t1_capacity():
    print("\n" + "=" * 70)
    print("  T1 — INDEPENDENT CAPACITY: how many symbols can vary independently?")
    print("=" * 70)
    print("  attack: greedy search for mutually-independent relation sets;")
    print("          200 targeted attempts to build N+1 independent symbols.")
    print("  rule: a set counts only if its readout is SURJECTIVE onto {0,1}^k.")
    rows = []
    for n in (3, 4, 8, 16):
        pool = [rand_relation(n, RNG) for _ in range(80)]
        singletons = [(1 << d, 0) for d in range(n)]
        # tightness: singletons achieve N (must hold)
        assert surjective_codes(n, singletons) == 2 ** n
        # greedy max: random orderings, add while surjective
        best = 0
        tried = 0
        for _ in range(60):
            order = RNG.sample(pool, len(pool))
            s = []
            for r in order:
                tried += 1
                if surjective_codes(n, s + [r]) == 2 ** (len(s) + 1):
                    s.append(r)
                    if len(s) > best:
                        best = len(s)
                        if best > n:
                            break
            if best > n:
                break
        # targeted N+1 attacks
        kills = 0
        for _ in range(200):
            cand = RNG.sample(pool, n + 1)
            if surjective_codes(n, cand) == 2 ** (n + 1):
                kills += 1
        rows.append((n, best, kills, tried))
        print(f"  N={n:>2}: max independent found = {best} (bound {n}) | "
              f"N+1 attacks succeeding = {kills}/200 | candidates tried = {tried}")
    print("  THEOREM (all N, incl. 32/64): readout is a deterministic map from")
    print("  2^N states, so at most 2^N patterns; k independent symbols need")
    print("  2^k patterns -> k <= N. Pigeonhole. No simulation can violate it.")
    print("  VERDICT: HARD BOUND CONFIRMED — PUNIT never exceeds N independent")
    print("  symbols. It ties plain bits at best, never beats them.")
    return rows

# --------------------------------------------------------------------------
# T2 — density -> collision

def t2_density_collision():
    print("\n" + "=" * 70)
    print("  T2 — DENSITY -> COLLISION: K symbols crammed into N=8 dims")
    print("=" * 70)
    print("  attack: random symbols+targets, greedy sequential writes; measure")
    print("  exact SAT rate (brute force), satisfaction after writes, collisions.")
    n = 8
    TRIALS = 120
    ks = (2, 4, 6, 8, 12, 16, 24, 32, 40)
    print(f"  {'K':>3} {'dens':>5} | {'exact SAT%':>9} | {'satisfied%':>10} | {'collision%':>10}")
    curve = []
    for k in ks:
        sat_ct = sat_final = coll = 0
        for _ in range(TRIALS):
            syms = [(p, q, RNG.choice([0, 1]))
                    for (p, q) in (rand_relation(n, RNG) for _ in range(k))]
            if brute_sat(n, syms) is not None:
                sat_ct += 1
            _, ok = greedy_write(n, syms)
            sat_final += sum(ok) / k
            # collision: an earlier symbol that a later write destroyed.
            # measured incrementally:
            state = 0
            alive = [False] * k
            destroyed = 0
            for i, (p, q, t) in enumerate(syms):
                state = drive(state, p, q, t, n)
                for j in range(i):
                    pj, qj, tj = syms[j]
                    now = rel_read(state, pj, qj) == bool(tj)
                    if alive[j] and not now:
                        destroyed += 1
                    alive[j] = now
                alive[i] = rel_read(state, p, q) == bool(t)
            coll += destroyed / k
        row = (k, k / n, sat_ct / TRIALS * 100, sat_final / TRIALS * 100,
               coll / TRIALS * 100)
        curve.append(row)
        print(f"  {k:>3} {k/n:>5.2f} | {row[2]:>9.1f} | {row[3]:>10.1f} | {row[4]:>10.1f}")

    # adversarial variants at K=16
    print("  --- adversarial variants (K=16, N=8) ---")
    K = 16
    # (a) shared-dim flood: 8 need D0=1, 8 need D0=0
    syms_a = []
    for i in range(8):
        d = RNG.choice([d for d in range(1, n)])
        syms_a.append(( (1 << 0) | (1 << d), 0, 1))
    for i in range(8):
        d = RNG.choice([d for d in range(1, n)])
        syms_a.append((1 << d, 1 << 0, 1))          # needs D0=0
    mx = max_satisfiable(n, syms_a)
    print(f"  (a) shared-dim flood (8x D0=1 vs 8x D0=0): max satisfiable = {mx}/16 "
          f"(expect 8: D0 cannot be both)")

    # (b) nested overlaps: A, A&B, A&B&C, ...
    nested = []
    m = 0
    for d in range(n):
        m |= (1 << d)
        nested.append((m, 0, 1))
    # distinct patterns over all states:
    pats = set()
    for s in range(1 << n):
        pats.add(tuple(1 if rel_read(s, p, q) else 0 for (p, q, _) in nested))
    print(f"  (b) nested chain of {n}: {len(nested)} 'symbols' -> {len(pats)} distinct "
          f"patterns = {math.log2(len(pats)):.2f} independent bits, NOT {n}")

    # (c) complement pairs: A&B vs A&~B, etc.
    syms_c = []
    for d in range(0, n, 2):
        e = d + 1
        syms_c.append(((1 << d) | (1 << e), 0, 1))
        syms_c.append(((1 << d), (1 << e), 1))
    mx_c = max_satisfiable(n, syms_c)
    print(f"  (c) {len(syms_c)//2} complement pairs (X&Y vs X&~Y): max satisfiable = "
          f"{mx_c}/{len(syms_c)} (each pair mutually exclusive)")

    # (d) random write-order variance
    var = []
    for _ in range(10):
        syms = [(p, q, RNG.choice([0, 1]))
                for (p, q) in (rand_relation(n, RNG) for _ in range(K))]
        order = RNG.sample(range(K), K)
        _, ok = greedy_write(n, syms, order)
        var.append(sum(ok) / K * 100)
    print(f"  (d) random write orders x10: satisfaction {min(var):.1f}%..{max(var):.1f}% "
          f"(mean {sum(var)/len(var):.1f}%) — order matters, no canonical result")
    print("  VERDICT: collisions grow with density; exact SAT collapses past K=N;")
    print("  adversarial sharing halves capacity; nested 'symbols' are mostly")
    print("  redundant (8 nested -> 3.17 bits). Nothing here beats K dims.")
    return curve

# --------------------------------------------------------------------------
# T3 — noise -> decode error

def t3_noise():
    print("\n" + "=" * 70)
    print("  T3 — NOISE -> DECODE ERROR: per-symbol BER, PUNIT vs conventional")
    print("=" * 70)
    print("  attack: store N symbols (PUNIT: N jointly-SAT relations; conv: N bits),")
    print("  add per-dim Gaussian noise, threshold-decode each symbol.")
    sigmas = (0.0, 0.05, 0.10, 0.15, 0.20, 0.30, 0.40, 0.50)
    TRIALS = 1500
    curves = {}
    for n in (8, 16):
        # find a jointly-SAT relation set (resample count is itself data)
        resamples = 0
        while True:
            syms = [(p, q, RNG.choice([0, 1]))
                    for (p, q) in (rand_relation(n, RNG) for _ in range(n))]
            s0 = brute_sat(n, syms)
            resamples += 1
            if s0 is not None or resamples > 300:
                break
        if s0 is None:
            print(f"  N={n}: could not find SAT set in 300 tries — recorded as failure")
            continue
        print(f"  N={n}: SAT set found after {resamples} tries "
              f"(finding a storable set already costs search)")
        base = [(s0 >> d) & 1 for d in range(n)]          # conventional bits
        b_punit, b_conv = [], []
        for sig in sigmas:
            err_p = err_c = tot = 0
            for _ in range(TRIALS):
                noisy = [((s0 >> d) & 1) + RNG.gauss(0, sig) for d in range(n)]
                thr = [1 if v >= 0.5 else 0 for v in noisy]
                st = sum(v << d for d, v in enumerate(thr))
                for (p, q, t) in syms:
                    if (rel_read(st, p, q) == bool(t)) is False:
                        err_p += 1
                    tot += 1
                for d in range(n):
                    if thr[d] != base[d]:
                        err_c += 1
            b_punit.append(err_p / tot * 100)
            b_conv.append(err_c / tot * 100)
        curves[n] = (list(sigmas), b_punit, b_conv)
        print(f"  N={n}: " +
              " | ".join(f"s={s:.2f}: PUNIT {p:.2f}% / conv {c:.2f}%"
                         for s, p, c in zip(sigmas, b_punit, b_conv)))
    print("  VERDICT: read the numbers — relations compound per-dim noise through")
    print("  min(); expect PUNIT per-symbol BER >= conventional. If PUNIT ever wins")
    print("  here it would be news; if it loses, the 'robust readout' claim from")
    print("  E4 applies only to REDUNDANT single-bit encodings, not to packed sets.")
    return curves


# --------------------------------------------------------------------------
# T4 — full cost accounting (analytic; no simulation needed)

def t4_accounting():
    print("\n" + "=" * 70)
    print("  T4 — FULL COST ACCOUNTING: every bit counted")
    print("=" * 70)
    print("  K independent bits. Conventional: K cells, log2(K) address lines.")
    print("  PUNIT: N=K cells (DPI minimum). Gate pattern = N ternary choices")
    print("  (+/-/absent) = N*log2(3) addr bits presented per read. If gate")
    print("  patterns are STORED (reconfigurable): K patterns x N*log2(3) bits.")
    print("  Structural lock: |legal| relation specs x 2N bits (2 bits/dim).")
    A3 = math.log2(3)
    print(f"  {'K':>5} | {'conv cells':>10} {'conv addr':>9} | "
          f"{'PUNIT cells':>11} {'PUNIT addr':>10} | {'gate store':>10} {'struct lock':>11} | eff.bits/bit (stored-gate)")
    rows = []
    for K in (8, 32, 64, 256):
        conv_addr = math.ceil(math.log2(K))
        punit_addr = math.ceil(K * A3)
        gate_store = K * K * A3
        struct = K * 2 * K            # curated legal set of K relations
        eff = (K + gate_store + struct) / K
        rows.append((K, conv_addr, punit_addr, gate_store, struct, eff))
        print(f"  {K:>5} | {K:>10} {conv_addr:>9} | "
              f"{K:>11} {punit_addr:>10} | {gate_store:>10.0f} {struct:>11.0f} | {eff:>24.1f}x")
    print("  compound-query flip side (analytic): read one 4-way conjunction.")
    print("    PUNIT: 1 address presentation (1.58N bits) + 1 relational read.")
    print("    conv : 4 address presentations + 4 reads + AND in logic.")
    print("  VERDICT: for STORAGE, PUNIT loses by 1-2 orders of magnitude once")
    print("  metadata is counted — and even with presented (unstored) gates its")
    print("  address width (1.58N) dwarfs conventional (log2 N). The ONLY")
    print("  structural win is single-shot compound QUERIES, and only if the")
    print("  physics delivers the relational read for free.")
    return rows


# --------------------------------------------------------------------------
# T5 — computational cost

def t5_compute():
    print("\n" + "=" * 70)
    print("  T5 — COMPUTATIONAL COST: wall-clock encode/decode scaling")
    print("=" * 70)
    print("  (software caveat: a physical PUNIT would read views in parallel;")
    print("   this measures the simulation cost, i.e. what the MODEL pays.)")
    rows = []
    for n in (3, 4, 8, 16, 32, 64):
        syms = [(p, q, RNG.choice([0, 1]))
                for (p, q) in (rand_relation(n, RNG) for _ in range(n))]
        t0 = time.perf_counter()
        for _ in range(20):
            greedy_write(n, syms)
        t_enc = (time.perf_counter() - t0) / 20 * 1000
        # decode: all views if feasible else 200k sampled views
        if n <= 16:
            nviews = 2 ** n - 1
            t0 = time.perf_counter()
            s = 0
            for _ in range(nviews):
                p, q = rand_relation(n, RNG, max_terms=n)
                rel_read(0b1010101010101010 & ((1 << n) - 1), p, q)
            t_dec = (time.perf_counter() - t0) / nviews * 1000
            note = f"{nviews} views"
        else:
            t0 = time.perf_counter()
            for _ in range(200000):
                p, q = rand_relation(n, RNG, max_terms=n)
                rel_read(RNG.getrandbits(n), p, q)
            t_dec = (time.perf_counter() - t0) / 200000 * 1000 * (3 ** n - 1) / 1000
            note = "200k sampled, extrapolated to 3^N-1"
        rows.append((n, t_enc, t_dec, note))
        if n <= 16:
            per_view_us = t_dec * 1000.0
        else:
            per_view_us = t_dec / (3 ** n - 1) * 1e6
        print(f"  N={n:>2}: encode {n} symbols {t_enc:>8.2f} ms | per-view decode "
              f"{per_view_us:>8.3f} us ({note})")
    print("  VERDICT: decode-all-views scales as O(3^N) relation evals — the")
    print("  combinatorial address space is also a combinatorial READ cost in")
    print("  any sequential implementation. Parallel physics is not optional;")
    print("  it is load-bearing for the concept.")
    return rows

# --------------------------------------------------------------------------
# T6 — adversarial gauntlet

def t6_gauntlet():
    print("\n" + "=" * 70)
    print("  T6 — ADVERSARIAL GAUNTLET (N=8, exact ground truth)")
    print("=" * 70)
    n = 8
    # (a) D0 flood: 10 symbols need D0=1, 10 need D0=0 (plus random elsewhere)
    syms_a = []
    for _ in range(10):
        d = RNG.choice([d for d in range(1, n)])
        syms_a.append(((1 << 0) | (1 << d), 0, 1))
    for _ in range(10):
        d = RNG.choice([d for d in range(1, n)])
        syms_a.append(((1 << d), (1 << 0), 1))
    ma = max_satisfiable(n, syms_a)
    print(f"  (a) D0 flood, 10 need D0=1 vs 10 need D0=0: max satisfiable = {ma}/20")

    # (b) complement pairs
    syms_b = []
    for d in range(0, n, 2):
        e = d + 1
        syms_b.append(((1 << d) | (1 << e), 0, 1))
        syms_b.append(((1 << d), (1 << e), 1))
    mb = max_satisfiable(n, syms_b)
    print(f"  (b) 4 complement pairs (X&Y vs X&~Y): max satisfiable = {mb}/{len(syms_b)}")

    # (c) density extreme: K=24 random, greedy vs exact
    syms_c = [(p, q, RNG.choice([0, 1]))
              for (p, q) in (rand_relation(n, RNG) for _ in range(24))]
    _, ok = greedy_write(n, syms_c)
    g = sum(ok)
    mx = max_satisfiable(n, syms_c)
    print(f"  (c) K=24 random: greedy satisfies {g}/24, exact max = {mx}/24 "
          f"(greedy is a lower bound)")

    # (d) sniper: SAT instance where naive greedy fails -> method honesty check
    sniper = [((1 << 0), 0, 1), ((1 << 0) | (1 << 1), 0, 0)]
    _, ok_s = greedy_write(n, sniper)
    mx_s = max_satisfiable(n, sniper)
    print(f"  (d) sniper (A=1, A&B=0): greedy {sum(ok_s)}/2, exact max {mx_s}/2 — "
          f"greedy's bit choice is arbitrary; exact search is ground truth")
    print("  VERDICT: contested dims halve capacity exactly as predicted; no")
    print("  surprises, no rescues. The substrate obeys the counting, always.")


# --------------------------------------------------------------------------
# Plots

def make_plots(t1_rows, t2_curve, t3_curves, t4_rows):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import os
    outdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "plots")
    os.makedirs(outdir, exist_ok=True)

    # p1: N -> independent symbols + address width
    ns = [r[0] for r in t1_rows] + [32, 64]
    fig, ax1 = plt.subplots(figsize=(8, 5))
    ax1.bar([r[0] for r in t1_rows], [r[1] for r in t1_rows], width=1.2,
            color="steelblue", label="max independent symbols (measured)")
    ax1.plot(ns, ns, "k--", label="hard bound k<=N")
    ax1.set_xlabel("physical dimensions N")
    ax1.set_ylabel("independently recoverable symbols")
    ax1.set_title("PUNIT independent capacity: never exceeds N")
    ax2 = ax1.twinx()
    ax2.plot(ns, [x * math.log2(3) for x in ns], "r-o", label="PUNIT addr bits (1.58N)")
    ax2.plot(ns, [math.log2(x) for x in ns], "g-s", label="conventional addr bits (log2 N)")
    ax2.set_ylabel("address bits per read")
    h1, l1 = ax1.get_legend_handles_labels()
    h2, l2 = ax2.get_legend_handles_labels()
    ax1.legend(h1 + h2, l1 + l2, loc="upper left", fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, "p1_capacity.png"), dpi=110)
    plt.close(fig)

    # p2: density -> collision / satisfaction
    dens = [r[1] for r in t2_curve]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(dens, [r[3] for r in t2_curve], "g-o", label="% symbols satisfied (greedy)")
    ax.plot(dens, [r[2] for r in t2_curve], "b-s", label="% exactly satisfiable (brute force)")
    ax.plot(dens, [r[4] for r in t2_curve], "r-^", label="% write collisions")
    ax.axvline(1.0, color="k", linestyle="--", label="density = 1 (K=N)")
    ax.set_xlabel("density K/N (symbols per dimension, N=8)")
    ax.set_ylabel("percent")
    ax.set_title("Density vs collision: packing past K=N collapses")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, "p2_collision.png"), dpi=110)
    plt.close(fig)

    # p3: noise -> BER
    if 8 in t3_curves:
        sig, bp, bc = t3_curves[8]
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.plot(sig, bp, "r-o", label="PUNIT relations BER")
        ax.plot(sig, bc, "g-s", label="conventional bits BER")
        ax.set_xlabel("reader noise sigma")
        ax.set_ylabel("per-symbol bit error rate %")
        ax.set_title("Noise vs decode error (N=8, 8 symbols)")
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(os.path.join(outdir, "p3_noise.png"), dpi=110)
        plt.close(fig)

    # p4: total cost incl metadata
    ks = [r[0] for r in t4_rows]
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(ks, ks, "g-s", label="conventional total bits (=K)")
    ax.plot(ks, [k + r[3] + r[4] for k, r in zip(ks, t4_rows)], "r-o",
            label="PUNIT total bits (cells + stored gates + struct lock)")
    ax.set_xscale("log", base=2)
    ax.set_yscale("log", base=2)
    ax.set_xlabel("K independent bits (log scale)")
    ax.set_ylabel("total bits incl. metadata (log scale)")
    ax.set_title("Total storage cost: PUNIT loses once metadata is counted")
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(os.path.join(outdir, "p4_totalcost.png"), dpi=110)
    plt.close(fig)
    print(f"\n  plots saved to {outdir}/ (p1_capacity, p2_collision, p3_noise, p4_totalcost)")


# --------------------------------------------------------------------------
# main

def main():
    print("PUNIT ADVERSARIAL STRESS TEST — attempting to break the architecture.")
    t1_rows = t1_capacity()
    t2_curve = t2_density_collision()
    t3_curves = t3_noise()
    t4_rows = t4_accounting()
    t5_compute()
    t6_gauntlet()
    make_plots(t1_rows, t2_curve, t3_curves, t4_rows)
    print("\n" + "=" * 70)
    print("  BOTTOM LINE — where the net density advantage dies")
    print("=" * 70)
    print("  It never lives for STORAGE. Counting everything:")
    print("   - independent symbols: hard-capped at N (T1, theorem).")
    print("   - packing past K=N: SAT collapses, collisions climb (T2).")
    print("   - per-symbol noise: relations compound dim noise (T3).")
    print("   - metadata: stored gates cost O(K^2); address width 1.58N vs")
    print("     log2(N) (T4). Effective density < 1 bit per cell, always.")
    print("  What survives, narrowed to its true shape:")
    print("   - ONE substrate, MANY single-shot relational reads (query side).")
    print("   - graceful degradation via overlap redundancy (E4, single-bit).")
    print("   - compound queries (A&B&C&D) in one address+read — IFF the")
    print("     physics delivers relational readout natively. That is now the")
    print("     entire remaining 'massive' claim, and it is a physics claim,")
    print("     not a software claim. Software must compute the relations,")
    print("     which is exactly what conventional storage does.")


if __name__ == "__main__":
    main()
