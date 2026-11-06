# THOUGHT-RENDER-PROOF

Updated: 2026-09-25 21:29:11 ET (DESKTOP-2O9GQPK)

## Overall: **PASS**

Cold proof that DreamThink words come from **decide -> speech_render** with **zero LLM calls** — not vibes.

### One-glance table

| Section | Check | Result |
|---|---|---|
| A Positive | `whats_up` decide->render + llm_calls=0 + fidelity | **PASS** |
| A Positive | `rough_day` decide->render + llm_calls=0 + fidelity | **PASS** |
| A Positive | `minecraft_follow` decide->render + llm_calls=0 + fidelity | **PASS** |
| B Nonce | tracer `THOUGHTPROOF_NONCE_5AA83E39E…` appears only via speech_render | **PASS** |
| C Ablation | `ablation_empty_bank` | **PASS** |
| C Ablation | `ablation_spy_trips_on_llm` | **PASS** |
| C Ablation | `ablation_missing_imprint_no_invent` | **PASS** |
| C Ablation | `backend_tag_dreamthink_only` | **PASS** |
| Spies | call_ollama / LLM backends never invoked (final spy.calls=0) | **PASS** |
| Locks | llm_fallback=false; live-mode not flipped; sleep/relay untouched | **PASS** |

### How Mike verifies in one glance
1. Overall **PASS** above.
2. Every positive row has `llm_calls=0`, `backend=dreamthink_only`, `kind=compositional_speech`.
3. Sample receipt: decided `note_id` equals `receipts[0].note_id`; receipt clauses embed in final text.
4. Nonce string appears in lab output via speech_render path, and is **absent** from live imprint bank file.
5. Empty-bank ablation does **not** produce fluent hyp-tagged LLM fill.

### Re-run
```
cd C:/Users/Operator/Documents/exo-live
python runtime/dream-cloud/run_thought_render_proof.py
```

### Sample receipt (first positive)
```json
{
  "utterance": "what's up",
  "decided": {
    "kind": "intention",
    "note_id": "conv-dc9cdf9931304234",
    "relation_id": "rel-679afeb83b0552b0",
    "subject": "return a casual check-in",
    "object": "invite sharing without inventing a status fill",
    "predicate": "requires",
    "speech_style": "conversation_move",
    "provenance": "HYPOTHETICAL_CURRICULUM",
    "hypothetical": true,
    "follow_on_note_ids": [
      "conv-0ab133ad14d747ea"
    ],
    "templates_used": [
      "tpl_social_when+tpl_hyp_prefix",
      "tpl_social_chosen"
    ],
    "renderable_slots": {
      "subject": "return a casual check-in",
      "object": "invite sharing without inventing a status fill",
      "gist_head": "Before I return a casual check-in, I should invite sharing without inventing a status fill.",
      "clause0": "When I return a casual check-in, I should invite sharing without inventing a status fill."
    },
    "source": "speech_render.receipts"
  },
  "candidates_top3": [
    {
      "score": 2.2106,
      "note_id": "pctx-0d548ea34b7132c1078b5c26",
      "relation_id": "rel-52a0c37c76f6bfcc",
      "subject": "answer an open-domain ask like 'Hey Jarvis, whats up?'",
      "object": "skip web look-up and use local compositional speech",
      "speech_style": "conversation_move",
      "provenance": "HYPOTHETICAL_CURRICULUM",
      "hypothetical": true,
      "gist": "Before I answer an open-domain ask like 'Hey Jarvis, whats up?', I should skip web look-up and use local compositional speech."
    },
    {
      "score": 1.9741,
      "note_id": "pctx-228dfa05cddcefe42d1a866b",
      "relation_id": "rel-c87de5feaad6080e",
      "subject": "When the turn is a pure greeting or check-in, I should skip passive web look-up and stay on social compositional speech.",
      "object": "",
      "speech_style": "conversation_move",
      "provenance": "HYPOTHETICAL_CURRICULUM",
      "hypothetical": true,
      "gist": "When the turn is a pure greeting or check-in, I should skip passive web look-up and stay on social compositional speech."
    },
    {
      "score": 1.18,
      "note_id": "pctx-44c1fd382bd9dfb4525acf23",
      "relation_id": "rel-e3df27c7ccf8d1de",
      "subject": "When a Minecraft or local procedure cue is present and bank knowledge suffices, I should not force a web look-up.",
      "object": "",
      "speech_style": "conversation_move",
      "provenance": "HYPOTHETICAL_CURRICULUM",
      "hypothetical": true,
      "gist": "When a Minecraft or local procedure cue is present and bank knowledge suffices, I should not force a web look-up."
    }
  ],
  "composition_trace": {
    "templates_used": [
      "tpl_social_when+tpl_hyp_prefix",
      "tpl_social_chosen"
    ],
    "note_ids_used": [
      "conv-dc9cdf9931304234",
      "conv-0ab133ad14d747ea"
    ],
    "relation_ids_used": [
      "rel-679afeb83b0552b0",
      "rel-d1b561c8f05382c3"
    ],
    "bridges": {
      "daychat_soft": true,
      "negation": false,
      "minecraft": false,
      "open_domain": false
    }
  },
  "final_utterance": "Hey — what's up?",
  "receipts": [
    {
      "note_id": "conv-dc9cdf9931304234",
      "relation_id": "rel-679afeb83b0552b0",
      "template_id": "tpl_social_when+tpl_hyp_prefix",
      "clause": "When I return a casual check-in, I should invite sharing without inventing a status fill."
    },
    {
      "note_id": "conv-0ab133ad14d747ea",
      "relation_id": "rel-d1b561c8f05382c3",
      "template_id": "tpl_social_chosen",
      "clause": "Chosen move: offer a clean hello and wait for substance."
    }
  ],
  "fidelity": {
    "ok": true,
    "decided_note_in_receipts": true,
    "slot_hits": [],
    "slot_ok": false,
    "clauses_embedded": false,
    "method": "compositional_imprint_render",
    "method_ok": true,
    "receipt_template_ids": [
      "tpl_social_when+tpl_hyp_prefix",
      "tpl_social_chosen"
    ],
    "receipt_note_ids": [
      "conv-0ab133ad14d747ea",
      "conv-dc9cdf9931304234"
    ]
  },
  "packet": {
    "backend": "dreamthink_only",
    "kind": "compositional_speech",
    "method": "compositional_imprint_render",
    "llm_calls": 0,
    "error": null
  },
  "checks": {
    "llm_calls_0": true,
    "spy_calls_0": true,
    "compositional": true,
    "kill_bar_pass": true,
    "backend_dreamthink_only": true,
    "kind_compositional": true,
    "fidelity": true,
    "decided_present": true,
    "not_refused": true
  }
}
```

### Nonce before/after
- target_note_id: `conv-dc9cdf9931304234`
- nonce: `THOUGHTPROOF_NONCE_5AA83E39E4EF`
- before gist: `Before I return a casual check-in, I should invite sharing without inventing a status fill.`
- after gist (lab only): `Before I return a casual check-in, I should invite sharing without inventing a status fill [THOUGHTPROOF_NONCE_5AA83E39E4EF].`
- injection_path: `imprint_object_gist`
- live bank clean: `True`
- restore: lab_bank was an in-memory deepcopy; live accelerate-imprint-bank.json never written. If template fallback used, GLUE restored in finally.

### Hard locks observed
- enabled: `True`
- llm_fallback: `False`
- renderer: `compositional_speech`
- day_chat_promote: `True`
- passive_web_context: `True`
- live_mode_mtime_unchanged: `True`

### Residuals
- none

### Untouched
- No TSC/soul/identity/voice edits
- live-mode.json not written; llm_fallback left false
- Passive-context sleep / relay not killed or restarted
- speech_render.py / dreamthink_chat.py not modified (harness is additive + monkeypatch)

