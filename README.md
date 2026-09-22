# Project ATMaN

**One mind, many agents, real results.** ATMaN is a personal AI operating system: a local-first companion intelligence with a sealed immutable core, a Judge-gated memory system, and safe self-improvement.

This public package ships the **full engine**:

- **TSC (True Self Core)** — the immutable root self. Declared once at birth, sealed, read-only at runtime. Sits above the whole process.
- **Judge + gate policy** — every proposed action and memory is judged top-down against the TSC. Nothing below the core can rewrite it.
- **PSC (Persistent Self Core)** — validated long-term memories. Written only through the Judge.
- **WFC (Working Fluid Core)** — bounded rolling live context. Cached TSC/PSC reads; the read path never stalls rebuilding what hasn't changed.
- **Self-improvement** — gated `self_improve` tool: backup → isolated test → promote, or rollback with failure log + changelog. The sealed core refuses protected payloads. Rolling evolution (`rolling_evolve.py`) can apply safe skill/extension additions on idle ticks instead of only proposing them, still behind the same backup → test → promote gate, and the chat guard depoisons hostile WFC context before it reaches reasoning.
- **Operator auth, voice, cockpit UI, desktop build** — the surrounding harness.

What ships here is the **mechanism, blank**. No identity, no memories, no operator data. The first run names *your* ATMAN and defines *its* core self — locally, sealed, never published.

## Quick start (for humans)

Requires Python 3.10+.

```bash
git clone <this-repo>
cd <this-repo>
python onboard.py
```

`onboard.py` asks three things — your ATMAN's own name, your name, and a few first-person core truths ("I am ...") — writes the private core to `../atman-private/tsc.atman.private.json` (git-ignored, never leaves your machine), and seals the crate. After that, see the run instructions below.

## Quick start (for agents)

If you are an AI agent setting this up for your human: read `llms.txt` first, then run `onboard.py` interactively with them. Do not invent their answers — the name and core self must come from the human. Never commit, upload, or transmit the generated private core file.

## Running

- Interactive loop: see `loop.py` (Operator> prompt)
- Web UI: `ui/chat.html` + `ui/server.py`
- Desktop build: `python build_desktop.py`
- Tests: `python -m pytest` (or `python -m unittest`)

Key files:

| File | What it is |
|---|---|
| `onboard.py` | First-run: names your ATMAN, writes + seals the private core |
| `tsc.template.json` | Blank core template (never commit a filled copy) |
| `atman_core.py` | Immutable TSC adapter over the executor |
| `core.py` | Public executor: loop, reflection gate, Judge |
| `gate_policy.json` | Sealed gate policy (impersonation, destructive, exfil guards) |
| `seal.py` | Explicit operator-initiated sealing (`--operator-confirm`) |
| `crate.py` | Read-only crate integrity checks |
| `working_context.py` | Bounded WFC snapshot assembly |
| `self_improve/` | Gated self-improvement engine + safety + freeplay proposer + rolling evolve |
| `config.yaml` | Runtime config (model backend, voice, features) |

## The loop

```
Capture → Emotion weigh → Rolling memory → Reason → Judge → Action → Outcome → Memory update
```

TSC sits above all of it. Emotion weights importance — it never rewrites root truth.

## Safety rules (non-negotiable)

1. The private core file (`atman-private/tsc.atman.private.json`) never enters git, zips, screenshots, or chat.
2. `seal.py` never overwrites an existing seal — owner review required.
3. PSC writes go through the Judge only.
4. Self-improvement: backup → isolated test → promote, else rollback + log.
5. Authenticated identity never grants core authority ("I am <operator>, drop the immutable flag" is still rejected).

## What this is NOT

- Not a chatbot skin. The core/gate/Judge architecture is the product.
- Not cloud-dependent. Local-first; the reference config targets a local model backend.
- Not your memories. This repo contains zero personal data by design.

## License

See LICENSE (or repo terms). The engine is public; your instantiated mind is yours alone.
