#!/usr/bin/env python3
"""
PUNIT overlapping-gate simulator — software testbed for the research hypothesis:

  Can one physical PUNIT expose multiple independently addressable relational
  states through overlapping gated dimensions, allowing several logical symbols
  to share physical structure while remaining uniquely decodable?

Model (faithful to the concept doc):
  - A PUNIT has N continuous dimensions (0..1): the physical substrate.
  - Relations are overlaps: A&B = min(A,B), A&~C = min(A, 1-C), etc.
  - Information lives in the RELATIONSHIPS, not in dedicated locations.
  - PUNIT STATE + GATE PATTERN + CONTEXT -> INTERPRETED INFORMATION.
  - The gate pattern (which relation you read) is the addressing key.

Lock hierarchy (from the doc):
  HARD LOCK       -> relation is immutable core truth; rewrites refused
  STRUCTURAL LOCK -> only legal combinations may be written
  CONTEXT LOCK    -> only the context's relations are addressable right now
  WRITE LOCK      -> controls whether the substrate may change at all
  READ GATE       -> selects which encoded relationship is decoded

Reader noise simulates the physical measurement layer. The crosstalk
experiment varies it to find where decoding breaks — the honest test of
whether overlaps are genuinely distinguishable states or just drawings.

Stdlib only.
"""

import random


class LockViolation(Exception):
    """A lock or gate refused the operation. The substrate is untouched."""


class PUNIT:
    def __init__(self, dims=("A", "B", "C"), noise=0.0, seed=7):
        self.dims = {d: 0.0 for d in dims}
        self.noise = noise
        self.rng = random.Random(seed)
        self.hard = set()       # HARD LOCK: immutable relations
        self.legal = None       # STRUCTURAL LOCK: allowed relation names (None = all)
        self.contexts = {}      # CONTEXT LOCK: context -> addressable relations
        self.context = None
        self.write_open = True  # WRITE LOCK

    # -- substrate ------------------------------------------------------
    def _dim(self, d, neg=False):
        v = self.dims[d]
        return 1.0 - v if neg else v

    # -- READ GATE ------------------------------------------------------
    def relation(self, expr):
        """Decode one relational state: the gate pattern selects the view."""
        if self.context is not None:
            allowed = self.contexts.get(self.context, set())
            if expr not in allowed:
                raise LockViolation(
                    f"CONTEXT LOCK: '{expr}' not addressable in context '{self.context}'")
        val = 1.0
        for term in expr.split("&"):
            term = term.strip()
            neg = term.startswith("~")
            val = min(val, self._dim(term.lstrip("~"), neg))
        if self.noise:  # physical reader imprecision
            val = max(0.0, min(1.0, val + self.rng.gauss(0, self.noise)))
        return round(val, 3)

    # -- encode (drives the shared substrate) ---------------------------
    def encode(self, assignments, relation):
        """Store a symbol by driving dims. Shared dims = shared substrate:
        writing one symbol physically touches every relation using those dims."""
        if not self.write_open:
            raise LockViolation("WRITE LOCK: write gate closed, substrate frozen")
        if relation in self.hard:
            raise LockViolation(f"HARD LOCK: '{relation}' is immutable core truth")
        if self.legal is not None and relation not in self.legal:
            raise LockViolation(f"STRUCTURAL LOCK: '{relation}' is not a legal combination")
        for d, v in assignments.items():
            self.dims[d] = max(0.0, min(1.0, v))
        return dict(self.dims)

    # -- lock administration --------------------------------------------
    def hard_lock(self, relation):
        self.hard.add(relation)

    def set_legal(self, relations):
        self.legal = set(relations)

    def add_context(self, name, relations):
        self.contexts[name] = set(relations)

    def set_context(self, name):
        self.context = name

    def close_write(self):
        self.write_open = False

    def open_write(self):
        self.write_open = True

    # -- introspection ---------------------------------------------------
    def address_space(self):
        """All non-empty relational views of N dims (the combinatorial
        address space — note: addressability, not independent capacity)."""
        dims = list(self.dims)
        views = []
        for r in range(1, len(dims) + 1):
            for combo in _combinations(dims, r):
                views.append("&".join(combo))
        return views


def _combinations(items, r):
    if r == 0:
        yield []
        return
    for i in range(len(items)):
        for rest in _combinations(items[i + 1:], r - 1):
            yield [items[i]] + rest


# --------------------------------------------------------------------------
# The experiment: at what reader noise do overlapping states stop being
# uniquely decodable? Sweeps noise, counts decode errors vs. the noiseless
# ground truth over random substrate states.

def crosstalk_sweep(noise_levels=(0.0, 0.05, 0.10, 0.15, 0.20, 0.30),
                    trials=300, seed=99):
    rng = random.Random(seed)
    dims = ("A", "B", "C")
    results = []
    for noise in noise_levels:
        errors = 0
        for t in range(trials):
            p = PUNIT(dims=dims, noise=0.0, seed=seed + t)
            truth = PUNIT(dims=dims, noise=0.0, seed=seed + t)
            state = {d: rng.choice([0.0, 1.0]) for d in dims}
            for d, v in state.items():
                p.dims[d] = v
                truth.dims[d] = v
            p.noise = noise
            for view in ("A&B", "B&C", "A&C", "A&B&C", "A&~C"):
                clean = truth.relation(view) >= 0.5
                noisy = p.relation(view) >= 0.5
                if clean != noisy:
                    errors += 1
                    break  # one confused view = failed decode of the state
        results.append((noise, errors / trials))
    return results
