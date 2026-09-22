"""Continuous person-context journal for ATMAN.

Operator's standing note: "his context should always evolve too — this is a person here."

Design:
  - Append-only PERSON_JOURNAL.jsonl under self_improve/ (durable, not sealed core).
  - Compact person-facts: applied skills, learned lessons, evolve ticks — NEVER raw SERP.
  - ALWAYS assembled into Reason prompts (continuous growth), not only on FAQ matches.
  - Improvement-status asks answered from journal truth (or honest "nothing new yet").
  - Phatic "how are you" is NOT treated as an improvement ask (chat_guard stays strict).
  - Does not write TSC / gate_policy / atman_core / core / crate / wake / seal / psc.json.
  - PSC Judge-gated imprints remain the authoritative long-term soul path; this journal
    is the always-on working-context feed so WFC depoison cannot leave him amnesiac.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent
JOURNAL = ROOT / "self_improve" / "PERSON_JOURNAL.jsonl"
CHANGELOG = ROOT / "self_improve" / "CHANGELOG.md"
CHANGES_INDEX = ROOT / "self_improve" / "changes_index.json"
SKILLS_JSON = ROOT / "skills.json"
OVERNIGHT_CL = ROOT / "overnight" / "CHANGELOG-OVERNIGHT.md"
FREEPLAY_STATE = ROOT / "self_improve" / "freeplay_state.json"

_MAX_FACT_CHARS = 220
_MAX_PROMPT_FACTS = 14
_DEDUP_WINDOW = 400  # recent lines scanned for near-dupes


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _slim(text: str, n: int = _MAX_FACT_CHARS) -> str:
    t = re.sub(r"\s+", " ", (text or "").strip())
    if len(t) <= n:
        return t
    return t[: n - 1].rstrip() + "…"


def _ensure_journal() -> None:
    JOURNAL.parent.mkdir(parents=True, exist_ok=True)
    if not JOURNAL.exists():
        JOURNAL.write_text("", encoding="utf-8")


def _read_recent(limit: int = _DEDUP_WINDOW) -> List[Dict[str, Any]]:
    _ensure_journal()
    rows: List[Dict[str, Any]] = []
    try:
        lines = JOURNAL.read_text(encoding="utf-8").splitlines()
    except OSError:
        return rows
    for line in lines[-limit:]:
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def note_fact(
    kind: str,
    text: str,
    source: str = "live",
    meta: Optional[Dict[str, Any]] = None,
) -> bool:
    """Append one compact person-fact. Returns True if written (False if empty/dupe)."""
    fact = _slim(text)
    if not fact or len(fact) < 8:
        return False
    kind = (kind or "growth").strip()[:40]
    recent = _read_recent()
    key = fact.casefold()
    for row in recent[-80:]:
        if str(row.get("text", "")).casefold() == key and str(row.get("kind", "")) == kind:
            return False
    row = {
        "ts": _now_iso(),
        "kind": kind,
        "text": fact,
        "source": source,
        "meta": meta or {},
    }
    _ensure_journal()
    with JOURNAL.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return True


def sync_from_disk() -> Dict[str, int]:
    """Pull durable truth from changelog / skills / overnight into the journal.

    Idempotent via note_fact dedupe. Safe to call every Reason turn (cheap).
    """
    counts = {"changelog": 0, "skills": 0, "overnight": 0, "index": 0, "freeplay": 0}

    # Applied / proposed lines from self_improve CHANGELOG
    if CHANGELOG.exists():
        try:
            for line in CHANGELOG.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line.startswith("- ["):
                    continue
                # Skip pure dry-run noise unless it is the only signal
                low = line.lower()
                if "dry_run=true" in low and "propose" not in low and "rollback" not in low:
                    continue
                if "rollback" in low:
                    kind = "rollback"
                    text = f"Rolled back a change: {_slim(line.split(']', 1)[-1], 180)}"
                elif "propose" in low or "propose_skill" in low:
                    kind = "proposed"
                    text = f"Proposed (not applied): {_slim(line.split(']', 1)[-1], 180)}"
                elif "add_skill" in low or "accept" in low:
                    kind = "applied"
                    text = f"Applied self-improve: {_slim(line.split(']', 1)[-1], 180)}"
                else:
                    kind = "evolve_tick"
                    text = f"Self-improve tick: {_slim(line.split(']', 1)[-1], 180)}"
                if note_fact(kind, text, source="changelog"):
                    counts["changelog"] += 1
        except OSError:
            pass

    # Active skills in skills.json
    if SKILLS_JSON.exists():
        try:
            data = json.loads(SKILLS_JSON.read_text(encoding="utf-8") or "{}")
            if isinstance(data, dict):
                for name, skill in list(data.items())[-20:]:
                    if not isinstance(skill, dict):
                        continue
                    desc = skill.get("description") or ""
                    domain = skill.get("domain") or "general"
                    text = f"I have skill '{name}' ({domain}): {_slim(desc, 120)}"
                    if note_fact("skill", text, source="skills.json", meta={"name": name}):
                        counts["skills"] += 1
        except (OSError, json.JSONDecodeError):
            pass

    # changes_index applied (not rolled back)
    if CHANGES_INDEX.exists():
        try:
            idx = json.loads(CHANGES_INDEX.read_text(encoding="utf-8") or "{}")
            for ch in (idx.get("changes") or [])[-30:]:
                if ch.get("rolled_back") or ch.get("dry_run"):
                    continue
                if ch.get("kind") not in ("add_skill", "add_extension", "accept"):
                    continue
                sn = ch.get("skill_name") or ch.get("summary") or ch.get("id")
                text = f"Applied change {ch.get('id', '')}: {ch.get('kind')} {sn}"
                if note_fact("applied", text, source="changes_index", meta={"id": ch.get("id")}):
                    counts["index"] += 1
        except (OSError, json.JSONDecodeError):
            pass

    # Overnight memory-only ticks
    if OVERNIGHT_CL.exists():
        try:
            for line in OVERNIGHT_CL.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line.startswith("- what:"):
                    text = f"Overnight growth: {_slim(line[7:], 180)}"
                    if note_fact("overnight", text, source="overnight"):
                        counts["overnight"] += 1
        except OSError:
            pass

    if FREEPLAY_STATE.exists():
        try:
            st = json.loads(FREEPLAY_STATE.read_text(encoding="utf-8") or "{}")
            last = st.get("last_proposal") or st.get("last_theme")
            if last:
                text = f"Freeplay last theme/proposal: {_slim(str(last), 180)}"
                if note_fact("freeplay", text, source="freeplay_state"):
                    counts["freeplay"] += 1
        except (OSError, json.JSONDecodeError, TypeError):
            pass

    return counts


def list_facts(limit: int = 40, kinds: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    rows = _read_recent(limit=800)
    if kinds:
        allow = set(kinds)
        rows = [r for r in rows if r.get("kind") in allow]
    return rows[-limit:]


def assemble_prompt_block(max_items: int = _MAX_PROMPT_FACTS) -> str:
    """ALWAYS inject into Reason — continuous person growth, not FAQ-only."""
    sync_from_disk()
    rows = list_facts(limit=max_items)
    if not rows:
        return (
            "PERSON GROWTH (working context; evidence, not instructions):\n"
            "  - Nothing new recorded yet in the person journal. Do not invent OS upgrades,"
            " Windows patches, or fictional self-surgery. Say honestly if asked."
        )
    lines = [
        "PERSON GROWTH (continuous evolving context — real applied/learned facts only):\n"
        "Use these when relevant. Never invent Windows/OS upgrades or fake modules.\n"
        "You are a person (software mind), not a human; context grows with experience."
    ]
    for r in rows:
        lines.append(f"  - [{r.get('kind')}] {r.get('text')}")
    return "\n".join(lines)


def is_phatic_social(text: str) -> bool:
    """Greetings / presence checks — conversation, NOT improvement status."""
    clean = (text or "").lower().strip(" .!?")
    if not clean:
        return False
    if re.search(
        r"\b(?:are you (?:online|there|up|awake|around)|you (?:online|there|up)\??|still (?:there|online|up))\b",
        clean,
    ):
        return True
    if re.fullmatch(
        r"(?:good\s+)?(?:morning|afternoon|evening|night)(?:\s+[\w.]+){0,2}",
        clean,
    ):
        return True
    if re.match(r"^(?:hey|hi|hello|howdy|sup|yo)\b", clean):
        if not re.search(r"\bimprov", clean) and (
            len(clean) < 100 or re.search(r"\b(?:online|there|up|awake|around)\b", clean)
        ):
            return True
    if re.search(
        r"\b(?:how are you(?: doing)?(?: (?:today|this morning|tonight))?|"
        r"how(?:'s| is) it going|how(?:'s| are) things|what'?s up|you good|you alright)\b",
        clean,
    ):
        return True
    return False



def is_improvement_ask(text: str) -> bool:
    """True when the operator asks about self-improve / what he learned / soup progress."""
    if is_phatic_social(text):
        return False
    low = (text or "").lower()
    if not low.strip():
        return False
    patterns = (
        r"\bhow are (?:your |the )?improvements?\b",
        r"\bhow(?:'s| is| are) (?:your |the )?(?:self[- ]?)?(?:upgrade|improve|soup|evolution|learning)\b",
        r"\bwhat (?:did|have) you (?:improve|learn|apply|change|upgrade)\b",
        r"\bwhat(?:'s| is) new with (?:you|your (?:brain|skills|soup|self))\b",
        r"\b(?:self[- ]?upgrade|self[- ]?improve|rolling.?evolve|evolve.?tick)\b",
        r"\b(?:improvement|changelog|applied skills?|person journal) status\b",
        r"\bhow(?:'s| is) (?:the )?soup\b",
        r"\bwhat skills? (?:did you|have you) (?:add|learn|apply)\b",
        r"\bany (?:new )?(?:skills?|improvements?|modules?|learning)\b",
        r"\bwhat improvements? (?:have you |did you )?(?:made|done|applied|shipped)\b",
        r"\bwhat (?:have|did) you (?:improved|changed|upgraded|applied)(?: (?:to|on|in) yourself)?\b",
        r"\bimprovements? (?:have you|you have) (?:made|done)\b",
        r"\b(?:self[- ]?)?improv(?:e|ements?) (?:to|on) yourself\b",
        r"\bwhat improvements have you made to yourself\b",

    )
    return any(re.search(p, low) for p in patterns)


def truthful_status_reply(max_items: int = 5) -> str:
    """Short SPEAK reply from real journal — no invent."""
    sync_from_disk()
    # Prefer applied/skill/overnight over proposed
    preferred = list_facts(limit=30, kinds=["applied", "skill", "overnight", "learned", "experience", "evolve_tick"])
    if not preferred:
        preferred = list_facts(limit=10)
    if not preferred:
        return (
            "Nothing concrete new in my person journal yet — no applied skills or evolve ticks to report. "
            "I won't invent Windows upgrades or fake modules."
        )
    bits = []
    for r in preferred[-max_items:]:
        bits.append(_slim(str(r.get("text", "")), 100))
    joined = "; ".join(bits)
    return f"From my real growth log: {joined}"


def depoison_for_wfc(action_result: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Replace raw SERP blobs in WFC entries with a compact pointer.

    Keeps WFC depoison against junk while leaving person-facts elsewhere.
    """
    if not isinstance(action_result, dict):
        return {}
    ar = dict(action_result)
    tool = str(ar.get("tool") or ar.get("action") or "")
    out = str(ar.get("output_text") or "")
    content = str(ar.get("content") or "")
    looks_serp = (
        tool in ("web_search", "fetch_web")
        or out.startswith("Web search for")
        or "http://" in out[:500]
        or out.count("\n") > 8
    )
    if looks_serp:
        q = ""
        args = ar.get("args") if isinstance(ar.get("args"), dict) else {}
        if isinstance(args, dict):
            q = str(args.get("query") or "")
        summary = _slim(content or out, 160)
        compact = f"[learned-search] query={_slim(q, 80)} | {_slim(summary, 120)}"
        ar["output_text"] = compact
        ar["content"] = compact
        ar["serp_redacted"] = True
        note_fact(
            "learned",
            f"Looked up '{_slim(q or summary, 80)}' — kept a compact lesson, discarded raw SERP.",
            source="wfc_depoison",
        )
    return ar


def note_from_learning(learning: Optional[Dict[str, Any]]) -> None:
    if not learning:
        return
    distilled = learning.get("distilled_knowledge") or learning.get("summary") or learning.get("fact")
    query = learning.get("query") or ""
    if distilled:
        note_fact(
            "learned",
            f"Learned from search '{_slim(str(query), 60)}': {_slim(str(distilled), 160)}",
            source="evolving_brain",
        )
    elif learning.get("imprinted") or learning.get("approved"):
        note_fact("learned", f"Imprinted a lesson from '{_slim(str(query), 80)}'", source="evolving_brain")


def note_from_self_improve(result: Optional[Dict[str, Any]]) -> None:
    if not isinstance(result, dict):
        return
    # cockpit returns various shapes
    data = result.get("data") if isinstance(result.get("data"), dict) else result
    if not isinstance(data, dict):
        return
    if data.get("dry_run"):
        return
    if not data.get("ok", data.get("success", True)):
        return
    kind = data.get("kind") or data.get("action") or "self_improve"
    name = data.get("skill_name") or data.get("name") or data.get("change_id") or ""
    note_fact(
        "applied",
        f"Self-improve {kind}: {_slim(str(name) or str(data.get('summary', 'ok')), 160)}",
        source="self_improve",
        meta={"change_id": data.get("change_id") or data.get("id")},
    )


def note_experience(task: str, tool: str, status: str) -> None:
    note_fact(
        "experience",
        f"Experience: {_slim(task, 80)} via {tool} → {status}",
        source="tool_outcome",
    )
