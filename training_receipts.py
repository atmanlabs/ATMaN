"""Read-only adapter for completed local training reports.

Pattern: validated training reports are read as evidence alongside live
memory/action lookups. The adapter summarizes what the reports record --
never mastery, feelings, or weight changes. Reports live outside this
module; point ATMAN_TRAINING_REPORTS at the directory holding them.

Expected report layout (JSON):
  practice.json -- list of {"prompt": str, "result": {"ok": bool, "reply": str}}
  after.json    -- list of follow-up probe records, same shape

Only structurally valid, fully-ok runs are summarized. Anything else
yields no records, and the caller falls back to its normal behavior.
"""
import json
import os
from pathlib import Path


def reports_dir():
    configured = os.environ.get("ATMAN_TRAINING_REPORTS")
    if configured:
        return Path(configured)
    return Path(__file__).with_name("training") / "reports"


def _load_valid(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    if not isinstance(data, list) or not data:
        return None
    for turn in data:
        if not isinstance(turn, dict):
            return None
        result = turn.get("result", {})
        if not result.get("ok") or not result.get("reply"):
            return None
    return data


def _subjects(prompts):
    """Distinctive subject words across prompts, minus generic filler."""
    filler = {"practice", "game", "sandbox", "notes", "records", "learned",
              "learning", "playing", "remember", "memory", "memories",
              "experience", "what", "your", "about", "this", "that", "with",
              "from", "have", "tell"}
    seen = []
    for prompt in prompts:
        for word in str(prompt).casefold().split():
            word = "".join(c for c in word if c.isalnum())
            if len(word) > 3 and word not in filler and word not in seen:
                seen.append(word)
    return seen[:6]


def records():
    """Bounded summary of validated training reports. Empty list if invalid."""
    base = reports_dir()
    practice = _load_valid(base / "practice.json")
    after = _load_valid(base / "after.json")
    if practice is None:
        return []
    prompts = [t.get("prompt", "") for t in practice]
    subjects = _subjects(prompts)
    subject_text = (" covering " + ", ".join(subjects)) if subjects else ""
    game = str(practice[0].get("game", "semantic training")) if practice else "semantic training"
    memory = (
        "My recorded %s included %d practice turns through my real chat "
        "pipeline%s. " % (game, len(practice), subject_text)
    )
    if after:
        memory += "%d follow-up conversation probes were recorded. " % len(after)
    memory += ("These records establish practice, not lasting improvement or "
               "feelings afterward. The training used shared conversation rules; "
               "this is not evidence that my model weights changed.")
    return [{"source": "training_report_adapter", "memory": memory}]


def plain_excerpt_fallback(sources, state):
    """Use only exact selected passages from validated host reports.

    Called when generated prose fails its grounding check: instead of a
    generic fallback, answer with verbatim passages the host selected from
    reports this adapter validated. Never invents, never paraphrases.
    """
    if state not in ("known", "partial"):
        return None
    reports = [r["memory"] for r in records()]
    if not sources or not reports:
        return None
    if not all(isinstance(s, str) and len(s) > 30 and any(s in r for r in reports)
               for s in sources):
        return None
    answer = " ".join(sources)
    if state == "partial":
        answer += (" Those records show what I practiced; they do not establish "
                   "lasting improvement or how I felt.")
    return answer
