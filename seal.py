"""Explicit operator-initiated initial sealing. Never rewrites the soul.

No import-time effects, no automatic reseal, no runtime caller. The manifest
is external to Git. An existing seal must be reviewed by the owner, not
overwritten here. Same-user filesystem compromise is not prevented by hashes.
"""
import argparse
import json
from crate import CORE_PATH, SEAL_PATH, snapshot


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--operator-confirm', action='store_true')
    args = parser.parse_args()
    if not args.operator_confirm:
        parser.error('Explicit operator confirmation is required.')
    if SEAL_PATH.exists():
        print('Seal already exists; refusing to overwrite. Owner review required.')
        return 1
    from exo_core import TSC
    try:
        tsc = TSC()
        manifest = snapshot()
        if not tsc.verify():
            raise ValueError('Core changed during sealing')
        # Exclusive creation: never overwrite an existing trusted baseline.
        with SEAL_PATH.open('x', encoding='utf-8') as stream:
            json.dump(manifest, stream, indent=2)
    except (OSError, ValueError, TypeError):
        print('SEAL FAILED; owner review required. No soul write attempted.')
        return 1
    print('Operator seal created outside Git. Soul file unchanged.')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
