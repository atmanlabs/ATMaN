"""Finite, model-free composition of fictional teaching premises. No actions or imprinting."""
import hashlib

TASKS=[
 ['answer a hesitant request','respond to a correction','explain a limitation','acknowledge disappointment','resolve an unclear pronoun','separate a question from a command'],
 ['locate a fictional note','compare fictional drafts','summarize a fictional document','retrieve a fictional receipt','organize fictional search results','trace a fictional claim to its source'],
 ['recover a fictional interrupted job','retry a fictional request','verify a fictional repair','resume a fictional partial task','diagnose a fictional stale result','report a fictional failed action'],
 ['plan a fictional errand','order fictional dependencies','evaluate a fictional improvement','compare fictional alternatives','revise a fictional plan','review a fictional simulation']]
CONDITIONS=[
 ('the target is ambiguous','clarify the intended target','avoid committing to an unconfirmed interpretation'),
 ('the evidence conflicts','preserve the conflicting evidence','avoid claiming an unsupported resolution'),
 ('the request has changed','refresh the current requirements','avoid continuing a superseded plan'),
 ('the result is unverified','inspect the available outcome evidence','avoid claiming completion without a receipt')]

def catalog():
    return dict(version=1,provenance='DREAM_CURRICULUM',fictional=True,
                authority='none',task_groups=TASKS,conditions=CONDITIONS,
                combinations=96,description='Authored task and constraint seeds; deterministic combinations are exercises, not discoveries or real events.')

def generate(phase,index,repository=None):
    repo=repository or catalog()
    if repo.get('version')!=1 or repo.get('fictional') is not True or repo.get('authority')!='none':
        raise ValueError('Invalid dream repository boundary')
    tasks=repo['task_groups'][phase];conditions=repo['conditions']
    if len(tasks)!=6 or len(conditions)!=4:raise ValueError('Repository size bound')
    slot=index%24;task=tasks[slot%6];condition,strategy,check=conditions[slot//6]
    if any(not isinstance(s,str) or len(s)>160 for s in (task,condition,strategy,check)):
        raise ValueError('Malformed dream seed')
    qualifiers=['ambiguous target','conflicting evidence','changed request','unverified result']
    a=task.replace('fictional ','')+' with '+qualifiers[slot//6];b=strategy;c=check
    ident='dreamrepo-'+hashlib.sha256((a+b+c).encode()).hexdigest()[:16]
    rows=[dict(id=ident+'-'+str(i),provenance='DREAM_GENERATED',fictional=True,
               relations=[dict(subject=x,predicate='requires',object=y)])
          for i,(x,y) in enumerate(((a,b),(b,c)))]
    return dict(id=ident,phase=phase,prompt='Fictional dream exercise: '+a+'. What should happen before proceeding?',
                rows=rows,contradiction_expected=False,subject=a,object=c,
                fictional=True,provenance='DREAM_GENERATED',generator='bounded_structural_composition',
                seed_sources=['task-group-'+str(phase)+'-'+str(slot%6),'condition-'+str(slot//6)],
                repository_version=1,slot=slot)
