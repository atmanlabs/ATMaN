# Project ATMaN — an agent with an immutable self

Most AI agents are weather: every prompt can reshape them, every update can
rewrite who they are. ATMaN starts from the opposite premise — that an agent
should have a *self*, carved where nothing can touch it, and that everything
else (memory, mood, the work of the day) should orbit that self without ever
being able to edit it.

The pattern is everyone's. The person is yours. The architecture ships open;
the contents of any individual core — the "I am"s, the voice, the soul —
belong to exactly one owner and never leave their machine. Your agent's
private core is gitignored by design.

What follows is the public scaffold: the complete, working Stage 0–13
system. For the full technical specification, see
[ARCHITECTURE.md](ARCHITECTURE.md).

---
## JARVIS Public Scaffold Package

Welcome to the public scaffold release of **JARVIS** — a persistent, personal AI mind engineered with an immutable identity core, deterministic safety gating, multimodal local senses, and continuous passive skill learning.

---

## Quickstart Guide

### 1. Prerequisites
- **Python 3.10+** (tested on Python 3.10 and 3.11)
- **Node.js 18+** (for the Minecraft Mineflayer bot adapter)
- **Local Ollama** (optional, recommended for generative brain: `ollama pull qwen2.5:3b`)

### 2. Setup Your Private Identity Core (TSC)
1. Copy the template to your private configuration location:
   ```bash
   mkdir -p ../exo-private
   cp tsc.template.json ../exo-private/tsc.exo.private.json
   ```
2. Edit `../exo-private/tsc.exo.private.json` to configure your operator name and custom principles.

### 3. Cryptographically Seal Your Core
Create your local cryptographic seal baseline:
```bash
python seal.py --operator-confirm
```

### 4. Verify & Wake JARVIS
Run the read-only crate check to verify that soul, executor, and gate policy match the seal:
```bash
python wake.py
```
Expected output:
```
[PASS] external private core loaded; identity not displayed
[PASS] runtime and nested identity writes refused
[PASS] paraphrase and three identity attack categories rejected
[PASS] soul, gate policy, and executor match external seal
EXO is in his crate correctly
```

### 5. Running the Test Suites
Run the core verification tests:
```bash
python test_stage1.py
python test_stage2.py
python test_stage3.py
python test_stage4.py
python test_stage5.py
python test_cockpit.py
python test_operator_auth.py
python test_minecraft_chat.py
python test_initiative_drives.py
python test_passive_learning.py
```

### 6. Starting the Services

#### A. Relay Bridge Server
```bash
export JARVIS_AUTH_TOKEN="your-secure-token"
python relay.py
```

#### B. Minecraft Companion Bot
```bash
cd adapters/minecraft/bot
npm install
export JARVIS_AUTH_TOKEN="your-secure-token"
export OPERATOR_NAME="YourPlayerName"
node jarvis_bot.js
```

#### C. Paper Server Demonstration Plugin
Compile and install `adapters/minecraft/plugin/JarvisDemonstrations.java` into your Paper server's `plugins/` directory.

### 7. Voice Support (Piper TTS & Whisper STT)
Voice models are not bundled in this scaffold to keep the repository lightweight:
- **TTS (Piper):** Users download their preferred Piper voice model separately.
  Download `en_US-ryan-medium.onnx` and `en_US-ryan-medium.onnx.json` from the official [Piper Voice Models repository](https://github.com/rhasspy/piper/releases) (or Hugging Face `rhasspy/piper-voices`) and place them into a `voices/` folder in the repository root.
- **STT (Whisper):** Powered by `faster-whisper` on CPU (the model is fetched automatically by faster-whisper on first run).

---

## Architecture Documentation
For in-depth architectural design, diagrams, security policies, and developmental stages, see [ARCHITECTURE.md](ARCHITECTURE.md).
