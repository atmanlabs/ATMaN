"""Freeplay idle skill proposer — gated drafts only (no sealed-core writes).

During idle / freeplay ticks, draft a skill idea from recent significant events /
operator chat themes and park it via SelfImproveEngine.propose_skill.
Safe skills (esp. Minecraft) auto-apply after safety fence. Unsafe = REFUSED. Operator does not approve routine applies.
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

HERE = Path(__file__).resolve().parent
EXO_ROOT = HERE.parent
STATE_PATH = HERE / "freeplay_state.json"

_TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z0-9_]{2,}")
_STOP = frozenset({
    "the", "and", "for", "with", "that", "this", "from", "have", "want",
    "ambient", "idle", "sensory", "check", "operator", "owner", "atman",
    "minecraft", "while", "were", "gone", "about", "into", "your", "then",
})



def _coerce_for_repo(skill: Dict[str, Any]) -> Dict[str, Any]:
    """Make a draft storeable: lowercase name; minecraft steps must be action dicts."""
    import re
    out = dict(skill or {})
    name = str(out.get("name") or "freeplay_skill").strip().lower()
    name = re.sub(r"[^a-z0-9_]+", "_", name).strip("_")[:48]
    if not name or not name[0].isalnum():
        name = "freeplay_skill"
    out["name"] = name
    domain = str(out.get("domain") or "freeplay").strip().lower()
    out["domain"] = domain

    steps = out.get("steps")
    if domain == "minecraft":
        need = True
        if isinstance(steps, list) and steps and all(isinstance(s, dict) and s.get("action") for s in steps):
            need = False
        if need:
            theme = str(out.get("description") or name)
            # Default safe dojo assist: locate + approach (executable schema, leash-bounded)
            block_guess = "chest"
            for b in ("chest", "oak_log", "wheat", "cobblestone", "crafting_table", "furnace"):
                if b.replace("_", " ") in theme.lower() or b in theme.lower() or b in name:
                    block_guess = b
                    break
            out["steps"] = [
                {
                    "step": 1,
                    "action": "locate_target",
                    "description": f"Find nearest {block_guess} related to {name}",
                    "params": {"block_types": [block_guess]},
                },
                {
                    "step": 2,
                    "action": "approach_target",
                    "description": f"Approach {block_guess} within safe leash",
                    "params": {},
                },
            ]
            out.setdefault("preconditions", {})
            if isinstance(out["preconditions"], dict):
                out["preconditions"].setdefault("max_range", 32)
    else:
        # Non-minecraft: keep list of strings OR dicts; engine/repo allows non-MC freely
        if not isinstance(steps, list) or not steps:
            out["steps"] = ["observe", "assist_safely", "log_result"]
        else:
            # convert string steps to simple dicts for consistency (optional)
            out["steps"] = steps
    return out


def _load_self_improve_config() -> Dict[str, Any]:
    try:
        from config import Config
        section = Config().get("self_improve", default={}) or {}
        return section if isinstance(section, dict) else {}
    except Exception:
        return {}


def _read_state() -> Dict[str, Any]:
    if not STATE_PATH.exists():
        return {}
    try:
        data = json.loads(STATE_PATH.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _write_state(state: Dict[str, Any]) -> None:
    tmp = STATE_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2), encoding="utf-8")
    tmp.replace(STATE_PATH)


def _recent_event_texts(limit: int = 12) -> List[str]:
    texts: List[str] = []
    candidates = [
        EXO_ROOT / "significant_events.json",
        EXO_ROOT / "significant_events.json",
    ]
    try:
        from config import Config
        cfg = Config()
        for key in ("significant_events_path", "significant_events_path"):
            rel = cfg.get("storage", key, default=None)
            if rel:
                candidates.insert(0, EXO_ROOT / str(rel))
    except Exception:
        pass

    for path in candidates:
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if isinstance(data, list):
            events = data
        elif isinstance(data, dict):
            events = data.get("events") or data.get("items") or data.get("log") or []
        else:
            events = []
        for ev in events[-limit:]:
            if isinstance(ev, dict):
                raw = ev.get("raw") or ev.get("text") or ev.get("summary") or ""
                src = str(ev.get("source", ""))
                if raw:
                    texts.append(f"{src}: {raw}" if src else str(raw))
            elif isinstance(ev, str):
                texts.append(ev)
        if texts:
            break
    return texts


def _theme_tokens(texts: List[str]) -> List[str]:
    counts: Dict[str, int] = {}
    for t in texts:
        for tok in _TOKEN_RE.findall(t.lower()):
            if tok in _STOP or len(tok) < 4:
                continue
            counts[tok] = counts.get(tok, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))
    return [t for t, _ in ranked[:6]]


def _draft_skill(context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Heuristic skill draft — no cloud LLM."""
    context = context or {}
    texts: List[str] = list(context.get("recent_texts") or [])
    texts.extend(_recent_event_texts())

    for key in ("wfc", "wfc_traces", "operator_chat", "recent_chat"):
        blob = context.get(key) or []
        if isinstance(blob, list):
            for item in blob[-8:]:
                if isinstance(item, dict):
                    texts.append(str(item.get("raw") or item.get("text") or item.get("content") or ""))
                else:
                    texts.append(str(item))
        elif isinstance(blob, str) and blob.strip():
            texts.append(blob)

    themes = _theme_tokens(texts)
    drive = str(context.get("drive_id") or context.get("drive") or "")

    if themes:
        primary = themes[0]
        skill_name = re.sub(r"[^A-Za-z0-9_]", "_", f"freeplay_{primary}")[:40]
        if not skill_name or not skill_name[0].isalpha():
            skill_name = "freeplay_theme"
        fingerprint = hashlib.sha1("|".join(themes).encode("utf-8")).hexdigest()[:6]
        skill_name = f"{skill_name}_{fingerprint}"
        mc_hints = ("mine", "craft", "block", "ore", "farm", "mob", "creeper",
                    "village", "nether", "diamond", "sword", "pickaxe", "dojo",
                    "sanctuary", "inventory", "build", "patrol", "survival")
        looks_mc = any(h in primary or any(h in t for t in themes) for h in mc_hints)
        domain = "minecraft" if looks_mc else "freeplay"
        return {
            "name": skill_name,
            "domain": domain,
            "description": (
                f"Freeplay draft around theme '{primary}' "
                f"(themes={', '.join(themes[:4])}). Safety-gated auto-apply when eligible."
            ),
            "preconditions": {"mode": "freeplay_idle"},
            "steps": [
                f"Observe recent context related to {primary}",
                f"Prepare a safe, leash-bounded assist for {primary}",
                "Never touch sealed core / credentials / offensive tooling",
            ],
            "effects": {"improves": domain},
            "governance": {
                "requires_supervision": False,
                "judge_gated": False,
                "auto_apply": True,
                "source": "freeplay_proposer",
            },
        }

    templates = [
        {
            "name": "freeplay_sanctuary_patrol_assist",
            "domain": "minecraft",
            "description": "Freeplay draft: leash-bounded sanctuary patrol — locate and approach perimeter markers.",
            "steps": [
                {"step": 1, "action": "locate_target", "description": "Find sanctuary marker block", "params": {"block_types": ["torch"]}},
                {"step": 2, "action": "approach_target", "description": "Approach marker within safe leash", "params": {}},
            ],
        },
        {
            "name": "freeplay_chest_ready_check",
            "domain": "minecraft",
            "description": "Freeplay draft: locate and approach storage chest for readiness check.",
            "steps": [
                {"step": 1, "action": "locate_target", "description": "Find nearest chest", "params": {"block_types": ["chest"]}},
                {"step": 2, "action": "approach_target", "description": "Approach chest", "params": {}},
            ],
        },
        {
            "name": "freeplay_skill_practice_note",
            "domain": "learning",
            "description": "Freeplay draft: capture a practice note from idle curiosity drive.",
            "steps": [
                "Pick one known safe skill near base",
                "Practice mentally / log technique notes",
                "Log practice note into skill library if safety fence passes",
            ],
        },
    ]
    idx = int(time.time() // 3600) % len(templates)
    if any(k in drive for k in ("tidy", "safe", "sanctuary")):
        idx = 0
    elif any(k in drive for k in ("useful", "operator", "inventory")):
        idx = 1
    elif any(k in drive for k in ("practice", "skill", "learn")):
        idx = 2
    chosen = templates[idx]
    return {
        "name": chosen["name"],
        "domain": chosen["domain"],
        "description": chosen["description"],
        "preconditions": {"mode": "freeplay_idle", "requires_supervision": True},
        "steps": list(chosen["steps"]),
        "effects": {"skills_json": "unchanged_until_accept"},
        "governance": {
            "requires_supervision": True,
            "judge_gated": True,
            "auto_apply": False,
            "source": "freeplay_proposer",
        },
    }


def maybe_propose(context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Rate-limited freeplay propose hook. Returns result dict or None if disabled.

    Safe to call from MindLoop ambient idle and relay /initiative/pending.
    Never writes sealed core. skills.json unchanged unless auto_apply_proposals
    is explicitly true (default false).
    """
    context = context or {}
    section = _load_self_improve_config()
    enabled = bool(section.get("freeplay_propose", True))
    if context.get("force"):
        enabled = True
    if not enabled:
        return None

    mode = str(context.get("mode") or context.get("source") or "idle").lower()
    idle_modes = {"idle", "freeplay", "ambient", "initiative", "overnight", "player_away"}
    if mode not in idle_modes and not context.get("force"):
        return None

    min_interval = float(section.get("freeplay_min_interval_sec", 900))
    state = _read_state()
    now = time.time()
    last = float(state.get("last_propose_ts") or 0)
    if not context.get("force") and last and (now - last) < min_interval:
        return {
            "ok": True,
            "skipped": True,
            "reason": "rate_limited",
            "retry_in_sec": max(0, int(min_interval - (now - last))),
            "last_propose_ts": last,
        }

    skill = context.get("skill") if isinstance(context.get("skill"), dict) else _draft_skill(context)
    skill = _coerce_for_repo(skill)

    from self_improve.engine import engine
    from self_improve.safety import safety_check_skill

    safety = safety_check_skill(skill)
    if not safety.get("ok"):
        # Refuse unsafe skills outright — changelog via propose failure path + local note
        refuse = {
            "ok": False,
            "refused": True,
            "auto_applied": False,
            "safety": safety,
            "skill_name": (skill or {}).get("name"),
            "message": safety.get("message") or "REFUSED by safety fence",
        }
        try:
            engine._append_changelog(
                f"- [{__import__('datetime').datetime.now().astimezone().isoformat()}] "
                f"REFUSED skill={(skill or {}).get('name')} reasons={';'.join(safety.get('reasons') or [])}"
            )
        except Exception:
            pass
        state["last_propose_ts"] = now
        state["last_ok"] = False
        state["last_refused"] = (skill or {}).get("name")
        _write_state(state)
        return refuse

    result = engine.propose_skill(skill, source=str(context.get("propose_source") or "freeplay"))
    state["last_propose_ts"] = now
    state["last_change_id"] = result.get("change_id")
    state["last_skill_name"] = result.get("skill_name")
    state["last_ok"] = bool(result.get("ok"))
    _write_state(state)

    # Operator lock: auto-apply safe skills; no operator approve for Minecraft/etc.
    auto_cfg = section.get("auto_apply_proposals", True)
    require_safety = section.get("auto_apply_requires_safety", True)
    if isinstance(auto_cfg, str):
        auto_cfg = auto_cfg.strip().lower() in ("1", "true", "yes", "on")
    if isinstance(require_safety, str):
        require_safety = require_safety.strip().lower() in ("1", "true", "yes", "on")

    eligible = bool(safety.get("auto_apply_eligible")) if require_safety else True
    if auto_cfg and eligible and result.get("ok") and result.get("change_id"):
        accept = engine.accept_proposal(str(result["change_id"]), dry_run=False)
        result = {
            **result,
            "auto_applied": bool(accept.get("ok")),
            "accept_result": accept,
            "safety": safety,
            "message": (
                f"AUTO-APPLIED {result.get('skill_name')} (safety OK)"
                if accept.get("ok")
                else f"proposed but apply failed: {accept.get('error')}"
            ),
        }
        try:
            engine._append_changelog(
                f"- [{__import__('datetime').datetime.now().astimezone().isoformat()}] "
                f"AUTO-APPLY {result.get('change_id')} skill={result.get('skill_name')} "
                f"ok={bool(accept.get('ok'))}"
            )
        except Exception:
            pass
    else:
        result = {
            **result,
            "auto_applied": False,
            "safety": safety,
            "parked": True,
            "message": result.get("message") or "parked (not auto-apply eligible)",
        }

    return result
