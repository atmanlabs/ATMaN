#!/usr/bin/env python3
"""reasoning_moves — adjacent moves, always on.

The sim doesn't know what to do to learn yet, so it gets a starter set of small
moves (one step from parroting) applied to EVERY cognition turn via
LocalBrain.think(). Selection starts dumb (round-robin); the meta-move
("did that help?") logs the training signal for smarter selection later.

Moves never touch TSC/PSC and never break a turn: any failure falls back to the
raw reasoning. Only runs on a real backend (Ollama); the simulated stub gains
nothing from a second echo pass. Kill switch: ATMAN_MOVES=0.
"""

import json
import os
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
STATE_PATH = os.path.join(HERE, "moves-state.json")
LOG_PATH = os.path.join(HERE, "moves.jsonl")

MOVES = [
    {
        "name": "restate",
        "instruction": (
            "Restate the reasoning above in your own words, in one or two "
            "sentences. Drop everything that does not matter. If you cannot, "
            "say what blocks you."
        ),
    },
    {
        "name": "sure_vs_guess",
        "instruction": (
            "From the reasoning above, name one thing you are SURE of and one "
            "thing you are GUESSING. Label them exactly SURE: and GUESS:."
        ),
    },
    {
        "name": "change_my_mind",
        "instruction": (
            "Name one specific observation or fact that would make you change "
            "the conclusion in the reasoning above. Be concrete."
        ),
    },
    {
        "name": "connect",
        "instruction": (
            "Connect the reasoning above to one earlier thing from this "
            "conversation or your memories. If nothing genuinely connects, "
            "say so plainly."
        ),
    },
    {
        "name": "unknowns",
        "instruction": (
            "Name one thing you do not know here that you wish you did. "
            "One sentence."
        ),
    },
]

META_INSTRUCTION = (
    "Did that move help your thinking? Answer YES or NO first, "
    "then one short phrase why."
)


def moves_enabled():
    return os.environ.get("ATMAN_MOVES", "1") != "0"


def _load_state():
    try:
        with open(STATE_PATH) as f:
            s = json.load(f)
            return {"next": int(s.get("next", 0)), "applied": int(s.get("applied", 0))}
    except Exception:
        return {"next": 0, "applied": 0}


def _save_state(state):
    tmp = STATE_PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f)
    os.replace(tmp, STATE_PATH)


def _log(entry):
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")


def apply_moves(generate, raw_reasoning, context_hint=""):
    """Run the next rotation move + the meta-move.

    generate: callable(prompt, options) -> text (the backend's generate).
    Returns the log entry dict. Never raises: failures return a skipped entry.
    """
    state = _load_state()
    move = MOVES[state["next"] % len(MOVES)]
    entry = {
        "ts": datetime.now().isoformat(),
        "move": move["name"],
        "context_hint": (context_hint or "")[:200],
        "raw_len": len(raw_reasoning or ""),
        "moved": "",
        "meta": "",
        "status": "ok",
    }
    try:
        move_prompt = (
            "[PRIOR REASONING]\n"
            f"{raw_reasoning}\n\n"
            f"[MOVE: {move['name']}]\n"
            f"{move['instruction']}"
        )
        moved = generate(move_prompt, {"num_predict": 120}) or ""
        entry["moved"] = moved.strip()[:600]

        meta_prompt = (
            f"[MOVE APPLIED: {move['name']}]\n"
            f"Result: {entry['moved']}\n\n"
            f"{META_INSTRUCTION}"
        )
        meta = generate(meta_prompt, {"num_predict": 40}) or ""
        entry["meta"] = meta.strip()[:200]

        state["next"] += 1
        state["applied"] += 1
        _save_state(state)
    except Exception as e:
        entry["status"] = f"skipped: {type(e).__name__}"
    _log(entry)
    return entry


def render_section(entry):
    """Text section appended to the turn's reasoning. Empty when skipped."""
    if entry.get("status") != "ok" or not entry.get("moved"):
        return ""
    return (
        f"\n\n[REASONING MOVE: {entry['move']}]\n"
        f"{entry['moved']}\n"
        f"[META: {entry['meta']}]"
    )
