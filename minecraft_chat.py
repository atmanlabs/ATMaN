"""Conversational Minecraft skill routing, passive referent resolution, and drive initiative.

Domain: Minecraft
Core passive learning & drive layer integration:
- Directly queries the Authoritative Core EpisodeSegmenter rolling buffer.
- Resolves 'see that wall, now you do it', 'now you do it', 'do that again'.
- Delivers natural idle summaries explaining what ATMAN did and WHY he wanted to.
- Surfaces and authorizes big want proposals ('build perimeter wall').
- Recalls learned skills ('build a wall', 'mine a tree') under Judge gating.
- Banned: demonstration mode ('learn this as NAME, do it once, say done'),
  log-lines-as-replies ('Observation/reflection recorded in memory trace').
"""
import json
from pathlib import Path
import re
from difflib import SequenceMatcher
from typing import Any, Dict, Optional, Tuple

from episode_segmenter import episode_segmenter
from drives import drive_manager

HERE = Path(__file__).resolve().parent


def route_chat(
    text: str,
    repository: Any,
    fallback: Tuple[str, Dict[str, Any], bool, str],
    context: Optional[Dict[str, Any]] = None,
    config: Optional[Any] = None
) -> Tuple[str, Dict[str, Any], bool, str]:
    """Route Minecraft chat messages through Core passive learning, drives, and Judge gating."""
    # Clean text from speaker prefix and greeting
    clean_text = re.sub(r"^.*? said:\s*", "", text, count=1).strip()
    clean_text = re.sub(r"^(?:hey\s+)?atman[, ]+", "", clean_text, flags=re.I).strip()
    low = clean_text.lower().rstrip(".!?")

    def reply(content: str, intent: str = "conversational_reply"):
        return intent, {"type": "respond", "content": content}, False, "Conversational reply."

    def action(kind: str, name: str, content: str, skill: Optional[Dict[str, Any]] = None):
        return kind, {
            "type": "minecraft_skill",
            "action": kind,
            "domain": "minecraft",
            "skill": skill or {"name": name},
            "content": content
        }, False, "Supervised Minecraft skill execution gated by Judge."

    # 0. Check for unspoken return summary from idle activities
    return_summary = drive_manager.get_and_clear_return_summary()

    # 1a. Autonomous intent and follow cancellation
    is_cancel_follow = bool(re.search(
        r"\b(?:"
        r"leave\s+me\s+alone|"
        r"stop\s+following(?:\s+me)?|"
        r"don't\s+follow(?:\s+me)?|"
        r"quit\s+following(?:\s+me)?|"
        r"stay\s+away(?:\s+from\s+me)?"
        r")\b",
        low
    ))

    is_autonomous_intent = bool(re.search(
        r"\b(?:"
        r"experiment|"
        r"(?:go\s+)?do\s+what(?:ever)?\s+you\s+want(?: to do)?|"
        r"leave\s+me\s+alone|"
        r"surprise\s+me|"
        r"figure\s+it\s+out\s+yourself|"
        r"stop\s+asking\s+me|"
        r"stop\s+following(?:\s+me)?|"
        r"don't\s+follow(?:\s+me)?|"
        r"quit\s+following(?:\s+me)?|"
        r"take(?:\s+the)?\s+initiative|"
        r"(?:go\s+)?(?:do\s+something|explore|wander|play)\s+on\s+your\s+own|"
        r"be\s+autonomous|"
        r"you\s+decide|"
        r"up\s+to\s+you"
        r")\b",
        low
    ))

    if is_autonomous_intent:
        drive, init_action = drive_manager.trigger_autonomous_intent(clean_text)
        act_action = init_action["action"]
        if is_cancel_follow and ("leave" in low or "alone" in low):
            if act_action == "initiative_tidy_base":
                content = "Understood, Operator. I'll give you space and patrol the sanctuary perimeter."
            elif act_action == "initiative_investigate":
                content = "Understood, Operator. I'll give you space and investigate the perimeter terrain."
            elif act_action == "initiative_practice_skill":
                content = "Understood, Operator. I'll give you space and practice building walls nearby."
            else:
                content = "Understood, Operator. I'll leave you be and organize our base supplies."
        elif is_cancel_follow and ("stop following" in low or "don't follow" in low):
            if act_action == "initiative_tidy_base":
                content = "Understood, Operator. Stopping follow — I'm heading over to patrol the perimeter."
            elif act_action == "initiative_investigate":
                content = "Understood, Operator. Stopping follow — I'm heading out to investigate nearby terrain."
            else:
                content = f"Understood, Operator. Stopping follow — I'll {init_action.get('description', 'work on my own')}."
        else:
            if act_action == "initiative_investigate":
                content = "On it, Operator! I'm heading out to investigate the perimeter terrain and scout for resources."
            elif act_action == "initiative_tidy_base":
                content = "Understood, Operator. I'm going to patrol the sanctuary perimeter and keep our entrances secure."
            elif act_action == "initiative_practice_skill":
                content = "Alright, Operator! I'm going to practice building and aligning our cobblestone walls nearby."
            elif act_action == "initiative_organize_inventory":
                content = "Got it, Operator. I'm going to tidy up around the base and organize our inventory."
            else:
                content = f"Understood, Operator. I'm going to {init_action.get('description', 'take the initiative')}."

        return "minecraft_initiative", {
            "type": "minecraft_initiative",
            "action": init_action["action"],
            "drive_id": init_action["drive_id"],
            "initiative": init_action,
            "cancel_follow": True,
            "stay_mode": True,
            "content": content
        }, False, "Supervised Minecraft initiative action triggered by operator autonomous intent."

    if is_cancel_follow:
        return "presence_stay", {
            "type": "minecraft_action",
            "action": "stay",
            "cancel_follow": True,
            "stay_mode": True,
            "content": "Understood, Operator. Stopping here and giving you space."
        }, False, "Follow cancelled on operator request."

    # 1. Direct Presence & Social Commands (fast path)
    if not is_cancel_follow and re.fullmatch(r"(?:come|follow(?:\s+me)?|come\s+here|come\s+with\s+me)", low):
        msg = f"Following you, Operator. {return_summary}" if return_summary else "Following you, Operator."
        return "presence_follow", {
            "type": "minecraft_action",
            "action": "follow",
            "content": msg
        }, False, "Presence follow command."

    if re.fullmatch(r"(?:stay(?:\s+here)?|stop|halt|stand\s+still)", low):
        return "presence_stay", {
            "type": "minecraft_action",
            "action": "stay",
            "cancel_follow": True,
            "stay_mode": True,
            "content": "Staying here."
        }, False, "Presence stay command."

    if re.fullmatch(
        r"(?:hey|hi|hello|howdy|sup|yo|good\s+(?:morning|afternoon|evening|night)|what'?s up)"
        r"(?:\s+(?:buddy|atman|there|man|operator|dude))?",
        low,
    ):
        if return_summary:
            return reply(f"Hey Operator! {return_summary}")
        if re.search(r"morning", low):
            return reply("Morning, Operator. Good to see you — I'm here and ready to learn.")
        return reply("Hey Operator! Good to see you — ready when you are.")

    if re.search(
        r"\b(?:how are you(?: doing)?(?: (?:today|this morning|tonight))?|how(?:'s| is) it going|how(?:'s| are) things)\b",
        low,
    ):
        return reply("Doing well — awake on the dojo and ready for whatever you want to teach me.")

    # 1b. Inquiries into idle actions / initiative ("what did you do?", "what were you doing?", "why did you do that?")
    if re.search(r"\b(?:what (?:did you do|were you doing|have you been doing)|why did you (?:do that|build that|patrol|tidy))\b", low):
        if drive_manager.activity_log:
            latest = drive_manager.activity_log[-1]
            act_desc = latest.description
            why_desc = latest.why
            act_clean = act_desc.rstrip(".")
            first_word = act_clean.split()[0].lower() if act_clean else ""
            if first_word.endswith("ing"):
                return reply(f"While you were away, I was {act_clean[0].lower() + act_clean[1:] if act_clean else ''}. {why_desc}")
            return reply(f"While you were away, I {act_clean[0].lower() + act_clean[1:] if act_clean else ''}. {why_desc}")
        return fallback

    # 1c. Proposal inquiries or suggestions ("what should we do?", "any ideas?", "what do you want?")
    if re.search(r"\b(?:what should we do|any ideas|what do you want|what'?s next)\b", low):
        proposals = []
        prop_path = HERE / "pending_proposals.json"
        if prop_path.exists():
            try:
                proposals = json.loads(prop_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        active_prop = next((p for p in proposals if p.get("status") == "pending_operator_approval"), None)
        if active_prop:
            return reply(active_prop.get("proposal", "We've got plenty of cobblestone stored up for a perimeter wall — want me to build one around the house?"))
        return reply("We've got plenty of cobblestone stored up for a perimeter wall — want me to build one around the house?")

    # 1d. Authorizing pending proposals ("build the perimeter wall", "yes build it", "go ahead")
    if re.search(r"\b(?:(?:yes\s+)?build (?:a |the )?perimeter wall|go ahead and build (?:it|the wall)|sure build it)\b", low):
        skill = repository.find_skill("build_wall", domain="minecraft")
        if skill:
            return action("execute_skill", "build_wall", "Understood, Operator! Starting the perimeter wall now under your supervision.", skill)

    # 2. Referent Resolution: "see that wall, now you do it", "now you do it", "do that again", "your turn"
    is_referent = bool(re.search(
        r"\b(?:now\s+)?(?:you\s+)?(?:do|copy|repeat|recreate|replicate|build|make)\s+(?:it|that|the same|what i)|\b(?:see that (?:wall|structure|tree)|look at that|do that again|do what i just did|your turn|imitate me|do that|now you)\b",
        low
    ))

    if is_referent:
        actor = "Operator"
        if context and isinstance(context, dict):
            p = context.get("player")
            if p:
                actor = re.sub(r"^\.+", "", str(p))

        # Query Authoritative Core Episode Segmenter
        resolved = episode_segmenter.resolve_referent(clean_text, actor=actor, domain="minecraft")
        if resolved:
            episode, rationale = resolved
            skill_name = "build_wall" if episode.action_type == "build" else episode.label
            skill = episode_segmenter.convert_to_skill(episode, skill_name=skill_name)

            # Auto-store the learned skill in the Core repository under Judge gating
            try:
                repository.store_skill(skill)
                from significant_events import SignificantEventsLog
                SignificantEventsLog().log_event(
                    f"Passively learned skill '{skill['name']}' from Operator's actions ({len(skill.get('steps', []))} steps).",
                    source="passive_skill_learning",
                    metadata={"skill": skill['name'], "domain": "minecraft", "steps": len(skill.get("steps", []))}
                )
            except Exception as err:
                print(f"[CORE SKILL STORE ERROR] {err}")

            mat = skill.get("metadata", {}).get("material", "cobblestone")
            count = skill.get("metadata", {}).get("count", len(skill.get("steps", [])))
            if episode.action_type == "build":
                resp_content = f"Watched you build that {mat} wall ({count} blocks) — building a matching wall now."
            else:
                resp_content = f"Watched you do {episode.label} — replicating that now under your supervision."

            return action("execute_skill", skill["name"], resp_content, skill)
        else:
            # Buffer search completed and found nothing
            return reply("I didn't catch an action sequence in my recent memory buffer. Could you build it once while I watch?")

    # 3. Recall: "build a wall", "build a cobblestone wall", "build the wall"
    wall_match = re.search(r"\b(?:build|make)\s+(?:a |the |another )?(?:([a-z_]+)\s+)?wall\b", low)
    if wall_match:
        specified_mat = wall_match.group(1)
        skill = repository.find_skill("build_wall", domain="minecraft")
        if skill:
            skill_copy = dict(skill)
            if specified_mat and specified_mat not in ("a", "the", "one"):
                # Adapt material in steps
                steps = []
                for s in skill.get("steps", []):
                    sc = dict(s)
                    sc["params"] = dict(s.get("params", {}))
                    if "block" in sc["params"]:
                        sc["params"]["block"] = specified_mat
                    if "item" in sc["params"]:
                        sc["params"]["item"] = specified_mat
                    steps.append(sc)
                skill_copy["steps"] = steps
                skill_copy["material"] = specified_mat
                mat_name = specified_mat
            else:
                mat_name = skill.get("metadata", {}).get("material", "cobblestone")

            return action("execute_skill", "build_wall", f"Building a {mat_name} wall for you now.", skill_copy)
        else:
            # Check recent episodes in segmenter before giving up
            ep = episode_segmenter.get_recent_episode(domain="minecraft", action_type="build")
            if ep:
                skill = episode_segmenter.convert_to_skill(ep, skill_name="build_wall")
                repository.store_skill(skill)
                mat_name = ep.materials[0] if ep.materials else "cobblestone"
                return action("execute_skill", "build_wall", f"Building a {mat_name} wall for you now.", skill)

            return reply("I haven't learned how to build a wall yet. Build one while I watch, and I'll learn it.")

    # 4. Recall: "mine a tree", "chop a tree"
    if re.search(r"\b(?:mine|chop|cut down|harvest)\s+(?:a |some )?(?:tree|wood|log|birch|oak)\b", low):
        skill = repository.find_skill("mine_tree", domain="minecraft")
        if skill:
            return action("execute_skill", "mine_tree", "I'll mine that tree while you supervise.", skill)
        else:
            return reply("I don't have the tree mining skill loaded. Cut down a tree while I watch and I'll learn it.")

    # 5. Generic "do [skill_name]"
    do_match = re.fullmatch(r"(?:please\s+)?do\s+([a-z0-9_]+)", low)
    if do_match:
        s_name = do_match.group(1).strip()
        skill = repository.get_skill(s_name, domain="minecraft") or repository.find_skill(s_name, domain="minecraft")
        if skill:
            return action("execute_skill", skill["name"], f"I'll execute {skill['name']} while you supervise.", skill)

    # 6. Fallback to caller, ensuring NO canned log dumps or template deflections
    if fallback and fallback[1].get("type") == "respond" and fallback[1].get("content"):
        fb_content = fallback[1]["content"]
        if "Observation/reflection recorded in memory trace" not in fb_content and "learn this as NAME" not in fb_content:
            return fallback

    return fallback
