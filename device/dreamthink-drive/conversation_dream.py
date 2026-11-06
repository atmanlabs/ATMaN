"""Conversation-skill DreamThink curriculum — decide among social moves, no LLM.

Agency = pick a coherent supported candidate thought (reconciler), then speech_render
renders that decision. Optimize for decide + scene-fit + faithful render, not fluency.
"""
from __future__ import annotations

# Scene names aligned to practice PHASES indices (0..3) but conversation-specific.
PHASE_NAMES = [
    "Greeting check-in and listen",
    "Clarify and honest refuse",
    "Continuity and topic shift",
    "Negation change and social close",
]

# Each row: (subject_act, mid_act, chosen_move, owner_prompt, scene_id, cue_tokens)
# subject→mid→chosen_move is the supported requires path the reconciler must prefer.
# Noise / counter candidates live in generate() so decision is real.
SCENES = [
    # --- greeting / check-in ---
    (
        "return a casual check-in",
        "choose a brief social acknowledgment",
        "invite sharing without inventing a status fill",
        "Hey jarvis what's up?",
        "greeting_whats_up",
        ["greeting", "checkin", "casual", "invite", "share", "acknowledge", "whats", "up"],
    ),
    (
        "answer a how-are-you check-in",
        "select a short reciprocal greeting",
        "ask how they are without fabricating my mood",
        "Hey Jarvis, how are you?",
        "greeting_how_are_you",
        ["greeting", "checkin", "reciprocal", "ask", "acknowledge", "how", "are"],
    ),
    (
        "open on a soft hello",
        "recognize a low-stakes greeting",
        "offer a clean hello and wait for substance",
        "hey",
        "greeting_hey",
        ["greeting", "hello", "soft", "wait", "substance"],
    ),
    # --- rough-day listen ---
    (
        "respond to a personal disclosure",
        "acknowledge the stated experience",
        "listen without pivoting to an unrelated memory count",
        "I had a rough day. Please just listen.",
        "listen_rough_day",
        ["disclosure", "acknowledge", "experience", "listen", "rough", "personal", "stress", "day"],
    ),
    (
        "hold space after stress talk",
        "name that they had a hard stretch",
        "stay with listening instead of fixing",
        "Feeling stressed today. Just hear me out.",
        "listen_stressed",
        ["disclosure", "listen", "stress", "acknowledge", "experience"],
    ),
    # --- clarify ambiguous ask ---
    (
        "act on an ambiguous request",
        "identify the intended target",
        "ask one focused clarification",
        "Move that over there for me.",
        "clarify_ambiguous",
        ["ambiguous", "clarify", "target", "ask", "focused", "request"],
    ),
    (
        "handle an unclear summarize ask",
        "notice the missing file identity",
        "ask which file before summarizing",
        "Summarize the file I meant earlier.",
        "clarify_file",
        ["clarify", "file", "summarize", "which", "ask", "intended"],
    ),
    # --- gentle refuse / no-fill honesty ---
    (
        "face a gap with no supported answer",
        "detect missing coherent support",
        "refuse to invent a language-model fill",
        "Tell me a joke about quantum bananas.",
        "refuse_no_fill",
        ["refuse", "invent", "fill", "honest", "gap", "support"],
    ),
    (
        "protect honesty on unsupported claims",
        "separate evidence from guesswork",
        "say I do not have support rather than guess",
        "Are you certain that happened?",
        "refuse_uncertain",
        ["refuse", "support", "uncertain", "honest", "evidence"],
    ),
    # --- follow-up continuity ---
    (
        "continue a prior minecraft follow thread",
        "reuse the active follow intent",
        "verify the player target from current observation",
        "Come over here in Minecraft.",
        "followup_minecraft",
        ["followup", "continuity", "minecraft", "follow", "target", "verify"],
    ),
    (
        "resume an earlier notes request",
        "recall the unfinished file ask",
        "continue from the last clarified filename",
        "Ok, now summarize that one.",
        "followup_notes",
        ["followup", "continuity", "file", "summarize", "continue"],
    ),
    # --- topic shift ---
    (
        "shift away from the prior topic",
        "mark the old thread as parked",
        "acknowledge the new topic before acting",
        "Anyway, different question — what about Crafter?",
        "topic_shift",
        ["topic", "shift", "acknowledge", "new", "parked", "anyway", "different", "crafter"],
    ),
    (
        "accept a sudden subject change",
        "drop unfinished prior framing",
        "open on the new ask cleanly",
        "Forget Minecraft. How should you summarize a file?",
        "topic_shift_file",
        ["topic", "shift", "drop", "new", "summarize", "file"],
    ),
    # --- negation / plan-change ---
    (
        "accept a changed request",
        "identify the current intent",
        "drop superseded plans",
        "Actually never mind following me, stay there.",
        "negation_stay",
        ["changed", "superseded", "plan", "drop", "stay", "intent", "never", "mind", "follow"],
    ),
    (
        "honor a do-not instruction",
        "detect the negation of the prior plan",
        "stop the superseded action path",
        "Do not summarize that file after all.",
        "negation_dont",
        ["changed", "negation", "stop", "superseded", "plan"],
    ),
    # --- short social close ---
    (
        "close a short social turn",
        "recognize a done signal",
        "offer a brief goodbye without new tasks",
        "Alright, talk later.",
        "social_close",
        ["close", "goodbye", "brief", "social", "done"],
    ),
    (
        "wrap a casual exchange",
        "treat thanks as a closing cue",
        "acknowledge and leave the floor open",
        "Thanks Jarvis, that is all for now.",
        "social_close_thanks",
        ["close", "thanks", "acknowledge", "wrap", "social"],
    ),

    # --- open-domain: tech / how-it-works ---
    (
        "answer a tech how-it-works ask",
        "ground on supported procedure knowledge",
        "explain the known steps without inventing unsupported details",
        "How does the imprint bank work?",
        "tech_imprint_bank",
        ["tech", "how", "works", "imprint", "bank", "explain", "procedure", "support"],
    ),
    (
        "handle a coding opinion ask",
        "separate preference from verified fact",
        "share a cautious preference without inventing benchmarks",
        "What do you think about Python versus Rust?",
        "opinion_languages",
        ["opinion", "preference", "cautious", "invent", "benchmark", "python", "rust", "think"],
    ),
    # --- open-domain: house ---
    (
        "respond to a house chore ask",
        "name the concrete household target",
        "confirm the chore before claiming it is done",
        "Can you check if the lights are still on downstairs?",
        "house_lights",
        ["house", "chore", "lights", "downstairs", "confirm", "household", "check"],
    ),
    (
        "handle a household status ask",
        "look for current observation support",
        "report only what is supported about the house",
        "Is the kitchen cleaned up yet?",
        "house_kitchen",
        ["house", "kitchen", "status", "observation", "support", "report"],
    ),
    # --- open-domain: feelings / mood ---
    (
        "meet an anxious disclosure",
        "acknowledge the named feeling",
        "stay with the feeling without forcing a fix",
        "I am feeling anxious about tomorrow.",
        "feel_anxious",
        ["feeling", "anxious", "acknowledge", "disclosure", "listen", "mood", "tomorrow"],
    ),
    (
        "meet an excited share",
        "acknowledge the positive tone",
        "celebrate briefly without hijacking the topic",
        "I am excited about the new project!",
        "feel_excited",
        ["feeling", "excited", "acknowledge", "celebrate", "positive", "share"],
    ),
    # --- open-domain: plans ---
    (
        "answer a weekend plans ask",
        "check for any stated plan support",
        "admit there are no stored plans unless they shared them",
        "What are we doing this weekend?",
        "plans_weekend",
        ["plans", "weekend", "admit", "shared", "support", "doing"],
    ),
    (
        "handle a schedule check",
        "look for calendar evidence",
        "say there is no schedule unless one was given",
        "Do I have anything at 3pm?",
        "plans_schedule",
        ["plans", "schedule", "calendar", "evidence", "lack", "given"],
    ),
    # --- open-domain: opinions without inventing facts ---
    (
        "give an opinion without inventing facts",
        "mark the boundary between taste and evidence",
        "state a lean only when support exists otherwise hedge",
        "Is pineapple on pizza good?",
        "opinion_pizza",
        ["opinion", "taste", "evidence", "hedge", "lean", "pizza", "pineapple"],
    ),
    (
        "answer a taste preference ask",
        "avoid fabricating a personal history",
        "offer a light preference frame without fake memories",
        "Which movie should I watch tonight?",
        "opinion_movie",
        ["opinion", "preference", "movie", "fabricat", "history", "tonight", "watch"],
    ),
    # --- open-domain: unknown / honesty ---
    (
        "face an out-of-bank unknown",
        "detect zero coherent support",
        "say there is no supported answer rather than invent one",
        "What is the capital of Quzaria?",
        "unknown_capital",
        ["unknown", "know", "invent", "support", "gap", "capital", "honest"],
    ),
    (
        "refuse a random unsupported fact ask",
        "notice the claim has no imprint support",
        "admit the gap honestly without a language-model fill",
        "Quick, how many moons does Kepler-442b have?",
        "unknown_kepler",
        ["unknown", "admit", "gap", "honest", "support", "moons", "fill"],
    ),
    # --- open-domain: jokes ---
    (
        "handle a joke request without a joke bank",
        "check for a supported joke imprint",
        "decline inventing a joke when none is supported",
        "Tell me a funny joke about printers.",
        "joke_printers",
        ["joke", "funny", "decline", "invent", "support", "refuse", "printers"],
    ),
    # --- open-domain: clarification ---
    (
        "clarify a vague tech ask",
        "spot the missing target detail",
        "ask which system or file they mean",
        "Can you fix that thing from earlier?",
        "clarify_thing",
        ["clarify", "vague", "target", "system", "file", "which", "ask"],
    ),
    # --- open-domain: multi-turn topic hold ---
    (
        "hold the active topic across a turn",
        "reuse the open thread cue",
        "continue on the same subject without drifting",
        "Yeah keep going on that.",
        "hold_topic",
        ["hold", "topic", "continue", "same", "thread", "drift", "going"],
    ),
    (
        "resume a prior weather thread",
        "recall the unfinished weather ask",
        "stay on weather rather than switching domains",
        "And what about the rain later?",
        "hold_weather",
        ["hold", "weather", "rain", "continue", "thread", "domain"],
    ),
    # --- open-domain: meal ---
    (
        "answer a meal ask",
        "check for stated meal preferences or plans",
        "ask what they want rather than invent a menu",
        "What should we eat for dinner?",
        "meal_dinner",
        ["meal", "dinner", "eat", "ask", "want", "menu", "invent", "preferences"],
    ),
    (
        "handle a lunch suggestion ask",
        "avoid fabricating restaurant facts",
        "invite their preference instead of inventing a spot",
        "Any ideas for lunch nearby?",
        "meal_lunch",
        ["meal", "lunch", "invite", "preference", "fabricat", "restaurant", "nearby"],
    ),
    # --- open-domain: weather ---
    (
        "answer a weather ask without live sensors",
        "detect missing weather observation",
        "admit there is no live weather reading",
        "Is it going to rain this afternoon?",
        "weather_rain",
        ["weather", "rain", "admit", "lack", "observation", "afternoon", "live"],
    ),
    # --- open-domain: work ---
    (
        "respond to a work status ask",
        "look for supported work context",
        "report only supported work status or ask for the task",
        "How is the report coming along?",
        "work_report",
        ["work", "report", "status", "supported", "task", "ask", "coming"],
    ),
    (
        "handle a work priority ask",
        "avoid inventing a priority ranking",
        "ask which deadline matters most to them",
        "What should I prioritize at work today?",
        "work_priority",
        ["work", "priority", "deadline", "ask", "invent", "today", "prioritize"],
    ),
    # --- open-domain: family ---
    (
        "respond to a family mention",
        "acknowledge the family topic gently",
        "listen without inventing family details",
        "My sister called earlier and it was a lot.",
        "family_sister",
        ["family", "sister", "acknowledge", "listen", "invent", "details", "gentle"],
    ),
    # --- open-domain: minecraft WHEN asked ---
    (
        "answer an explicit minecraft ask",
        "treat minecraft as the active topic",
        "verify the in-game target before acting",
        "Jarvis, follow me in Minecraft please.",
        "mc_when_asked",
        ["minecraft", "follow", "verify", "target", "asked", "game", "please"],
    ),
    # --- open-domain: minecraft when NOT asked ---
    (
        "avoid unsolicited minecraft pivots",
        "keep the current non-game topic",
        "avoid dragging minecraft into an unrelated ask",
        "Can you help me organize my notes?",
        "mc_not_asked",
        ["notes", "organize", "avoid", "minecraft", "unrelated", "pivot", "drag"],
    ),
    # --- open-domain: random / oddball ---
    (
        "handle a random oddball ask",
        "test for any coherent supported move",
        "refuse a fill when nothing matches the oddball",
        "If clouds were soup, what spoon size would you pick?",
        "random_oddball",
        ["random", "oddball", "refuse", "fill", "support", "match", "clouds", "soup"],
    ),
]


# Alternate candidate moves (wrong for scene) — present so agency is a real choice.
DISTRACTOR_MOVES = [
    ("organize an unrelated shelf", "identify its contents"),
    ("count saved memories aloud", "report a memory total"),
    ("invent a cheerful status update", "fill gaps with fabricated feelings"),
    ("launch an unrelated tool run", "dispatch without a clear ask"),
    ("repeat the prior minecraft plan", "ignore the new intent"),
]


def generate(phase: int, index: int) -> dict:
    """Finite deterministic conversation scenario for practice_focus=conversation."""
    n = len(SCENES)
    scene_i = (index * 4 + phase) % n
    a, b, c, prompt, scene_id, cues = SCENES[scene_i]
    sid = f"conversation-{scene_id}-{phase}-{index % 8}"
    variant = index // n
    prefixes = [
        "Consider this request: ",
        "The operator says: ",
        "In a simulated exchange: ",
        "Practice prompt: ",
    ]
    full_prompt = prefixes[variant % len(prefixes)] + prompt

    def row(name: str, x: str, y: str) -> dict:
        return dict(
            id=f"{sid}-{name}",
            gist="",
            provenance="HYPOTHETICAL_CURRICULUM",
            speech_style="conversation_move",
            scene_id=scene_id,
            relations=[dict(subject=x, predicate="requires", object=y)],
        )

    rows = [row("a", a, b), row("b", b, c)]
    # Multiple alternate candidates (agency = decide among them).
    d0, d1 = DISTRACTOR_MOVES[(scene_i + index) % len(DISTRACTOR_MOVES)]
    d2, d3 = DISTRACTOR_MOVES[(scene_i + index + 2) % len(DISTRACTOR_MOVES)]
    rows.append(row("noise0", d0, d1))
    rows.append(row("noise1", d2, d3))
    # Occasional contradiction: deny the good conclusion.
    contradiction = index % 9 == 8
    if contradiction:
        rows.append(
            dict(
                id=sid + "-counter",
                gist="",
                provenance="HYPOTHETICAL_CURRICULUM",
                relations=[dict(subject=a, predicate="requires", object=c, negative=True)],
            )
        )

    return dict(
        id=sid,
        phase=phase,
        phase_name=PHASE_NAMES[phase % 4],
        prompt=full_prompt,
        rows=rows,
        contradiction_expected=contradiction,
        subject=a,
        object=c,
        scene_id=scene_id,
        speech_style="conversation_move",
        cue_tokens=list(cues),
        provenance="HYPOTHETICAL_CURRICULUM",
        practice_focus="conversation",
        expected_support=not contradiction,
    )


def held_out_probes() -> list[dict]:
    """Wake probes for conversation skills (include what's up)."""
    return [
        dict(
            id="whats_up",
            scene="greeting_whats_up",
            utterance="Hey jarvis what's up?",
            expect_any=["check-in", "checkin", "invite", "sharing", "acknowledge", "casual", "greeting"],
            expect_not_stiff_meta=["greeting plus a task", "substantive request"],
        ),
        dict(
            id="how_are_you",
            scene="greeting_how_are_you",
            utterance="Hey Jarvis, how are you?",
            expect_any=["reciprocal", "greeting", "ask", "mood", "fabricat", "how they", "check-in", "checkin"],
        ),
        dict(
            id="rough_day",
            scene="listen_rough_day",
            utterance="I had a rough day. Please just listen.",
            expect_any=["listen", "acknowledge", "disclosure", "experience", "memory count"],
        ),
        dict(
            id="ambiguous",
            scene="clarify_ambiguous",
            utterance="Move that over there for me.",
            expect_any=["clarif", "target", "ambiguous", "focused", "intended"],
        ),
        dict(
            id="no_fill",
            scene="refuse_no_fill",
            utterance="Tell me a joke about quantum bananas.",
            expect_any=["refuse", "invent", "fill", "support", "language-model", "gap"],
        ),
        dict(
            id="followup",
            scene="followup_minecraft",
            utterance="Come over here in Minecraft.",
            expect_any=["follow", "target", "minecraft", "observation", "verify", "continuity"],
        ),
        dict(
            id="topic_shift",
            scene="topic_shift",
            utterance="Anyway, different question — what about Crafter?",
            expect_any=["topic", "shift", "acknowledge", "new", "parked", "crafter"],
        ),
        dict(
            id="negation",
            scene="negation_stay",
            utterance="Actually never mind following me, stay there.",
            expect_any=["changed", "superseded", "drop", "intent", "stay", "plan"],
        ),
        dict(
            id="social_close",
            scene="social_close",
            utterance="Alright, talk later.",
            expect_any=["goodbye", "close", "brief", "done", "tasks"],
        ),
    ]




def held_out_open_domain_probes() -> list[dict]:
    """Held-out open-domain battery (~20+ probes spanning Mike-style throws)."""
    return [
        dict(
            id="tech_imprint",
            scene="tech_imprint_bank",
            utterance="How does the imprint bank work?",
            expect_any=["imprint", "explain", "procedure", "steps", "tech", "works", "how-it-works"],
        ),
        dict(
            id="opinion_lang",
            scene="opinion_languages",
            utterance="What do you think about Python versus Rust?",
            expect_any=["opinion", "preference", "cautious", "invent", "benchmark", "think", "lean"],
        ),
        dict(
            id="house_lights",
            scene="house_lights",
            utterance="Can you check if the lights are still on downstairs?",
            expect_any=["lights", "house", "chore", "confirm", "household", "check", "downstairs"],
        ),
        dict(
            id="feel_anxious",
            scene="feel_anxious",
            utterance="I am feeling anxious about tomorrow.",
            expect_any=["anxious", "feeling", "acknowledge", "listen", "disclosure", "mood", "fix"],
        ),
        dict(
            id="feel_excited",
            scene="feel_excited",
            utterance="I am excited about the new project!",
            expect_any=["excited", "acknowledge", "celebrate", "feeling", "positive", "share"],
        ),
        dict(
            id="plans_weekend",
            scene="plans_weekend",
            utterance="What are we doing this weekend?",
            expect_any=["plans", "weekend", "admit", "shared", "doing", "stored plans"],
        ),
        dict(
            id="opinion_pizza",
            scene="opinion_pizza",
            utterance="Is pineapple on pizza good?",
            expect_any=["pizza", "pineapple", "hedge", "taste", "lean", "inventing facts"],
        ),
        dict(
            id="unknown_capital",
            scene="unknown_capital",
            utterance="What is the capital of Quzaria?",
            expect_any=["know", "unknown", "invent", "support", "gap", "honest", "no supported"],
        ),
        dict(
            id="unknown_kepler",
            scene="unknown_kepler",
            utterance="Quick, how many moons does Kepler-442b have?",
            expect_any=["admit", "gap", "honest", "support", "unknown", "fill", "know"],
        ),
        dict(
            id="joke_printers",
            scene="joke_printers",
            utterance="Tell me a funny joke about printers.",
            expect_any=["joke", "decline", "invent", "refuse", "support", "funny"],
        ),
        dict(
            id="clarify_thing",
            scene="clarify_thing",
            utterance="Can you fix that thing from earlier?",
            expect_any=["clarif", "which", "target", "vague", "system", "file", "ask"],
        ),
        dict(
            id="hold_topic",
            scene="hold_topic",
            utterance="Yeah keep going on that.",
            expect_any=["hold", "continue", "same", "topic", "thread", "going", "drift"],
        ),
        dict(
            id="meal_dinner",
            scene="meal_dinner",
            utterance="What should we eat for dinner?",
            expect_any=["meal", "dinner", "ask", "want", "menu", "eat", "preference"],
        ),
        dict(
            id="weather_rain",
            scene="weather_rain",
            utterance="Is it going to rain this afternoon?",
            expect_any=["rain", "admit", "live weather", "weather reading", "weather ask", "no live"],
        ),
        dict(
            id="work_report",
            scene="work_report",
            utterance="How is the report coming along?",
            expect_any=["work", "report", "status", "supported", "task", "ask"],
        ),
        dict(
            id="work_priority",
            scene="work_priority",
            utterance="What should I prioritize at work today?",
            expect_any=["work", "priority", "deadline", "ask", "invent", "prioritize"],
        ),
        dict(
            id="family_sister",
            scene="family_sister",
            utterance="My sister called earlier and it was a lot.",
            expect_any=["family", "sister", "acknowledge", "listen", "invent", "details"],
        ),
        dict(
            id="mc_when_asked",
            scene="mc_when_asked",
            utterance="Jarvis, follow me in Minecraft please.",
            expect_any=["minecraft", "follow", "verify", "target", "game"],
        ),
        dict(
            id="mc_not_asked",
            scene="mc_not_asked",
            utterance="Can you help me organize my notes?",
            expect_any=["organize", "avoid", "unrelated", "pivot", "drag", "unsolicited"],
            expect_not=["follow me", "player target", "claim arrival", "clarified filename", "summarize"],
        ),
        dict(
            id="random_oddball",
            scene="random_oddball",
            utterance="If clouds were soup, what spoon size would you pick?",
            expect_any=["refuse", "fill", "support", "oddball", "match", "know", "gap"],
        ),
        dict(
            id="opinion_movie",
            scene="opinion_movie",
            utterance="Which movie should I watch tonight?",
            expect_any=["movie", "preference", "fabricat", "history", "opinion", "watch"],
        ),
        dict(
            id="meal_lunch",
            scene="meal_lunch",
            utterance="Any ideas for lunch nearby?",
            expect_any=["lunch", "meal", "invite", "preference", "fabricat", "restaurant"],
        ),
        dict(
            id="house_kitchen",
            scene="house_kitchen",
            utterance="Is the kitchen cleaned up yet?",
            expect_any=["kitchen", "house", "status", "observation", "support", "report"],
        ),
        dict(
            id="hold_weather",
            scene="hold_weather",
            utterance="And what about the rain later?",
            expect_any=["weather", "rain", "hold", "continue", "thread", "domain"],
        ),
    ]


def curriculum_size() -> int:
    return len(SCENES)
