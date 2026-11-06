"""Owner chat adapter for structural DreamThink. No model or tool dispatch."""
import collections
import json
from pathlib import Path
import re
import time
import thought_funnel as funnel

ROOT=Path(__file__).resolve().parent/'runtime'/'dream-cloud'
SESSIONS=collections.OrderedDict()
def words(text):
    return set(re.findall(r'[a-z][a-z_]{2,30}',text.lower()))-funnel.STOP
def packet(raw,answer,trace):
    return dict(backend='dreamthink_only',gist='Structural DreamThink live experiment',
        candidate=raw,intent='conversational_reply',contradictions=[],should_imprint=False,
        proposed_action=dict(type='respond',content=answer,say=answer,show=answer),
        dreamthink_trace=trace,rationale='Algorithmic synthesis plus literal rendering; sealed identity + PSC/WFC memory as read-only decide fuel; no model fallback or tools.')
def thought(event,authenticated,root=ROOT,*,psc=None,wfc=None):
    if not authenticated or str(event.get('speaker','')).casefold()!='mike':
        return None
    if event.get('ingest') or event.get('training_context') or event.get('source')=='nuance_rehearsal':
        return None
    mode=root/'thought-funnel'/'live-mode.json'
    settings=funnel.read(mode,{})
    if settings.get('enabled') is not True:
        if event.get('source')=='dreamthink_practice':
            return packet(str(event.get('raw','')),'Practice is paused because DreamThink mode is off.',dict(kind='disabled_practice',llm_calls=0))
        return None
    raw=str(event.get('raw',''))[:4000]
    command=raw.lower().strip(' .!?')
    if command in ('normal mode','dreamthink off','turn off dreamthink'):
        funnel.save(mode,dict(enabled=False,changed_at=time.time(),reason='authenticated owner command'))
        SESSIONS.clear()
        return packet(raw,'Normal conversation mode is restored for your next message.',dict(kind='mode_control',llm_calls=0))
    if command in ('dreamthink status','dreamthink is online','your dreamthink mind is online'):
        return packet(raw,"DreamThink is online for this conversation. I can test simple connections from your inputs and dream material. If no coherent connection emerges, I will say so.",dict(kind='mode_status',llm_calls=0))
    # Honor the shared sleep state without affecting the voice implementation.
    rest=funnel.read(root.parent/'timed-sleep.json',{})
    # daychat_smoke: non-waking harness bypass only (does not alter timed-sleep.json).
    _sleep_bypass = event.get('source') in ('dreamthink_practice', 'daychat_smoke') or event.get('daychat_smoke') is True
    if rest.get('task')=='dreamthink_four_hour' and rest.get('state')=='sleeping' and time.time()<rest.get('wake_at',0) and not _sleep_bypass:
        if command in ('wake','wake up','wake up jarvis','jarvis wake up'):
            from timed_sleep import handle
            handle(None,'wake')
            return packet(raw,'I am awake. The scheduled DreamThink practice has stopped.',dict(kind='owner_wake',llm_calls=0))
        return packet(raw,'I am in the scheduled DreamThink sleep session. Say wake up if you want to end it early.',dict(kind='sleep_status',llm_calls=0))
    cfg=funnel.config(funnel.read(root/'thought-funnel'/'config.json',{}))
    if not cfg['enabled'] or funnel.read(root/'config.json',{}).get('enabled',True) is not True:
        return packet(raw,'DreamThink is disabled. I have not switched to the language model. Say normal mode to restore ordinary conversation.',dict(kind='disabled',llm_calls=0))
    # Compositional NO-LLM speech from imprint bank (before extractive recall).
    # day_chat_promote / compositional_speech renderer: attempt for all owner chat,
    # not only procedure-like cues. Kill bars + llm_calls=0 still gate the claim.
    try:
        import speech_render as speech
        promote = (
            settings.get('day_chat_promote') is True
            or str(settings.get('renderer') or '') in ('compositional_speech', 'speech_render')
        )
        if promote or speech.procedure_cues(raw):
            bank_raw=funnel.read(root/'accelerate-imprint-bank.json',[])
            if isinstance(bank_raw,dict):
                bank=list(bank_raw.get('imprints') or [])
            elif isinstance(bank_raw,list):
                bank=list(bank_raw)
            else:
                bank=[]
            # Cheap merge: practice-looking rows from funnel pool as extra imprints.
            try:
                cfg_pool=funnel.config(funnel.read(root/'thought-funnel'/'config.json',{}))
                for row in funnel.pool(root,cfg_pool)[:40]:
                    if not isinstance(row,dict):continue
                    gist=str(row.get('gist') or row.get('memory') or '')
                    if not gist:continue
                    low=gist.lower();prov=str(row.get('provenance') or row.get('source') or '')
                    if ('practice' in low or 'before i' in low or 'i should' in low
                            or prov.upper().startswith('DREAM') or prov.upper().startswith('HYPOTHETICAL')):
                        bank.append(dict(gist=gist,id=row.get('id'),provenance=prov or 'DREAM',hypothetical=True))
            except Exception:
                pass
            # Passive web context: quiet EXTERNAL_CONTEXT fuel for decide/render (not search UX).
            # Default ON when compositional day-chat is promoted; explicit false disables.
            ext_ctx=None
            passive_flag=settings.get('passive_web_context')
            if passive_flag is None:
                passive_flag=True if promote else False
            # Identity/remember-me: local sealed+PSC fuel only — never web for "your name".
            try:
                import identity_wire as _id_skip
                if _id_skip.self_knowledge_cues(raw):
                    passive_flag = False
            except Exception:
                pass
            if passive_flag:
                try:
                    import passive_context as pctx
                    ext_ctx=pctx.lookup(raw,settings=dict(settings,passive_web_context=True))
                    for cand in (ext_ctx.get('candidates') or []):
                        bank.append(cand)
                except Exception:
                    ext_ctx=None
            # READ-ONLY brain fuel: sealed identity + PSC/WFC memory (never LLM).
            try:
                import identity_wire as _idw
                import memory_fuel as _mfuel
                if _idw.self_knowledge_cues(raw):
                    snip = _mfuel.profile_snippet(psc)
                    cand = _idw.identity_candidate(raw, profile_snippet=snip)
                    if cand:
                        bank.append(cand)
                for mc in _mfuel.memory_candidates(raw, psc=psc, wfc=wfc, limit=10):
                    bank.append(mc)
            except Exception:
                pass
            rendered=speech.render(raw,imprint_bank=bank,external_context=ext_ctx)
            ans=str(rendered.get('answer') or '')
            internal=str(rendered.get('internal_thought') or '')
            forbidden=any(b in ans.lower() for b in getattr(speech,'FORBIDDEN_SURFACE',()))
            claim=((rendered.get('compositional') or rendered.get('kill_bar_pass'))
                   and bool(ans) and rendered.get('llm_calls',0)==0
                   and not forbidden and not rendered.get('refused'))
            if claim:
                now=time.time()
                kill_keys=('clause_count','receipt_count','attribution_density','unique_relation_ids',
                           'unique_template_ids','unique_note_ids','unique_surface_strings',
                           'relation_diversity_ok','density_ok','kill_bar_pass','kill_reasons')
                kill_metrics={k:rendered[k] for k in kill_keys if k in rendered}
                passive_meta={}
                if isinstance(ext_ctx,dict):
                    passive_meta=dict(
                        passive_triggered=bool(ext_ctx.get('triggered')),
                        passive_ok=bool(ext_ctx.get('ok')),
                        passive_skipped=ext_ctx.get('skipped'),
                        passive_elapsed_ms=ext_ctx.get('elapsed_ms'),
                        passive_snippet_n=len(ext_ctx.get('snippets') or []),
                        passive_used=bool(rendered.get('external_context_used')),
                    )
                trace=dict(timestamp=now,input=raw,source='owner_live_input',kind='compositional_speech',
                    method=rendered.get('method'),llm_calls=0,compositional=True,
                    receipts=rendered.get('receipts'),fingerprint=rendered.get('fingerprint'),
                    imprint_bank_size=rendered.get('imprint_bank_size'),utilization=rendered.get('utilization'),
                    internal_thought=internal,spoken_move=ans,
                    **kill_metrics,**passive_meta)
                try:funnel.save(root/'thought-funnel'/'live-chat-latest.json',trace)
                except OSError:pass
                return packet(raw,ans,dict(kind='compositional_speech',method=rendered.get('method'),
                    llm_calls=0,compositional=True,receipts=rendered.get('receipts'),
                    **kill_metrics,**passive_meta))
    except Exception:
        pass
    from dreamthink_recall import recall
    recalled=recall(raw,psc,wfc,event)
    if recalled is not None:
        try:
            funnel.save(root/'thought-funnel'/'live-recall-latest.json',dict(timestamp=time.time(),input=raw,**recalled))
        except OSError:pass
        ans=str(recalled.get('answer') or '')
        try:
            import speech_render as speech
            low=ans.lower()
            if any(b in low for b in speech.FORBIDDEN_SURFACE) and speech.procedure_cues(raw):
                body=ans
                for bad in speech.FORBIDDEN_SURFACE:
                    body=re.sub(re.escape(bad)+r'\s*:?\s*','',body,flags=re.I)
                body=speech.strip_wrappers(body.strip())
                if body and not body.lower().startswith('a hypothetical practice lesson suggests'):
                    ans='A hypothetical practice lesson suggests: '+(body[0].lower()+body[1:] if body[0].isupper() else body)
                elif body:
                    ans=body
        except Exception:
            pass
        return packet(raw,ans,dict(kind='read_only_recall',method=recalled['method'],llm_calls=0))
    now=time.time();key=str(event.get('session_id','owner'))[:160]
    prior=SESSIONS.pop(key,[])
    prior=[r for r in prior if now-r['received_at']<600][-6:]
    current=[]
    # Input fragments are asserted premises, never independent verified facts.
    for i,clause in enumerate(re.split(r'[.;\n]',raw)[:8]):
        if funnel.TEXT_REL.fullmatch(clause.strip()):
            current.append(dict(id='input-'+funnel.digest([key,raw,i]),gist=clause.strip(),
                provenance='OPERATOR_PREMISE_NOT_VERIFIED',received_at=now))
    SESSIONS[key]=(prior+current)[-8:]
    while len(SESSIONS)>8:SESSIONS.popitem(last=False)
    query=words(raw)
    dreams=funnel.pool(root,cfg)
    dreams=[r for r in dreams if len(query & words(r.get('gist','')))>=2]
    dreams.sort(key=lambda r:len(query & words(r.get('gist',''))),reverse=True)
    inputs=(prior+current+dreams)[:cfg['max_states']]
    result=funnel.synthesize(inputs,settings=cfg)
    candidates=sorted(result['thoughts'],key=lambda t:len(query & set(t['contributing_concepts'])),reverse=True)
    selected=next((t for t in candidates if query & set(t['contributing_concepts'])),None)
    if selected:
        r=selected['relationship'];a=r['subject'].replace('_',' ');b=r['object'].replace('_',' ')
        if r['predicate']=='associated':
            answer=f"My dream material links {a} with {b}. That is a tentative association, not yet an explanation or a verified fact."
        else:
            verb={'requires':'depends on','precedes':'comes before','is_a':'is a kind of'}[r['predicate']]
            answer=f"If those premises hold, {a} {verb} {b}."
        if result['contradictions']:answer+=' Other conflicting branches were withheld.'
    elif result['contradictions']:
        answer='Those fragments conflict, so I am withholding a conclusion rather than choosing a side.'
    elif current:
        answer='I have that as a temporary premise. I do not yet have enough connected material to derive a new relationship.'
    else:
        answer='I have not formed a coherent DreamThink response to that yet. I am not filling the gap with a language-model answer.'
    trace=dict(timestamp=now,input=raw,source='owner_live_input',session_id=key,
        selected=selected,result=result,llm_calls=0,kind='structural_synthesis')
    try:
        # Only latest owner trace: bounded diagnostic, never fed to PSC or dream pool.
        funnel.save(root/'thought-funnel'/'live-chat-latest.json',trace)
    except OSError:pass
    return packet(raw,answer,dict(kind='structural_synthesis',selected_id=selected['id'] if selected else None,
        llm_calls=0,status=result['status'],resources=result['resources']))
