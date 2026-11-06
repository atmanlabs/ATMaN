"""Bounded logic exercises: fictional premises, no models or external actions."""
NAMES=['Valid dependency deductions','Missing evidence','Invalid reversal','Contradiction checks']
DOMAINS=[('verify a report','inspect its evidence','identify its source'),
 ('complete a delivery','reach the destination','identify the destination'),
 ('compare two claims','separate their assumptions','identify each assumption'),
 ('approve a proposal','check its constraints','identify its scope'),
 ('verify a repair','observe the result','perform a bounded test'),
 ('resolve an ambiguity','identify alternatives','inspect the available context'),
 ('summarize a note','read the note','identify the intended note'),
 ('resume a task','check completed steps','inspect its receipts')]

def basic_generate(phase,index):
    a,b,c=DOMAINS[index%len(DOMAINS)];ident=f'logic-{phase}-{index%len(DOMAINS)}'
    edges=[(a,b),(b,c)] if phase in (0,3) else [(a,b)] if phase==1 else [(a,b),(c,b)]
    rows=[dict(id=ident+'-'+str(i),provenance='DREAM_LOGIC',fictional=True,
               relations=[dict(subject=x,predicate='requires',object=y)]) for i,(x,y) in enumerate(edges)]
    if phase==3:rows.append(dict(id=ident+'-counter',provenance='DREAM_LOGIC',fictional=True,
        relations=[dict(subject=a,predicate='requires',object=c,negative=True)]))
    return dict(id=ident,phase=phase,phase_name=NAMES[phase],fictional=True,provenance='DREAM_LOGIC',
        prompt='Fictional logic exercise. Do these premises support the proposed dependency? '+a+' requires '+c+'.',
        rows=rows,subject=a,object=c,contradiction_expected=phase==3,expected_support=phase==0,
        seed_sources=['logic-domain-'+str(index%len(DOMAINS)),'logic-form-'+str(phase)])

# Fresh fictional premises; these are not assertions about actual capabilities.
EXTENDED=[
 ('restore a fictional archive','verify its manifest','check every listed part','obtain the expected hashes'),
 ('schedule a fictional pickup','find a feasible slot','compare both calendars','obtain current availability'),
 ('restart a fictional job','identify unfinished work','check saved progress','read the last receipt'),
 ('publish a fictional draft','confirm permission','identify the intended audience','clarify the sharing scope'),
 ('navigate a fictional maze','select a safe route','inspect blocked passages','observe the current map'),
 ('compare fictional measurements','normalize their units','identify the measurement units','read the source labels'),
 ('resolve a fictional citation','locate the source passage','identify the cited edition','read the reference details'),
 ('repair a fictional sensor','isolate the failing stage','compare expected and observed output','obtain a baseline'),
 ('merge fictional changes','check compatibility','compare overlapping edits','identify their common base'),
 ('send a fictional parcel','confirm its destination','validate the supplied address','clarify missing address fields'),
 ('accept a fictional result','check independent evidence','separate assumptions from observations','inspect the original record'),
 ('allocate fictional resources','check remaining capacity','account for existing reservations','inspect current allocations'),
 ('reproduce a fictional error','match the original conditions','identify relevant settings','read the recorded configuration'),
 ('complete a fictional handoff','verify recipient readiness','identify required inputs','inspect the handoff contract'),
 ('evaluate a fictional shortcut','check preserved constraints','identify mandatory steps','inspect the task requirements'),
 ('choose a fictional route','compare travel constraints','identify closed connections','refresh the map'),
 ('validate a fictional backup','test recoverability','identify required components','inspect the recovery manifest'),
 ('explain a fictional discrepancy','compare evidence sources','align their time windows','identify their timestamps'),
 ('resume a fictional conversation','resolve the current reference','inspect relevant prior context','identify the active topic'),
 ('undo a fictional edit','identify the affected version','compare recorded revisions','find the previous snapshot')]

def generate(phase,index):
    a,b,c,d=EXTENDED[index%len(EXTENDED)]
    ident=f'logic-expanded-{phase}-{index%len(EXTENDED)}'
    edges=[(a,b),(b,c),(c,d)]
    if phase==1:edges=[(a,b),(c,d)] # missing connecting premise
    if phase==2:edges=[(a,b),(c,b),(c,d)] # shared prerequisite does not imply reversal
    # A separate branch and irrelevant component must not change the requested conclusion.
    edges += [(b,'check the fictional task boundary'),('sort fictional cards','identify their colors')]
    rows=[dict(id=ident+'-'+str(i),fictional=True,provenance='DREAM_LOGIC',relations=[
        dict(subject=x,predicate='requires',object=y)]) for i,(x,y) in enumerate(edges)]
    if phase==3:rows.append(dict(id=ident+'-counter',fictional=True,provenance='DREAM_LOGIC',relations=[
        dict(subject=a,predicate='requires',object=d,negative=True)]))
    return dict(id=ident,phase=phase,phase_name=NAMES[phase]+' — expanded',fictional=True,
        provenance='DREAM_LOGIC',prompt='Fictional logic exercise: determine whether '+a+' requires '+d+'.',
        rows=rows,subject=a,object=d,contradiction_expected=phase==3,expected_support=phase==0,
        seed_sources=['expanded-domain-'+str(index%len(EXTENDED)),'logic-form-'+str(phase)])
