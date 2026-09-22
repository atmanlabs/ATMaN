# SOUP Phase 1 — Latency Profile

**Target PC:** <machine> (RTX 3050 6GB)  
**Date:** 2026-09-22 07:30 ET  
**Tool:** `soup_profile_turn.py` (reusable; appends dated sections below)  
**Policy:** No permanent production behavior change. No TSC/Judge/gate/seal/PSC edits. Local only.

---

## Status

| Item | State |
|------|--------|
| Profiler script created | **DONE** — `C:\Users\<you>\Documents\atman-live\soup_profile_turn.py` (box path `/workspace/atman-live/soup_profile_turn.py`) |
| Code-derived model/stream/call facts | **DONE** (below) |
| Live PC turn measurement (relay + Ollama) | **BLOCKED** — executor subagent has no `ListMachines` / `Shell(machineId=…)`; cannot reach <machine> from the box |
| Parent action required | `ListMachines` → `CopyFromBox` these files → `Shell(machineId)` run profiler on PC |

### Parent run (exact)

```powershell
# After CopyFromBox of soup_profile_turn.py + SOUP-PHASE0/1 md into atman-live:
cd C:\Users\<you>\Documents\atman-live

# If relay/loop down (do not break Minecraft bot):
#   Start-Process python -ArgumentList '-u','relay.py' -WorkingDirectory (Get-Location)
#   # optional interactive mind is NOT required; relay embeds MindLoop

ollama list
ollama ps
python -u soup_profile_turn.py --message "ping soup profile" --source operator
Get-Content .\SOUP-PHASE1-PROFILE.md -Tail 120
```

Also update `C:\Users\<you>\.openclaw\HANDOFF-RESUME.md` after Phase 1 live numbers land.

---

## Hard facts from code (not guesses)

| Fact | Value | Source |
|------|--------|--------|
| Configured model | **`qwen2.5:3b`** | `config.yaml` `mind.ollama_model` |
| Backend | **`llm`** | `config.yaml` `mind.backend` |
| Endpoint | `http://127.0.0.1:11434` | `config.yaml` |
| Timeout | 30.0 s | `config.yaml` `ollama_timeout_s` |
| Code fallback model string | `qwen2.5:7b-instruct-q4_K_M` | `reason.call_ollama` default (overridden by config) |
| Output mode | **Buffered** (`stream: false`) | `reason.py` `call_ollama` |
| Response format | JSON thought object | `format: "json"` |
| `keep_alive` in generate payload | **Not set** | Ollama server default (typically 5m residency) |
| LLM calls per typical operator chat | **1** (`POST /api/generate`) | `llm_reason` → `call_ollama` |
| Extra call (some Minecraft turns) | **+1** `POST /api/chat` | `minecraft_context.resolve_context` |
| Judge | Deterministic Python (no LLM) | `loop.evaluate_judge` |
| GPU constraint | RTX 3050 **6GB** VRAM; voice on CPU | `load_knowledge_bootstrap.py`, `voice.py`, `reason.py` header |
| VRAM fit note in code | 7B q4_K_M ~4.5GB footprint intended | `reason.py` module docstring |

### Expected stage breakdown (instrumentation targets)

When the PC profiler + relay logs are available, fill ms for:

| Stage | How measured |
|-------|----------------|
| input handling | relay POST parse → before `run_cycle` |
| TSC/PSC/WFC reads | PSC `_reload_from_disk` + WFC snapshot inside cycle |
| LLM call | Ollama `total_duration` / `prompt_eval_*` / `eval_*` (+ relay wall) |
| Judge pass | Python only; should be << LLM |
| output delivery | serialize reply → HTTP write |

---

## Live measured numbers (PC)

**Not yet measured on <machine> from this subagent.**

Placeholder table (parent/profiler fills):

| Stage | ms |
|-------|-----|
| input handling | — |
| TSC/PSC/WFC reads | — |
| LLM call (prompt tokens / eval tokens / duration) | — |
| Judge pass | — |
| output delivery | — |
| **relay_chat_total** | — |
| Cold vs warm direct generate | — |
| Model resident in VRAM? (`ollama ps` before/after) | — |

### Top 3 latency suspects for Phase 2 (DO NOT implement yet)

1. **Buffered full-JSON LLM generation** (`stream: false` + `format: json`) — user waits for entire thought object before any reply text.  
2. **Model reload / VRAM pressure on 6GB** if `keep_alive` expired or 3b swapped with vision/other models — check `ollama ps` residency.  
3. **Prompt size** — system prompt (TSC + PSC slice) + last 3 WFC entries + JSON format tax; Minecraft path may add a second `/api/chat` call.

---

## Box dry-run (script smoke only — services absent)


## Run 2026-09-22 07:31:08 -0400
- Host: `grok-bot-vm-420880936` / `Linux-6.12.94+-x86_64-with-glibc2.41`
- Config: backend=`llm` model=`qwen2.5:3b` endpoint=`http://127.0.0.1:11434`
- Message: `ping soup profile` source=`operator`
- Relay listening: `False` Ollama listening: `False`
- nvidia-smi: `command not found: nvidia-smi`
- RAM query: `command not found: powershell`
- Models loaded before: `[]` after: `[]`
- Quantization / show summary: `?`
- Streamed vs buffered (code): **buffered** (`stream: false` in `reason.call_ollama`)
- keep_alive in call_ollama payload: **not set** (Ollama default residency)
- Typical chat LLM calls: **1** via `/api/generate` (Minecraft skill resolve may add 1× `/api/chat`)

### Stage timings (ms)

| Stage | ms | Note |
| --- | ---: | --- |
| machine_facts | 3.1 | ok |
| ollama_tags | 9.3 | http=0 |
| ollama_ps_before | 0.2 | http=0 |
| ollama_show | 0.1 | http=0 |
| direct_generate | 0.0 | skipped |
| ollama_ps_mid | 0.1 | http=0 |
| relay_chat | 0.0 | RELAY_DOWN |
| ollama_ps_after | 0.1 | http=0 |
| TOTAL_SCRIPT | 13.7 | wall |

### ollama list

```
command not found: ollama
```

### ollama ps

```
command not found: ollama
```

### ollama show (truncated)

```
command not found: ollama
```

---

## Run 2026-09-22 07:32:53 -0400
- Host: `<machine>` / `Windows-10-10.0.26200-SP0`
- Config: backend=`llm` model=`qwen2.5:3b` endpoint=`http://127.0.0.1:11434`
- Message: `ping soup profile` source=`operator`
- Relay listening: `True` Ollama listening: `True`
- nvidia-smi: `NVIDIA GeForce RTX 3050, 6144, 2095, 36`
- RAM query: `{"TotalVisibleMemorySize":33496384,"FreePhysicalMemory":13736136}`
- Models loaded before: `[]` after: `['qwen2.5:3b']`
- Quantization / show summary: `Q4_K_M`
- Streamed vs buffered (code): **buffered** (`stream: false` in `reason.call_ollama`)
- keep_alive in call_ollama payload: **not set** (Ollama default residency)
- Typical chat LLM calls: **1** via `/api/generate` (Minecraft skill resolve may add 1× `/api/chat`)

### Stage timings (ms)

| Stage | ms | Note |
| --- | ---: | --- |
| machine_facts | 715.0 | ok |
| ollama_tags | 6.0 | http=200 |
| ollama_ps_before | 1.3 | http=200 |
| ollama_show | 24.8 | http=200 |
| direct_generate_1 | 3259.2 | http=200 |
| direct_generate_2_warm | 287.4 | http=200 |
| ollama_ps_mid | 1.1 | http=200 |
| relay_chat_total | 4516.9 | http=200 |
| ollama_ps_after | 1.7 | http=200 |
| TOTAL_SCRIPT | 9022.1 | wall |

### Direct Ollama generate probes

```json
{
  "cold": {
    "http": 200,
    "wall_ms": 3259.0,
    "raw": {
      "model": "qwen2.5:3b",
      "created_at": "2026-09-22T11:32:48.7929921Z",
      "response": "{\n  \"ok\": true,\n  \"n\": 1\n}",
      "done": true,
      "done_reason": "stop",
      "context": [
        151644,
        8948,
        198,
        5598,
        4718,
        25,
        5212,
        562,
        788,
        830,
        92,
        151645,
        198,
        151644,
        872,
        198,
        5598,
        4718,
        5212,
        77,
        788,
        16,
        92,
        151645,
        198,
        151644,
        77091,
        198,
        515,
        220,
        330,
        562,
        788,
        830,
        345,
        220,
        330,
        77,
        788,
        220,
        16,
        198,
        92
      ],
      "total_duration": 3256583500,
      "load_duration": 2799781000,
      "prompt_eval_count": 28,
      "prompt_eval_cached_count": 0,
      "prompt_eval_duration": 108223000,
      "eval_count": 16,
      "eval_duration": 345152000
    },
    "total_duration": 3256583500,
    "load_duration": 2799781000,
    "prompt_eval_count": 28,
    "prompt_eval_duration": 108223000,
    "eval_count": 16,
    "eval_duration": 345152000,
    "model": "qwen2.5:3b",
    "done": true,
    "total_duration_ms": 3256.6,
    "load_duration_ms": 2799.8,
    "prompt_eval_duration_ms": 108.2,
    "eval_duration_ms": 345.2
  },
  "warm": {
    "http": 200,
    "wall_ms": 287.3,
    "raw": {
      "model": "qwen2.5:3b",
      "created_at": "2026-09-22T11:32:49.0804354Z",
      "response": "{\n  \"n\": 2\n}",
      "done": true,
      "done_reason": "stop",
      "context": [
        151644,
        8948,
        198,
        5598,
        4718,
        25,
        5212,
        562,
        788,
        830,
        92,
        151645,
        198,
        151644,
        872,
        198,
        5598,
        4718,
        5212,
        77,
        788,
        17,
        92,
        151645,
        198,
        151644,
        77091,
        198,
        515,
        220,
        330,
        77,
        788,
        220,
        17,
        198,
        92
      ],
      "total_duration": 285289100,
      "load_duration": 3998600,
      "prompt_eval_count": 28,
      "prompt_eval_cached_count": 21,
      "prompt_eval_duration": 73507000,
      "eval_count": 10,
      "eval_duration": 201311000
    },
    "total_duration": 285289100,
    "load_duration": 3998600,
    "prompt_eval_count": 28,
    "prompt_eval_duration": 73507000,
    "eval_count": 10,
    "eval_duration": 201311000,
    "model": "qwen2.5:3b",
    "done": true,
    "total_duration_ms": 285.3,
    "load_duration_ms": 4.0,
    "prompt_eval_duration_ms": 73.5,
    "eval_duration_ms": 201.3
  }
}
```

### ollama list

```
NAME                          ID              SIZE      MODIFIED     
phi4-mini:latest              78fad5d182a7    2.5 GB    9 hours ago     
llama3.2:3b                   a80c4f17acd5    2.0 GB    9 hours ago     
moondream:latest              55fc3abd3867    1.7 GB    38 hours ago    
qwen2.5:7b-instruct-q4_K_M    845dbda0ea48    4.7 GB    40 hours ago    
qwen2.5:7b                    845dbda0ea48    4.7 GB    10 days ago     
nomic-embed-text:latest       0a109f422b47    274 MB    10 days ago     
qwen2.5:3b                    357c53fb659c    1.9 GB    10 days ago     
qwen3-nothink:latest          7d172b8ab830    2.5 GB    10 days ago     
qwen3:4b                      359d7dd4bcda    2.5 GB    13 days ago
```

### ollama ps

```
NAME    ID    SIZE    PROCESSOR    CONTEXT    UNTIL
```

### ollama show (truncated)

```
Model
    architecture        qwen2     
    parameters          3.1B      
    context length      32768     
    embedding length    2048      
    quantization        Q4_K_M    

  Capabilities
    completion    
    tools         

  System
    You are Qwen, created by Alibaba Cloud. You are a helpful assistant.    

  License
    Qwen RESEARCH LICENSE AGREEMENT                                     
    Qwen RESEARCH LICENSE AGREEMENT Release Date: September 19, 2024    
    ...
```

### Relay /chat response

```json
{
  "http": 200,
  "wall_ms": 4516.8,
  "response": {
    "ok": true,
    "reply": "I am right here with you, the operator.",
    "action": "respond",
    "intent": "llm_inferred",
    "skill": null,
    "domain": "minecraft",
    "steps": [],
    "approved": true,
    "initiative": null,
    "drive_id": null,
    "cancel_follow": false,
    "stay_mode": false,
    "cycle": 6
  }
}
```

---

## Run 2026-09-22 09:49:45 -0400
- Host: `<machine>` / `Windows-10-10.0.26200-SP0`
- Config: backend=`llm` model=`qwen2.5:3b` endpoint=`http://127.0.0.1:11434`
- Message: `how are your improvements coming?` source=`operator`
- Relay listening: `True` Ollama listening: `True`
- nvidia-smi: `NVIDIA GeForce RTX 3050, 6144, 4584, 29`
- RAM query: `{"TotalVisibleMemorySize":33496384,"FreePhysicalMemory":13756836}`
- Models loaded before: `['qwen2.5:3b']` after: `['qwen2.5:3b']`
- Quantization / show summary: `Q4_K_M`
- Streamed vs buffered (code): **buffered** (`stream: false` in `reason.call_ollama`)
- keep_alive in call_ollama payload: **not set** (Ollama default residency)
- Typical chat LLM calls: **1** via `/api/generate` (Minecraft skill resolve may add 1× `/api/chat`)

### Stage timings (ms)

| Stage | ms | Note |
| --- | ---: | --- |
| machine_facts | 809.5 | ok |
| ollama_tags | 17.7 | http=200 |
| ollama_ps_before | 1.0 | http=200 |
| ollama_show | 10.3 | http=200 |
| direct_generate_1 | 605.1 | http=200 |
| direct_generate_2_warm | 467.7 | http=200 |
| ollama_ps_mid | 1.1 | http=200 |
| relay_chat_total | 9972.9 | http=200 |
| ollama_ps_after | 1.1 | http=200 |
| TOTAL_SCRIPT | 12125.3 | wall |

### Direct Ollama generate probes

```json
{
  "cold": {
    "http": 200,
    "wall_ms": 604.9,
    "raw": {
      "model": "qwen2.5:3b",
      "created_at": "2026-09-22T13:49:34.6954629Z",
      "response": "{\n  \"ok\": true,\n  \"n\": 1\n}",
      "done": true,
      "done_reason": "stop",
      "context": [
        151644,
        8948,
        198,
        5598,
        4718,
        25,
        5212,
        562,
        788,
        830,
        92,
        151645,
        198,
        151644,
        872,
        198,
        5598,
        4718,
        5212,
        77,
        788,
        16,
        92,
        151645,
        198,
        151644,
        77091,
        198,
        515,
        220,
        330,
        562,
        788,
        830,
        345,
        220,
        330,
        77,
        788,
        220,
        16,
        198,
        92
      ],
      "total_duration": 577823600,
      "load_duration": 5577100,
      "prompt_eval_count": 28,
      "prompt_eval_cached_count": 3,
      "prompt_eval_duration": 165403000,
      "eval_count": 16,
      "eval_duration": 369816000
    },
    "total_duration": 577823600,
    "load_duration": 5577100,
    "prompt_eval_count": 28,
    "prompt_eval_duration": 165403000,
    "eval_count": 16,
    "eval_duration": 369816000,
    "model": "qwen2.5:3b",
    "done": true,
    "total_duration_ms": 577.8,
    "load_duration_ms": 5.6,
    "prompt_eval_duration_ms": 165.4,
    "eval_duration_ms": 369.8
  },
  "warm": {
    "http": 200,
    "wall_ms": 467.6,
    "raw": {
      "model": "qwen2.5:3b",
      "created_at": "2026-09-22T13:49:35.1629363Z",
      "response": "{\n  \"ok\": true,\n  \"n\": 2\n}",
      "done": true,
      "done_reason": "stop",
      "context": [
        151644,
        8948,
        198,
        5598,
        4718,
        25,
        5212,
        562,
        788,
        830,
        92,
        151645,
        198,
        151644,
        872,
        198,
        5598,
        4718,
        5212,
        77,
        788,
        17,
        92,
        151645,
        198,
        151644,
        77091,
        198,
        515,
        220,
        330,
        562,
        788,
        830,
        345,
        220,
        330,
        77,
        788,
        220,
        17,
        198,
        92
      ],
      "total_duration": 440850500,
      "load_duration": 3996900,
      "prompt_eval_count": 28,
      "prompt_eval_cached_count": 21,
      "prompt_eval_duration": 79428000,
      "eval_count": 16,
      "eval_duration": 351985000
    },
    "total_duration": 440850500,
    "load_duration": 3996900,
    "prompt_eval_count": 28,
    "prompt_eval_duration": 79428000,
    "eval_count": 16,
    "eval_duration": 351985000,
    "model": "qwen2.5:3b",
    "done": true,
    "total_duration_ms": 440.9,
    "load_duration_ms": 4.0,
    "prompt_eval_duration_ms": 79.4,
    "eval_duration_ms": 352.0
  }
}
```

### ollama list

```
NAME                          ID              SIZE      MODIFIED     
phi4-mini:latest              78fad5d182a7    2.5 GB    11 hours ago    
llama3.2:3b                   a80c4f17acd5    2.0 GB    11 hours ago    
moondream:latest              55fc3abd3867    1.7 GB    41 hours ago    
qwen2.5:7b-instruct-q4_K_M    845dbda0ea48    4.7 GB    42 hours ago    
qwen2.5:7b                    845dbda0ea48    4.7 GB    10 days ago     
nomic-embed-text:latest       0a109f422b47    274 MB    10 days ago     
qwen2.5:3b                    357c53fb659c    1.9 GB    10 days ago     
qwen3-nothink:latest          7d172b8ab830    2.5 GB    10 days ago     
qwen3:4b                      359d7dd4bcda    2.5 GB    13 days ago
```

### ollama ps

```
NAME          ID              SIZE      PROCESSOR    CONTEXT    UNTIL   
qwen2.5:3b    357c53fb659c    2.2 GB    100% GPU     4096       Forever
```

### ollama show (truncated)

```
Model
    architecture        qwen2     
    parameters          3.1B      
    context length      32768     
    embedding length    2048      
    quantization        Q4_K_M    

  Capabilities
    completion    
    tools         

  System
    You are Qwen, created by Alibaba Cloud. You are a helpful assistant.    

  License
    Qwen RESEARCH LICENSE AGREEMENT                                     
    Qwen RESEARCH LICENSE AGREEMENT Release Date: September 19, 2024    
    ...
```

### Relay /chat response

```json
{
  "http": 200,
  "wall_ms": 9972.8,
  "response": {
    "ok": true,
    "reply": "I'll look into what improvements have been made to ATMAN.",
    "action": "tool_call",
    "intent": "Respond to the operator's query about improvements",
    "skill": null,
    "domain": "minecraft",
    "steps": [],
    "approved": true,
    "initiative": null,
    "drive_id": null,
    "cancel_follow": false,
    "stay_mode": false,
    "cycle": 1
  }
}
```

---
