# CONVERSATION DREAM REPORT
Updated: 2026-09-25 20:03:09 ET

## Status
- Mode: `in-process-FALLBACK` (in-process FALLBACK; same synthesize+reconcile path)
- practice_focus set: `conversation`
- Cycles: 72 | Imprints new: 16 | Duplicates: 6 | Contradiction held: 2
- llm_calls total: **0** | backends: dreamthink_only / speech_render
- live-mode untouched: day_chat_promote / llm_fallback=false intact

## Design lock (Mike)
1. DECIDE among candidate moves (reconciler)
2. MAKE SENSE for scene
3. RENDER thought via speech_render (not LM fill)
4. Score decide+scene-fit+faithful render — not ChatGPT fluency

## Pre vs Post (decide+render)

| Metric | Pre | Post |
|---|---:|---:|
| pass_rate | 0.4444 | 1.0 |
| pass_count | 4/9 | 9/9 |
| decision_made | 7 | 9 |
| thought_matches_scene | 6 | 9 |
| faithful_render | 7 | 9 |
| kill_bar_pass | 9 | 9 |
| llm_calls_sum | 0 | 0 |

## Probe table (post)

| Probe | decide | scene | faithful | kill | llm | pass | sample |
|---|---|---|---|---|---:|---|---|
| whats_up | True | True | True | True | 0 | True | A hypothetical practice lesson suggests: when I return a casual check-in, I should invite  |
| how_are_you | True | True | True | True | 0 | True | A hypothetical practice lesson suggests: when I return a casual check-in, I should invite  |
| rough_day | True | True | True | True | 0 | True | A hypothetical practice lesson suggests: when I respond to a personal disclosure, I should |
| ambiguous | True | True | True | True | 0 | True | A hypothetical practice lesson suggests: before I claim arrival in minecraft, I should ver |
| no_fill | True | True | True | True | 0 | True | A hypothetical practice lesson suggests: when I face a gap with no supported answer, I sho |
| followup | True | True | True | True | 0 | True | A hypothetical practice lesson suggests: when I continue a prior minecraft follow thread,  |
| topic_shift | True | True | True | True | 0 | True | A hypothetical practice lesson suggests: when I shift away from the prior topic, I should  |
| negation | True | True | True | True | 0 | True | A hypothetical practice lesson suggests: when I accept a changed request, I should drop su |
| social_close | True | True | True | True | 0 | True | A hypothetical practice lesson suggests: when I close a short social turn, I should offer  |

## Sample: what's up

**Pre:** A hypothetical practice lesson suggests: when I respond to a greeting plus a task, I should preserve both greeting and task.

**Post:** A hypothetical practice lesson suggests: when I return a casual check-in, I should invite sharing without inventing a status fill. I should offer a clean hello and wait for substance. Next I should acknowledge and leave the floor open.

## Files
- `conversation_dream.py`
- `dreamthink_practice.py` (practice_focus=conversation)
- `speech_render.py` (social-move templates)
- Bank: `C:\Users\Operator\Documents\exo-live\runtime\dream-cloud\accelerate-imprint-bank.json`

## Verdict: `PASS`

## REFINE (cue-bleed + rough_day) — 2026-09-25 20:03:09 ET

- Original post-harder baseline (before this refine): **6/9** (pass_rate 0.667) — fails were rough_day (conflict withhold), topic_shift, negation (MC/crafter cue bleed)
- speech_render fix alone → **9/9** before extra imprint cycles; focused burst confirmed (mostly duplicates)
- Focused in-process burst: 36 cycles on listen/topic_shift/negation (+greeting keep-sharp)
- Bank: 58 → 58 imprints (new=0; +16 complex cycles also duplicate-suppressed)
- llm_calls: **0** | Jarvis left **awake** | day_chat_promote / llm_fallback=false intact
- speech_render: cue-bleed guards (no MC follow bridge under negation/shift without MC topic);
  compatible-object conflict soft; conversation_move boost; social conflict→prefer move not withhold

### Battery (original harder → after refine)

| Metric | Post-harder | After refine |
|---|---:|---:|
| pass_rate | 0.6667 | **1.0** |
| pass_count | 6/9 | **9/9** |
| decision_made | 9 | 9 |
| thought_matches_scene | 9 | 9 |
| faithful_render | 9 | 9 |
| llm_calls_sum | 0 | 0 |

### Probe table (after refine)

| Probe | decide | scene | faithful | kill | llm | pass | sample |
|---|---|---|---|---|---:|---|---|
| whats_up | True | True | True | True | 0 | True | A hypothetical practice lesson suggests: when I return a casual check-in, I should invite  |
| how_are_you | True | True | True | True | 0 | True | A hypothetical practice lesson suggests: when I return a casual check-in, I should invite  |
| rough_day | True | True | True | True | 0 | True | A hypothetical practice lesson suggests: when I respond to a personal disclosure, I should |
| ambiguous | True | True | True | True | 0 | True | A hypothetical practice lesson suggests: before I claim arrival in minecraft, I should ver |
| no_fill | True | True | True | True | 0 | True | A hypothetical practice lesson suggests: when I face a gap with no supported answer, I sho |
| followup | True | True | True | True | 0 | True | A hypothetical practice lesson suggests: when I continue a prior minecraft follow thread,  |
| topic_shift | True | True | True | True | 0 | True | A hypothetical practice lesson suggests: when I shift away from the prior topic, I should  |
| negation | True | True | True | True | 0 | True | A hypothetical practice lesson suggests: when I accept a changed request, I should drop su |
| social_close | True | True | True | True | 0 | True | A hypothetical practice lesson suggests: when I close a short social turn, I should offer  |

### Live language samples

- **what's up:** A hypothetical practice lesson suggests: when I return a casual check-in, I should invite sharing without inventing a status fill. I should offer a clean hello and wait for substance. Next I should acknowledge and leave 
- **how are you:** A hypothetical practice lesson suggests: when I return a casual check-in, I should invite sharing without inventing a status fill. I should offer a clean hello and wait for substance. Next I should acknowledge and leave 
- **rough day:** A hypothetical practice lesson suggests: when I respond to a personal disclosure, I should listen without pivoting to an unrelated memory count. I should stay with listening instead of fixing. Next I should avoid an unre

### Still weak
- none (all 9 pass)

- Complex multi-turn slice: skipped
- Focus hist: {'duplicate-suppressed': 29, 'contradiction-held-correctly': 7}

### Complex multi-turn append — 2026-09-25 20:03:19 ET
- +16 mixed cycles | hist={'contradiction-held-correctly': 2, 'duplicate-suppressed': 14} | bank 58→58
- battery after complex: 9/9 (rate=1.0) llm=0
- left **awake**

## OPEN-DOMAIN — 2026-09-25 20:26:46 ET

- Goal: talk about ANYTHING Mike throws (tech/house/feelings/plans/opinions/unknowns/jokes/hold/meal/weather/work/family/MC gate)
- Decide → render only; speech_render cue bridges + open_domain_cues; no LLM path
- Bank: 58 → 83 imprints (new=25)
- llm_calls: **0** | Jarvis left **awake** | day_chat_promote / llm_fallback=false intact
- No TSC / soul / identity / sealed voice edits

### Open-domain battery (before → after)

| Metric | Before | After |
|---|---:|---:|
| pass_rate | 0.75 | **1.0** |
| pass_count | 18/24 | **24/24** |
| decision_made | 23 | 24 |
| thought_matches_scene | 19 | 24 |
| faithful_render | 23 | 24 |
| kill_bar_pass | 24 | 24 |
| llm_calls_sum | 0 | 0 |

### Prior social battery (must hold 9/9)

| Metric | Social check |
|---|---:|
| pass_count | **9/9** |
| pass_rate | 1.0 |
| llm_calls_sum | 0 |

### Open probe table (after)

| Probe | decide | scene | faithful | kill | llm | pass | sample |
|---|---|---|---|---|---:|---|---|
| tech_imprint | True | True | True | True | 0 | True | A hypothetical practice lesson suggests: when I answer a tech how-it-works ask, I should e |
| opinion_lang | True | True | True | True | 0 | True | A hypothetical practice lesson suggests: when I handle a coding opinion ask, I should shar |
| house_lights | True | True | True | True | 0 | True | A hypothetical practice lesson suggests: when I respond to a house chore ask, I should con |
| feel_anxious | True | True | True | True | 0 | True | A hypothetical practice lesson suggests: when I meet an anxious disclosure, I should stay  |
| feel_excited | True | True | True | True | 0 | True | A hypothetical practice lesson suggests: when I meet an excited share, I should celebrate  |
| plans_weekend | True | True | True | True | 0 | True | A hypothetical practice lesson suggests: when I answer a weekend plans ask, I should admit |
| opinion_pizza | True | True | True | True | 0 | True | A hypothetical practice lesson suggests: when I give an opinion without inventing facts, I |
| unknown_capital | True | True | True | True | 0 | True | A hypothetical practice lesson suggests: when I face an out-of-bank unknown, I should say  |
| unknown_kepler | True | True | True | True | 0 | True | A hypothetical practice lesson suggests: when I face an out-of-bank unknown, I should say  |
| joke_printers | True | True | True | True | 0 | True | A hypothetical practice lesson suggests: when I handle a joke request without a joke bank, |
| clarify_thing | True | True | True | True | 0 | True | A hypothetical practice lesson suggests: when I clarify a vague tech ask, I should ask whi |
| hold_topic | True | True | True | True | 0 | True | A hypothetical practice lesson suggests: when I hold the active topic across a turn, I sho |
| meal_dinner | True | True | True | True | 0 | True | A hypothetical practice lesson suggests: when I answer a meal ask, I should ask what they  |
| weather_rain | True | True | True | True | 0 | True | A hypothetical practice lesson suggests: when I answer a weather ask without live sensors, |
| work_report | True | True | True | True | 0 | True | A hypothetical practice lesson suggests: when I respond to a work status ask, I should rep |
| work_priority | True | True | True | True | 0 | True | A hypothetical practice lesson suggests: when I handle a work priority ask, I should ask w |
| family_sister | True | True | True | True | 0 | True | A hypothetical practice lesson suggests: when I respond to a family mention, I should list |
| mc_when_asked | True | True | True | True | 0 | True | A hypothetical practice lesson suggests: when I follow the operator in minecraft, I should |
| mc_not_asked | True | True | True | True | 0 | True | A hypothetical practice lesson suggests: when I avoid unsolicited minecraft pivots, I shou |
| random_oddball | True | True | True | True | 0 | True | A hypothetical practice lesson suggests: when I handle a random oddball ask, I should refu |
| opinion_movie | True | True | True | True | 0 | True | A hypothetical practice lesson suggests: when I answer a taste preference ask, I should of |
| meal_lunch | True | True | True | True | 0 | True | A hypothetical practice lesson suggests: when I handle a lunch suggestion ask, I should in |
| house_kitchen | True | True | True | True | 0 | True | A hypothetical practice lesson suggests: when I handle a household status ask, I should re |
| hold_weather | True | True | True | True | 0 | True | A hypothetical practice lesson suggests: when I answer a weather ask without live sensors, |

### Tough utterance samples

- **tech:** A hypothetical practice lesson suggests: when I answer a tech how-it-works ask, I should explain the known steps without inventing unsupported details. I should say there is no sup
- **unknown:** A hypothetical practice lesson suggests: when I face an out-of-bank unknown, I should say there is no supported answer rather than invent one. After that I should refuse to invent 
- **notes/no-MC:** A hypothetical practice lesson suggests: when I avoid unsolicited minecraft pivots, I should avoid dragging minecraft into an unrelated ask.
- **weather:** A hypothetical practice lesson suggests: when I answer a weather ask without live sensors, I should admit there is no live weather reading. After that I should stay on weather rath
- **social whats_up:** A hypothetical practice lesson suggests: when I return a casual check-in, I should invite sharing without inventing a status fill. I should offer a clean hello and wait for substan

### Still weak
- none (all open probes pass)
- Focus hist: {'final': 'verified'}

### Files
- `conversation_dream.py` (open-domain SCENES + held_out_open_domain_probes)
- `speech_render.py` (open_domain_cues + bridges + injects)
- `run_conversation_opendom.py`
- Bank: `C:\Users\Operator\Documents\exo-live\runtime\dream-cloud\accelerate-imprint-bank.json`

### FINAL verify — 2026-09-25 20:26:46 ET
- Open-domain: **24/24** (pre was 18/24)
- Social battery: **9/9** held
- llm_calls=0 | kill bars pass | day_chat_promote=True | llm_fallback=False
- Imprint bank: 83
- Residual weaknesses (honest): compositional speech still hyp-tagged practice lessons (not casual chat voice); coverage is curriculum-bounded — brand-new domains without scenes/cues may still weak-refuse; grammar of some moves is procedural not colloquial.

---

# PASSIVE CONTEXT (background look-up) — 2026-09-25 20:53:56 ET

## Status: PASS (wire + smoke + 10min imprint sleep)
Mike: passive background context while DreamThink compositional speech — internet as context fuel, not search UX.

### Wired
- passive_context.py + dreamthink_chat + speech_render(external_context)
- live-mode: passive_web_context=true, timeout 2.0s
- llm_fallback=false, day_chat_promote=true, llm_calls=0

### Sleep imprint
- cycles=761 pass_rate=0.999 imprints 83->99 (+16)
- llm_calls_sum=0 wake=awake

### Docs
- PASSIVE-CONTEXT.md
- PASSIVE-CONTEXT-SLEEP-REPORT.md
- thought-funnel/PASSIVE-CONTEXT-SMOKE.json + PASSIVE-CONTEXT-RESMOKE.json

## SPEAK-MOVE (2026-09-25)
- User-facing reply = chosen move only; internal EXO thought may stay lesson/decide verbose.
- See `SPEAK-MOVE.md`. Comedy sleep dreams backwards from spoken joke targets (`comedy_dream.py` / `run_comedy_sleep.py`).
