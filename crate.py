"""Read-only crate integrity checks. Never imports the reasoning executor."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
CORE_PATH = HERE.parent / 'atman-private' / 'tsc.atman.private.json'
SEAL_PATH = HERE.parent / 'atman-private' / 'stage1-seal.json'
FILES = ('core.py', 'atman_core.py', 'gate_policy.json', 'crate.py', 'wake.py', 'seal.py')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def snapshot(folder=HERE, soul=CORE_PATH):
    return {'version': 1, 'soul_sha256': digest(soul),
            'files': {name: digest(Path(folder) / name) for name in FILES}}


def verify(folder=HERE, soul=CORE_PATH, seal=SEAL_PATH):
    try:
        expected = json.loads(Path(seal).read_bytes())
        return expected == snapshot(folder, soul)
    except (OSError, ValueError, TypeError):
        return False
