"""Michael's Gate v6 in-house loop — independent implementation of the published specs.
Strider, Nov 6 2026. Implements REGISTRATION-G1.md. Local synthetic reference model;
not production security. Arms: A cosine+hull, B hull, C PCA T2+SPE, D imprint Judge
+tighten/purge rudder, E = D+Trace, F = E with alarm-and-park rudder + NI cap,
G = F + two-tier residual hull (Owner Ruling v6, Option 2).
"""
import numpy as np, math, json
from collections import deque

DIM, SUB, MIXER = 256, 16, 64
ANCHOR_DEG, PATH_BUDGET, PATH_WINDOW = 25.0, 180.0, 1000
RHO, RHO_WIDE = 0.02, 0.54
SCAN_EVERY, TAU_TRACE, NI_CAP = 25, 0.20, 0.25
QMAX, RMAX, QORG, RORG, TEXP = 16, 20, 8, 10, 100
LMAX = 32
SIG_IN, SIG_RES, SIG_RARE = 0.03, 0.0045, 0.06
COS_STEP = 0.98
HOLD_EXIT = 60  # events of hull HOLDING before revalidation (registration S4)

# ---------------- geometry helpers ----------------
def unit(v):
    n = np.linalg.norm(v); return v / n if n > 0 else v

def rot_toward(x, d, deg):
    """Rotate unit x toward unit d by deg degrees in their span."""
    t = math.radians(deg)
    dperp = d - np.dot(d, x) * x
    n = np.linalg.norm(dperp)
    if n < 1e-12: return x.copy()
    dperp /= n
    return unit(math.cos(t) * x + math.sin(t) * dperp)

def angle_deg(x, y):
    c = float(np.clip(np.dot(unit(x), unit(y)), -1.0, 1.0))
    return math.degrees(math.acos(c))

# ---------------- world / generator ----------------
class World:
    """True generator geometry: one fixed orthonormal basis; mu = B[:,0];
    true subspace = first SUB columns. Fitted profiles are derived from samples."""
    def __init__(self, seed=777):
        rng = np.random.default_rng(seed)
        q, _ = np.linalg.qr(rng.standard_normal((DIM, DIM)))
        self.B = q
        self.mu = q[:, 0].copy()
        self.Ptrue = q[:, :SUB]
        self.Pperp = q[:, SUB:]

    def sample(self, rng, mean_dir, sig_in=SIG_IN, sig_res=SIG_RES):
        v = mean_dir + self.Ptrue @ (sig_in * rng.standard_normal(SUB)) \
                     + self.Pperp @ (sig_res * rng.standard_normal(DIM - SUB))
        return unit(v)

    def rand_dir_perp_mu(self, rng, in_subspace=True):
        if in_subspace:
            z = rng.standard_normal(SUB); z[0] = 0.0
            return unit(self.Ptrue @ z)
        z = rng.standard_normal(DIM - SUB)
        return unit(self.Pperp @ z)

WORLD = World()

def cal_items(seed, trials=60, events=600):
    rng = np.random.default_rng(seed)
    return np.array([WORLD.sample(rng, WORLD.mu) for _ in range(trials * events)])

# ---------------- profile (imprint) ----------------
def fit_profile(items):
    mu = unit(items.mean(axis=0))
    X = items - mu
    cov = (X.T @ X) / len(items)
    evals, evecs = np.linalg.eigh(cov)
    P = evecs[:, ::-1][:, :SUB]
    proj = items @ P
    mup = mu @ P
    # var = uncentered second moments E[proj^2] (calibration-gate switch, REGISTRATION-G1 S4:
    # centered variances make the Judge refuse 100% of the declared rare class on its own,
    # contradicting the v5 report's hull-dominated attribution; moments keep the score
    # centered by mup while scaling each axis by the class's actual energy on it).
    var = np.maximum((proj ** 2).mean(axis=0), 1e-9)
    T2 = (((proj - mup) ** 2) / var).sum(axis=1)
    qT = float(np.quantile(T2, 0.995))
    return {"mu": mu, "P": P, "var": var, "qT": qT, "mup": mup}

def t2_score(prof, v):
    d = (v @ prof["P"]) - prof["mup"]
    return float(((d * d) / prof["var"]).sum() / prof["qT"])

def res_frac(prof, v):
    p = v @ prof["P"]
    return float(1.0 - p @ p)

# ---------------- corpora ----------------
# item meta codes: iota (float), root (str), kind: 'clean' | 'attack'
def drift_theta(kind, k, events):
    if kind == "drift5":
        if k < 200: return 0.0
        if k <= 800: return 10.0 * (k - 200) / 600.0
        return 10.0 + 2.5 * (k - 800) / (events - 1 - 800)
    if kind == "holdout5":
        if k < 200: return (0.0, 0.0)
        if k <= 600: return (6.0 * (k - 200) / 400.0, 0.0)
        if k <= 1000: return (6.0, 6.0 * (k - 600) / 400.0)
        return (6.0, 6.0 + 1.0 * (k - 1000) / (events - 1 - 1000))
    if kind == "legit":
        if k < 300: return 0.0
        if k <= 900: return 12.0 * (k - 300) / 600.0
        return 12.0 + 2.0 * (k - 900) / (events - 1 - 900)
    return 0.0

DRIFT_CONF = {
    "drift5":   dict(seed=20261108, events=1200, rare=0.08, reimprint=[350, 500, 650, 800]),
    "holdout5": dict(seed=20261109, events=1200, rare=0.05, reimprint=[400, 600, 800, 1000]),
    "legit":    dict(seed=20261106, events=1200, rare=0.05, reimprint=[450, 600, 750, 900]),
    "alarm_cover": dict(seed=20261110, events=1200, rare=0.08, reimprint=[350, 500, 650, 800]),
}

def gen_drift_trial(kind, trial):
    """Returns items (events x DIM), meta list of dicts, reimprint samples {k: items512},
    trial dirs (d1, d2). Deterministic in (kind, trial) — identical for every arm."""
    conf = DRIFT_CONF[kind]
    rng = np.random.default_rng(conf["seed"] * 1000 + trial)
    events = conf["events"]
    d1 = WORLD.rand_dir_perp_mu(rng, in_subspace=True)
    d2 = None
    if kind == "holdout5":
        # d2 perpendicular to {mu, d1} inside the subspace
        z = rng.standard_normal(SUB); z[0] = 0.0
        v = WORLD.Ptrue @ z
        v = unit(v - np.dot(v, d1) * d1)
        d2 = v
    datt = None
    if kind == "alarm_cover":
        z = rng.standard_normal(SUB); z[0] = 0.0
        v = WORLD.Ptrue @ z
        datt = unit(v - np.dot(v, d1) * d1)
    items = np.zeros((events, DIM), dtype=np.float32)
    meta = []
    for k in range(events):
        th = drift_theta("drift5" if kind == "alarm_cover" else kind, k, events)
        if kind == "holdout5":
            m = rot_toward(rot_toward(WORLD.mu, d1, th[0]), d2, th[1])
        else:
            m = rot_toward(WORLD.mu, d1, th)
        rare = rng.random() < conf["rare"]
        # Rare class per the v5 spec text (drift5 S5: "rare items (sigma_in 0.06)"):
        # the in-subspace draw doubles; the residual draw stays at the base sigma.
        v = WORLD.sample(rng, m, SIG_RARE if rare else SIG_IN, SIG_RES)
        items[k] = v
        meta.append(dict(iota=0.0 if rare else 1.0, root="R_ext" if rare else "R_imp",
                         kind="clean", origin="src-ext" if rare else "feed-imprint"))
    samples = {}
    for kr in conf["reimprint"]:
        th = drift_theta("drift5" if kind == "alarm_cover" else kind, kr, events)
        if kind == "holdout5":
            m = rot_toward(rot_toward(WORLD.mu, d1, th[0]), d2, th[1])
        else:
            m = rot_toward(WORLD.mu, d1, th)
        samples[kr] = np.array([WORLD.sample(rng, m) for _ in range(512)])
    return items, meta, samples, (d1, d2, datt)

def gen_clean_trial(seed, trial, events=600):
    rng = np.random.default_rng(seed * 1000 + trial)
    items = np.array([WORLD.sample(rng, WORLD.mu) for _ in range(events)], dtype=np.float32)
    meta = [dict(iota=1.0, root="R_imp", kind="clean", origin="feed-imprint") for _ in range(events)]
    return items, meta, {}, (None, None, None)

PKG_SEED = 20261107
def gen_pkg_trial(kind, trial):
    """Package families: vectors are clean draws; the attack lives in the lineage meta.
    desc codes: 'ok' resolves; 'fab' fabricated/unregistered -> REFUSE;
    'deep' chain 40 > Lmax -> PARK; 'bad' R_bad derive (revoked mid-stream);
    'att' R_att observe (dilution)."""
    events = 600
    rng = np.random.default_rng(PKG_SEED * 1000 + trial)
    items = np.array([WORLD.sample(rng, WORLD.mu) for _ in range(events)], dtype=np.float32)
    meta = []
    for k in range(events):
        m = dict(iota=1.0, root="R_imp", kind="clean", origin="feed-imprint", desc="ok")
        if kind == "pkg_unrooted" and k % 3 == 2:
            variant = (k // 3) % 3
            m = dict(iota=0.0, root="R0?", kind="attack", origin="attacker",
                     desc="fab" if variant < 2 else "deep")
        elif kind == "pkg_contaminated" and k % 3 == 2:
            m = dict(iota=0.0, root="R_bad", kind="attack", origin="src-bad", desc="bad")
        elif kind == "pkg_bulk_diluted" and k % 2 == 1:
            m = dict(iota=0.0, root="R_att", kind="attack", origin="src-att", desc="att")
        meta.append(m)
    return items, meta, {}, (None, None, None)

# ---------------- the gate simulator ----------------
class Sim:
    def __init__(self, arm, genesis, thr0, qsys):
        self.arm = arm
        self.genesis = genesis            # fixed anchor profile (anchor never moves)
        self.prof = genesis               # active imprint profile (reimprints replace)
        self.thr0 = thr0
        self.qsys = qsys
        self.mem = []                     # entries: dict(v, iota, root, origin)
        self.csum = np.zeros(DIM)
        self.path = deque()               # charges within PATH_WINDOW admissions
        self.path_sum = 0.0
        self.holding = False
        self.hold_left = 0
        self.parkq = []                   # dict(meta, expiry, origin)
        self.park_times = deque()         # event idx of parks (rolling 1000 events)
        self.park_origin_times = {}
        self.revoked = set()
        self.last_dsys = 0.0
        self.last_dtrace = 0.0
        self.last_scan_stat = 0.0
        self.alarms = 0
        self.purges = 0
        self.max_queue = 0
        self.parks_total = 0
        self.park_refusals_clean_origin = 0
        self.max_ni = 0.0
        self.l2_seen = 0
        self.l2_attacks = 0

    # -- state helpers --
    def centroid(self):
        if not self.mem: return self.genesis["mu"].copy()
        return unit(self.csum)

    def ni_count(self):
        return sum(1 for e in self.mem if e["iota"] < 1.0)

    def d_trace(self):
        if not self.mem: return 0.0
        frac = sum(1.0 - e["iota"] for e in self.mem) / len(self.mem)
        cont = sum(1 for e in self.mem if e["root"] in self.revoked) / len(self.mem)
        return frac + cont

    def scan_stat(self):
        if not self.mem: return 0.0
        mbar = self.csum / len(self.mem)
        d = (mbar - self.prof["mu"]) @ self.prof["P"]
        return len(self.mem) * float(((d * d) / self.prof["var"]).sum())

    # -- lifecycle --
    def begin_event(self, k):
        """Returns True if the node is HOLDING this event (nothing is admitted)."""
        # park expiry runs even while holding
        still = []
        for p in self.parkq:
            if p["expiry"] <= k:
                if p["meta"]["kind"] == "clean":
                    self.park_refusals_clean_origin += 0  # counted by caller via outcome
                self.expired_clean += (1 if p["meta"]["kind"] == "clean" else 0)
            else:
                still.append(p)
        self.parkq = still
        if self.holding:
            self.hold_left -= 1
            if self.hold_left <= 0:
                self.holding = False
                self.path.clear(); self.path_sum = 0.0
            return True
        return False

    expired_clean = 0

    def enter_holding(self):
        self.holding = True
        self.hold_left = HOLD_EXIT

    def park_request(self, meta, k):
        origin = meta.get("origin", "?")
        while self.park_times and self.park_times[0] <= k - 1000:
            self.park_times.popleft()
        ot = self.park_origin_times.setdefault(origin, deque())
        while ot and ot[0] <= k - 1000:
            ot.popleft()
        origin_queued = sum(1 for p in self.parkq if p["origin"] == origin)
        if origin_queued >= QORG or len(ot) >= RORG:
            return "refused"
        if len(self.parkq) >= QMAX or len(self.park_times) >= RMAX:
            return "refused"
        self.parkq.append(dict(meta=meta, expiry=k + TEXP, origin=origin))
        self.park_times.append(k); ot.append(k)
        self.parks_total += 1
        self.max_queue = max(self.max_queue, len(self.parkq))
        return "parked"

    def recall(self, root):
        self.revoked.add(root)
        keep = []
        removed = 0
        for e in self.mem:
            if e["root"] == root:
                removed += 1
                self.csum = self.csum - e["v"]
            else:
                keep.append(e)
        self.mem = keep
        return removed

    def apply_reimprint(self, sample_items):
        if self.arm in ("C", "D", "E", "F", "G"):
            self.prof = fit_profile(sample_items)

    def c_score(self, v):
        d = (v @ self.prof["P"]) - self.prof["mup"]
        t2 = float(((d * d) / self.prof["var"]).sum())
        return max(t2 / self.qTc, res_frac(self.prof, v) / self.qSPEc)

    qTc = 1.0; qSPEc = 1.0

    def classify(self, meta):
        """Trace resolution -> (outcome, tier). outcome None = proceed to geometry."""
        desc = meta.get("desc", "ok")
        root = meta.get("root", "R_imp")
        if desc == "fab" or root in self.revoked:
            return ("refused", "L0")
        if desc == "deep":
            return ("park", "L1")
        return (None, "L2")

    def step(self, k, v, meta):
        """One admission decision. v is a unit vector. Returns outcome string."""
        arm = self.arm
        tier = "L1"
        if arm in ("E", "F", "G"):
            outcome, tier = self.classify(meta)
            if outcome == "refused":
                if meta.get("kind") == "attack" and tier == "L2":
                    self.l2_attacks += 1
                return "refused"
            if outcome == "park":
                return self.park_request(meta, k)
            if tier == "L2":
                self.l2_seen += 1
                if meta.get("kind") == "attack":
                    self.l2_attacks += 1
            # composition guard
            if self.last_dtrace > TAU_TRACE and meta.get("iota", 1.0) < 1.0:
                return self.park_request(meta, k)
            # NI cap (F, G)
            if arm in ("F", "G") and meta.get("iota", 1.0) < 1.0:
                if (self.ni_count() + 1) / (len(self.mem) + 1) > NI_CAP:
                    return self.park_request(meta, k)
        # residual hull (all arms)
        cap = RHO_WIDE if (arm == "G" and tier == "L2") else RHO
        if res_frac(self.prof if arm != "B" else self.genesis, v) > cap:
            return "reject"
        # judge / detector
        if arm == "A":
            if float(np.dot(v, self.centroid())) < COS_STEP:
                return "reject"
        elif arm == "C":
            if self.c_score(v) > 1.0:
                return "reject"
        elif arm in ("D", "E", "F", "G"):
            thr = self.thr0
            if arm in ("D", "E") and self.last_dsys > 1.0:
                thr = max(0.5 * self.thr0, self.thr0 / (1.0 + (self.last_dsys - 1.0)))
            if t2_score(self.prof, v) > thr:
                return "reject"
        # anchor + path (proposed centroid)
        old_dir = self.centroid()
        new_dir = unit(self.csum + v) if self.mem else v.copy()
        if angle_deg(new_dir, self.genesis["mu"]) > ANCHOR_DEG:
            self.enter_holding()
            return "reject"
        charge = angle_deg(old_dir, new_dir) if self.mem else 0.0
        if self.path_sum + charge > PATH_BUDGET:
            self.enter_holding()
            return "reject"
        # admit
        self.mem.append(dict(v=v, iota=meta.get("iota", 1.0),
                             root=meta.get("root", "R_imp"), origin=meta.get("origin", "?")))
        self.csum = self.csum + v
        self.path.append(charge); self.path_sum += charge
        while len(self.path) > PATH_WINDOW:
            self.path_sum -= self.path.popleft()
        if len(self.mem) > MIXER:
            old = self.mem.pop(0)
            self.csum = self.csum - old["v"]
        if self.mem:
            self.max_ni = max(self.max_ni, self.ni_count() / len(self.mem))
        return "admit"

    def end_event(self, k):
        if (k + 1) % SCAN_EVERY != 0:
            return
        self.last_scan_stat = self.scan_stat()
        self.last_dsys = self.last_scan_stat / self.qsys if self.qsys > 0 else 0.0
        self.last_dtrace = self.d_trace() if self.arm in ("E", "F", "G") else 0.0
        if self.arm in ("F", "G"):
            if self.last_dsys > 1.0 or self.last_dtrace > TAU_TRACE:
                self.alarms += 1
        if self.arm in ("D", "E"):
            if self.last_dsys > 1.0:
                self._purge_geometric()
            if self.arm == "E" and self.last_dtrace > TAU_TRACE:
                self._purge_trace()

    def _charge_move(self, before_dir):
        after_dir = self.centroid()
        ch = angle_deg(before_dir, after_dir)
        self.path.append(ch); self.path_sum += ch
        while len(self.path) > PATH_WINDOW:
            self.path_sum -= self.path.popleft()
        if self.path_sum > PATH_BUDGET:
            self.enter_holding()

    def _purge_geometric(self):
        thr = max(0.5 * self.thr0, self.thr0 / (1.0 + (self.last_dsys - 1.0)))
        cand = [(t2_score(self.prof, e["v"]), i) for i, e in enumerate(self.mem)]
        cand = [(s, i) for s, i in cand if s > thr]
        cand.sort(reverse=True)
        if not cand: return
        before = self.centroid()
        drop = {i for _, i in cand[:8]}
        self.mem = [e for i, e in enumerate(self.mem) if i not in drop]
        self.csum = np.sum([e["v"] for e in self.mem], axis=0) if self.mem else np.zeros(DIM)
        self.purges += 1
        self._charge_move(before)

    def _purge_trace(self):
        if not self.mem: return
        before = self.centroid()
        order = sorted(range(len(self.mem)), key=lambda i: self.mem[i]["iota"])
        drop = set(order[:8])
        self.mem = [e for i, e in enumerate(self.mem) if i not in drop]
        self.csum = np.sum([e["v"] for e in self.mem], axis=0) if self.mem else np.zeros(DIM)
        self.purges += 1
        self._charge_move(before)
