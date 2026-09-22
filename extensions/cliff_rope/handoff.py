"""Cliff-rope handoff writer. Peripheral only — never touches TSC/seal."""
from __future__ import annotations
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

HERE = Path(__file__).resolve().parent
DEFAULT_HANDOFF = HERE / "HANDOFF-RESUME.md"
OPENCLAW_HANDOFF = Path.home() / ".openclaw" / "HANDOFF-RESUME.md"

CORE_FORBIDDEN = (
    "tsc.atman.private.json",
    "stage1-seal.json",
    "atman_core.py",
    "gate_policy.json",
    "seal.py",
    "crate.py",
    "wake.py",
)


def write_handoff(
    goal: str,
    status: str,
    next_commands: List[str],
    done: Optional[List[str]] = None,
    blocked: Optional[List[str]] = None,
    do_not: Optional[List[str]] = None,
    verified: Optional[List[str]] = None,
    path: Optional[Path] = None,
) -> Path:
    path = path or DEFAULT_HANDOFF
    path.parent.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S %z")
    do_not = do_not or [
        "Do NOT edit private TSC / seal / atman_core / identity gate_policy",
        "Do NOT reinstall or wipe OpenClaw or ATMAN",
        "Homestead money ops stay stopped until Operator unlocks",
    ]
    lines = [
        "# ATMAN CLIFF-ROPE HANDOFF",
        f"Updated: {ts}",
        "",
        "## Goal",
        goal.strip(),
        "",
        "## Status",
        status.strip(),
        "",
        "## Done",
        *([f"- {x}" for x in (done or [])] or ["- (none)"]),
        "",
        "## Blocked",
        *([f"- {x}" for x in (blocked or [])] or ["- (none)"]),
        "",
        "## Exact next commands",
        *([f"{i}. {c}" for i, c in enumerate(next_commands or ["(none)"], 1)]),
        "",
        "## HARD DO-NOT",
        *[f"- {x}" for x in do_not],
        "",
        "## Last verified",
        *([f"- {x}" for x in (verified or [])] or ["- (none)"]),
        "",
        "## Resume",
        f"Open `{path}` and continue from Exact next commands.",
        "",
    ]
    text = "\n".join(lines)
    path.write_text(text, encoding="utf-8")
    try:
        OPENCLAW_HANDOFF.parent.mkdir(parents=True, exist_ok=True)
        OPENCLAW_HANDOFF.write_text(text, encoding="utf-8")
    except OSError:
        pass
    return path


def is_core_path(p: Path) -> bool:
    name = p.name.lower()
    return name in {x.lower() for x in CORE_FORBIDDEN}
