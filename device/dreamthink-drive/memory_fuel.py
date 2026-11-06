"""READ-ONLY PSC/WFC memory fuel for DreamThink decide→render.

Mike lock: everything but the LLM is fine — memory is part of the brain.
This module never writes PSC/WFC and never calls a model. It only shapes
existing memories into imprint-bank candidates for speech_render.
"""
from __future__ import annotations

import hashlib
import re
from typing import Any

PROFILE_CATS = ("operator_profile", "owner_taste", "embodied_identity")
STOP = set(
    "what which who where when how did do does have has had you your yours me my "
    "mine i we us our about tell please remember recall know the a an and or is "
    "are was were to in of from with that this it just".split()
)


def _concepts(text: str) -> set[str]:
    words = re.findall(r"[a-z][a-z0-9_]{1,35}", (text or "").lower())
    return {w for w in words if w not in STOP and len(w) > 2}


def _rows_from_psc(psc) -> list[dict]:
    if psc is None:
        return []
    try:
        rows = list(getattr(psc, "memories", None) or [])
        if rows:
            return [r for r in rows if isinstance(r, dict)]
    except Exception:
        pass
    if isinstance(psc, list):
        return [r for r in psc if isinstance(r, dict)]
    if isinstance(psc, dict):
        mems = psc.get("memories")
        if isinstance(mems, list):
            return [r for r in mems if isinstance(r, dict)]
    return []


def profile_snippet(psc, max_chars: int = 180) -> str | None:
    """Best short operator-profile line for remember-me / identity context."""
    preferred = []
    for row in _rows_from_psc(psc):
        cat = str(row.get("category") or "")
        if cat not in PROFILE_CATS:
            continue
        note = str(row.get("memory") or row.get("text") or "").strip()
        if not note:
            continue
        preferred.append((cat, note))
    if not preferred:
        return None
    # Prefer operator_profile, then embodied personhood, then taste.
    order = {"operator_profile": 0, "embodied_identity": 1, "owner_taste": 2}
    preferred.sort(key=lambda x: order.get(x[0], 9))
    note = preferred[0][1]
    # Drop section headers if present (ASCII or unicode dashes).
    note = re.sub(r"^[A-Z][A-Z0-9 /&,.\-—–]{6,}[:—–-]\s*", "", note)
    note = re.sub(r"^OPERATOR PROFILE\s*[—–-]\s*", "", note, flags=re.I)
    if len(note) > max_chars:
        note = note[: max_chars - 1].rsplit(" ", 1)[0] + "…"
    return note


def memory_candidates(raw: str, psc=None, wfc=None, limit: int = 12) -> list[dict]:
    """Build decide-fuel candidates from PSC (+ light WFC). Read-only."""
    out: list[dict] = []
    terms = _concepts(raw)
    # Always include a few profile rows as soft context for owner chat.
    profile_rows = []
    scored = []
    for row in _rows_from_psc(psc)[-2500:]:
        cat = str(row.get("category") or "")
        source = str(row.get("source") or "")
        # Skip dream hypotheses as factual owner memory fuel.
        if cat == "dream_hypothesis" or source.startswith("DREAM"):
            continue
        note = str(row.get("memory") or row.get("text") or "").strip()
        if not note or len(note) < 12:
            continue
        if re.search(r"password|bearer\s|api[_ -]?key|access[_ -]?token", note, re.I):
            continue
        toks = _concepts(note)
        overlap = terms & toks
        entry = dict(
            id=str(row.get("id") or ("mem-" + hashlib.sha256(note.encode()).hexdigest()[:14])),
            gist=note if note.lower().startswith("before i ") else (
                f"Before I use remembered context about this, I should stay faithful to: {note[:220]}"
            ),
            memory=note,
            category=cat,
            provenance="PSC_MEMORY_READONLY",
            authority="verified_event",
            hypothetical=False,
            speech_style="memory_context",
            cue_tokens=sorted(list(toks)[:24]),
            subject="use remembered operator context",
            object="stay faithful to saved notes without inventing",
        )
        # For speak_move / identity, attach spoken only on remember-me style rows later.
        if cat in PROFILE_CATS:
            profile_rows.append(entry)
        score = len(overlap)
        if cat in PROFILE_CATS:
            score += 1.5
        if overlap or cat in PROFILE_CATS:
            scored.append((score, entry))
    scored.sort(key=lambda x: x[0], reverse=True)
    seen = set()
    for score, entry in scored:
        if len(out) >= limit:
            break
        nid = entry["id"]
        if nid in seen:
            continue
        seen.add(nid)
        # Parse-friendly gist for speech_render.
        note = entry.get("memory") or ""
        entry["gist"] = (
            f"Before I answer with remembered context, I should stay faithful to this note: {note[:240]}"
        )
        entry["relations"] = [
            dict(
                subject="answer using remembered context",
                predicate="requires",
                object="stay faithful to saved notes without inventing",
            )
        ]
        out.append(entry)

    # Recent WFC owner turns as session context (not authority).
    for i, row in enumerate(list(wfc or [])[-8:]):
        if not isinstance(row, dict):
            continue
        if str(row.get("speaker", "")).casefold() not in ("mike", "operator", ""):
            # allow missing speaker for harness
            if row.get("speaker") and str(row.get("speaker")).casefold() != "mike":
                continue
        raw_turn = str(row.get("raw") or "").strip()
        if len(raw_turn) < 4 or raw_turn == raw:
            continue
        nid = "wfc-" + hashlib.sha256(raw_turn.encode()).hexdigest()[:12]
        if nid in seen:
            continue
        out.append(
            dict(
                id=nid,
                gist=f"Before I continue this thread, I should remember you just said: {raw_turn[:200]}",
                memory=raw_turn,
                provenance="WFC_SESSION_READONLY",
                authority="verified_event",
                hypothetical=False,
                speech_style="memory_context",
                subject="continue the active conversation thread",
                object="reuse the recent owner utterance as context",
                cue_tokens=sorted(list(_concepts(raw_turn))[:16]),
            )
        )
        if len(out) >= limit + 4:
            break
    return out


def remember_me_candidate(psc=None) -> dict | None:
    """Strong remember-me decide candidate from profile + sealed identity."""
    try:
        import identity_wire as iw
    except Exception:
        return None
    snip = profile_snippet(psc)
    return iw.identity_candidate("do you remember me", profile_snippet=snip)
