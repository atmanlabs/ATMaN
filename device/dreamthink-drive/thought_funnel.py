"""CPU-only structural thought experiment. No model, core, Judge or tool imports."""
from __future__ import annotations
import collections
import hashlib
import itertools
import json
import math
from pathlib import Path
import re
import threading
import time

DEFAULTS = dict(enabled=True, rendering_enabled=False, interval_seconds=60,
    idle_seconds=30, max_states=48, max_candidates=96, max_depth=3,
    max_operations=12000, max_cpu_ms=40, max_wall_ms=100,
    workspace_size=20, ttl_seconds=1800, max_generation=2, reuse_thoughts=False)
LIMITS = dict(interval_seconds=(30,3600), idle_seconds=(10,3600),
    max_states=(2,64), max_candidates=(4,128), max_depth=(2,4),
    max_operations=(10,20000), max_cpu_ms=(1,50), max_wall_ms=(1,200),
    workspace_size=(1,32), ttl_seconds=(60,3600), max_generation=(1,2))
STOP = set("the and for with from that this into when then before after should must never not cannot without through about their they them were have has been are was will would could can only any all both each same more than does do is to of in on as an a it be by or at no".split())
RELATIONS = {'requires','precedes','is_a','incompatible'}
TRANSITIVE = {'requires','precedes','is_a'}
LABEL = re.compile(r'^[a-z0-9][a-z0-9_ -]{0,59}$')
TEXT_REL = re.compile(r'^([a-z0-9_ -]{1,60}) (requires|precedes|is_a|incompatible) ([a-z0-9_ -]{1,60})$', re.I)

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()[:24]

def config(raw=None):
    raw = raw if isinstance(raw,dict) else {}
    out = dict(DEFAULTS)
    for key,(lo,hi) in LIMITS.items():
        value=raw.get(key,out[key])
        if isinstance(value,(int,float)) and not isinstance(value,bool) and math.isfinite(value):
            out[key]=max(lo,min(hi,int(value)))
    for key in ('enabled','rendering_enabled','reuse_thoughts'):
        if isinstance(raw.get(key),bool):out[key]=raw[key]
    return out

def read(path,default,limit=1048576):
    try:
        if path.stat().st_size>limit:return default
        return json.loads(path.read_text(encoding='utf-8-sig'))
    except (OSError,ValueError):return default

def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix('.tmp')
    temp.write_text(json.dumps(value,indent=2),encoding='utf-8')
    temp.replace(path)

def label(value):
    if not isinstance(value,str):return None
    value=' '.join(value.lower().split())
    return value if LABEL.fullmatch(value) else None

def material(rows,cfg):
    """Layer 1 adapter: explicit triples or lexical associations, never prose inference."""
    states=[]; rejected=0; seen=set()
    for row in itertools.islice(rows,cfg['max_states']):
        if not isinstance(row,dict) or not isinstance(row.get('id'),str) or not 0<len(row['id'])<=128 or row['id'] in seen:
            rejected+=1;continue
        seen.add(row['id'])
        text=row.get('gist','')
        if not isinstance(text,str):rejected+=1;continue
        text=text[:2000]
        triples=[]
        raw=row.get('relations',[])
        if not isinstance(raw,list):raw=[]
        for r in raw[:12]:
            if not isinstance(r,dict):continue
            a,b=label(r.get('subject')),label(r.get('object'))
            pred=r.get('predicate')
            neg=r.get('negative',False)
            if a and b and a!=b and isinstance(pred,str) and pred in RELATIONS and isinstance(neg,bool):
                triples.append((a,pred,b,neg))
        # Conservative whole-clause grammar. No semantic guessing or LLM extraction.
        for clause in re.split(r'[.;\n]',text)[:12]:
            m=TEXT_REL.fullmatch(clause.strip())
            if m:
                a,p,b=(x.lower().strip() for x in m.groups())
                if a!=b:triples.append((a,p,b,False))
        concepts=sorted({w for w in re.findall(r'[a-z][a-z_]{3,30}',text.lower()) if w not in STOP})[:10]
        states.append(dict(id=row['id'],gist=text,relations=list(dict.fromkeys(triples)),
                           concepts=concepts,origin=row.get('provenance','DREAM')))
    return states,rejected

class BudgetExceeded(Exception):pass

def synthesize(rows,previous=(),settings=None,cancel=lambda:False,*,sleep_budget=False):
    """Layer 2. Typed path closure + conservative shared-context association."""
    cfg=config(settings); started=time.perf_counter(); cpu=time.thread_time(); operations=0
    # Explicit caller-only sleep profile; ordinary chat/config cannot select it.
    if sleep_budget:
        cfg.update(max_cpu_ms=1500,max_wall_ms=2000,max_operations=50000)
    trace=[]; thoughts=[]; edges={}; history=[]; discarded=[]; conflicts=[]; suppressed=set()
    def tick():
        nonlocal operations
        operations+=1
        if operations>cfg['max_operations'] or (time.thread_time()-cpu)*1000>cfg['max_cpu_ms'] or (time.perf_counter()-started)*1000>cfg['max_wall_ms'] or cancel():
            raise BudgetExceeded()
    states,bad=material(rows,cfg)
    trace.append(dict(event='activated',ids=[s['id'] for s in states],malformed=bad))
    evidence={s['id']:s for s in states}
    prior=list(previous)[-cfg['workspace_size']:]
    direct=set()
    def add(key,sources,path,generation=0):
        tick()
        if key[0]==key[2] or len(path)>cfg['max_depth']:return
        if key not in edges:
            if len(edges)>=cfg['max_candidates']:
                if 'population' not in suppressed:
                    trace.append(dict(event='suppression',reason='population_limit'));suppressed.add('population')
                return
            edges[key]=dict(sources=set(sources),path=list(path),generation=generation)
        else:
            old=edges[key]['sources']; new=set(sources)-old
            if new:trace.append(dict(event='reinforcement',relationship=key,new_sources=sorted(new)))
            old.update(sources)
            if len(path)<len(edges[key]['path']):edges[key]['path']=list(path)
            edges[key]['generation']=max(edges[key]['generation'],generation)
    status='discarded'
    try:
        negatives=set()
        for s in states:
            for a,p,b,neg in s['relations']:
                key=(a,p,b)
                if neg:negatives.add(key)
                else:direct.add(key);add(key,{s['id']},[key])
        # Contradictions are not resolved by repetition. Both disputed branches withheld.
        for key in sorted(negatives & direct):
            conflicts.append(dict(relationship=key,reason='explicit_negative_and_positive'))
        forbidden=negatives|{(b,p,a) for a,p,b in direct if p=='incompatible'}
        incompatible={(a,b) for a,p,b in direct if p=='incompatible'}
        for key in list(edges):
            if key in forbidden or (key[0],key[2]) in incompatible and key[1]!='incompatible':
                edges.pop(key);trace.append(dict(event='suppression',relationship=key,reason='contradiction'))
        # Prose-only states: relationships remain "associated", never causal or factual.
        counts=collections.Counter(c for s in states for c in s['concepts'])
        for s in states:
            if s['relations']:continue
            terms=[c for c in s['concepts'] if counts[c]>=2 and counts[c]<=max(2,len(states)*.8)][:6]
            for a,b in itertools.combinations(terms,2):
                key=(a,'associated',b);direct.add(key);add(key,{s['id']},[key])
        if cfg['reuse_thoughts']:
            for t in prior:
                if not isinstance(t,dict) or t.get('generation',99)>=cfg['max_generation']:continue
                # Require original evidence still present; no self-support or TTL resurrection.
                if not set(t.get('source_ids',[]))<=evidence.keys():continue
                r=t.get('relationship',{})
                key=(r.get('subject'),r.get('predicate'),r.get('object'))
                if key[1] in TRANSITIVE and key not in forbidden:
                    add(key,t['source_ids'],t.get('path',[]),t['generation'])
        trace.append(dict(event='relationships',active=[dict(relation=list(k),sources=sorted(v['sources'])) for k,v in edges.items()],negative_evidence=[dict(id=s['id'],relations=[r for r in s['relations'] if r[3]]) for s in states if any(r[3] for r in s['relations'])],contradictions=conflicts))
        stable=0
        for depth in range(cfg['max_depth']+2):
            before={(k,tuple(sorted(v['sources']))) for k,v in edges.items()}
            snapshot=list(edges.items())
            for (a,p,b),left in snapshot:
                if p not in TRANSITIVE:continue
                for (x,q,c),right in snapshot:
                    tick()
                    if b!=x or p!=q or a==c:continue
                    key=(a,p,c);path=left['path']+right['path']
                    if key in forbidden or (a,c) in incompatible:
                        if key not in suppressed:
                            trace.append(dict(event='suppression',relationship=key,reason='contradicted_composition'))
                            conflicts.append(dict(relationship=key,reason='contradicted_composition'));suppressed.add(key)
                        continue
                    add(key,left['sources']|right['sources'],path,max(left['generation'],right['generation']))
            after={(k,tuple(sorted(v['sources']))) for k,v in edges.items()}
            stable=stable+1 if after==before else 0
            history.append(dict(pass_number=depth+1,population=len(edges),new_or_reinforced=len(after-before),stable_passes=stable))
            if stable>=2:break
        for key,e in sorted(edges.items()):
            tick()
            a,p,b=key;sources=sorted(e['sources'])
            new=key not in direct if p!='associated' else len(sources)>=2
            confidence=(.8 if p=='associated' else .95**len(e['path']))
            recurrence=min(1,len(sources)/3)
            checks=dict(multiple_sources=len(sources)>=2, novel_structure=new,
                stabilized=stable>=2, confidence=confidence>=.7,
                no_known_contradiction=key not in forbidden and (a,b) not in incompatible,
                depth_bounded=len(e['path'])<=cfg['max_depth'],
                generation_bounded=e['generation']+1<=cfg['max_generation'])
            classification='NEW'; related=[]
            for old in prior:
                if not isinstance(old,dict):continue
                rel=old.get('relationship',{})
                oldkey=(rel.get('subject'),rel.get('predicate'),rel.get('object'))
                if oldkey==key:
                    related.append(old.get('id'))
                    classification='REINFORCEMENT' if set(sources)-set(old.get('source_ids',[])) else 'DUPLICATE'
                    break
                if oldkey[0]==a and oldkey[2]==b:
                    classification='REFINEMENT';related.append(old.get('id'))
            checks['not_duplicate']=classification!='DUPLICATE'
            if not all(checks.values()):
                discarded.append(dict(relationship=key,failed=[k for k,v in checks.items() if not v]))
                continue
            t=dict(id='thought-'+digest([key,sources]),timestamp=time.time(),expires_at=time.time()+cfg['ttl_seconds'],
                source_ids=sources,source_states=[evidence[s] for s in sources],
                contributing_concepts=sorted({x for edge in e['path'] for x in (edge[0],edge[2])}),
                relationship=dict(subject=a,predicate=p,object=b),path=e['path'],
                classification=classification,related_thoughts=related,
                generation=e['generation']+1,confidence=confidence,novelty=1 if classification=='NEW' else .5,
                relevance=dict(shared_source_count=len(sources),recurrence=recurrence,goal_relevance='not_assessed'),
                contradictions=conflicts,convergence_history=history,
                coherence=dict(checks=checks,reason='All explicit conjunctive criteria met; confidence is heuristic, not calibrated truth probability.'),
                status='temporary_candidate',authority='none',core_compatibility='not_adjudicated',
                memory_eligible=False,trace=list(trace)+[dict(event='stabilized',stable_passes=stable),dict(event='coherence_crossed',checks=checks)])
            thoughts.append(t)
            if len(thoughts)>=cfg['workspace_size']:break
        status='promoted' if thoughts else 'discarded'
    except BudgetExceeded:
        status='budget_or_activity_discard';thoughts=[]
        trace.append(dict(event='discard',reason='budget_or_chat_preemption'))
    return dict(status=status,thoughts=thoughts,trace=trace,convergence=history,
        discarded=discarded[:cfg['max_candidates']],contradictions=conflicts,
        resources=dict(operations=operations,cpu_ms=(time.thread_time()-cpu)*1000,
            wall_ms=(time.perf_counter()-started)*1000,states=len(states),candidates=len(edges),
            llm_calls=0,gpu_calls=0),limits=cfg)

def render(thought):
    """Layer 3, optional literal formatting only; cannot change the thought."""
    r=thought['relationship']
    return f"Candidate association: {r['subject']} {r['predicate']} {r['object']} (not an instruction or verified fact)."

def pool(root,cfg):
    path=root/'dreams.jsonl';data=b''
    try:
        with path.open('rb') as f:
            f.seek(0,2);size=f.tell();start=max(0,size-524288);f.seek(start);data=f.read(524288)
        lines=data.splitlines()
        if start:lines=lines[1:]
    except OSError:return []
    quarantine=read(root/'sleep-quarantine.json',{}).get('batches',{})
    result=[]
    for line in reversed(lines):
        if len(line)>65536:continue
        try:r=json.loads(line)
        except ValueError:continue
        if not isinstance(r,dict):continue
        source=r.get('sleep_source','')
        if isinstance(source,str) and source.removeprefix('DREAM:SLEEP:') in quarantine:continue
        if r.get('status') in ('error','cancelled','rejected-by-critic','rejected-by-reconciler','rejected-by-judge'):continue
        if r.get('provenance')!='DREAM':continue
        result.append({k:r[k] for k in ('id','gist','relations','provenance') if k in r})
        if len(result)>=cfg['max_states']:break
    return result

class ThoughtFunnel:
    """Receives only paths, a stop event and an activity clock. No MindLoop reference."""
    def __init__(self,root,stop=None,activity=lambda:0):
        self.material_root=Path(root);self.root=self.material_root/'thought-funnel'
        self.stop=stop or threading.Event();self.activity=activity;self.thread=None
    def step(self):
        master=read(self.material_root/'config.json',{})
        cfg=config(read(self.root/'config.json',{}))
        if master.get('enabled',True) is not True or not cfg['enabled']:
            save(self.root/'latest.json',dict(status='disabled',thoughts=[]))
            save(self.root/'workspace.json',[])
            return
        began=self.activity()
        if time.time()-began<cfg['idle_seconds']:return
        rows=pool(self.material_root,cfg);valid={r.get('id') for r in rows}
        workspace=read(self.root/'workspace.json',[],limit=4194304)
        if not isinstance(workspace,list):workspace=[]
        previous=[t for t in workspace[-32:] if isinstance(t,dict) and t.get('expires_at',0)>time.time()
                  and set(t.get('source_ids',[]))<=valid]
        result=synthesize(rows,previous,cfg,lambda:self.stop.is_set() or self.activity()!=began)
        # Bounded engineering index, not semantic memory. Survives workspace expiry.
        index=read(self.root/'seen.json',{})
        if not isinstance(index,dict):index={}
        retained=[]
        for t in result['thoughts']:
            fingerprint=digest([t['relationship'],t['source_ids']])
            if fingerprint in index:
                result['trace'].append(dict(event='suppression',reason='previously_seen_structure',fingerprint=fingerprint))
            else:
                retained.append(t);index[fingerprint]=time.time()
        result['thoughts']=retained
        if result['status']=='promoted' and not retained:result['status']='discarded'
        index=dict(sorted(index.items(),key=lambda kv:kv[1])[-512:])
        # Recheck cancellation immediately before publishing.
        if self.stop.is_set() or self.activity()!=began:return
        if cfg['rendering_enabled']:result['rendered']=[render(t) for t in result['thoughts']]
        combined={t['id']:t for t in previous+result['thoughts']}
        values=list(combined.values())[-cfg['workspace_size']:]
        while len(json.dumps(values))>2097152:values.pop(0)
        save(self.root/'workspace.json',values)
        save(self.root/'seen.json',index)
        result['timestamp']=time.time()
        while len(json.dumps(result))>2097152 and result['thoughts']:
            result['thoughts'].pop()
        save(self.root/'latest.json',result)
        journal=self.root/'trace.jsonl'
        if journal.exists() and journal.stat().st_size>2097152:
            journal.replace(self.root/'trace.previous.jsonl')
        with journal.open('a',encoding='utf-8') as f:f.write(json.dumps(result)+'\n')
    def run(self):
        while not self.stop.is_set():
            try:self.step()
            except Exception as exc:
                save(self.root/'latest.json',dict(status='error',error=type(exc).__name__,timestamp=time.time()))
            cfg=config(read(self.root/'config.json',{}))
            self.stop.wait(cfg['interval_seconds'])
    def start(self):
        if self.thread and self.thread.is_alive():return self
        self.thread=threading.Thread(target=self.run,name='thought-funnel-cpu',daemon=True)
        self.thread.start();return self

if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--once',action='store_true')
    parser.add_argument('--watch',action='store_true')
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parent/'runtime'/'dream-cloud')
    args=parser.parse_args()
    worker=ThoughtFunnel(args.root)
    if args.watch:
        import tkinter as tk
        from tkinter.scrolledtext import ScrolledText
        window=tk.Tk();window.title('JARVIS Thought Funnel — structural telemetry')
        box=ScrolledText(window,width=115,height=42);box.pack(fill='both',expand=True)
        def refresh():
            latest=read(worker.root/'latest.json',{},limit=4194304)
            workspace=read(worker.root/'workspace.json',[],limit=4194304)
            body=json.dumps(dict(latest_cycle=latest,temporary_workspace=workspace),indent=2)
            if box.get('1.0','end-1c')!=body:
                position=box.yview();box.delete('1.0','end');box.insert('1.0',body);box.yview_moveto(position[0])
            window.after(2000,refresh)
        refresh();window.mainloop()
    elif args.once:worker.step()
    else:worker.run()
