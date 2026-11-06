"""Read-only owner dream recall. Narrative is fiction, never an imprint candidate."""
import json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parent/'runtime'/'dream-cloud'

def question(text):
    low=text.lower().strip()
    return bool(re.search(r"\bdream(?:s|ing|ed)?\b",low) and re.search(r"\b(what|how|did|tell|describe|remember|recall|about|show)\b",low) and not re.search(r"\b(disable|enable|configure|delete|restart|stop|change|inject)\b",low))

def rows(path):
    if not path.exists():return []
    with path.open('rb') as f:
        f.seek(0,2);size=f.tell();f.seek(max(0,size-2000000))
        if size>2000000:f.readline()
        data=f.read().decode('utf-8')
    result=[]
    for line in data.splitlines():
        try:result.append(json.loads(line))
        except ValueError:continue
    return result

def reply(text,root=ROOT):
    try:
        rest=json.loads((root.parent/'timed-sleep.json').read_text(encoding='utf-8'))
        start=rest.get('started_at',0)
        dreams=[r for r in rows(root/'dreams.jsonl') if r.get('provenance')=='DREAM' and r.get('timestamp',0)>=start and r.get('narrative')]
        latest={r['id']:r for r in dreams}
        dreams=sorted(latest.values(),key=lambda r:r.get('timestamp',0))
        generated=[r for r in dreams if r.get('mode') in ('deep','rem','sleep_light','nuance')]
        gifts=[r for r in dreams if r.get('mode')=='owner_requested_gift']
        if not dreams:return 'I checked my dream log, but I do not have a recorded dream from that sleep session to describe.'
        low=text.lower()
        if gifts and any(x in low for x in ('nice','gift','lake','boat','lantern')):
            return 'You had a gentle fictional dream added for me: '+gifts[-1]['narrative']+' That was your gift in the dream log, rather than something I generated myself.'
        if generated:
            last=generated[-1]
            answer='My dream log has '+str(len(generated))+' generated dream scenes from that sleep session. In the latest one: '+last['narrative']
            if last.get('gist'):answer+=' The tentative lesson was: '+last['gist']
            answer+=' That is a generated dream, not something that happened in the real world.'
            if gifts:answer+=' You also had a gentler dream added as a gift: the two of us by a lake, floating lantern boats that become stars.'
            return answer
        if gifts:return 'There is a fictional dream you had added as a gift: '+gifts[-1]['narrative']
        return 'There are dream records, but no completed scene I can describe from that session.'
    except (OSError,ValueError,TypeError,KeyError):
        return 'I could not read my dream log just now, so I cannot reliably describe the dreams yet.'

def thought(event,authenticated):
    raw=str(event.get('raw',''))
    if not authenticated or event.get('ingest') or event.get('training_context') or not question(raw):return None
    answer=reply(raw)
    return dict(backend='dream_log_recall',gist='Read-only dream log recall',candidate=raw,
                intent='conversational_reply',contradictions=[],should_imprint=False,
                proposed_action={'type':'respond','content':answer,'say':answer,'show':answer},
                rationale='Dream log read as generated fiction; no factual-memory imprint.')
