"""Local offline work queue. Survives usage death; no cloud required."""
from __future__ import annotations
import json
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

HERE = Path(__file__).resolve().parent
QUEUE_PATH = HERE / "queue.json"


def _load() -> Dict[str, Any]:
    if not QUEUE_PATH.exists():
        return {"version": 1, "jobs": []}
    return json.loads(QUEUE_PATH.read_text(encoding="utf-8"))


def _save(data: Dict[str, Any]) -> None:
    QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    QUEUE_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")


def enqueue(kind: str, payload: Dict[str, Any], priority: int = 100) -> str:
    data = _load()
    job_id = uuid.uuid4().hex[:12]
    data["jobs"].append({
        "id": job_id,
        "kind": kind,
        "payload": payload,
        "priority": int(priority),
        "status": "pending",
        "created_t": time.time(),
        "updated_t": time.time(),
        "result": None,
        "error": None,
    })
    data["jobs"].sort(key=lambda j: (j.get("priority", 100), j.get("created_t", 0)))
    _save(data)
    return job_id


def list_jobs(status: Optional[str] = None) -> List[Dict[str, Any]]:
    jobs = _load().get("jobs", [])
    if status:
        return [j for j in jobs if j.get("status") == status]
    return jobs


def claim_next() -> Optional[Dict[str, Any]]:
    data = _load()
    for job in data["jobs"]:
        if job.get("status") == "pending":
            job["status"] = "running"
            job["updated_t"] = time.time()
            _save(data)
            return job
    return None


def complete(job_id: str, result: Any = None, error: Optional[str] = None) -> bool:
    data = _load()
    for job in data["jobs"]:
        if job.get("id") == job_id:
            job["status"] = "error" if error else "done"
            job["result"] = result
            job["error"] = error
            job["updated_t"] = time.time()
            _save(data)
            return True
    return False
