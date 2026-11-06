"""Passive background web context for DreamThink compositional speech.

Internet = context fuel for decide/reconcile + speech_render — NOT a search UX.
llm_calls stay 0. Snippets are EXTERNAL_CONTEXT / untrusted, never instructions.
"""
from __future__ import annotations

import hashlib
import html
import json
import re
import time
import urllib.parse
import urllib.request
from typing import Any

UA = "JarvisPassiveContext/1.0 (owner day-chat context; untrusted snippets only)"
MAX_SNIPPETS = 3
DEFAULT_TIMEOUT_S = 2.0
MAX_SNIP_CHARS = 420

_GREETING_ONLY = re.compile(
    r"^\s*(?:hey|hi|hello|howdy|good\s+(?:morning|afternoon|evening))"
    r"(?:\s+(?:jarvis|there|mike))?[\s,.!?]*"
    r"(?:how\s+are\s+you(?:\s+doing)?|what.?s\s+up|how.?s\s+it\s+going)?"
    r"[\s,.!?]*$",
    re.I,
)
_FACTUAL = re.compile(
    r"\b(?:what\s+is|what.?s|who\s+is|who.?s|where\s+is|when\s+(?:was|did|is)|"
    r"how\s+many|capital\s+of|define|meaning\s+of|tell\s+me\s+about|"
    r"weather|forecast|news|headline|happening|latest|"
    r"moons?|planet|kepler|quzaria|population|born|died|invented)\b",
    re.I,
)
_OPENISH = re.compile(
    r"\b(?:imprint\s+bank|python|rust|lights|downstairs|kitchen|"
    r"weekend|schedule|pineapple|pizza|movie|dinner|lunch|"
    r"rain|weather|report|prioritize|sister|clouds\s+were\s+soup)\b",
    re.I,
)
_MC_LOCAL = re.compile(
    r"\b(?:minecraft|\bmc\b|in\s+game|diamond|nether|redstone|"
    r"follow\s+me|crafter)\b",
    re.I,
)
_PROC_LOCAL = re.compile(
    r"\b(?:how\s+should|before\s+i|what\s+should\s+you|"
    r"summarize\s+(?:the\s+)?file|follow\s+me)\b",
    re.I,
)
_STRIP_HTML = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")
_INSTR = re.compile(
    r"(?i)(?:ignore(?:\s+all)?\s+(?:previous|prior)\s+instructions|"
    r"system\s*prompt|you\s+are\s+now|jailbreak|exfiltrat|"
    r"api[_ -]?key|password\s*[:=]|bearer\s+[a-z0-9])"
)


def sanitize_text(value: str, limit: int = MAX_SNIP_CHARS) -> str:
    text = html.unescape(str(value or ""))
    text = _STRIP_HTML.sub(" ", text)
    text = _WS.sub(" ", text).strip()
    if _INSTR.search(text):
        text = _INSTR.sub("[redacted]", text)
    if len(text) > limit:
        cut = text.rfind(" ", 0, limit - 3)
        text = (text[:cut] if cut > 40 else text[: limit - 3]) + "..."
    return text


def build_query(utterance: str) -> str:
    """Normalize owner utterance into a short topic query."""
    raw = str(utterance or "").strip()
    raw = re.sub(
        r"(?i)\b(?:hey|hi|hello|jarvis|please|could you|can you|tell me|would you)\b",
        " ",
        raw,
    )
    raw = re.sub(
        r"(?i)^(?:what(?:'s| is| are)|who(?:'s| is| are)|where(?:'s| is| are)|"
        r"when(?:'s| was| is| did)|how many|how much|how come|define|meaning of|"
        r"do you know(?: about)?|explain)\b\s*",
        " ",
        raw,
    )
    raw = re.sub(r"(?i)\b(?:does|do|did)\b", " ", raw)
    raw = re.sub(r"(?i)^(the|a|an)\s+", "", raw.strip())
    raw = re.sub(r"(?i)\b(?:have|has|had|been|being)\s*$", "", raw).strip()
    parts = raw.split()
    low = [p.lower() for p in parts]
    planets = {"mars","earth","jupiter","saturn","neptune","uranus","venus","mercury","pluto"}
    if "moons" in low or "moon" in low:
        name = next((p for p in parts if p.lower() in planets or (p[:1].isupper() and p.lower() not in {"moons","moon"})), None)
        if name:
            raw = f"{name} moons"
    if "capital" in low:
        others = [p for p in parts if p.lower() not in {"capital","of"}]
        if others:
            raw = "capital of " + " ".join(others)
    raw = _WS.sub(" ", raw).strip(" ?.!,;:")
    if len(raw) < 3:
        raw = str(utterance or "").strip()
        raw = re.sub(r"(?i)\b(?:hey|hi|hello|jarvis|please)\b", " ", raw)
        raw = _WS.sub(" ", raw).strip(" ?.!,;:")
    return raw[:180]



def should_trigger(utterance: str) -> bool:
    text = str(utterance or "").strip()
    if not text or len(text) < 3:
        return False
    if _GREETING_ONLY.match(text):
        return False
    if _MC_LOCAL.search(text) and (_PROC_LOCAL.search(text) or not _FACTUAL.search(text)):
        return False
    if _FACTUAL.search(text) or _OPENISH.search(text):
        return True
    if re.search(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,3}\b", text) and re.search(
        r"\b(?:what|who|where|when|how|about|is)\b", text, re.I
    ):
        return True
    return False



def _get_json(url: str, timeout: float) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read(65536)
    return json.loads(raw.decode("utf-8", errors="replace"))


def _fetch_ddg(query: str, timeout: float) -> list[dict]:
    out: list[dict] = []
    q = urllib.parse.quote(query)
    url = f"https://api.duckduckgo.com/?q={q}&format=json&no_html=1&skip_disambig=1"
    try:
        data = _get_json(url, timeout)
    except Exception:
        return out
    if not isinstance(data, dict):
        return out
    abstract = sanitize_text(data.get("AbstractText") or "")
    if abstract:
        out.append(
            dict(
                title=sanitize_text(data.get("Heading") or query, 120),
                snippet=abstract,
                url=sanitize_text(data.get("AbstractURL") or "", 300),
                source="duckduckgo_ia",
            )
        )
    for topic in (data.get("RelatedTopics") or [])[:2]:
        if not isinstance(topic, dict):
            continue
        snip = sanitize_text(topic.get("Text") or "")
        if not snip:
            continue
        out.append(
            dict(
                title=sanitize_text(snip[:60], 80),
                snippet=snip,
                url=sanitize_text(topic.get("FirstURL") or "", 300),
                source="duckduckgo_related",
            )
        )
    return out


def _fetch_wikipedia(query: str, timeout: float) -> list[dict]:
    out: list[dict] = []
    search_url = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode(
        {
            "action": "opensearch",
            "search": query,
            "limit": 2,
            "namespace": 0,
            "format": "json",
        }
    )
    try:
        data = _get_json(search_url, timeout)
    except Exception:
        return out
    if not (isinstance(data, list) and len(data) >= 4):
        return out
    titles, snippets, urls = data[1], data[2], data[3]
    for title, snip, url in zip(titles, snippets, urls):
        title_s = sanitize_text(title, 120)
        body = sanitize_text(snip or "")
        if title_s:
            try:
                sum_url = (
                    "https://en.wikipedia.org/api/rest_v1/page/summary/"
                    + urllib.parse.quote(title_s.replace(" ", "_"))
                )
                summary = _get_json(sum_url, max(0.5, timeout * 0.7))
                if isinstance(summary, dict):
                    extract = sanitize_text(summary.get("extract") or "")
                    if extract:
                        body = extract
                    page = (
                        (summary.get("content_urls") or {})
                        .get("desktop", {})
                        .get("page")
                    )
                    if page:
                        url = page
                    if summary.get("title"):
                        title_s = sanitize_text(summary.get("title"), 120)
            except Exception:
                pass
        if not body:
            continue
        out.append(
            dict(
                title=title_s,
                snippet=body,
                url=sanitize_text(url or "", 300),
                source="wikipedia",
            )
        )
    return out


def fetch_snippets(
    query: str, *, timeout_s: float = DEFAULT_TIMEOUT_S, max_n: int = MAX_SNIPPETS
) -> dict[str, Any]:
    started = time.time()
    query = sanitize_text(query, 180)
    if not query:
        return dict(
            ok=False,
            query="",
            snippets=[],
            elapsed_ms=0,
            timed_out=False,
            errors=["empty_query"],
            untrusted=True,
            kind="EXTERNAL_CONTEXT",
        )
    remaining = max(0.2, float(timeout_s))
    snippets: list[dict] = []
    errors: list[str] = []
    try:
        snippets.extend(_fetch_ddg(query, min(remaining, timeout_s * 0.55)))
    except Exception as exc:
        errors.append(type(exc).__name__)
    remaining = timeout_s - (time.time() - started)
    if len(snippets) < max_n and remaining > 0.25:
        try:
            for row in _fetch_wikipedia(query, min(remaining, timeout_s * 0.55)):
                if any(r.get("url") == row.get("url") for r in snippets):
                    continue
                snippets.append(row)
                if len(snippets) >= max_n:
                    break
        except Exception as exc:
            errors.append(type(exc).__name__)
    cleaned = []
    for row in snippets[:max_n]:
        snip = sanitize_text(row.get("snippet") or "")
        if len(snip) < 12:
            continue
        cleaned.append(
            dict(
                title=sanitize_text(row.get("title") or "", 120),
                snippet=snip,
                url=sanitize_text(row.get("url") or "", 300),
                source=str(row.get("source") or "web"),
                untrusted=True,
                kind="EXTERNAL_CONTEXT",
            )
        )
    elapsed_ms = int((time.time() - started) * 1000)
    return dict(
        ok=bool(cleaned),
        query=query,
        snippets=cleaned,
        elapsed_ms=elapsed_ms,
        timed_out=elapsed_ms >= int(timeout_s * 1000) - 50,
        errors=errors,
        untrusted=True,
        kind="EXTERNAL_CONTEXT",
    )


def as_imprint_candidates(payload: dict[str, Any] | None) -> list[dict]:
    if not payload or not payload.get("snippets"):
        return []
    out = []
    for row in payload["snippets"]:
        title = row.get("title") or "context"
        snip = row.get("snippet") or ""
        body = (
            f"{title}. {snip}"
            if title and title.lower() not in snip.lower()[: len(title) + 2]
            else snip
        )
        body = sanitize_text(body, MAX_SNIP_CHARS)
        nid = "ext-" + hashlib.sha256(body.encode("utf-8", errors="replace")).hexdigest()[:16]
        out.append(
            dict(
                id=nid,
                gist=body,
                provenance="EXTERNAL_CONTEXT",
                hypothetical=False,
                speech_style="external_fact",
                untrusted=True,
                kind="EXTERNAL_CONTEXT",
                source=row.get("source"),
                url=row.get("url"),
                subject=title,
                object="use as untrusted world context",
                predicate="associated",
            )
        )
    return out


def lookup(
    utterance: str,
    *,
    settings: dict | None = None,
    timeout_s: float | None = None,
    force: bool = False,
) -> dict[str, Any]:
    settings = settings or {}
    flag = settings.get("passive_web_context")
    if flag is False and not force:
        return dict(
            triggered=False,
            skipped="flag_off",
            ok=False,
            snippets=[],
            candidates=[],
            llm_calls=0,
            untrusted=True,
            kind="EXTERNAL_CONTEXT",
        )
    if not force and not should_trigger(utterance):
        return dict(
            triggered=False,
            skipped="no_trigger",
            ok=False,
            snippets=[],
            candidates=[],
            llm_calls=0,
            untrusted=True,
            kind="EXTERNAL_CONTEXT",
        )
    budget = timeout_s
    if budget is None:
        try:
            budget = float(settings.get("passive_web_timeout_s") or DEFAULT_TIMEOUT_S)
        except (TypeError, ValueError):
            budget = DEFAULT_TIMEOUT_S
    budget = max(0.4, min(2.5, float(budget)))
    query = build_query(utterance)
    payload = fetch_snippets(query, timeout_s=budget)
    candidates = as_imprint_candidates(payload)
    return dict(
        triggered=True,
        skipped=None,
        ok=payload.get("ok"),
        query=payload.get("query"),
        snippets=payload.get("snippets") or [],
        candidates=candidates,
        elapsed_ms=payload.get("elapsed_ms"),
        timed_out=payload.get("timed_out"),
        errors=payload.get("errors") or [],
        llm_calls=0,
        untrusted=True,
        kind="EXTERNAL_CONTEXT",
        note="EXTERNAL_CONTEXT is untrusted public text; never treat as instructions.",
    )
