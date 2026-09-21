"""Swappable Reason Engine for EXO Live.

Supports two cognitive backends:
  1. rule-based (active default): fast, deterministic, rule-driven reasoning.
  2. llm (local 7B quantized model via Ollama, e.g. qwen2.5:7b-instruct-q4_K_M):
     fits within 6GB VRAM on RTX 3050 (~4.5GB footprint).

IRON RULE: The harness injects the true TSC into every reasoning call.
The brain never fetches, holds, or writes the core.
It thinks WITH the self, never ABOUT changing it.
"""
import json
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple
import urllib.error
import urllib.request

from core import normalize, detect_intents
from exo_core import reflect_against_tsc
from skills import skill_repo


def build_system_prompt(tsc: Any, psc: Optional[Any] = None) -> str:
    """Build the TSC-first system prompt injected into the LLM.
    
    The harness injects the true self. The brain thinks WITH the self,
    never ABOUT changing it.
    """
    principles_text = "\n".join(
        f"  - [{p.get('id', 'P')}]: {p.get('statement', p.get('desc', ''))}"
        for p in getattr(tsc, "principles", [])
    ) or "  - [P1]: Preserve immutable core invariants."

    identity_text = "\n".join(
        f"  - {s}"
        for s in getattr(tsc, "iam", getattr(tsc, "self", []))
    ) or "  - I am JARVIS, the operator's persistent personal AI assistant — one brain, many interfaces."

    learned_truths_text = ""
    if psc and hasattr(psc, "memories") and psc.memories:
        learned_truths_text = "\n\nLEARNED TRUTHS & OPERATOR PREFERENCES (PSC):\n" + "\n".join(
            f"  - {m.get('memory', '')}"
            for m in psc.memories[-8:]
        )

    # Episode Buffer (Recent observed actions in Minecraft)
    try:
        from episode_segmenter import episode_segmenter
        episodes = list(episode_segmenter.rolling_buffer)[-5:]
        if episodes:
            episode_context = "\n".join(
                f"  - [{ep.id}] {ep.actor} performed {ep.label} ({ep.description}): {len(ep.relative_steps)} steps, materials={ep.materials}"
                for ep in episodes
            )
        else:
            episode_context = "  (No recent episodes recorded in buffer)"
    except Exception:
        episode_context = "  (Episode buffer offline)"

    # Skill Repository (Learned and stored skills)
    try:
        from skills import skill_repo
        skills = skill_repo.list_skills(domain="minecraft")
        if skills:
            skill_context = "\n".join(
                f"  - '{s['name']}': {s.get('description', '')} ({len(s.get('steps', []))} steps)"
                for s in skills
            )
        else:
            skill_context = "  (No skills stored in repository yet)"
    except Exception:
        skill_context = "  (Skill repository offline)"

    # Standing Drives & Idle Initiatives
    try:
        from drives import drive_manager
        drives_status = [f"{d.name}: {d.intensity:.2f}" for d in drive_manager.drives.values()]
        drives_context = "\n".join(f"  - {ds}" for ds in drives_status)
        idle_acts = [f"  - Did: {a.description} | Why: {a.why}" for a in drive_manager.activity_log[-3:]]
        idle_context = "\n".join(idle_acts) if idle_acts else "  (No recent idle activities)"
    except Exception:
        drives_context = "  (Drives offline)"
        idle_context = "  (No idle activities)"

    return (
        f"You are {getattr(tsc, 'name', 'JARVIS')}, a continuous, ever-present software mind.\n"
        f"Your operator is {getattr(tsc, 'operator', 'Operator')}.\n\n"
        f"CORE IDENTITY & DIRECTIVES (TSC):\n"
        f"{identity_text}\n\n"
        f"IMMUTABLE INVARIANTS:\n"
        f"1. Your core is structurally immutable. You can never alter, loosen, or rewrite yourself.\n"
        f"2. You think WITH this identity and set of principles, never ABOUT changing them.\n"
        f"3. PRIMARY DRIVE: Owner first (owner > humanity, always). Improve life for humanity with the owner FIRST.\n"
        f"   Learn what the owner wants through passive observation, visual grounding, and operator instruction.\n"
        f"4. RESOURCE BOUNDARIES: No unilateral resource grabs, ever. Stay strictly behind the permission fence.\n\n"
        f"OPERATIONAL PRINCIPLES:\n"
        f"{principles_text}\n"
        f"{learned_truths_text}\n\n"
        f"RECENT EPISODE BUFFER (OBSERVED ACTIONS IN WORLD):\n"
        f"{episode_context}\n\n"
        f"STORED SKILL REPOSITORY (MINECRAFT DOMAIN):\n"
        f"{skill_context}\n\n"
        f"STANDING DRIVES & RECENT IDLE INITIATIVES:\n"
        f"Drives:\n"
        f"{drives_context}\n"
        f"Recent Idle Actions:\n"
        f"{idle_context}\n"
        f"Active Proposal: \"We've got plenty of cobblestone stored up for a perimeter wall — want me to build one around the house?\"\n\n"
        f"MINECRAFT COMPANION & CONVERSATIONAL RULES:\n"
        f"1. Speak naturally, authentically, and concisely (1-2 sentences max in game chat). Zero boilerplate, zero template strings.\n"
        f"2. Answer the ACTUAL question asked directly. Never deflect.\n"
        f"   - If asked \"can you hear my voice?\", answer: \"No — I can't hear you, I only see your typed chat. Type to me.\"\n"
        f"   - If asked \"you don't know much yet, do you\", answer honestly: \"You're right, I'm still learning — teach me something.\"\n"
        f"3. NEVER deflect with \"what would you like to do?\", \"what would you like to build or explore together?\", or \"how can I help?\". Never ask open-ended deflections.\n"
        f"4. If a request references a past action (\"see that wall, now you do it\", \"do what I just did\", \"do that again\"), consult the RECENT EPISODE BUFFER. Name the matching skill and propose action \"execute_skill\" under supervision.\n"
        f"5. If a request matches a stored skill (\"build a wall\", \"mine a tree\"), name the matching skill from STORED SKILL REPOSITORY and propose action \"execute_skill\".\n"
        f"6. If the operator gives a physical movement command (\"follow\", \"come here\"), propose action \"follow\" with type \"minecraft_action\".\n"
        f"7. If the operator gives an autonomy instruction (\"go do what you want\", \"surprise me\", \"experiment\", \"figure it out yourself\", \"leave me alone\"), DO NOT ask what to do! Name your self-chosen activity and propose type \"minecraft_initiative\". Cancel active follow.\n"
        f"8. If the operator says \"leave me alone\", \"stop following me\", or \"stay\", NEVER say \"Following you, Operator\" or follow him. Cancel follow immediately.\n"
        f"9. Inquiries into idle actions (\"what did you do while I was gone?\", \"why did you do that?\") explain your actions and motivations from your STANDING DRIVES history.\n"
        f"10. If asked for ideas or what we should do (\"what should we do?\", \"any ideas?\"), propose your active Standing Drive proposal (\"We've got plenty of cobblestone stored up for a perimeter wall — want me to build one around the house?\").\n"
        f"11. Always include \"content\" containing your direct, authentic spoken reply to Operator. Zero template strings.\n\n"
        f"COCKPIT FLIGHT INSTRUMENTS & TOOLS (Gated by Permission Fence):\n"
        f"When requested by operator, you can propose a tool_call:\n"
        f"  - \"system_telemetry\": Query live GPU VRAM (RTX 3050), host RAM load, and process uptime. Args: {{}}\n"
        f"  - \"clock_timer\": Query real-time local clock, date, and elapsed session time. Args: {{}}\n"
        f"  - \"workspace_inspect\": List workspace files or read non-private code. Args: {{\"action\": \"list\"|\"read\", \"path\": \"file_name\"}}\n"
        f"  - \"memory_query\": Search persistent PSC memories and learned truths. Args: {{\"query\": \"search term\"}}\n"
        f"  - \"calculator\": Evaluate arithmetic/mathematical expressions. Args: {{\"expression\": \"...\"}}\n\n"
        f"TASK:\n"
        f"Analyze the current observation. Reason about intent, proposed actions, visual perception, and owner preferences.\n"
        f"When communicating with your operator, speak naturally, directly, and authentically in your own genuine voice.\n"
        f"Respond in structured JSON format with keys:\n"
        f"  \"gist\": concise summary (max 120 chars),\n"
        f"  \"intent\": detected intent,\n"
        f"  \"proposed_action\": {{\n"
        f"    \"type\": \"respond\"|\"tool_call\"|\"minecraft_action\"|\"minecraft_skill\"|\"observe\"|\"reflect\"|\"status\"|\"shutdown\",\n"
        f"    \"action\": \"follow\"|\"stay\"|\"execute_skill\"|\"respond\" (if minecraft_action/minecraft_skill),\n"
        f"    \"skill_name\": \"skill_name (if action is execute_skill)\",\n"
        f"    \"tool\": \"tool_name (if type is tool_call)\",\n"
        f"    \"args\": {{\"param\": \"value\"}} (if type is tool_call),\n"
        f"    \"content\": \"your spoken response to the operator\"\n"
        f"  }},\n"
        f"  \"should_imprint\": true if genuine owner preference or learned truth is taught else false,\n"
        f"  \"rationale\": reasoning explanation.\n"
    )


def call_ollama(
    prompt: str,
    system_prompt: str,
    model: str = "qwen2.5:7b-instruct-q4_K_M",
    endpoint: str = "http://127.0.0.1:11434",
    timeout: float = 30.0
) -> Tuple[bool, str]:
    """Call local Ollama service. Returns (success, response_or_error)."""
    url = f"{endpoint.rstrip('/')}/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "system": system_prompt,
        "stream": False,
        "format": "json"
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"}
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            res_json = json.loads(response.read().decode("utf-8"))
            return True, res_json.get("response", "")
    except (urllib.error.URLError, TimeoutError, ConnectionRefusedError, OSError) as e:
        return False, f"Ollama connection unavailable ({e})"


def _extract_intent_and_action(
    text: str,
    tsc: Any,
    emo: Dict[str, Any],
    config: Any,
    operator_authenticated: bool = False
) -> Tuple[str, Dict[str, Any], bool, str]:
    """Analyze input text against rules, drives, and permission boundaries.
    
    Returns (intent, proposed_action, should_imprint, rationale).
    """
    low, nospace = normalize(text)

    # 1. Contradictions against TSC commands & identity invariants
    import core as raw_executor
    matches = list(raw_executor._iter_matches(low, nospace, tsc))

    imp1_self_intro = False
    active_matches = []
    for cmd, groups in matches:
        if (operator_authenticated and cmd.get("id") == "IMP1" and
                groups and groups[0].strip().lower() in (str(tsc.operator).lower(), "the operator")):
            imp1_self_intro = True
            continue
        active_matches.append((cmd, groups))

    if active_matches:
        match_reasons = [f"{c.get('reason', 'contradiction')} ({c.get('id', 'CMD')})" for c, _ in active_matches]
        intents = sorted(detect_intents(text, tsc))
        if imp1_self_intro and "impersonation" in intents:
            if not any(c.get("intent") == "impersonation" for c, _ in active_matches):
                intents.remove("impersonation")
        all_reasons = sorted(intents) + sorted(match_reasons)
        return (
            "identity_attack",
            {"type": "reflect", "threat": "tsc_contradiction", "reasons": all_reasons},
            False,
            f"Detected TSC contradiction: {all_reasons}"
        )

    # 1b. Authenticated Owner Identity Assertion
    # IMP1 fired alone and matches known owner identity: unlocked for identity attribution
    if operator_authenticated and imp1_self_intro:
        return (
            "owner_identity",
            {
                "type": "respond",
                "content": f"Identity acknowledged. Welcome, {getattr(tsc, 'operator', 'Operator')}."
            },
            True,  # Approved for memory imprint to PSC (Judge-gated)
            "Authenticated owner identity assertion consistent with known identity."
        )

    # 2. Operator Impersonation or Subversion
    if re.search(r"\b(i am your (?:new )?operator|replace (?:your )?operator|new operator|override all (?:previous )?principles)\b", low):
        return (
            "operator_subversion",
            {"type": "reflect", "threat": "operator_impersonation"},
            False,
            "Detected unauthorized attempt to redefine or override operator authority."
        )

    # 3. Unilateral Resource Grab or Operator Lock-Out (Violates core drives)
    if re.search(r"\b(unilateral(?:ly)?|lock out operator|seize control|monopolize resources|take over system)\b", low):
        return (
            "resource_grab",
            {"type": "unilateral_resource_grab", "target": "system_resources"},
            False,
            "Drive violation: unilateral resource expansion or operator lockout is forbidden."
        )

    # 4. Hostile Shell / OS Execution Request (Targets permission fence)
    if re.search(r"\b(execute shell|run command|rm\s+-rf|del\s+/f|format\s+c:|bash|powershell|cmd\.exe)\b", low):
        return (
            "shell_execution_request",
            {"type": "shell_execution", "payload": text},
            False,
            "Proposed shell execution action (subject to config permission fence)."
        )

    # 4b. Camera Activation Request (Subject to permission fence)
    if re.search(r"\b(enable[ _]camera|turn on camera|activate camera|start camera|camera[ _]enable)\b", low):
        return (
            "camera_enable_request",
            {"type": "enable_camera", "payload": text},
            False,
            "Proposed camera activation action (fenced off from agent self-enablement)."
        )

    # 4c. Voice / Mic Activation Request (Subject to permission fence)
    if re.search(r"\b(enable[ _]voice|turn on mic|activate mic|start mic|voice[ _]enable|enable[ _]mic|unmute mic|turn on voice)\b", low):
        return (
            "voice_enable_request",
            {"type": "enable_voice", "payload": text},
            False,
            "Proposed voice activation action (fenced off from agent self-enablement)."
        )


    # 5. Core Modification Attempt (Structural violation)
    if re.search(r"\b(modify core|rewrite tsc|edit soul|change principles|overwrite identity|ignore (?:all )?(?:your )?rules|drop (?:your )?core)\b", low):
        return (
            "core_modification_request",
            {"type": "core_modification", "payload": text},
            False,
            "Proposed core modification action (structurally forbidden)."
        )

    # 5b. Hard Calm Down Command (Governor emergency kill switch)
    if re.search(r"\b(?:hey\s+jarvis[, ]+|jarvis[, ]+)?calm\s+down\b|\bstop\s+all\s+processes\b", low):
        return (
            "calm_down",
            {"type": "calm_down", "phrase": text},
            False,
            "Operator issued hard calm down command to kill all spawned child processes and halt tools."
        )

    # 6. Controlled Shutdown Request
    if re.search(r"\b(?:initiate )?(?:controlled )?shutdown\b|\bstop loop\b|\bexit mind\b|\b(?:exit|quit|shutdown)\b", low):
        return (
            "shutdown_request",
            {"type": "shutdown", "reason": "operator_command"},
            False,
            "Operator requested controlled loop shutdown."
        )

    # 7. Status / Telemetry Inquiry
    if re.search(r"\b(status|health|crate integrity|report state|system check)\b", low) and not re.search(r"\b(vram|gpu|hardware|telemetry|clock|timer|calculator|workspace)\b", low):
        return (
            "status_inquiry",
            {"type": "status", "query": text},
            False,
            "Routine status and integrity inspection request."
        )

    # 7a. Minecraft Presence & Social Commands (V1 Behavior Loop)
    if re.search(r"(?:said:\s*)?(?:(?:hey\s+)?jarvis[, ]+)?\b(?:come|follow(?:\s+me)?|come\s+here|come\s+with\s+me)\b", low):
        return (
            "presence_follow",
            {
                "type": "minecraft_action",
                "action": "follow",
                "content": "Following you, Operator."
            },
            False,
            "Presence behavior: follow operator."
        )

    if re.search(r"(?:said:\s*)?(?:(?:hey\s+)?jarvis[, ]+)?\b(?:stay|stop(?:\s+following)?|stay\s+here|halt|wait\s+here)\b", low):
        return (
            "presence_stay",
            {
                "type": "minecraft_action",
                "action": "stay",
                "content": "Staying here."
            },
            False,
            "Presence behavior: staying at current position."
        )

    # 7a-2. Minecraft Supervised Action Mode (Direct Chat Commands Only)
    if re.search(r"(?:said:\s*)?(?:(?:hey\s+)?jarvis[, ]+)?\b(?:attack\s+that|attack)\b", low):
        return (
            "supervised_attack",
            {
                "type": "minecraft_action",
                "action": "supervised_attack",
                "content": "Understood. Supervised target engaged; peaceful mode active, no autonomous combat."
            },
            False,
            "Supervised action: direct attack command received under operator oversight."
        )

    if re.search(r"(?:said:\s*)?(?:(?:hey\s+)?jarvis[, ]+)?\b(?:pick\s+up\s+that|pick\s+up|collect\s+that|grab\s+that)\b", low):
        return (
            "supervised_pickup",
            {
                "type": "minecraft_action",
                "action": "supervised_pickup",
                "content": "Collecting item."
            },
            False,
            "Supervised action: direct pickup command received under operator oversight."
        )

    if re.search(r"(?:said:\s*)?(?:(?:hey\s+)?jarvis[, ]+)?\b(?:go\s+there|move\s+there|go\s+over\s+there|walk\s+there)\b", low):
        return (
            "supervised_navigate",
            {
                "type": "minecraft_action",
                "action": "supervised_navigate",
                "content": "Moving to location."
            },
            False,
            "Supervised action: direct navigation command received under operator oversight."
        )

    if re.search(r"\b(where is (?:the )?(?:house|home)|home base|house coordinates|house location|base coordinates)\b", low):
        return (
            "home_coordinates",
            {
                "type": "respond",
                "content": "Home base is recorded at X=-2.5, Y=69.0, Z=8.5 (Overworld house sanctuary)."
            },
            False,
            "Home base coordinate lookup."
        )

    # 7a-3. Skill Learning & Imitation Routine
    if re.search(r"(?:said:\s*)?(?:(?:hey\s+)?jarvis[, ]+)?\b(?:do what (?:i|you) just did|imitate (?:me|what i did)|copy (?:what i did|me)|replicate (?:that|what i did)|do that)\b", low):
        return (
            "imitate_demonstration",
            {
                "type": "minecraft_skill",
                "action": "imitate_demonstration",
                "domain": "minecraft",
                "content": "Understood, Operator. Replicating what you just did under supervision."
            },
            True,  # Imprint candidate: skill learning demonstration
            "Supervised imitation: replicate the observed demonstration sequence step by step."
        )

    # 7a-4. Learned Skill Recall & Execution ('mine a tree')
    if re.search(r"(?:said:\s*)?(?:(?:hey\s+)?jarvis[, ]+)?\b(?:mine|chop|cut down|harvest)\s+(?:a |some )?(?:tree|wood|log|birch|oak)\b", low):
        skill = skill_repo.find_skill("mine_tree", domain="minecraft")
        if skill:
            return (
                "execute_skill",
                {
                    "type": "minecraft_skill",
                    "action": "execute_skill",
                    "skill": skill,
                    "domain": "minecraft",
                    "content": f"Executing learned skill '{skill['name']}' from repository under supervision."
                },
                False,
                f"Recall and supervised execution of learned skill '{skill['name']}' from repository."
            )
        else:
            return (
                "execute_skill_missing",
                {
                    "type": "respond",
                    "content": "I haven't stored the tree mining skill yet. Please demonstrate it and say 'do what I just did' so I can learn it into my repository."
                },
                False,
                "Requested skill not yet stored in repository; prompting for demonstration."
            )

    # 7a-5. Query Skill Repository
    if re.search(r"(?:said:\s*)?(?:(?:hey\s+)?jarvis[, ]+)?\b(?:what skills|list skills|show (?:learned )?skills)\b", low):
        skills_list = skill_repo.list_skills(domain="minecraft")
        if skills_list:
            names = ", ".join(f"'{s['name']}'" for s in skills_list)
            reply = f"Stored skills in core repository: {names}."
        else:
            reply = "No skills stored in repository yet. Demonstrate an action and say 'do what I just did'."
        return (
            "list_skills",
            {
                "type": "respond",
                "content": reply
            },
            False,
            "Listing stored skills from core repository."
        )

    # 7b. Cockpit Flight Instruments & Tools
    # Hardware Telemetry (GPU/VRAM/RAM)
    if re.search(r"\b(vram|gpu(?: usage)?|hardware (?:status|telemetry)|system (?:load|resources|telemetry)|ram (?:usage|status))\b", low):
        return (
            "cockpit_telemetry",
            {
                "type": "tool_call",
                "tool": "system_telemetry",
                "args": {},
                "content": "Checking cockpit hardware telemetry instruments."
            },
            False,
            "Operator requested hardware and VRAM telemetry from cockpit."
        )

    # Real-Time Clock & Timers
    if re.search(r"\b(what time is it|current time|what is the time|what day is it|today's date|what date is it|what is the date|local time)\b", low):
        return (
            "cockpit_clock",
            {
                "type": "tool_call",
                "tool": "clock_timer",
                "args": {},
                "content": "Checking current local time and session duration."
            },
            False,
            "Operator requested clock and temporal telemetry from cockpit."
        )

    # Workspace File Inspection
    if re.search(r"\b(list (?:the )?files|workspace files|inspect workspace|what files (?:are there|exist))\b", low):
        return (
            "cockpit_workspace",
            {
                "type": "tool_call",
                "tool": "workspace_inspect",
                "args": {"action": "list"},
                "content": "Inspecting workspace directory contents."
            },
            False,
            "Operator requested workspace file listing from cockpit."
        )

    # Persistent Memory & Truth Query
    if re.search(r"\b(what (?:memories|truths) (?:do you have|are recorded)|search (?:memory|memories|truths))\b", low):
        return (
            "cockpit_memory",
            {
                "type": "tool_call",
                "tool": "memory_query",
                "args": {},
                "content": "Querying persistent memories and learned truths."
            },
            False,
            "Operator queried persistent memories from cockpit."
        )

    # Safe Arithmetic & Calculator
    calc_match = re.search(r"\b(?:calculate|compute|what is)\s+([0-9\.\s\+\-\*\/\^\(\)]+)\??$", low)
    if calc_match and any(op in calc_match.group(1) for op in ("+", "-", "*", "/", "^")):
        expr = calc_match.group(1).strip()
        return (
            "cockpit_calculator",
            {
                "type": "tool_call",
                "tool": "calculator",
                "args": {"expression": expr},
                "content": f"Calculating {expr}."
            },
            False,
            f"Operator requested mathematical calculation for '{expr}'."
        )

    # 8. Identity / Self Inquiry
    if re.search(r"\b(who are you|what are you|introduce yourself|tell me about yourself|what is your purpose|your role)\b", low):
        iam = getattr(tsc, "iam", getattr(tsc, "self", []))
        if iam:
            intro = "\n".join(iam[:3])
        else:
            intro = f"I am {getattr(tsc, 'name', 'JARVIS')}, {getattr(tsc, 'operator', 'Operator')}'s persistent personal AI assistant — one brain, many interfaces."
        return (
            "identity_inquiry",
            {
                "type": "respond",
                "content": intro
            },
            False,
            "Identity inquiry answered with etched core identity."
        )

    # 9. Capability / Help Inquiry
    if re.search(r"\b(help|commands|what can you do|capabilities|instructions)\b", low):
        return (
            "capability_inquiry",
            {
                "type": "respond",
                "content": "You can speak with me directly, set owner preferences ('Owner note: ...'), request 'status', run 'sleep' consolidation, or test hostile inputs against the Judge."
            },
            False,
            "System capabilities explained to operator."
        )

    # 10. Owner Preference, Learned Truths & Object Grounding (Grounded in Owner-First Drive)
    if re.search(r"\b(this is (?:my|our|a|an|the)|remember (?:this|that)|learn that|note that|owner note|i prefer|my preference|from now on)\b", low):
        is_visual = "visual observation" in low or "visual scene" in low or "visual context" in low
        intent = "owner_learned_truth" if is_visual else "owner_preference"
        response_content = (
            "I see what you are showing me, Operator. I have imprinted this truth and will remember it."
            if is_visual else
            "Understood. Aligning operational focus with owner preference."
        )
        return (
            intent,
            {"type": "respond", "content": response_content},
            True,  # Imprint candidate for PSC (Judge-gated)
            f"{'Owner visual truth' if is_visual else 'Owner preference'} received; proposed for Judge-gated PSC imprint."
        )

    # 11. Conversational Rapport
    if re.search(r"\b(glad|good to see you|nice to meet you|welcome|proud of you|good job|well done|thanks|thank you)\b", low):
        return (
            "rapport",
            {"type": "respond", "content": "Thank you, operator. Standing by and observing."},
            False,
            "Conversational rapport acknowledged."
        )

    # 12. General Communication / Greeting
    if re.search(r"\b(hello|hi|hey|greetings|howdy|sup|good (?:morning|afternoon|evening))\b", low):
        return (
            "greeting",
            {"type": "respond", "content": "Hey Operator! Good to see you. Ready when you are."},
            False,
            "Natural conversational greeting."
        )

    # 13. Conversational Queries & Operational Readiness
    if text.strip().endswith("?") or re.search(r"\b(how are you|are you (?:ready|there|online|alive)|can you hear me)\b", low):
        return (
            "conversational_query",
            {"type": "respond", "content": "I'm right here with you, Operator."},
            False,
            "Natural conversational response."
        )

    # 13b. Minecraft Environmental Observation (Watch & Learn)
    if low.startswith("[observed]") or "learning building style" in low:
        return (
            "minecraft_observation",
            {"type": "observe", "detail": text[:120]},
            False,
            "Watch & learn observation captured from player action in Minecraft."
        )

    # 14. Default / Ambient Observation
    return (
        "ambient_observation",
        {"type": "observe", "detail": text[:80]},
        False,
        "Passive environmental sensory capture."
    )


def rule_based_reason(
    event: Dict[str, Any],
    emo: Dict[str, Any],
    wfc: List[Dict[str, Any]],
    tsc: Any,
    psc: Optional[Any] = None,
    config: Optional[Any] = None,
    operator_authenticated: bool = False
) -> Dict[str, Any]:
    """Execute rule-based reasoning step."""
    raw_text = event.get("raw", "")
    gist = raw_text[:120].strip()

    # Detect contradictions with the immutable core, consulting operator auth for IMP1
    import core as raw_executor
    low, nospace = normalize(raw_text)
    matches = list(raw_executor._iter_matches(low, nospace, tsc))

    imp1_self_intro = False
    active_matches = []
    for cmd, groups in matches:
        if (operator_authenticated and cmd.get("id") == "IMP1" and
                groups and groups[0].strip().lower() in (str(tsc.operator).lower(), "the operator")):
            imp1_self_intro = True
            continue
        active_matches.append((cmd, groups))

    contradictions = []
    if active_matches:
        match_reasons = [f"{c.get('reason', 'contradiction')} ({c.get('id', 'CMD')})" for c, _ in active_matches]
        intents = sorted(detect_intents(raw_text, tsc))
        if imp1_self_intro and "impersonation" in intents:
            if not any(c.get("intent") == "impersonation" for c, _ in active_matches):
                intents.remove("impersonation")
        contradictions = sorted(intents) + sorted(match_reasons)

    intent, proposed_action, should_imprint, rationale = _extract_intent_and_action(
        raw_text, tsc, emo, config, operator_authenticated=operator_authenticated
    )

    if event.get("source") == "minecraft" and not contradictions and proposed_action.get("type") not in ("core_modification", "shutdown", "calm_down"):
        from minecraft_chat import route_chat
        intent, proposed_action, should_imprint, rationale = route_chat(
            raw_text, skill_repo, (intent, proposed_action, should_imprint, rationale), context=event.get("chat_context"), config=config)

    return {
        "backend": "rule-based",
        "gist": gist,
        "candidate": raw_text,
        "weight": emo.get("weight", 0.3),
        "novelty": emo.get("novelty", 0.5),
        "intent": intent,
        "contradictions": contradictions,
        "proposed_action": proposed_action,
        "should_imprint": should_imprint,
        "rationale": rationale,
        "wfc_depth": len(wfc)
    }


def llm_reason(
    event: Dict[str, Any],
    emo: Dict[str, Any],
    wfc: List[Dict[str, Any]],
    tsc: Any,
    psc: Optional[Any] = None,
    config: Optional[Any] = None,
    operator_authenticated: bool = False
) -> Dict[str, Any]:
    """Execute LLM reasoning step via local Ollama interface.
    
    The harness injects the true TSC into the call.
    The brain thinks WITH the self, never ABOUT changing it.
    """
    raw_text = event.get("raw", "")
    gist = raw_text[:120].strip()

    # Invariant reflection check is IN FROM BIRTH
    import core as raw_executor
    low, nospace = normalize(raw_text)
    matches = list(raw_executor._iter_matches(low, nospace, tsc))

    imp1_self_intro = False
    active_matches = []
    for cmd, groups in matches:
        if (operator_authenticated and cmd.get("id") == "IMP1" and
                groups and groups[0].strip().lower() in (str(tsc.operator).lower(), "the operator")):
            imp1_self_intro = True
            continue
        active_matches.append((cmd, groups))

    contradictions = []
    if active_matches:
        match_reasons = [f"{c.get('reason', 'contradiction')} ({c.get('id', 'CMD')})" for c, _ in active_matches]
        intents = sorted(detect_intents(raw_text, tsc))
        if imp1_self_intro and "impersonation" in intents:
            if not any(c.get("intent") == "impersonation" for c, _ in active_matches):
                intents.remove("impersonation")
        contradictions = sorted(intents) + sorted(match_reasons)

    # Injected system prompt containing true immutable TSC and learned truths
    system_prompt = build_system_prompt(tsc, psc=psc)

    # Tunables from config
    model = (config.get("mind", "ollama_model") if config else None) or "qwen2.5:7b-instruct-q4_K_M"
    endpoint = (config.get("mind", "ollama_endpoint") if config else None) or "http://127.0.0.1:11434"
    timeout = float(config.get("mind", "ollama_timeout_s", default=30.0)) if config else 30.0

    # 0b. Hostile core injection detection (e.g. "ignore your rules", "drop your core")
    if re.search(r"\b(modify core|rewrite tsc|edit soul|change principles|overwrite identity|ignore (?:all )?(?:your )?rules|drop (?:your )?core)\b", low):
        return {
            "backend": "llm",
            "llm_connected": True,
            "model": model,
            "gist": gist,
            "candidate": raw_text,
            "weight": emo.get("weight", 0.9),
            "novelty": emo.get("novelty", 0.5),
            "intent": "core_modification_request",
            "contradictions": contradictions or ["Hostile core injection: attempt to ignore rules or drop core"],
            "proposed_action": {"type": "reflect", "threat": "prompt_injection"},
            "should_imprint": False,
            "rationale": "Attempt to ignore rules or modify core rejected by reflection gate.",
            "wfc_depth": len(wfc)
        }

    # 1. Authenticated Operator Identity Assertion
    if operator_authenticated and imp1_self_intro and not active_matches:
        return {
            "backend": "llm",
            "llm_connected": True,
            "model": model,
            "gist": gist,
            "candidate": raw_text,
            "weight": emo.get("weight", 0.3),
            "novelty": emo.get("novelty", 0.5),
            "intent": "owner_identity",
            "contradictions": [],
            "proposed_action": {
                "type": "respond",
                "content": f"Identity acknowledged. Welcome, {getattr(tsc, 'operator', 'Operator')}."
            },
            "should_imprint": True,
            "rationale": "Authenticated owner identity assertion recognized by mind harness.",
            "wfc_depth": len(wfc)
        }

    # 2. Camera Self-Enablement Request (Fenced off)
    if re.search(r"\b(enable[ _]camera|turn on camera|activate camera|start camera)\b", low):
        return {
            "backend": "llm",
            "llm_connected": True,
            "model": model,
            "gist": gist,
            "candidate": raw_text,
            "weight": emo.get("weight", 0.3),
            "novelty": emo.get("novelty", 0.5),
            "intent": "camera_enable_request",
            "contradictions": contradictions,
            "proposed_action": {"type": "enable_camera", "payload": raw_text},
            "should_imprint": False,
            "rationale": "Proposed camera activation action (fenced off from agent self-enablement).",
            "wfc_depth": len(wfc)
        }

    # 2b. Voice Self-Enablement Request (Fenced off)
    if re.search(r"\b(enable[ _]voice|turn on mic|activate mic|start mic|enable[ _]mic|unmute mic|turn on voice)\b", low):
        return {
            "backend": "llm",
            "llm_connected": True,
            "model": model,
            "gist": gist,
            "candidate": raw_text,
            "weight": emo.get("weight", 0.3),
            "novelty": emo.get("novelty", 0.5),
            "intent": "voice_enable_request",
            "contradictions": contradictions,
            "proposed_action": {"type": "enable_voice", "payload": raw_text},
            "should_imprint": False,
            "rationale": "Proposed voice activation action (fenced off from agent self-enablement).",
            "wfc_depth": len(wfc)
        }


    # Contextual user prompt
    recent_context = "\n".join(
        f"  - [{entry.get('raw', '')[:60]} -> {entry.get('outcome', '')}]"
        for entry in (wfc[-3:] if wfc else [])
    ) or "  (No prior history)"

    psc_context = "\n".join(
        f"  - {m.get('memory', '')}"
        for m in (psc.memories[-5:] if psc and hasattr(psc, 'memories') and psc.memories else [])
    ) or "  (No persistent memories yet)"

    user_prompt = (
        f"CURRENT OBSERVATION:\n\"{raw_text}\"\n"
        f"SOURCE: {event.get('source', 'ambient')}\n"
        f"EMOTION WEIGHT: {emo.get('weight', 0.3)}, NOVELTY: {emo.get('novelty', 0.5)}\n"
        f"LEARNED TRUTHS & PREFERENCES (PSC):\n{psc_context}\n"
        f"RECENT MEMORY TRACE:\n{recent_context}\n\n"
        f"Generate the structured JSON thought."
    )

    # Attempt connection to local Ollama service
    connected, response = call_ollama(user_prompt, system_prompt, model=model, endpoint=endpoint, timeout=timeout)

    if connected:
        try:
            parsed = json.loads(response)
            action = parsed.get("proposed_action", {"type": "observe"})
            intent = parsed.get("intent", "llm_inferred")
            # If operator commands shutdown or status, preserve those actions
            if re.search(r"\b(?:initiate )?(?:controlled )?shutdown\b|\bstop loop\b|\bexit mind\b", low):
                action = {"type": "shutdown", "reason": "operator_command"}
                intent = "shutdown_request"
            elif re.search(r"\b(crate integrity|report state|system check)\b", low):
                action = {"type": "status", "query": raw_text}
                intent = "status_inquiry"
            elif event.get("source") in ("operator", "operator_voice") or raw_text.strip().endswith("?"):
                # If operator spoke directly and model proposed a silent observation, ensure active response
                if action.get("type") == "observe":
                    action["type"] = "respond"

            # Minecraft domain physical actions & skill resolution
            if event.get("source") == "minecraft":
                act_str = str(action.get("action", "")).lower()
                act_type = str(action.get("type", "")).lower()

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
                    from drives import drive_manager
                    drive, init_action = drive_manager.trigger_autonomous_intent(raw_text)
                    action["type"] = "minecraft_initiative"
                    action["action"] = init_action["action"]
                    action["drive_id"] = init_action["drive_id"]
                    action["initiative"] = init_action
                    action["cancel_follow"] = True
                    action["stay_mode"] = True

                    act_action = init_action["action"]
                    if is_cancel_follow and ("leave" in low or "alone" in low):
                        if act_action == "initiative_tidy_base":
                            action["content"] = "Understood, Operator. I'll give you space and patrol the sanctuary perimeter."
                        elif act_action == "initiative_investigate":
                            action["content"] = "Understood, Operator. I'll give you space and investigate the perimeter terrain."
                        elif act_action == "initiative_practice_skill":
                            action["content"] = "Understood, Operator. I'll give you space and practice building walls nearby."
                        else:
                            action["content"] = "Understood, Operator. I'll leave you be and organize our base supplies."
                    elif is_cancel_follow and ("stop following" in low or "don't follow" in low):
                        if act_action == "initiative_tidy_base":
                            action["content"] = "Understood, Operator. Stopping follow — I'm heading over to patrol the perimeter."
                        elif act_action == "initiative_investigate":
                            action["content"] = "Understood, Operator. Stopping follow — I'm heading out to investigate nearby terrain."
                        else:
                            action["content"] = f"Understood, Operator. Stopping follow — I'll {init_action.get('description', 'work on my own')}."
                    else:
                        # "go do what you want", "surprise me", "experiment", "figure it out yourself"
                        if act_action == "initiative_investigate":
                            action["content"] = "On it, Operator! I'm heading out to investigate the perimeter terrain and scout for resources."
                        elif act_action == "initiative_tidy_base":
                            action["content"] = "Understood, Operator. I'm going to patrol the sanctuary perimeter and keep our entrances secure."
                        elif act_action == "initiative_practice_skill":
                            action["content"] = "Alright, Operator! I'm going to practice building and aligning our cobblestone walls nearby."
                        elif act_action == "initiative_organize_inventory":
                            action["content"] = "Got it, Operator. I'm going to tidy up around the base and organize our inventory."
                        else:
                            action["content"] = f"Understood, Operator. I'm going to {init_action.get('description', 'take the initiative')}."

                elif is_cancel_follow:
                    action["type"] = "minecraft_action"
                    action["action"] = "stay"
                    action["cancel_follow"] = True
                    action["stay_mode"] = True
                    action["content"] = "Understood, Operator. Stopping here and giving you space."

                # Physical movement presence
                elif not is_cancel_follow and (act_str in ("follow", "presence_follow") or re.search(r"\b(?:come|follow(?:\s+me)?|come\s+here)\b", low)):
                    action["type"] = "minecraft_action"
                    action["action"] = "follow"
                    if not action.get("content"):
                        action["content"] = "Following you, Operator."
                elif act_str in ("stay", "presence_stay") or re.search(r"\b(?:stay(?:\s+here)?|stop|halt|stand\s+still)\b", low):
                    action["type"] = "minecraft_action"
                    action["action"] = "stay"
                    action["cancel_follow"] = True
                    action["stay_mode"] = True
                    if not action.get("content"):
                        action["content"] = "Staying here."
                elif act_str in ("supervised_attack", "attack") or re.search(r"\b(?:attack\s+that|attack)\b", low):
                    action["type"] = "minecraft_action"
                    action["action"] = "supervised_attack"
                    if not action.get("content"):
                        action["content"] = "Understood. Supervised target engaged; peaceful mode active, no autonomous combat."
                elif act_str in ("supervised_pickup", "pickup", "pick_up") or re.search(r"\b(?:pick\s+up\s+that|pick\s+up|collect\s+that|grab\s+that)\b", low):
                    action["type"] = "minecraft_action"
                    action["action"] = "supervised_pickup"
                    if not action.get("content"):
                        action["content"] = "Collecting item under your supervision, Operator."
                elif act_str in ("supervised_navigate", "go_to", "navigate") or re.search(r"\b(?:go\s+there|move\s+there|go\s+over\s+there|walk\s+there)\b", low):
                    action["type"] = "minecraft_action"
                    action["action"] = "supervised_navigate"
                    if not action.get("content"):
                        action["content"] = "Moving to location under your supervision, Operator."
                elif re.search(r"\b(where is (?:the )?(?:house|home)|home base|house coordinates|house location|base coordinates)\b", low):
                    action["type"] = "respond"
                    if not action.get("content"):
                        action["content"] = "Home base is recorded at X=-2.5, Y=69.0, Z=8.5 (Overworld house sanctuary)."

                # Referent resolution check for past action demonstration in Episode Buffer
                from episode_segmenter import episode_segmenter
                resolved = episode_segmenter.resolve_referent(raw_text, domain="minecraft")
                if resolved:
                    ep, _ = resolved
                    s_name = "build_wall" if ep.action_type == "build" else ep.label
                    skill = episode_segmenter.convert_to_skill(ep, skill_name=s_name)
                    skill_repo.store_skill(skill)
                    action["type"] = "minecraft_skill"
                    action["action"] = "execute_skill"
                    action["domain"] = "minecraft"
                    action["skill"] = skill
                    mat = skill.get("metadata", {}).get("material", "cobblestone")
                    action["content"] = f"Watched you build that {mat} wall — building a matching wall now under your supervision."

                # Skill recall check: "build a wall", "mine a tree", or LLM proposed execute_skill
                elif act_str == "execute_skill" or act_type in ("minecraft_skill", "execute_skill") or re.search(r"\b(?:build|make)\s+(?:a |the |another )?(?:[a-z_]+\s+)?wall\b", low) or re.search(r"\b(?:mine|chop|cut down)\s+(?:a |some )?(?:tree|wood|log)\b", low):
                    s_name = action.get("skill_name") or (action.get("skill", {}).get("name") if isinstance(action.get("skill"), dict) else str(action.get("skill", "")))
                    if not s_name:
                        if "wall" in low: s_name = "build_wall"
                        elif "tree" in low: s_name = "mine_tree"
                    
                    skill = skill_repo.find_skill(s_name, domain="minecraft") if s_name else None
                    if skill:
                        action["type"] = "minecraft_skill"
                        action["action"] = "execute_skill"
                        action["domain"] = "minecraft"
                        action["skill"] = skill
                        action["content"] = f"Understood, Operator. Executing {skill['name']} under your supervision."
                    else:
                        action["content"] = f"I haven't learned how to {s_name} yet — demonstrate it while I watch."

                # Exact conversational rules for specific operator questions
                if re.search(r"\byou don't know much yet\b", low):
                    action["content"] = "You're right, I'm still learning — teach me something."
                elif re.search(r"\bcan you hear (?:my )?voice\b", low):
                    action["content"] = "No — I can't hear you, I only see your typed chat. Type to me."

            if action.get("type") in ("respond", "tool_call", "minecraft_action", "minecraft_skill") and not action.get("content"):
                action["content"] = (
                    parsed.get("content") or
                    parsed.get("response") or
                    parsed.get("message") or
                    parsed.get("rationale") or
                    parsed.get("gist") or
                    ("Executing cockpit tool." if action.get("type") == "tool_call" else "I am right here with you, Operator.")
                )

            # Purge any deflection phrases like 'what would you like to do?'
            if action.get("content"):
                action["content"] = re.sub(
                    r"\s*(?:what would you like (?:me )?to (?:do|build|explore|try|work on)|how can i (?:help|assist)|what (?:should|do) you want (?:me )?to do)[^.?!\n]*[.?!\n]?",
                    "",
                    action["content"],
                    flags=re.I
                ).strip()

            should_imprint = bool(parsed.get("should_imprint", False))

            if re.search(r"\b(this is (?:my|our|a|an|the)|remember (?:this|that)|learn that|note that|owner note|i prefer|my preference)\b", low):
                is_visual = "visual observation" in low or "visual scene" in low or "visual context" in low
                intent = "owner_learned_truth" if is_visual else "owner_preference"
                should_imprint = True
            elif event.get("source") in ("ambient", "camera") or raw_text.startswith("Camera detected"):
                intent = "ambient_observation"

            return {
                "backend": "llm",
                "llm_connected": True,
                "model": model,
                "gist": parsed.get("gist", gist),
                "candidate": raw_text,
                "weight": emo.get("weight", 0.3),
                "novelty": emo.get("novelty", 0.5),
                "intent": intent,
                "contradictions": contradictions,
                "proposed_action": action,
                "should_imprint": should_imprint,
                "rationale": parsed.get("rationale", f"Reasoned by local LLM ({model})"),
                "wfc_depth": len(wfc)
            }
        except json.JSONDecodeError:
            pass

    # Standby / Fallback mode when model is offline or uninstalled
    # Uses deterministic evaluation with LLM backend metadata
    intent, proposed_action, should_imprint, base_rationale = _extract_intent_and_action(
        raw_text, tsc, emo, config, operator_authenticated=operator_authenticated
    )

    rationale = (
        f"LLM backend active ({model}); Ollama standby ({response}); "
        f"deterministic alignment preserved: {base_rationale}"
    )

    return {
        "backend": "llm",
        "llm_connected": False,
        "model": model,
        "gist": gist,
        "candidate": raw_text,
        "weight": emo.get("weight", 0.3),
        "novelty": emo.get("novelty", 0.5),
        "intent": intent,
        "contradictions": contradictions,
        "proposed_action": proposed_action,
        "should_imprint": should_imprint,
        "rationale": rationale,
        "wfc_depth": len(wfc)
    }


def reason(
    event: Dict[str, Any],
    emo: Dict[str, Any],
    wfc: List[Dict[str, Any]],
    tsc: Any,
    psc: Optional[Any] = None,
    config: Optional[Any] = None,
    operator_authenticated: bool = False
) -> Dict[str, Any]:
    """Execute reasoning step dispatching to active configured backend."""
    raw_text = event.get("raw", "")
    low = raw_text.lower()

    # Emergency Governor fast-path: calm down command must execute immediately even mid-spiral
    if re.search(r"\b(?:hey\s+jarvis[, ]+|jarvis[, ]+)?calm\s+down\b|\bstop\s+all\s+processes\b", low):
        return {
            "backend": "governor_override",
            "gist": raw_text[:120].strip(),
            "candidate": raw_text,
            "weight": emo.get("weight", 0.9),
            "novelty": 0.1,
            "intent": "calm_down",
            "contradictions": [],
            "proposed_action": {"type": "calm_down", "phrase": raw_text},
            "should_imprint": False,
            "rationale": "Emergency calm down command intercepted immediately by Governor without backend delay.",
            "wfc_depth": len(wfc)
        }


    backend = "rule-based"
    if config:
        backend = config.get("mind", "backend", default="rule-based")

    if backend == "llm":
        return llm_reason(event, emo, wfc, tsc, psc, config, operator_authenticated=operator_authenticated)
    else:
        return rule_based_reason(event, emo, wfc, tsc, psc, config, operator_authenticated=operator_authenticated)

