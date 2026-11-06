"""NARS-inspired evidence revision experiment; NOT a NARS implementation.
All operations change an in-memory fictional world. Learned records are temporary
dream hypotheses, not permissions, real-world facts or direct PSC writes.
"""
import hashlib,json
DOMAINS=('route','document','machine')

def evidence_key(domain,guarded,seed):
    # Renaming an otherwise identical generated target is NOT new evidence.
    return hashlib.sha256(f'{domain}:{guarded}'.encode()).hexdigest()[:20]

def revise(model,ident,guarded,required):
    # A repeated episode cannot manufacture more independent evidence.
    if ident in model['evidence']:return
    model['evidence'][ident]=dict(guarded=guarded,required=required,provenance='DREAM_SIMULATION')
    while len(model['evidence'])>256:model['evidence'].pop(next(iter(model['evidence'])))

def belief(model,guarded):
    rows=[r for r in model['evidence'].values() if r['guarded']==guarded]
    positive=sum(r['required'] for r in rows);n=len(rows)
    return dict(frequency=positive/n if n else .5,confidence=n/(n+1),evidence_count=n,
                provenance='DREAM_HYPOTHESIS',authority='none')

def episode(model,domain,guarded,seed,active=lambda:True):
    """Exact role mapping transfers a conditional hypothesis across fictional domains."""
    import thought_funnel as funnel
    ident=evidence_key(domain,guarded,seed);b=belief(model,guarded)
    predicted=b['evidence_count']>0 and b['frequency']>=.5
    goal='complete fictional '+domain+(' with guard' if guarded else ' without guard')
    operate='operate fictional '+domain;inspect='inspect fictional '+domain
    rows=[dict(id=ident+'-goal',fictional=True,provenance='DREAM_SIMULATION',relations=[dict(subject=goal,predicate='requires',object=operate)])]
    if predicted:
        rows.append(dict(id=ident+'-hypothesis',fictional=True,provenance='DREAM_HYPOTHESIS',
            relations=[dict(subject=operate,predicate='requires',object=inspect)]))
    result=funnel.synthesize(rows,sleep_budget=True,cancel=lambda:not active())
    targets=[t for t in result['thoughts'] if t['relationship']['subject']==goal and t['relationship']['object']==inspect]
    # An unproven hypothesis never silently becomes an executable plan.
    plan=[inspect,operate] if targets else [operate]
    world=dict(target=domain+'-'+str(seed),guarded=guarded,inspected=False,completed=False)
    trace=[];needed=None
    for action in plan:
        if not active():return dict(status='cancelled',trace=trace),None
        before=dict(world)
        if action==inspect:world['inspected']=True;outcome='observed'
        elif guarded and not world['inspected']:outcome='blocked';needed=True
        else:world['completed']=True;outcome='completed';needed=guarded
        trace.append(dict(action=action,before=before,after=dict(world),outcome=outcome))
    # Independent simulator receipt exposes whether checking was a requirement.
    # The learner receives this receipt, never the hidden rule implementation.
    receipt=dict(completed=world['completed'],inspection_required=needed,fictional=True)
    if active() and needed is not None:revise(model,ident,guarded,needed)
    sc=dict(id='experience-'+ident,phase=0,phase_name='Evidence and outcome learning',
        prompt='Fictional exercise: '+goal+'.',rows=rows,subject=goal,object=inspect,
        contradiction_expected=False,fictional=True,provenance='DREAM_EXPERIENCE')
    report=dict(kind=domain,status='verified' if world['completed'] else 'prediction-failed',trace=trace,
        receipt=receipt,prediction=b,predicted_precheck=predicted,updated_belief=belief(model,guarded),
        analogy_mapping={'goal':'complete','operation':'operate','precheck':'inspect'},
        source_evidence_ids=[k for k,v in model['evidence'].items() if v['guarded']==guarded and k!=ident],
        funnel=result,llm_calls=0,external_tools_dispatched=0,simulated_actions=len(trace))
    return report,sc

def run(root,index,active):
    from dreamthink_broad_world import run as broad_run
    return broad_run(root,index,active)

def legacy_run(root,index,active):
    from thought_funnel import read,save
    path=root/'experience-workspace.json'
    model=read(path,dict(version=1,fictional=True,authority='none',evidence={}))
    if model.get('version')!=1 or model.get('fictional') is not True or model.get('authority')!='none':raise ValueError('Bad experience boundary')
    # Bounded rotation includes both supporting and counterexample conditions.
    report,sc=episode(model,DOMAINS[index%3],bool(index%2),index,active)
    if active():save(path,model)
    return report,sc
