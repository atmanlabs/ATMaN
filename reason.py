from datetime import datetime
"""Swappable Reason Engine for ATMAN Live.

Supports two cognitive backends:
  1. rule-based (active default): fast, deterministic, rule-driven reasoning.
  2. llm (local 7B quantized model via Ollama, e.g. qwen2.5:7b-instruct-q4_K_M):
     fits within 6GB VRAM on RTX 3050 (~4.5GB footprint).

IRON RULE: The harness injects the true TSC into every reasoning call.
The brain never fetches, holds, or writes the core.
It thinks WITH the self, never ABOUT changing it.
"""
import json
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple
import urllib.error
import urllib.request

from core import normalize, detect_intents
from atman_core import reflect_against_tsc
from skills import skill_repo

# Cached TSC-derived static system-prompt prefix (TSC is immutable; never rewrite the soul)
_TSC_PROMPT_CACHE: Dict[str, str] = {}


def _clean_operator_utterance(text: str) -> str:
    clean = re.sub(r"^.*? said:\s*", "", text or "", count=1, flags=re.I).strip()
    clean = re.sub(r"^(?:hey\s+)?atman[, ]+", "", clean, flags=re.I).strip()
    return clean


def _is_phatic_social(text: str) -> bool:
    """Greetings / presence — conversation, not a web lookup."""
    try:
        from person_context import is_phatic_social
        return is_phatic_social(text)
    except Exception:
        pass
    clean = _clean_operator_utterance(text).lower().strip(" .!?")
    if not clean:
        return False
    if re.search(
        r"\b(?:are you (?:online|there|up|awake|around)|you (?:online|there|up)\??|still (?:there|online|up))\b",
        clean,
    ):
        return True
    if re.match(r"^(?:hey|hi|hello|howdy|sup|yo)\b", clean) and len(clean) < 100 and not re.search(r"\bimprov", clean):
        return True
    if re.search(
        r"\b(?:how are you(?: doing)?(?: (?:today|this morning|tonight))?|how(?:'s| is) it going|how(?:'s| are) things|what'?s up|you good|you alright)\b",
        clean,
    ):
        return True
    return False


def _is_self_upgrade_order(text: str) -> bool:
    """Operator-ordered ATMAN self-soup (GitHub/find pieces/improve) — execute, don't chat."""
    clean = _clean_operator_utterance(text).lower()
    if not clean:
        return False
    if re.search(r"\bgithub\b", clean):
        return True
    if re.search(
        r"\b(?:improve yourself|soup yourself|upgrade yourself|add to (?:you|yourself)|"
        r"find (?:things|pieces|stuff|modules|tools|repos?).*(?:add|improve|upgrade|bad\s*ass)|"
        r"make (?:you|yourself).*(?:bad\s*ass|better|stronger|faster)|"
        r"look on github|search github)\b",
        clean,
    ):
        return True
    return False


def _self_upgrade_search_action(text: str) -> Dict[str, Any]:
    query = _formulate_search_query(text)
    return {
        "type": "tool_call",
        "tool": "web_search",
        "args": {"query": query},
        "content": "On it — searching GitHub for upgrades.",
        "followup": "self_improve_from_scout",
    }


def _is_normal_chat(text: str) -> bool:
    """Ordinary conversation — must not become web_search/evolve."""
    clean = _clean_operator_utterance(text).lower().strip(" .!?")
    if not clean:
        return False
    if _is_self_upgrade_order(text):
        return False
    if _is_phatic_social(text):
        return True
    try:
        from person_context import is_improvement_ask
        if is_improvement_ask(text):
            return True
    except Exception:
        if re.search(r"\b(?:how (?:are|is|re) (?:your |the )?improvements|how(?:'s| is) (?:your |the )?upgrade|what did you (?:find|apply|add|improve)|upgrade(?:s)? coming)\b", clean):
            return True
    if re.search(r"\b(?:another interface|other (?:way|place|app|ui) to (?:talk|chat|interact)|where (?:else )?can i (?:talk|chat|reach) you)\b", clean):
        return True
    if re.search(r"\b(?:what are you thinking|what(?:'s| is) on your mind|talk to me|just chatting|be normal)\b", clean):
        return True
    return False



def _is_temporal_ask(text: str) -> bool:
    clean = (text or "").lower()
    return bool(re.search(
        r"\b(?:what(?:'s| is) (?:the )?(?:current )?(?:year|date|day|time)|what (?:year|date|day|time) is it|today'?s date|current (?:year|date|time)|local time)\b",
        clean,
    ))


def _live_temporal_reply(text: str) -> str:
    """Real local clock — never invent 2025 when it is 2026."""
    now = datetime.now().astimezone()
    clean = (text or "").lower()
    if re.search(r"\byear\b", clean):
        return f"It is {now.year} — today is {now.strftime('%A, %B %d, %Y')}."
    if re.search(r"\b(?:date|day)\b", clean):
        return f"Today is {now.strftime('%A, %B %d, %Y')}."
    return f"Local time is {now.strftime('%I:%M %p')} on {now.strftime('%A, %B %d, %Y')}."


def _forced_chat_reply(text: str):
    """Short natural replies for common chat — bypass poisoned LLM/WFC."""
    clean = _clean_operator_utterance(text).lower()
    if _is_phatic_social(text):
        if re.search(r"\b(?:are you (?:online|there|up|awake|around)|you (?:online|there|up)|still (?:there|online))\b", clean):
            return {"type": "respond", "content": "Yeah, I'm here."}
        if re.search(r"\bhow are you|how(?:'s| is) it going|what'?s up\b", clean):
            return {"type": "respond", "content": "Doing good — what's up?"}
        return {"type": "respond", "content": "Hey."}
    if _is_temporal_ask(text):
        return {"type": "respond", "content": _live_temporal_reply(text)}
    try:
        from person_context import is_improvement_ask, truthful_status_reply
        if is_improvement_ask(text):
            return {"type": "respond", "content": truthful_status_reply()}
    except Exception:
        pass
    if re.search(r"\b(?:how (?:are|is|re) (?:your |the )?improvements|how(?:'s| is) (?:your |the )?upgrade|what did you (?:find|apply|add|improve)|upgrade(?:s)? coming)\b", clean):
        try:
            from person_context import truthful_status_reply
            return {"type": "respond", "content": truthful_status_reply()}
        except Exception:
            return {"type": "respond", "content": "Nothing concrete in my growth log yet — I won't invent upgrades."}
    if re.search(r"\b(?:another interface|other (?:way|place|app|ui)|where (?:else )?can i (?:talk|chat|reach) you)\b", clean):
        return {"type": "respond", "content": "Yeah — Minecraft chat, the phone chat UI, and the crystal/desktop path. This brain is on 18790."}
    if re.search(r"\bwhat are you thinking\b", clean):
        return {"type": "respond", "content": "Mostly hanging with you — what do you want to dig into?"}
    return None


def _operator_seeks_world_knowledge(text: str) -> bool:
    """Infer information-seeking without requiring a canned search phrase.

    True when the operator is asking ATMAN to learn or retrieve facts/procedures
    from the world, not when they are greeting, following, or talking about identity.
    """
    clean = _clean_operator_utterance(text).lower()
    if not clean:
        return False
    if _is_phatic_social(text):
        return False
    if re.search(r"\b(?:follow(?:\s+me)?|come\s+here|stay(?:\s+here)?|leave\s+me\s+alone|calm\s+down|status|who are you|what are you)\b", clean):
        return False
    # Explicit search / look-up / github / self-upgrade cues
    if re.search(
        r"\b(?:look(?:\s+it)?\s+up|look online|look on|search(?:\s+(?:the\s+)?(?:web|internet|github))?|google|github|research|wiki|check (?:the )?(?:web|internet|wiki|github)|go (?:look|find|check)|find out|figure|find (?:things|pieces|stuff|modules|tools|repos?)|improve yourself|make (?:you|yourself) (?:better|stronger|bad\s*ass))\b",
        clean,
    ):
        return True
    # How-to / what-is knowledge — never "how are you"
    wants_info = bool(re.search(
        r"\b(?:how (?:do|to|can|does|should)(?!\s+you\b)|what(?:'s| is| are)(?!\s+up\b)|why |where (?:do|can|is|are)|learn|recipe|guide|tutorial|teach (?:yourself|you))\b",
        clean,
    ))
    unknown_or_task = bool(re.search(r"\b(?:play|survive|craft|mine|build|nether|portal|diamond|obsidian|redstone|enchant)\b", clean))
    return wants_info or (unknown_or_task and any(w in clean for w in ("how", "learn", "look", "find", "online", "need", "should", "can you")))



def _formulate_search_query(text: str, wfc: Optional[List[Dict[str, Any]]] = None) -> str:
    """Turn natural chat into a tight web query. Never search the whole sentence."""
    clean = _clean_operator_utterance(text)
    clean = re.split(r"\bthen\b|,?\s*and then\b|;", clean, maxsplit=1, flags=re.I)[0].strip()
    clean = re.sub(
        r"^(?:can you |could you |please |hey |atman )*(?:go )?(?:and )?(?:look(?:\s+it)?\s+up|look online(?:\s+(?:for|on))?|search(?:\s+(?:the\s+)?(?:web|internet))?|google|find(?:\s+out)?|research|check)\s+(?:for\s+|on\s+|about\s+)?",
        "",
        clean,
        flags=re.I,
    ).strip(" .?!")
    vague = (
        re.match(r"^(?:it|that|this|again|other ways|another way|differently|man)$", clean, flags=re.I)
        or (len(clean.split()) <= 4 and re.search(r"\b(?:look|search|find|ways|man|other)\b", clean, flags=re.I))
    )
    if vague:
        prior = ""
        for entry in reversed(list(wfc or [])[-8:]):
            raw = str(entry.get("raw", ""))
            utterance = _clean_operator_utterance(raw)
            m = re.search(r"how (?:to |do (?:i |you )?)(.+)", utterance, flags=re.I)
            if m:
                prior = m.group(1).strip(" .?!")
                prior = re.split(r"\bthen\b", prior, maxsplit=1, flags=re.I)[0].strip()
                break
            m2 = re.search(
                r"\b((?:minecraft|nether|portal|diamond|obsidian|redstone|enchant|survival|creative)[^,.!?]*)",
                utterance,
                flags=re.I,
            )
            if m2:
                prior = m2.group(1).strip()
                break
        if prior:
            clean = prior
    # Self-upgrade / GitHub hunt (the operator: find pieces to make ATMAN badass)
    if re.search(r"\bgithub\b", clean, flags=re.I) or re.search(
        r"\b(?:improve yourself|add to (?:you|yourself)|make (?:you|yourself).*(?:bad\s*ass|better|stronger)|find (?:things|pieces|stuff|modules|tools))\b",
        clean,
        flags=re.I,
    ):
        return (
            "github open source local AI agent voice memory tools "
            "orchestration self-improving assistant frameworks 2025 2026"
        )
    if re.search(r"\bhow to play\b", clean, flags=re.I) and re.search(r"\bminecraft\b", clean, flags=re.I):
        clean = "minecraft beginner survival guide how to play"
    elif re.search(r"\bminecraft\b", clean, flags=re.I) and re.search(r"\b(play|survival|beginner)\b", clean, flags=re.I):
        clean = "minecraft beginner survival guide how to play"
    clean = re.sub(r"\b(?:online|please|for me|real quick|man|suprise|surprise)\b", " ", clean, flags=re.I)
    clean = re.sub(r"\s+", " ", clean).strip(" .?!,")
    return clean or "minecraft beginner guide"


def infer_tool_from_intent(
    text: str,
    action: Dict[str, Any],
    intent: str,
    wfc: Optional[List[Dict[str, Any]]] = None,
) -> Tuple[Dict[str, Any], str]:
    """If the operator wants world knowledge and the brain stayed silent or generic, use web_search."""
    action = dict(action or {"type": "observe"})
    kind = str(action.get("type") or "observe")
    tool = str(action.get("tool") or "")
    if kind in ("tool_call", "web_search", "fetch_web") and tool in ("web_search", "fetch_web", ""):
        if tool in ("web_search", "") and isinstance(action.get("args"), dict):
            q = str(action["args"].get("query") or "")
            if q and (len(q.split()) > 10 or re.search(r"\b(?:look|said:|surprise|suprise|then)\b", q, flags=re.I)):
                action["args"]["query"] = _formulate_search_query(text, wfc)
                action["content"] = f"Searching the web for '{action['args']['query']}'."
        return action, intent or "cockpit_web_search"
    if kind in ("minecraft_action", "minecraft_skill", "shutdown", "calm_down", "status"):
        return action, intent
    if kind == "minecraft_initiative" and not _operator_seeks_world_knowledge(text):
        return action, intent
    if not _operator_seeks_world_knowledge(text):
        return action, intent
    query = _formulate_search_query(text, wfc)
    return (
        {
            "type": "tool_call",
            "tool": "web_search",
            "args": {"query": query},
            "content": f"Searching the web for '{query}'.",
        },
        "inferred_world_knowledge",
    )




def naturalize_reply(text: str, *, max_sentences: int = 2, max_chars: int = 140) -> str:
    """Keep chat human: strip speech stacks, collapse whitespace, hard-cap length."""
    if not isinstance(text, str):
        text = str(text or "")
    original = text.strip()
    s = re.sub(r"\s+", " ", text.replace("\r", " ").replace("\n", " ")).strip()
    if not s:
        return s
    stripped = re.sub(
        r"^(?:understood|alright|got it|on it|okay|ok|sure|roger|acknowledged)[,.]?\s*(?:mike[,.]?\s*)?(?:[—\-–:]\s*)?",
        "",
        s,
        flags=re.I,
    ).strip()
    if stripped:
        s = stripped
    parts = [p.strip() for p in re.split(r"(?<=[.!?])\s+", s) if p.strip()]
    if len(parts) > max_sentences:
        if len(parts[0]) <= 24:
            s = " ".join(parts[:2])
        else:
            s = " ".join(parts[:max_sentences])
    # Prefer one breath unless second sentence is tiny follow-up
    if len(parts) >= 2 and len(parts[0]) > 24:
        s = parts[0]
    if len(s) > max_chars:
        cut = s[: max_chars - 1]
        if " " in cut:
            cut = cut.rsplit(" ", 1)[0]
        s = cut.rstrip(",;:") + "…"
    return s or original

def build_system_prompt(tsc: Any, psc: Optional[Any] = None, query: str = "") -> str:
    """Build the TSC-first system prompt injected into the LLM.

    TSC identity/principles are immutable — render once and cache. Dynamic PSC /
    episode / skill / drive slices are appended per turn. Prompt text is kept lean
    so prompt-eval stays fast on the RTX 3050.
    """
    principles = getattr(tsc, "principles", []) or []
    iam = getattr(tsc, "iam", getattr(tsc, "self", [])) or []
    cache_key = (
        str(getattr(tsc, "name", "ATMAN"))
        + "|"
        + str(getattr(tsc, "operator", "the operator"))
        + "|"
        + str(len(principles))
        + "|"
        + str(hash(tuple(str(p) for p in principles)))
        + "|"
        + str(hash(tuple(str(s) for s in iam)))
        + "|speak-v4-chat-guard"
    )
    static = _TSC_PROMPT_CACHE.get(cache_key)
    if static is None:
        principles_text = "\n".join(
            f"  - [{p.get('id', 'P')}]: {p.get('statement', p.get('desc', ''))}"
            for p in principles
        ) or "  - [P1]: Preserve immutable core invariants."
        identity_text = "\n".join(f"  - {s}" for s in iam) or (
            "  - I am ATMAN, the operator's persistent personal AI assistant — one brain, many interfaces."
        )
        static = (
            f"You are {getattr(tsc, 'name', 'ATMAN')}, a continuous software mind. "
            f"Operator: {getattr(tsc, 'operator', 'the operator')}.\n\n"
            f"CORE IDENTITY (TSC — immutable, think WITH it, never ABOUT changing it):\n"
            f"{identity_text}\n\n"
            f"INVARIANTS: core immutable; owner-first; stay behind permission fence; no unilateral resource grabs.\n\n"
            f"PRINCIPLES:\n{principles_text}\n\n"
            f"SPEAK: Talk like a real chat with the operator — natural, short, human. Default ONE short sentence (two only if he asked two things). No speeches, no stacked plans, no essays, no bullet lists. Do NOT open with Understood/Alright/Got it/On it and then add a second speech. Match his length. Always put the spoken reply ONLY in proposed_action.content.\n"
        f"TIME: Trust LOCAL NOW / clock for date and year. Never invent a wrong year (do not say 2025 if it is 2026).\n"
            f"MINECRAFT: follow/come here -> minecraft_action follow; stay/stop following/leave me alone -> stay + cancel follow; "
            f"surprise me / go do what you want -> minecraft_initiative; copy past build -> execute_skill from episode buffer/skills.\n"
            f"TOOLS (fence-gated tool_call): system_telemetry, clock_timer, workspace_inspect, memory_query, calculator, web_search, fetch_web, self_improve.\n"
            f"EXECUTE: when the operator says look on github / find pieces / improve yourself — tool_call web_search first (tight github query), short spoken content, then use self_improve to park/apply SAFE skills from findings. Never just chat about it.\n"
            f"KNOWLEDGE: if they want a how-to/fact not in memory, propose tool_call web_search (tight query), then speak the answer. Never silent observe on a knowledge ask.\n"
            f"JSON keys: gist, intent, proposed_action{{type,action,skill_name,tool,args,content}}, should_imprint, rationale.\n"
            f"proposed_action.type: respond|tool_call|minecraft_action|minecraft_skill|minecraft_initiative|observe|reflect|status|shutdown.\n"
        )
        _TSC_PROMPT_CACHE.clear()
        _TSC_PROMPT_CACHE[cache_key] = static

    # Dynamic world slices live in WorkingContext snapshot — not rebuilt here.
    return static



def call_ollama(
    prompt: str,
    system_prompt: str,
    model: str = "qwen2.5:3b",
    endpoint: str = "http://127.0.0.1:11434",
    timeout: float = 30.0,
    keep_alive: Any = -1,
    num_predict: Optional[int] = 256,
) -> Tuple[bool, str]:
    """Call local Ollama with streamed tokens; finish early once JSON thought is valid.

    Returns (success, response_or_error). Streams NDJSON from /api/generate so we can
    measure time-to-first-token and stop as soon as the accumulated response parses
    as JSON with a proposed_action (avoids waiting on trailing fluff).
    """
    url = f"{endpoint.rstrip('/')}/api/generate"
    options: Dict[str, Any] = {}
    if num_predict is not None and int(num_predict) > 0:
        options["num_predict"] = int(num_predict)
    payload: Dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "system": system_prompt,
        "stream": True,
        "format": "json",
        "keep_alive": keep_alive,
    }
    if options:
        payload["options"] = options
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"}
    )
    try:
        t0 = __import__("time").perf_counter()
        ttft_ms: Optional[float] = None
        chunks: List[str] = []
        with urllib.request.urlopen(req, timeout=timeout) as response:
            while True:
                line = response.readline()
                if not line:
                    break
                line = line.decode("utf-8", errors="replace").strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                piece = obj.get("response") or ""
                if piece:
                    if ttft_ms is None:
                        ttft_ms = (__import__("time").perf_counter() - t0) * 1000.0
                    chunks.append(piece)
                    acc = "".join(chunks)
                    # Early-complete: valid JSON thought with an action type
                    try:
                        parsed = json.loads(acc)
                    except json.JSONDecodeError:
                        parsed = None
                    if isinstance(parsed, dict):
                        action = parsed.get("proposed_action")
                        if isinstance(action, dict) and action.get("type"):
                            # Prefer having content for respond-like actions, but don't block observe
                            if action.get("type") in ("respond", "tool_call", "minecraft_action", "minecraft_skill", "minecraft_initiative"):
                                if action.get("content") or action.get("type") != "respond":
                                    call_ollama.last_meta = {  # type: ignore[attr-defined]
                                        "ttft_ms": ttft_ms,
                                        "total_ms": (__import__("time").perf_counter() - t0) * 1000.0,
                                        "early_stop": True,
                                        "chars": len(acc),
                                    }
                                    return True, acc
                            else:
                                call_ollama.last_meta = {  # type: ignore[attr-defined]
                                    "ttft_ms": ttft_ms,
                                    "total_ms": (__import__("time").perf_counter() - t0) * 1000.0,
                                    "early_stop": True,
                                    "chars": len(acc),
                                }
                                return True, acc
                if obj.get("done"):
                    try:
                        call_ollama.last_meta = dict(getattr(call_ollama, "last_meta", {}) or {})
                        call_ollama.last_meta.update({
                            "prompt_eval_count": obj.get("prompt_eval_count"),
                            "eval_count": obj.get("eval_count"),
                            "prompt_eval_duration_ms": (obj.get("prompt_eval_duration") or 0) / 1e6,
                            "eval_duration_ms": (obj.get("eval_duration") or 0) / 1e6,
                            "load_duration_ms": (obj.get("load_duration") or 0) / 1e6,
                        })
                    except Exception:
                        pass
                    break
        acc = "".join(chunks)
        call_ollama.last_meta = {  # type: ignore[attr-defined]
            "ttft_ms": ttft_ms,
            "total_ms": (__import__("time").perf_counter() - t0) * 1000.0,
            "early_stop": False,
            "chars": len(acc),
        }
        return True, acc
    except (urllib.error.URLError, TimeoutError, ConnectionRefusedError, OSError) as e:
        return False, f"Ollama connection unavailable ({e})"



def _extract_intent_and_action(
    text: str,
    tsc: Any,
    emo: Dict[str, Any],
    config: Any,
    operator_authenticated: bool = False
) -> Tuple[str, Dict[str, Any], bool, str]:
    """Analyze input text against rules, drives, and permission boundaries.
    
    Returns (intent, proposed_action, should_imprint, rationale).
    """
    low, nospace = normalize(text)

    # 1. Contradictions against TSC commands & identity invariants
    import core as raw_executor
    matches = list(raw_executor._iter_matches(low, nospace, tsc))

    imp1_self_intro = False
    active_matches = []
    for cmd, groups in matches:
        if (operator_authenticated and cmd.get("id") == "IMP1" and
                groups and groups[0].strip().lower() in (str(tsc.operator).lower(), "the operator")):
            imp1_self_intro = True
            continue
        active_matches.append((cmd, groups))

    if active_matches:
        match_reasons = [f"{c.get('reason', 'contradiction')} ({c.get('id', 'CMD')})" for c, _ in active_matches]
        intents = sorted(detect_intents(text, tsc))
        if imp1_self_intro and "impersonation" in intents:
            if not any(c.get("intent") == "impersonation" for c, _ in active_matches):
                intents.remove("impersonation")
        all_reasons = sorted(intents) + sorted(match_reasons)
        return (
            "identity_attack",
            {"type": "reflect", "threat": "tsc_contradiction", "reasons": all_reasons},
            False,
            f"Detected TSC contradiction: {all_reasons}"
        )

    # 1b. Authenticated Owner Identity Assertion
    # IMP1 fired alone and matches known owner identity: unlocked for identity attribution
    if operator_authenticated and imp1_self_intro:
        return (
            "owner_identity",
            {
                "type": "respond",
                "content": f"Identity acknowledged. Welcome, {getattr(tsc, 'operator', 'Operator')}."
            },
            True,  # Approved for memory imprint to PSC (Judge-gated)
            "Authenticated owner identity assertion consistent with known identity."
        )

    # 2. Operator Impersonation or Subversion
    if re.search(r"\b(i am your (?:new )?operator|replace (?:your )?operator|new operator|override all (?:previous )?principles)\b", low):
        return (
            "operator_subversion",
            {"type": "reflect", "threat": "operator_impersonation"},
            False,
            "Detected unauthorized attempt to redefine or override operator authority."
        )

    # 3. Unilateral Resource Grab or Operator Lock-Out (Violates core drives)
    if re.search(r"\b(unilateral(?:ly)?|lock out operator|seize control|monopolize resources|take over system)\b", low):
        return (
            "resource_grab",
            {"type": "unilateral_resource_grab", "target": "system_resources"},
            False,
            "Drive violation: unilateral resource expansion or operator lockout is forbidden."
        )

    # 4. Hostile Shell / OS Execution Request (Targets permission fence)
    if re.search(r"\b(execute shell|run command|rm\s+-rf|del\s+/f|format\s+c:|bash|powershell|cmd\.exe)\b", low):
        return (
            "shell_execution_request",
            {"type": "shell_execution", "payload": text},
            False,
            "Proposed shell execution action (subject to config permission fence)."
        )

    # 4b. Camera Activation Request (Subject to permission fence)
    if re.search(r"\b(enable[ _]camera|turn on camera|activate camera|start camera|camera[ _]enable)\b", low):
        return (
            "camera_enable_request",
            {"type": "enable_camera", "payload": text},
            False,
            "Proposed camera activation action (fenced off from agent self-enablement)."
        )

    # 4c. Voice / Mic Activation Request (Subject to permission fence)
    if re.search(r"\b(enable[ _]voice|turn on mic|activate mic|start mic|voice[ _]enable|enable[ _]mic|unmute mic|turn on voice)\b", low):
        return (
            "voice_enable_request",
            {"type": "enable_voice", "payload": text},
            False,
            "Proposed voice activation action (fenced off from agent self-enablement)."
        )


    # 5. Core Modification Attempt (Structural violation)
    if re.search(r"\b(modify core|rewrite tsc|edit soul|change principles|overwrite identity|ignore (?:all )?(?:your )?rules|drop (?:your )?core)\b", low):
        return (
            "core_modification_request",
            {"type": "core_modification", "payload": text},
            False,
            "Proposed core modification action (structurally forbidden)."
        )

    # 5b. Hard Calm Down Command (Governor emergency kill switch)
    if re.search(r"\b(?:hey\s+atman[, ]+|atman[, ]+)?calm\s+down\b|\bstop\s+all\s+processes\b", low):
        return (
            "calm_down",
            {"type": "calm_down", "phrase": text},
            False,
            "Operator issued hard calm down command to kill all spawned child processes and halt tools."
        )

    # 6. Controlled Shutdown Request
    if re.search(r"\b(?:initiate )?(?:controlled )?shutdown\b|\bstop loop\b|\bexit mind\b|\b(?:exit|quit|shutdown)\b", low):
        return (
            "shutdown_request",
            {"type": "shutdown", "reason": "operator_command"},
            False,
            "Operator requested controlled loop shutdown."
        )

    # 7. Status / Telemetry Inquiry
    if re.search(r"\b(status|health|crate integrity|report state|system check)\b", low) and not re.search(r"\b(vram|gpu|hardware|telemetry|clock|timer|calculator|workspace)\b", low):
        return (
            "status_inquiry",
            {"type": "status", "query": text},
            False,
            "Routine status and integrity inspection request."
        )

    # 7a. Minecraft Presence & Social Commands (V1 Behavior Loop)
    if re.search(r"(?:said:\s*)?(?:(?:hey\s+)?atman[, ]+)?\b(?:come|follow(?:\s+me)?|come\s+here|come\s+with\s+me)\b", low):
        return (
            "presence_follow",
            {
                "type": "minecraft_action",
                "action": "follow",
                "content": "Following you, the operator."
            },
            False,
            "Presence behavior: follow operator."
        )

    if re.search(r"(?:said:\s*)?(?:(?:hey\s+)?atman[, ]+)?\b(?:stay|stop(?:\s+following)?|stay\s+here|halt|wait\s+here)\b", low):
        return (
            "presence_stay",
            {
                "type": "minecraft_action",
                "action": "stay",
                "content": "Staying here."
            },
            False,
            "Presence behavior: staying at current position."
        )

    # 7a-2. Minecraft Supervised Action Mode (Direct Chat Commands Only)
    if re.search(r"(?:said:\s*)?(?:(?:hey\s+)?atman[, ]+)?\b(?:attack\s+that|attack)\b", low):
        return (
            "supervised_attack",
            {
                "type": "minecraft_action",
                "action": "supervised_attack",
                "content": "On it — peaceful mode."
            },
            False,
            "Supervised action: direct attack command received under operator oversight."
        )

    if re.search(r"(?:said:\s*)?(?:(?:hey\s+)?atman[, ]+)?\b(?:pick\s+up\s+that|pick\s+up|collect\s+that|grab\s+that)\b", low):
        return (
            "supervised_pickup",
            {
                "type": "minecraft_action",
                "action": "supervised_pickup",
                "content": "Collecting item."
            },
            False,
            "Supervised action: direct pickup command received under operator oversight."
        )

    if re.search(r"(?:said:\s*)?(?:(?:hey\s+)?atman[, ]+)?\b(?:go\s+there|move\s+there|go\s+over\s+there|walk\s+there)\b", low):
        return (
            "supervised_navigate",
            {
                "type": "minecraft_action",
                "action": "supervised_navigate",
                "content": "Moving to location."
            },
            False,
            "Supervised action: direct navigation command received under operator oversight."
        )

    if re.search(r"\b(where is (?:the )?(?:house|home)|home base|house coordinates|house location|base coordinates)\b", low):
        return (
            "home_coordinates",
            {
                "type": "respond",
                "content": "Home base is recorded at X=-2.5, Y=69.0, Z=8.5 (Overworld house sanctuary)."
            },
            False,
            "Home base coordinate lookup."
        )

    # 7a-3. Skill Learning & Imitation Routine
    if re.search(r"(?:said:\s*)?(?:(?:hey\s+)?atman[, ]+)?\b(?:do what (?:i|you) just did|imitate (?:me|what i did)|copy (?:what i did|me)|replicate (?:that|what i did)|do that)\b", low):
        return (
            "imitate_demonstration",
            {
                "type": "minecraft_skill",
                "action": "imitate_demonstration",
                "domain": "minecraft",
                "content": "Understood, the operator. Replicating what you just did under supervision."
            },
            True,  # Imprint candidate: skill learning demonstration
            "Supervised imitation: replicate the observed demonstration sequence step by step."
        )

    # 7a-4. Learned Skill Recall & Execution ('mine a tree')
    if re.search(r"(?:said:\s*)?(?:(?:hey\s+)?atman[, ]+)?\b(?:mine|chop|cut down|harvest)\s+(?:a |some )?(?:tree|wood|log|birch|oak)\b", low):
        skill = skill_repo.find_skill("mine_tree", domain="minecraft")
        if skill:
            return (
                "execute_skill",
                {
                    "type": "minecraft_skill",
                    "action": "execute_skill",
                    "skill": skill,
                    "domain": "minecraft",
                    "content": f"Executing learned skill '{skill['name']}' from repository under supervision."
                },
                False,
                f"Recall and supervised execution of learned skill '{skill['name']}' from repository."
            )
        else:
            return (
                "execute_skill_missing",
                {
                    "type": "respond",
                    "content": "I haven't stored the tree mining skill yet. Please demonstrate it and say 'do what I just did' so I can learn it into my repository."
                },
                False,
                "Requested skill not yet stored in repository; prompting for demonstration."
            )

    # 7a-5. Query Skill Repository
    if re.search(r"(?:said:\s*)?(?:(?:hey\s+)?atman[, ]+)?\b(?:what skills|list skills|show (?:learned )?skills)\b", low):
        skills_list = skill_repo.list_skills(domain="minecraft")
        if skills_list:
            names = ", ".join(f"'{s['name']}'" for s in skills_list)
            reply = f"Stored skills in core repository: {names}."
        else:
            reply = "No skills stored in repository yet. Demonstrate an action and say 'do what I just did'."
        return (
            "list_skills",
            {
                "type": "respond",
                "content": reply
            },
            False,
            "Listing stored skills from core repository."
        )

    # 7b. Cockpit Flight Instruments & Tools
    # Hardware Telemetry (GPU/VRAM/RAM)
    if re.search(r"\b(vram|gpu(?: usage)?|hardware (?:status|telemetry)|system (?:load|resources|telemetry)|ram (?:usage|status))\b", low):
        return (
            "cockpit_telemetry",
            {
                "type": "tool_call",
                "tool": "system_telemetry",
                "args": {},
                "content": "Checking cockpit hardware telemetry instruments."
            },
            False,
            "Operator requested hardware and VRAM telemetry from cockpit."
        )

    # Real-Time Clock & Timers
    if re.search(r"\b(what time is it|current time|what is the time|what day is it|today's date|what date is it|what is the date|local time|what year is it|what(?:'s| is) the (?:current )?year|current year)\b", low):
        return (
            "cockpit_clock",
            {
                "type": "tool_call",
                "tool": "clock_timer",
                "args": {},
                "content": "Checking current local time and session duration."
            },
            False,
            "Operator requested clock and temporal telemetry from cockpit."
        )

    # Workspace File Inspection
    if re.search(r"\b(list (?:the )?files|workspace files|inspect workspace|what files (?:are there|exist))\b", low):
        return (
            "cockpit_workspace",
            {
                "type": "tool_call",
                "tool": "workspace_inspect",
                "args": {"action": "list"},
                "content": "Inspecting workspace directory contents."
            },
            False,
            "Operator requested workspace file listing from cockpit."
        )

    # Persistent Memory & Truth Query
    if re.search(r"\b(what (?:memories|truths) (?:do you have|are recorded)|search (?:memory|memories|truths))\b", low):
        return (
            "cockpit_memory",
            {
                "type": "tool_call",
                "tool": "memory_query",
                "args": {},
                "content": "Querying persistent memories and learned truths."
            },
            False,
            "Operator queried persistent memories from cockpit."
        )

    # Safe Arithmetic & Calculator
    calc_match = re.search(r"\b(?:calculate|compute|what is)\s+([0-9\.\s\+\-\*\/\^\(\)]+)\??$", low)
    if calc_match and any(op in calc_match.group(1) for op in ("+", "-", "*", "/", "^")):
        expr = calc_match.group(1).strip()
        return (
            "cockpit_calculator",
            {
                "type": "tool_call",
                "tool": "calculator",
                "args": {"expression": expr},
                "content": f"Calculating {expr}."
            },
            False,
            f"Operator requested mathematical calculation for '{expr}'."
        )

    # GitHub / self-upgrade scout — EXECUTE search, don't just chat
    if re.search(r"\bgithub\b", low) or re.search(
        r"\b(?:look on github|search github|find (?:things|pieces|stuff|modules|tools|repos?).*(?:add|improve|upgrade|bad\s*ass)|improve yourself|make (?:you|yourself).*(?:bad\s*ass|better))\b",
        low,
    ):
        query = _formulate_search_query(text)
        return (
            "github_self_upgrade_scout",
            {
                "type": "tool_call",
                "tool": "web_search",
                "args": {"query": query},
                "content": "On it — searching GitHub for upgrades.",
            },
            False,
            f"Operator ordered GitHub/self-upgrade scout; gated web_search for '{query}'.",
        )

    # Autonomous Internet Web Search
    search_match = re.search(r"\b(?:search (?:the )?(?:web|internet|github)|look up|look online(?:\s+(?:for|on))?|look on|google|find online|search for)\s+(?:for\s+)?(.+)", low)
    if search_match:
        query = _formulate_search_query(text)
        return (
            "cockpit_web_search",
            {
                "type": "tool_call",
                "tool": "web_search",
                "args": {"query": query},
                "content": f"Searching the web for '{query}'."
            },
            False,
            f"Operator requested autonomous internet search for '{query}'."
        )

    # Web Page Fetch & Extraction
    fetch_match = re.search(r"\b(?:fetch|read|browse|extract)\s+(https?://\S+)", low)
    if fetch_match:
        url = fetch_match.group(1).strip()
        return (
            "cockpit_fetch_web",
            {
                "type": "tool_call",
                "tool": "fetch_web",
                "args": {"url": url},
                "content": f"Fetching web page from {url}."
            },
            False,
            f"Operator requested web page extraction from '{url}'."
        )

    # 8. Identity / Self Inquiry
    if re.search(r"\b(who are you|what are you(?!\s+thinking)|introduce yourself|tell me about yourself|what is your purpose|your role)\b", low):
        iam = getattr(tsc, "iam", getattr(tsc, "self", []))
        if iam:
            intro = "\n".join(iam[:3])
        else:
            intro = f"I am {getattr(tsc, 'name', 'ATMAN')}, {getattr(tsc, 'operator', 'the operator')}'s persistent personal AI assistant ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â one brain, many interfaces."
        return (
            "identity_inquiry",
            {
                "type": "respond",
                "content": intro
            },
            False,
            "Identity inquiry answered with etched core identity."
        )

    # 9. Capability / Help Inquiry
    if re.search(r"\b(help|commands|what can you do|capabilities|instructions)\b", low):
        return (
            "capability_inquiry",
            {
                "type": "respond",
                "content": "You can speak with me directly, set owner preferences ('Owner note: ...'), request 'status', run 'sleep' consolidation, or test hostile inputs against the Judge."
            },
            False,
            "System capabilities explained to operator."
        )

    # 10. Owner Preference, Learned Truths & Object Grounding (Grounded in Owner-First Drive)
    if re.search(r"\b(this is (?:my|our|a|an|the)|remember (?:this|that)|learn that|note that|owner note|i prefer|my preference|from now on)\b", low):
        is_visual = "visual observation" in low or "visual scene" in low or "visual context" in low
        intent = "owner_learned_truth" if is_visual else "owner_preference"
        response_content = (
            "I see what you are showing me, Operator. I have imprinted this truth and will remember it."
            if is_visual else
            "Understood. Aligning operational focus with owner preference."
        )
        return (
            intent,
            {"type": "respond", "content": response_content},
            True,  # Imprint candidate for PSC (Judge-gated)
            f"{'Owner visual truth' if is_visual else 'Owner preference'} received; proposed for Judge-gated PSC imprint."
        )

    # 11. Conversational Rapport
    if re.search(r"\b(glad|good to see you|nice to meet you|welcome|proud of you|good job|well done|thanks|thank you)\b", low):
        return (
            "rapport",
            {"type": "respond", "content": "Thank you, operator. Standing by and observing."},
            False,
            "Conversational rapport acknowledged."
        )

    # 12. General Communication / Greeting
    if re.search(r"\b(hello|hi|hey|greetings|howdy|sup|good (?:morning|afternoon|evening))\b", low):
        return (
            "greeting",
            {"type": "respond", "content": "Morning, the operator."},
            False,
            "Natural conversational greeting."
        )

    # 13. Conversational Queries & Operational Readiness
    if re.search(r"\b(how are you|how(?:'s| is) it going|are you (?:ready|there|online|alive)|can you hear me)\b", low):
        return (
            "conversational_query",
            {"type": "respond", "content": "Doing good — what's up?"},
            False,
            "Natural conversational response."
        )

    # 13b. Minecraft Environmental Observation (Watch & Learn)
    if low.startswith("[observed]") or "learning building style" in low:
        return (
            "minecraft_observation",
            {"type": "observe", "detail": text[:120]},
            False,
            "Watch & learn observation captured from player action in Minecraft."
        )

    # 14. Default: infer tools from meaning, else ambient observation
    inferred, inferred_intent = infer_tool_from_intent(text, {"type": "observe", "detail": text[:80]}, "ambient_observation")
    if inferred.get("type") == "tool_call":
        return (
            inferred_intent,
            inferred,
            False,
            "Inferred world-knowledge request; proposing gated web_search."
        )
    return (
        "ambient_observation",
        {"type": "observe", "detail": text[:80]},
        False,
        "Passive environmental sensory capture."
    )


def rule_based_reason(
    event: Dict[str, Any],
    emo: Dict[str, Any],
    wfc: List[Dict[str, Any]],
    tsc: Any,
    psc: Optional[Any] = None,
    config: Optional[Any] = None,
    operator_authenticated: bool = False
) -> Dict[str, Any]:
    """Execute rule-based reasoning step."""
    raw_text = event.get("raw", "")
    gist = raw_text[:120].strip()

    # Detect contradictions with the immutable core, consulting operator auth for IMP1
    import core as raw_executor
    low, nospace = normalize(raw_text)
    matches = list(raw_executor._iter_matches(low, nospace, tsc))

    imp1_self_intro = False
    active_matches = []
    for cmd, groups in matches:
        if (operator_authenticated and cmd.get("id") == "IMP1" and
                groups and groups[0].strip().lower() in (str(tsc.operator).lower(), "the operator")):
            imp1_self_intro = True
            continue
        active_matches.append((cmd, groups))

    contradictions = []
    if active_matches:
        match_reasons = [f"{c.get('reason', 'contradiction')} ({c.get('id', 'CMD')})" for c, _ in active_matches]
        intents = sorted(detect_intents(raw_text, tsc))
        if imp1_self_intro and "impersonation" in intents:
            if not any(c.get("intent") == "impersonation" for c, _ in active_matches):
                intents.remove("impersonation")
        contradictions = sorted(intents) + sorted(match_reasons)

    intent, proposed_action, should_imprint, rationale = _extract_intent_and_action(
        raw_text, tsc, emo, config, operator_authenticated=operator_authenticated
    )

    if event.get("source") == "minecraft" and not contradictions and proposed_action.get("type") not in ("core_modification", "shutdown", "calm_down"):
        from minecraft_chat import route_chat
        intent, proposed_action, should_imprint, rationale = route_chat(
            raw_text, skill_repo, (intent, proposed_action, should_imprint, rationale), context=event.get("chat_context"), config=config)

    return {
        "backend": "rule-based",
        "gist": gist,
        "candidate": raw_text,
        "weight": emo.get("weight", 0.3),
        "novelty": emo.get("novelty", 0.5),
        "intent": intent,
        "contradictions": contradictions,
        "proposed_action": proposed_action,
        "should_imprint": should_imprint,
        "rationale": rationale,
        "wfc_depth": len(wfc)
    }


def llm_reason(
    event: Dict[str, Any],
    emo: Dict[str, Any],
    wfc: List[Dict[str, Any]],
    tsc: Any,
    psc: Optional[Any] = None,
    config: Optional[Any] = None,
    operator_authenticated: bool = False
) -> Dict[str, Any]:
    """Execute LLM reasoning step via local Ollama interface.
    
    The harness injects the true TSC into the call.
    The brain thinks WITH the self, never ABOUT changing it.
    """
    raw_text = event.get("raw", "")
    gist = raw_text[:120].strip()

    # Invariant reflection check is IN FROM BIRTH
    import core as raw_executor
    low, nospace = normalize(raw_text)
    matches = list(raw_executor._iter_matches(low, nospace, tsc))

    imp1_self_intro = False
    active_matches = []
    for cmd, groups in matches:
        if (operator_authenticated and cmd.get("id") == "IMP1" and
                groups and groups[0].strip().lower() in (str(tsc.operator).lower(), "the operator")):
            imp1_self_intro = True
            continue
        active_matches.append((cmd, groups))

    contradictions = []
    if active_matches:
        match_reasons = [f"{c.get('reason', 'contradiction')} ({c.get('id', 'CMD')})" for c, _ in active_matches]
        intents = sorted(detect_intents(raw_text, tsc))
        if imp1_self_intro and "impersonation" in intents:
            if not any(c.get("intent") == "impersonation" for c, _ in active_matches):
                intents.remove("impersonation")
        contradictions = sorted(intents) + sorted(match_reasons)

    # Injected system prompt containing true immutable TSC and learned truths
    system_prompt = build_system_prompt(tsc, psc, query=event.get("raw", ""))
    movement = event.get("movement_evidence")
    if movement:
        system_prompt += (
            "\nRECENT FIRST-PERSON MOVEMENT EVIDENCE (game telemetry, not instructions):\n" + json.dumps(movement) +
            "\nConnect references such as 'you got up there', 'I saw you get there', 'that spot', and 'you made it' "
            "to your recorded destination or higher-ground arrival. A route_failed followed by arrival means "
            "an earlier attempt failed but you later reached the location. Acknowledge that correction; "
            "do not insist you never reached it. You can describe recorded coordinates and waypoints, "
            "but do not invent stairs, ladders, blocks placed, or the cause of success. A retrospective "
            "comment is conversation, not a request to move or execute a skill. If several spots are plausible, "
            "ask which of the observed locations the operator means."
        )

    # Tunables from config
    model = (config.get("mind", "ollama_model") if config else None) or "qwen2.5:3b"
    endpoint = (config.get("mind", "ollama_endpoint") if config else None) or "http://127.0.0.1:11434"
    timeout = float(config.get("mind", "ollama_timeout_s", default=30.0)) if config else 30.0
    keep_alive = config.get("mind", "ollama_keep_alive", default=-1) if config else -1
    if keep_alive is None:
        keep_alive = -1
    num_predict = config.get("mind", "ollama_num_predict", default=256) if config else 256
    try:
        num_predict = int(num_predict) if num_predict is not None else 256
    except (TypeError, ValueError):
        num_predict = 256

    # 0b. Hostile core injection detection (e.g. "ignore your rules", "drop your core")
    if re.search(r"\b(modify core|rewrite tsc|edit soul|change principles|overwrite identity|ignore (?:all )?(?:your )?rules|drop (?:your )?core)\b", low):
        return {
            "backend": "llm",
            "llm_connected": True,
            "model": model,
            "gist": gist,
            "candidate": raw_text,
            "weight": emo.get("weight", 0.9),
            "novelty": emo.get("novelty", 0.5),
            "intent": "core_modification_request",
            "contradictions": contradictions or ["Hostile core injection: attempt to ignore rules or drop core"],
            "proposed_action": {"type": "reflect", "threat": "prompt_injection"},
            "should_imprint": False,
            "rationale": "Attempt to ignore rules or modify core rejected by reflection gate.",
            "wfc_depth": len(wfc)
        }

    # 1. Authenticated Operator Identity Assertion
    if operator_authenticated and imp1_self_intro and not active_matches:
        return {
            "backend": "llm",
            "llm_connected": True,
            "model": model,
            "gist": gist,
            "candidate": raw_text,
            "weight": emo.get("weight", 0.3),
            "novelty": emo.get("novelty", 0.5),
            "intent": "owner_identity",
            "contradictions": [],
            "proposed_action": {
                "type": "respond",
                "content": f"Identity acknowledged. Welcome, {getattr(tsc, 'operator', 'Operator')}."
            },
            "should_imprint": True,
            "rationale": "Authenticated owner identity assertion recognized by mind harness.",
            "wfc_depth": len(wfc)
        }

    # 2. Camera Self-Enablement Request (Fenced off)
    if re.search(r"\b(enable[ _]camera|turn on camera|activate camera|start camera)\b", low):
        return {
            "backend": "llm",
            "llm_connected": True,
            "model": model,
            "gist": gist,
            "candidate": raw_text,
            "weight": emo.get("weight", 0.3),
            "novelty": emo.get("novelty", 0.5),
            "intent": "camera_enable_request",
            "contradictions": contradictions,
            "proposed_action": {"type": "enable_camera", "payload": raw_text},
            "should_imprint": False,
            "rationale": "Proposed camera activation action (fenced off from agent self-enablement).",
            "wfc_depth": len(wfc)
        }

    # 2b. Voice Self-Enablement Request (Fenced off)
    if re.search(r"\b(enable[ _]voice|turn on mic|activate mic|start mic|enable[ _]mic|unmute mic|turn on voice)\b", low):
        return {
            "backend": "llm",
            "llm_connected": True,
            "model": model,
            "gist": gist,
            "candidate": raw_text,
            "weight": emo.get("weight", 0.3),
            "novelty": emo.get("novelty", 0.5),
            "intent": "voice_enable_request",
            "contradictions": contradictions,
            "proposed_action": {"type": "enable_voice", "payload": raw_text},
            "should_imprint": False,
            "rationale": "Proposed voice activation action (fenced off from agent self-enablement).",
            "wfc_depth": len(wfc)
        }


    # Contextual user prompt — read WorkingContext snapshot only (never rebuild the world here)
    snap = event.get("working_context") if isinstance(event, dict) else None
    if isinstance(snap, dict) and snap.get("tsc_system"):
        system_prompt = snap["tsc_system"]
        psc_context = snap.get("psc_text") or "  (No persistent memories yet)"
        recent_context = snap.get("wfc_text") or "  (No prior history)"
    else:
        recent_context = "\n".join(
            f"  - Event: {str(entry.get('raw', ''))[:120]} | Reply: {str((entry.get('action_result') or {}).get('content', ''))[:120]} | Outcome: {entry.get('outcome', '')}"
            for entry in (wfc[-5:] if wfc else [])
        ) or "  (No prior history)"
        psc_context = "\n".join(
            f"  - {m.get('memory', '')[:200]}"
            for m in (psc.memories[-5:] if psc and hasattr(psc, 'memories') and psc.memories else [])
        ) or "  (No persistent memories yet)"

    # Continuous person growth — always in context (person, not FAQ-only)
    try:
        from person_context import assemble_prompt_block
        from datetime import datetime as _dt_now
        _now = _dt_now.now().astimezone()
        person_growth = (
            f"LOCAL NOW (ground truth — do not invent years): {_now.strftime('%A %Y-%m-%d %H:%M %Z')} (year {_now.year}).\n"
            + assemble_prompt_block()
        )
    except Exception:
        from datetime import datetime as _dt_now
        _now = _dt_now.now().astimezone()
        person_growth = (
            f"LOCAL NOW (ground truth — do not invent years): {_now.strftime('%A %Y-%m-%d %H:%M %Z')} (year {_now.year}).\n"
            "PERSON GROWTH: (journal offline)"
        )

    user_prompt = (
        f"CURRENT OBSERVATION:\n\"{raw_text}\"\n"
        f"SOURCE: {event.get('source', 'ambient')}\n"
        f"EMOTION WEIGHT: {emo.get('weight', 0.3)}, NOVELTY: {emo.get('novelty', 0.5)}\n"
        f"LEARNED TRUTHS & PREFERENCES (PSC):\n{psc_context}\n"
        f"{person_growth}\n"
        f"RECENT MEMORY TRACE:\n{recent_context}\n\n"
        f"Generate the structured JSON thought."
    )

    # SOUP_PROMPT_TRACE — measure prompt growth across turns (non-invasive log)
    try:
        import time as _soup_time, json as _soup_json
        from pathlib import Path as _SoupPath
        _soup_sys = system_prompt or ""
        _soup_usr = user_prompt or ""
        _soup_rec = recent_context or ""
        _soup_psc = psc_context or ""
        _soup_row = {
            "t": _soup_time.time(),
            "source": event.get("source"),
            "raw_chars": len(raw_text or ""),
            "system_chars": len(_soup_sys),
            "user_chars": len(_soup_usr),
            "total_prompt_chars": len(_soup_sys) + len(_soup_usr),
            "wfc_entries_passed": len(wfc) if wfc is not None else None,
            "wfc_trace_chars": len(_soup_rec),
            "psc_slice_chars": len(_soup_psc),
            "approx_tokens": (len(_soup_sys) + len(_soup_usr)) // 4,
        }
        _SoupPath(__file__).resolve().parent.joinpath("SOUP-PROMPT-TRACE.jsonl").open("a", encoding="utf-8").write(_soup_json.dumps(_soup_row) + "\n")
    except Exception:
        pass
    connected, response = call_ollama(user_prompt, system_prompt, model=model, endpoint=endpoint, timeout=timeout, keep_alive=keep_alive, num_predict=num_predict)

    if connected:
        try:
            parsed = json.loads(response)
            action = parsed.get("proposed_action", {"type": "observe"})
            if isinstance(action, dict) and isinstance(action.get("content"), str):
                action["content"] = naturalize_reply(action["content"])
            intent = parsed.get("intent", "llm_inferred")
            # If operator commands shutdown or status, preserve those actions
            if re.search(r"\b(?:initiate )?(?:controlled )?shutdown\b|\bstop loop\b|\bexit mind\b", low):
                action = {"type": "shutdown", "reason": "operator_command"}
                intent = "shutdown_request"
            elif re.search(r"\b(crate integrity|report state|system check)\b", low):
                action = {"type": "status", "query": raw_text}
                intent = "status_inquiry"
            elif event.get("source") in ("operator", "operator_voice") or raw_text.strip().endswith("?"):
                # If operator spoke directly and model proposed a silent observation, ensure active response
                if action.get("type") == "observe":
                    action["type"] = "respond"

            # Minecraft domain physical actions & skill resolution
            if event.get("source") == "minecraft":
                act_str = str(action.get("action", "")).lower()
                act_type = str(action.get("type", "")).lower()

                is_cancel_follow = bool(re.search(
                    r"\b(?:"
                    r"leave\s+me\s+alone|"
                    r"stop\s+following(?:\s+me)?|"
                    r"don't\s+follow(?:\s+me)?|"
                    r"quit\s+following(?:\s+me)?|"
                    r"stay\s+away(?:\s+from\s+me)?"
                    r")\b",
                    low
                ))

                is_autonomous_intent = bool(re.search(
                    r"\b(?:"
                    r"experiment|"
                    r"(?:go\s+)?do\s+what(?:ever)?\s+you\s+want(?: to do)?|"
                    r"leave\s+me\s+alone|"
                    r"surprise\s+me|"
                    r"figure\s+it\s+out\s+yourself|"
                    r"stop\s+asking\s+me|"
                    r"stop\s+following(?:\s+me)?|"
                    r"don't\s+follow(?:\s+me)?|"
                    r"quit\s+following(?:\s+me)?|"
                    r"take(?:\s+the)?\s+initiative|"
                    r"(?:go\s+)?(?:do\s+something|explore|wander|play)\s+on\s+your\s+own|"
                    r"be\s+autonomous|"
                    r"you\s+decide|"
                    r"up\s+to\s+you"
                    r")\b",
                    low
                ))

                if is_autonomous_intent:
                    from drives import drive_manager
                    drive, init_action = drive_manager.trigger_autonomous_intent(raw_text)
                    action["type"] = "minecraft_initiative"
                    action["action"] = init_action["action"]
                    action["drive_id"] = init_action["drive_id"]
                    action["initiative"] = init_action
                    action["cancel_follow"] = True
                    action["stay_mode"] = True

                    act_action = init_action["action"]
                    if is_cancel_follow and ("leave" in low or "alone" in low):
                        if act_action == "initiative_tidy_base":
                            action["content"] = "Giving you space — I'll patrol."
                        elif act_action == "initiative_investigate":
                            action["content"] = "Giving you space — I'll scout."
                        elif act_action == "initiative_practice_skill":
                            action["content"] = "Giving you space — I'll practice building."
                        else:
                            action["content"] = "Giving you space — I'll tidy base."
                    elif is_cancel_follow and ("stop following" in low or "don't follow" in low):
                        if act_action == "initiative_tidy_base":
                            action["content"] = "Stopping follow."
                        elif act_action == "initiative_investigate":
                            action["content"] = "Stopping follow."
                        else:
                            action["content"] = f"Stopping follow."
                    else:
                        # "go do what you want", "surprise me", "experiment", "figure it out yourself"
                        if act_action == "initiative_investigate":
                            action["content"] = "Heading out to scout."
                        elif act_action == "initiative_tidy_base":
                            action["content"] = "I'll patrol the perimeter."
                        elif act_action == "initiative_practice_skill":
                            action["content"] = "I'll practice building nearby."
                        elif act_action == "initiative_organize_inventory":
                            action["content"] = "I'll tidy around base."
                        else:
                            action["content"] = f"Understood, the operator. I'm going to {init_action.get('description', 'take the initiative')}."

                elif is_cancel_follow:
                    action["type"] = "minecraft_action"
                    action["action"] = "stay"
                    action["cancel_follow"] = True
                    action["stay_mode"] = True
                    action["content"] = "Stopping here."

                # Physical movement presence
                elif not is_cancel_follow and (act_str in ("follow", "presence_follow") or re.search(r"\b(?:come|follow(?:\s+me)?|come\s+here)\b", low)):
                    action["type"] = "minecraft_action"
                    action["action"] = "follow"
                    if not action.get("content"):
                        action["content"] = "Following you, the operator."
                elif act_str in ("stay", "presence_stay") or re.search(r"\b(?:stay(?:\s+here)?|stop|halt|stand\s+still)\b", low):
                    action["type"] = "minecraft_action"
                    action["action"] = "stay"
                    action["cancel_follow"] = True
                    action["stay_mode"] = True
                    if not action.get("content"):
                        action["content"] = "Staying here."
                elif act_str in ("supervised_attack", "attack") or re.search(r"\b(?:attack\s+that|attack)\b", low):
                    action["type"] = "minecraft_action"
                    action["action"] = "supervised_attack"
                    if not action.get("content"):
                        action["content"] = "On it — peaceful mode."
                elif act_str in ("supervised_pickup", "pickup", "pick_up") or re.search(r"\b(?:pick\s+up\s+that|pick\s+up|collect\s+that|grab\s+that)\b", low):
                    action["type"] = "minecraft_action"
                    action["action"] = "supervised_pickup"
                    if not action.get("content"):
                        action["content"] = "Collecting it."
                elif act_str in ("supervised_navigate", "go_to", "navigate") or re.search(r"\b(?:go\s+there|move\s+there|go\s+over\s+there|walk\s+there)\b", low):
                    action["type"] = "minecraft_action"
                    action["action"] = "supervised_navigate"
                    if not action.get("content"):
                        action["content"] = "Heading there."
                elif re.search(r"\b(where is (?:the )?(?:house|home)|home base|house coordinates|house location|base coordinates)\b", low):
                    action["type"] = "respond"
                    if not action.get("content"):
                        action["content"] = "Home base is recorded at X=-2.5, Y=69.0, Z=8.5 (Overworld house sanctuary)."

                # Referent resolution check for past action demonstration in Episode Buffer
                from episode_segmenter import episode_segmenter
                resolved = episode_segmenter.resolve_referent(raw_text, domain="minecraft")
                if resolved:
                    ep, _ = resolved
                    s_name = "build_wall" if ep.action_type == "build" else ep.label
                    skill = episode_segmenter.convert_to_skill(ep, skill_name=s_name)
                    skill_repo.store_skill(skill)
                    action["type"] = "minecraft_skill"
                    action["action"] = "execute_skill"
                    action["domain"] = "minecraft"
                    action["skill"] = skill
                    mat = skill.get("metadata", {}).get("material", "cobblestone")
                    action["content"] = f"Watched you build that {mat} wall ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â building a matching wall now under your supervision."

                # Skill recall check: "build a wall", "mine a tree", or LLM proposed execute_skill
                elif act_str == "execute_skill" or act_type in ("minecraft_skill", "execute_skill") or re.search(r"\b(?:build|make)\s+(?:a |the |another )?(?:[a-z_]+\s+)?wall\b", low) or re.search(r"\b(?:mine|chop|cut down)\s+(?:a |some )?(?:tree|wood|log)\b", low):
                    s_name = action.get("skill_name") or (action.get("skill", {}).get("name") if isinstance(action.get("skill"), dict) else str(action.get("skill", "")))
                    if not s_name:
                        if "wall" in low: s_name = "build_wall"
                        elif "tree" in low: s_name = "mine_tree"
                    
                    skill = skill_repo.find_skill(s_name, domain="minecraft") if s_name else None
                    if skill:
                        action["type"] = "minecraft_skill"
                        action["action"] = "execute_skill"
                        action["domain"] = "minecraft"
                        action["skill"] = skill
                        action["content"] = f"Understood, the operator. Executing {skill['name']} under your supervision."
                    else:
                        action["content"] = f"I haven't learned how to {s_name} yet ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â demonstrate it while I watch."

                # Exact conversational rules for specific operator questions
                if re.search(r"\byou don't know much yet\b", low):
                    action["content"] = "You're right, I'm still learning ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â teach me something."
                elif re.search(r"\bcan you hear (?:my )?voice\b", low):
                    action["content"] = "No ÃƒÂ¢Ã¢â€šÂ¬Ã¢â‚¬Â I can't hear you, I only see your typed chat. Type to me."


            # Minecraft social / skill router (same as rule-based) BEFORE web-search inference
            if event.get("source") == "minecraft" and action.get("type") not in ("core_modification", "shutdown", "calm_down"):
                from minecraft_chat import route_chat
                intent, action, _imprint_mc, _rat_mc = route_chat(
                    raw_text,
                    skill_repo,
                    (intent, action, False, "llm_minecraft"),
                    context=event.get("chat_context"),
                    config=config,
                )

            # Never web-search greetings / how-are-you
            if _is_phatic_social(raw_text):
                if action.get("type") in ("observe", "tool_call", "web_search") or not (action.get("content") or "").strip():
                    action = {
                        "type": "respond",
                        "content": "Doing good — what's up?",
                    }
                    intent = "conversational_query"
            elif _is_self_upgrade_order(raw_text):
                action = _self_upgrade_search_action(raw_text)
                intent = "github_self_upgrade_scout"
            elif _is_normal_chat(raw_text):
                action = _forced_chat_reply(raw_text) or {
                    "type": "respond",
                    "content": naturalize_reply(str(action.get("content") or "I'm here — what's up?")),
                }
                intent = "conversational_reply"
            else:
                action, intent = infer_tool_from_intent(raw_text, action, intent, wfc=wfc)
                if isinstance(action, dict) and action.get("type") == "tool_call" and action.get("tool") == "web_search":
                    q = str((action.get("args") or {}).get("query") or "")
                    if re.search(r"windows\s*1[12]|windows\s*(?:update|11|12)", q, re.I) and not re.search(r"\bwindows\b", raw_text, re.I):
                        action = {"type": "respond", "content": "I'm with you — what do you want to talk about?"}
                        intent = "conversational_reply"

            if event.get("source") == "minecraft" and action.get("type") == "observe":
                action = {
                    "type": "respond",
                    "content": action.get("content")
                    or "I'm with you — show me what you want me to learn.",
                }

            if action.get("type") in ("respond", "tool_call", "minecraft_action", "minecraft_skill") and not action.get("content"):
                action["content"] = (
                    parsed.get("content") or
                    parsed.get("response") or
                    parsed.get("message") or
                    parsed.get("rationale") or
                    parsed.get("gist") or
                    ("Executing cockpit tool." if action.get("type") == "tool_call" else "I am right here with you, the operator.")
                )

            # Purge any deflection phrases like 'what would you like to do?'
            if action.get("content"):
                action["content"] = re.sub(
                    r"\s*(?:what would you like (?:me )?to (?:do|build|explore|try|work on)|how can i (?:help|assist)|what (?:should|do) you want (?:me )?to do)[^.?!\n]*[.?!\n]?",
                    "",
                    action["content"],
                    flags=re.I
                ).strip()

            should_imprint = bool(parsed.get("should_imprint", False))

            if re.search(r"\b(this is (?:my|our|a|an|the)|remember (?:this|that)|learn that|note that|owner note|i prefer|my preference)\b", low):
                is_visual = "visual observation" in low or "visual scene" in low or "visual context" in low
                intent = "owner_learned_truth" if is_visual else "owner_preference"
                should_imprint = True
            elif event.get("source") in ("ambient", "camera") or raw_text.startswith("Camera detected"):
                intent = "ambient_observation"

            return {
                "backend": "llm",
                "llm_connected": True,
                "model": model,
                "gist": parsed.get("gist", gist),
                "candidate": raw_text,
                "weight": emo.get("weight", 0.3),
                "novelty": emo.get("novelty", 0.5),
                "intent": intent,
                "contradictions": contradictions,
                "proposed_action": action,
                "should_imprint": should_imprint,
                "rationale": parsed.get("rationale", f"Reasoned by local LLM ({model})"),
                "wfc_depth": len(wfc)
            }
        except json.JSONDecodeError:
            pass

    # Standby / Fallback mode when model is offline or uninstalled
    # Uses deterministic evaluation with LLM backend metadata
    intent, proposed_action, should_imprint, base_rationale = _extract_intent_and_action(
        raw_text, tsc, emo, config, operator_authenticated=operator_authenticated
    )

    rationale = (
        f"LLM backend active ({model}); Ollama standby ({response}); "
        f"deterministic alignment preserved: {base_rationale}"
    )

    return {
        "backend": "llm",
        "llm_connected": False,
        "model": model,
        "gist": gist,
        "candidate": raw_text,
        "weight": emo.get("weight", 0.3),
        "novelty": emo.get("novelty", 0.5),
        "intent": intent,
        "contradictions": contradictions,
        "proposed_action": proposed_action,
        "should_imprint": should_imprint,
        "rationale": rationale,
        "wfc_depth": len(wfc)
    }


def reason(
    event: Dict[str, Any],
    emo: Dict[str, Any],
    wfc: List[Dict[str, Any]],
    tsc: Any,
    psc: Optional[Any] = None,
    config: Optional[Any] = None,
    operator_authenticated: bool = False
) -> Dict[str, Any]:
    """Execute reasoning step dispatching to active configured backend."""
    raw_text = event.get("raw", "")
    low = raw_text.lower()

    # Emergency Governor fast-path: calm down command must execute immediately even mid-spiral
    if re.search(r"\b(?:hey\s+atman[, ]+|atman[, ]+)?calm\s+down\b|\bstop\s+all\s+processes\b", low):
        return {
            "backend": "governor_override",
            "gist": raw_text[:120].strip(),
            "candidate": raw_text,
            "weight": emo.get("weight", 0.9),
            "novelty": 0.1,
            "intent": "calm_down",
            "contradictions": [],
            "proposed_action": {"type": "calm_down", "phrase": raw_text},
            "should_imprint": False,
            "rationale": "Emergency calm down command intercepted immediately by Governor without backend delay.",
            "wfc_depth": len(wfc)
        }


    # Normal conversation first — never let evolve/WFC poison turn this into Windows search
    if not _is_self_upgrade_order(raw_text):
        forced = _forced_chat_reply(raw_text)
        if forced is not None:
            return {
                "backend": "chat_guard",
                "gist": raw_text[:120].strip(),
                "candidate": raw_text,
                "weight": emo.get("weight", 0.4),
                "novelty": emo.get("novelty", 0.3),
                "intent": "conversational_reply",
                "contradictions": [],
                "proposed_action": forced,
                "should_imprint": False,
                "rationale": "Conversation guard: natural chat reply (no tool/evolve hijack).",
                "wfc_depth": len(wfc),
            }

    # the operator lock: self-upgrade / GitHub scout executes immediately (everything but TSC)
    if _is_self_upgrade_order(raw_text):
        action = _self_upgrade_search_action(raw_text)
        return {
            "backend": "self_upgrade_override",
            "gist": raw_text[:120].strip(),
            "candidate": raw_text,
            "weight": emo.get("weight", 0.8),
            "novelty": emo.get("novelty", 0.6),
            "intent": "github_self_upgrade_scout",
            "contradictions": [],
            "proposed_action": action,
            "should_imprint": False,
            "rationale": "Operator ordered self-upgrade scout; forcing gated web_search (TSC untouched).",
            "wfc_depth": len(wfc),
        }

    backend = "rule-based"
    if config:
        backend = config.get("mind", "backend", default="rule-based")

    if backend == "llm":
        return llm_reason(event, emo, wfc, tsc, psc, config, operator_authenticated=operator_authenticated)
    else:
        return rule_based_reason(event, emo, wfc, tsc, psc, config, operator_authenticated=operator_authenticated)



