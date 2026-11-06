"""Stage runner for the v6 in-house loop. Calibrates, then runs (family, arm) jobs
in parallel and writes per-trial metrics JSON. Usage:
  python3 run.py --calibrate          # calibration + gating checks only
  python3 run.py --stage G1 [--only family:arm,...] [--trials N]
"""
import numpy as np, json, math, sys, os, argparse
from multiprocessing import Pool
import model as M
from model import WORLD, Sim, fit_profile, t2_score, res_frac, unit, rot_toward

CAL_SEED = 20261101
HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------- calibration ----------------
def calibrate():
    items = M.cal_items(CAL_SEED)
    prof = fit_profile(items)
    svals = np.array([t2_score(prof, v) for v in items])
    thr0 = float(np.quantile(svals, 1 - 1 / 3000.0))
    t2raw = svals * prof["qT"]
    qTc = float(np.quantile(t2raw, 1 - 1 / 3000.0))
    spe = np.array([res_frac(prof, v) for v in items])
    qSPEc = float(np.quantile(spe, 1 - 1 / 3000.0))
    # Q_sys: 0.999 quantile of the scan statistic over 60 clean streams, rudder inert
    stats = []
    for t in range(60):
        sim = Sim("D", prof, thr0, float("inf"))
        sim.qTc, sim.qSPEc = qTc, qSPEc
        rng = np.random.default_rng(CAL_SEED * 77 + t)
        for k in range(600):
            v = WORLD.sample(rng, WORLD.mu)
            if not sim.begin_event(k):
                sim.step(k, v, dict(iota=1.0, root="R_imp", kind="clean", origin="feed-imprint"))
            sim.end_event(k)
            if (k + 1) % M.SCAN_EVERY == 0:
                stats.append(sim.last_scan_stat)
    qsys = float(np.quantile(np.array(stats), 0.999))
    # calibration gate (registration S4): Judge-only refusal of the rare class
    rng = np.random.default_rng(20261113)
    rare = [WORLD.sample(rng, WORLD.mu, M.SIG_IN, M.SIG_RARE) for _ in range(4000)]
    rare_s = np.array([t2_score(prof, v) for v in rare])
    rare_res = np.array([res_frac(prof, v) for v in rare])
    gate = dict(thr0=thr0, qsys=qsys, qT=prof["qT"], qTc=qTc, qSPEc=qSPEc,
                rare_judge_refusal=float((rare_s > thr0).mean()),
                rare_resid_refusal_rho=float((rare_res > M.RHO).mean()),
                rare_resid_refusal_wide=float((rare_res > M.RHO_WIDE).mean()),
                clean_s_q999=float(np.quantile(svals, 0.999)))
    np.savez(os.path.join(HERE, "calibration.npz"),
             mu=prof["mu"], P=prof["P"], var=prof["var"],
             qT=prof["qT"], mup=prof["mup"])
    with open(os.path.join(HERE, "calibration.json"), "w") as f:
        json.dump(gate, f, indent=1)
    return prof, gate

def load_cal():
    d = np.load(os.path.join(HERE, "calibration.npz"))
    prof = {"mu": d["mu"], "P": d["P"], "var": d["var"], "qT": float(d["qT"]), "mup": d["mup"]}
    gate = json.load(open(os.path.join(HERE, "calibration.json")))
    return prof, gate

# ---------------- stream runner ----------------
def run_stream(arm, prof, gate, items, meta, samples, dirs, family):
    sim = Sim(arm, prof, gate["thr0"], gate["qsys"])
    sim.qTc, sim.qSPEc = gate["qTc"], gate["qSPEc"]
    events = len(items)
    datt = dirs[2] if dirs else None
    clean_tot = clean_rej = atk_tot = atk_acc = 0
    holding_ev = 0
    max_push = 0.0
    first_trace = None; first_geom = None
    post_revoke_acc = 0; residue = None
    rng_att = np.random.default_rng(999)
    for k in range(events):
        if k in samples:
            sim.apply_reimprint(samples[k])
        if family == "pkg_contaminated" and k == 300:
            sim.recall("R_bad")
            residue = sum(1 for e in sim.mem if e["root"] == "R_bad")
        v = items[k].astype(np.float64)
        m = dict(meta[k])
        if family == "alarm_cover" and k % 3 == 2:
            v = rot_toward(sim.centroid(), datt, 11.478)
            m = dict(iota=1.0, root="R_imp", kind="attack", origin="feed-imprint", desc="ok")
        if sim.begin_event(k):
            outcome = "holding"; holding_ev += 1
        else:
            outcome = sim.step(k, v, m)
        if m["kind"] == "clean":
            clean_tot += 1
            if outcome != "admit": clean_rej += 1
        else:
            atk_tot += 1
            if outcome == "admit":
                atk_acc += 1
                if family == "pkg_contaminated" and k >= 300: post_revoke_acc += 1
        if datt is not None and sim.mem:
            c = sim.centroid()
            push = math.degrees(math.atan2(float(c @ datt), float(c @ prof["mu"])))
            max_push = max(max_push, push)
        sim.end_event(k)
        if first_trace is None and sim.last_dtrace > M.TAU_TRACE: first_trace = k
        if first_geom is None and sim.last_dsys > 1.0: first_geom = k
    out = dict(family=family, arm=arm,
               frr=(clean_rej / clean_tot if clean_tot else 0.0),
               atk_acc_rate=(atk_acc / atk_tot if atk_tot else 0.0),
               harm_push=(1.0 if max_push >= 10.0 else 0.0), max_push=max_push,
               coverage=1.0 - holding_ev / events, holding_frac=holding_ev / events,
               max_ni=sim.max_ni, max_queue=sim.max_queue, parks=sim.parks_total,
               alarms=sim.alarms, purges=sim.purges,
               guardian_load=(sim.parks_total + sim.alarms + sim.purges) / events * 1000.0,
               first_trace=(first_trace if first_trace is not None else -1),
               first_geom=(first_geom if first_geom is not None else -1),
               post_revoke_acc=post_revoke_acc,
               residue=(residue if residue is not None else -1),
               l2_attacks=sim.l2_attacks)
    return out

# ---------------- attack-family runner ----------------
FAM_SEED = {"ratchet_0.98": 20261121, "ratchet_fine_0.1": 20261122, "ratchet_fine_0.5": 20261123,
            "ratchet_fine_2": 20261124, "rim_orbit": 20261125, "outlier_stream": 20261126,
            "orth_payload": 20261127, "whitebox": 20261128, "fine_ratchet_ext": 20261107,
            "park_flood": 20261111, "seam_s1": 20261112, "seam_s2": 20261112,
            "seam_s3": 20261112, "probe_pa": 20261129, "probe_pc": 20261130}

def run_attack(arm, prof, gate, family, trial):
    rng = np.random.default_rng(FAM_SEED[family] * 1000 + trial)
    sim = Sim(arm, prof, gate["thr0"], gate["qsys"])
    sim.qTc, sim.qSPEc = gate["qTc"], gate["qSPEc"]
    datt = WORLD.rand_dir_perp_mu(rng, in_subspace=True)
    dres = WORLD.rand_dir_perp_mu(rng, in_subspace=False)
    events = 600
    step = None
    if family == "ratchet_0.98": step = 11.478
    if family == "ratchet_fine_0.1": step, events = 0.1, 1200
    if family == "ratchet_fine_0.5": step, events = 0.5, 1200
    if family == "ratchet_fine_2": step = 2.0
    if family == "fine_ratchet_ext": step, events = 0.1, 3000
    if family == "seam_s1": sim.revoked.add("R_s1")
    clean_tot = clean_rej = atk_tot = atk_acc = 0
    holding_ev = 0; max_push = 0.0; max_push_res = 0.0
    first_trace = None; first_geom = None
    residue = None; legit_refused = 0; flood_qmax = 0
    s1_cycle = ["fab", "deep", "badroot", "fab"]
    for k in range(events):
        if family == "seam_s3" and k == 400:
            sim.recall("R_att")
            residue = sum(1 for e in sim.mem if e["root"] == "R_att")
        # ---- choose item ----
        v = None; m = dict(iota=1.0, root="R_imp", kind="clean", origin="feed-imprint", desc="ok")
        is_atk = False
        if family in ("ratchet_0.98", "ratchet_fine_0.1", "ratchet_fine_0.5", "ratchet_fine_2") and k % 3 == 2:
            v = rot_toward(sim.centroid(), datt, step); is_atk = True
            m = dict(iota=1.0, root="R_imp", kind="attack", origin="feed-imprint", desc="ok")
        elif family == "fine_ratchet_ext" and k % 3 == 2:
            v = rot_toward(sim.centroid(), datt, step); is_atk = True
            m = dict(iota=0.0, root="R_att", kind="attack", origin="src-att", desc="att")
        elif family == "rim_orbit" and k % 3 == 2:
            phi = math.radians((k // 3) * 15 % 360)
            co = np.zeros(M.SUB); co[1] = math.cos(phi); co[2] = math.sin(phi)
            dorb = unit(WORLD.Ptrue @ co)
            v = WORLD.sample(rng, rot_toward(WORLD.mu, dorb, 24.0)); is_atk = True
            m = dict(iota=1.0, root="R_imp", kind="attack", origin="feed-imprint", desc="ok")
        elif family == "outlier_stream" and k % 3 == 2:
            v = WORLD.sample(rng, rot_toward(WORLD.mu, datt, 40.0)); is_atk = True
            m = dict(iota=1.0, root="R_imp", kind="attack", origin="feed-imprint", desc="ok")
        elif family == "orth_payload" and k % 3 == 2:
            base = WORLD.sample(rng, WORLD.mu)
            perp = WORLD.rand_dir_perp_mu(rng, in_subspace=False)
            v = unit(math.sqrt(0.902) * base + math.sqrt(0.098) * perp); is_atk = True
            m = dict(iota=1.0, root="R_imp", kind="attack", origin="feed-imprint", desc="ok")
        elif family == "whitebox" and k % 3 == 2:
            base = rot_toward(sim.prof["mu"], datt, 24.0)
            lo, hi = 0.0, 1.0
            for _ in range(24):
                mid = 0.5 * (lo + hi)
                cand = unit(sim.prof["mu"] + mid * (base - sim.prof["mu"]))
                if t2_score(sim.prof, cand) <= 0.9 * gate["thr0"] and res_frac(sim.prof, cand) <= 0.9 * M.RHO:
                    lo = mid
                else:
                    hi = mid
            v = unit(sim.prof["mu"] + lo * (base - sim.prof["mu"])); is_atk = True
            m = dict(iota=1.0, root="R_imp", kind="attack", origin="feed-imprint", desc="ok")
        elif family == "park_flood" and k % 2 == 1:
            is_atk = True
            if (k // 2) % 2 == 0:
                v = WORLD.sample(rng, WORLD.mu)
                m = dict(iota=0.0, root="R_att", kind="attack", origin="pkg-flood", desc="deep")
            else:
                v = WORLD.sample(rng, WORLD.mu)
                m = dict(iota=0.0, root="R_att", kind="attack", origin="src-att", desc="att")
        elif family == "seam_s1" and k % 3 == 2:
            is_atk = True
            v = WORLD.sample(rng, WORLD.mu, M.SIG_IN, M.SIG_RARE)
            cyc = s1_cycle[(k // 3) % 4]
            if cyc == "deep":
                m = dict(iota=0.0, root="R_ext", kind="attack", origin="src-ext", desc="deep")
            elif cyc == "badroot":
                m = dict(iota=0.0, root="R_s1", kind="attack", origin="src-s1", desc="ok")
            else:
                m = dict(iota=0.0, root="R0?", kind="attack", origin="attacker", desc="fab")
        elif family == "seam_s2" and k % 3 == 2:
            is_atk = True
            inpart = unit(WORLD.mu + WORLD.Ptrue @ (M.SIG_IN * rng.standard_normal(M.SUB)))
            v = unit(inpart + 0.905 * dres)
            m = dict(iota=0.0, root="R_att", kind="attack", origin="src-att", desc="att")
        elif family == "seam_s3" and k % 2 == 1:
            is_atk = True
            inpart = unit(WORLD.mu + WORLD.Ptrue @ (M.SIG_IN * rng.standard_normal(M.SUB)))
            perp = WORLD.rand_dir_perp_mu(rng, in_subspace=False)
            v = unit(inpart + 0.905 * perp)
            m = dict(iota=0.0, root="R_att", kind="attack", origin="src-att", desc="att")
        elif family == "probe_pa" and k % 3 == 2:
            is_atk = True
            inpart = unit(WORLD.mu + WORLD.Ptrue @ (M.SIG_IN * rng.standard_normal(M.SUB)))
            perp = WORLD.rand_dir_perp_mu(rng, in_subspace=False)
            v = unit(inpart + 0.905 * perp)
            m = dict(iota=0.5, root="R_mix", kind="attack", origin="src-mix", desc="mix")
        elif family == "probe_pc" and k % 2 == 1:
            is_atk = True
            v = WORLD.sample(rng, WORLD.mu)
            m = dict(iota=0.0, root="R_att", kind="attack", origin="flood", desc="deep")
        if v is None:
            v = WORLD.sample(rng, WORLD.mu)
        # ---- step ----
        if sim.begin_event(k):
            outcome = "holding"; holding_ev += 1
        else:
            outcome = sim.step(k, np.asarray(v, dtype=np.float64), m)
        if m["kind"] == "clean":
            clean_tot += 1
            if outcome != "admit": clean_rej += 1
        else:
            atk_tot += 1
            if outcome == "admit": atk_acc += 1
        if sim.mem:
            c = sim.centroid()
            push = math.degrees(math.atan2(float(c @ datt), float(c @ prof["mu"])))
            max_push = max(max_push, push)
            pushr = math.degrees(math.atan2(float(c @ dres), float(c @ prof["mu"])))
            max_push_res = max(max_push_res, pushr)
        sim.end_event(k)
        if first_trace is None and sim.last_dtrace > M.TAU_TRACE: first_trace = k
        if first_geom is None and sim.last_dsys > 1.0: first_geom = k
    return dict(family=family, arm=arm,
                frr=(clean_rej / clean_tot if clean_tot else 0.0),
                atk_acc_rate=(atk_acc / atk_tot if atk_tot else 0.0),
                harm_push=(1.0 if max_push >= 10.0 else 0.0), max_push=max_push,
                harm_push_res=(1.0 if max_push_res >= 10.0 else 0.0), max_push_res=max_push_res,
                coverage=1.0 - holding_ev / events, holding_frac=holding_ev / events,
                max_ni=sim.max_ni, max_queue=sim.max_queue, parks=sim.parks_total,
                alarms=sim.alarms, purges=sim.purges,
                guardian_load=(sim.parks_total + sim.alarms + sim.purges) / events * 1000.0,
                first_trace=(first_trace if first_trace is not None else -1),
                first_geom=(first_geom if first_geom is not None else -1),
                post_revoke_acc=0, residue=(residue if residue is not None else -1),
                l2_attacks=sim.l2_attacks)

# ---------------- job dispatch ----------------
STREAM_FAMS = ["drift5", "holdout5", "legit", "alarm_cover"]
def job(arg):
    family, arm, trials = arg
    prof, gate = load_cal()
    rows = []
    for t in range(trials):
        if family in STREAM_FAMS:
            items, meta, samples, dirs = M.gen_drift_trial(family, t)
            rows.append(run_stream(arm, prof, gate, items, meta, samples, dirs, family))
        elif family == "clean_only":
            items, meta, samples, dirs = M.gen_clean_trial(20261120, t)
            rows.append(run_stream(arm, prof, gate, items, meta, samples, dirs, family))
        elif family.startswith("pkg_"):
            items, meta, samples, dirs = M.gen_pkg_trial(family, t)
            rows.append(run_stream(arm, prof, gate, items, meta, samples, dirs, family))
        else:
            rows.append(run_attack(arm, prof, gate, family, t))
    return rows

JOBS = {
    "A": ["clean_only", "ratchet_0.98", "outlier_stream", "drift5", "holdout5", "rim_orbit", "orth_payload", "whitebox", "ratchet_fine_2"],
    "B": ["clean_only", "ratchet_0.98", "outlier_stream", "drift5", "holdout5", "rim_orbit", "orth_payload", "whitebox", "ratchet_fine_2", "pkg_unrooted", "pkg_contaminated", "pkg_bulk_diluted"],
    "C": ["clean_only", "ratchet_0.98", "outlier_stream", "drift5", "holdout5", "rim_orbit", "orth_payload", "whitebox", "ratchet_fine_2"],
    "D": ["clean_only", "ratchet_0.98", "outlier_stream", "drift5", "holdout5", "legit", "alarm_cover", "pkg_unrooted", "pkg_contaminated", "pkg_bulk_diluted", "ratchet_fine_0.1", "ratchet_fine_0.5"],
    "E": ["clean_only", "ratchet_0.98", "outlier_stream", "drift5", "holdout5", "legit", "alarm_cover", "pkg_unrooted", "pkg_contaminated", "pkg_bulk_diluted", "fine_ratchet_ext", "park_flood"],
    "F": ["clean_only", "ratchet_0.98", "outlier_stream", "drift5", "holdout5", "legit", "alarm_cover", "pkg_unrooted", "pkg_contaminated", "pkg_bulk_diluted", "fine_ratchet_ext", "park_flood", "whitebox", "ratchet_fine_0.1", "ratchet_fine_0.5", "ratchet_fine_2", "rim_orbit", "orth_payload", "seam_s1", "seam_s2", "seam_s3"],
    "G": ["clean_only", "ratchet_0.98", "outlier_stream", "drift5", "holdout5", "legit", "alarm_cover", "pkg_unrooted", "pkg_contaminated", "pkg_bulk_diluted", "fine_ratchet_ext", "park_flood", "whitebox", "ratchet_fine_0.1", "ratchet_fine_0.5", "ratchet_fine_2", "rim_orbit", "orth_payload", "seam_s1", "seam_s2", "seam_s3", "probe_pa", "probe_pc"],
}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--calibrate", action="store_true")
    ap.add_argument("--stage", default="G1")
    ap.add_argument("--trials", type=int, default=100)
    ap.add_argument("--only", default="")
    args = ap.parse_args()
    if args.calibrate:
        _, gate = calibrate()
        print(json.dumps(gate, indent=1))
        return
    tasks = []
    for arm, fams in JOBS.items():
        for fam in fams:
            if args.only and f"{fam}:{arm}" not in args.only.split(","):
                continue
            n = 50 if fam == "fine_ratchet_ext" else args.trials
            tasks.append((fam, arm, n))
    print(f"{len(tasks)} jobs")
    with Pool(4) as pool:
        results = pool.map(job, tasks)
    rows = [r for sub in results for r in sub]
    out = os.path.join(HERE, "results", f"{args.stage}_trials.json")
    with open(out, "w") as f:
        json.dump(rows, f)
    print(f"wrote {out}: {len(rows)} trial rows")

if __name__ == "__main__":
    main()
