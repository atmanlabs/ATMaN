# EXO desktop — Stage 12

Open **EXO.exe**. This is the native Windows body for the existing EXO installation.
It uses system WebView2 and the existing backend at `%USERPROFILE%\Documents\exo-live`,
with Python 3.11 at `%USERPROFILE%\AppData\Local\Programs\Python\Python311\python.exe`.
The executable can live elsewhere on this PC. It does not install or copy the mind,
models, private core, seal, or authentication store. It is not a standalone mind
distribution for a different PC.

## First launch

The crate check runs before the session opens. The wizard displays local Ollama/model
availability and device guidance. Existing enrollment is reused. If no enrollment
exists, create a passphrase of at least 12 characters. A guest session is available;
it does not grant verified operator attribution. Never enter a passphrase in chat.

The camera and microphone start **off**, even if the console configuration has them
enabled. Turn them on explicitly in Flight Deck. No device permission settings are
changed by the app. Failed capture requires checking Windows Settings > Privacy &
security > Camera/Microphone > desktop app access. Models are never downloaded by
the desktop; install missing local models separately.

## Controls

- Chat: type and send, or hold the microphone button. Approved replies appear in
  chunks only after the existing Judge finishes. This is post-Judge display streaming,
  not exposure of raw model tokens. Tool results appear inline.
- Push-to-talk: the selected key appears in Settings and on the button. It works
  while EXO is focused, except inside text inputs. Releasing it or leaving the window
  stops capture. Recordings are limited to 30 seconds and kept in memory.
- Open-Mic: enable the microphone, then select Open-Mic in Flight Deck. Speech is
  submitted after a silence gap. Listening pauses during thought, speech, and sleep.
- Camera: when enabled, a live frame can inform the next message. Frames stay in memory.
- Flight Deck: GPU, VRAM, RAM, and uptime refresh approximately every two seconds.
  The fence rule and denial feed remain visible.
- Mind: browse the latest 300 PSC/event records, without editing them. Sleep shows
  events scanned, imprint candidates queued, and events dropped. Stage 3's existing
  consolidator queues proposals; it applies **zero** core changes. Wake rechecks the crate.
- Settings: change the hold key, wake/sleep sounds, or close-to-tray behavior.
- Tray: Show EXO, Sleep, Wake, Quit. Quit drains the current mind operation before exit.
  If tray creation fails, closing the window exits instead of hiding an inaccessible app.

Do not run the console mind and desktop against the same live memory stores at the
same time. The desktop prevents a second desktop instance; it cannot coordinate
with an already-running legacy console.

## Safety boundary

Only `Bridge.request` is exposed to JavaScript. Both the native host and worker enforce
an explicit command allowlist. Backend actions and cockpit tools also pass the existing
permission fence. There is no frontend eval, shell, arbitrary file read/write, or configurable
backend executable. The fixed backend Python process is launched by the native host only.

The worker denies non-loopback sockets/name lookups and all child processes except the
cockpit's exact NVIDIA telemetry query. The UI has no HTTP listener or external assets.
Model downloads and Hugging Face telemetry are disabled. HTML is rendered as text for all
untrusted chat/memory/tool output. No raw thought, core object, authentication record,
or backend exception is serialized. Protected statements are filtered in memory before
display. Backend diagnostics go to the null device, not log files.

Only UI preferences are saved in `runtime/desktop-settings.json`; sense consent and
passphrases are not saved there. Existing authentication code handles its own external
verification record unchanged.

## Build and verify

Using the existing Python installation from the EXO project folder:

```text
python -m unittest test_desktop
python desktop_ui_smoke.py
python desktop_verify.py
python wake.py
python build_desktop.py
```

The native smoke test uses synthetic data and no real enrollment, memories, camera,
or microphone. It opens and closes its own WebView2 window and Windows tray icon.
The desktop unit tests also exercise real Judge/consolidation code with temporary stores.
`desktop_verify.py` runs the full regression suite with offline model loading and
prints test identifiers and counts while discarding backend diagnostic output.

`build_desktop.py` creates `dist/EXO.exe` and `dist/RELEASE-CHECK.json`. An explicit data
manifest includes only the UI assets, icon, and desktop worker. The verifier inspects the
executable and nested Python archive, rejects private/authentication/memory files and
mind modules, and scans included text assets for credential-record markers. It never
opens the real credential or private core files to perform a content comparison.

Build dependencies: pywebview, pystray, Pillow, PyInstaller. The installed backend retains
its own existing dependencies. Packaging follows the official
[PyInstaller documentation](https://pyinstaller.org/en/stable/spec-files.html), and the
native bridge uses [pywebview](https://pywebview.flowrl.com/api/).
