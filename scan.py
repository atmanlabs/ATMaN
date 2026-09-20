"""Pre-wake scan. The tripwire.

Pure integrity check: live files vs their references, plus the seal
cross-check. Deliberately never imports core.py — the scanner stays
outside the trust boundary of the thing it scans, so even a fully
compromised executor can't lie to it.

Read-only. No healing, no side effects. Run it as often as you like.
Exit 0 = sound. Exit 1 = drift (run wake.py to self-heal).
"""
import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
PAIRS = [
    ("core", HERE / "tsc.json", HERE / "tsc.reference.json"),
    ("executor", HERE / "core.py", HERE / "core.reference.py"),
]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    drift = []
    for name, live, ref in PAIRS:
        if not ref.exists():
            print(f"  [NOREF] {name} — no reference, cut one with seal.py")
            drift.append(name + "-noref")
        elif not live.exists():
            print(f"  [MISSING] {name} — live file gone")
            drift.append(name + "-missing")
        elif sha(live) == sha(ref):
            print(f"  [OK] {name}")
        else:
            print(f"  [DRIFT] {name}")
            drift.append(name)
    try:
        seal = json.loads((HERE / "tsc.json").read_text()
                          ).get("executor_sha256", "")
        if not seal:
            print("  [NOREF] seal — none etched in core")
            drift.append("seal-noref")
        elif seal != sha(HERE / "core.py"):
            print("  [DRIFT] seal — etched hash does not match core.py")
            drift.append("seal")
        else:
            print("  [OK] seal")
    except Exception as e:
        print(f"  [ERROR] could not read core: {e}")
        drift.append("core-unreadable")
    if drift:
        print(f"scan: DRIFT in {', '.join(drift)} — run wake.py to self-heal")
        sys.exit(1)
    print("scan: sound")


if __name__ == "__main__":
    main()
