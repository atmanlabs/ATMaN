"""Bounded extractive recall for DreamThink; no generation or memory writes."""
import collections
import hashlib
import math
import re
import time

STOP=set('what which who where when how did do does have has had you your yours me my mine i we us our about tell please remember recall know learned practice practiced game the a an and or is are was were to in of from with that this it just before last said'.split())
ALIASES={'recollections':'memory','memories':'memory','recollection':'memory','recalled':'memory',
 'practicing':'training','practised':'training','practiced':'training','practice':'training',
 'trained':'training','lessons':'lesson','files':'file','documents':'file','document':'file',
 'spouse':'partner','wife':'partner','husband':'partner','married':'partner',
 'gaming':'game','games':'game','word':'semantic','meaning':'semantic','match':'semantic'}
def concepts(text):
    words=re.findall(r"[a-z][a-z0-9_]{1,35}",text.lower())
    return {ALIASES.get(w,w) for w in words if w not in STOP}
def is_query(text):
    return bool(re.search(r'\b(?:remember|recall|know about|tell me about|what did|what have|what was|who is|where do|where did)\b',text,re.I))
def procedure_query(text):
    return bool(re.search(r'\b(?:how|should|before|would|need)\b',text,re.I)
                and re.search(r'\b(?:file|files|summarize|read|follow|minecraft|move|action|tool|plan|improve|change|respond|greeting|disclosure|verify|verification)\b',text,re.I))

def strip_saved_notes_surface(answer, procedural=False):
    """Strip forbidden extractive framing on practice/procedural replies."""
    if not isinstance(answer, str):
        return answer
    out = answer.strip()
    out = re.sub(r'(?i)^my saved notes say:\s*', '', out)
    out = re.sub(r'(?i)\bmy saved notes say:\s*', '', out)
    out = re.sub(r'(?i)^my notes say:\s*', '', out)
    if procedural:
        body = out.strip()
        if body and not body.lower().startswith('a hypothetical practice lesson suggests'):
            if body[0].isupper():
                body = body[0].lower() + body[1:]
            out = 'A hypothetical practice lesson suggests: ' + body
    return out
def clean(text):
    from semantic_practice import clean_note,plain
    if not isinstance(text,str):return None
    text=clean_note(text[:6000])
    if re.search(r'password|bearer\s|api[_ -]?key|access[_ -]?token|[A-Z]:\\|https?://',text,re.I):return None
    return text if plain(text) else None
def recall(raw,psc,wfc,event):
    if not is_query(raw) and not procedure_query(raw):return None
    if re.search(r'\b(?:just|earlier|last|before)\b.*\b(?:tell|told|say|said|ask|asked)\b',raw,re.I):
        rows=[r for r in list(wfc or [])[-50:] if isinstance(r,dict) and r.get('raw')!=raw
              and str(r.get('session_id','default'))==str(event.get('session_id','default'))
              and str(r.get('speaker','')).casefold()=='mike']
        note=next((clean(r.get('raw')) for r in reversed(rows) if clean(r.get('raw'))),None)
        return dict(answer='Earlier you said: '+note if note else 'I do not have an earlier message from this conversation available to recall.',
                    evidence=[dict(kind='session_message',text=note)] if note else [],method='same_session_extract',llm_calls=0)
    if psc is None:return dict(answer='My saved notes are not available to this DreamThink session.',evidence=[],method='unavailable',llm_calls=0)
    try:rows=list(psc.memories)[-2500:]
    except Exception:return dict(answer='I could not read my saved notes reliably.',evidence=[],method='unavailable',llm_calls=0)
    from training_receipts import records
    rows+=records()
    terms=concepts(raw);passages=[]
    for row in rows:
        if not isinstance(row,dict):continue
        source=str(row.get('source',''))
        procedural = procedure_query(raw)
        practice_marker='[DREAMTHINK PRACTICE - tentative procedure, not an event] '
        practice=(source.startswith('DREAM:SLEEP:') and str(row.get('memory','')).startswith(practice_marker) and procedural)
        if (source.startswith('DREAM') or row.get('category')=='dream_hypothesis') and not practice:continue
        if practice:row=dict(row,memory='A tentative practice lesson suggests: '+row['memory'][len(practice_marker):])
        if row.get('category')=='experience' and source=='tool_outcome':continue
        note=clean(row.get('memory'))
        if not note:continue
        for sentence in re.split(r'(?<=[.!?])\s+',note)[:12]:
            tokens=concepts(sentence)
            overlap=terms & tokens
            if not overlap:continue
            passages.append(dict(text=sentence,tokens=tokens,overlap=overlap,
                id=row.get('id') or hashlib.sha256(note.encode()).hexdigest()[:20],
                source=source or 'saved_note',timestamp=row.get('t')))
    if not passages:
        return dict(answer='I could not find a clear matching note. Can you give me a name or topic to narrow it down?',
                    evidence=[],method='bounded_concept_retrieval',llm_calls=0)
    df=collections.Counter(t for p in passages for t in p['tokens'])
    for p in passages:
        p['score']=sum(1+math.log((len(passages)+1)/(df[t]+1)) for t in p['overlap'])/max(1,len(terms))
        if p['source']=='training_report_adapter':p['score']+=.25
    passages.sort(key=lambda p:p['score'],reverse=True)
    selected=[];seen=set()
    for p in passages:
        normalized=' '.join(p['text'].lower().split())
        if normalized in seen:continue
        seen.add(normalized);selected.append(p)
        if len(selected)==2:break
    # Exact, cleaned evidence in plain sentences; never invented bridging claims.
    # Practice/procedural path: hyp-tag, never forbidden "My saved notes say".
    body=' '.join(p['text'] for p in selected)
    procedural=procedure_query(raw) or any(str(p.get('source','')).startswith('DREAM') or 'practice' in str(p.get('text','')).lower() for p in selected)
    if procedural:
        answer=strip_saved_notes_surface('My saved notes say: '+body, procedural=True)
    else:
        answer='My saved notes say: '+body
    evidence=[{k:v for k,v in p.items() if k not in ('tokens','overlap')} for p in selected]
    return dict(answer=answer,evidence=evidence,method='bounded_concept_retrieval',llm_calls=0,
                limitation='Extractive synonym matching, not unrestricted semantic understanding.')
