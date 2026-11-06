"""READ-ONLY sealed identity → DreamThink decide/render candidates.

HARD LOCK: never mutate TSC / soul / sealed identity / voice files.
Daychat identity gap was UNWIRED (not offline): TSC.iam + roster remain
readable; speech_render simply never loaded them as decide fuel.
"""
from __future__ import annotations

import re
from typing import Any

IDENTITY_CUE_RE = re.compile(
    r"\b(?:"
    r"who\s+are\s+you|"
    r"what\s+are\s+you(?!\s+thinking)|"
    r"what(?:'s|\s+is)\s+your\s+name|"
    r"introduce\s+yourself|"
    r"tell\s+me\s+about\s+yourself|"
    r"are\s+you\s+jarvis|"
    r"your\s+name\b|"
    r"who\s+is\s+jarvis"
    r")\b",
    re.I,
)

REMEMBER_ME_RE = re.compile(
    r"\b(?:"
    r"do\s+you\s+remember\s+me|"
    r"remember\s+me|"
    r"do\s+you\s+know\s+(?:who\s+)?i\s+am|"
    r"who\s+am\s+i(?:\s+to\s+you)?"
    r")\b",
    re.I,
)

IDENTITY_MOVE = "state sealed self-intro from identity facts"
IDENTITY_SUBJECT = "answer an identity inquiry"
REMEMBER_MOVE = "prove operator recognition from sealed identity and profile memory"
REMEMBER_SUBJECT = "answer a remember-me inquiry"


def identity_cues(text: str) -> bool:
    return bool(IDENTITY_CUE_RE.search(text or ""))


def remember_me_cues(text: str) -> bool:
    return bool(REMEMBER_ME_RE.search(text or ""))


def self_knowledge_cues(text: str) -> bool:
    return identity_cues(text) or remember_me_cues(text)


def load_sealed() -> dict[str, Any]:
    """Read sealed self-knowledge only. Never writes."""
    out: dict[str, Any] = {
        "ok": False,
        "name": None,
        "operator": None,
        "iam": [],
        "runtime": None,
        "role": None,
        "source": None,
        "error": None,
    }
    try:
        from exo_core import TSC

        tsc = TSC()
        out["name"] = str(getattr(tsc, "name", "") or "")
        out["operator"] = str(getattr(tsc, "operator", "") or "")
        iam = getattr(tsc, "iam", ()) or ()
        out["iam"] = [str(x) for x in iam if str(x).strip()]
        out["source"] = "tsc.iam+name+operator"
        if out["name"] and out["iam"]:
            out["ok"] = True
    except Exception as exc:  # noqa: BLE001
        out["error"] = f"tsc:{exc}"
    try:
        from connection_identity import roster

        ent = (roster().get("entities") or {}).get("jarvis") or {}
        out["role"] = ent.get("role")
        out["runtime"] = ent.get("runtime")
        if not out["source"]:
            out["source"] = "identity_roster"
        if out["role"] and not out["ok"]:
            out["name"] = out["name"] or "JARVIS"
    except Exception as exc:  # noqa: BLE001
        if out["error"]:
            out["error"] += f"; roster:{exc}"
        else:
            out["error"] = f"roster:{exc}"
    return out


def spoken_from_sealed(utterance: str = "") -> str | None:
    """Natural spoken self-intro built only from sealed facts."""
    sealed = load_sealed()
    if not sealed.get("ok") and not (sealed.get("name") and sealed.get("iam")):
        return None
    name = sealed.get("name") or "JARVIS"
    operator = sealed.get("operator") or "Mike"
    iam = list(sealed.get("iam") or [])
    primary = iam[0] if iam else f"I am {name}, {operator}'s persistent personal AI assistant."
    spoken = primary
    if spoken.startswith("I am "):
        spoken = "I'm " + spoken[5:]
    utt = (utterance or "").lower()
    if re.search(r"what(?:'s|\s+is)\s+your\s+name|your\s+name\b", utt):
        return f"I'm {name}."
    if re.search(r"\bare\s+you\s+jarvis\b", utt):
        return f"Yes — I'm {name}, {operator}'s persistent personal AI assistant."
    presence = next(
        (x for x in iam if "persistent presence" in x.lower() or "one authoritative brain" in x.lower()),
        None,
    )
    if presence and presence not in primary:
        if "persistent presence" in presence.lower():
            spoken = spoken.rstrip(".") + " — a persistent presence, not just a chat window."
        elif "across PC" in presence or "across pc" in presence.lower():
            spoken = spoken.rstrip(".") + " One brain across PC and phone."
    return spoken


def spoken_remember_me(profile_snippet: str | None = None) -> str:
    sealed = load_sealed()
    operator = sealed.get("operator") or "Mike"
    name = sealed.get("name") or "JARVIS"
    base = f"Of course I remember you — you're {operator}, my operator. I'm {name}."
    snip = (profile_snippet or "").strip()
    if snip:
        # Keep short; attribute as remembered profile, never invent.
        clip = snip
        if len(clip) > 140:
            clip = clip[:137].rsplit(" ", 1)[0] + "…"
        return f"{base} From what I've kept: {clip}"
    return f"{base} Keeping this brain sharp with you."


def identity_candidate(utterance: str = "", profile_snippet: str | None = None) -> dict[str, Any] | None:
    """Decide candidate (conversation_move) for speech_render; llm_calls stays 0."""
    if remember_me_cues(utterance) and not identity_cues(utterance):
        spoken = spoken_remember_me(profile_snippet)
        subject, obj, scene = REMEMBER_SUBJECT, REMEMBER_MOVE, "identity_remember_me"
        nid = "identity-sealed-remember"
    else:
        spoken = spoken_from_sealed(utterance)
        if not spoken:
            return None
        subject, obj, scene = IDENTITY_SUBJECT, IDENTITY_MOVE, "identity_self_intro"
        nid = "identity-sealed-self"
    sealed = load_sealed()
    name = sealed.get("name") or "JARVIS"
    operator = sealed.get("operator") or "Mike"
    gist = f"Before I {subject}, I should {obj}."
    return dict(
        id=nid,
        gist=gist,
        subject=subject,
        object=obj,
        speech_style="conversation_move",
        scene_id=scene,
        practice_focus="identity",
        provenance="SEALED_IDENTITY_READONLY",
        authority="verified_event",
        hypothetical=False,
        spoken=spoken,
        say=spoken,
        cue_tokens=[
            "identity", "self", "intro", "name", "jarvis", "who", "are", "you",
            "assistant", "remember", "operator", "profile", name.lower(), operator.lower(),
            "sealed",
        ],
        relations=[dict(subject=subject, predicate="requires", object=obj)],
        sealed_source=sealed.get("source"),
    )


def identity_blocker() -> str | None:
    sealed = load_sealed()
    if sealed.get("ok"):
        return None
    return "Sealed identity unreadable for daychat wire: " + str(
        sealed.get("error") or "no TSC.iam / name"
    )
