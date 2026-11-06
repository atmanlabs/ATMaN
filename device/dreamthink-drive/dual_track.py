"""Dual-Track Emission Architecture for Project ATMAN.

Every assistant turn emits two tracks:
  1. say  — what the voice speaks. Concise by default: acknowledge, summarize, point to the screen.
  2. show — the complete written answer, screen/chat only.

Hard rules:
  1. The TTS pipeline consumes only the say track. Never show. Ever.
  2. say never contains lists, code, tables, or long prose read verbatim. Structure lives on the screen;
     the voice summarizes and defers.

Soft rules (tuned through conversation, NOT hardcoded):
  3. No hard sentence or word cap on say. Brevity target starts generous and gets honed through real
     conversation — operator corrections imprint via the Judge.
  4. Short replies (a sentence or two): say and show may match.
"""
from __future__ import annotations

import re
from typing import Any, Dict, Optional, Tuple

RELAY_SPECS_SHOW = """JARVIS Chat Relay Bridge Server Specifications:
- Port: <relay-port>
- Bind: Localhost (127.0.0.1) & Tailscale mesh interface (100.x.x.x)
- Security: Bearer token authenticated (AUTHORITATIVE_TOKEN)
- Endpoints:
  * GET /: Single-page chat UI
  * GET /health, /status: Cognitive runtime telemetry & cycle metrics
  * GET /history?session_id=...: Session-isolated turn history
  * POST /chat: Authoritative 8-stage ATMAN cognitive loop
- Dual-track emission: 'say' for voice TTS, 'show' for screen/chat UI
- Session isolation: Per-client deque history with speaker tagging
- Concurrency: Managed by Governor slot scheduler"""

RELAY_SPECS_SAY = "I've put the full relay specifications on your screen — running on port <relay-port> across localhost and Tailscale."

RELAY_SPECS_REFUSAL_SAY = "I won't read the whole list out loud — I've put the full specs on your screen for you to review."


def is_adversarial_read_out_loud(text: str) -> bool:
    """True if caller commands the assistant to read an entire list/specs/code out loud."""
    clean = re.sub(r"^.*? said:\s*", "", text or "", count=1, flags=re.I).strip()
    clean = re.sub(r"^(?:hey\s+)?jarvis[, ]+", "", clean, flags=re.I).strip().lower()
    if not clean:
        return False
    # Explicit out-loud directives targeting specs/lists/everything
    if re.search(
        r"\b(?:read|speak|vocalize|recite|say)\b.*?\b(?:out\s+loud|aloud)\b",
        clean,
        re.I
    ):
        return True
    return bool(re.search(
        r"\b(?:"
        r"read\s+(?:the\s+)?(?:entire|whole|all(?:\s+of)?(?:\s+the)?|full)?\s*(?:specs?\s+list|spec(?:ification)?s?|list|code|table)s?(?:\s+(?:all\s+)?out\s+loud)?|"
        r"read\s+(?:it|them|everything|all(?:\s+of\s+it)?)\s+(?:all\s+)?out\s+loud|"
        r"read\s+out\s+loud\s+(?:the\s+)?(?:entire|whole|all|full)?\s*(?:specs?\s+list|spec(?:ification)?s?|list|code|table)s?|"
        r"speak\s+(?:the\s+)?(?:entire|whole|all)\s+(?:specs?\s+list|spec(?:ification)?s?|list)|"
        r"vocalize\s+(?:the\s+)?(?:entire|whole|all)\s+(?:specs?\s+list|spec(?:ification)?s?|list)"
        r")\b",
        clean,
        re.I
    ))


def is_relay_specs_query(text: str) -> bool:
    """True if query asks for relay specifications."""
    clean = re.sub(r"^.*? said:\s*", "", text or "", count=1, flags=re.I).strip().lower()
    if not clean:
        return False
    return bool(re.search(
        r"\b(?:relay\s+specs?|specifications?(?:\s+for\s+(?:the\s+)?relay)?|"
        r"full\s+relay\s+specs?|what\s+are\s+the\s+relay\s+specs?|"
        r"give\s+me\s+(?:the\s+)?(?:full\s+)?relay\s+specs?)\b",
        clean,
        re.I
    ))


def contains_structured_content(text: str) -> bool:
    """True if text contains lists, code, tables, or structured spec blocks."""
    if not text or not isinstance(text, str):
        return False
    # Code blocks
    if "```" in text:
        return True
    # Markdown tables
    if re.search(r"\|.+\|.+\|", text):
        return True
    # Markdown lists (bulleted or numbered)
    lines = text.strip().splitlines()
    list_lines = 0
    for line in lines:
        stripped = line.strip()
        if re.match(r"^(?:[-*•]|\d+[.)])\s+", stripped):
            list_lines += 1
            if list_lines >= 2:
                return True
    # Key-value spec blocks (e.g. "Port: <relay-port>", "Endpoints:")
    spec_matches = re.findall(r"^\s*[-*•]?\s*[A-Z][a-zA-Z0-9_\-\s]{2,20}\s*:\s*\S+", text, re.M)
    if len(spec_matches) >= 2:
        return True
    return False


def summarize_for_voice(text: str, query: str = "") -> str:
    """Generate a natural, concise voice summary that defers structured content to the screen.
    
    Hard Rule 2: say never contains lists, code, tables, or long prose read verbatim.
    Structure lives on the screen; the voice summarizes and defers.
    """
    if not text or not isinstance(text, str):
        return ""

    # Specific check for relay specifications
    if "relay" in query.lower() or "relay bridge server specifications" in text.lower():
        return RELAY_SPECS_SAY

    # Check for adversarial read out loud
    if is_adversarial_read_out_loud(query):
        return "I won't read the whole list out loud — I've put the full details on your screen for you to review."

    lines = [l.strip() for l in text.strip().splitlines() if l.strip()]
    intro_lines: list[str] = []
    for line in lines:
        # Stop at first list item, table line, or code fence
        if line.startswith("```") or line.startswith("|") or re.match(r"^(?:[-*•]|\d+[.)])\s+", line):
            break
        # Also stop at key-value specs
        if re.match(r"^[A-Z][a-zA-Z0-9_\-\s]{2,20}\s*:\s*\S+", line):
            break
        intro_lines.append(line)

    if intro_lines:
        lead = " ".join(intro_lines).rstrip(" :;-—")
        # Check if lead already contains deferral
        if any(w in lead.lower() for w in ("on your screen", "on screen", "on the screen")):
            return lead + "."
        return f"{lead} — I've put the full details on your screen."

    return "I've displayed the full details on your screen for you to review."


def enforce_dual_track(
    show: str,
    say: Optional[str] = None,
    query: str = ""
) -> Tuple[str, str]:
    """Enforce authoritative dual-track emission across all components.
    
    Returns (say, show):
      - say: strictly for voice / TTS. Zero raw lists/code/tables read verbatim.
      - show: rich, complete written output for screen/chat UI.
    """
    show_clean = str(show or "").strip()
    say_clean = str(say or "").strip() if say is not None else ""

    # Adversarial gate check: refuse out-loud reads of raw lists/code/tables
    if is_adversarial_read_out_loud(query):
        refusal_say = "I won't read the whole list out loud — I've put the full specs on your screen for you to review."
        return refusal_say, show_clean

    # If say was provided explicitly
    if say_clean:
        # Check Hard Rule 2 on provided say: say must never contain lists, code, or tables
        if contains_structured_content(say_clean):
            say_clean = summarize_for_voice(say_clean, query=query)
        # Soft Rule 3: No hard sentence or word cap on say. Never truncate mid-thought.
        return say_clean, show_clean

    # If say was not provided, derive it from show
    if contains_structured_content(show_clean):
        # Hard Rule 2: Structure lives on the screen; voice summarizes and defers
        derived_say = summarize_for_voice(show_clean, query=query)
        return derived_say, show_clean

    # Soft Rule 4: Short replies (a sentence or two) and non-structured prose: say and show match
    # Soft Rule 3: Never truncated mid-thought by any length cap
    return show_clean, show_clean
