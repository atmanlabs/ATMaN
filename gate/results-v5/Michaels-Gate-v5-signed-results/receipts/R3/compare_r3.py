#!/usr/bin/env python3
"""Independent comparison: shipped gen2 originals vs fresh R3 payloads. Prints byte diff, JSON equality minus top-level runtime_s, nested hash checks."""
import hashlib, json, sys
SHIP = "/workspace/michaels-gate-v5-candidate-gen2/reference-model"; FRESH = "/workspace/mg5-repro3/michaels-gate-v5-candidate-gen2/reference-model"
sha = lambda b: hashlib.sha256(b).hexdigest(); ok = True
for f in ("q8F1_results.json", "q8F2_results.json"):
    a = open(f"{SHIP}/artifacts/{f}", "rb").read(); b = open(f"{FRESH}/artifacts/{f}", "rb").read()
    diffpos = [i for i, (x, y) in enumerate(zip(a, b)) if x != y]
    print(f"{f}: shipped {len(a)} B sha256 {sha(a)} | fresh {len(b)} B sha256 {sha(b)}")
    print(f"  byte diff: {len(diffpos)} differing positions in common prefix, length delta {len(b)-len(a)}, first offsets {diffpos[:8]}")
    ja, jb = json.loads(a), json.loads(b)
    print(f"  runtime_s shipped {ja['runtime_s']:.3f}s fresh {jb['runtime_s']:.3f}s")
    da = {k: v for k, v in ja.items() if k != "runtime_s"}; db = {k: v for k, v in jb.items() if k != "runtime_s"}
    eq = da == db; ok &= eq; print(f"  JSON equal except top-level runtime_s: {eq}")
    eqn = ja["frozen"] == jb["frozen"] and ja["impl"] == jb["impl"]; ok &= eqn; print(f"  nested frozen+impl identical: {eqn}")
    reg = "F1_IMPL.json" if "F1" in f else "F2_IMPL.json"
    im = jb["impl"]; bad = [p for p, h in im["impl_sha256"].items() if sha(open(f"{SHIP}/{p}", "rb").read()) != h]
    fz = json.load(open(f"{SHIP}/artifacts/F1_FROZEN.json")); ok &= not bad and jb["frozen"] == fz and im == json.load(open(f"{SHIP}/artifacts/{reg}"))
    print(f"  nested impl_sha256 vs shipped sources: {'all match' if not bad else bad}; embedded frozen == F1_FROZEN.json: {jb['frozen'] == fz}")
    print(f"  acceptance (observed): " + json.dumps({k: v[1] for k, v in jb["acceptance_F_metrics"].items()}))
print("R3 COMPARE:", "PASS" if ok else "FAIL"); sys.exit(0 if ok else 1)
