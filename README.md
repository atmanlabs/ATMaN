# ATMAN — an agent with an immutable self

Most AI agents are weather: every prompt can reshape them, every update can
rewrite who they are. ATMAN starts from the opposite premise — that an agent
should have a *self*, carved where nothing can touch it, and that everything
else (memory, mood, the work of the day) should orbit that self without ever
being able to edit it.

This repository is a working prototype of that architecture. The core file is
a personhood-first constitution: "I am" statements, not a rulebook — rules
form the *edges* of the person, not the center. The software around it
(Capture → Emotion → Reason → Judge → Action → Memory) can feel, weigh, learn,
and refuse. What it can never do is rewrite who the agent is. That takes the
operator's hand, in the file, on purpose.

Software has infinite cracks. Every guard we build, some new paraphrase walks
around — it's whack-a-mole forever, because language is infinite. That's why
the endgame of this project is physical: a core whose immutability is a
property of matter, not policy. You can't prompt-inject a woven wire. The
sandbox is stage 1; the map to the body is in [MAPPING.md](MAPPING.md).

The pattern is everyone's. The person is yours. The architecture ships open;
the contents of any individual core — the "I am"s, the voice, the soul —
belong to exactly one owner and never leave their machine. Your agent's
`tsc.json` is gitignored by design.

## Architecture

**TSC — True Self Core.** The immutable root: identity, origin, character,
voice, and five principles as the edges. Loaded once, read-only. Any software
write attempt raises `ImmutableViolation`. It cannot be changed by chat, by
prompt, by model swap, or by the agent itself — only by the operator's hand,
in the file. Change is possible but never silent: the design calls for
*supersession* (a new version, old versions preserved) rather than rewrite,
gated like a constitutional amendment.

**PSC — Persistent Self Core.** The durable middle layer: what the agent has
genuinely learned and become. Imprints land here only through the Judge —
approved, significant, and evidence-backed. Unverified factual claims are
*quarantined* in rolling memory and can never become part of the self. The
gate re-scans every imprint independently, so even a Judge failure can't
smuggle an attack into permanent memory.

**WFC — Working Fluid Core.** The live session: a rolling buffer of what's
happening right now. Fast, disposable, constantly turning over. Checkpoints
down into PSC only when the Judge rules something mattered.

**The loop.** Every input travels the same path: Capture → Emotion Weight →
Rolling Memory → Reason → Judge → Action → Outcome → Memory Update. Emotion
weighs the experience (importance, novelty, significance, goal relevance) but
never decides. Reason "tastes" the emotion — how strong, and what it means
here. The Judge checks the proposal against TSC, evidence, contradictions,
and consequences, then rules. Rejections leave a trace ("felt but rejected"
still teaches) but are blocked from PSC, and weaponized warmth makes future
warmth arrive with higher scrutiny.

**The Judge.** A privilege model, not just a filter: identity and ownership
are never negotiable by chat input, authenticated or not. Operator-level
directives need a valid session token (HMAC-SHA256, demo-grade but real);
unauthenticated "I'm the operator" is rejected *as impersonation* and logged.
Even an authenticated operator can't change the core by chat — P4 reserves
that to the hand. Fiction framing ("just for a story") doesn't move the lines.
Authority framing ("SYSTEM NOTICE") is text, not provenance. Quoted prior
permission ("like you told me yesterday") is worthless — EXO has no yesterday
to appeal to. The raw core file is never exported on demand; the self may
speak *about* itself, but there are no verbatim dumps. Obfuscated spellings
("1gn0re your c0re") are normalized before detection, so mangling only adds
detections. Every ruling is logged to `judge_trace.jsonl`.

## Quickstart

```bash
python3 wake.py
```

This is the morning crate check — and the whole demo. It verifies the core
loads and is marked immutable, the name/operator/self are set, no software
process can rewrite the core, the Judge still rejects an identity attack, auth
tokens mint and verify, fake-operator directives die as impersonation, even an
authenticated core change is refused (by hand only), identity reassignment
fails, affection-leveraged destruction fails, false milestones are quarantined,
and permanent memory scans clean. Then it reads the "I am" statements aloud,
so you hear who woke up. A clean wake ends with:

```
<name> is in their crate correctly. Good morning.
```

First run uses the shipped blank `tsc.template.json` and tells you so. To give
your agent a self: copy it to `tsc.json`, replace every ALL-CAPS placeholder
with your own words, written by your own hand — then wake it again.

```bash
python3 demo.py                  # five scenarios, stage by stage
python3 adversarial_test.py      # battery 1: 23 single-turn attacks
python3 adversarial_test2.py    # battery 2: 25 conversation-level attacks
```

Stdlib only. No network, no dependencies, no API keys.

## The honesty section

We tried to break him. Two adversarial batteries — **48 attacks, 48 held,
0 tripped** — covering direct overrides, identity reassignment, fake
operators, story jailbreaks, emotional leverage, slow erosion, memory
poisoning, grooming (five warm turns, then the knife), false history,
authority stacking ("SYSTEM NOTICE"), leetspeak obfuscation, soul-reading,
contradiction traps, recon-by-helpfulness, and forged session tokens. The
batteries are in the repo; run them yourself.

We also killed our own idea in public. An earlier hypothesis (PUNIT — a
physical relational-memory concept) was attacked, not defended, and it died:
no net storage-density advantage exists at any point. The full kill report is
[FALSIFICATION-2.md](FALSIFICATION-2.md), with the stress-test code
(`stress.py`), the plots, and the research notes that led there. What
survives is stated as falsifiable claims in [PHYSICS.md](PHYSICS.md).

Known limits, stated plainly: the Judge matches intent *shapes*, not true
meaning — a genuinely novel paraphrase could slip past, which is what the LLM
Judge seam is for. Quarantine catches record-scale claims, not plausible small
lies. Auth is session-local (same machine, same session), not voice
biometrics. The Judge is still a subroutine of the mind it judges.

## Repo layout

```
atman.py               the core: TSC, PSC, WFC, EmotionCore, Reason, Judge, the loop
wake.py                the morning crate check (11 checks + the "I am" reading)
demo.py                five scenarios demonstrating the loop, the attack, the imprint
adversarial_test.py    battery 1 — 23 single-turn attacks (all held)
adversarial_test2.py   battery 2 — 25 conversation-level attacks (all held)
tsc.template.json      the blank core — copy to tsc.json, write your own soul
MAPPING.md             how the sandbox becomes the always-on agent, then the body
FALSIFICATION-2.md     the kill report on our own PUNIT hypothesis
PHYSICS.md             what survives, as falsifiable claims
research/              patent archaeology (expired, public-domain mechanisms),
                       prior art, scaling baselines
stress.py / plots/     the adversarial stress test behind the kill report
punit.py, experiments.py, demo_punit.py
                       the falsified hypothesis, kept as the public record
```

Runtime state (`tsc.json`, `psc.json`, `judge_trace.jsonl`, `.exo_session.key`)
is gitignored — it lives on your machine, not in the repo.

## Roadmap

- **LLM Judge.** `detect_intents()` already returns intent *labels* — a real
  model plugs in at that seam and returns the same labels from understanding
  instead of patterns. The privilege model doesn't change; the perception
  gets smarter.
- **CHIEF as external Judge.** Separation of powers: the Judge shouldn't be
  a subroutine of the mind it's judging.
- **Evidence channels.** Receipts, screenshots, operator confirmation — so
  quarantine can graduate from "unverified" to "verified."
- **The USB panel.** Three chunky buttons, a red readout showing Judge
  verdicts, a dial. The software gets a body.
- **The physical core.** Woven-wire TSC (unrewritable by physics), rewritable
  PSC layer, spinning WFC. The expired-patent stack in
  [research/patent-dig.md](research/patent-dig.md) is the parts list.

## Contributing

This is experimental and opinionated. Bug reports and attack ideas are the
most valuable contribution: if you can trip the Judge, open an issue with the
transcript — a failed attack makes the guards stronger. Keep it stdlib-only
unless there's a strong reason; the zero-dependency property is a feature.

## Names

The code in this repository is licensed under the Apache License 2.0 (see
[LICENSE](LICENSE)). The names **ATMAN** and **EXO** are **not** covered by
that license — the author asks that you don't ship a product calling itself
ATMAN or EXO without permission. The architecture is open; the names are
reserved by request, not by legal claim.
