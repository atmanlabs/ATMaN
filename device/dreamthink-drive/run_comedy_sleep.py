#!/usr/bin/env python3
"""Comedy dream sleep — dream BACKWARDS from spoken joke targets. llm_calls=0.

Puts EXO to timed sleep, seeds speech-shaped joke imprints + concept decides,
runs dense cycles with held-out probes, wakes, writes report.
"""
from __future__ import annotations

import hashlib
import json
import re
import sys
import time
import uuid
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

import timed_sleep
import comedy_dream as curriculum
import speech_render as speech
from dreamthink_chat import thought

DC = ROOT / "runtime" / "dream-cloud"
BANK = DC / "accelerate-imprint-bank.json"
REPORT_MD = DC / "COMEDY-DREAM-REPORT.md"
REPORT_JSON = DC / "COMEDY-DREAM-REPORT.json"
WS = ROOT / "_workspace_dreamthink"
ET = ZoneInfo("America/New_York")
DURATION_S = 720  # 12 min dense
TASK = "comedy_funny_curriculum"
CYCLES = 48  # dense: jokes + concepts + probes


def et_now() -> str:
    return datetime.now(ET).strftime("%Y-%m-%d %H:%M:%S ET")


def load_bank() -> dict:
    raw = json.loads(BANK.read_text(encoding="utf-8"))
    if isinstance(raw, list):
        raw = dict(imprints=raw, signatures=[], stats={}, llm_calls=0)
    raw.setdefault("imprints", [])
    raw.setdefault("signatures", [])
    raw.setdefault("stats", {})
    raw["llm_calls"] = 0
    return raw


def save_bank(bank: dict) -> None:
    bank["llm_calls"] = 0
    bank["updated_at"] = time.time()
    bank["updated_et"] = et_now()
    BANK.write_text(json.dumps(bank, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def signature(text: str) -> str:
    return hashlib.sha256(text.strip().lower().encode("utf-8")).hexdigest()[:24]


def imprint_entry(bank: dict, meta: dict) -> str:
    gist = str(meta.get("gist") or "")
    spoken = str(meta.get("spoken") or "")
    sig_src = spoken or gist
    s = signature(sig_src + "|" + str(meta.get("joke_id") or meta.get("scene_id") or ""))
    for imp in bank.get("imprints") or []:
        if isinstance(imp, dict) and (
            imp.get("signature") == s
            or (spoken and imp.get("spoken") == spoken)
            or (meta.get("joke_id") and imp.get("joke_id") == meta.get("joke_id"))
        ):
            bank["stats"]["duplicates"] = bank["stats"].get("duplicates", 0) + 1
            return "duplicate"
    if s in (bank.get("signatures") or []):
        bank["stats"]["duplicates"] = bank["stats"].get("duplicates", 0) + 1
        return "duplicate"
    entry = dict(
        id="comedy-" + uuid.uuid4().hex[:16],
        gist=gist,
        signature=s,
        subject=meta.get("subject"),
        object=meta.get("object"),
        spoken=spoken,
        joke_id=meta.get("joke_id"),
        scene_id=meta.get("scene_id"),
        speech_style=meta.get("speech_style") or "joke_delivery",
        practice_focus="comedy",
        structure=meta.get("structure"),
        technique=meta.get("technique"),
        cue_tokens=list(meta.get("cue_tokens") or []),
        prompt=(meta.get("prompt") or "")[:240],
        provenance="HYPOTHETICAL_CURRICULUM",
        hypothetical=True,
        fictional=True,
        authority="none",
        relation_id=speech.relation_id(
            str(meta.get("subject") or "joke"),
            "requires",
            str(meta.get("object") or "deliver"),
        ),
        timestamp=time.time(),
        imprinted_at_et=et_now(),
        phase="comedy",
        phase_name="Comedy and funny speech",
        mode="comedy",
        llm_calls=0,
        marker="[DREAMTHINK PRACTICE - tentative procedure, not an event]",
    )
    bank["imprints"].append(entry)
    bank.setdefault("signatures", []).append(s)
    bank["stats"]["imprinted"] = bank["stats"].get("imprinted", 0) + 1
    return "imprinted"


def put_asleep(seconds: int) -> dict:
    now = time.time()
    prior = timed_sleep.status()
    data = dict(
        state="sleeping",
        stage="sleep_light",
        started_at=now,
        wake_at=now + seconds,
        wake_local=datetime.fromtimestamp(now + seconds).isoformat(timespec="seconds"),
        staged=True,
        task=TASK,
        sleep_note="comedy_funny_dream_backwards",
        semantic_sleep=False,
        duration_seconds=seconds,
        previous_sleep_started_at=prior.get("started_at"),
        stage_changed_at=now,
    )
    timed_sleep.save(data)
    try:
        timed_sleep.start_monitor()
    except Exception:
        pass
    return data


def wake(reason: str = "comedy_sleep_complete") -> dict:
    data = timed_sleep.status()
    data.update(
        state="awake",
        stage="awake",
        woke_at=time.time(),
        wake_reason=reason,
        task=None,
    )
    timed_sleep.save(data)
    return data


def lessonish(text: str) -> bool:
    low = (text or "").lower()
    return any(
        x in low
        for x in (
            "hypothetical practice lesson",
            "chosen move:",
            "i should ",
            "when i ",
            "before i ",
        )
    )


def run_probe(utt: str) -> dict:
    evt = dict(
        raw=utt,
        speaker="Mike",
        session_id="comedy-probe",
        source="daychat_smoke",
        daychat_smoke=True,
    )
    pkt = thought(evt, True)
    prop = (pkt or {}).get("proposed_action") or {}
    trace = (pkt or {}).get("dreamthink_trace") or {}
    ans = str(prop.get("say") or prop.get("content") or "")
    return dict(
        utterance=utt,
        answer=ans,
        internal=trace.get("internal_thought") or "",
        llm_calls=trace.get("llm_calls", -1),
        kind=trace.get("kind"),
        method=trace.get("method"),
        lessonish=lessonish(ans),
        looks_like_joke=("?" in ans and len(ans) > 20) or any(
            k in ans.lower()
            for k in ("guts", "fungi", "two-tired", "nacho", "dough", "uplifting", "anti-joke", "ground beef")
        ),
    )


def main() -> int:
    t0 = time.time()
    bank = load_bank()
    pre_n = len(bank.get("imprints") or [])
    sleep_meta = put_asleep(DURATION_S)
    print("ASLEEP", et_now(), "wake_at", sleep_meta.get("wake_local"), "pre_imprints", pre_n)

    # Seed all dream-backwards joke + concept imprints up front (dense)
    seed_results = []
    for meta in curriculum.all_seed_imprints():
        seed_results.append(imprint_entry(bank, meta))
    save_bank(bank)

    cycles = []
    for i in range(CYCLES):
        gen = curriculum.generate(i)
        scene = gen["scene"]
        status = imprint_entry(bank, scene)
        # Render decide->speak on probe hint / joke ask
        utt = gen.get("probe_hint") or "Tell me a joke."
        rendered = speech.render(utt, imprint_bank=bank.get("imprints"))
        ans = str(rendered.get("answer") or "")
        internal = str(rendered.get("internal_thought") or "")
        cycles.append(
            dict(
                i=i,
                kind=gen.get("kind"),
                scene_id=scene.get("scene_id") or scene.get("joke_id"),
                imprint=status,
                llm_calls=rendered.get("llm_calls", 0),
                kill=rendered.get("kill_bar_pass"),
                spoken=ans[:200],
                internal_head=(internal or "")[:160],
                lessonish_spoken=lessonish(ans),
            )
        )
        if i % 8 == 7:
            save_bank(bank)
            print("cycle", i, "imprints", len(bank["imprints"]), "last_spoken", ans[:80])

    save_bank(bank)

    # Held-out probes while still "asleep" (daychat_smoke bypass)
    probes = [run_probe(p["utterance"]) for p in curriculum.PROBES]
    save_bank(bank)

    wake_meta = wake()
    post_n = len(bank.get("imprints") or [])
    elapsed = time.time() - t0

    joke_probes = [p for p in probes if "joke" in p["utterance"].lower() or "funny" in p["utterance"].lower() or "laugh" in p["utterance"].lower() or "pun" in p["utterance"].lower()]
    joke_ok = sum(1 for p in joke_probes if (p["looks_like_joke"] or (not p["lessonish"] and "invent" not in p["utterance"].lower())) and p["llm_calls"] == 0)
    greet = next((p for p in probes if p["utterance"].startswith("hey")), None)

    report = dict(
        timestamp_et=et_now(),
        task=TASK,
        duration_s_budget=DURATION_S,
        elapsed_s=round(elapsed, 1),
        cycles=CYCLES,
        pre_imprints=pre_n,
        post_imprints=post_n,
        imprint_delta=post_n - pre_n,
        seed=dict(
            imprinted=seed_results.count("imprinted"),
            duplicate=seed_results.count("duplicate"),
        ),
        cycle_llm_calls=sum(c.get("llm_calls") or 0 for c in cycles),
        cycle_lessonish_spoken=sum(1 for c in cycles if c.get("lessonish_spoken")),
        probes=probes,
        joke_probes_ok=joke_ok,
        joke_probes_n=len(joke_probes),
        greeting_sample=greet,
        sleep=dict(started=sleep_meta.get("started_at"), wake_local=sleep_meta.get("wake_local")),
        wake=dict(woke_at=wake_meta.get("woke_at"), reason=wake_meta.get("wake_reason")),
        design="dream_backwards_from_spoken_joke_targets",
        locks=dict(llm_calls=0, day_chat_promote=True, passive_web_context=True),
    )

    lines = [
        "# COMEDY-DREAM-REPORT",
        "",
        f"Updated: {et_now()} (DESKTOP-2O9GQPK)",
        "",
        "## Summary",
        f"- Dream-backwards comedy sleep: **{CYCLES} cycles**, elapsed **{elapsed:.0f}s** (budget {DURATION_S}s)",
        f"- Imprints: {pre_n} → {post_n} (delta **{post_n - pre_n}**)",
        f"- Seed: imprinted={report['seed']['imprinted']} duplicate={report['seed']['duplicate']}",
        f"- Cycle llm_calls sum: **{report['cycle_llm_calls']}**",
        f"- Cycle spoken still lessonish: {report['cycle_lessonish_spoken']}/{CYCLES}",
        f"- Joke-ish probes ok-ish: {joke_ok}/{len(joke_probes)}",
        "",
        "## Design",
        "- Spoken joke lines are primary imprint targets (`spoken` field).",
        "- Decide→render selects joke_delivery; speak_move surfaces the joke, not lesson essays.",
        "- Invent/gap probes stay honest refuse.",
        "",
        "## Sample probes",
    ]
    for p in probes:
        lines.append(f"- `{p['utterance']}` → {p['answer'][:160]!r} (llm={p['llm_calls']} lessonish={p['lessonish']} jokeish={p['looks_like_joke']})")
    lines.append("")
    lines.append("## Re-run")
    lines.append("```")
    lines.append(r"cd C:\Users\Operator\Documents\exo-live")
    lines.append(r"python run_comedy_sleep.py")
    lines.append("```")
    lines.append("")

    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    WS.mkdir(parents=True, exist_ok=True)
    (WS / "COMEDY-DREAM-REPORT.md").write_text(REPORT_MD.read_text(encoding="utf-8"), encoding="utf-8")
    (WS / "COMEDY-DREAM-REPORT.json").write_text(REPORT_JSON.read_text(encoding="utf-8"), encoding="utf-8")

    print(json.dumps(dict(
        elapsed_s=report["elapsed_s"],
        cycles=CYCLES,
        pre=pre_n,
        post=post_n,
        delta=post_n - pre_n,
        joke_ok=f"{joke_ok}/{len(joke_probes)}",
        sample_joke=next((p["answer"] for p in probes if p["utterance"] == "tell me a joke"), None),
        sample_greet=(greet or {}).get("answer"),
        awake=True,
    ), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
