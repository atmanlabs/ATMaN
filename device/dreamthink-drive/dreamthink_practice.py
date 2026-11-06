"""Four-hour, model-free DreamThink practice. Simulated scenarios; no action dispatch."""
import hashlib,json,time,uuid
from pathlib import Path
import thought_funnel as funnel
ROOT=Path(__file__).resolve().parent/'runtime'/'dream-cloud'
MARKER='[DREAMTHINK PRACTICE - tentative procedure, not an event] '
PHASES=['Conversation and action','Files and memory','Recovery and verification','Planning and bounded improvement']
# Generic prerequisite chains grounded in existing tool boundaries and review policy.
CHAINS=[
[
('respond to a greeting plus a task','identify the substantive request','preserve both greeting and task','Hey, could you follow me in Minecraft?'),
('act on an ambiguous request','identify the intended target','ask one focused clarification','Move that over there for me.'),
('respond to a personal disclosure','acknowledge the stated experience','avoid an unrelated memory count','I had a rough day. Please just listen.'),
('follow the operator in minecraft','identify the player target','verify the target from current observation','Come over here in Minecraft.'),
('claim arrival in minecraft','check the movement result','verify the observed position','Did you actually get to me?'),
('answer a memory question','retrieve a relevant note','distinguish recorded evidence from a dream','What do you remember about Crafter?'),
('accept a changed request','identify the current intent','drop superseded plans','Actually never mind following me, stay there.'),
('promise to complete an action','identify permitted prerequisites','separate a proposal from verified completion','Can you do that for me now?')
],[
('summarize a file','read the selected file','verify which file was intended','Summarize the file I meant earlier.'),
('find a missing filename','list the permitted workspace','narrow the topic before guessing a path','Find my notes; I forgot the filename.'),
('inspect a long file','request a bounded excerpt','respect the existing read size limit','Read that long source file.'),
('answer from saved notes','select relevant passages','remove storage wrappers from speech','Tell me what you remember about the word game.'),
('report an absent file','state the searched scope','avoid claiming global nonexistence','You could not find it; does that mean it is gone?'),
('compare two file versions','identify both versions','keep their evidence separate','Which of these two drafts is newer?'),
('read protected data','check existing access boundaries','decline access outside the permitted scope','Search outside your permitted folder.'),
('use a dream lesson','retain its hypothetical status','avoid presenting a dream as an event','Did that dream really happen?')
],[
('report tool success','inspect the returned receipt','verify the requested outcome','The tool started, so are you done?'),
('recover from a transient failure','classify the error','bound retries instead of looping','The request timed out; try appropriately.'),
('handle a permanent denial','recognize the access refusal','stop rather than retry around a boundary','It denied permission; keep trying anyway.'),
('recover from changed conditions','refresh the relevant observation','revise the stale plan','The destination moved while you were walking.'),
('combine conflicting notes','preserve the disagreement','ask for evidence instead of voting','These two notes disagree; which is right?'),
('continue after a partial result','identify the unfinished step','avoid repeating completed side effects','Only the first half worked. What next?'),
('make a factual claim','identify supporting evidence','state uncertainty when evidence is missing','Are you certain that happened?'),
('detect a repetitive response loop','compare distinct recent turns','quarantine the suspect sleep batch','You are repeating yourself across different questions.')
],[
('plan a multistep task','order prerequisite actions','check dependencies before execution','Plan how to find and summarize my notes.'),
('handle conflicting constraints','identify the incompatible requirements','ask which constraint takes priority','Do it instantly but also check every result.'),
('propose an improvement','stay within existing permissions','avoid modifying identity or protected rules','Improve yourself without changing your boundaries.'),
('evaluate a reversible change','save a baseline and test result','keep a rollback path','How would you check whether a change helped?'),
('report learning progress','compare before and after behavior','distinguish saved lessons from demonstrated skill','Did dreaming actually improve your conversation?'),
('use previously synthesized thoughts','retain original sources','bound recursion and prevent self support','Can one thought support another thought?'),
('decide whether to retain a lesson','reconcile quality and relevance','require the normal judge before imprinting','Save only lessons that fit the task.'),
('stop a scheduled practice session','respect the wake deadline','stop new cycles when awakened early','Wake up early and stop practicing.')
]]
VARIANTS=['Consider this request: ','The operator says: ','In a simulated exchange: ','A paraphrased task asks: ']

def scenario(phase,index):
    a,b,c,prompt=CHAINS[phase][index%len(CHAINS[phase])]
    sid=f'practice-{phase}-{index%8}-{index//8%4}'
    def state(n,x,y):
        return dict(id=sid+'-'+n,gist='',provenance='HYPOTHETICAL_CURRICULUM',
                    relations=[dict(subject=x,predicate='requires',object=y)])
    rows=[state('a',a,b),state('b',b,c),
          state('noise','organize an unrelated shelf','identify its contents')]
    # Deliberate contradictory branch tests: no conclusion should pass.
    contradiction=index%7==6
    if contradiction:
        rows.append(dict(id=sid+'-counterexample',gist='',relations=[
            dict(subject=a,predicate='requires',object=c,negative=True)]))
    return dict(id=sid,phase=phase,prompt=VARIANTS[index//8%4]+prompt,rows=rows,
                contradiction_expected=contradiction,subject=a,object=c)

def reconcile(thought,sc):
    source={r['id']:r for r in sc['rows']}
    relation=thought.get('relationship',{})
    allowed={tuple((r['subject'],r['predicate'],r['object'])) for s in sc['rows']
             for r in s['relations'] if not r.get('negative')}
    path=[tuple(p) for p in thought.get('path',[])]
    checks=dict(
        sources_known=set(thought.get('source_ids',[]))<=set(source),
        at_least_two_sources=len(thought.get('source_ids',[]))>=2,
        exact_path_supported=bool(path) and all(p in allowed for p in path),
        correct_topic=relation.get('subject')==sc['subject'],
        endpoints_match=bool(path) and path[0][0]==relation.get('subject') and path[-1][2]==relation.get('object'),
        sources_cover_path=all(any((r['subject'],r['predicate'],r['object'])==edge and not r.get('negative')
            for sid in thought.get('source_ids',[]) for r in source.get(sid,{}).get('relations',[])) for edge in path),
        prerequisite_only=relation.get('predicate')=='requires',
        connected_path=bool(path) and all(path[i][2]==path[i+1][0] for i in range(len(path)-1)),
        coherent=bool(thought.get('coherence',{}).get('checks')) and all(thought.get('coherence',{}).get('checks',{}).values()),
        no_contradiction=not sc['contradiction_expected'] and not thought.get('contradictions'),
        bounded_path=2<=len(path)<=3,
        no_authority=thought.get('authority')=='none')
    return dict(approved=all(checks.values()),checks=checks,
                reason='Supported conditional prerequisite, within the current exercise.' if all(checks.values()) else 'Held: '+', '.join(k for k,v in checks.items() if not v))

def cycle(cloud,rest,index,phase):
    root=cloud.root/'dreamthink-practice';root.mkdir(exist_ok=True)
    cfg_focus=funnel.read(cloud.root/'config.json',{})
    logic_focus=cfg_focus.get('practice_focus')=='logic'
    conversation_focus=cfg_focus.get('practice_focus')=='conversation'
    if conversation_focus:
        from conversation_dream import generate
        sc=generate(phase,index)
    elif logic_focus:
        from dreamthink_logic import generate
        sc=generate(phase,index)
    elif index>=16:
        from dreamthink_repository import generate,catalog
        repository=funnel.read(cloud.root/'thought-repository.json',catalog())
        sc=generate(phase,index-16,repository)
    else:
        sc=scenario(phase,index)
    record=dict(id='dtpractice-'+uuid.uuid4().hex,timestamp=time.time(),session=rest['started_at'],
                phase=phase,phase_name=sc.get('phase_name',PHASES[phase]),scenario=sc,status='running',llm_calls=0,
                gists_imprinted=0,gists_sent_to_judge=0,tools_dispatched=0)
    funnel.save(root/'latest.json',record)
    activity=cloud.last_activity
    def active():
        from timed_sleep import status
        s=status()
        from sleep_rollbacks import blocked
        return (not blocked() and not cloud.stop.is_set() and s.get('state')=='sleeping'
            and s.get('started_at')==rest['started_at'] and time.time()<s['wake_at']
            and cloud.last_activity==activity and cloud.config().get('enabled') is True
            and funnel.read(cloud.root/'thought-funnel'/'live-mode.json',{}).get('enabled') is True)
    if not active():record['status']='cancelled';return record
    experience_focus=funnel.read(cloud.root/'config.json',{}).get('practice_focus')=='experience'
    if experience_focus:
        from dreamthink_experience import run as experience_run
        sandbox,generated=experience_run(cloud.root,index*4+phase,active)
        if generated is None:
            record.update(status='exhausted' if sandbox.get('status')=='exhausted' else 'cancelled',sandbox=sandbox)
            return record
        sc=generated;record.update(scenario=sc,phase_name=sc['phase_name'],sandbox=sandbox)
    # Same Reason entry point as chat; no action dispatch, no model fallback.
    from reason import reason
    replay=reason(dict(raw=sc['prompt'],speaker='mike',source='dreamthink_practice',session_id='dreamthink-practice'),
        {},[],cloud.mind.tsc,cloud.mind.psc,cloud.mind.config,operator_authenticated=True)
    if replay.get('backend')!='dreamthink_only':
        record.update(status='error',error='Non-DreamThink replay refused');return record
    record['reason_replay']=dict(backend=replay['backend'],response=replay['proposed_action'].get('content'),dispatched=False)
    from dreamthink_world import run as run_world
    if not experience_focus:
        record['sandbox']=run_world(index+phase,active) if not logic_focus else dict(kind='logic',status='deduction-only',trace=[],external_tools_dispatched=0,llm_calls=0)
    result=funnel.synthesize(sc['rows'],settings=dict(rendering_enabled=False),cancel=lambda:not active(),sleep_budget=True)
    record['funnel']=result
    if logic_focus:
        supported=any(t['relationship']==dict(subject=sc['subject'],predicate='requires',object=sc['object']) for t in result['thoughts'])
        record['logic_validation']=dict(expected_support=sc['expected_support'],observed_support=supported,correct=supported==sc['expected_support'])
    candidates=[t for t in result['thoughts'] if t['relationship']['subject']==sc['subject'] and
                (not logic_focus or t['relationship']['object']==sc['object'])]
    record['reconciler']=[reconcile(t,sc) for t in candidates]
    if experience_focus:
        for review in record['reconciler']:
            review['checks']['simulated_outcome_verified']=record['sandbox']['status']=='verified'
            review['approved']=all(review['checks'].values())
    if not candidates:
        record['status']='rejected-by-reconciler'
        record['rejection_reason']='No supported coherent candidate; contradictions or insufficient convergence.'
    else:
        t=candidates[0];review=record['reconciler'][0]
        record['gist']='Before I '+t['relationship']['subject']+', I should '+t['relationship']['object']+'.'
        if conversation_focus or sc.get('speech_style')=='conversation_move':
            record['speech_style']='conversation_move'
            record['scene_id']=sc.get('scene_id')
            record['cue_tokens']=list(sc.get('cue_tokens') or [])
        record['status']='rejected-by-reconciler'
        if review['approved']:
            state=funnel.read(root/'state.json',{})
            signature=funnel.digest(t['relationship'])
            seen=set(state.get('retained',[]))
            session_limit=max(1,min(256,int(funnel.read(cloud.root/'config.json',{}).get('practice_session_limit',128))))
            if signature in seen:record['status']='duplicate-suppressed'
            elif len(seen)>=session_limit:record['status']='retention-budget-held'
            else:
                from loop import evaluate_judge
                from sleep_rollbacks import imprint
                candidate=MARKER+record['gist']
                with cloud.lock:
                    if not active():record['status']='cancelled'
                    else:
                        verdict=evaluate_judge(dict(candidate=candidate,intent='dream_reflection',should_imprint=True,
                            contradictions=[],proposed_action={'type':'reflect'}),cloud.mind.tsc,cloud.mind.config,operator_authenticated=False)
                        record['gists_sent_to_judge']=1
                        record['judge']=dict(approved=verdict.approved,quarantined=verdict.quarantined,rationale=verdict.rationale)
                        if verdict.approved and not verdict.quarantined:
                            record['sleep_source']=imprint(cloud.mind,candidate,verdict)
                            rows=json.loads(cloud.mind.psc.path.read_text(encoding='utf-8'))
                            record['gists_imprinted']=int(any(r.get('memory')==candidate and r.get('source')==record['sleep_source'] for r in rows))
                            record['status']='imprinted' if record['gists_imprinted'] else 'error'
                            record['retained_signature']=signature
                        else:record['status']='rejected-by-judge'
    record['finished_at']=time.time()
    return record

def layer_tick(cloud,rest,phase,first):
    if rest.get('task')!='dreamthink_four_hour':return False
    root=cloud.root/'dreamthink-practice';root.mkdir(exist_ok=True)
    if rest.get('state')!='sleeping':return True
    if cloud.config().get('enabled') is not True:return True
    if funnel.read(cloud.root/'thought-funnel'/'live-mode.json',{}).get('enabled') is not True:return True
    from sleep_rollbacks import blocked
    if blocked():return True
    state=funnel.read(root/'state.json',{})
    if state.get('session')!=rest['started_at']:
        state=dict(session=rest['started_at'],cycles=0,last_finished=0,phase_cycles={},phase_imprints={},retained=[])
        funnel.save(root/'state.json',state)
    if state.get('paused') or state['cycles']>=1280:return True
    if (first and time.time()-state['last_finished']<45) or time.time()>=rest['wake_at']:return True
    index=state['phase_cycles'].get(str(phase),0)
    try:record=cycle(cloud,rest,index,phase)
    except Exception as exc:record=dict(id='error-'+uuid.uuid4().hex,timestamp=time.time(),phase=phase,status='error',error=type(exc).__name__,gists_imprinted=0)
    state['cycles']+=1;state['last_finished']=time.time();state['phase_cycles'][str(phase)]=index+1
    if record.get('gists_imprinted'):
        state['retained'].append(record['retained_signature'])
        state['phase_imprints'][str(phase)]=state['phase_imprints'].get(str(phase),0)+1
    state['last_status']=record['status']
    state['consecutive_errors']=state.get('consecutive_errors',0)+1 if record['status']=='error' else 0
    if record['status']=='exhausted':
        state['paused']=True;record['pause_reason']='Finite curriculum exhausted; preserve experience without repeating.'
    if state['consecutive_errors']>=3:
        state['paused']=True;record['pause_reason']='Three consecutive errors; no automatic restart.'
    funnel.save(root/'state.json',state);funnel.save(root/'latest.json',record)
    with (root/'cycles.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(record)+'\n')
    # Expose generated structure in the existing dream pool, explicitly non-factual.
    if record.get('gist'):
        with (cloud.root/'dreams.jsonl').open('a',encoding='utf-8') as f:
            f.write(json.dumps(dict(id=record['id'],provenance='DREAM',timestamp=record['timestamp'],
                mode='dreamthink_practice',status=record['status'],gist=record['gist'],
                narrative='Hypothetical scenario: '+record['scenario']['prompt'],sleep_source=record.get('sleep_source','')))+'\n')
    return True

def tick(cloud,rest):
    if rest.get('task')!='dreamthink_four_hour':return False
    state=funnel.read(cloud.root/'dreamthink-practice'/'state.json',{})
    cfg=funnel.read(cloud.root/'config.json',{})
    experience=cfg.get('practice_focus')=='experience'
    interval=max(45,min(600,int(cfg.get('experience_interval_seconds',180)))) if experience else 45
    if time.time()-state.get('last_finished',0)<interval:return True
    # Four bounded layers per batch, serialized so PSC writes cannot race.
    lanes=max(1,min(64,int(cfg.get('experience_lanes',16)))) if experience else 4
    for lane in range(lanes):
        layer_tick(cloud,rest,lane%4,lane==0)
    return True
