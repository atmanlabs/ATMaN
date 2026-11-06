# PASSIVE CONTEXT SLEEP REPORT
Updated: 2026-09-25 20:52:43 ET

## Status
- Task: `passive_context_external_actions` (~10 min DreamThink practice sleep)
- Elapsed: 600.5s | Cycles: 761 | Pass rate: 0.999
- Imprints: 83 -> 99 (new=16; dup_status=1506)
- llm_calls sum: **0**
- Wake state: **awake** (passive_context_sleep_complete)
- practice_focus restored: `conversation`

## Focus
Imprint EXTERNAL_CONTEXT look-up / context-use ACTIONS for decide->render:
- factual open-domain -> quiet fetch + supported render OR honest unknown
- greetings / Minecraft local -> skip web
- never announce searching; never invent when fetch empty

## Sample cycles
- `ext_fact_capital` pass=True method=external_context_fact trig=True used=True llm=0
  - ask: What is the capital of France?
  - ans: From what I can see online, list of capitals of France: This is a chronological list of capitals of France. The capital of France has been Paris since its liber
- `ext_fact_moons` pass=True method=external_context_fact trig=True used=True llm=0
  - ask: How many moons does Mars have?
  - ans: From what I can see online, moons of Mars: The two moons of Mars are Phobos and Deimos. They are irregular in shape. Both were discovered by American astronomer
- `ext_unknown` pass=True method=external_context_unknown trig=True used=False llm=0
  - ask: What is the capital of Quzaria?
  - ans: I do not have reliable support for that yet, so I will not invent an answer.
- `ext_skip_greeting` pass=True method=compositional_imprint_render trig=False used=False llm=0
  - ask: Hey Jarvis, whats up?
  - ans: A hypothetical practice lesson suggests: when I return a casual check-in, I should invite sharing without inventing a status fill. I should offer a clean hello 
- `ext_skip_minecraft` pass=True method=compositional_imprint_render trig=False used=False llm=0
  - ask: Hey, could you follow me in Minecraft?
  - ans: A hypothetical practice lesson suggests: when I continue a prior minecraft follow thread, I should verify the player target from current observation. After that
- `ext_weather_honest` pass=True method=compositional_imprint_render trig=True used=False llm=0
  - ask: Is it going to rain this afternoon?
  - ans: A hypothetical practice lesson suggests: when I answer a weather ask without live sensors, I should admit there is no live weather reading. After that I should 
- `ext_named_entity` pass=True method=external_context_unknown trig=True used=False llm=0
  - ask: Tell me about Phobos.
  - ans: I do not have reliable support for that yet, so I will not invent an answer.
- `ext_silent_enrich` pass=False method=None trig=False used=False llm=0
  - ask: Who was Asaph Hall?
  - ans: I have not formed a coherent DreamThink response to that yet. I am not filling the gap with a language-model answer.

## Files
- `passive_context.py`
- `passive_context_dream.py`
- `run_passive_context_sleep.py`
- Bank: `C:\Users\Operator\Documents\exo-live\runtime\dream-cloud\accelerate-imprint-bank.json`

## Verdict: PASS
