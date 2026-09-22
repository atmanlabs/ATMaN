"""Rolling self-evolution — continuous scout→apply→advance. Sealed core never touched.

Operator lock (2026-09-22): evolving is the purpose. Not one-shot "ok I did it."
"""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

HERE = Path(__file__).resolve().parent
STATE_PATH = HERE / "evolve_state.json"

# Rotate topics so he doesn't keep finding the same voice repo
QUERY_ROTATION: List[str] = [
    "github local AI voice assistant open source python",
    "github minecraft bot pathfinding agent javascript",
    "github local LLM memory RAG agent python",
    "github tool use function calling agent framework",
    "github piper tts faster-whisper voice pipeline",
    "github personal AI companion desktop automation",
    "github self improving agent sandbox skills",
    "github openclaw alternative local agent gateway",
    "github multimodal camera observation agent",
    "github minecraft mineflayer skill learning bot",
]


def _cfg() -> Dict[str, Any]:
    try:
        from config import Config
        section = Config().get("self_improve", default={}) or {}
        return section if isinstance(section, dict) else {}
    except Exception:
        return {}


def _read_state() -> Dict[str, Any]:
    if not STATE_PATH.exists():
        return {"query_index": 0, "last_tick_ts": 0, "seen_repos": [], "ticks": 0}
    try:
        data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {"query_index": 0, "last_tick_ts": 0, "seen_repos": [], "ticks": 0}


def _write_state(state: Dict[str, Any]) -> None:
    tmp = STATE_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2), encoding="utf-8")
    tmp.replace(STATE_PATH)


def _next_query(state: Dict[str, Any]) -> str:
    idx = int(state.get("query_index") or 0) % len(QUERY_ROTATION)
    q = QUERY_ROTATION[idx]
    state["query_index"] = idx + 1
    # Bias away from already-seen repo names
    seen = state.get("seen_repos") or []
    if seen:
        last = str(seen[-1]).rstrip("/").split("/")[-1]
        if last:
            q = f"{q} -{last}"
    return q


def _web_search(query: str) -> Dict[str, Any]:
    """Best-effort search via Cockpit tool path."""
    try:
        from config import Config
        from cockpit import Cockpit
        cockpit = Cockpit(Config())
        res = cockpit.execute_tool("web_search", {"query": query, "max_results": 5})
        if isinstance(res, dict):
            return {
                "ok": bool(res.get("success")),
                "query": query,
                "results": (res.get("data") or {}).get("results") if isinstance(res.get("data"), dict) else res.get("data"),
                "output": res.get("output") or "",
            }
    except Exception as e:
        return {"ok": False, "query": query, "error": str(e), "results": [], "output": ""}
    return {"ok": False, "query": query, "results": [], "output": ""}


def _advance_stubs(engine) -> List[str]:
    """Bump parked scout stubs one generation — continuous refinement."""
    advanced = []
    ext_dir = HERE / "extensions"
    if not ext_dir.exists():
        return advanced
    for path in sorted(ext_dir.glob("scout_*.py")):
        try:
            src = path.read_text(encoding="utf-8")
        except Exception:
            continue
        if "STATUS = \"parked_stub\"" in src:
            gen = 1
            new = src.replace("STATUS = \"parked_stub\"", 'STATUS = "evolving_gen_1"', 1)
        elif 'STATUS = "evolving_gen_' in src:
            import re
            m = re.search(r'STATUS = "evolving_gen_(\d+)"', src)
            gen = int(m.group(1)) + 1 if m else 2
            if gen > 8:
                continue  # cap churn; still rolling via new scouts
            new = re.sub(r'STATUS = "evolving_gen_\d+"', f'STATUS = "evolving_gen_{gen}"', src, count=1)
        else:
            continue
        # Append generation note once
        marker = f"# evolve_tick_gen_{gen}"
        if marker not in new:
            new = new.rstrip() + f"\n\n{marker}\nDEFICIT = \"needs concrete capability wired\"\n"
        try:
            r = engine.add_extension_module(path.stem, new, dry_run=False)
            if r.get("ok"):
                advanced.append(path.name)
        except Exception:
            continue
    return advanced


def maybe_evolve(context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Rate-limited rolling evolution tick. Safe to call from idle / initiative / chat orders."""
    context = context or {}
    section = _cfg()
    enabled = bool(section.get("rolling_evolve", True))
    if context.get("force"):
        enabled = True
    if not enabled:
        return None

    min_interval = float(section.get("rolling_evolve_interval_sec", 600))
    state = _read_state()
    now = time.time()
    last = float(state.get("last_tick_ts") or 0)
    if not context.get("force") and last and (now - last) < min_interval:
        return {
            "ok": True,
            "skipped": True,
            "reason": "rate_limited",
            "retry_in_sec": max(0, int(min_interval - (now - last))),
        }

    from self_improve.engine import engine

    query = _next_query(state)
    search = _web_search(query)
    ingest = engine.ingest_scout_results(
        {
            "query": query,
            "results": search.get("results") or [],
            "output": search.get("output") or "",
        },
        source="rolling_evolve",
    )

    # Track seen repos
    seen = list(state.get("seen_repos") or [])
    for u in ingest.get("urls") or []:
        if u not in seen:
            seen.append(u)
    state["seen_repos"] = seen[-50:]

    advanced = _advance_stubs(engine)
    state["last_tick_ts"] = now
    state["ticks"] = int(state.get("ticks") or 0) + 1
    state["last_query"] = query
    state["last_applied"] = ingest.get("applied_skills") or []
    state["last_extensions"] = ingest.get("extensions") or []
    state["last_advanced"] = advanced
    _write_state(state)

    try:
        engine._append_changelog(
            f"- rolling_evolve tick={state['ticks']} query={query!r} "
            f"applied={len(state['last_applied'])} ext={len(state['last_extensions'])} "
            f"advanced_stubs={len(advanced)}"
        )
    except Exception:
        pass

    return {
        "ok": True,
        "rolling": True,
        "tick": state["ticks"],
        "query": query,
        "search_ok": search.get("ok"),
        "ingest": ingest,
        "advanced_stubs": advanced,
        "improved": bool(ingest.get("improved") or advanced),
    }
