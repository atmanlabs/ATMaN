from pathlib import Path
import os as _os
def _local_root():
    root = _os.environ.get("ATMAN_LOCAL_ROOT")
    if not root:
        raise SystemExit("Set ATMAN_LOCAL_ROOT to your local ATMAN checkout to run this training harness.")
    return Path(root)
p=_local_root()/'REVIEW.md';s=p.read_text(encoding='utf-8')
old='    from epistemic_dialogue import route as epistemic_route\n    epistemic_action = epistemic_route(classified_request, raw_text)'
new='''    if event.get('training_context', {}).get('review'):
        # This typed request supplies its run trace directly. It is not a request
        # to retrieve personal history from PSC before authoring the reflection.
        classified_request = dict(classified_request, knowledge_need='none',
                                  self_topic='none', conversation_intent='factual')
    from epistemic_dialogue import route as epistemic_route
    epistemic_action = epistemic_route(classified_request, raw_text)'''
assert s.count(old)==1;p.write_text(s.replace(old,new),encoding='utf-8')
print('Self-review uses its supplied trace in normal reasoning instead of requesting unrelated PSC recall.')
