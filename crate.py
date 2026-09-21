"""Read-only crate integrity checks. Never imports the reasoning executor."""
import hashlib
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
CORE_PATH = Path(os.environ.get('JARVIS_CORE_PATH') or os.environ.get('EXO_CORE_PATH') or (HERE.parent / 'exo-private' / 'tsc.exo.private.json'))
SEAL_PATH = Path(os.environ.get('JARVIS_SEAL_PATH') or os.environ.get('EXO_SEAL_PATH') or (HERE.parent / 'exo-private' / 'stage1-seal.json'))
FILES = ('core.py', 'exo_core.py', 'gate_policy.json', 'crate.py', 'wake.py', 'seal.py')


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
