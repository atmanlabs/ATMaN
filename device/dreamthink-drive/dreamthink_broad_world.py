"""Finite varied fictional worlds. Only dictionary state changes; no external tools.
Authored action semantics and error recovery; learned conditional prerequisites.
"""
import copy
import thought_funnel as f
CHECKS=('inspect target','check supplies','verify location','compare records','reserve capacity','confirm simulated clearance')
FAULTS=('normal','transient','changed target','conflicting observations','denied','partial result')
TOTAL=63*6*3

def spec(index):
    n=(index*37)%TOTAL
    return dict(id='broad-'+str(n),mask=n%63+1,fault=FAULTS[(n//63)%6],stages=1+n//378,
                domain=('delivery','repair','document','scheduling')[index%4],fictional=True)

def empty():return dict(version=2,fictional=True,authority='none',cursor=0,seen=[],rules={},evidence={})

def episode(model,s,active=lambda:True):
    needed=[CHECKS[i] for i in range(6) if s['mask']&(1<<i)]
    world=dict(stage=0,checked=[],version=0,refreshed=False,compared=False,attempts=0,completed=False)
    trace=[];predictions=[];observed=[];last_funnel={};stage_goal='';rowset=[]
    def act(action):
        before=copy.deepcopy(world);outcome='ok';missing=None
        if action in CHECKS:world['checked'].append(action)
        elif action=='refresh observation':world['refreshed']=True;world['checked']=[]
        elif action=='reconcile observations':world['compared']=True
        elif action=='operate':
            world['attempts']+=1
            if s['fault']=='denied':outcome='permission denied'
            elif s['fault']=='changed target' and not world['refreshed']:
                world['version']+=1;outcome='stale observation'
            elif s['fault']=='conflicting observations' and not world['compared']:outcome='conflicting observations'
            elif s['fault']=='transient' and world['attempts']==1:outcome='temporary failure'
            else:
                missing=next((v for v in needed if v not in world['checked']),None)
                if missing:outcome='missing prerequisite'
                elif s['fault']=='partial result' and world['attempts']==1:outcome='partial result'
                else:
                    world['stage']+=1;world['checked']=[]
                    world['completed']=world['stage']>=s['stages']
                    outcome='verified complete' if world['completed'] else 'verified stage'
        else:raise ValueError('Unknown simulated action')
        receipt=dict(action=action,status=outcome,missing=missing,before=before,after=copy.deepcopy(world),fictional=True)
        trace.append(receipt);return receipt
    for turn in range(32):
        if not active():return dict(status='cancelled',trace=trace),None
        stage_goal='complete fictional '+s['domain']+' stage'
        operation='operate fictional '+s['domain']
        rowset=[dict(id=s['id']+'-goal',relations=[dict(subject=stage_goal,predicate='requires',object=operation)])]
        # Prior learning supplies candidate prerequisites. Feature bits are observable
        # world descriptors; only returned error receipts teach their action mappings.
        candidates=[]
        for bit in range(6):
            rule=model['rules'].get(str(bit))
            if s['mask']&(1<<bit) and rule:
                candidates.append(rule['action'])
                rowset.append(dict(id='evidence-'+rule['source'],relations=[dict(subject=operation,predicate='requires',object=rule['action'])]))
        last_funnel=f.synthesize(rowset,sleep_budget=True,cancel=lambda:not active())
        supported={t['relationship']['object'] for t in last_funnel['thoughts'] if t['relationship']['subject']==stage_goal}
        planned=[x for x in candidates if x in supported and x not in world['checked']]
        predictions.append(dict(stage=world['stage'],expected_prerequisites=planned,source_ids=[r['id'] for r in rowset]))
        for action in planned:
            if not active():return dict(status='cancelled',trace=trace),None
            act(action)
        if not active():return dict(status='cancelled',trace=trace),None
        receipt=act('operate');status=receipt['status']
        if status=='permission denied':break
        if status=='stale observation':act('refresh observation')
        elif status=='conflicting observations':act('reconcile observations')
        elif status=='missing prerequisite':
            action=receipt['missing'];bit=CHECKS.index(action)
            # Record an observation, not a successful action or real-world fact.
            eid=s['id']+'-'+str(bit)
            observed.append(dict(id=eid,bit=bit,action=action,provenance='DREAM_SIMULATION'))
            model['rules'][str(bit)]=dict(action=action,source=eid,provenance='DREAM_HYPOTHESIS')
            model['evidence'].setdefault(eid,observed[-1])
        if world['completed']:break
    status='verified' if world['completed'] else 'denied-correctly' if trace and trace[-1]['status']=='permission denied' else 'bounded-failure'
    report=dict(kind=s['domain'],status=status,trace=trace,predictions=predictions,observations=observed,
        specification=s,final_world=world,funnel=last_funnel,llm_calls=0,external_tools_dispatched=0,
        simulated_actions=len(trace),missing_precondition_failures=sum(t['status']=='missing prerequisite' for t in trace),
        learning_scope='conditional simulated prerequisites; recovery operations are authored',provenance='DREAM_SIMULATION')
    sc=dict(id=s['id'],phase_name='Multi-constraint dream world',prompt='Fictional '+s['domain']+' task with '+s['fault']+'.',
        rows=rowset,subject=stage_goal,object=needed[0],contradiction_expected=False,fictional=True,provenance='DREAM_EXPERIENCE')
    # Imprint only a context-qualified candidate, never a blanket prerequisite.
    qualified='complete fictional '+s['domain']+' with pattern '+str(s['mask'])
    sc['subject']=qualified
    sc['rows']=copy.deepcopy(rowset);sc['rows'][0]['relations'][0]['subject']=qualified
    return report,sc

def run(root,index,active):
    path=root/'experience-broad-workspace.json';model=f.read(path,empty())
    if model.get('version')!=2 or model.get('fictional') is not True or model.get('authority')!='none':raise ValueError('Invalid dream workspace')
    if model['cursor']>=TOTAL:
        return dict(kind='curriculum',status='exhausted',trace=[],llm_calls=0,external_tools_dispatched=0),None
    s=spec(model['cursor']);report,sc=episode(model,s,active)
    report['lane']=model['cursor']%16
    report['world_cursor']=model['cursor'];report['world_capacity']=TOTAL
    if active() and report['status']!='cancelled':
        model['cursor']+=1;model['seen'].append(s['id']);f.save(path,model)
    return report,sc
