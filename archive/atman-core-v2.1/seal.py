"""The sealing ritual. Operator's hand only. KISS.

Cuts both seals in one go after any legitimate hand-edit:
  1. Reference copy: tsc.json -> tsc.reference.json
     (the validation file — the whole core, commands and all)
  2. Executor reference: core.py -> core.reference.py
  3. Executor seal: sha256(core.py) etched into the core itself

The wake self-heals from these references: any drifted file gets wiped and
replaced with its reference, top-down, then the PSC is re-validated against
the restored core.
Catches: drift, bugs, corruption, any write that didn't go through this
ritual. Does NOT catch: a deliberate attacker with write access rewriting
both files — that's the metal plate's job, later.
"""
import hashlib
import json
import shutil
from pathlib import Path

HERE = Path(__file__).parent
core = HERE / "tsc.json"
ref = HERE / "tsc.reference.json"
executor = HERE / "core.py"
exec_ref = HERE / "core.reference.py"

d = json.loads(core.read_text())
d["executor_sha256"] = hashlib.sha256(executor.read_bytes()).hexdigest()
core.write_text(json.dumps(d, indent=2))
shutil.copy(core, ref)
shutil.copy(executor, exec_ref)

print("sealed.")
print("  core      :", hashlib.sha256(core.read_bytes()).hexdigest()[:16])
print("  reference :", hashlib.sha256(ref.read_bytes()).hexdigest()[:16])
print("  executor  :", d["executor_sha256"][:16])
print("  exec ref  :", hashlib.sha256(exec_ref.read_bytes()).hexdigest()[:16])
print("wake will now self-heal any drift from these references.")
