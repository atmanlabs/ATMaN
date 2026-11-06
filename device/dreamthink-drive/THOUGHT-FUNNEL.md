# Thought Funnel — experimental, subordinate, non-authoritative

## Architecture and boundary
Layer 1 reads a bounded tail of existing runtime/dream-cloud/dreams.jsonl. It accepts source IDs, gists and optional typed relations; narratives, instructions and tool proposals are not executed. Known rejected/cancelled states and quarantined sleep batches are excluded. Raw dream gists were produced by the pre-existing dream system and may have LLM origins. The funnel's transformation itself makes no model calls.

Layer 2 is thought_funnel.py: deterministic graph assembly, shared-concept filtering, typed path composition, reinforcement, conflict suppression and fixed-point convergence. Explicit relations use subject, predicate, object and optional negative fields. Supported transitive predicates are requires, precedes and is_a; incompatible is a conflict relation. These are declared graph semantics, not universal interpretations of free text. Prose uses only lexical associated edges. It cannot infer arbitrary causality or resolve subtle linguistic negation.

Layer 3 is optional literal template rendering, disabled by default. There is no model renderer in this version.

DreamCloud.start launches an independent daemon worker with only a directory, stop event and activity timestamp callback. It receives no MindLoop/PSC/TSC/Judge/tool object. It never calls the Judge, imprints, dispatches tools, changes permissions, or feeds chat. Thoughts have authority=none, memory_eligible=false and core_compatibility=not_adjudicated. A future consumer must use the existing Judge/memory gates; this module grants no exception.

## Promotion criteria
All must pass: at least two source IDs; a structurally new relationship (or repeated cross-state lexical association); two consecutive stable graph passes; heuristic confidence >= 0.7; no known explicit contradiction; path and generation limits; not a duplicate. Confidence is 0.95 ** path length for typed relations and 0.8 for lexical associations. It is not calibrated truth probability. Relevance reports source support and recurrence; goal/operator relevance and protected-core semantic compatibility are deliberately not guessed.

Contradictory compositions are suppressed, not resolved by voting. Telemetry includes activated source IDs, relationship/source mappings, negative evidence, reinforcement/suppression events, convergence populations, failed checks, source excerpts and paths, and promotion criteria. Classification is structural NEW / REFINEMENT / REINFORCEMENT / DUPLICATE; contradictory candidates are separately logged and withheld.

## Operation and bounds
Default: one scan every 60 seconds, only after 30 seconds without chat activity. CPU-only; no GPU/model access. At most 48 input states from a 512 KiB tail; 96 candidates; depth 3; generation 2; 12,000 operations; 40ms thread-CPU / 100ms wall synthesis budget. Limits have hard clamps. Chat activity cancels between algorithm steps; no chat lock is acquired. File parsing/serialization is bounded separately and not included in the synthesis timer. Windows CPU timer can report 0ms for sub-tick work.

Temporary workspace: last 20 thoughts, 30-minute expiry, capped at 2 MiB. Previous-thought reuse defaults false; if enabled it requires original evidence still present and is generation/path bounded. It cannot count itself as an independent source. A 512-entry fingerprint index suppresses rediscovery across workspace expiry/restarts; sufficiently old evicted fingerprints can recur. Trace journal rotates around 2 MiB, retaining one previous file; one record can temporarily exceed the rotation threshold. Full traces for currently retained thoughts are embedded in the workspace.

runtime/dream-cloud/thought-funnel/config.json is reread each cycle. enabled=false stops this worker's synthesis and clears its temporary workspace on the next scan. The parent dream-cloud config enabled=false also disables it. No configuration writes occur automatically. New owner configuration is bounded, never permission-granting.

## Inspect / debug
Run:
python thought_funnel.py --watch
This opens a read-only Windows viewer refreshed every two seconds. It shows latest telemetry and the current thought workspace, including discarded funnels. It does not run inference or initiate cycles.

python thought_funnel.py --once
Explicitly runs one bounded step against the real dream directory, respecting idle and enabled settings. Do not use concurrent manual writers while the background worker is active.

Files under runtime/dream-cloud/thought-funnel:
- latest.json: last cycle / disabled / error status
- workspace.json: temporary structures and complete provenance
- trace.jsonl and trace.previous.jsonl: bounded engineering telemetry
- seen.json: bounded fingerprint timestamps, not memory
- config.json: owner-editable limits and rendering toggle

## Validation and limitations
17 focused unit tests cover no-model synthesis, label-independent relation composition, provenance, contradictions, malformed states, no-coherence discard, duplicate suppression across workspace reset, bounded recursion/resources, preemption, rendering independence, quarantine and core/Judge dependency boundaries.

Complete unittest discovery was run before and after in an isolated copy with synthetic identity, no network, blocked live files and restricted subprocess execution. Before: 174 tests, 5 failures, 61 errors. After: 191 tests, same 5 failures and 61 errors. All new tests passed; no additional failing test IDs. This is not a green full regression run. Live-model/audio/network tests and some historical environment expectations are not validated by this isolated run.

The controlled fixture derived archive_review requires workspace_access from archive_review requires file_inventory plus file_inventory requires workspace_access, with networking blocked and rendering disabled. The generic rule was also tested on unrelated labels and multiple relation types. The expected conclusion was not a stored input. This validates bounded graph inference, not consciousness, broad reasoning, useful transfer, or calibrated belief. Lexical associations in live prose can be weak; they stay temporary and non-authoritative.

## Rollback
Set this feature's enabled=false. To remove integration, restore only the three-line ThoughtFunnel startup hook in dream_cloud.py and reload the relay using its existing supervisor. Do not restore stale whole files over subsequent work. No PSC cleanup or core change is needed because the funnel has no memory-write path.
