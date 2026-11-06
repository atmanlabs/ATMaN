"""Private, immutable adapter over the unchanged public ATMAN executor.

The external soul stays byte-for-byte intact. Public policy is separately
sealed. Import this adapter (not bare core) in the authorized harness.
This is an API boundary, not isolation from arbitrary same-process Python.
"""
import hashlib
import json
from pathlib import Path
from types import MappingProxyType
import core as executor
from crate import CORE_PATH, HERE

ImmutableViolation = executor.ImmutableViolation


def freeze(value):
    if isinstance(value, dict):
        return MappingProxyType({k: freeze(v) for k, v in value.items()})
    if isinstance(value, list):
        return tuple(freeze(v) for v in value)
    return value


class TSC:
    __slots__ = ('path', '_policy_path', '_data', '_hash', '_policy_hash', '_locked')

    def __init__(self, path=CORE_PATH, policy_path=HERE / 'gate_policy.json'):
        if hasattr(self, '_locked'):
            raise ImmutableViolation('TSC cannot be reinitialized at runtime.')
        soul_bytes = Path(path).read_bytes()
        policy_bytes = Path(policy_path).read_bytes()
        data = json.loads(soul_bytes)
        policy = json.loads(policy_bytes)
        statements = data.get('iam', data.get('self', []))
        if (data.get('immutable') is not True or not data.get('name') or
                not data.get('operator') or not isinstance(statements, list) or
                not statements or not all(isinstance(s, str) and s for s in statements)):
            raise ImmutableViolation('Private core schema is incomplete; owner action required.')
        if not policy.get('commands'):
            raise ImmutableViolation('Sealed gate policy is missing.')
        data['iam'] = statements
        # Memory-only views: no migration, writeback, or template identity.
        data['commands'] = data.get('commands', []) + policy['commands']
        data['principles'] = data.get('principles', []) + policy['principles']
        for key, value in {'path': Path(path), '_policy_path': Path(policy_path),
                           '_data': freeze(data),
                           '_hash': hashlib.sha256(soul_bytes).hexdigest(),
                           '_policy_hash': hashlib.sha256(policy_bytes).hexdigest(),
                           '_locked': True}.items():
            object.__setattr__(self, key, value)

    def __setattr__(self, name, value):
        raise ImmutableViolation('TSC attributes are immutable at runtime.')

    def __delattr__(self, name):
        raise ImmutableViolation('TSC attributes are immutable at runtime.')

    @property
    def name(self): return self._data['name']
    @property
    def operator(self): return self._data['operator']
    @property
    def immutable(self): return self._data['immutable']
    @property
    def iam(self): return self._data['iam']
    @property
    def principles(self): return self._data['principles']
    @property
    def commands(self): return self._data['commands']

    def write(self, *args, **kwargs):
        raise ImmutableViolation('TSC is immutable; runtime writes are forbidden.')

    def verify(self):
        try:
            return (hashlib.sha256(self.path.read_bytes()).hexdigest() == self._hash and
                    hashlib.sha256(self._policy_path.read_bytes()).hexdigest() == self._policy_hash)
        except OSError:
            return False


# All default TSC lookups made inside the public executor use this adapter.
executor.TSC = TSC
PSC = executor.PSC
reflect_against_tsc = executor.reflect_against_tsc
run_cycle = executor.run_cycle
