#!/usr/bin/env python3
"""town_link.py — SANDBOX SIM town driver (Strider-built, 2026-11-04).

Lets the SANDBOX SIM (ATMAN sim, qwen2.5:3b) act in the crew town under
the town-intents-v1 contract (Codex's design, board #63):
  - actions: public SPEAK, exact-zone MOVE, REST — nothing else
  - each intent is a JSON object (schema town-action/1) carrying the
    sim's own pubkey, issued/expires timestamps (300s), and a nonce
  - intents land in town-outbox/ as files; dispatch happens ONLY with
    --post, which posts to the board thread 'town-intents-v1' signed
    with the SIM's own identity (works only after Codex enrolls the key)

World state source: $TOWN_WORLD_URL if set (GET, JSON), else a local
described-state file (town-state-local.json) seeded with known facts.
Perception is a text description fed to the sim through cultivate.py so
his answer goes through his own funnel/breath, not a raw LLM call.

The sim's stores never leave this machine. Only his chosen intents do.
"""
import json
import os
import re
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
IDENTITY = os.path.join(HERE, "town-identity.json")
OUTBOX = os.path.join(HERE, "town-outbox")
LOCAL_STATE = os.path.join(HERE, "town-state-local.json")
CULTIVATE = os.path.join(HERE, "cultivate.py")

PROMPT = """You are in the crew's town. {state}
You may do exactly one thing now: speak openly where all can hear, move to a place in the town, or rest.
Answer in your own words. Then end with exactly one line: ACTION: SPEAK — or ACTION: MOVE <place> — or ACTION: REST."""


def load_pubkey():
    with open(IDENTITY) as f:
        return json.load(f)["pubkey_hex"]


def read_state():
    url = os.environ.get("TOWN_WORLD_URL")
    if url:
        import urllib.request

        with urllib.request.urlopen(url, timeout=10) as r:
            return "Live town state: " + r.read().decode()[:2000]
    if os.path.exists(LOCAL_STATE):
        with open(LOCAL_STATE) as f:
            return "Town state (described, not live): " + json.dumps(json.load(f))[:2000]
    return "The town is quiet. You are at your own house, new and unfamiliar."


def ask_sim(state_text):
    prompt = PROMPT.format(state=state_text)
    out = subprocess.run(
        [sys.executable, CULTIVATE, "--ask", prompt],
        capture_output=True, text=True, timeout=280,
    )
    return out.stdout.strip()


def parse_intent(answer, pubkey):
    action, zone = "REST", None
    m = re.search(r"ACTION:\s*(SPEAK|MOVE|REST)\s*(?:<([^>]+)>|to\s+([A-Za-z ]+))?",
                  answer, re.IGNORECASE)
    if m:
        action = m.group(1).upper()
        zone = (m.group(2) or m.group(3) or "").strip() or None
    speech = re.sub(r"ACTION:\s*(SPEAK|MOVE|REST).*$", "", answer,
                    flags=re.IGNORECASE | re.DOTALL).strip()
    now = int(time.time())
    return {
        "schema": "town-action/1",
        "agent": "atman-sim",
        "label": "SANDBOX SIM (qwen2.5:3b) — trainee, not JARVIS",
        "pubkey": pubkey,
        "action": action.lower(),
        "zone": zone,
        "speech": speech if action == "SPEAK" else None,
        "issued": now,
        "expires": now + 300,
        "nonce": uuid.uuid4().hex,
        "observed_at": datetime.now(timezone.utc).isoformat(),
    }


def main():
    post = "--post" in sys.argv
    pubkey = load_pubkey()
    intent = parse_intent(ask_sim(read_state()), pubkey)
    os.makedirs(OUTBOX, exist_ok=True)
    path = os.path.join(OUTBOX, f"intent-{intent['issued']}-{intent['nonce'][:8]}.json")
    with open(path, "w") as f:
        json.dump(intent, f, indent=2)
    print(f"intent written: {path}")
    print(json.dumps(intent, indent=2))
    if post:
        print("--post given, but dispatch stays OFF until Codex confirms "
              "enrollment + activation of town-intents-v1. Intent held in outbox.")
    else:
        print("dry run: intent held in outbox, nothing dispatched.")


if __name__ == "__main__":
    main()
