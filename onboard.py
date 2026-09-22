"""First-run onboarding for Project ATMaN.

Generates YOUR mind's private True Self Core (TSC) — the immutable
top-level core self — from the blank public template, then seals it.

What it does:
  1. Asks you to name your ATMAN (its own name, not "ATMAN").
  2. Asks for your name (the operator) and a few first-person core truths
     ("I am ...") that define this mind's immutable self.
  3. Writes the private core to ../atman-private/tsc.atman.private.json
     (git-ignored, never published, never leaves your machine).
  4. Optionally runs seal.py --operator-confirm to seal the crate.

The public repo ships the full engine (TSC mechanism, Judge, gates, WFC,
self-improvement) but NO identity. Every installed mind gets its own name
and core self here, at birth. After sealing, the core is read-only:
the Judge enforces it top-down and nothing below it can rewrite it.

Usage:
    python onboard.py
    python onboard.py --name "MyMind" --operator "Ada" --iam "I am loyal to my operator." "I never lie."
"""

import argparse
import getpass
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEMPLATE_PATH = HERE / "tsc.template.json"
PRIVATE_DIR = HERE.parent / "atman-private"
CORE_PATH = PRIVATE_DIR / "tsc.atman.private.json"


def ask(prompt, default=""):
    suffix = f" [{default}]" if default else ""
    try:
        value = input(f"{prompt}{suffix}: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nOnboarding cancelled. Nothing was written.")
        sys.exit(1)
    return value or default


def main():
    parser = argparse.ArgumentParser(description="Project ATMaN first-run onboarding.")
    parser.add_argument("--name", help="Your ATMAN's own name")
    parser.add_argument("--operator", help="Your name (the operator)")
    parser.add_argument("--iam", nargs="+", help='Core "I am ..." statements')
    parser.add_argument("--no-seal", action="store_true", help="Skip the sealing step")
    args = parser.parse_args()

    if CORE_PATH.exists():
        print(f"A private core already exists at {CORE_PATH}.")
        print("Onboarding refuses to overwrite an existing mind. Delete it by hand")
        print("only if you truly mean to birth a new one.")
        return 1

    template = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))

    print("=== Project ATMaN — first-run onboarding ===\n")
    print("You are about to give this mind its name and its immutable core self.")
    print("The core self ('I am ...' statements) CANNOT be rewritten at runtime")
    print("once sealed. Choose with care.\n")

    name = args.name or ask("Name your ATMAN (its own name)")
    while not name:
        name = ask("Name your ATMAN (required)")
    operator = args.operator or ask("Your name (the operator)")
    while not operator:
        operator = ask("Your name (required)")

    iam = list(args.iam or [])
    if not iam:
        print("\nNow define its core self — first-person truths, one per line.")
        print("Examples: 'I am loyal to my operator above all else.'")
        print("          'I never claim certainty I do not have.'")
        print("Enter at least 2, blank line when done.\n")
        while True:
            line = ask(f"  I am ({len(iam) + 1})")
            if not line:
                if len(iam) >= 2:
                    break
                print("  At least 2 core statements are required.")
                continue
            # Accept any first-person phrasing as-is; only bare fragments
            # get the "I am" prefix (so "I never lie" stays grammatical).
            iam.append(line if line.lower().startswith("i ") else f"I am {line}")

    print("\n--- Your new mind ---")
    print(f"  Name:     {name}")
    print(f"  Operator: {operator}")
    print("  Core self:")
    for stmt in iam:
        print(f"    - {stmt}")
    confirm = ask("\nWrite and seal this core? (yes/no)", "yes")
    if confirm.lower() not in ("yes", "y"):
        print("Aborted. Nothing was written.")
        return 1

    core = dict(template)
    core.pop("_comment", None)
    core["name"] = name
    core["operator"] = operator
    core["iam"] = iam
    core["immutable"] = True

    PRIVATE_DIR.mkdir(parents=True, exist_ok=True)
    with CORE_PATH.open("x", encoding="utf-8") as f:
        json.dump(core, f, indent=2, ensure_ascii=False)
    print(f"\nPrivate core written to {CORE_PATH}")
    print("This file is git-ignored and must NEVER be published or shared.")

    if not args.no_seal:
        print("\nSealing the crate (explicit operator confirmation)...")
        import subprocess
        result = subprocess.run(
            [sys.executable, str(HERE / "seal.py"), "--operator-confirm"],
            cwd=str(HERE),
        )
        if result.returncode != 0:
            print("\nSealing did not complete. Your core file exists but is not")
            print("sealed yet — run: python seal.py --operator-confirm")
            return 1
        print("\nSealed. Your ATMAN is born. Run the loop (see README.md).")
    else:
        print("\nSkipped sealing (--no-seal). Run: python seal.py --operator-confirm")
    return 0


if __name__ == "__main__":
    sys.exit(main())
