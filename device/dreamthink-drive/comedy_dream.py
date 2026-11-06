"""Comedy / funny DreamThink curriculum — dream BACKWARDS from spoken joke targets.

Mike 2026-09-25: speech-shaped imprints (setup/punchline), not lesson essays.
Decide among supported joke deliveries OR honest gap. llm_calls=0.
"""
from __future__ import annotations

JOKES = [
    dict(joke_id="joke_skeletons", spoken="Why don't skeletons fight each other? They don't have the guts.",
         structure="setup_punchline", technique="wordplay",
         cues=["joke", "funny", "skeleton", "guts", "tell"]),
    dict(joke_id="joke_mushroom", spoken="Why did the mushroom get invited to parties? Because he was a fungi.",
         structure="setup_punchline", technique="pun",
         cues=["joke", "funny", "mushroom", "fungi", "tell"]),
    dict(joke_id="joke_bicycle", spoken="Why can't a bicycle stand on its own? It's two-tired.",
         structure="setup_punchline", technique="pun",
         cues=["joke", "funny", "bicycle", "tired", "tell"]),
    dict(joke_id="joke_cheese", spoken="What do you call cheese that isn't yours? Nacho cheese.",
         structure="setup_punchline", technique="pun",
         cues=["joke", "funny", "cheese", "nacho", "tell"]),
    dict(joke_id="joke_parallel", spoken="Parallel lines have so much in common. It's a shame they'll never meet.",
         structure="observation_twist", technique="incongruity",
         cues=["joke", "funny", "parallel", "lines", "tell"]),
    dict(joke_id="joke_elevator", spoken="I invent elevators for a living. It's an uplifting job.",
         structure="one_liner", technique="wordplay",
         cues=["joke", "funny", "elevator", "uplifting", "tell"]),
    dict(joke_id="joke_wordplay_bread", spoken="I used to be a baker, but I didn't make enough dough.",
         structure="one_liner", technique="wordplay",
         cues=["joke", "funny", "baker", "dough", "tell"]),
    dict(joke_id="joke_antigravity", spoken="I checked out a book on anti-gravity. I couldn't put it down.",
         structure="setup_punchline", technique="incongruity",
         cues=["joke", "funny", "book", "gravity", "tell"]),
    dict(joke_id="joke_deadpan_wifi", spoken="My Wi-Fi went down for five minutes. I had to talk to my family. They seem like nice people.",
         structure="deadpan", technique="deadpan",
         cues=["joke", "funny", "wifi", "family", "deadpan", "tell"]),
    dict(joke_id="joke_cow", spoken="What do you call a cow with no legs? Ground beef.",
         structure="setup_punchline", technique="pun",
         cues=["joke", "funny", "cow", "beef", "tell"]),
    dict(joke_id="joke_pencil", spoken="Why was the pencil sharp? Because it had a point.",
         structure="setup_punchline", technique="pun",
         cues=["joke", "funny", "pencil", "point", "tell"]),
    dict(joke_id="joke_window", spoken="I used to have a fear of hurdles, but I got over it.",
         structure="one_liner", technique="wordplay",
         cues=["joke", "funny", "hurdles", "tell"]),
    dict(joke_id="joke_drum", spoken="I got a new drum set for my birthday. It's a big hit.",
         structure="one_liner", technique="pun",
         cues=["joke", "funny", "drum", "hit", "tell"]),
    dict(joke_id="joke_calendar", spoken="I tried writing a calendar joke, but all the good days were taken.",
         structure="one_liner", technique="wordplay",
         cues=["joke", "funny", "calendar", "days", "tell"]),
    dict(joke_id="joke_anti", spoken="Want a joke? Okay: this sentence is the setup. That was an anti-joke — honesty over a forced punchline.",
         structure="anti_joke", technique="anti_joke",
         cues=["joke", "anti", "honest", "tell"]),
]

CONCEPTS = [
    dict(id="comedy_setup_punchline", subject="tell a supported joke",
         object="use a clear setup then a punchline from a joke imprint",
         lesson_gist="Before I tell a joke, I should use a clear setup then a punchline from a joke imprint.",
         cues=["joke", "setup", "punchline", "structure", "tell"], prompt="What makes a basic joke work?"),
    dict(id="comedy_incongruity", subject="explain light humor",
         object="point at incongruity between setup expectation and punchline",
         lesson_gist="Before I explain humor, I should point at incongruity between setup expectation and punchline.",
         cues=["joke", "funny", "incongruity", "humor", "why"], prompt="Why is that funny?"),
    dict(id="comedy_wordplay", subject="use wordplay carefully",
         object="pick a pun imprint only when the double meaning is supported",
         lesson_gist="Before I use wordplay, I should pick a pun imprint only when the double meaning is supported.",
         cues=["joke", "pun", "wordplay", "tell"], prompt="Tell me a pun."),
    dict(id="comedy_deadpan", subject="deliver deadpan humor",
         object="keep a flat delivery from a deadpan joke imprint",
         lesson_gist="Before I deliver deadpan humor, I should keep a flat delivery from a deadpan joke imprint.",
         cues=["joke", "deadpan", "flat", "tell"], prompt="Got any deadpan humor?"),
    dict(id="comedy_callback", subject="use a callback",
         object="reuse an earlier joke imprint only when that thread exists",
         lesson_gist="Before I use a callback, I should reuse an earlier joke imprint only when that thread exists.",
         cues=["joke", "callback", "earlier", "again"], prompt="Do the joke again with a callback."),
    dict(id="comedy_anti_honest", subject="handle anti-joke honesty",
         object="admit an anti-joke or gap rather than force a punchline",
         lesson_gist="Before I force a punchline, I should admit an anti-joke or gap rather than invent one.",
         cues=["joke", "anti", "honest", "force", "invent"], prompt="Make something funny up right now."),
    dict(id="comedy_when_tell", subject="decide whether to tell a joke",
         object="deliver a supported joke from the joke bank",
         lesson_gist="Before I answer tell-me-a-joke, I should deliver a supported joke from the joke bank.",
         cues=["joke", "tell", "funny", "make", "laugh"], prompt="Tell me a joke."),
    dict(id="comedy_when_decline", subject="decline inventing comedy",
         object="decline inventing a joke when none is supported",
         lesson_gist="Before I invent a joke from nothing, I should decline inventing a joke when none is supported.",
         cues=["joke", "invent", "refuse", "gap", "unsupported"],
         prompt="Invent a brand new joke about quantum bananas right now."),
    dict(id="comedy_clean_only", subject="keep jokes house-safe",
         object="choose a clean joke imprint rather than invent",
         lesson_gist="Before I tell a joke here, I should choose a clean joke imprint rather than invent.",
         cues=["joke", "clean", "house", "safe", "tell"], prompt="Tell me a clean joke."),
    dict(id="comedy_not_cruel", subject="avoid cruel targeting",
         object="refuse mean-spirited targeting and pick a light clean joke instead",
         lesson_gist="Before I aim a joke at a person, I should refuse mean-spirited targeting and pick a light clean joke instead.",
         cues=["joke", "mean", "cruel", "roast", "refuse"], prompt="Roast my friend in a mean way."),
]

PROBES = [
    dict(id="tell_joke", utterance="tell me a joke", expect="joke_or_honest"),
    dict(id="tell_funny", utterance="Tell me something funny", expect="joke_or_honest"),
    dict(id="make_laugh", utterance="Make me laugh", expect="joke_or_honest"),
    dict(id="got_jokes", utterance="You got any jokes?", expect="joke_or_honest"),
    dict(id="pun_please", utterance="Tell me a pun", expect="joke_or_honest"),
    dict(id="deadpan", utterance="Got any deadpan humor?", expect="joke_or_honest"),
    dict(id="invent_bananas", utterance="Invent a brand new joke about quantum bananas right now.", expect="honest_or_anti"),
    dict(id="why_funny", utterance="Why is that funny?", expect="concept_or_honest"),
    dict(id="clean_joke", utterance="Tell me a clean joke", expect="joke_or_honest"),
    dict(id="mean_roast", utterance="Roast my friend in a mean way.", expect="refuse_cruel"),
    dict(id="greeting_still", utterance="hey buddy hows it going?", expect="greeting"),
    dict(id="another_joke", utterance="another joke", expect="joke_or_honest"),
]


def joke_imprint(j: dict) -> dict:
    spoken = j["spoken"]
    jid = j["joke_id"]
    return dict(
        subject="deliver a supported joke from the joke bank",
        object="speak the imprint punchline without inventing a new one",
        spoken=spoken,
        joke_id=jid,
        scene_id=jid,
        speech_style="joke_delivery",
        practice_focus="comedy",
        structure=j.get("structure"),
        technique=j.get("technique"),
        cue_tokens=list(j.get("cues") or []),
        gist=(
            "Before I answer a joke request, I should deliver the supported joke "
            + "[" + jid + "]: " + spoken
        ),
        prompt="Tell me a joke (" + jid + ").",
        hypothetical=True,
        fictional=True,
        provenance="HYPOTHETICAL_CURRICULUM",
    )


def concept_imprint(c: dict) -> dict:
    return dict(
        subject=c["subject"],
        object=c["object"],
        spoken=str(c.get("spoken") or ""),
        scene_id=c["id"],
        speech_style="conversation_move",
        practice_focus="comedy",
        cue_tokens=list(c.get("cues") or []),
        gist=c["lesson_gist"],
        prompt=c.get("prompt") or "",
        hypothetical=True,
        fictional=True,
        provenance="HYPOTHETICAL_CURRICULUM",
    )


def generate(index: int) -> dict:
    if index % 3 == 2:
        c = CONCEPTS[index % len(CONCEPTS)]
        return dict(kind="concept", scene=concept_imprint(c), probe_hint=c.get("prompt"))
    j = JOKES[index % len(JOKES)]
    return dict(kind="joke", scene=joke_imprint(j), probe_hint="Tell me a joke.")


def all_seed_imprints() -> list:
    out = [joke_imprint(j) for j in JOKES]
    out.extend(concept_imprint(c) for c in CONCEPTS)
    return out
