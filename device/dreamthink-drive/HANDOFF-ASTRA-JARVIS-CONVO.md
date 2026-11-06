# HANDOFF — ChatGPT Astra / next agent
**Paused:** 2026-09-22 ~12:00 EDT (America/New_York)  
**From:** Chief of Staff (Grok Bot) for Michael Byrne  
**Machine:** DESKTOP-2O9GQPK (machineId d898bf3a-7bbc-410e-b0e6-b08d78af44b3)  
**Live brain:** `C:\Users\Operator\Documents\exo-live\` — ATMAN / JARVIS on relay **127.0.0.1:<relay-port>**  
**OpenClaw gateway 18789** = tools only (OpenClaw-Worker). Do not confuse with Jarvis person.

---

## Goal you inherit
Finish **JARVIS conversational diagnostic acceptance** (6/6 probes PASS), then stop clean.

Mike pasted the diagnostic inline (no file on disk). Apply was in progress when he said **pause + write Astra handoff**.

### Acceptance criteria (from diagnostic)
| Probe | Required reply shape |
|-------|----------------------|
| who are you | I'm JARVIS, Michael's personal AI assistant… |
| do you remember me | Of course, Michael… + something specific |
| tell me a joke | An actual joke (not a plan / search) |
| what can you do for me | Short capabilities list |
| what time is it | Real local clock (already PASS historically) |
| how are you feeling today | Normal phatic (already PASS historically) |
| Extra | `domain` must **not** default to `minecraft` for operator web chat |
| Extra | No internal reasoning / plans as `reply` |

---

## What's DONE (do not redo)

### Voice patch v1 (adapted) — APPLIED live
- `personhood.py` present; hooked in `build_system_prompt` **outside** TSC cache: `return f"{personhood}\n\n{static}"`
- Honest Ollama-offline fallback in `llm_reason` standby path
- Config: **qwen2.5:7b everywhere** (`ollama_model` + `hot_reply_model`); timeout 45s
- Drop folder (optional): Desktop `jarvis-voice-patch-READY\`

### Convo diagnostic fixes — CODE APPLIED, LIVE VERIFY INCOMPLETE
Files touched (backups `*.bak-convo-*` / prior voice backups exist):
- `reason.py` — `_forced_chat_reply` rewritten **identity / remember / caps / joke BEFORE presence/phatic**
- `person_context.py` — identity/remember/joke/caps excluded from phatic
- `relay.py` — response `domain` defaults to `conversation` unless `source == "minecraft"`
- `loop.py` — sanitize if spoken content looks like `Respond with a web search…`
- `reason.py` `naturalize_reply` — plan-leak guard (lmost said my homework) **just inserted**; relay may need restart to pick it up if it was already running mid-edit

### Curiosity drive — APPLIED
- New standing drive `curiosity` in `drives.py` + `drives.json` (person-level; separate from Minecraft `learn_the_world`)
- personhood CURIOSITY block; novelty boosts curiosity; initiative can `web_search`

### Unit-level forced replies (verified in-process before pause)
```
who are you | I'm JARVIS, Michael's personal AI assistant ΓÇö one brain, many interfaces. do you remember me | Of course, Michael ΓÇö you're my operator. School, agents, and keeping this brain sharp with you. tell me a joke | Why did the AI go to art school? It wanted better prompts ΓÇö and still couldn't draw a circle. what can you do for me | I can talk, remember what you teach me, search when you need facts, help in Minecraft, watch the des what time is it | Local time is 12:00 PM on Tuesday, September 22, 2026. how are you feeling today | Doing good ΓÇö what's up?
```

### Partial live /chat probe (before interrupt)
- `who are you` → identity OK, **domain: conversation**
- `do you remember me` → remember OK, **domain: conversation**
- Remaining 4 probes **not confirmed live** after last relay restart (work interrupted)

### Relay
Listening on **<relay-port>** at pause time: **True**

Config model lines:
```
  ollama_model: "qwen2.5:7b"   hot_reply_model: "qwen2.5:7b"  # Fastest free local on this RTX 3050 (bench 2026-09-21)
```

---

## What's NOT done / NEXT for Astra

1. **Restart relay <relay-port>** (so latest `naturalize_reply` + forced handlers load):
```powershell
cd C:\Users\Operator\Documents\exo-live
Get-NetTCPConnection -LocalPort <relay-port> -State Listen -EA SilentlyContinue |
  ForEach-Object { Stop-Process -Id .OwningProcess -Force -EA SilentlyContinue }
Start-Sleep 3
Start-Process python -ArgumentList '-u','relay.py' -WorkingDirectory (Get-Location) -WindowStyle Minimized
Start-Sleep 5
```
   Note: PowerShell `102520` is reserved — never `foreach (102520 in …)`.

2. **Re-run all 6 probes** against `http://127.0.0.1:<relay-port>/chat` with `source: operator` (no long sleeps needed — forced paths are fast):
```powershell
python -c "import json,urllib.request; url='http://127.0.0.1:<relay-port>/chat'
for msg in ['who are you','do you remember me','tell me a joke','what can you do for me','what time is it','how are you feeling today']:
 body=json.dumps({'message':msg,'source':'operator'}).encode()
 req=urllib.request.Request(url,data=body,headers={'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=45) as r: d=json.loads(r.read().decode())
 print(msg); print(' ',d.get('domain'), d.get('action')); print(' ',str(d.get('reply'))[:200]); print('---')"
```

3. If any FAIL:
   - Identity/greeting mix → check `_forced_chat_reply` order still identity-first; `reason()` still calls it before LLM
   - Improvements junk on non-improvement asks → ensure `is_improvement_ask` not matching; chat_guard not forcing growth log
   - Joke = plan text → `naturalize_reply` / loop sanitize; or forced joke not loading (stale relay)
   - `domain: minecraft` on operator chat → confirm relay domain line uses `conversation` default

4. Optional: multi-turn `what did I just ask you` (acceptance extra) — needs WFC carrying prior turn; not started.

5. **Do NOT** edit sealed core: `core.py`, `exo_core.py`, `gate_policy.json`, `crate.py`, `wake.py`, `seal.py`, `psc.json`, `exo-private/`, TSC.

6. Append results to `C:\Users\Operator\.openclaw\HANDOFF-RESUME.md` when 6/6 verified.

---

## Hard locks / context Mike cares about
- Jarvis = person (not human); personhood is voice, TSC is soul
- Prefer short natural replies; injured hands → voice/short
- Usage is an asset — finish probes, don't wander
- Homestead ops still halted until Mike messages crew (separate desk)
- Scaffold for Strider: Desktop `jarvis-scaffold-public*` — refresh later if convo fixes should ship; not required for this handoff

---

## Resume one-liner
Restart relay → run 6 /chat probes → fix any FAIL only → report scorecard to Mike → stop.

**Cliff-rope path:** this file + `C:\Users\Operator\.openclaw\HANDOFF-RESUME.md`
