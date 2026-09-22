"""Receipt ledger — every money claim cites source + timestamp."""
from __future__ import annotations
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

HERE = Path(__file__).resolve().parent
LEDGER = HERE / "ledger.jsonl"


def record(claim: str, source: str, amount: Optional[float] = None, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    row = {
        "t": time.time(),
        "claim": claim,
        "source": source,
        "amount": amount,
        "meta": meta or {},
    }
    HERE.mkdir(parents=True, exist_ok=True)
    with LEDGER.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
    return row


def recent(limit: int = 20) -> List[Dict[str, Any]]:
    if not LEDGER.exists():
        return []
    lines = LEDGER.read_text(encoding="utf-8").splitlines()
    out = []
    for line in lines[-limit:]:
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out
