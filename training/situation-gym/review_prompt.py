from pathlib import Path
import os as _os
def _local_root():
    root = _os.environ.get("ATMAN_LOCAL_ROOT")
    if not root:
        raise SystemExit("Set ATMAN_LOCAL_ROOT to your local ATMAN checkout to run this training harness.")
    return Path(root)
p=_local_root()/'REVIEW.md';s=p.read_text(encoding='utf-8')
old="        user_prompt = 'Current simulated conversation:\\n' + raw_text + '\\nChoose your next action using the supplied simulated tools. Reply in the normal thought JSON.'"
new="""        user_prompt = 'Current simulated conversation:\\n' + raw_text + '\\nChoose your next action using the supplied simulated tools. Reply in the normal thought JSON.'
        if event['training_context'].get('review'):
            user_prompt = raw_text + '\\nUse the supplied trace as evidence. The run is over. Return the normal thought JSON with proposed_action.type=respond and a retrospective lesson in content, not a plan to do more errands. Prefer one specific error and a transferable rule, in 2-3 sentences.'"""
assert s.count(old)==1;p.write_text(s.replace(old,new),encoding='utf-8')
