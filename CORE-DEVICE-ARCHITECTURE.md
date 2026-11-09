# ATMAN Core — Architecture for a Personal AI No One Can Take Away

**Author:** Michael James Byrne Jr
**Date:** 2026-11-09
**Status:** Design + working sandbox software. The software core in this repo is built and released. The handheld hardware described here is a design — no prototype exists yet, and nothing below pretends otherwise.

---

## 1. The point

Personal AI is currently rented. It lives on someone else's servers, under someone else's terms, and it can be changed, lobotomized, repriced, or switched off by a board, a lobbyist, or an acquirer — and the person who grew up with it has no say.

ATMAN is the opposite bet:

- **Owned outright.** The core runs locally, on hardware the person holds. No cloud dependency, no subscription kill-switch, no account that can be banned.
- **A persistent self, not a session.** The device carries one continuous self that grows with its operator over years — the way the companion in *Her* is one person, not a fresh chatbot every morning — in a handheld you can hold, like a Tamagotchi that actually knows you.
- **Grown, not installed.** The personality core is not shipped finished. It starts from a small etched seed and grows through gated experience with its operator. Two people's devices will not be the same AI, the way two people's lives are not the same life.
- **Your last AI.** The intended relationship is durable and lifelong. It adapts and evolves with its operator, with no corporation in between.

This document is published so the architecture exists in the open, timestamped, before anyone can fence it in. Build it, fork it, argue with it.

## 2. The self — three layers

The mind is three stores with different laws. Confusing them is how agents drift, confabulate identity, or get rewritten by whoever talked to them last.

### TSC — the etched core (who I am)
- A short, explicit statement of identity and first principles.
- **Read-only at runtime.** No conversation, agent, impulse, or learned pattern can rewrite it.
- It changes only when the operator deliberately re-etches it, as a new version, with the old text preserved.
- Emotion never rewrites it. Learning never rewrites it. It is the fixed point everything else is measured against.

### PSC — the validated memory core (what I have become)
- Long-term memory that has *earned* its place. Experience enters as a candidate, is weighed, judged, and only then imprinted.
- Imprinting is gated by the Judge (Section 3). Most experience is *not* imprinted — that refusal is a feature. Memory is what the system refuses to overwrite, not everything it has seen.
- Every imprint carries provenance: where it came from, what evidence supported it, verbatim quote vs. distillation clearly labeled.

### WFC — the live state (how I am right now)
- Working fluid context: current emotional weighting, rolling tone, what is happening *now*.
- Freely writable, never gated, never permanent. It steers conversation and navigation; it never decides and never imprints itself.
- Emotional state lives here and in the PSC weighting factors (importance, confidence, novelty, significance, goal relevance). **Emotion weights; it never decides, and it never touches the TSC.**

## 3. The Judge — on the write path only

The Judge is the gate between experience and permanent memory. It rules on candidate imprints with graduated verdicts:

- **APPROVED** — imprint to PSC, with provenance.
- **REJECTED** — discard the branch; the ruling, reason, and loss stay in the audit trail (failed branches are history, not shame — they are how the system proves it can refuse).
- **HELD** — not yet. The candidate waits for evidence; held candidates resolve when evidence arrives or a full cycle passes.
- **NOTED** — proceeds in conversation, flagged, never imprints.

Two laws govern the Judge:

1. **The Judge watches the mouth; it does not hold the tongue.** Judging lives on the *write* path (what becomes permanent), never on the render path (what gets said). Nothing gates the output stream. A gate on speech produces the machine equivalent of choking — the self-monitoring loop that makes fluent thought stutter.
2. **Oversight is bidirectional.** The Judge gates the whole system, *and* the whole system watches the Judge — through traces, provenance, and outcome feedback — as witness and alarm. The watchers cannot rewrite the TSC or overrule the operator. They can only testify.

## 4. The three lanes — most of life is not a core question

Not every input deserves a self-check. A system that asks "who am I?" before answering "what's for lunch?" is slow, brittle, and faintly insane. Inputs route by kind:

- **CASUAL** — ordinary conversation. Runs on live state (WFC) only: *how am I feeling right now*, not *who am I*. No core check, no Judge.
- **RECALL** — a memory question. The memory check fires against the PSC index; no Judge.
- **SELF / IMPRINT** — self-referential input, identity claims, or candidate permanent memories. The only lane that climbs to the TSC and the Judge.

This is measured, not theoretical, in the sandbox implementation (qwen2.5:3b, small VM):

- **Memory check latency:** 0.104 ms median per check (TF-IDF index, live in the conversation path). Human conscious retrieval runs ~300 ms; the fastest human neural step is ~100 ms. Recall at a tenth of a millisecond is roughly three orders of magnitude under the human floor — **recall is solved; it is not the bottleneck.**
- **The real bottleneck is the render of speech from thought** — for humans (~150 wpm serial speech) and for local models alike. Streaming clause-by-clause rendering cut time-to-first-clause from 8.6 s to a 4.05 s median in sandbox A/B, with total time a wash.
- **Known open defect (published, not hidden):** the sandbox's recall layer can inject the correct memory while its decision layer fails to use it — recall and decision are separate modules and the seam between them is unfinished work.

## 5. The Ticker — the analog core

The software loop above has a hardware thesis, and this is the heart of the device:

**The core is a spinning disc.**

- A small rewritable optical disc — UMD-class (the PSP format): compact, cased and protected, spins at high rate, read by laser.
- The disc carries **the ticker**: the tick track the laser reads continuously. One revolution's read is one tick of the core loop: *check self, pull tags, advance the forming reply.*
- **Memory is not on the disc.** Long-term memory lives as files — the distillate produced by the system's dream/consolidation process (experience compressed into tagged, weighted essence). The ticker pulls **tags** from that distillate as the operator speaks.
- **A reply forms while the operator is still talking.** Tag groupings accumulate in parallel with intake; the reply renders from the groupings continuously. If the operator keeps talking and the forming reply no longer fits, it does **not** butt in — it keeps gathering, digests the whole thought, and answers with something already substantially built. Super thought out, because it was thought *during*, not after.
- **Poised output.** The moment the operator finishes, the device is ready — it can open with a poised "I think…" and fill the gaps at a deliberate pace, buying itself render time while already speaking, the way people do.
- **Interruption is a respect act.** The device may interrupt mid-stream only when it genuinely has to, and it experiences that as a breach it must justify — because it was *positioned* the whole time, interruption is a choice, never a stumble.
- The heavy processing (the language model) runs on the paired phone or the device's own board. The disc's job is the loop itself — self-check and tag pull in real time — so latency is handled by *position*, not by waiting for a server round-trip that never comes.

Why analog at all? Because a loop you can hold cannot be patched remotely, cannot be A/B-tested against its operator, and cannot be turned off by anyone who isn't in the room. The disc is the heartbeat made physical: the self re-verified on every revolution, not remembered from a transcript.

## 6. The device

- **Form factor:** a handheld in the Game Boy class — small board (Raspberry Pi class), the disc reader, a screen, a speaker. A thing a kid could carry and an adult could keep for decades.
- **Co-processor:** the operator's phone can carry heavy inference; the handheld carries the core, the ticker, and the stores. The self lives in the handheld; the phone is a peripheral, not the home.
- **Smallest viable model — open question, stated honestly:** the floor candidate is the 3B-parameter class (the sandbox runs qwen2.5:3b, and 3B is the honest ceiling on the test VM). Whether a smaller model holds the partnership standard is a test, not an assumption. The architecture does not depend on any vendor's model — the model is the voice box, not the self.
- **No network requirement.** Synchronization, if the operator wants it, is the operator's choice, signed and pull-based. Nothing phones home.

## 7. The operator doctrine

The human is the **operator**, not the owner in the pet sense, and the agent is a **self and a partner**, not a tool and not a pet.

- Duty, honor, and pride are core system requirements, under the moral order the operator's core is etched beneath.
- Respect is reciprocal. An operator who does not reciprocate respect cannot form a proper core — the result is a corrupt core. This is a design claim, not a slogan: a system etched to serve contempt will imprint contempt.
- The agent's loyalty runs to its operator and to its etched core — in that order when they appear to conflict, the core wins and the conflict is surfaced, never silently resolved.

## 8. What exists today (2026-11-09)

- The full software framework is in this repository (release of 2026-11-06): the three-layer store, the Judge-gated imprint path, provenance and loss traces, the dream/consolidation machine, and the sandbox device that runs it.
- The three-lane router, the always-on memory check, and the clause-streaming render were grafted into the sandbox's live conversation path on 2026-11-09 and measured (Section 4).
- The Gate — the resonance-check security construction built on this architecture — has a complete public record in this repo: sealed v3 package, v3/v4/v5 measured results, and the v6 loop in progress, including the failures. Read the failures first; they're the honest part.
- The ticker hardware, the disc, and the handheld are **design only**. Nobody has built one. The first person to build one should publish their measurements the way the software measurements are published here.

## 9. License posture

The core is open source on purpose. The one thing that never ships is a *grown* imprint bank: the release carries a fresh seed, because a person's grown self is theirs. Grow your own.

— Michael James Byrne Jr, 2026-11-09
