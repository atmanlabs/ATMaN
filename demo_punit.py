#!/usr/bin/env python3
"""PUNIT demo — run the hypothesis, watch where it holds and where it breaks.

  1. SHARED SUBSTRATE .... two symbols share dimension B, each uniquely
                            decodable through its own gate pattern
  2. CONTRADICTION ........ conflicting assignments corrupt each other —
                            overlaps don't mint capacity; the structural
                            lock exists for exactly this
  3. LOCK HIERARCHY ....... hard / structural / context / write locks refuse
  4. CROSSTALK EXPERIMENT . sweep reader noise -> find where decoding breaks
"""
from punit import PUNIT, LockViolation, crosstalk_sweep


def banner(title):
    print(f"\n{'=' * 70}\n  {title}\n{'=' * 70}")


def main():
    # ------------------------------------------------------------------
    banner("1. SHARED SUBSTRATE — two symbols, one shared dimension")
    p = PUNIT()
    p.encode({"A": 1.0, "B": 1.0}, "A&B")   # symbol X lives in A∩B
    p.encode({"B": 1.0, "C": 1.0}, "B&C")   # symbol Y lives in B∩C (B shared!)
    print("  physical substrate:", p.dims, "<- ONE vector holds BOTH symbols")
    print("  gate A&B  ->", p.relation("A&B"), " (symbol X)")
    print("  gate B&C  ->", p.relation("B&C"), " (symbol Y)")
    print("  gate A&~C ->", p.relation("A&~C"), " (correctly empty — no symbol there)")
    print("  address space:", len(p.address_space()), "relational views from 3 dims")

    # ------------------------------------------------------------------
    banner("2. CONTRADICTION — the honest limit")
    p.encode({"A": 1.0, "C": 0.0}, "A&~C")  # wants C=0 ... but C=1 from symbol Y
    print("  wrote A&~C needing C=0, but substrate had C=1 (symbol Y's doing)")
    print("  gate B&C  ->", p.relation("B&C"), " <- symbol Y DESTROYED by the conflict")
    print("  overlaps share physics: contradictory assignments corrupt each other.")

    # ------------------------------------------------------------------
    banner("3. LOCK HIERARCHY")
    q = PUNIT()
    q.encode({"A": 1.0, "B": 1.0}, "A&B")
    q.hard_lock("A&B")
    try:
        q.encode({"A": 0.0, "B": 0.0}, "A&B")
    except LockViolation as e:
        print("  HARD LOCK      :", e)

    q.set_legal({"A&B", "B&C"})
    try:
        q.encode({"A": 1.0, "C": 1.0}, "A&C")
    except LockViolation as e:
        print("  STRUCTURAL LOCK:", e)

    q.add_context("day", {"A&B"})
    q.add_context("night", {"B&C"})
    q.set_context("day")
    try:
        q.relation("B&C")
    except LockViolation as e:
        print("  CONTEXT LOCK   :", e)
    q.set_context("night")
    print("  context 'night': gate B&C ->", q.relation("B&C"), "(now addressable)")

    q.close_write()
    try:
        q.encode({"C": 1.0}, "B&C")
    except LockViolation as e:
        print("  WRITE LOCK     :", e)

    # ------------------------------------------------------------------
    banner("4. CROSSTALK EXPERIMENT — where does decoding break?")
    print("  noise = reader imprecision. error = a state decoded wrong.")
    for noise, err in crosstalk_sweep():
        bar = "#" * int(err * 40)
        print(f"  noise {noise:.2f}  err {err*100:5.1f}% {bar}")
    print("\n  read it: overlaps stay uniquely decodable while reader noise <<")
    print("  state separation. the gates select cleanly — until physics says no.")

    banner("HYPOTHESIS STATUS")
    print("  CONFIRMED : one substrate, many addressable relational views,")
    print("              gate patterns decode them without confusion.")
    print("  BOUNDED   : contradictory assignments corrupt — capacity is still")
    print("              N dims; the win is associative density, not new bits.")
    print("  NEXT TEST : physical reader resolving A∩B vs A without crosstalk.")


if __name__ == "__main__":
    main()
