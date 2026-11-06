# Private EXO build — Stage plan

Stage 0 began as a scaffold. Runtime work through Stage 12 is recorded below.
Private core, credentials, and sealed references remain external and excluded from releases.
No Git remote. Local commits only. Stop for approval before each stage.

External core location (never copy into this repository):
C:\Users\Operator\Documents\exo-private\tsc.exo.private.json

Stage plan:
0. Orientation: scaffold and checkpoint; no EXO execution.
1. Core/crate: independently check a fresh public-main clone and batteries;
   verify structural immutability and authorized external-core wiring/wake.
2. Continuous loop: demonstrate at least five cases, hostile rejection,
   Judge-gated clean PSC, rolling WFC, and controlled shutdown.
3. Memory/sleep: weighted event log; pending proposals; zero core changes.
4. Trust pipeline: local sneak sweep and OS-isolated fixed-policy guardian;
   prove catch/deny/allow and access separation. No runtime TSC writes.
5. Brain/docs: swappable backend, rule-based default, configuration and
   permission fence, stub switching, operator instructions. Real model fit
   requires its own verification; no unsolicited downloads or purchases.
6. Backup/package: private extracted-package wake/loop checks, manifest and
   credential checks. Same-machine backup must not be called off-box.
7. Operator auth + camera senses: PBKDF2 operator verification outside Git;
   identity attribution unlocked while iron rule holds; owner-toggled camera
   with in-memory frame diff/vision and zero disk writes.
8. Smart brain: LLM backend online via local Ollama (qwen2.5:7b-instruct-q4_K_M);
   natural generative riffing with immutable TSC injection; Judge byte-checking
   outputs and enforcing permission fence; graceful offline fallback.
9. Voice (local ears and mouth): CPU faster-whisper STT (base), CPU piper-tts
   (en_US-ryan-medium); walkie-talkie loop with zero audio on disk; owner-toggled
   mic default OFF; voice carries zero privilege over typing; spoken mutability attacks
   quarantined by Judge.
10. Multimodal Vision + Voice & Grounded Learning: Local Moondream 1.7GB VLM online in Ollama;
    live camera eye + push-to-talk voice chat fusion; hardware buffer flushing for real-time live capture;
    operator-taught visual truths grounded and imprinted into PSC (Judge-approved, zero core changes);
    memory recall of taught objects in subsequent turns.
11. Cockpit Flight Deck & Tool System: Gated tool execution engine (cockpit.py);
    hardware telemetry instruments (RTX 3050 VRAM via nvidia-smi, Win32 RAM load via ctypes, uptime);
    real-time clock & timer; path-jailed workspace inspection; persistent memory query; safe calculator;
    console ASCII flight deck (cockpit/flightdeck command); on-demand loop and voice tool calling.
12. Native desktop body: pywebview with system WebView2; existing HTML and icons completed;
    private-pipe, allowlisted and fence-checked adapter over the unchanged Stages 1–11 mind;
    first-run enrollment/verification and local environment guidance; crate splash and Windows tray;
    post-Judge display streaming, inline tools, hold-to-talk and visible configurable focused-window key;
    local voice, operator-only camera/mic/open-mic controls, live two-second cockpit gauges and denial feed;
    read-only PSC/events and existing sleep consolidation with candidate/drop progress;
    animated eye and toggleable local chimes; body-only PyInstaller executable with archive exclusion checks.




For every stage: check usage, implement only the approved stage, verify,
commit locally, write a timestamped handoff, then stop for approval.
Save incomplete checkpoints honestly if interrupted; never claim tests ran
when they did not. Outages cannot be guaranteed to respect stage boundaries.

Owner reports a clean-clone 305/305 run this morning. Record as owner-verified;
independently reproduce it in Stage 1 before building on the public baseline.
Never import the sandbox's old PSC. Never touch physical-core/PUNIT research.
