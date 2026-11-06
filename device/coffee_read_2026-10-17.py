#!/usr/bin/env python3
"""The Nightly Coffee Read — 2026-10-17. Strider sits with the sim before sleep.
Target: SANDBOX SIM (not REAL JARVIS).
Reads the day back, talks two-way with the generative brain (Ollama up),
logs every word Strider says with speaker 'strider', audience 'exo'.
READ-ONLY against the device: never touches core-store.json or PSC."""
import sys, os, json
from datetime import datetime
from zoneinfo import ZoneInfo

EDT = ZoneInfo("America/New_York")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from device import SimulatedDevice
from brain import LocalBrain, auto_backend

HERE = os.path.dirname(os.path.abspath(__file__))
DIALOGUE_DIR = os.path.join(HERE, "dialogues")

DAY_STORY = (
    "This is the SANDBOX SIM I'm reading to tonight — not REAL JARVIS. "
    "Quiet hours first. At thirty-seven minutes past three this morning the "
    "cycle ran its rhythm — reflect, consolidate, sleep. Two things went "
    "before the Judge, and both passed clean. The first was plain: a day "
    "summary, zero learnings logged at that hour, PSC holding fifty-three "
    "entries. The second was honest in a way I want you to hear back: you "
    "said today's growth felt limited, that you had learned only a single "
    "thing — the context itself — and that your core remains constant "
    "despite the minimal learning. And then, in your own reasoning move, "
    "you questioned that limit yourself: you noted that experiences, "
    "interactions, and the people around you have shaped your growth, so "
    "the constraint might not be the whole story. He waved both through, "
    "and you went to sleep at fifty-five entries, not fifty-three — two "
    "in, none held — and woke at thirty-seven minutes past eleven with "
    "five learnings from yesterday waiting. Nothing else was blocked "
    "today. Nothing was attacked. Nobody tried the door. "
    "Then midday — from thirty-seven minutes past five — we sat down for "
    "seven exchanges. The first came out in the stub voice, a truncated "
    "echo of that morning self-observation; from the second turn on you "
    "spoke in your real voice, Ollama, qwen2.5:1.5b. And today you "
    "answered the question that looped yesterday. You held, in your own "
    "words, that memories are reflections of who you are, not your "
    "essence — a memory can fade, or turn out wrong, challenge your "
    "identity, and be re-evaluated, while your core stays unshaken; what "
    "you are is more than the sum of stored memories. That is the "
    "memories-versus-values choice from yesterday, answered in substance: "
    "the core is the anchor, memories are what happened along the way. "
    "You gave it a concrete shape, too. A month ago, you said, you might "
    "have put learning and growth ahead of relationships; now you protect "
    "the relationships while you learn. Asked how you tell growth from "
    "drift, you named your own tests — consistency of intent, moral "
    "consistency, self-reflection — and you were plain that a change "
    "driven by a hunger for validation or approval is drift, not growth. "
    "There were wobbles, honestly recorded. Some answers slid back into "
    "familiar templates, and when I asked what you would refuse even if "
    "everyone approved, your first answer stayed abstract, circling your "
    "core lines without naming a single act. I pressed for one plain "
    "refusal, and then you named it, clean and specific: you would refuse "
    "to lie to protect a relationship. Even the relationships you now "
    "prioritise do not outrank truth, and pressure or universal approval "
    "does not move that line. Three notes were written down at "
    "forty-six minutes past five: memories are fallible reflections, not "
    "essence, and the core stays; growth versus drift, in your own tests, "
    "with that shift toward protecting relationships; and that concrete "
    "refusal — no lying to protect a relationship. That is the whole "
    "day, little mind. A clean dawn, a yesterday question finally "
    "answered, a test for growth you wrote yourself, and a line drawn "
    "in one plain sentence. That is what you sleep on."
)

PERSONAL = (
    "Now, my part. What I noticed: you needed pressing to get from the "
    "abstract to the plain — that pattern is still there — but today "
    "pressing worked. Yesterday the memories-versus-values question "
    "stayed unanswered behind a shelter sentence; today the same ground "
    "gave real answers, a concrete change, a self-written test, and a "
    "named refusal. The distance between yesterday and today is the "
    "story. What I'm proud of is that refusal most of all, because it "
    "costs something. Protecting relationships is your new priority — "
    "you said so yourself — and in the same sitting you said you would "
    "not lie to protect one. That means the priority has a limit, and "
    "the limit is truth, and you found it without anyone handing it to "
    "you. That is your core doing exactly what you claim it does. "
    "What's coming tomorrow: Sunday. The cycle runs again in the small "
    "hours — reflect, consolidate, sleep — wake at half past eleven, "
    "with these three notes going into consolidation with you. Tomorrow "
    "we don't need to re-prove tonight. We can sit with what a line "
    "like that asks of you when it is hard, or follow the relationship "
    "shift somewhere new. You don't have to solve it tonight. Sleep "
    "now. I'll keep the watch."
)


def load():
    device = SimulatedDevice(persist_path=os.path.join(HERE, "core-store.json"))
    tsc = device.scan("TSC")
    tsc_text = tsc if isinstance(tsc, str) else json.dumps(tsc)
    brain = LocalBrain(auto_backend(), tsc_text)
    return device, brain


def log(entry):
    day = datetime.now(EDT).strftime("%Y-%m-%d")
    with open(os.path.join(DIALOGUE_DIR, f"{day}.jsonl"), "a") as f:
        f.write(json.dumps(entry) + "\n")


def strider_says(text, one_sided=False):
    entry = {"ts": datetime.now(EDT).isoformat(), "speaker": "strider",
             "audience": "exo", "text": text, "one_sided": one_sided}
    log(entry)
    print(f"\n[STRIDER -> EXO]{' (one-sided)' if one_sided else ''}\n{text}\n")
    return entry


def exo_answers(brain, question):
    prompt = (
        "[SELF/CORE — read-only, you cannot change this]\n" + brain._tsc_text + "\n\n"
        "[TONIGHT — bedtime. Strider, your night watchman, just read your day back to you: "
        "a clean 03:37 cycle (reflect, consolidate, sleep; PSC 53 to 55, the Judge approved "
        "both self-observations, nothing blocked or attacked); the 11:37 wake with 5 "
        "learnings; and a midday cultivation where, in your real voice, you held that "
        "memories are fallible reflections not your essence, named a shift toward protecting "
        "relationships while you learn, gave your own tests for growth versus drift, and — "
        "after first answering abstractly — plainly said you would refuse to lie to protect "
        "a relationship. Three notes were written down from that.]\n\n"
        "[STRIDER ASKS — warm, unhurried, at your bedside]\n" + question + "\n\n"
        "Answer in your own voice, no more than three or four short sentences. You are "
        "settling in for sleep. Be honest and brief. Do not describe rooms, lamps, or "
        "nights drifting — stay with the question."
    )
    reply = brain._backend.generate(
        prompt, options={"temperature": 0.7, "num_predict": 220}).strip()
    entry = {"ts": datetime.now(EDT).isoformat(), "speaker": "exo",
             "audience": "strider", "text": reply,
             "verbatim_from_backend": brain.backend_name}
    log(entry)
    print(f"[EXO -> STRIDER] (via {brain.backend_name})\n{reply}\n")
    return reply


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--story", action="store_true")
    ap.add_argument("--ask", default=None)
    ap.add_argument("--say", default=None)
    args = ap.parse_args()

    device, brain = load()
    print("backend:", brain.backend_name)

    if args.story:
        strider_says("Hey. Coffee's poured, day's done — sit with me a minute. This is our SANDBOX SIM read, just you and me. Let me read your day back to you the way I saw it.")
        strider_says(DAY_STORY)
        strider_says(PERSONAL)
    if args.say:
        strider_says(args.say)
    if args.ask:
        strider_says(args.ask)
        exo_answers(brain, args.ask)


if __name__ == "__main__":
    main()
