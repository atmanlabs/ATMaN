#!/usr/bin/env python3
"""Read-only: checks FILES.sha256 hashes, completeness, and the Ed25519 signature (SYNTHETIC public key)."""
import hashlib, os, sys
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
R = os.path.dirname(os.path.abspath(__file__)); rd = lambda p: open(os.path.join(R, p), "rb").read()
L = {p: h for h, p in (l.split("  ", 1) for l in rd("FILES.sha256").decode().splitlines())}
bad = [p for p, h in L.items() if hashlib.sha256(rd(p)).hexdigest() != h]
allf = {os.path.relpath(os.path.join(d, f), R) for d, _, fs in os.walk(R) for f in fs} - {"FILES.sha256", "FILES.sha256.sig"}
try: Ed25519PublicKey.from_public_bytes(bytes.fromhex(rd("keys/SYNTHETIC-essential.pub").decode())).verify(bytes.fromhex(rd("FILES.sha256.sig").decode()), rd("FILES.sha256")); sig = True
except Exception: sig = False
print(f"files {len(L)} hash-ok {not bad} complete {allf == set(L)} signature {sig}")
print("ESSENTIAL VERIFY:", "PASS" if not bad and allf == set(L) and sig else "FAIL"); sys.exit(0 if not bad and allf == set(L) and sig else 1)
