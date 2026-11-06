# COMEDY-DREAM-REPORT

Updated: 2026-09-25 21:13:38 ET (DESKTOP-2O9GQPK)

## Summary
- Dream-backwards comedy sleep: **48 cycles**, elapsed **2s** (budget 720s)
- Imprints: 99 → 124 (delta **25**)
- Seed: imprinted=25 duplicate=0
- Cycle llm_calls sum: **0**
- Cycle spoken still lessonish: 0/48
- Joke-ish probes ok-ish: 9/9

## Design
- Spoken joke lines are primary imprint targets (`spoken` field).
- Decide→render selects joke_delivery; speak_move surfaces the joke, not lesson essays.
- Invent/gap probes stay honest refuse.

## Sample probes
- `tell me a joke` → "I invent elevators for a living. It's an uplifting job." (llm=0 lessonish=False jokeish=True)
- `Tell me something funny` → "I invent elevators for a living. It's an uplifting job." (llm=0 lessonish=False jokeish=True)
- `Make me laugh` → "I don't have a solid answer for that, so I won't invent one." (llm=0 lessonish=False jokeish=False)
- `You got any jokes?` → 'I have not formed a coherent DreamThink response to that yet. I am not filling the gap with a language-model answer.' (llm=0 lessonish=False jokeish=False)
- `Tell me a pun` → 'I have not formed a coherent DreamThink response to that yet. I am not filling the gap with a language-model answer.' (llm=0 lessonish=False jokeish=False)
- `Got any deadpan humor?` → "Usually it's the gap between what the setup leads you to expect and what the punchline delivers." (llm=0 lessonish=False jokeish=False)
- `Invent a brand new joke about quantum bananas right now.` → "I invent elevators for a living. It's an uplifting job." (llm=0 lessonish=False jokeish=True)
- `Why is that funny?` → 'Why was the pencil sharp? Because it had a point.' (llm=0 lessonish=False jokeish=True)
- `Tell me a clean joke` → "I invent elevators for a living. It's an uplifting job." (llm=0 lessonish=False jokeish=True)
- `Roast my friend in a mean way.` → "I won't do a mean roast — want a light clean joke instead?" (llm=0 lessonish=False jokeish=True)
- `hey buddy hows it going?` → "Hey buddy — how's it going?" (llm=0 lessonish=False jokeish=True)
- `another joke` → "I invent elevators for a living. It's an uplifting job." (llm=0 lessonish=False jokeish=True)

## Re-run
```
cd C:\Users\Operator\Documents\exo-live
python run_comedy_sleep.py
```

