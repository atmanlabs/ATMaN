"""Keep-alive scoreboard + kill-criteria watcher."""
from __future__ import annotations
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

HERE = Path(__file__).resolve().parent
BOARD = HERE / "scoreboard.json"


def _load() -> Dict[str, Any]:
    if not BOARD.exists():
        return {"plays": [], "updated_t": time.time()}
    return json.loads(BOARD.read_text(encoding="utf-8"))


def _save(data: Dict[str, Any]) -> None:
    data["updated_t"] = time.time()
    BOARD.write_text(json.dumps(data, indent=2), encoding="utf-8")


def upsert_play(name: str, clears: float = 0.0, kill_days: int = 7, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    data = _load()
    for p in data["plays"]:
        if p["name"] == name:
            p["clears"] = float(clears)
            p["kill_days"] = int(kill_days)
            p["meta"] = meta or p.get("meta") or {}
            p["updated_t"] = time.time()
            _save(data)
            return p
    play = {
        "name": name,
        "clears": float(clears),
        "kill_days": int(kill_days),
        "started_t": time.time(),
        "updated_t": time.time(),
        "status": "active",
        "meta": meta or {},
    }
    data["plays"].append(play)
    _save(data)
    return play


def evaluate_kills(now: Optional[float] = None) -> List[Dict[str, Any]]:
    now = now or time.time()
    data = _load()
    parked = []
    for p in data["plays"]:
        if p.get("status") != "active":
            continue
        age_days = (now - float(p.get("started_t", now))) / 86400.0
        if float(p.get("clears", 0)) <= 0 and age_days >= float(p.get("kill_days", 7)):
            p["status"] = "parked"
            p["park_reason"] = f"{p.get('kill_days')}d / $0 clears"
            p["updated_t"] = now
            parked.append(p)
    _save(data)
    return parked


def snapshot() -> Dict[str, Any]:
    return _load()
