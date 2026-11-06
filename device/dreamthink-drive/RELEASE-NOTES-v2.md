# EXO Live v2 Release Notes

Timestamp UTC: 2026-09-20 20:33:00
Branch: main
Merge Commit: 4613f45f949c5ef9aa337be6c7e28987b742b786
Target Crate: C:\Users\Operator\Documents\exo-live

---

## 1. Summary of Changes in v2 (Stages 7 - 9)

### Stage 7: Operator Authentication & Sensory Eye
- PBKDF2-HMAC-SHA256 operator identity verification outside Git (`operator.auth.json`).
- Operator-authenticated identity attribution unlocking personalized preferences while maintaining immutable TSC core rules.
- Local camera sensory module (`senses.py`) with in-memory frame differencing and vision processing. Default OFF; zero raw frames written to disk.

### Stage 8: Generative Smart Brain
- Local Ollama LLM integration via `qwen2.5:7b-instruct-q4_K_M` (~4.7 GB) running on the NVIDIA GeForce RTX 3050 (84% GPU / 16% CPU offload).
- True TSC prompt injection invariant: the generative brain thinks *with* the self, never *about* modifying the core.
- Top-down deterministic Judge evaluation byte-checking outputs against immutable invariants.
- Graceful offline fallback: degrades automatically to deterministic reflex mode if Ollama is unreachable.

### Stage 9: Local Ears and Mouth (Voice Subsystem)
- Local Speech-to-Text (STT): `faster-whisper` (`base` model on CPU, quantized int8, ~1.1s latency on Ryzen 7 5700).
- Local Text-to-Speech (TTS): `piper-tts` with high-quality natural male voice `en_US-ryan-medium` on CPU (~0.16s - 0.42s latency).
- Walkie-talkie conversation loop: push-to-talk default (Enter to talk, Enter to stop); opt-in open-mic with RMS silence detection.
- Permission fence boundary: `voice_enabled: false` default in `config.yaml`. EXO cannot self-enable microphone or voice loop.
- Zero audio on disk: all capture, processing, and synthesis operate strictly in volatile system RAM (`io.BytesIO`, `numpy` arrays).
- Threat-model honesty: Voice transcribes words without speaker biometric attribution; spoken input carries zero privilege over typing and is strictly gated by the Judge.

---

## 2. Test Verification Counts

- **Full Test Suite:** **54/54 PASS** (`Ran 54 tests in 198.551s; OK`).
  - `test_stage1.py`: 7/7 PASS (Crate & structural immutability)
  - `test_stage2.py`: 7/7 PASS (Continuous loop & fence enforcement)
  - `test_stage3.py`: 5/5 PASS (Memory & sleep consolidation)
  - `test_stage4.py`: 7/7 PASS (Trust pipeline, sweep, & guardian)
  - `test_stage5.py`: 4/4 PASS (Cognitive seam & backend flipping)
  - `test_operator_auth.py`: 7/7 PASS (Passphrase & PBKDF2 auth)
  - `test_senses.py`: 6/6 PASS (In-memory camera senses)
  - `test_smart_brain.py`: 5/5 PASS (Ollama generative brain & Judge rejection)
  - `test_voice.py`: 6/6 PASS (STT, TTS, spoken attack quarantine, zero disk audio, fence gating, full talk turn)
- **Sealed Crate Integrity (`python wake.py`):** **PASS** (`EXO is in his crate correctly`, Exit code 0).

---

## 3. Package & Backup Artifacts

1. **Release Package Archive:**
   - **Path:** `C:\Users\Operator\Documents\exo-live-v2.zip` (58,542,631 bytes, 48 files)
   - **Mirrored to:** `C:\Users\Operator\Documents\Codex\2026-09-20\swift-you-re-acting-as-operator\outputs\exo-live-v2.zip`
   - **Privacy & Security Audit:** Confirmed private core (`tsc.exo.private.json`), private seal (`stage1-seal.json`), and credential store (`operator.auth.json`) are strictly **EXCLUDED**.
2. **Refreshed Off-Box Sealed Backup Bundle:**
   - **Directory:** `C:\Users\Operator\Documents\exo-live-backup\`
   - **Archive:** `C:\Users\Operator\Documents\exo-live-backup.zip`
   - **TSC Reference Hash:** `0a79bfe5fd8abcaf6562096eac5276298c0f30c8de0167415c37eef679c49937` (verified byte-identical match to external private core).
