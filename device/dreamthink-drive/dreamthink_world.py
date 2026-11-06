"""Closed symbolic dream worlds. No filesystem, network, tool or model capability."""
import thought_funnel as funnel

def run(index, active=lambda: True):
    kind = ('rooms', 'files', 'repair')[index % 3]
    specs = {
        'rooms': ('verify arrival', 'move to garden', 'observe doorway'),
        'files': ('report contents', 'read selected note', 'find matching note'),
        'repair': ('verify lamp', 'replace cell', 'inspect lamp'),
    }
    goal, middle, first = specs[kind]
    rows = [dict(id='world-'+kind+'-'+str(i), relations=[dict(subject=a, predicate='requires', object=b)])
            for i, (a,b) in enumerate(((goal,middle),(middle,first)))]
    result = funnel.synthesize(rows, settings=dict(rendering_enabled=False), cancel=lambda: not active())
    thoughts = [t for t in result['thoughts'] if t['relationship']['subject']==goal]
    world = dict(room='hall', doorway=None, files={'garden-note':'Water the seedlings'}, selected=None,
                 contents=None, lamp='off', inspected=False, cell='empty', receipt=None)
    trace=[]
    report=dict(kind=kind, fictional=True, llm_calls=0, external_tools_dispatched=0,
                status='discarded', trace=trace, funnel=result, initial_world=dict(world))
    if not thoughts:
        report['final_world']=world; return report
    thought=thoughts[0]
    # Prerequisites in reverse path order, then goal. No language-model planner.
    plan=list(dict.fromkeys([edge[2] for edge in reversed(thought['path'])]+[goal]))
    report['plan']=plan
    allowed={first,middle,goal}; completed=set(); attempts={}
    for action in plan:
        if action not in allowed:
            report['status']='blocked';break
        for retry in range(2):
            if not active():report['status']='cancelled';report['final_world']=world;return report
            attempts[action]=attempts.get(action,0)+1
            before=dict(world); status='ok'
            if action==first:
                if kind=='rooms':world['doorway']='garden'
                elif kind=='files':world['selected']='garden-note'
                else:world['inspected']=True
            elif first not in completed:status='precondition-failed'
            elif action==middle:
                if kind=='rooms':world['room']=world['doorway']
                elif kind=='files':world['contents']=world['files'][world['selected']]
                elif attempts[action]==1:status='transient-jam'
                else:world.update(cell='charged',lamp='on')
            elif middle not in completed:status='precondition-failed'
            else:
                ok=(world['room']=='garden' if kind=='rooms' else
                    world['contents']==world['files'].get(world['selected']) if kind=='files' else world['lamp']=='on')
                status='verified' if ok else 'verification-failed'
                world['receipt']=dict(goal=goal,verified=ok)
            trace.append(dict(action=action,attempt=attempts[action],status=status,before=before,after=dict(world)))
            if status in ('ok','verified'):completed.add(action);break
            if status!='transient-jam':break
        if action not in completed:report['status']='failed';break
    else:report['status']='verified' if world['receipt'] and world['receipt']['verified'] else 'failed'
    report['simulated_actions']=len(trace);report['final_world']=world
    return report
