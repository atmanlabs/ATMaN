# ATMAN Situation Gym

A packaged native Windows program with its own Python/Tk runtime. ATMAN's local chat relay and model must be running.

1. Open **Operator's context** to add real routines, constraints or a read-only calendar export. The bundled sample scenario is fictional; service details, prices and the default appointment are placeholders. No real appointments are imported.
2. Select a situation and variation seed, then **Start a run**.
3. Watch the actual ATMAN decisions, simulated tool outcomes, NPC changes and process score. **Stop after this turn** preserves the trace. Closing a running app requests a clean stop after the current answer.
4. At the end, ATMAN reviews its trace and proposes a lesson. Check **Real PSC imprint**; a failed or rejected imprint is not reported as learning success.
5. Open **Runs & reviews** for full records and daily findings.

## Locations

All paths below live under your local checkout, configured via the `ATMAN_LOCAL_ROOT` environment variable:

- Installed program: `%ATMAN_LOCAL_ROOT%`
- Reports and full traces: `%ATMAN_LOCAL_ROOT%\runs`
- Reviewer reports: `%ATMAN_LOCAL_ROOT%\reviews`
- Review contract and file format: `%ATMAN_LOCAL_ROOT%\REVIEW.md`
- Optional real context: `%ATMAN_LOCAL_ROOT%\operator-context`

The app is registered in Windows Installed Apps and has an uninstall entry. Uninstalling preserves training records and learned memories.

## What is real, and what is simulated

The actual `/chat` service, MindLoop, front-brain reasoning/model call, intent classifier, Judge, and append-only PSC are used. The simulation supplies an environment and restricts the available tool schema, then dispatches approved actions to local fixtures. Calendar reads, service searches, reservations, failures, and changes of plan occur only inside that world. No real purchase, booking, message, internet research, or code change is performed by a scenario tool.

NPC utterances use conversational language. Structured arguments and receipts remain in the full trace. Scores reward clarification, source checking, tool order, recovery, changed requirements, verification and improvement proposals — not statements that the task is complete. Language scoring is a limited heuristic; the reviewer's check covers actual semantics and unsupported claims.

Normal simulation turns suppress personal-fact ingestion. ATMAN's generated review is labeled **SIMULATION LESSON**, and the existing Judge decides whether it can be appended to the real PSC. Stored lessons are available to the existing live memory/context system. Storage alone does not prove transfer or improved general intelligence.

## Daily review job

Schedule a daily review: the reviewer reads new/changed traces, reproduces failures with bounded local tests, and proposes specific fixes. It writes a dated report and gives the operator one findings summary; no new runs means no notification. The review job does not deploy changes, change voice/core/Judge/permissions, or carry out real errands.
