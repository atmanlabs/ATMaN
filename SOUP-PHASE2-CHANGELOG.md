# SOUP Phase 2 Changelog

## Fix 2a — wire keep_alive (2026-09-22 07:36 -0400)

**Change:** `call_ollama` and Minecraft `/api/chat` now send `keep_alive` from `config.yaml` (`mind.ollama_keep_alive`, default -1). Backups: `reason.py.bak-soup-p2a-*`, `minecraft_context.py.bak-soup-p2a-*`.

**Why:** Config already said forever-resident, but the payload never included `keep_alive`, so Ollama unloaded after ~5 min and charged ~2.8s reload.

**Before (Phase 1):**
- Cold tiny generate: 3259 ms (load 2800)
- Warm tiny generate: 287 ms
- Full relay turn: 4517 ms
- `ollama ps` UNTIL: ~4–5 minutes

**After Fix 2a:**
- Cold tiny generate: 2999.7 ms (load 2785.0)
- Warm tiny generate: 156.5 ms (load 4.6)
- Full relay turn (warm): 6704.2 ms
- Residency expires_at: 2319-01-02T06:23:26.934067007-05:00

**Interpretation:** Keep-alive does not shrink a warm full turn; it removes the 2.8s reload tax between turns. Streaming + prompt shrink still needed for sub-2s first token on the 4.5s path.

## Fix 2b — stream + early JSON stop + num_predict=256 (2026-09-22 07:37 -0400)

**Change:** `call_ollama` now uses `stream: true`, caps `num_predict` (config `mind.ollama_num_predict`, default 256), and returns as soon as accumulated tokens parse as JSON with a `proposed_action.type`. Records `ttft_ms` / `early_stop` on `call_ollama.last_meta`. Backup: `reason.py.bak-soup-p2b-*`. Config restored from bak after accidental wipe; `ollama_num_predict: 256` added.

**Before Fix 2b (after 2a, warm):**
- Warm tiny generate: ~157 ms
- Full relay turn: ~6704 ms (buffered)

**After Fix 2b:**
- Direct stream call meta: {'ttft_ms': 173.285400000168, 'total_ms': 1165.6184000021312, 'early_stop': True, 'chars': 193}
- Full relay turn 1 (how are you): 4467.4 ms → "Good morning! How do you do? Hope you're having a great day!"
- Full relay turn 2 (ping): 5032.8 ms → "Good morning! How do you do? Hope you're having a great day!"

**Note:** HTTP `/chat` still returns one shot (Minecraft/UI get the full reply at end). Streaming cuts *generation* wall time via early-stop + token cap; first-token UI streaming would need SSE next. Prompt shrink is Fix 2c.

## Fix 2 — WorkingContext snapshot (TSC once / PSC on imprint / capped WFC) (2026-09-22 07:44 -0400)

**Change:** Added `working_context.py`. Loop assembles one snapshot per cycle; Reason only reads it. TSC system prefix cached once. PSC text refreshed only when dirty (after Judge-gated imprint). WFC prompt window capped (`wfc_prompt_window=5`, slim chars, no movement blobs). Removed per-turn PSC disk reload unless dirty. Backups: `reason.py.bak-soup-snapshot-*`, `loop.py.bak-soup-snapshot-*`.

**Before (10-turn measure):** system ~3.2–4.0k fluctuating; wfc_n 0→9; wfc_ch 20→1330; ~tok 1414→1257; wall ~3.1–4.7s

**After:** see SOUP-PHASE2-WFC-AFTER.md / trace curve printed above.
