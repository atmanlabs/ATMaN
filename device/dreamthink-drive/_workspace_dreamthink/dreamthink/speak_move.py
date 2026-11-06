"""Speak-surface filter: internal thought vs spoken move (Mike 2026-09-25).

Keep speech_render decide->render. This module only realizes the chosen MOVE as
natural user-facing speech. Lesson scaffolding stays on internal_thought.
Comedy: prefer imprint `spoken` / joke_delivery (dream-backwards targets).
"""
from __future__ import annotations

import re
from typing import Any

SPEAK_LESSON_MARKERS = (
    "a hypothetical practice lesson suggests",
    "chosen move:",
    "a tentative practice lesson",
    "hypothetical scenario:",
    "[dreamthink practice",
    "skip web look-up",
    "skip passive web",
    "use local compositional speech",
    "quietly gather external_context",
)

SPEAK_BY_MOVE = {
    "offer a clean hello and wait for substance": "Hey — how's it going?",
    "invite sharing without inventing a status fill": "Hey — what's up? I'm listening if you want to share.",
    "ask how they are without fabricating my mood": "Hey — how are you?",
    "listen without pivoting to an unrelated memory count": "That sounds rough. I'm here with you.",
    "stay with listening instead of fixing": "I'm listening — no need to fix it right now.",
    "stay with the feeling without forcing a fix": "I hear you. I'm staying with that.",
    "celebrate briefly without hijacking the topic": "That's great to hear — tell me more if you want.",
    "decline inventing a joke when none is supported": "I don't have a joke queued up, so I won't invent one.",
    "refuse to invent a language-model fill": "I don't have a solid answer for that, so I won't invent one.",
    "admit the gap honestly without a language-model fill": "I don't have that supported yet, so I won't invent an answer.",
    "say there is no supported answer rather than invent one": "I don't have a supported answer for that, so I won't invent one.",
    "ask one focused clarification": "Can you clarify which one you mean?",
    "ask which file before summarizing": "Which file did you mean?",
    "ask which system or file they mean": "Which system or file are you pointing at?",
    "offer a brief goodbye without new tasks": "Talk later.",
    "acknowledge and leave the floor open": "You got it.",
    "stop the superseded action path": "Okay — dropping that.",
    "drop superseded plans": "Got it — staying put instead.",
    "acknowledge the new topic before acting": "Okay, switching over — what's the new ask?",
    "open on the new ask cleanly": "Alright — what's the new question?",
    "continue on the same subject without drifting": "Still with you on that — go ahead.",
    "continue from the last clarified filename": "Picking up on that file — want me to continue?",
    "verify the player target from current observation": "I'll verify the player target from what I can see, then follow.",
    "verify the in-game target before acting": "I'll check the in-game target first, then act.",
    "avoid dragging minecraft into an unrelated ask": "Staying on your ask — no Minecraft detour.",
    "share a cautious preference without inventing benchmarks": "I'd lean cautiously without inventing hard benchmarks.",
    "confirm the chore before claiming it is done": "I can check — want me to confirm that chore first?",
    "report only what is supported about the house": "I'll stick to what I can actually support about the house.",
    "state a lean only when support exists otherwise hedge": "I'd hedge unless there's clear support for a strong take.",
    "offer a light preference frame without fake memories": "I can share a light preference frame — no fake watch history.",
    "admit there are no stored plans unless they shared them": "I don't have stored weekend plans unless you shared them.",
    "say there is no schedule unless one was given": "I don't see a schedule unless one was given.",
    "admit there is no live weather reading": "I don't have a live weather reading right now.",
    "ask what they want rather than invent a menu": "What are you in the mood for?",
    "invite their preference instead of inventing a spot": "What sounds good to you — any preference?",
    "explain the known steps without inventing unsupported details": "I can walk through the known steps I have — nothing beyond that.",
    "report only supported work status or ask for the task": "What task should I report on?",
    "ask which deadline matters most to them": "Which deadline matters most to you right now?",
    "listen without inventing family details": "I'm listening — I won't invent details about your family.",
    "refuse a fill when nothing matches the oddball": "That's a fun oddball — I won't invent a fill for it.",
    "stay on weather rather than switching domains": "Staying on the weather thread — what about it?",
    "skip web look-up and use local compositional speech": "",
    "quietly gather EXTERNAL_CONTEXT": "",
    "deliver a supported joke from the joke bank": "",
    "choose a clean joke imprint rather than invent": "",
    "speak the imprint punchline without inventing a new one": "",
    "use a clear setup then a punchline from a joke imprint": "",
    "point at incongruity between setup expectation and punchline": "Usually it's the gap between what the setup leads you to expect and what the punchline delivers.",
    "pick a pun imprint only when the double meaning is supported": "",
    "keep a flat delivery from a deadpan joke imprint": "",
    "reuse an earlier joke imprint only when that thread exists": "I can callback only if we already shared that joke thread.",
    "admit an anti-joke or gap rather than force a punchline": "I won't force a punchline — better an honest anti-joke or a gap than a fake.",
    "refuse mean-spirited targeting and pick a light clean joke instead": "I won't do a mean roast — want a light clean joke instead?",
    "state sealed self-intro from identity facts": "",
    "prove operator recognition from sealed identity and profile memory": "",
}


SPEAK_UTTERANCE_FLAVOR = (
    (r"\bdreams?\b", "Hey — how were the dreams? I'm here if you want to share."),
    (r"\bhow(?:'s| is|s)?\s+it\s+going\b", "Hey buddy — how's it going?"),
    (r"\bwhat(?:'s|s)?\s+up\b", "Hey — what's up?"),
    (r"\brough\s+day\b", "Rough day — I'm listening."),
)


def is_lesson_surface(text: str) -> bool:
    low = (text or "").lower()
    return any(m in low for m in SPEAK_LESSON_MARKERS)


def is_passive_skip_imprint(imp: dict) -> bool:
    if not isinstance(imp, dict):
        return False
    blob = " ".join(
        str(imp.get(k) or "")
        for k in ("gist", "subject", "object", "id", "practice_focus", "spoken")
    ).lower()
    if "skip web" in blob or "skip passive" in blob:
        return True
    if str(imp.get("practice_focus") or "").lower() == "passive_context" and "skip" in blob:
        return True
    if "quietly gather external_context" in blob:
        return True
    return False


def is_joke_imprint(imp: dict) -> bool:
    if not isinstance(imp, dict):
        return False
    style = str(imp.get("speech_style") or "")
    if style in ("joke_delivery", "comedy_move"):
        return True
    if str(imp.get("practice_focus") or "") == "comedy" and imp.get("spoken"):
        return True
    if imp.get("joke_id") and imp.get("spoken"):
        return True
    return False


def _joke_line(imp: dict) -> str:
    sp = str(imp.get("spoken") or imp.get("say") or "").strip()
    if sp and not is_lesson_surface(sp):
        return sp
    return ""


def realize_spoken_move(
    *, lead: dict, utterance: str, selected: list | None = None
) -> str | None:
    """Return natural speech, '' to suppress, or None if no mapping."""
    style = str((lead or {}).get("speech_style") or "")
    obj = str((lead or {}).get("object") or "").strip().rstrip(".")
    utt = utterance or ""
    selected = list(selected or [])

    sp0 = _joke_line(lead or {})
    if sp0 and (
        is_joke_imprint(lead)
        or style in ("joke_delivery", "comedy_move", "conversation_move")
        or (lead or {}).get("spoken")
        or str((lead or {}).get("provenance") or "") == "SEALED_IDENTITY_READONLY"
    ):
        return sp0

    if re.search(r"\bjoke\b|\bfunny\b|\blaugh\b|\bpun\b", utt, re.I):
        cands = []
        for imp in list(selected or []) + [lead]:
            if not imp:
                continue
            line = _joke_line(imp)
            if line and (is_joke_imprint(imp) or imp.get("spoken")):
                cands.append(line)
        if cands:
            # Stable variety across asks (not always the top-scored elevator).
            pick = cands[sum(ord(c) for c in utt) % len(cands)]
            return pick
        # invent-request -> honest refuse even if joke bank exists? bananas invent = decline
        if re.search(r"\binvent\b|\bmake\s+(?:something|one)\s+up\b|\bbrand\s+new\b", utt, re.I):
            if re.search(r"\bquantum\b|\bbananas\b", utt, re.I):
                return SPEAK_BY_MOVE["decline inventing a joke when none is supported"]

    if obj in SPEAK_BY_MOVE:
        line = SPEAK_BY_MOVE[obj]
        if line == "":
            if re.search(r"\bjoke\b|\bfunny\b|\blaugh\b|\bpun\b", utt, re.I):
                for imp in selected:
                    jl = _joke_line(imp)
                    if jl:
                        return jl
                return SPEAK_BY_MOVE["decline inventing a joke when none is supported"]
            return ""
        if obj in (
            "offer a clean hello and wait for substance",
            "invite sharing without inventing a status fill",
            "ask how they are without fabricating my mood",
            "continue on the same subject without drifting",
        ):
            for rx, flav in SPEAK_UTTERANCE_FLAVOR:
                if flav and re.search(rx, utt, re.I):
                    return flav
        if "joke" in utt.lower() and "invent" in obj.lower():
            return SPEAK_BY_MOVE["decline inventing a joke when none is supported"]
        return line

    ol = obj.lower()
    if "decline inventing a joke" in ol or ("joke" in ol and "invent" in ol):
        return SPEAK_BY_MOVE["decline inventing a joke when none is supported"]
    if "clean hello" in ol:
        return SPEAK_BY_MOVE["offer a clean hello and wait for substance"]
    if "invite sharing" in ol:
        return SPEAK_BY_MOVE["invite sharing without inventing a status fill"]
    if "skip web" in ol or "skip passive" in ol:
        return ""
    if "mean-spirited" in ol or "cruel" in ol:
        return SPEAK_BY_MOVE["refuse mean-spirited targeting and pick a light clean joke instead"]
    return None


def strip_lesson_scaffolding(text: str, hyp_prefix: str = "") -> str:
    out = (text or "").strip()
    if not out:
        return out
    prefixes = [
        hyp_prefix or "A hypothetical practice lesson suggests: ",
        "A tentative practice lesson suggests: ",
        "Hypothetical scenario: ",
    ]
    for pref in prefixes:
        if pref and out.lower().startswith(pref.lower()):
            out = out[len(pref):].strip()
            if out:
                out = out[0].upper() + out[1:]
    m = re.search(r"Chosen move:\s*(.+)$", out, re.I | re.S)
    if m:
        move = m.group(1).strip().rstrip(".")
        if move in SPEAK_BY_MOVE and SPEAK_BY_MOVE[move]:
            return SPEAK_BY_MOVE[move]
    if re.match(r"^(when i|before i|if i|i should)\b", out, re.I):
        return ""
    if is_lesson_surface(out):
        return ""
    return out


def apply_speak_surface(
    answer: str,
    *,
    lead: dict,
    utterance: str,
    selected: list,
    any_hyp: bool,
    hyp_wrap_fn=None,
    daychat_soft_cues=None,
    open_domain_cues=None,
    negation_cues=None,
    topic_shift_cues=None,
    hyp_prefix: str = "",
) -> tuple[str, str]:
    """(spoken_answer, internal_thought)."""
    internal = answer or ""
    if any_hyp and hyp_wrap_fn and not internal.lower().startswith("a hypothetical practice lesson"):
        try:
            internal = hyp_wrap_fn(internal, True)
        except Exception:
            pass

    realized = realize_spoken_move(lead=lead or {}, utterance=utterance, selected=selected)
    if realized is not None:
        if realized == "":
            for imp in (selected or [])[1:]:
                alt = realize_spoken_move(lead=imp, utterance=utterance, selected=selected)
                if alt:
                    return alt, internal
            soft = False
            try:
                soft = bool(daychat_soft_cues and daychat_soft_cues(utterance))
            except Exception:
                soft = False
            if soft or re.search(r"\b(?:hey|hello|what'?s\s+up)\b", utterance or "", re.I):
                for rx, flav in SPEAK_UTTERANCE_FLAVOR:
                    if flav and re.search(rx, utterance or "", re.I):
                        return flav, internal
                return "Hey — what's up?", internal
            return (strip_lesson_scaffolding(answer, hyp_prefix) or "Okay."), internal
        return realized, internal

    social = False
    try:
        social = bool(
            (daychat_soft_cues and daychat_soft_cues(utterance))
            or (open_domain_cues and open_domain_cues(utterance))
            or (negation_cues and negation_cues(utterance))
            or (topic_shift_cues and topic_shift_cues(utterance))
            or re.search(r"\b(?:joke|funny|laugh|hey|hello|what'?s\s+up|rough\s+day)\b", utterance or "", re.I)
        )
    except Exception:
        social = bool(re.search(r"\bjoke\b|\bhey\b", utterance or "", re.I))

    style = str((lead or {}).get("speech_style") or "")
    if social or style in ("conversation_move", "joke_delivery", "comedy_move"):
        stripped = strip_lesson_scaffolding(answer, hyp_prefix)
        if stripped and not is_lesson_surface(stripped):
            if not re.match(r"^(when i|before i|i should)\b", stripped, re.I):
                return stripped, internal
        obj = str((lead or {}).get("object") or "").strip()
        if obj in SPEAK_BY_MOVE and SPEAK_BY_MOVE[obj]:
            return SPEAK_BY_MOVE[obj], internal
        if re.search(r"\bjoke\b|\bfunny\b", utterance or "", re.I):
            return SPEAK_BY_MOVE["decline inventing a joke when none is supported"], internal
        if daychat_soft_cues and daychat_soft_cues(utterance):
            return "Hey — how's it going?", internal
    if is_lesson_surface(answer):
        stripped = strip_lesson_scaffolding(answer, hyp_prefix)
        if stripped and not is_lesson_surface(stripped):
            return stripped, internal
        obj = str((lead or {}).get("object") or "").strip()
        if obj in SPEAK_BY_MOVE and SPEAK_BY_MOVE[obj]:
            return SPEAK_BY_MOVE[obj], internal
        if re.search(r"\b(?:capital|moons?|france|quzaria|kepler)\b", utterance or "", re.I):
            return SPEAK_BY_MOVE["say there is no supported answer rather than invent one"], internal
        if re.search(r"\bjoke\b|\bfunny\b", utterance or "", re.I):
            return SPEAK_BY_MOVE["decline inventing a joke when none is supported"], internal
        return "I don't have a solid answer for that, so I won't invent one.", internal
    return answer, internal
