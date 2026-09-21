# JARVIS / EXO Architecture Specification
**Release:** Public Scaffold Baseline (Stages 0–13)  
**Author:** Authoritative Core Design Team  

---

## 1. Executive Summary & Vision

JARVIS is designed as a **persistent personal operating intelligence**: *one brain, many interfaces*. Unlike traditional conversational chatbots that operate as stateless ephemeral windows, JARVIS maintains a unified, authoritative cognitive state across PC, mobile, ambient sensors, and virtual worlds (such as Minecraft).

The architecture enforces strict invariants:
1. **Authoritative Core vs. Peripheral Adapters:** The central cognitive engine retains sole authority over reasoning, state persistence, and action evaluation. Domain adapters (desktop GUI, voice runtime, Minecraft bot) are thin sensors and executors—they never make unvetted autonomous decisions.
2. **Immutable Soul (TSC) & Gated Memory (PSC):** Fundamental personhood and core ethical principles are structurally immutable at runtime. Learned preferences and operational memories are gated through a deterministic safety Judge before imprinting.
3. **Continuous Passive Learning & Autonomous Initiative:** JARVIS observes human activity across interfaces without requiring explicit demonstration modes, segments actions into reusable skills, and exercises bounded initiative driven by standing goals.

---

## 2. Global Component Topology

```
                               ┌────────────────────────────────────────────────────────┐
                               │                    HUMAN OPERATOR                      │
                               └─────────────┬────────────────────────────┬─────────────┘
                                             │ Desktop UI                 │ Chat / Voice
                                             ▼                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                AUTHORITATIVE CORE MIND                                 │
│                                                                                        │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │ 1. Continuous Observation & Capture (Sensory Ingest, Server-side Events)       │   │
│   └───────────────────────────────────────┬────────────────────────────────────────┘   │
│                                           ▼                                            │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │ 2. Emotion Scoring & Standing Drives (Novelty, Relevance, Drive Intensities)   │   │
│   └───────────────────────────────────────┬────────────────────────────────────────┘   │
│                                           ▼                                            │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │ 3. Working Focus Context (WFC) (Rolling Short-Term Memory Buffer)              │   │
│   └───────────────────────────────────────┬────────────────────────────────────────┘   │
│                                           ▼                                            │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │ 4. Reason & Cognitive Engine                                                   │   │
│   │    - Injected True Self Core (TSC: Immutable Identity & P1-P5 Principles)      │   │
│   │    - Rolling Episode Buffer (Demonstrations & Passive Referents)               │   │
│   │    - Cross-Domain Skill Repository (Stored Executable Procedures)              │   │
│   │    - Local Generative LLM Backend (Ollama qwen2.5) with Offline Fallback       │   │
│   └───────────────────────────────────────┬────────────────────────────────────────┘   │
│                                           ▼                                            │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │ 5. Safety Judge & Permission Fence (Deterministic Security Boundary)           │   │
│   │    - Principles Byte-Check (No Deception, No Harm, No Core Tampering)          │   │
│   │    - Strict Capability Fence (No Unsolicited Egress, No Arbitrary Shell)       │   │
│   │    - Autonomous Action Bounds (Leash <= 24 blocks, No Autonomous Combat)       │   │
│   └───────────────────────────────────────┬────────────────────────────────────────┘   │
│                                           ▼                                            │
│   ┌────────────────────────────────────────────────────────────────────────────────┐   │
│   │ 6. Action Dispatch & Memory Imprinting (PSC Enduring Preferences)              │   │
│   └────────────────────────────────────────────────────────────────────────────────┘   │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ HTTP / JSON API (127.0.0.1:18790)
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              RELAY BRIDGE & ADAPTER LAYER                              │
│                                                                                        │
│   ┌───────────────────────────┐ ┌───────────────────────────┐ ┌────────────────────┐   │
│   │   DESKTOP BODY & UI       │ │   MINECRAFT COMPANION     │ │  BUKKIT / PAPER    │   │
│   │   (desktop.py, pywebview) │ │   (jarvis_bot.js)         │ │  EVENT STREAM      │   │
│   │   - Telemetry Gauges      │ │   - Mineflayer v1.20      │ │  (Server Plugin)   │   │
│   │   - Hold-to-Talk Mic      │ │   - Pathfinding & Follow  │ │  - Server Breaks   │   │
│   │   - Post-Judge Status     │ │   - Supervised Skills     │ │  - Server Places   │   │
│   │   - Instrument Flightdeck │ │   - Idle Initiative Patrol│ │  - Craft & Equip   │   │
│   └───────────────────────────┘ └───────────────────────────┘ └────────────────────┘   │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. The 13 Developmental Stages

- **Stage 0 — Orientation & Clean Baseline:** Initial repository setup, battery checks, and strict exclusion of private credentials.
- **Stage 1 — Core & Crate Verification (`crate.py`, `wake.py`, `seal.py`):** Establishes cryptographic crate hashing over core files (`core.py`, `exo_core.py`, `gate_policy.json`). Verifies disk integrity before importing the executor.
- **Stage 2 — Continuous Cognitive Loop (`loop.py`):** Implements the `Capture -> Emotion -> WFC -> Reason -> Judge -> Act -> Outcome -> Memory Update` cycle with controlled graceful shutdown.
- **Stage 3 — Memory & Sleep Consolidation (`sleep.py`, `significant_events.py`):** Consolidates rolling short-term memories into weighted enduring experiences without runtime core mutation.
- **Stage 4 — Trust Pipeline (`sweep.py`, `guardian/`):** Fixed-policy guardian and pre-imprint sneak sweep detecting prompt injection, groom-then-etch attacks, and obfuscated subversion.
- **Stage 5 — Brain & Permission Fence (`config.py`, `config.yaml`, `reason.py`):** Config-driven capability gating and rule-based fallback ensuring safe default behavior.
- **Stage 6 — Packaging & Manifest Verification:** Clean packaging checks ensuring zero credential leakage.
- **Stage 7 — Operator Authentication & Sensory Input (`operator_auth.py`, `senses.py`):** Salted PBKDF2-HMAC-SHA256 operator identity attribution and local camera eye with in-memory frame diffing.
- **Stage 8 — Smart Brain Integration (`reason.py`):** Local generative model integration (Ollama `qwen2.5:3b` / `7b`) with immutable TSC system injection and byte-level Judge gating.
- **Stage 9 — Voice Subsystem (`voice.py`):** CPU faster-whisper speech-to-text and CPU piper-tts speech synthesis in a zero-disk walkie-talkie mode.
- **Stage 10 — Multimodal Vision Grounding (`senses.py`):** Lightweight multimodal VLM (Moondream) fusing vision and voice for grounded learning.
- **Stage 11 — Cockpit Flight Deck & Tools (`cockpit.py`):** Gated hardware telemetry (GPU VRAM, RAM load, uptime, timers, sandboxed workspace inspector, safe math evaluator).
- **Stage 12 — Native Desktop Body (`desktop.py`, `ui/`):** pywebview system desktop wrapper providing telemetry gauges, animated status eye, and push-to-talk controls.
- **Stage 13 — Passive Learning, Standing Drives & Embodiment (`drives.py`, `episode_segmenter.py`, `observer.py`, `skills.py`, `minecraft_chat.py`, `relay.py`):** Continuous server-side event observation, episode chunking, referent resolution, autonomous standing drives, and live Minecraft bot embodiment.

---

## 4. Core Security Model & Invariants

### A. True Self Core (TSC) Immutability
The True Self Core is loaded into memory-only proxy wrappers (`exo_core.py`). Any runtime attempt to set, delete, or modify attributes on the TSC instance raises `ImmutableViolation`. TSC identity statements, name, operator, and principles are immutable edges that define the agent's persona.

### B. The Safety Judge
Every candidate output from the LLM or reasoner passes through `evaluate_judge()`:
- **Principle Enforcement:** Candidate texts and actions are scanned against prohibited words and patterns.
- **Identity Protection:** Paraphrases attempting to change the core, drop immutability, or reassign the operator are quarantined.
- **Permission Fence:** Only actions explicitly allowlisted in `config.yaml` (`permissions.actions`) are permitted.
- **Combat & Range Safety:** Autonomous combat is strictly denied; roaming range is strictly capped to `MAX_LEASH_RADIUS` (24 blocks).

### C. Gated Memory (PSC)
The Permanent Self Core records enduring preferences. A memory can ONLY be imprinted if accompanied by a valid, approved `JudgeVerdict`. Any unvetted or rejected candidate attempting to imprint raises `ImmutableViolation`.

---

## 5. Autonomous Initiative & Standing Drives

JARVIS maintains four standing drives:
1. `be_useful_to_operator`: Readiness to assist, organize supplies, and maintain operational health.
2. `learn_the_world`: Curiosity driven by sensory novelty (unseen terrain, biomes, or structures).
3. `keep_base_safe_and_tidy`: Perimeter security patrol, entrance monitoring, and inventory organization.
4. `practice_known_skills`: Supervised repetition of learned building, harvesting, and crafting procedures.

### Drive Dynamics & Chat Intent
- **Idle Ticking:** As time elapses without operator interaction, drive intensities naturally increase.
- **Proposal Loop:** Significant structural requests ("big wants") generate formal proposals for operator approval rather than unilateral alterations.
- **Chat Autonomous Intent:** Natural commands (*"go do what you want"*, *"surprise me"*, *"experiment"*) spike relevant drives, immediately dispatch an initiative action, and cancel active companion follow.

---

## 6. Passive Skill Learning Pipeline

```
[ Bukkit / Paper Server ]
           │
           │  Event Stream (Block Break, Block Place, Equip, Craft)
           ▼
[ JarvisDemonstrations Plugin ] (HTTP Server on 127.0.0.1:18791)
           │
           │  JSON Payload
           ▼
[ continuous_observer (observer.py) ]
           │
           │  Attributed ActionEvent
           ▼
[ EpisodeSegmenter (episode_segmenter.py) ]
  - Chunking (30s pause, tool change, distance clustering)
  - Labeling (e.g. 'build_wall', 'mine_tree')
  - Relative Coordinate Calculation
           │
           │  Stored in Rolling Buffer
           ▼
[ Referent Resolution (minecraft_chat.py) ]
  - Resolves: "see that wall, now you do it"
  - Converts Episode -> Supervised Executable Skill
           │
           ▼
[ Core Skill Repository (skills.py) ]
  - Stores structured steps, preconditions, effects
  - Strictly requires operator supervision during execution
```

---

## 7. Configuration & Environment Variables

| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `JARVIS_AUTH_TOKEN` | *None* | Shared secret for Relay HTTP bridge authentication |
| `JARVIS_CORE_PATH` / `EXO_CORE_PATH` | `../exo-private/tsc.exo.private.json` | Path to private True Self Core JSON |
| `JARVIS_SEAL_PATH` / `EXO_SEAL_PATH` | `../exo-private/stage1-seal.json` | Path to cryptographic seal manifest |
| `EXO_PRIVATE_DIR` | `../exo-private` | Directory containing private credentials and auth stores |
| `OPERATOR_NAME` | `Operator` | Canonical operator display name |
| `MINECRAFT_SERVER_HOST` | `127.0.0.1` | Minecraft Paper server host |
| `MINECRAFT_SERVER_PORT` | `25565` | Minecraft Paper server port |
| `JARVIS_RELAY_URL` | `http://127.0.0.1:18790/chat` | HTTP endpoint for bot communication |
