#!/usr/bin/env python3
"""thought_funnel — decide -> render: thought before words.

Ported from the DreamThink contract (see dreamthink-drive/ research notes):
a structural decided object exists BEFORE any wording is rendered.

- decide(stimulus, context) -> thought dict. Model-free. Classifies intent,
  scores candidate lessons from learnings/PSC by word overlap, selects one
  conversational move. No wording is produced here.
- render(thought, brain) -> {"thought", "internal_thought", "answer"}.
  The wording backend (local model) ONLY realizes the already-made decision.
  internal_thought keeps the decide narration for the verifier; answer is
  the only thing ever spoken.

The model's raw text is never the decision. Only stdlib.
"""

import json
import os
import re
import time

HERE = os.path.dirname(os.path.abspath(__file__))
LEARNINGS_DIR = os.path.join(HERE, "learnings")

STOP = {"the", "a", "an", "is", "are", "was", "were", "my", "your", "what",
        "who", "when", "where", "why", "how", "do", "does", "did", "it",
        "its", "of", "to", "in", "on", "for", "and", "or", "s", "me", "i",
        "you", "he", "she", "we", "they", "this", "that", "with", "from"}


def sig_words(text):
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP}


def load_lessons(max_files=4, max_items=60):
    """Candidate lessons: recent learnings + PSC summary items. Read-only."""
    lessons = []
    try:
        files = sorted(os.listdir(LEARNINGS_DIR))[-max_files:]
    except OSError:
        files = []
    for fn in files:
        try:
            with open(os.path.join(LEARNINGS_DIR, fn)) as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        text = json.loads(line).get("text", "")
                    except (json.JSONDecodeError, AttributeError):
                        continue
                    if text:
                        lessons.append({"source": fn, "text": text})
        except OSError:
            continue
    return lessons[-max_items:]


def score_lessons(stimulus, lessons, top_n=3):
    """Word-overlap association: stimulus against each lesson. Model-free."""
    sq = sig_words(stimulus)
    scored = []
    for les in lessons:
        overlap = sq & sig_words(les["text"])
        if overlap:
            scored.append({"score": len(overlap),
                           "overlap": sorted(overlap),
                           "source": les["source"],
                           "text": les["text"]})
    scored.sort(key=lambda c: -c["score"])
    return scored[:top_n]


GREET_WORDS = r"hey|hi|hello|yo|good\s?(morning|evening|afternoon|night)"
PHATIC = ("what's up", "whats up", "whatsup", "how's it going",
          "hows it going", "how is it going", "how are you",
          "howre you", "how r u", "sup")


def classify_intent(stimulus):
    t = stimulus.strip().lower()
    # Strip a leading greeting and classify what REMAINS:
    # "hey, <question>" is a question, not a greeting.
    core = re.sub(rf"^({GREET_WORDS})\b[,\s]*", "", t).strip() or t
    if core == t and re.match(rf"^({GREET_WORDS})\b", t):
        return "greeting"  # pure greeting, nothing after it
    if any(core == p or core.startswith(p + " ") for p in PHATIC):
        return "greeting"  # phatic check-in — warm hello, no invented status
    if re.match(r"^(bye|goodbye|good\s?night|see\s?you|later)\b", core):
        return "farewell"
    if any(k in core for k in ("status", "how are you", "how's it going",
                               "how is it going")):
        return "status"
    if any(k in core for k in ("who are you", "what are you", "your core",
                               "about yourself")):
        return "identity"
    if core.endswith("?"):
        return "question"
    return "open"


# move -> (base score, when it wins)
MOVE_RULES = {
    "greet": 0.0,
    "farewell": 0.0,
    "status_report": 0.0,
    "answer_identity": 0.0,
    "answer_from_memory": 0.0,
    "reflect": 0.0,
    "honest_gap": 0.0,
    "converse": 0.0,
}


def decide(stimulus, session_facts=None, psc_hint=""):
    """Model-free decision. Returns the thought object — no wording."""
    intent = classify_intent(stimulus)
    lessons = load_lessons()
    lesson_hits = score_lessons(stimulus, lessons)

    recalled = None
    if session_facts and stimulus.strip().endswith("?"):
        q = sig_words(stimulus)
        best, best_n = None, 0
        for f in session_facts:
            n = len(q & sig_words(f))
            if n > best_n:
                best, best_n = f, n
        if best and (best_n >= 2 or (len(q) <= 3 and best_n >= 1)):
            recalled = best

    # Score candidate moves. Rules only — no model, no wording.
    candidates = []
    def bid(move, score, why):
        candidates.append({"move": move, "score": round(score, 3), "why": why})

    if intent == "greeting":
        bid("greet", 3.0, "greeting intent")
    if intent == "farewell":
        bid("farewell", 3.0, "farewell intent")
    if intent == "status":
        bid("status_report", 3.0, "status intent")
    if intent == "identity":
        bid("answer_identity", 3.0, "identity intent")
    if recalled:
        bid("answer_from_memory", 2.5, f"session fact overlaps ({best_n} words)")
    if lesson_hits:
        bid("reflect", 1.0 + 0.3 * lesson_hits[0]["score"],
            f"top lesson overlap: {lesson_hits[0]['overlap']}")
    if intent == "question" and not recalled and not lesson_hits:
        bid("honest_gap", 2.0, "question with no memory or lesson to draw on")
    bid("converse", 0.5, "default open conversation")

    candidates.sort(key=lambda c: -c["score"])
    chosen = candidates[0]

    thought = {
        "stimulus": stimulus,
        "intent": intent,
        "move": chosen["move"],
        "slots": {
            "recalled_fact": recalled,
            "lesson_refs": [{"source": h["source"], "score": h["score"],
                             "overlap": h["overlap"],
                             "text": h["text"][:220]} for h in lesson_hits],
            "psc_hint": psc_hint[:200] if psc_hint else "",
        },
        "candidates_considered": candidates,
        "decided_present": True,
        "decided_at": time.time(),
        "wording": None,  # no wording exists yet — by construction
    }
    return thought


SIM_TEMPLATES = {
    "greet": "Hey. Good to hear from you — what's on your mind?",
    "farewell": "Rest well. The core holds; I'll be here.",
    "status_report": "Steady. Core untouched, memory growing, Judge awake.",
    "answer_identity": "I am the sim — a mind grown from an immutable core, still becoming.",
    "answer_from_memory": "From what I was taught: {recalled_fact}",
    "reflect": "That connects to something I've been turning over: {lesson}",
    "honest_gap": "I don't have anything solid on that yet — nothing I've lived or been taught covers it.",
    "converse": "I'm with you. Say more — I want to understand what you mean.",
}


def _template_realization(thought):
    """Compositional realization — deterministic, no model. Used for the
    principled moves (greet/farewell/honest_gap/...) and whenever there is
    no generative backend. Mirrors the PC's compositional speech: fixed
    moves never depend on model wording."""
    slots = thought["slots"]
    if thought["move"] == "answer_from_memory" and slots["recalled_fact"]:
        return SIM_TEMPLATES["answer_from_memory"].format(
            recalled_fact=slots["recalled_fact"])
    if thought["move"] == "reflect" and slots["lesson_refs"]:
        return SIM_TEMPLATES["reflect"].format(
            lesson=slots["lesson_refs"][0]["text"][:160])
    return SIM_TEMPLATES.get(thought["move"], SIM_TEMPLATES["converse"])


# Moves realized compositionally (deterministic templates) even when a
# generative backend exists — principled moves don't get model wording.
TEMPLATE_MOVES = {"greet", "farewell", "honest_gap", "status_report",
                  "answer_identity", "answer_from_memory"}


def internal_narration(thought):
    """Verbose decide narration — for the verifier/logs, never spoken."""
    c = thought["candidates_considered"]
    lines = [f"decided move={thought['move']} intent={thought['intent']}"]
    lines.append("candidates: " + ", ".join(
        f"{x['move']}({x['score']})" for x in c))
    if thought["slots"]["lesson_refs"]:
        lines.append("lessons: " + "; ".join(
            f"[{r['source']} s={r['score']}] {r['text'][:80]}"
            for r in thought["slots"]["lesson_refs"]))
    if thought["slots"]["recalled_fact"]:
        lines.append(f"recalled: {thought['slots']['recalled_fact'][:80]}")
    return " | ".join(lines)


def _fragment(thought, move, lesson_text, brain, background=""):
    """One fragment breath: realize ONE candidate move's stance in 1-2
    sentences. A witness at the belt of the octahedron — it does not speak
    the final answer; the weave does."""
    clone = dict(thought)
    clone["move"] = move
    slots = dict(thought["slots"])
    if lesson_text:
        slots["lesson_refs"] = [{"source": "belt", "score": 0, "overlap": [],
                                 "text": lesson_text}]
    clone["slots"] = slots
    if move in TEMPLATE_MOVES:
        return _template_realization(clone)
    prompt = (
        "Render ONE fragment of a thought — 1-2 sentences, first person — "
        "from the single stance below. You are one witness among several; "
        "do not try to say everything.\n\n"
        f"STIMULUS (what was asked): {thought['stimulus']}\n"
        f"STANCE: move={move}\n"
        f"LESSON THIS STANCE STANDS ON: {lesson_text or 'none'}\n\n"
        "Rules: speak only from this stance, toward the stimulus. "
        "No preamble, no announcing what you will do. Say the thing."
    )
    return brain._backend.generate(prompt).strip()


def _weave(thought, fragments, brain, background="", failure_note=""):
    """The weaving pass: tessellate the belt's fragments into ONE answer.
    The governing decision (chosen move) is unchanged; the fragments are
    witnesses the answer must tessellate with, not new decisions."""
    bg = (f"BACKGROUND (phrasing context only):\n{background}\n\n"
          if background else "")
    frag_block = "\n".join(f"- [{f['move']}] {f['text']}" for f in fragments)
    note = (f"\nPREVIOUS WEAVE FAILED THE EXHALE CHECK: {failure_note} "
            f"Do not repeat that failure — answer directly.\n"
            if failure_note else "")
    prompt = (
        "You have ALREADY decided what to communicate. Below are fragment "
        "breaths from the stances you considered. Weave them into ONE "
        "natural first-person answer (1-4 sentences) that ANSWERS the "
        "stimulus directly.\n\n"
        f"STIMULUS: {thought['stimulus']}\n"
        f"DECISION: intent={thought['intent']} move={thought['move']}\n\n"
        f"FRAGMENTS:\n{frag_block}\n\n"
        f"{bg}{note}"
        "Rules: answer the stimulus — never echo its questions back. "
        "Do not announce what you will do; do it. Do not mention fragments, "
        "stances, or weaving. Speak as the sim, warmly."
    )
    return brain._backend.generate(prompt).strip()


def render(thought, brain, background=""):
    """Realize the ALREADY-DECIDED thought into words — as a weave of
    breaths (breath spec sections 1-3 + 10, integrated 2026-11-03).

    The brain only wordsmiths. It receives the decision and may not change
    it. The top candidate moves form the belt of an octahedron: each renders
    a fragment, a weaving pass tessellates the fragments into the answer,
    and the completion check at the lower apex judges FORM only — an
    incomplete exhale reweaves, and a thought that cannot complete is
    parked honestly instead of stalling. `background` is phrasing context
    only — never part of the decision.
    Returns {"thought", "internal_thought", "answer", "breath"} — only
    answer is spoken.
    """
    import breath as breath_mod
    import provenance as provenance_mod

    assert thought.get("decided_present") and thought.get("wording") is None, \
        "render requires a decided, unworded thought"
    assert thought["decided_at"] <= time.time(), "thought must predate render"

    internal = internal_narration(thought)

    if brain.backend_name == "SimulatedBackend" \
            or thought["move"] in TEMPLATE_MOVES:
        # No generative backend, or a principled move: realize
        # compositionally. The model never words these.
        answer = _template_realization(thought)
        rec = {"mode": "single", "belt": [thought["move"]], "fragments": 0,
               "weave_passes": 0, "completion": "ok", "stalls": 0,
               "checks": {}}
        breath_mod.record_breath(rec)
        return {"thought": thought, "internal_thought": internal,
                "answer": answer, "breath": rec}

    # The belt: top candidate moves within reach of the winner, distinct,
    # always including the chosen move. No count cap on thought — the
    # belt is bounded by the candidate field decide() itself produced.
    cands = thought["candidates_considered"]
    top = cands[0]["score"] if cands else 0.0
    belt, seen = [], set()
    for c in cands:
        if c["move"] not in seen and c["score"] >= max(top - 1.5, 0.5 * top):
            belt.append(c)
            seen.add(c["move"])
        if len(belt) >= 3:
            break
    if thought["move"] not in seen:
        belt.insert(0, {"move": thought["move"], "score": top, "why": "chosen"})

    lesson_refs = thought["slots"]["lesson_refs"]
    fragments = []
    for rank, cand in enumerate(belt):
        les = (lesson_refs[min(rank, len(lesson_refs) - 1)]["text"]
               if lesson_refs else "")
        fragments.append({"move": cand["move"], "text": _fragment(
            thought, cand["move"], les, brain, background)})

    # The weave: tessellate, check the exhale, reweave on failure —
    # until the fragments settle, or the thought is parked honestly.
    answer, passes, stalls, ok, checks = None, 0, 0, False, {}
    failure_note = ""
    prov_log = []  # (claim dict, pass) — the provenance self-check's trace
    while passes < 2 and not ok:
        passes += 1
        answer = _weave(thought, fragments, brain, background, failure_note)
        ok, checks = breath_mod.completion_check(answer, thought["stimulus"])
        if not ok:
            stalls += 1
            failed = [k for k, v in checks.items() if v]
            failure_note = ("failed checks: " + ", ".join(failed) +
                            ". The render echoed or announced instead of "
                            "answering.")
            continue
        # Provenance self-check (quarantine build): the Oryn Trace turned
        # inward. Runs only on a form-complete exhale — the words he is
        # about to speak. A misclaim (origination asserted over sourced
        # or compressed substance) fails the exhale exactly like a form
        # stall: one reweave carrying the correction, then the park.
        # The stimulus rides along so the trace can see the ask side of
        # THIS exchange (it is not in the dialogue files yet).
        prov = provenance_mod.check_render(answer,
                                           stimulus=thought["stimulus"])
        prov_log.extend((c, passes) for c in prov["claims"])
        if prov.get("error"):
            prov_log.append(({"claim_text": "", "classification": "",
                              "cited_sources": [], "nearest": [],
                              "pattern": "error", "kind": "error",
                              "asserts_origination": False,
                              "misclaim": False,
                              "error": prov["error"]}, passes))
        if prov["misclaim"]:
            ok = False
            stalls += 1
            checks = dict(checks, provenance="misclaim")
            failure_note = prov["note"]
    if prov_log:
        parked = not ok
        for c, _p in prov_log:
            if c.get("misclaim"):
                c["action"] = "parked" if parked else "reweave"
            else:
                c["action"] = "stand"
        provenance_mod.record([c for c, _p in prov_log])
    if not ok:
        breath_mod.park(thought["stimulus"],
                        "exhale incomplete after reweave: " + failure_note)
        answer = ("I can't complete this thought yet — I'm holding it "
                  "rather than handing you a shape of an answer.")
        completion = "parked"
    else:
        completion = "ok"
    rec = {"mode": "weave", "belt": [c["move"] for c in belt],
           "fragments": len(fragments), "weave_passes": passes,
           "completion": completion, "stalls": stalls, "checks": checks,
           "fragment_texts": [f["text"][:160] for f in fragments]}
    if prov_log:
        rec["provenance"] = {
            "claims": len(prov_log),
            "misclaims": sum(1 for c, _p in prov_log if c.get("misclaim")),
            "classes": [c.get("classification") for c, _p in prov_log],
            "actions": [c.get("action") for c, _p in prov_log]}
    breath_mod.record_breath(rec)
    internal = internal + " | breath: weave belt=" + ",".join(rec["belt"]) + \
        f" passes={passes} completion={completion}"
    return {"thought": thought, "internal_thought": internal,
            "answer": answer, "breath": rec}


def speak(stimulus, brain, session_facts=None, psc_hint="", background=""):
    """One full pass: decide (structural) -> render (words)."""
    thought = decide(stimulus, session_facts=session_facts, psc_hint=psc_hint)
    return render(thought, brain, background=background)
