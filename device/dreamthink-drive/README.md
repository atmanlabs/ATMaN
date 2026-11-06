# Project ATMAN (JARVIS)

> **Personal Agent OS & Cognitive Companion**  
> An agentic operating system where the language model is a component, not the self.

---

## The Core Architectural Principle

**The language model is NOT the self.**  
The model is an interchangeable component used for interpretation, planning, natural language generation, hypothesis formulation, and tool selection.  
The **self** lives in the surrounding system — identity store, evidence-based memory, standing drives, capability permissions, execution history, operator relationships, and continuity across model substitutions.

---

## Architectural Highlights

- **4-Layer Self**:
  - **Layer A (Immutable Identity)**: Sealed core boundaries and principles (P1–P5) enforced by cryptographic digest.
  - **Layer B (Stable Character)**: Temperament and communication style modifiable only through verified operator review.
  - **Layer C (Learned Preferences)**: Habits, tool preferences, and workflows updated gradually with evidence provenance.
  - **Layer D (Temporary State)**: Volatile per-turn scratchpad discarded without harming core selfhood.
- **Evidence-Based Memory**:
  - Every durable memory carries source, timestamp, confidence, supporting evidence, and allowed behavioral influence.
  - Transparent belief explanation: *"I believe [X] because of [past interactions], but I may be wrong."*
- **Real Permission System**:
  - 6 explicit capability levels (Level 0 Observe $\rightarrow$ Level 5 Forbidden).
  - Consequential actions require operator confirmation; core alteration and secret leakage are strictly forbidden.
- **Continuous Awareness Without Surveillance**:
  - Fast local volatile sensor processing (active window, idle time, hardware telemetry, camera motion, audio energy).
  - Raw multimedia discarded immediately; only selective events meeting explicit criteria are retained.
- **Visible Failures & Epistemic Uncertainty**:
  - Claims tagged with explicit badges: `[OBSERVED]`, `[INFERRED]`, `[REMEMBERED]`, `[GUESSED]`, `[PROPOSED]`, `[COMPLETED]`, `[FAILED]`.
- **Durable Audit Trail**:
  - Immutable action receipts in `audit_receipts.jsonl`.
  - *"Why did you do that?"* query handler reconstructs the full causal chain from trigger to execution.
- **Autonomous Development Companion**:
  - Watches test runs, detects tracebacks, records Architecture Decision Records (ADRs), tracks tasks, and learns coding preferences.

---

## Quickstart

```bash
# 1. Verify crate integrity
python wake.py

# 2. Run the architectural directives test suite
python -m unittest test_architectural_directives.py -v

# 3. Run the flight instruments test suite
python test_cockpit.py

# 4. Start the local relay server
python relay.py
```

Access the Cockpit flight deck and chat interface at `http://127.0.0.1:<relay-port>`.

For full documentation and handoff details, see [`ATMAN_HANDOFF.md`](file:///C:/Users/Operator/Desktop/jarvis-scaffold-public/ATMAN_HANDOFF.md).
