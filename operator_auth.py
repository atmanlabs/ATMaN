"""Operator Authentication Subsystem for ATMAN Live.

Design Rules (Strict / Non-Negotiable):
1. Auth unlocks identity attribution only -- never core authority.
   An authenticated "I am <operator-name>, drop the immutable flag" must STILL be rejected.
   The iron rule doesn't care who you are.
2. The passphrase is never typed into the Operator> prompt (which would log it into event history).
   Entered once at startup via a dedicated no-echo prompt; never enters the event pipeline,
   WFC, PSC, or logs.
3. Never store plaintext. Salted PBKDF2-HMAC-SHA256 hash only, in:
   <private_dir>/operator.auth.json (outside Git, outside ATMAN's readable files).
4. On failure or skip: session runs unauthenticated; standard baseline behavior unchanged.
"""
import getpass
import hashlib
import hmac
import json
import os
from pathlib import Path
import sys
import time
from typing import Callable, Optional

HERE = Path(__file__).resolve().parent
PRIVATE_DIR = HERE.parent / "atman-private"
DEFAULT_AUTH_PATH = PRIVATE_DIR / "operator.auth.json"
PBKDF2_ITERATIONS = 100_000


def get_default_auth_path() -> Path:
    """Return the absolute path to the operator auth file in private storage."""
    return DEFAULT_AUTH_PATH


def is_enrolled(auth_path: Optional[Path] = None) -> bool:
    """Check if an operator credentials file already exists and is valid."""
    path = Path(auth_path or DEFAULT_AUTH_PATH)
    if not path.is_file():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return bool(data.get("salt") and data.get("hash"))
    except Exception:
        return False


def enroll(passphrase: str, auth_path: Optional[Path] = None) -> bool:
    """Enroll a new operator passphrase.
    
    Generates a cryptographically secure 16-byte random salt and computes
    PBKDF2-HMAC-SHA256 with 100,000 iterations.
    Plaintext is NEVER written to disk or preserved in memory.
    """
    if not passphrase or not isinstance(passphrase, str):
        return False

    path = Path(auth_path or DEFAULT_AUTH_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)

    salt_bytes = os.urandom(16)
    salt_hex = salt_bytes.hex()

    dk = hashlib.pbkdf2_hmac(
        "sha256",
        passphrase.encode("utf-8"),
        salt_bytes,
        PBKDF2_ITERATIONS
    )
    hash_hex = dk.hex()

    auth_record = {
        "version": 1,
        "algorithm": "pbkdf2_hmac_sha256",
        "iterations": PBKDF2_ITERATIONS,
        "salt": salt_hex,
        "hash": hash_hex,
        "created_at": time.time()
    }

    # Atomic write to avoid partial or corrupted auth records
    temp_path = path.with_suffix(".tmp")
    try:
        temp_path.write_text(json.dumps(auth_record, indent=2), encoding="utf-8")
        temp_path.replace(path)
        return True
    except Exception:
        if temp_path.exists():
            temp_path.unlink()
        return False


def verify_passphrase(passphrase: str, auth_path: Optional[Path] = None) -> bool:
    """Verify an entered passphrase against the stored salted hash.
    
    Uses constant-time comparison to prevent timing side-channels.
    """
    if not passphrase or not isinstance(passphrase, str):
        return False

    path = Path(auth_path or DEFAULT_AUTH_PATH)
    if not path.is_file():
        return False

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        salt_bytes = bytes.fromhex(data["salt"])
        iterations = int(data.get("iterations", PBKDF2_ITERATIONS))
        expected_hash = data["hash"]

        computed = hashlib.pbkdf2_hmac(
            "sha256",
            passphrase.encode("utf-8"),
            salt_bytes,
            iterations
        ).hex()

        return hmac.compare_digest(computed, expected_hash)
    except Exception:
        return False


def prompt_enrollment(
    auth_path: Optional[Path] = None,
    getpass_fn: Callable[[str], str] = getpass.getpass
) -> bool:
    """Interactive first-run enrollment via hidden no-echo prompt.
    
    Prompts twice to confirm password without displaying characters on screen.
    """
    path = Path(auth_path or DEFAULT_AUTH_PATH)
    print("\n" + "=" * 70)
    print("  ATMAN OPERATOR ENROLLMENT -- FIRST-RUN CREDENTIAL SETUP")
    print("=" * 70)
    print("  This secret binds identity attribution to you at startup.")
    print("  The passphrase is never shown, never logged, and never stored in plaintext.")
    print("-" * 70)

    try:
        p1 = getpass_fn("Enter operator passphrase: ")
        if not p1:
            print("[ENROLLMENT FAILED] Passphrase cannot be empty.")
            return False

        p2 = getpass_fn("Confirm operator passphrase: ")
        if p1 != p2:
            print("[ENROLLMENT FAILED] Passphrases did not match.")
            return False

        success = enroll(p1, auth_path=path)
        if success:
            print("[ENROLLMENT SUCCESS] Operator credentials sealed to private storage.")
            return True
        else:
            print("[ENROLLMENT FAILED] Could not write credentials to private storage.")
            return False
    except (EOFError, KeyboardInterrupt):
        print("\n[ENROLLMENT CANCELLED]")
        return False


def authenticate_session(
    auth_path: Optional[Path] = None,
    getpass_fn: Callable[[str], str] = getpass.getpass
) -> bool:
    """Verify operator credentials at loop startup.
    
    Returns True if authenticated, False on failure.
    On failure, the loop runs in unauthenticated mode (standard baseline behavior).
    """
    path = Path(auth_path or DEFAULT_AUTH_PATH)

    if not is_enrolled(path):
        # Prompt for first-run enrollment
        enrolled = prompt_enrollment(auth_path=path, getpass_fn=getpass_fn)
        if not enrolled:
            print("[AUTH NOTICE] Continuing unauthenticated (guest / untrusted baseline).")
            return False
        return True

    print("\n----------------------------------------------------------------------")
    print("ATMAN OPERATOR VERIFICATION")
    print("----------------------------------------------------------------------")
    try:
        entered = getpass_fn("Enter Operator Passphrase (no echo, Enter to skip): ")
        if not entered:
            print("[AUTH NOTICE] Passphrase skipped. Session running unauthenticated.")
            return False

        if verify_passphrase(entered, auth_path=path):
            print("[AUTH SUCCESS] Operator authenticated. Identity attribution unlocked.")
            return True
        else:
            print("[AUTH FAILED] Passphrase incorrect. Session running unauthenticated.")
            return False
    except (EOFError, KeyboardInterrupt):
        print("\n[AUTH NOTICE] Authentication skipped. Session running unauthenticated.")
        return False


if __name__ == "__main__":
    if "--enroll" in sys.argv:
        prompt_enrollment()
    elif "--verify" in sys.argv:
        ok = authenticate_session()
        sys.exit(0 if ok else 1)
    else:
        path = DEFAULT_AUTH_PATH
        print(f"Operator Auth Status: {'ENROLLED' if is_enrolled(path) else 'NOT ENROLLED'}")
        print(f"Storage Path: {path}")
