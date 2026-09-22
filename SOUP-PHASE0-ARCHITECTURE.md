# SOUP Phase 0 — ATMAN Architecture Survey

**Machine target:** <machine> (`machineId` <machine-id>)  
**Surveyed from:** code under `C:\Users\<you>\Documents\atman-live\` (box mirror: `/workspace/atman-live`)  
**Date:** 2026-09-22 07:30 ET  
**Policy:** Read-only survey. No TSC / Judge / gate_policy / seal / PSC direct writes.

---

## Plain-language map (what talks to what)

ATMAN is **one brain, many mouths**. The brain is the Python **MindLoop** in `atman-live`. Everything else is a thin adapter that posts text (and optional context) into the brain and executes actions the Judge already approved.

1. **Human (operator)** talks via:
   - Relay chat UI / HTTP `POST http://127.0.0.1:18790/chat`
   - Desktop app (`desktop.py` → stdin pipe → `desktop_worker.py` → MindLoop)
   - Voice (STT in `voice.py`, CPU-only; GPU reserved for LLM)
   - Minecraft in-game chat (`jarvis_bot.js` → same relay `/chat`)
2. **Relay** (`relay.py`) owns one shared `MindLoop`, concurrency-guards via **Governor**, then runs **one full cycle** per message.
3. **MindLoop.run_cycle** stages (in order):
   - **Capture** — wrap raw text + source + optional Minecraft chat_context  
   - **Emotion** — weight/novelty (never decides)  
   - **WFC snapshot** — copy rolling short-term buffer; reload PSC from disk  
   - **Reason** — rule-based **or** local Ollama LLM (`config.yaml` `mind.backend: llm`)  
   - **Judge** — deterministic gate vs TSC + `gate_policy` + permission fence  
   - **Action** — dispatch only if Judge approved  
   - **Outcome / Memory** — Judge-gated PSC imprint; always append WFC; log significant_events
4. **Identity lives** in the **private soul file** (TSC) outside the public repo:  
   `..\atman-private\tsc.atman.private.json` (override via `JARVIS_CORE_PATH` / `EXO_CORE_PATH`).  
   Loaded only through `atman_core.TSC` as a frozen, write-refusing proxy. Principles/commands also merge sealed `gate_policy.json`.
5. **What is sealed:** SHA-256 manifest in `..\atman-private\stage1-seal.json` covers soul + `core.py`, `atman_core.py`, `gate_policy.json`, `crate.py`, `wake.py`, `seal.py`. `wake.py` verifies before trusting the crate. `seal.py` creates the first seal only with `--operator-confirm` and never overwrites.

OpenClaw (phone/gateway agent stack under `~\.openclaw`) is a **separate** local assistant path historically used on this PC; atman-live relay does **not** import OpenClaw. Cliff-rope handoff writes into `~\.openclaw\HANDOFF-RESUME.md` as a resume note only.

---

## 1. Reasoning loop

| Stage | Where | Role |
|-------|--------|------|
| Capture | `loop.py` `MindLoop.run_cycle` | Build cycle event from sensory/relay input |
| Emotion | `core.emotion_weigh` via loop | Score weight/novelty; never decides |
| WFC | `MindLoop.wfc` (`deque`, capacity from config) | Short-term rolling trace |
| Reason | `reason.reason` → `llm_reason` or `rule_based_reason` | Propose intent + action + imprint flag |
| Judge | `loop.evaluate_judge` (+ `core.judge` / reflect) | Approve/quarantine vs TSC + fence |
| Action | `MindLoop._dispatch_action` | Execute allowed action types only |
| Memory | PSC imprint + WFC append + `SignificantEventsLog` | Persist only Judge-approved imprints |

Governor (`governor.py`) can short-circuit **"calm down"** before Reason and caps concurrent spawns (max 5).

---

## 2. Memory systems

| Store | Path / location | Mutability |
|-------|-----------------|------------|
| **TSC** (True Self Core) | `atman-private\tsc.atman.private.json` via `atman_core.TSC` | **Immutable** at runtime; `ImmutableViolation` on write |
| **gate_policy** | `atman-live\gate_policy.json` | Sealed; merged into TSC view at load |
| **PSC** (Permanent Self Core) | `atman-live\psc.json` (`AuthenticatedPSC`) | Append-only / Judge-gated `imprint()` only |
| **WFC** | In-memory `deque` (default 50) | Ephemeral rolling; includes rejected traces |
| **significant_events** | `atman-live\significant_events.json` | Raw log for sleep consolidation |
| **drives** | `drives.py` `drive_manager` | Standing goals / initiative intensities |
| **skills** | skill repo (via relay `/skills`) | Judge-gated store |
| **EvolvingBrain** | `evolving_brain.py` | Knowledge / search learning helpers on top of PSC |

Sleep consolidation: `sleep.py` (SignificantEvents → weighted enduring material without rewriting TSC).

---

## 3. LLM backend(s)

From `config.yaml` (live fence config):

- `mind.backend: "llm"`
- `mind.ollama_model: "qwen2.5:3b"`
- `mind.ollama_endpoint: "http://127.0.0.1:11434"`
- `mind.ollama_timeout_s: 30.0`
- Vision: `moondream` (optional); Voice STT `base` int8 CPU; TTS Piper CPU

`reason.call_ollama`:

- Endpoint: `POST /api/generate`
- **`stream: false`** (fully buffered JSON thought)
- **`format: "json"`**
- Default model string in code fallback: `qwen2.5:7b-instruct-q4_K_M` (overridden by config to 3b)
- **No `keep_alive` field** in payload → Ollama server default residency applies
- On failure → falls through to rule-based path inside `llm_reason`

Extra Minecraft skill-resolution path (`minecraft_context.resolve_context`) may call **`/api/chat`** once (also `stream: false`, `num_predict: 110`) for non-trivial Minecraft phrasing — second model call on some Minecraft turns only.

Hardware note in bootstrap: **RTX 3050 6GB VRAM**; GPU reserved for LLM; voice on CPU.

---

## 4. Minecraft path

```
Player chat → jarvis_bot.js (Mineflayer)
           → HTTP POST 127.0.0.1:18790/chat  (Bearer token)
           → relay.py → MindLoop.run_cycle(source=minecraft, chat_context=…)
           → Judge-approved minecraft_action / skill / initiative
           → bot executes; completion POST /initiative/complete
```

Paper/Bukkit demo stream (optional): plugin → `127.0.0.1:18791` → `observer.py` → episode_segmenter → skills.

Canonical bot path (PC): `C:\Users\<you>\Documents\atman-minecraft\bot\jarvis_bot.js`  
Box scaffold mirror: `/workspace/atman-who-he-is/adapters/minecraft/bot/jarvis_bot.js`

---

## 5. Desktop app / worker

| Module | Role |
|--------|------|
| `desktop.py` | pywebview UI + tray; `PipeClient` to worker |
| `desktop_worker.py` | Allowlisted commands (`chat`, `sense`, `sleep`, voice record…); hosts MindLoop; **localhost-only** network fence |
| `build_desktop.py` | Packaging helper |
| `ui/` (scaffold) | `chat.html` etc. for relay UI |

Worker root on PC: `%USERPROFILE%\Documents\atman-live`.

---

## 6. wake / gate / seal / Judge

| File | Role |
|------|------|
| `wake.py` | One-shot crate verify + immutability / Judge smoke tests |
| `crate.py` | Hash snapshot + verify against seal |
| `seal.py` | Operator-only initial seal create (`--operator-confirm`); never reseals |
| `gate_policy.json` | Sealed command/principle fence merged into TSC |
| `loop.evaluate_judge` | Runtime Judge over proposed actions |
| `core.judge` / `reflect_against_tsc` | Lower-level identity contradiction checks |
| `guardian/` | Pre-imprint sneak sweep / policy docs |

---

## 7. Other interfaces

| Interface | Wiring |
|-----------|--------|
| Relay chat UI | `GET` static + `POST /chat` on :18790; Tailscale bind if present (historically `100.114.96.84:18790`) |
| Voice | `voice.py` + desktop record_start/stop; push-to-talk default |
| Cockpit tools | `cockpit.py` tools allowlisted in config |
| OpenClaw | Separate `~\.openclaw` agent/gateway; handoff file shared; **not** in MindLoop import graph |
| Overnight evolution | `overnight/overnight_evolution.py` posts curriculum through relay (memory-only) |

---

## Load-bearing modules (exact paths + one-line roles)

Paths relative to `C:\Users\<you>\Documents\atman-live\` unless noted.

| Path | Role |
|------|------|
| `loop.py` | MindLoop harness + evaluate_judge + AuthenticatedPSC + run_cycle |
| `reason.py` | Swappable reasoner: llm (`call_ollama`) vs rule-based |
| `relay.py` | HTTP bridge :18790; ATMAN entry for chat/events/skills/drives |
| `core.py` | Public ATMAN primitives (capture/emotion/judge/PSC base) |
| `atman_core.py` | Private TSC adapter; freezes soul + merges gate_policy |
| `config.yaml` | Backend model, timeouts, permission fence |
| `config.py` | Config loader |
| `gate_policy.json` | Sealed identity attack commands / principles |
| `crate.py` | Integrity digest of sealed files + soul |
| `wake.py` | Boot-time crate + Judge battery |
| `seal.py` | Operator-initiated first seal writer |
| `governor.py` | Concurrency cap + calm-down kill switch |
| `desktop_worker.py` | Desktop backend MindLoop host (piped) |
| `desktop.py` | Desktop UI wrapper |
| `voice.py` | Local STT/TTS (CPU) |
| `senses.py` | Camera / vision eye |
| `cockpit.py` | Telemetry + allowlisted tools |
| `drives.py` | Standing drives / initiative |
| `significant_events.py` | Event log for sleep |
| `sleep.py` | Consolidation pass |
| `sweep.py` / `guardian/` | Trust / sneak-sweep |
| `minecraft_chat.py` / `minecraft_context.py` | Minecraft language + skill resolve |
| `observer.py` / `episode_segmenter.py` / `skills.py` | Passive learning pipeline |
| `evolving_brain.py` | Knowledge imprint helpers |
| `operator_auth.py` | Operator auth helpers |
| `..\atman-private\tsc.atman.private.json` | **Identity soul (sealed, immutable)** |
| `..\atman-private\stage1-seal.json` | Seal manifest |
| `..\atman-minecraft\bot\jarvis_bot.js` | Minecraft Mineflayer adapter → relay |
| `..\atman-minecraft\server\` | Local Paper server tree |

---

## Survey notes / limits

- Phase 0 content above is **from reading code**, not guessing runtime process tables.
- Live process / Ollama residency / per-turn ms numbers belong in Phase 1 on the PC.
- Subagent that wrote this report **did not** have `ListMachines` / `Shell(machineId=…)`; PC disk write of this file requires parent `CopyFromBox`.
