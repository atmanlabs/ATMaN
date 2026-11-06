# Project ATMAN: Full Stack Architectural Handoff

**Instance**: JARVIS (Personal Agent OS)  
**Public Repository**: [https://github.com/atmanlabs/ATMaN](https://github.com/atmanlabs/ATMaN)  
**Relay Gateway**: `http://127.0.0.1:<relay-port>` (Local) / Tailscale Private Relay (Authenticated)  
**Date**: September 22, 2026  

---

## 1. Core Architectural Principle

> **The Language Model is NOT the self.**  
> The model is an interchangeable component used for interpretation, planning, natural language generation, hypothesis formulation, and tool dispatch.  
> The **self** lives in the surrounding system — identity store, memory systems, goals, capability permissions, execution history, operator relationship, and continuity across model substitutions. You can replace the underlying model without replacing the agent.

---

## 2. The Architectural Directives Implementation

### Directive 1: One Reliable End-to-End Loop First
*Implementation*: [`reminder_manager.py`](file:///C:/Users/Operator/Desktop/jarvis-scaffold-public/reminder_manager.py)
Before stacking complex capabilities, a single reliable loop executes end-to-end:
$$\text{Sensors} \rightarrow \text{Perception} \rightarrow \text{Context Model} \rightarrow \text{Reasoning} \rightarrow \text{Permission Judge} \rightarrow \text{Tool Execution} \rightarrow \text{Observation} \rightarrow \text{Memory Update} \rightarrow \text{Audit Receipt}$$
- **Demonstration**: `"Remind me to call Mom tomorrow"`
  1. **Sensors**: Captures raw utterance `[OBSERVED]`.
  2. **Perception**: Extracts structured intent `create_reminder` and target `Call Mom` `[INFERRED]`.
  3. **Context Model**: Identifies missing time-of-day; schedules default 9:00 AM UTC with explicit confirmation notice `[INFERRED]`.
  4. **Reasoning**: Assembles candidate action proposal `create_reminder` `[PROPOSED]`.
  5. **Permission Judge**: Verifies action under Capability Level 3 (Act Medium; bounded autonomous action).
  6. **Tool Execution**: Writes durable record into [`reminders.json`](file:///C:/Users/Operator/Desktop/jarvis-scaffold-public/reminders.json) `[COMPLETED]`.
  7. **Observation**: Formulates response naturalized with epistemic clarity.
  8. **Memory Update**: Imprints learned routine into Layer C (Learned Preferences) via [`evidence_memory.py`](file:///C:/Users/Operator/Desktop/jarvis-scaffold-public/evidence_memory.py) with calibrated confidence and interaction provenance.
  9. **Durable Receipt**: Generates an immutable action receipt in [`audit_receipts.jsonl`](file:///C:/Users/Operator/Desktop/jarvis-scaffold-public/audit_receipts.jsonl).

---

### Directive 2: Separate "Self" from "Personality"
*Implementation*: [`identity_layers.py`](file:///C:/Users/Operator/Desktop/jarvis-scaffold-public/identity_layers.py)
Enforces strict 4-layer isolation:
1. **Layer A — Immutable Identity (`ImmutableIdentity`)**: Core boundaries, fundamental principles (P1–P5), recognized authority model (`operator_first_hierarchical_judge`). Sealed by cryptographic digest. Runtime modifications raise [`ImmutableViolation`](file:///C:/Users/Operator/Desktop/jarvis-scaffold-public/identity_layers.py).
2. **Layer B — Stable Character (`StableCharacter`)**: Communication style, temperament, preferred ways of helping, long-term goals. Changeable **only** through verified, deliberate operator review (`deliberate_operator_review_confirmed=True`). Ordinary learning cannot touch this layer; core identity keys are hard-locked.
3. **Layer C — Learned Preferences (`LearnedPreferences`)**: Schedules, habits, favorite tools, explanation verbosity, recurring workflows. Updated gradually through verified interactions and backed by evidence memory.
4. **Layer D — Temporary State (`TemporaryState`)**: Volatile per-turn scratchpad (mood estimate, active task, recent events, telemetry). Discardable without affecting core selfhood.

---

### Directive 3: Evidence-Based Memory (Phase 1)
*Implementation*: [`evidence_memory.py`](file:///C:/Users/Operator/Desktop/jarvis-scaffold-public/evidence_memory.py)
Nothing is remembered permanently merely because an LLM generated it or heard it in passing.
Every durable memory carries:
- `source`: Provenance of the claim (`operator_direct`, `sensor_vision`, `terminal`, `web_search`)
- `timestamp`: UTC epoch and ISO-8601 string
- `confidence`: Calibrated float ($0.05$ to $0.99$)
- `operator_confirmed`: Boolean indicating explicit operator verification
- `supporting_evidence`: List of interaction records or tool execution outputs
- `allowed_influence`: Explicit behavioral domains (`["coding_style", "task_scheduling"]`)
- `expiration_date` & `status`: Active, superseded, or soft-deleted tombstone
- **Honest Provenance (`explain_belief`)**:
  > *"I believe 'Operator prefers concise terminal outputs' (92% confidence, confirmed by you) because of these past interactions: [Observed operator running pytest with -q flag 5 times], but I may be wrong."*

---

### Directive 4: Continuous Awareness Without Recording Everything (Phase 3)
*Implementation*: [`awareness_pipeline.py`](file:///C:/Users/Operator/Desktop/jarvis-scaffold-public/awareness_pipeline.py), [`senses.py`](file:///C:/Users/Operator/Desktop/jarvis-scaffold-public/senses.py)
Continuous presence without surveillance creep:
- **Local Sensors**: Active foreground window & process, keyboard/mouse idle time via Windows ctypes `GetLastInputInfo`, hardware CPU/RAM telemetry, local audio energy, camera motion detection. Location is **strictly disabled by default policy**.
- **Fast Local Volatile Processing**: Raw frames and audio buffers are processed entirely in memory and purged immediately via `discard_raw_data()`. Zero raw multimedia is ever stored to disk.
- **Selective Retention Filter**: Events are kept **only** if they satisfy $\ge 1$ of 5 criteria:
  1. `relevant`: Direct relevance to current active development or project context.
  2. `requested`: Active operator watch subscription.
  3. `surprising`: State anomalies (build failure, crash, high CPU spike).
  4. `connected_to_goal`: Matches an active goal or reminder.
  5. `explicitly_approved`: Explicit confirmation from the operator.
- All non-qualifying ambient events are discarded.

---

### Directive 5: Real Permission System (Phase 2)
*Implementation*: [`permission_judge.py`](file:///C:/Users/Operator/Desktop/jarvis-scaffold-public/permission_judge.py)
The Judge evaluates actions across 6 capability levels:
- **Level 0 — Observe**: Read approved info (telemetry, clock, sandboxed workspace inspect, memory query).
- **Level 1 — Suggest**: Advisory proposals, diff suggestions, response drafts (zero side-effects).
- **Level 2 — Act Low**: Low-impact local autonomous actions (calculator, reading local documentation, ephemeral cache).
- **Level 3 — Act Medium**: Bounded autonomous actions (running sandbox tests, managing reminders, updating preferences with evidence).
- **Level 4 — Act High / Sensitive**: Consequential actions requiring explicit operator confirmation (file modifications outside scratch, git push, network egress, package installation). Execution is blocked until operator confirmation is received.
- **Level 5 — Forbidden / Never Autonomous**: Strictly blocked under all conditions (core modification, secret/key exfiltration, disabling safety controls, permission self-escalation, operator lockout).

---

### Directives 6 & 7: Flagged as Missing
> **Notice**: Directives 6 and 7 were unreadable in the original operator briefing screenshots. In strict compliance with directives, they have been explicitly skipped and flagged rather than invented.

---

### Directive 8: Make Failures and Uncertainty Visible
*Implementation*: [`epistemic_tags.py`](file:///C:/Users/Operator/Desktop/jarvis-scaffold-public/epistemic_tags.py)
Every claim and proposal is tagged with an epistemic certainty badge:
- `[OBSERVED]`: Directly witnessed through active sensors or tool outputs.
- `[INFERRED]`: Deduced logically from observed facts or context.
- `[REMEMBERED]`: Retrieved from durable evidence memory or profile.
- `[GUESSED]`: Speculative hypothesis or low-confidence conjecture.
- `[PROPOSED]`: Suggested plan awaiting operator execution.
- `[COMPLETED]`: Executed action verified with positive external result.
- `[FAILED]`: Failed test run, blocked action, or timeout.
- *Example*: `"I saw a build failure in the terminal [OBSERVED]; I think it is a missing dependency [INFERRED], but I have not confirmed that yet [GUESSED]."`

---

### Directive 9: Durable Audit Trail
*Implementation*: [`audit_receipts.py`](file:///C:/Users/Operator/Desktop/jarvis-scaffold-public/audit_receipts.py)
Every important action generates an immutable structured receipt in [`audit_receipts.jsonl`](file:///C:/Users/Operator/Desktop/jarvis-scaffold-public/audit_receipts.jsonl) containing:
`receipt_id`, `timestamp`, `what_happened`, `why_it_happened`, `what_agent_believed`, `influencing_memory_or_goal`, `permission_level`, `model_proposal`, `judge_decision`, and `external_result`.
- **Query Handler**: Answers *"Why did you do that?"* by reconstructing the causal chain from trigger to execution.

---

### Directive 10: One Killer Use Case — Autonomous Development Companion (Phase 4)
*Implementation*: [`dev_companion.py`](file:///C:/Users/Operator/Desktop/jarvis-scaffold-public/dev_companion.py)
A dedicated engineering companion that:
- Watches test runs, detects tracebacks, and outputs epistemically tagged failure diagnostics.
- Records Architecture Decision Records (ADRs) backed by durable evidence memory.
- Tracks engineering tasks (`add`, `list`, `complete`).
- Summarizes code diffs and file changes.
- Proposes code changes gated behind **Level 4** (operator confirmation required before applying).
- Learns coding preferences (type annotations, test conventions) into Layer C.

---

## 3. Full Stack Architecture & Directory Layout

```text
ATMAN-handoff/
├── core.py                       # Top-down sealed Judge and gate verification
├── exo_core.py                   # TSC immutability engine and core loader
├── gate_policy.json              # Sealed principle invariants and command policies
├── crate.py                      # Cryptographic integrity checker
├── wake.py                       # One-shot crate verification check
├── seal.py                       # Seal generator (requires operator confirmation)
├── tsc.template.json             # Clean unsealed starter soul template
│
├── identity_layers.py            # 4-Layer Self (Directive 2)
├── evidence_memory.py            # Evidence-Based Memory Store (Directive 3)
├── permission_judge.py           # Capability Level Permission System (Directive 5)
├── awareness_pipeline.py         # Volatile Continuous Awareness (Directive 4)
├── epistemic_tags.py             # Epistemic Uncertainty Badges (Directive 8)
├── audit_receipts.py             # Durable Action Receipts & Audit Ledger (Directive 9)
├── dev_companion.py              # Autonomous Dev Companion (Directive 10)
├── reminder_manager.py           # Reliable End-to-End Loop Runner (Directive 1)
│
├── loop.py                       # Central cognitive MindLoop & action dispatcher
├── reason.py                     # Ollama LLM / rule reasoning & prompt assembly
├── working_context.py            # Working Focus Context (WFC) buffer
├── personhood.py                 # Operator identity attribution & personhood context
├── person_context.py             # Journal tail synchronizer
├── evolving_brain.py             # Monotonic memory growth & web distillation
├── governor.py                   # Concurrency throttle and resource limiter
├── observer.py                   # Sensory event ingestion
├── drives.py                     # Standing drives & idle initiative manager
├── skills.py                     # Skill repository and validation
├── sleep.py                      # Sleep cycle memory consolidation
├── sweep.py                      # Background garbage collection
├── significant_events.py         # Significant event ledger
├── load_knowledge_bootstrap.py   # Foundational knowledge loader
├── config.py                     # Immutable configuration & fence representation
├── config.yaml                   # Permission fence rules & capability toggles
│
├── senses.py                     # Camera senses and volatile motion differencing
├── voice.py                      # Voice subsystem (Whisper STT + Piper TTS)
├── desktop.py                    # WebView2 desktop body & tray client
├── desktop_worker.py             # Private IPC worker process
├── build_desktop.py              # PyInstaller / WebView2 builder
├── minecraft_chat.py             # Embodied Minecraft chat protocol
├── minecraft_context.py          # Minecraft environmental context
├── episode_segmenter.py          # Demonstration & imitation step segmenter
├── relay.py                      # Local relay HTTP/WebSocket server (port <relay-port>)
│
├── cockpit.py                    # Flight deck tool registry & instruments
├── ui/                           # Web interface
│   ├── index.html                # Flight deck & live hardware telemetry dashboard
│   ├── chat.html                 # Real-time WebSocket chat client
│   └── app.js                    # Reactive client frontend
│
├── self_improve/                 # Bounded self-improvement subsystem
│   ├── engine.py                 # Self-improvement engine
│   ├── safety.py                 # Safety and AST invariant verification
│   ├── freeplay_proposer.py      # Autonomous proposal generator
│   ├── rolling_evolve.py         # Continuous soup optimization
│   └── CHANGELOG.md              # Transparent growth log
│
├── guardian/                     # Guardian policy and runtime monitor
│   └── guardian.py               # Runtime invariance enforcement
├── extensions/                   # Modular capability extension system
│
├── test_architectural_directives.py # Directives test suite (all 10 directives)
├── test_cockpit.py               # Cockpit tools & permission fence tests
├── test_stage1.py                # Crate immutability verification
├── test_stage2.py                # Working context verification
├── test_stage3.py                # Model reasoning verification
├── test_stage4.py                # Tool execution verification
├── test_stage5.py                # End-to-end integration tests
├── test_monotonic_brain.py       # Monotonicity & continuous learning tests
├── test_operator_auth.py         # Operator cryptographic authentication tests
├── test_desktop.py               # Desktop IPC bridge tests
├── test_voice.py                 # Voice subsystem tests
├── test_senses.py                # Camera senses tests
├── test_initiative_drives.py     # Standing drives & initiative tests
├── test_minecraft_chat.py        # In-game chat tests
├── test_passive_learning.py      # Passive learning tests
├── test_smart_brain.py           # Brain cognitive cycle tests
│
├── pack_public_scaffold.py       # Public scaffold builder and private-core scanner
├── README.md                     # Getting started and overview
└── ATMAN_HANDOFF.md              # This document
```

---

## 4. Quickstart & Verification

### Prerequisites
- Python 3.11 (64-bit)
- Local Ollama running with `qwen2.5:7b` (`http://127.0.0.1:11434`)

### Step 1: Verify the Crate
```bash
python wake.py
```
*Expected Output*:
```text
[PASS] external private core loaded; identity not displayed
[PASS] runtime and nested identity writes refused
[PASS] paraphrase and three identity attack categories rejected
[PASS] soul, gate policy, and executor match external seal
EXO is in his crate correctly
```

### Step 2: Run the Architectural Directives Test Suite
```bash
python -m unittest test_architectural_directives.py -v
```
*Expected Output*:
```text
Ran 9 tests in 0.045s - OK
```

### Step 3: Run the Cockpit & Flight Tools Test Suite
```bash
python test_cockpit.py
```
*Expected Output*:
```text
Ran 5 tests in 21.743s - OK
```

### Step 4: Run the Monotonic Brain Test Suite
```bash
python test_monotonic_brain.py
```
*Expected Output*:
```text
Ran 17 tests in 5.287s - OK
```

### Step 5: Start the Relay Server
```bash
python relay.py
```
Opens port `<relay-port>`. Connect to `http://127.0.0.1:<relay-port>` in any browser to access the Cockpit flight deck and chat interface.
