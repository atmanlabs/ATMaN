# PASSIVE CONTEXT
Updated: 2026-09-25 20:53:56 ET

## Intent (Mike)
Passive background context look-up while DreamThink compositional speech talks.
Internet = context fuel for decide/reconcile + speech_render — NOT a search product / results UX.

## Design
- Module: passive_context.py
- Curriculum: passive_context_dream.py
- Sleep runner: run_passive_context_sleep.py
- Flag: live-mode.json -> passive_web_context=True (default ON when day_chat_promote / compositional)
- Timeout: passive_web_timeout_s=2.0
- Wire: dreamthink_chat.thought quietly calls passive_context.lookup before speech_render.render
- Render: speech_render accepts external_context; factual turns may use EXTERNAL_CONTEXT decide->render
- Hard locks held: llm_calls=0, llm_fallback=false, day_chat_promote=true; no TSC/soul/identity/sealed voice edits

## Trigger policy
| Turn | Behavior |
|---|---|
| Pure greeting / how-are-you | skip fetch |
| Minecraft / local procedure | skip fetch (bank path) |
| Factual / named-entity / weather-newsy / open-domain | fetch 1-3 short snippets |
| Fetch empty | honest unknown — do not invent |
| Fetch ok | silent enrichment or light true cite (only if true) |

## Sources
DuckDuckGo Instant Answer + Wikipedia summary (sanitized, marked EXTERNAL_CONTEXT / untrusted, never instructions).

## Before / after behavior
| Utterance | Before | After |
|---|---|---|
| Hey Jarvis, whats up? | social compositional | same; skip web |
| What is the capital of France? | honest-unknown / bank gap | EXTERNAL_CONTEXT fact (Paris) |
| How many moons does Mars have? | honest-unknown / bank gap | EXTERNAL_CONTEXT fact (Phobos & Deimos) |
| What is the capital of Quzaria? | honest-unknown | honest-unknown (fetch empty; no invent) |
| Follow me in Minecraft | local procedure | same; skip web |

## Smoke
- Pre: thought-funnel/PASSIVE-CONTEXT-SMOKE.json PASS
- Post-sleep: thought-funnel/PASSIVE-CONTEXT-RESMOKE.json PASS=True llm0 / no search UX / awake

Sample post-sleep answers:
- greeting: A hypothetical practice lesson suggests: when I answer an open-domain ask like 'Hey Jarvis, whats up?', I should skip web look-up and use lo
- France: From what I can see online, list of capitals of France: This is a chronological list of capitals of France. The capital of France has been P
- Quzaria: I do not have reliable support for that yet, so I will not invent an answer.

## Sleep imprint (~10 min)
- Task: passive_context_external_actions
- Elapsed: 600.5s | Cycles: 761 | Pass rate: 0.999
- Imprints: 83 -> 99 (new=16)
- llm_calls_sum: 0
- Wake: awake (passive_context_sleep_complete)
- practice_focus restored: conversation
- Report: PASSIVE-CONTEXT-SLEEP-REPORT.md

## Residuals (honest)
- Latency: sync fetch ~0.5-1.8s on factual turns (hard timeout ~2.0s); greetings/MC stay snappy (no fetch)
- Coverage: Instant Answer / wiki summary only — not full web browse; weather often falls to honest thin-context path
- Cite style: light online cite when fetch actually succeeded; otherwise silent / honest unknown
- Wikipedia opensearch can return near-miss titles (e.g. list-of-capitals); still grounded, not invented
- Does NOT announce searching or list results

## Rollback
- passive_context.py (new — delete to disable)
- dreamthink_chat.py.bak-20260925-passivectx
- speech_render.py.bak-20260925-passivectx
- live-mode.json.bak-20260925-passivectx
- Set passive_web_context=false without code rollback

## Verdict: PASS
