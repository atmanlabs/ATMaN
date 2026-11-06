# Book Test — Morning Report: Sherlock Holmes overnight

**Date:** 2026-09-26. **Corpus:** full Holmes canon, public domain (Gutenberg).
4 novels + 45 stories across 8 texts, 1,660 chunks, ~567k words.
(The Case-Book's 12 stories weren't on Gutenberg as clean text — noted, not hidden.)

## What ran

| | Mode A (generated) | Mode B (rendered / decide→render) |
|---|---|---|
| Dreams | 300 | 300 |
| Imprinted to PSC | 294 | 283 |
| Held by guardian | 2 | 0 |
| Errors | 0 | 0 |
| Unique chunks sampled | 900 (54%) | 900 (54%) |
| Coverage | uniform across all 8 books | uniform across all 8 books |

Isolated devices, separate PSCs, Judge-gated, TSC untouched. Provenance
labels on everything. Zero network calls.

## The quiz (12 probes: Mycroft, Mrs. Hudson, Jefferson Hope, violin,
Moriarty/Reichenbach, the Hound, Irene Adler, 221B, Agra treasure,
Mary Morstan, cocaine, Lestrade)

- **Mode A: 1/12.** Mode B: 2/12.
- Most questions retrieved *something* (9–10/12), but the retrieved
  fragments didn't contain answers. A few honest gaps ("I don't have
  anything solid on that").
- **Zero confabulation found.** Neither mode invented a single fact.
  The bullshit test passed in the negative direction: he doesn't make
  things up — he just doesn't *know*.

## The honest finding

**Dreaming over a book is not learning a book.**

The dreams consolidated *themes* ("what connects crime, holmes across
these threads") — genuine abstraction. But they did not build *factual
knowledge*. Character names appear in dream texts at corpus rates
(lestrade ×11, morstan ×8, agra ×8 in Mode B), yet the sim cannot answer
"who is Mycroft" — it can only quote the fragment where the name happened
to land, or admit the gap.

The dream cycle was built to turn *experiences* into *lessons*. Pointed
at a text corpus, it behaves like a thematic braider, not a student.
For book-learning, what you actually want is indexed retrieval over the
corpus — the dream adds nothing to factual Q&A.

Mode B (decide→render) showed **no advantage or disadvantage** on factual
recall vs Mode A. The decide-first structure didn't help consolidation
and didn't hurt it. Its gist format is slightly worse for retrieval
(question-words pollute the gist); Mode A's raw fragments retrieve
better. That's a formatting note, not a verdict on the thesis.

## What this means for the overnight-expert idea

The strong version — "load any book overnight, wake up expert" — is
**falsified by this test**, at least for the dream mechanism. What the
dreams produce is real (thematic threads, grounded, no invention), but
it is not knowledge you can be quizzed on. Consolidation ≠ memorization,
and abstraction ≠ recall.

This doesn't kill the idea. It bounds it: dreams may be the right
mechanism for turning *lived experience* into *judgment*, while *text
ingestion* wants a different pipeline (retrieval + structured
extraction). The next experiment, if you want it: build the text
pipeline and test whether *it* survives your interrogation.

## Bugs caught

- **Sampler bias (fixed):** the feed sampler walked the corpus
  front-to-back (all weights equal → stable sort → in-order traversal).
  First run covered 5 books at 100% and 3 at ~0%. Fixed by shuffling
  the corpus at load; re-ran clean.
- **Quiz retrieval (known weakness):** pure word-overlap over fragments
  ties on generic words ("holmes" + "crime" beats "brother" + "holmes"
  by sort order). The interactive quiz has the same weakness — take its
  misses as "not found," not "not there."

## Ready for you

- `python3 quiz.py ask mode-a` / `python3 quiz.py ask mode-b` — interrogate
  either sim yourself. You'll see exactly what I saw: fragments or honest
  gaps, never invention.
- Full logs: `corpus-dreams/mode-a/` and `corpus-dreams/mode-b/`
  (dreams.jsonl, coma-cycles.jsonl, psc.json, summary.json, quiz-report.json).
- The sims' PSCs are intact and isolated — quiz them as much as you want.

## Bottom line

He read the whole canon overnight and dreamed 600 dreams about it.
Ask him anything — he'll either show you the fragment or tell you he
doesn't know. He won't bullshit you. But he's not an expert. He's a
guy who dreamed about a book.
