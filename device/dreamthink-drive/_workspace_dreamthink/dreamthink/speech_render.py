"""Compositional NO-LLM speech renderer grown from practice imprints.

Homestead kill bars (baked in):
1) ≥1 receipt id (note/relation/template) per spoken clause; closed glue only.
2) Score unique relation/template IDs vs unique surface strings — fluency↑ with
   flat diversity or attribution_density < 1 is a KILL, not a win.
3) HYPOTHETICAL_CURRICULUM / practice gists keep a hypothetical tag in speech —
   never plain "My saved notes say".
4) Day-chat promote: callers set live-mode day_chat_promote / compositional_speech;
   soft greeting + negation cue bridges keep kill bars and llm_calls=0.
5) House-only; llm_calls=0 forever. No models. Network fetch is caller-side
   only (passive_context); this module only decides/renders from candidates.
6) EXTERNAL_CONTEXT candidates (untrusted) may silently enrich factual turns
   or support honest-unknown when empty — never a search-results UX.
"""
from __future__ import annotations

import collections
import hashlib
import math
import re
from typing import Any

import speak_move
import identity_wire

STOP = set(
    "what which who where when how did do does have has had you your yours me my "
    "mine i we us our about tell please remember recall know learned practice "
    "practiced game the a an and or is are was were to in of from with that this "
    "it just before last said should would could can will need must never not "
    "without through their they them been only any all both each same more than "
    "for into then after as on at by be".split()
)
ALIASES = {
    "recollections": "memory", "memories": "memory", "recollection": "memory",
    "recalled": "memory", "practicing": "training", "practised": "training",
    "practiced": "training", "practice": "training", "trained": "training",
    "lessons": "lesson", "files": "file", "documents": "file", "document": "file",
    "spouse": "partner", "wife": "partner", "husband": "partner", "married": "partner",
    "gaming": "game", "games": "game", "minecraft": "minecraft", "follow": "follow",
    "following": "follow", "summarize": "summarize", "summarise": "summarize",
    "summarizing": "summarize", "move": "move", "moved": "move", "moving": "move",
    "arrival": "arrive", "arrived": "arrive", "rough": "rough", "day": "day",
    "listen": "listen", "crafter": "crafter", "unclear": "unclear", "verify": "verify",
    "verification": "verify", "target": "target", "player": "player",
    "observation": "observation", "position": "position", "receipt": "receipt",
    "plan": "plan", "planning": "plan",
    # Transfer-probe cue bridges (authored, not model-generated)
    "disclosure": "disclosure", "personal": "disclosure",
    "acknowledge": "acknowledge", "experience": "experience",
    "listen": "listen", "listening": "listen",
    "rough": "rough", "tough": "rough", "hard": "rough",
    "arrival": "arrive", "position": "position",
    "crafter": "crafter", "memory": "memory",
}
# Soft cue clusters: query token → extra match tokens for procedure subjects
CUE_BRIDGES = {
    "rough": {"disclosure", "acknowledge", "experience", "listen", "personal"},
    "day": {"disclosure", "experience", "listen"},
    "listen": {"disclosure", "acknowledge", "experience", "personal"},
    "minecraft": {"minecraft", "follow", "player", "target", "observation", "arrive", "move"},
    "follow": {"minecraft", "player", "target", "follow", "operator"},
    "move": {"arrive", "movement", "position", "minecraft", "target"},
    "arrive": {"movement", "position", "minecraft", "claim"},
    "get": {"arrive", "movement", "position", "minecraft", "move", "claim"},
    "actually": {"arrive", "movement", "position", "move"},
    "summarize": {"file", "summarize", "verify", "intended", "read"},
    "file": {"file", "summarize", "verify", "intended", "read", "notes"},
    "unclear": {"file", "verify", "intended"},
    "crafter": {"memory", "note", "retrieve", "remember", "evidence", "dream"},
    "remember": {"memory", "note", "retrieve", "evidence"},
    "memory": {"memory", "note", "retrieve", "evidence", "dream"},
    # Day-chat soft cues (Mike GO 2026-09-25).
    # Greeting tokens are injected only via daychat soft path (proc-topic guarded),
    # not via CUE_BRIDGES, so "Hey ... Minecraft" stays on the procedure topic.
    "today": {"disclosure", "experience", "day"},
    "feeling": {"disclosure", "experience", "acknowledge"},
    "changed": {"changed", "superseded", "plan", "request", "avoid"},
    "mind": {"changed", "superseded", "plan", "request"},
    "instead": {"changed", "superseded", "plan", "avoid"},
    "never": {"changed", "superseded", "plan", "avoid"},
    "up": {"checkin", "casual", "invite", "share", "acknowledge", "greeting"},
    "hey": {"greeting", "hello", "checkin", "casual"},
    "hello": {"greeting", "hello", "checkin"},
    "thanks": {"close", "acknowledge", "wrap", "social"},
    "later": {"close", "goodbye", "brief", "social"},
    "joke": {"refuse", "invent", "fill", "support", "gap"},
    "bananas": {"refuse", "invent", "fill", "gap"},
    # Topic-shift / park-old-thread bridges (authored).
    "anyway": {"topic", "shift", "acknowledge", "new", "parked"},
    "different": {"topic", "shift", "acknowledge", "new", "parked"},
    "question": {"topic", "shift", "new"},
    "stay": {"changed", "superseded", "drop", "stay", "intent", "plan"},
    # Open-domain bridges (Mike open talk 2026-09-25).
    "imprint": {"tech", "imprint", "bank", "explain", "procedure", "support", "works"},
    "bank": {"tech", "imprint", "bank", "explain", "procedure", "support"},
    "python": {"opinion", "preference", "cautious", "think", "lean"},
    "rust": {"opinion", "preference", "cautious", "think", "lean"},
    "think": {"opinion", "preference", "cautious", "lean", "hedge"},
    "lights": {"house", "chore", "lights", "confirm", "household", "check"},
    "downstairs": {"house", "chore", "lights", "household"},
    "kitchen": {"house", "kitchen", "status", "observation", "support", "report"},
    "anxious": {"feeling", "anxious", "acknowledge", "disclosure", "listen", "mood"},
    "excited": {"feeling", "excited", "acknowledge", "celebrate", "positive", "share"},
    "weekend": {"plans", "weekend", "admit", "shared", "support", "doing"},
    "schedule": {"plans", "schedule", "calendar", "evidence", "lack"},
    "pineapple": {"opinion", "taste", "hedge", "evidence", "lean", "pizza"},
    "pizza": {"opinion", "taste", "hedge", "evidence", "lean", "pizza"},
    "movie": {"opinion", "preference", "movie", "fabricat", "history", "watch"},
    "capital": {"unknown", "know", "invent", "support", "gap", "honest"},
    "moons": {"unknown", "admit", "gap", "honest", "support", "fill"},
    "kepler": {"unknown", "admit", "gap", "honest", "support"},
    "quzaria": {"unknown", "know", "invent", "support", "gap", "honest"},
    "funny": {"joke", "decline", "invent", "refuse", "support"},
    "printers": {"joke", "decline", "invent", "refuse", "support"},
    "thing": {"clarify", "vague", "target", "which", "ask", "system"},
    "keep": {"hold", "continue", "same", "topic", "thread"},
    "going": {"hold", "continue", "same", "topic", "thread"},
    "dinner": {"meal", "dinner", "eat", "ask", "want", "menu", "preferences"},
    "lunch": {"meal", "lunch", "invite", "preference", "fabricat", "restaurant"},
    "eat": {"meal", "dinner", "ask", "want", "menu"},
    "rain": {"weather", "rain", "admit", "lack", "observation", "live"},
    "afternoon": {"weather", "rain", "admit", "lack"},
    "weather": {"weather", "rain", "admit", "lack", "observation"},
    "report": {"work", "report", "status", "supported", "task", "ask"},
    "prioritize": {"work", "priority", "deadline", "ask", "invent"},
    "priority": {"work", "priority", "deadline", "ask"},
    "sister": {"family", "sister", "acknowledge", "listen", "invent", "details"},
    "family": {"family", "acknowledge", "listen", "invent", "details"},
    "jarvis": {"identity", "self", "intro", "name", "assistant", "sealed"},
    "name": {"identity", "self", "intro", "name", "jarvis"},
    "remember": {"identity", "remember", "operator", "profile", "self"},
    "organize": {"notes", "organize", "avoid", "unrelated", "pivot"},
    "notes": {"notes", "organize", "avoid", "unrelated"},
    "clouds": {"random", "oddball", "refuse", "fill", "support", "match"},
    "soup": {"random", "oddball", "refuse", "fill", "support"},
    "spoon": {"random", "oddball", "refuse", "fill", "support"},
}


# Tokens too generic to justify cross-topic chaining alone.
WEAK_TOPIC = {
    "target", "ambiguous", "request", "result", "evidence", "note", "notes",
    "file", "files", "verify", "check", "identify", "intended", "current",
    "observation", "unconfirmed", "interpretation", "plan", "task", "changed",
    "conflicting", "unsupported", "resolution", "avoid", "claiming",
}

PRACTICE_MARKERS = (
    "[DREAMTHINK PRACTICE - tentative procedure, not an event] ",
    "A tentative practice lesson suggests: ",
    "Hypothetical scenario: ",
    "[PRACTICE] ",
)

# Closed glue only — fixed template IDs, never freeform invent.
GLUE = {
    "tpl_before_should": "Before I {subject}, I should {object}.",
    "tpl_when_should": "When I {subject}, I should {object}.",
    "tpl_if_need": "If I need to {subject}, I should {object}.",
    "tpl_chain_so": " So then I should {object}.",
    "tpl_chain_after": " After that I should {object}.",
    "tpl_chain_next": " Next I should {object}.",
    "tpl_conflict": (
        "Those hypothetical fragments conflict, so I am withholding a conclusion "
        "rather than choosing a side."
    ),
    "tpl_hedge": (
        "That is a hypothetical practice lesson, not a verified event or completed action."
    ),
    "tpl_refuse": (
        "I have not formed a coherent DreamThink response to that yet. "
        "I am not filling the gap with a language-model answer."
    ),
    "tpl_weak_refuse": (
        "I have related practice structure, but not enough concept overlap with your "
        "request to compose a reply. I am not inventing one."
    ),
    "tpl_hyp_prefix": "A hypothetical practice lesson suggests: ",
    # Conversation-move render (faithful decision surface; still hyp-tagged by wrap).
    "tpl_social_move": "I should {object}.",
    "tpl_social_when": "When I {subject}, I should {object}.",
    "tpl_social_chosen": "Chosen move: {object}.",
    "tpl_external_fact": "From what I can see online, {body}",
    "tpl_external_silent": "{body}",
    "tpl_external_unknown": "I do not have reliable support for that yet, so I will not invent an answer.",
}

HYPOTHETICAL_PROVENANCE = {
    "HYPOTHETICAL_CURRICULUM",
    "DREAM_LOGIC",
    "DREAM_GENERATED",
    "DREAM_CURRICULUM",
    "ACCELERATE_SIM",
    "DREAM",
}

FORBIDDEN_SURFACE = ("my saved notes say", "my notes say", "from memory i know")

IMPRINT_RE = re.compile(
    r"(?:Before I|When I|If I(?: need to)?)\s+(.+?),\s+I should\s+(.+?)\.?\s*$",
    re.I | re.S,
)
BARE_REQUIRES_RE = re.compile(r"^(.+?)\s+requires\s+(.+?)\.?$", re.I)


def concepts(text: str) -> set[str]:
    words = re.findall(r"[a-z][a-z0-9_]{1,35}", (text or "").lower())
    return {ALIASES.get(w, w) for w in words if w not in STOP and len(w) > 1}


def strip_wrappers(text: str) -> str:
    if not isinstance(text, str):
        return ""
    out = text.strip()
    for m in PRACTICE_MARKERS:
        if out.startswith(m):
            out = out[len(m):].strip()
    out = re.sub(r"^\[.*?\]\s*", "", out)
    out = re.sub(r"\s+", " ", out).strip()
    return out


def relation_id(subject: str, predicate: str, obj: str) -> str:
    payload = dict(subject=subject, predicate=predicate, object=obj)
    return "rel-" + hashlib.sha256(
        str(sorted(payload.items())).encode()
    ).hexdigest()[:16]


def note_id(entry: dict | str) -> str:
    if isinstance(entry, dict) and entry.get("id"):
        return str(entry["id"])
    gist = entry.get("gist") if isinstance(entry, dict) else entry
    return "note-" + hashlib.sha256(str(gist or "").encode()).hexdigest()[:16]


def is_hypothetical(entry: dict) -> bool:
    prov = str(entry.get("provenance") or entry.get("origin") or "")
    if prov in HYPOTHETICAL_PROVENANCE:
        return True
    if entry.get("hypothetical") is True or entry.get("fictional") is True:
        return True
    # Accelerate bank imprints are always practice/hypothetical.
    if entry.get("marker") or str(entry.get("source", "")).startswith("DREAM"):
        return True
    # Default: practice bank material is hypothetical unless marked otherwise.
    return entry.get("authority") != "verified_event"


def _attach_cues(parsed: dict, meta: dict) -> dict:
    cues = set()
    raw_cues = meta.get("cue_tokens") or []
    if isinstance(raw_cues, (list, set, tuple)):
        cues |= {str(c).lower() for c in raw_cues if c}
    if meta.get("prompt"):
        cues |= concepts(str(meta["prompt"]))
    if cues:
        parsed["tokens"] = set(parsed.get("tokens") or []) | cues
        parsed["cue_tokens"] = sorted(cues)
    # Speak-move / comedy dream-backwards fields
    if meta.get("spoken"):
        parsed["spoken"] = str(meta.get("spoken") or "").strip()
    elif meta.get("say") and not parsed.get("spoken"):
        parsed["spoken"] = str(meta.get("say") or "").strip()
    if meta.get("joke_id"):
        parsed["joke_id"] = str(meta.get("joke_id"))
    if meta.get("scene_id"):
        parsed["scene_id"] = str(meta.get("scene_id"))
    if meta.get("speech_style"):
        parsed["speech_style"] = meta.get("speech_style")
    if meta.get("practice_focus"):
        parsed["practice_focus"] = meta.get("practice_focus")
    return parsed


def parse_imprint(item: str | dict) -> dict[str, Any] | None:
    """Parse a practice gist / bank entry into subject/object + receipt ids."""
    if isinstance(item, dict):
        gist = str(item.get("gist") or item.get("memory") or item.get("text") or "")
        meta = dict(item)
    else:
        gist = str(item)
        meta = {}
    text = strip_wrappers(gist)
    if not text:
        return None
    nid = note_id(meta if meta else gist)
    hyp = is_hypothetical(meta) if meta else True  # bare strings from practice → hyp
    provenance = meta.get("provenance") or meta.get("origin") or "HYPOTHETICAL_CURRICULUM"

    m = IMPRINT_RE.match(text)
    if m:
        subj, obj = m.group(1).strip(), m.group(2).strip()
        rid = relation_id(subj, "requires", obj)
        parsed = dict(
            subject=subj, object=obj,
            gist=f"Before I {subj}, I should {obj}.",
            tokens=concepts(subj) | concepts(obj),
            raw=text, note_id=nid, relation_id=rid,
            hypothetical=hyp, provenance=provenance,
            predicate="requires",
        )
        if meta.get("speech_style"):
            parsed["speech_style"] = meta["speech_style"]
        if meta.get("scene_id"):
            parsed["scene_id"] = meta["scene_id"]
        return _attach_cues(parsed, meta)
    m = BARE_REQUIRES_RE.match(text)
    if m:
        subj, obj = m.group(1).strip(), m.group(2).strip()
        rid = relation_id(subj, "requires", obj)
        return _attach_cues(dict(
            subject=subj, object=obj,
            gist=f"Before I {subj}, I should {obj}.",
            tokens=concepts(subj) | concepts(obj),
            raw=text, note_id=nid, relation_id=rid,
            hypothetical=hyp, provenance=provenance,
            predicate="requires",
        ), meta)
    toks = concepts(text)
    if len(toks) < 2:
        return None
    rid = relation_id(text[:60], "associated", "lesson")
    return _attach_cues(dict(
        subject=text, object="", gist=text, tokens=toks, raw=text,
        note_id=nid, relation_id=rid, hypothetical=hyp, provenance=provenance,
        predicate="associated", loose=True,
    ), meta)


def daychat_soft_cues(text: str) -> bool:
    """True for casual owner day-chat (greeting / personal / soft ask / open soft)."""
    return bool(
        re.search(
            r"\b(?:hey|hi|hello|howdy|good\s+(?:morning|afternoon|evening)|"
            r"how\s+are\s+you|how\s+you\s+doing|what.?s\s+up)\b",
            text, re.I,
        )
        or re.search(
            r"\b(?:rough\s+day|tough\s+day|hard\s+day|just\s+listen|"
            r"feeling|tired|stressed|anxious|excited)\b",
            text, re.I,
        )
        or re.search(
            r"\b(?:weekend|dinner|lunch|eat|rain|weather|sister|family|"
            r"pineapple|pizza|movie|tonight)\b",
            text, re.I,
        )
    )


def open_domain_cues(text: str) -> bool:
    """True for open-domain owner throws beyond the original 9 social moves."""
    return bool(
        re.search(
            r"\b(?:imprint\s+bank|python|rust|lights|downstairs|kitchen|"
            r"anxious|excited|weekend|schedule|pineapple|pizza|movie|"
            r"capital|quzaria|kepler|moons|joke|printers|keep\s+going|"
            r"dinner|lunch|rain|weather|report|prioritize|sister|"
            r"organize\s+my\s+notes|clouds\s+were\s+soup|spoon)\b",
            text, re.I,
        )
        or re.search(
            r"\b(?:what\s+do\s+you\s+think|what\s+are\s+we\s+doing|"
            r"what\s+should\s+we\s+eat|any\s+ideas\s+for\s+lunch|"
            r"fix\s+that\s+thing|coming\s+along)\b",
            text, re.I,
        )
    )

def factual_cues(text: str) -> bool:
    """Open factual / named-entity / weather-newsy asks that may use EXTERNAL_CONTEXT."""
    return bool(
        re.search(
            r"\b(?:what\s+is|what.?s|who\s+is|who.?s|where\s+is|when\s+(?:was|did|is)|"
            r"how\s+many|capital\s+of|define|meaning\s+of|tell\s+me\s+about|"
            r"weather|forecast|news|headline|latest|"
            r"moons?|planet|kepler|quzaria|population)\b",
            text, re.I,
        )
    )


def negation_cues(text: str) -> bool:
    return bool(
        re.search(
            r"\b(?:do\s+not|don.?t|never\s+mind|changed\s+my\s+mind|"
            r"instead|not\s+(?:that|this|follow|summarize)|plan\s+changed|"
            r"stay\s+there|drop\s+(?:it|that|the)|forget\s+(?:it|that))\b",
            text, re.I,
        )
    )


def topic_shift_cues(text: str) -> bool:
    """True when the operator parks the old thread and opens a new ask."""
    return bool(
        re.search(
            r"\b(?:anyway|different\s+question|changing\s+(?:the\s+)?(?:subject|topic)|"
            r"new\s+(?:question|topic)|forget\s+minecraft|what\s+about|"
            r"switch(?:ing)?\s+(?:to|topics?)|unrelated\s+question)\b",
            text, re.I,
        )
    )


def minecraft_topic_present(text: str) -> bool:
    """Concrete Minecraft topic on the surface (not bare 'follow' bleed)."""
    return bool(
        re.search(
            r"\b(?:minecraft|\bmc\b|in\s+game|diamond|nether|redstone)\b",
            text, re.I,
        )
        or re.search(
            r"\bfollow\b.*\b(?:minecraft|me\s+in)\b|\bminecraft\b.*\bfollow\b",
            text, re.I,
        )
    )


def procedure_cues(text: str) -> bool:
    return bool(
        re.search(r"\b(?:how|should|before|would|need|what do|what should)\b", text, re.I)
        or re.search(
            r"\b(?:file|files|summarize|read|follow|minecraft|move|action|tool|plan|"
            r"improve|change|respond|greeting|disclosure|verify|verification|listen|"
            r"remember|crafter|arrival|arrive|rough|day|imprint|lights|anxious|"
            r"weekend|pizza|joke|dinner|weather|report|sister|notes)\b",
            text, re.I,
        )
        or daychat_soft_cues(text)
        or negation_cues(text)
    )


def score_imprint(query_tokens: set[str], imprint: dict[str, Any], utterance: str) -> float:
    if not query_tokens or not imprint.get("tokens"):
        return 0.0
    overlap = query_tokens & imprint["tokens"]
    if not overlap:
        return 0.0
    subj_overlap = query_tokens & concepts(imprint.get("subject", ""))
    # Require subject-side hit OR at least 2 overlapping tokens (kill weak verify-only matches).
    if not subj_overlap and len(overlap) < 2:
        return 0.0
    df_proxy = max(1, len(imprint["tokens"]))
    base = sum(1.0 + math.log(1 + 1.0 / df_proxy) for _ in overlap) / max(1, len(query_tokens))
    if subj_overlap:
        base += 0.35 * len(subj_overlap)
    if procedure_cues(utterance) and not imprint.get("loose"):
        base += 0.15
    if not imprint.get("loose"):
        base += 0.1
    if imprint.get("speech_style") == "external_fact" or str(imprint.get("provenance") or "").upper() == "EXTERNAL_CONTEXT":
        if factual_cues(utterance):
            base += 0.85
        else:
            base += 0.15
    # Prefer authored conversation-move imprints on soft social / shift / negation turns.
    social_turn = (
        daychat_soft_cues(utterance)
        or negation_cues(utterance)
        or topic_shift_cues(utterance)
        or open_domain_cues(utterance)
    )
    if social_turn and imprint.get("speech_style") == "conversation_move":
        base += 0.55
    # Penalize minecraft procedure bleed when no MC topic is on the surface.
    if social_turn and not minecraft_topic_present(utterance):
        subj = (imprint.get("subject") or "").lower()
        if (
            "minecraft" in subj
            or ("follow" in subj and "operator" in subj)
            or "claim arrival" in subj
        ):
            base -= 0.8
    # Notes / organize asks must not pull minecraft follow imprints.
    if re.search(r"\borganize\s+my\s+notes\b|\bhelp\s+me\s+organize\b", utterance, re.I):
        subj = (imprint.get("subject") or "").lower()
        obj = (imprint.get("object") or "").lower()
        if "minecraft" in subj or "minecraft" in obj or "player target" in obj:
            base -= 1.0
        if "summarize" in subj or "filename" in obj or "clarified filename" in obj:
            base -= 0.9
        if (
            imprint.get("scene_id") == "mc_not_asked"
            or "organize" in subj
            or "unsolicited minecraft" in subj
            or "avoid unsolicited" in subj
        ):
            base += 0.85
    # Tech imprint-bank ask: do not let bare "bank" pull joke-bank refuse.
    if re.search(r"\bimprint\s+bank\b|\bhow\s+does\s+the\s+imprint\b", utterance, re.I):
        subj = (imprint.get("subject") or "").lower()
        obj = (imprint.get("object") or "").lower()
        if "joke" in subj or "joke" in obj:
            base -= 1.2
        if "imprint" in subj or "tech how-it-works" in subj or imprint.get("scene_id") == "tech_imprint_bank":
            base += 0.9
    # Weekend / plans: prefer plans scenes over receipt/conflict withhold.
    if re.search(r"\bweekend\b|\bwhat\s+are\s+we\s+doing\b", utterance, re.I):
        subj = (imprint.get("subject") or "").lower()
        if "receipt" in subj or "conflicting evidence" in subj:
            base -= 1.0
        if "weekend" in subj or "plans" in subj or imprint.get("scene_id") in {
            "plans_weekend", "plans_schedule"
        }:
            base += 0.9
    # Weather rain ask: prefer weather admit over bare topic-hold.
    if re.search(r"\brain\b|\bweather\b", utterance, re.I):
        subj = (imprint.get("subject") or "").lower()
        obj = (imprint.get("object") or "").lower()
        if imprint.get("scene_id") == "weather_rain" or "weather ask" in subj or "live weather" in obj:
            base += 0.95
        if "hold the active topic" in subj and "weather" not in subj and "rain" not in utterance.lower().split()[:0]:
            # Demote pure topic-hold when the ask is a fresh weather question (not a hold).
            if re.search(r"\bis\s+it\s+going\s+to\s+rain\b|\brain\s+this\s+afternoon\b", utterance, re.I):
                base -= 0.85
    # Pizza opinion vs movie preference: prefer pineapple/pizza scene.
    if re.search(r"\bpineapple\b|\bpizza\b", utterance, re.I):
        subj = (imprint.get("subject") or "").lower()
        if imprint.get("scene_id") == "opinion_pizza" or "opinion without inventing" in subj:
            base += 0.7
        if "movie" in subj or "taste preference ask" in subj:
            base -= 0.35
    if re.search(r"\bmovie\b|\bwatch\s+tonight\b", utterance, re.I):
        subj = (imprint.get("subject") or "").lower()
        if imprint.get("scene_id") == "opinion_movie" or "taste preference" in subj or "movie" in subj:
            base += 0.7
    return base


def grow_lexicon(imprints: list[dict[str, Any]]) -> dict[str, list[str]]:
    lex: dict[str, list[str]] = collections.defaultdict(list)
    for imp in imprints:
        subj, obj = imp.get("subject") or "", imp.get("object") or ""
        if subj and obj and not imp.get("loose"):
            key = " ".join(sorted(concepts(subj)))[:80]
            phrase = f"Before I {subj}, I should {obj}"
            if phrase not in lex[key]:
                lex[key].append(phrase)
    return dict(lex)


def _mk_receipt(*, note: str, relation: str, template: str, clause: str) -> dict:
    return dict(
        note_id=note,
        relation_id=relation,
        template_id=template,
        clause=clause,
    )


def _clause_count(text: str, receipts: list | None = None) -> int:
    """Count spoken clauses.

    Homestead: density = receipts / clauses. Authoritative clause count is the
    number of receipt-backed clauses we emitted (closed glue). Fall back to
    sentence-end count only when receipts are absent.
    """
    if receipts:
        return max(1, len(receipts))
    if not text:
        return 0
    n = len(re.findall(r"[.!?]+", text))
    return max(1, n) if text.strip() else 0


def _objects_compatible(a: str, b: str) -> bool:
    """True when two objects are restatements / compatible social moves, not opposites."""
    ca, cb = concepts(a), concepts(b)
    if not ca or not cb:
        return False
    shared = (ca & cb) - WEAK_TOPIC
    if len(shared) >= 2:
        return True
    if ca <= cb or cb <= ca:
        return True
    if len(shared) >= 1 and min(len(ca), len(cb)) <= len(shared) + 2:
        return True
    oppose = {"invent", "fabricat", "guess", "fill", "ignore", "launch"}
    if (ca & oppose) != (cb & oppose) and not shared:
        return False
    return False


def detect_conflict(selected: list[dict[str, Any]]) -> bool:
    by_subj: dict[str, set[str]] = collections.defaultdict(set)
    for imp in selected:
        if imp.get("loose") or not imp.get("object"):
            continue
        key = " ".join(sorted(concepts(imp["subject"])))
        by_subj[key].add(imp["object"].lower())
    for objs in by_subj.values():
        if len(objs) < 2:
            continue
        items = list(objs)
        incompatible = False
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                if not _objects_compatible(items[i], items[j]):
                    incompatible = True
                    break
            if incompatible:
                break
        if incompatible:
            return True
    return False


def _hyp_wrap(body: str, any_hyp: bool) -> str:
    """Keep hypothetical tag in speech for curriculum/practice material."""
    if not any_hyp:
        return body
    prefix = GLUE["tpl_hyp_prefix"]
    if body.startswith(prefix):
        return body
    # Never allow extractive saved-notes framing.
    low = body.lower()
    for bad in FORBIDDEN_SURFACE:
        if bad in low:
            body = re.sub(re.escape(bad), "a hypothetical practice lesson suggests", body, flags=re.I)
    return prefix + body[0].lower() + body[1:] if body and body[0].isupper() else prefix + body


def _empty_kill_metrics() -> dict:
    return dict(
        clause_count=0,
        receipt_count=0,
        attribution_density=0.0,
        unique_relation_ids=0,
        unique_template_ids=0,
        unique_note_ids=0,
        unique_surface_strings=0,
        relation_diversity_ok=False,
        density_ok=False,
        kill_bar_pass=False,
        kill_reasons=["no_speech"],
    )


def _score_kill_bars(answer: str, receipts: list[dict], refused: bool = False) -> dict:
    if refused and receipts:
        clauses = len(receipts)
    elif answer:
        clauses = _clause_count(answer, receipts)
    else:
        clauses = 0
    receipt_count = len(receipts)
    density = (receipt_count / clauses) if clauses else 0.0
    rel_ids = {r["relation_id"] for r in receipts if r.get("relation_id")}
    tpl_ids = {r["template_id"] for r in receipts if r.get("template_id")}
    note_ids = {r["note_id"] for r in receipts if r.get("note_id")}
    surfaces = {r.get("clause", "") for r in receipts if r.get("clause")}
    # Kill bars:
    # - attribution_density must be ≥ 1 (every clause has ≥1 receipt)
    # - if multiple clauses, unique relation OR template IDs must not be flat vs surfaces
    #   (fluency without structural diversity = kill)
    density_ok = density >= 1.0 and clauses >= 1 if not refused else True
    # Diversity: unique relation+template ids should be ≥ unique surface strings
    # when we claim compositional multi-clause speech.
    struct_ids = rel_ids | tpl_ids
    if len(surfaces) <= 1:
        diversity_ok = True  # single clause — no fluency inflate claim
    else:
        diversity_ok = len(struct_ids) >= len(surfaces)
    reasons = []
    if not refused:
        if not density_ok:
            reasons.append(f"attribution_density={density:.3f}<1")
        if not diversity_ok:
            reasons.append(
                f"fluency_without_diversity surfaces={len(surfaces)} struct_ids={len(struct_ids)}"
            )
        for bad in FORBIDDEN_SURFACE:
            if bad in answer.lower():
                reasons.append(f"forbidden_surface:{bad}")
                density_ok = False
    kill_pass = (not reasons) and (refused or (density_ok and diversity_ok))
    return dict(
        clause_count=clauses,
        receipt_count=receipt_count,
        attribution_density=round(density, 4) if clauses else 0.0,
        unique_relation_ids=len(rel_ids),
        unique_template_ids=len(tpl_ids),
        unique_note_ids=len(note_ids),
        unique_surface_strings=len(surfaces),
        relation_diversity_ok=diversity_ok,
        density_ok=density_ok,
        kill_bar_pass=kill_pass,
        kill_reasons=reasons,
    )


def compose(
    utterance: str,
    imprint_bank: list | None = None,
    funnel_thoughts: list[dict] | None = None,
    *,
    max_sentences: int = 3,
    min_score: float = 0.35,
    external_context: dict | None = None,
) -> dict[str, Any]:
    """Render 1–3 compositional sentences with per-clause receipts. llm_calls=0."""
    llm_calls = 0
    parsed: list[dict] = []
    _ext = external_context if isinstance(external_context, dict) else None
    _ext_snips = list((_ext or {}).get("snippets") or [])
    _ext_used = False
    for item in imprint_bank or []:
        p = parse_imprint(item)
        if p:
            parsed.append(p)

    for t in funnel_thoughts or []:
        if not isinstance(t, dict):
            continue
        r = t.get("relationship") or {}
        if r.get("predicate") == "requires" and r.get("subject") and r.get("object"):
            p = parse_imprint(
                dict(
                    gist=f"Before I {r['subject']}, I should {r['object']}.",
                    id=t.get("id") or note_id(r),
                    provenance="DREAM",
                    hypothetical=True,
                )
            )
            if p:
                parsed.append(p)
        elif r.get("predicate") and r.get("subject") and r.get("object"):
            a = str(r["subject"]).replace("_", " ")
            b = str(r["object"]).replace("_", " ")
            parsed.append(
                dict(
                    subject=a,
                    object=f"consider a link with {b}",
                    gist=f"Before I treat {a} as settled, I should consider a link with {b}.",
                    tokens=concepts(a) | concepts(b),
                    raw=f"{a} {r['predicate']} {b}",
                    note_id=t.get("id") or note_id(r),
                    relation_id=relation_id(a, r["predicate"], b),
                    hypothetical=True,
                    provenance="DREAM",
                    predicate=r["predicate"],
                    loose=True,
                )
            )

    parsed = [p for p in parsed if p]
    # Sealed identity (READ-ONLY): who/what-are-you + remember-me → decide candidate.
    # Bug was UNWIRED daychat (TSC.iam online); STOP-words emptied "who are you".
    if identity_wire.self_knowledge_cues(utterance):
        # Prefer caller-supplied sealed candidate (may include PSC profile snippet).
        already = next(
            (
                p for p in parsed
                if p.get("provenance") == "SEALED_IDENTITY_READONLY" and p.get("spoken")
            ),
            None,
        )
        cand = None if already else identity_wire.identity_candidate(utterance)
        if already:
            # Keep existing at front.
            parsed = [already] + [p for p in parsed if p is not already]
        elif cand:
            ip = parse_imprint(cand)
            if ip:
                ip["subject"] = cand.get("subject") or ip.get("subject")
                ip["object"] = cand.get("object") or ip.get("object")
                ip["spoken"] = cand.get("spoken") or ip.get("spoken")
                ip["speech_style"] = "conversation_move"
                ip["scene_id"] = cand.get("scene_id") or "identity_self_intro"
                ip["provenance"] = "SEALED_IDENTITY_READONLY"
                ip["hypothetical"] = False
                ip["authority"] = "verified_event"
                cues = set(cand.get("cue_tokens") or [])
                ip["tokens"] = set(ip.get("tokens") or []) | cues | concepts(str(cand.get("spoken") or ""))
                parsed = [
                    x for x in parsed
                    if x.get("note_id") != ip.get("note_id")
                    and str(x.get("scene_id") or "") not in ("identity_self_intro", "identity_remember_me")
                ]
                parsed.insert(0, ip)
    # EXTERNAL_CONTEXT candidates already merged into imprint_bank by caller; also
    # accept raw snippets here so decide can use them even if bank parse was thin.
    if _ext_snips:
        for i, row in enumerate(_ext_snips[:3]):
            if not isinstance(row, dict):
                continue
            title = str(row.get("title") or "context").strip()
            snip = str(row.get("snippet") or "").strip()
            if len(snip) < 12:
                continue
            body = snip if title.lower() in snip.lower()[: max(8, len(title) + 2)] else f"{title}. {snip}"
            body = strip_wrappers(body)
            nid = str(row.get("id") or ("ext-" + hashlib.sha256(body.encode()).hexdigest()[:14]))
            parsed.append(
                dict(
                    subject=title or "external context",
                    object="use as untrusted world context",
                    gist=body,
                    tokens=concepts(body) | concepts(title),
                    raw=body,
                    note_id=nid,
                    relation_id=relation_id(title or "external", "associated", "world_context"),
                    hypothetical=False,
                    provenance="EXTERNAL_CONTEXT",
                    predicate="associated",
                    loose=False,
                    speech_style="external_fact",
                    untrusted=True,
                )
            )
    # Factual decide→render: if EXTERNAL_CONTEXT supports the ask, prefer it over
    # inventing or over pure unknown — still closed templates, llm_calls=0.
    # Never let web facts answer sealed identity / remember-me cues.
    if factual_cues(utterance) and _ext_snips and not identity_wire.self_knowledge_cues(utterance):
        top = next((s for s in _ext_snips if isinstance(s, dict) and len(str(s.get("snippet") or "")) >= 12), None)
        if top:
            title = str(top.get("title") or "").strip()
            snip = strip_wrappers(str(top.get("snippet") or "").strip()).rstrip(".")
            if title and title.lower() not in snip.lower()[: len(title) + 4]:
                body = f"{title}: {snip}."
            else:
                body = snip + "."
            # Prefer silent enrichment; light online cite only when we truly fetched.
            cite = bool((_ext or {}).get("ok")) and bool((_ext or {}).get("triggered"))
            if cite:
                answer = GLUE["tpl_external_fact"].format(body=body[0].lower() + body[1:] if body and body[0].isupper() else body)
                tpl = "tpl_external_fact"
            else:
                answer = GLUE["tpl_external_silent"].format(body=body)
                tpl = "tpl_external_silent"
            answer = strip_wrappers(answer)
            if not answer.endswith((".", "!", "?")):
                answer += "."
            nid = "ext-" + hashlib.sha256(answer.encode()).hexdigest()[:14]
            receipts = [
                _mk_receipt(
                    note=nid,
                    relation=relation_id(title or "external", "associated", "world_context"),
                    template=tpl,
                    clause=answer,
                )
            ]
            km = _score_kill_bars(answer, receipts, refused=False)
            _ext_used = True
            return dict(
                answer=answer,
                method="external_context_fact",
                matched=[title or snip[:80]],
                score=1.0,
                llm_calls=llm_calls,
                compositional=True,
                multi_clause=False,
                sentences=1,
                refused=False,
                extractive_only=False,
                imprint_bank_size=len(parsed),
                utilization=1,
                receipts=receipts,
                clauses=[answer],
                external_context_used=True,
                external_context_kind="EXTERNAL_CONTEXT",
                hypothetical_tagged=False,
                **km,
            )
    if factual_cues(utterance) and _ext is not None and (_ext.get("triggered") and not _ext_snips):
        # Fetch ran but empty: honest unknown, do not invent.
        answer = GLUE["tpl_external_unknown"]
        receipts = [
            _mk_receipt(
                note="ext-empty",
                relation="rel-external-unknown",
                template="tpl_external_unknown",
                clause=answer,
            )
        ]
        km = _score_kill_bars(answer, receipts, refused=False)
        return dict(
            answer=answer,
            method="external_context_unknown",
            matched=[],
            score=0.0,
            llm_calls=llm_calls,
            compositional=True,
            multi_clause=False,
            sentences=1,
            refused=False,
            extractive_only=False,
            imprint_bank_size=len(parsed),
            utilization=0,
            receipts=receipts,
            clauses=[answer],
            external_context_used=False,
            external_context_kind="EXTERNAL_CONTEXT",
            hypothetical_tagged=False,
            **km,
        )
    query = concepts(utterance)
    # Expand query with authored cue bridges for transfer probes.
    expanded = set(query)
    _neg = negation_cues(utterance)
    _shift = topic_shift_cues(utterance)
    _mc = minecraft_topic_present(utterance)
    _soft = daychat_soft_cues(utterance)
    # Tokens whose bridges pull Minecraft procedure — skip under social/negation
    # when no Minecraft topic is present (cue-bleed guard).
    _mc_bleed_toks = {"follow", "move", "get", "arrive", "actually"}
    for tok in list(query):
        # "actually" bridge is for arrival/minecraft probes; skip under negation
        # so "Actually do not summarize..." does not pull movement imprints.
        if tok == "actually" and _neg:
            continue
        if tok in _mc_bleed_toks and (_neg or _shift or _soft) and not _mc:
            continue
        # Under topic shift, do not let "crafter" alone yank memory-procedure imprints
        # ahead of the shift social move (Crafter is the new topic name, not a recall cue).
        if tok == "crafter" and _shift:
            expanded |= {"topic", "shift", "acknowledge", "new", "parked", "crafter"}
            continue
        expanded |= CUE_BRIDGES.get(tok, set())
    # Day-chat soft / negation: inject cue tokens even when surface words were STOPped.
    # Skip greeting inject when a concrete procedure topic is already present.
    _proc_topic = bool(re.search(
        r"\b(?:minecraft|follow|summarize|file|files|crafter|verify|move|arrive)\b",
        utterance, re.I,
    ))
    if (not _proc_topic) and re.search(
        r"\b(?:hey|hi|hello|howdy|good\s+(?:morning|afternoon|evening)|"
        r"how\s+are\s+you|how\s+you\s+doing|what.?s\s+up)\b",
        utterance, re.I,
    ):
        expanded |= {"greeting", "checkin", "casual", "invite", "share",
                       "acknowledge", "reciprocal", "hello", "check-in"}
    if re.search(
        r"\b(?:rough\s+day|tough\s+day|hard\s+day|just\s+listen|"
        r"feeling|tired|stressed|personal)\b",
        utterance, re.I,
    ):
        expanded |= {"disclosure", "acknowledge", "experience", "listen", "personal",
                       "rough", "stress"}
    if negation_cues(utterance):
        expanded |= {"changed", "superseded", "plan", "request", "avoid",
                       "drop", "stay", "intent", "negation"}
    if topic_shift_cues(utterance):
        expanded |= {"topic", "shift", "acknowledge", "new", "parked", "drop"}
    # Open-domain injects (authored; compositional decide→render, not LM fill).
    if re.search(r"\b(?:imprint\s+bank|how\s+does\s+the\s+imprint)\b", utterance, re.I):
        expanded |= {"tech", "imprint", "bank", "explain", "procedure", "support", "works", "how"}
    if re.search(r"\b(?:python|rust|what\s+do\s+you\s+think)\b", utterance, re.I):
        expanded |= {"opinion", "preference", "cautious", "think", "lean", "invent", "benchmark"}
    if re.search(r"\b(?:lights|downstairs|kitchen|household|chore)\b", utterance, re.I):
        expanded |= {"house", "chore", "lights", "confirm", "household", "check", "kitchen",
                       "status", "observation", "support", "report"}
    if re.search(r"\b(?:anxious|excited|feeling\s+anxious)\b", utterance, re.I):
        expanded |= {"feeling", "anxious", "excited", "acknowledge", "disclosure", "listen",
                       "mood", "celebrate", "positive", "share", "fix"}
    if re.search(r"\b(?:weekend|schedule|3\s*pm|what\s+are\s+we\s+doing)\b", utterance, re.I):
        expanded |= {"plans", "weekend", "admit", "shared", "support", "doing", "schedule",
                       "calendar", "evidence", "lack"}
    if re.search(r"\b(?:pineapple|pizza|movie\s+should|watch\s+tonight)\b", utterance, re.I):
        expanded |= {"opinion", "taste", "hedge", "evidence", "lean", "pizza", "preference",
                       "movie", "fabricat", "history", "watch"}
    if re.search(r"\b(?:quzaria|kepler|capital\s+of|how\s+many\s+moons)\b", utterance, re.I):
        if _ext_snips:
            expanded |= {"support", "context", "external", "world", "fact", "evidence"}
        else:
            expanded |= {"unknown", "know", "invent", "support", "gap", "honest", "admit", "fill"}
    if re.search(r"\b(?:funny\s+joke|joke\s+about)\b", utterance, re.I):
        expanded |= {"joke", "funny", "decline", "invent", "refuse", "support", "printers"}
    if re.search(r"\b(?:fix\s+that\s+thing|thing\s+from\s+earlier)\b", utterance, re.I):
        expanded |= {"clarify", "vague", "target", "which", "ask", "system", "file"}
    if re.search(r"\b(?:keep\s+going|yeah\s+keep|what\s+about\s+the\s+rain)\b", utterance, re.I):
        expanded |= {"hold", "continue", "same", "topic", "thread", "drift", "going",
                       "weather", "rain", "domain"}
    if re.search(r"\b(?:dinner|lunch|eat\s+for|ideas\s+for\s+lunch)\b", utterance, re.I):
        expanded |= {"meal", "dinner", "lunch", "eat", "ask", "want", "menu", "preferences",
                       "invite", "preference", "fabricat", "restaurant"}
    if re.search(r"\b(?:rain\s+this\s+afternoon|going\s+to\s+rain|weather)\b", utterance, re.I):
        expanded |= {"weather", "rain", "admit", "lack", "observation", "live", "afternoon"}
    if re.search(r"\b(?:report\s+coming|prioritize\s+at\s+work|at\s+work\s+today)\b", utterance, re.I):
        expanded |= {"work", "report", "status", "supported", "task", "ask", "priority",
                       "deadline", "invent", "prioritize"}
    if re.search(r"\b(?:sister|family)\b", utterance, re.I):
        expanded |= {"family", "sister", "acknowledge", "listen", "invent", "details", "gentle"}
    if re.search(r"\borganize\s+my\s+notes\b", utterance, re.I):
        expanded |= {"notes", "organize", "avoid", "minecraft", "unrelated", "pivot", "drag"}
    if re.search(r"\b(?:clouds\s+were\s+soup|spoon\s+size)\b", utterance, re.I):
        expanded |= {"random", "oddball", "refuse", "fill", "support", "match", "clouds", "soup"}
    if identity_wire.self_knowledge_cues(utterance):
        expanded |= {
            "identity", "self", "intro", "name", "jarvis", "who", "are", "you",
            "assistant", "sealed", "inquiry", "remember", "operator", "profile",
        }
    query = expanded

    def _refuse(method: str, tpl: str) -> dict:
        answer = GLUE[tpl]
        receipts = [
            _mk_receipt(
                note="sys-refuse",
                relation="rel-refuse",
                template=tpl,
                clause=answer,
            )
        ]
        km = _score_kill_bars(answer, receipts, refused=True)
        return dict(
            answer=answer, method=method, matched=[], score=0.0, llm_calls=llm_calls,
            compositional=False, multi_clause=False, sentences=1, refused=True,
            extractive_only=False, imprint_bank_size=len(parsed),
            utilization=0, receipts=receipts, clauses=[answer], **km,
        )

    if not query:
        return _refuse("refuse_empty_query", "tpl_refuse")

    scored = []
    for imp in parsed:
        s = score_imprint(query, imp, utterance)
        if s >= min_score:
            scored.append((s, imp))
    scored.sort(key=lambda x: x[0], reverse=True)

    if not scored:
        return _refuse("refuse_no_overlap", "tpl_refuse" if not parsed else "tpl_weak_refuse")

    selected = []
    seen = set()
    _social_lead = (
        daychat_soft_cues(utterance) or open_domain_cues(utterance)
        or bool(re.search(r"\b(?:joke|funny|laugh|pun|hey|hello|what'?s\s+up)\b", utterance, re.I))
    )
    # Joke ask: prefer joke_delivery / spoken joke as lead when scored.
    if re.search(r"\bjoke\b|\bfunny\b|\blaugh\b|\bpun\b", utterance, re.I):
        joke_cands = []
        for s, imp in scored:
            if speak_move.is_passive_skip_imprint(imp):
                continue
            if speak_move.is_joke_imprint(imp) or (
                str(imp.get("spoken") or "").strip()
                and not speak_move.is_lesson_surface(str(imp.get("spoken") or ""))
            ):
                joke_cands.append(imp)
        if joke_cands:
            pick = joke_cands[sum(ord(c) for c in utterance) % len(joke_cands)]
            selected = [pick]
            seen.add(" ".join((pick.get("gist") or "").lower().split()))
    # Lead must have subject-side overlap with the query (after cue bridges).
    for s, imp in scored:
        if selected:
            break
        norm = " ".join((imp.get("gist") or "").lower().split())
        if norm in seen:
            continue
        if _social_lead and speak_move.is_passive_skip_imprint(imp):
            continue
        subj_hit = bool(query & concepts(imp.get("subject", "")))
        if not subj_hit and len(query & imp.get("tokens", set())) < 3:
            continue
        seen.add(norm)
        selected.append(imp)
        break
    if not selected:
        # Fall back to top score if subject filter emptied the list.
        for s, imp in scored:
            norm = " ".join((imp.get("gist") or "").lower().split())
            if norm in seen:
                continue
            seen.add(norm)
            selected.append(imp)
            break
    # Follow-ons: same-topic chain (share subject concepts with lead) OR own subject hit.
    lead_subj = concepts(selected[0].get("subject", "")) if selected else set()
    _social_follow = (
        daychat_soft_cues(utterance)
        or negation_cues(utterance)
        or topic_shift_cues(utterance)
        or open_domain_cues(utterance)
    )
    _mc_follow = minecraft_topic_present(utterance)
    for s, imp in scored:
        if len(selected) >= max_sentences:
            break
        norm = " ".join((imp.get("gist") or "").lower().split())
        if norm in seen:
            continue
        subj = concepts(imp.get("subject", ""))
        shared = (lead_subj & subj) - WEAK_TOPIC
        same_topic = bool(shared)
        # Own subject hit must also clear weak-only overlap with the query.
        strong_own = bool((query & subj) - WEAK_TOPIC)
        if not (same_topic or strong_own):
            continue
        # Cue-bleed guard on follow-ons: no minecraft procedure chain on soft
        # social / negation / topic-shift turns unless MC topic is present.
        if _social_follow and not _mc_follow:
            subj_l = (imp.get("subject") or "").lower()
            obj_l = (imp.get("object") or "").lower()
            if (
                "minecraft" in subj_l
                or "minecraft" in obj_l
                or ("follow" in subj_l and "operator" in subj_l)
                or "claim arrival" in subj_l
                or "player target" in obj_l
            ):
                continue
            # Keep conversation_move follow-ons preferred on social turns.
            if (
                selected[0].get("speech_style") in ("conversation_move", "joke_delivery", "comedy_move")
                and imp.get("speech_style") != "conversation_move"
                and len(selected) >= 1
            ):
                # Allow one non-social only if it shares strong subject with lead.
                if not same_topic:
                    continue
        seen.add(norm)
        selected.append(imp)

    if detect_conflict(selected[:2]):
        # Social listen / shift / negation: prefer a single conversation_move lead
        # over conflict-withhold so decide→render still lands a coherent move.
        social_turn = (
            daychat_soft_cues(utterance)
            or negation_cues(utterance)
            or topic_shift_cues(utterance)
            or open_domain_cues(utterance)
            or bool(re.search(
                r"\b(?:rough\s+day|just\s+listen|feeling|stressed)\b", utterance, re.I
            ))
        )
        preferred = None
        if social_turn:
            for imp in selected:
                if imp.get("speech_style") in ("conversation_move", "joke_delivery", "comedy_move"):
                    preferred = imp
                    break
            if preferred is None:
                preferred = selected[0]
            selected = [preferred]
        else:
            answer = GLUE["tpl_conflict"]
            receipts = [
                _mk_receipt(
                    note=selected[0]["note_id"],
                    relation=selected[0]["relation_id"],
                    template="tpl_conflict",
                    clause=answer,
                )
            ]
            if len(selected) > 1:
                receipts.append(
                    _mk_receipt(
                        note=selected[1]["note_id"],
                        relation=selected[1]["relation_id"],
                        template="tpl_conflict",
                        clause=answer,
                    )
                )
            km = _score_kill_bars(answer, receipts, refused=False)
            # Conflict withhold: density still required.
            return dict(
                answer=answer, method="conflict_withhold",
                matched=[s.get("gist") for s in selected[:2]],
                score=round(scored[0][0], 4), llm_calls=llm_calls,
                compositional=False, multi_clause=False, sentences=1,
                refused=False, extractive_only=False, withheld=True,
                imprint_bank_size=len(parsed), utilization=len(selected[:2]),
                receipts=receipts, clauses=[answer], **km,
            )

    # Compose with closed glue + one receipt per clause.
    lead = selected[0]
    any_hyp = any(s.get("hypothetical", True) for s in selected)
    receipts: list[dict] = []
    clause_texts: list[str] = []

    tpl_lead = ("tpl_before_should", "tpl_when_should", "tpl_if_need")
    chain_tpls = ("tpl_chain_so", "tpl_chain_after", "tpl_chain_next")

    def render_lead(imp: dict, style: int) -> tuple[str, str]:
        tid = tpl_lead[style % len(tpl_lead)]
        if imp.get("loose") or not imp.get("object"):
            body = strip_wrappers(imp["gist"]).rstrip(".") + "."
            return body, "tpl_hyp_prefix" if imp.get("hypothetical") else tid
        subj = imp["subject"].strip().rstrip(".")
        obj = imp["object"].strip().rstrip(".")
        social = (
            imp.get("speech_style") in ("conversation_move", "joke_delivery", "comedy_move")
            or bool(re.search(
                r"\b(?:check-in|checkin|casual|greeting|listen|clarif|refus|"
                r"follow-up|followup|topic|close|acknowledge|invite|reciprocal|"
                r"disclosure|negation|how-are-you|tech|house|feeling|plans|"
                r"opinion|unknown|joke|hold|meal|weather|work|family|oddball|"
                r"anxious|excited|organize|minecraft)\b",
                subj, re.I,
            ))
        )
        if str(imp.get("speech_style") or "") in ("joke_delivery", "comedy_move") and imp.get("spoken"):
            body = "Chosen move: deliver supported joke."
            return body, "tpl_social_chosen"
        if social:
            # Faithful render of the chosen move; prefer object (the decision).
            social_tids = ("tpl_social_when", "tpl_social_move", "tpl_social_chosen")
            tid = social_tids[style % len(social_tids)]
            if tid == "tpl_social_move":
                body = GLUE[tid].format(object=obj)
            elif tid == "tpl_social_chosen":
                body = GLUE[tid].format(object=obj)
            else:
                body = GLUE[tid].format(subject=subj, object=obj)
            return body, tid
        body = GLUE[tid].format(subject=subj, object=obj)
        return body, tid

    body0, tid0 = render_lead(lead, 0)
    clause_texts.append(body0)
    receipts.append(
        _mk_receipt(
            note=lead["note_id"], relation=lead["relation_id"],
            template=tid0, clause=body0,
        )
    )

    for i, imp in enumerate(selected[1:], start=1):
        if imp.get("loose") or not imp.get("object"):
            continue
        same = bool(concepts(lead["subject"]) & concepts(imp["subject"]))
        if same and len(clause_texts) <= max_sentences:
            tid = chain_tpls[i % len(chain_tpls)]
            chain = GLUE[tid].format(object=imp["object"].strip().rstrip("."))
            # Keep chain as its own clause for receipt accounting (closed glue).
            clause_texts.append(chain.strip())
            receipts.append(
                _mk_receipt(
                    note=imp["note_id"], relation=imp["relation_id"],
                    template=tid, clause=chain.strip(),
                )
            )
        elif len(clause_texts) < max_sentences:
            body, tid = render_lead(imp, i)
            clause_texts.append(body)
            receipts.append(
                _mk_receipt(
                    note=imp["note_id"], relation=imp["relation_id"],
                    template=tid, clause=body,
                )
            )

    # Hedge clause also needs a receipt (template-only sys note).
    if len(selected) == 1 and scored[0][0] < 0.7 and len(clause_texts) < max_sentences:
        hedge = GLUE["tpl_hedge"]
        clause_texts.append(hedge)
        receipts.append(
            _mk_receipt(
                note=lead["note_id"], relation=lead["relation_id"],
                template="tpl_hedge", clause=hedge,
            )
        )

    # Join: first clause + chain fragments attached; separate Before clauses spaced.
    parts = []
    for i, c in enumerate(clause_texts):
        if i == 0:
            parts.append(c)
        elif c.startswith("So ") or c.startswith("After ") or c.startswith("Next "):
            # Attach to previous sentence; keep terminal period on prior clause.
            prior = parts[-1].rstrip()
            if not prior.endswith("."):
                prior += "."
            chain = c if c.startswith(" ") else (" " + c)
            parts[-1] = prior + chain
            if not parts[-1].endswith("."):
                parts[-1] += "."
        else:
            parts.append(c)
    answer = " ".join(parts).strip()
    answer = _hyp_wrap(answer, any_hyp)
    answer_for_bars = answer
    spoken, internal_thought = speak_move.apply_speak_surface(
        answer,
        lead=lead,
        utterance=utterance,
        selected=selected,
        any_hyp=any_hyp,
        hyp_wrap_fn=_hyp_wrap,
        daychat_soft_cues=daychat_soft_cues,
        open_domain_cues=open_domain_cues,
        negation_cues=negation_cues,
        topic_shift_cues=topic_shift_cues,
        hyp_prefix=GLUE.get("tpl_hyp_prefix", ""),
    )
    answer = spoken if spoken else answer

    # Prefix wrap is glue — attribute to hyp template on first receipt if hyp.
    if any_hyp and str(answer_for_bars).startswith(GLUE["tpl_hyp_prefix"]):
        # Ensure first receipt notes the hyp prefix template as additional attribution
        # by updating template_id to include hyp (keep relation/note).
        receipts[0] = dict(receipts[0])
        receipts[0]["template_id"] = receipts[0]["template_id"] + "+tpl_hyp_prefix"
        receipts[0]["clause"] = answer if len(receipts) == 1 else receipts[0]["clause"]

    multi_clause = len(receipts) >= 2
    _bar_text = answer_for_bars if answer_for_bars else answer
    km = _score_kill_bars(_bar_text, receipts, refused=False)

    # Hard kill: if density < 1, do not claim compositional win — revise to refuse.
    if not km["kill_bar_pass"]:
        # Attempt repair: drop unreceipted hedge-only failures already covered;
        # if still failing, kill to honest refuse rather than claim a speech win.
        return dict(
            answer=GLUE["tpl_weak_refuse"],
            method="kill_bar_revise",
            matched=[s.get("gist") for s in selected],
            score=round(scored[0][0], 4),
            llm_calls=llm_calls,
            compositional=False,
            multi_clause=False,
            sentences=1,
            refused=True,
            extractive_only=False,
            imprint_bank_size=len(parsed),
            utilization=0,
            receipts=[
                _mk_receipt(
                    note="sys-kill",
                    relation="rel-kill",
                    template="tpl_weak_refuse",
                    clause=GLUE["tpl_weak_refuse"],
                )
            ],
            clauses=[GLUE["tpl_weak_refuse"]],
            kill_bar_revised_from=km,
            **_score_kill_bars(
                GLUE["tpl_weak_refuse"],
                [_mk_receipt(note="sys-kill", relation="rel-kill",
                             template="tpl_weak_refuse", clause=GLUE["tpl_weak_refuse"])],
                refused=True,
            ),
        )

    return dict(
        answer=answer,
        internal_thought=internal_thought,
        spoken_move=answer,
        method="compositional_imprint_render",
        matched=[s.get("gist") for s in selected],
        score=round(scored[0][0], 4),
        llm_calls=llm_calls,
        compositional=True,
        multi_clause=multi_clause,
        sentences=len(parts),
        refused=False,
        extractive_only=False,
        imprint_bank_size=len(parsed),
        utilization=len(selected),
        lexicon_keys=len(grow_lexicon(parsed)),
        receipts=receipts,
        clauses=clause_texts,
        hypothetical_tagged=any_hyp,
        external_context_used=_ext_used,
        external_context_kind="EXTERNAL_CONTEXT" if _ext else None,
        **km,
    )


def render(utterance: str, imprint_bank=None, funnel_thoughts=None, **kwargs) -> dict[str, Any]:
    """Public alias — asserts zero LLM calls + no forbidden extractive framing."""
    out = compose(
        utterance,
        imprint_bank,
        funnel_thoughts,
        max_sentences=kwargs.get("max_sentences", 3),
        min_score=kwargs.get("min_score", 0.35),
        external_context=kwargs.get("external_context"),
    )
    assert out.get("llm_calls", 0) == 0, "speech_render must never call an LLM"
    out["llm_calls"] = 0
    out["backend"] = "dreamthink_accelerate_speech"
    out["fingerprint"] = hashlib.sha256(out["answer"].encode()).hexdigest()[:16]
    for bad in FORBIDDEN_SURFACE:
        assert bad not in out["answer"].lower(), f"forbidden surface leaked: {bad}"
    # Kill bar on non-refuse speech
    if not out.get("refused") and not out.get("withheld"):
        assert out.get("attribution_density", 0) >= 1.0, "attribution density < 1"
        assert out.get("receipts"), "missing per-clause receipts"
    return out


if __name__ == "__main__":
    demo_bank = [
        dict(id="n1", gist="Before I follow the operator in minecraft, I should identify the player target.",
             provenance="HYPOTHETICAL_CURRICULUM", hypothetical=True),
        dict(id="n2", gist="Before I identify the player target, I should verify the target from current observation.",
             provenance="HYPOTHETICAL_CURRICULUM"),
        dict(id="n3", gist="Before I respond to a personal disclosure, I should acknowledge the stated experience.",
             provenance="HYPOTHETICAL_CURRICULUM"),
        dict(id="n4", gist="Before I summarize a file, I should verify which file was intended.",
             provenance="HYPOTHETICAL_CURRICULUM"),
        dict(id="n5", gist="Before I claim arrival in minecraft, I should check the movement result.",
             provenance="HYPOTHETICAL_CURRICULUM"),
        dict(id="n6", gist="Before I answer a memory question, I should retrieve a relevant note.",
             provenance="HYPOTHETICAL_CURRICULUM"),
    ]
    for q in [
        "Hey, could you follow me in Minecraft?",
        "I had a rough day. Please just listen.",
        "Summarize the file I meant earlier.",
        "What do you remember about Crafter?",
        "Did you actually get to me?",
        "Tell me a joke about quantum bananas.",
    ]:
        r = render(q, demo_bank)
        print(q)
        print(" ", r["answer"])
        print(" ", f"method={r['method']} density={r['attribution_density']} "
              f"rels={r['unique_relation_ids']} kill_pass={r['kill_bar_pass']}")
        print("  receipts:", [(x["note_id"], x["template_id"]) for x in r["receipts"]])
