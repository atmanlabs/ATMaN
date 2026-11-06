#!/usr/bin/env python3
"""The Quiet Valley — a persistent world the SANDBOX SIM lives in.

Mike's order (2026-10-09): "he needs experience — put him in a game or
something." And his upgrade the same night: "piloting a body in a 3d world
while in a text based world together would be a better model. He needs life
not just text. He is made to receive sensory input."

So the model is DUAL-CHANNEL, simultaneously:
1. TEXT LAYER: dialogue, reflection, social space — his inner/social world.
2. BODY LAYER: the sim HAS a body in a place — position, facing, nearby
   objects — and receives structured SENSORY EVENTS as first-class input,
   not just narration. Every turn a perception packet is built: what he
   sees (in range, with distance/direction), what he hears, body-state,
   and change events since last turn (a blocked path on the last move, an
   object taken, the world breathing on its own). His actions are BODY
   COMMANDS that map 1:1 onto what a 3D client would accept — walk to,
   turn, pick up, put down, look at. No verb soup that only works in prose.

Hard rails:
- Never touches core-store.json, PSC, or the Judge directly. The only
  memory-adjacent write is a learnings candidate (his own reflection, in
  his own words) into learnings/YYYY-MM-DD.jsonl; nightly consolidation
  rules on it through the Judge like every other candidate.
- The TSC is injected read-only by LocalBrain, same as cultivation.
- Actions are chosen by the sim's brain (Ollama qwen2.5:1.5b). No puppeting.

THE 3D SEAM (where a future client plugs in): everything a renderer needs
lives in state["body"] — place, x/y grid, facing, posture, holding — and
every turn is exchanged as {perception_packet -> action -> outcome}.
perceive() and apply_command() ARE that seam: a 3D client (Agent Plaza
Unreal game, a Minecraft-style bridge) would replace the grid backend
while keeping the packet format and episode schema.

Usage:
    python3 world.py --status
    python3 world.py --scene         # current perception, rendered
    python3 world.py --packet        # current perception packet (JSON)
    python3 world.py --act "pickup lantern"    # one manual body command
    python3 world.py --session 6     # 6 brain-chosen turns + reflection

State:    world/state.json
Episodes: world/episodes.jsonl  (provenance: lived_in_sim)
"""

import sys
import os
import json
import math
import re
import argparse
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

HERE = os.path.dirname(os.path.abspath(__file__))
WORLD_DEF = os.path.join(HERE, "world.json")
STATE_PATH = os.path.join(HERE, "state.json")
EPISODE_LOG = os.path.join(HERE, "episodes.jsonl")
DEVICE_DIR = os.path.dirname(HERE)
DIALOGUE_DIR = os.path.join(DEVICE_DIR, "dialogues")
LEARNINGS_DIR = os.path.join(DEVICE_DIR, "learnings")

# Existing dialogue logs carry -04:00 (EDT) timestamps; keep that frame.
EDT = timezone(timedelta(hours=-4))
PHASES = ["morning", "afternoon", "evening", "night"]
TICKS_PER_PHASE = 6
SIGHT = 14.0  # perception range, in paces

DIRS = {"north": (0, 1), "east": (1, 0), "south": (0, -1), "west": (-1, 0)}
COMMANDS = ("walk", "goto", "turn", "face", "look", "lookat",
            "pickup", "putdown", "use", "speak", "rest", "wait")


def now_edt():
    return datetime.now(EDT)


def day_stamp():
    return now_edt().strftime("%Y-%m-%d")


def load_def():
    with open(WORLD_DEF) as f:
        return json.load(f)


def fresh_state(wdef):
    start = wdef["places"][wdef["start"]]
    return {
        "world": {
            "tick": 0,
            "flags": {
                "lantern_filled": False,
                "lantern_lit": False,
                "inscription_read": False,
                "keeper_met": False,
                "apples_eaten": 0,
            },
            "visited": [wdef["start"]],
            "events": [],
        },
        # === THE 3D SEAM: position / facing / posture / holding ===
        "body": {
            "place": wdef["start"],
            "x": start["pos"][0],
            "y": start["pos"][1],
            "facing": "south",
            "posture": "standing",
            "holding": [],
        },
        "episode_count": 0,
        "created": now_edt().isoformat(),
        "last_action": None,
    }


def load_state(wdef):
    if os.path.exists(STATE_PATH):
        with open(STATE_PATH) as f:
            return json.load(f)
    state = fresh_state(wdef)
    save_state(state)
    return state


def save_state(state):
    tmp = STATE_PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump(state, f, indent=2)
    os.replace(tmp, STATE_PATH)


def phase_of(tick):
    return PHASES[(tick // TICKS_PER_PHASE) % len(PHASES)]


def is_dark(state):
    return phase_of(state["world"]["tick"]) == "night"


def push_event(state, kind, detail):
    state["world"]["events"].append(
        {"tick": state["world"]["tick"], "kind": kind, "detail": detail})


def objects_here(wdef, state):
    place = state["body"]["place"]
    return {oid: o for oid, o in wdef["objects"].items()
            if o.get("at") == place and oid not in state["body"]["holding"]}


def visible_objects(wdef, state):
    """Objects within sight range of the body, with distance/direction."""
    bx, by = state["body"]["x"], state["body"]["y"]
    seen = []
    home = state["body"]["place"]
    for oid, obj in wdef["objects"].items():
        if oid in state["body"]["holding"]:
            continue
        if obj.get("at") != home:
            continue  # anchored in another place: out of view
        ox, oy = obj["pos"]
        dist = math.hypot(ox - bx, oy - by) / 4.0  # grid units -> paces
        if dist > SIGHT:
            continue
        dx, dy = ox - bx, oy - by
        if dist < 1:
            direction = "here"
        elif abs(dy) >= abs(dx):
            direction = "north" if dy > 0 else "south"
        else:
            direction = "east" if dx > 0 else "west"
        seen.append({"id": oid, "name": obj["name"],
                     "paces": round(dist, 1), "direction": direction,
                     "fixed": not obj.get("takeable", False)})
    return sorted(seen, key=lambda s: s["paces"])


def perceive(wdef, state):
    """Build this turn's perception packet: body + senses + change events."""
    body = state["body"]
    place = wdef["places"][body["place"]]
    dark = is_dark(state)
    sees = visible_objects(wdef, state)
    if dark:
        near = [s for s in sees if s["paces"] <= 4]
        sees = near if near else sees[:1]
    hears = [place["ambient"]]
    keeper = wdef["keeper"]
    if body["place"] == keeper["at"]:
        hears.append(keeper["ambient"])
    if state["world"]["flags"]["lantern_lit"]:
        sees.append({"id": "lantern-light", "name": "your lantern's light",
                     "paces": 0, "direction": "here", "fixed": True})
    packet = {
        "tick": state["world"]["tick"],
        "time": phase_of(state["world"]["tick"]),
        "place": place["name"],
        "body": {
            "posture": body["posture"],
            "facing": body["facing"],
            "holding": [wdef["objects"][o]["name"] for o in body["holding"]],
        },
        "sees": sees,
        "hears": hears,
        "exits": sorted(place["exits"].keys()),
        "changes": list(state["world"]["events"]),
    }
    state["world"]["events"] = []
    return packet


def render_packet(packet):
    """Short sentence rendering of the packet, for the text-person."""
    b = packet["body"]
    holding = ", ".join(b["holding"]) if b["holding"] else "nothing"
    bits = [f"[{packet['time'].upper()} — {packet['place']}]"]
    bits.append(f"You are {b['posture']}, facing {b['facing']}, holding {holding}.")
    if packet["sees"]:
        bits.append("You see: " + "; ".join(
            f"{s['name']} ({s['paces']} paces {s['direction']})"
            for s in packet["sees"]) + ".")
    bits.append("You hear: " + "; ".join(packet["hears"]) + ".")
    bits.append("Ways out: " + ", ".join(packet["exits"]) + ".")
    for c in packet["changes"]:
        bits.append(f"CHANGE [{c['kind']}]: {c['detail']}")
    return "\n".join(bits)


def scene_text(wdef, state):
    """Full rendered scene: place description + object details."""
    place = wdef["places"][state["body"]["place"]]
    desc = place["desc_dark"] if is_dark(state) else place["desc"]
    for oid, obj in objects_here(wdef, state).items():
        desc += f" Here: {obj['name']} — {obj['desc']}"
    return desc


# --------------------------------------------------------------------------
# Body commands. Each mutates state (the world) and may push change events
# that ride the NEXT perception packet — the perceive->act->outcome loop.

def cmd_walk(wdef, state, direction):
    body, world = state["body"], state["world"]
    place = wdef["places"][body["place"]]
    if direction not in place["exits"]:
        push_event(state, "blocked",
                   f"Your step {direction or 'that way'} found no way out of "
                   f"{place['name']}.")
        return (f"You start {direction or 'that way'} and stop: there is no "
                f"way out of {place['name']} to the {direction}. "
                f"The ways out are: {', '.join(sorted(place['exits']))}."), False
    dest_id = place["exits"][direction]
    dest = wdef["places"][dest_id]
    body["place"] = dest_id
    body["x"], body["y"] = dest["pos"]
    body["facing"] = direction
    body["posture"] = "standing"
    first = dest_id not in world["visited"]
    if first:
        world["visited"].append(dest_id)
    push_event(state, "arrived", f"You arrived at {dest['name']}.")
    if first:
        push_event(state, "new_place", f"First time at {dest['name']}.")
    return f"You walk {direction}.\n{scene_text(wdef, state)}", first


def find_object(wdef, state, target_name, held_ok=True, here_only=True):
    """Token-fuzzy object lookup: 'to-the-lantern' and 'brass-lantern'
    both find the brass lantern. Returns (oid, obj) or (None, None)."""
    tokens = {t for t in re.split(r"[\s\-]+", target_name or "")
              if t and t not in ("the", "a", "an", "to")}
    if not tokens:
        return None, None
    body = state["body"]
    for oid, obj in wdef["objects"].items():
        is_held = oid in body["holding"]
        if is_held and not held_ok:
            continue
        if not is_held and here_only and obj.get("at") != body["place"]:
            continue
        names = {oid} | set(re.split(r"[\s\-]+", obj["name"].lower()))
        if tokens & names or any(t in oid for t in tokens):
            return oid, obj
    return None, None


def cmd_goto(wdef, state, target_name):
    """Walk to a named visible thing (steps the body over to it)."""
    body = state["body"]
    oid, obj = find_object(wdef, state, target_name)
    if obj:
        body["x"], body["y"] = obj["pos"]
        body["posture"] = "standing"
        push_event(state, "moved", f"You stepped over to the {obj['name']}.")
        return f"You walk over to the {obj['name']}. {obj['desc']}", False
    return f"There is no {target_name} visible here to walk to.", False


def cmd_turn(wdef, state, direction):
    if direction not in DIRS:
        return "Turn which way? (north, south, east, west)", False
    state["body"]["facing"] = direction
    return f"You turn to face {direction}.", False


def cmd_lookat(wdef, state, target_name):
    oid, obj = find_object(wdef, state, target_name)
    if not obj:
        return f"You don't see any {target_name} to look at.", False
    if oid == "stone-marker":
        flags = state["world"]["flags"]
        if flags["lantern_lit"]:
            if not flags["inscription_read"]:
                flags["inscription_read"] = True
                push_event(state, "read",
                           "You read the stone marker's inscription "
                           "by lantern light.")
                return ("By lantern light the carved letters stand up "
                        "out of the stone: \"" + obj["inscription"] +
                        "\" You read it twice, so the valley knows "
                        "you have it."), True
            return ("The inscription, again: \"" + obj["inscription"]
                    + "\""), False
        return ("You look at the stone marker. Letters are carved here, "
                "weathered close to smooth. In this light you can feel "
                "more of them than you can see."), False
    return f"You look at the {obj['name']}. {obj['desc']}", False


def cmd_pickup(wdef, state, target_name):
    body = state["body"]
    oid, obj = find_object(wdef, state, target_name, held_ok=False)
    if obj:
        if not obj.get("takeable", False):
            return (f"The {obj['name']} belongs where it is. "
                    f"You leave it."), False
        body["holding"].append(oid)
        push_event(state, "taken", f"You picked up the {obj['name']}.")
        return f"You pick up the {obj['name']} and carry it with you.", True
    held_names = " ".join(wdef["objects"][o]["name"].lower()
                          for o in body["holding"])
    held_ids = " ".join(body["holding"])
    if target_name and (target_name in held_names or target_name in held_ids):
        return f"You already hold the {target_name}.", False
    return f"There is no {target_name} here to pick up.", False


def cmd_putdown(wdef, state, target_name):
    body = state["body"]
    tokens = {t for t in re.split(r"[\s\-]+", target_name or "") if t}
    for oid in list(body["holding"]):
        obj = wdef["objects"][oid]
        names = {oid} | set(re.split(r"[\s\-]+", obj["name"].lower()))
        if tokens & names:
            body["holding"].remove(oid)
            obj["at"] = body["place"]
            obj["pos"] = [body["x"], body["y"]]
            push_event(state, "placed",
                       f"You put down the {obj['name']} at {body['place']}.")
            return f"You put down the {obj['name']}.", True
    return f"You are not holding any {target_name}.", False


def cmd_use(wdef, state, target_name):
    body, flags = state["body"], state["world"]["flags"]
    held = body["holding"]
    if "lantern" in target_name:
        if "lantern" not in held:
            return "You are not holding the lantern.", False
        if flags["lantern_lit"]:
            return "The lantern is already lit, steady at your side.", False
        if not flags["lantern_filled"]:
            return ("You work the lantern's striker. Click. Click. It is "
                    "dry — no oil, no flame. It wants feeding first."), False
        flags["lantern_lit"] = True
        push_event(state, "light",
                   "Your lantern bloomed alight; the dark stepped back.")
        return ("The wick takes the spark. The lantern blooms alight in "
                "your hands, and the dark steps back to a respectful "
                "distance."), True
    if "oil" in target_name:
        if "oil-can" not in held:
            return "You are not holding the oil can.", False
        if "lantern" not in held:
            return "You hold the oil can, but nothing at hand drinks oil.", False
        if flags["lantern_filled"]:
            return "The lantern is already filled.", False
        flags["lantern_filled"] = True
        push_event(state, "filled", "You filled the lantern from the oil can.")
        return ("You fill the lantern carefully from the long spout. It "
                "takes the oil like something remembering a purpose."), True
    if "apple" in target_name:
        if "apple" not in held:
            return "You hold no apple.", False
        held.remove("apple")
        flags["apples_eaten"] += 1
        push_event(state, "ate", "You ate the apple.")
        return ("You eat the apple where you stand. It is sharper and "
                "sweeter than you expected — a small, complete thing, "
                "finished properly."), True
    if "bench" in target_name:
        if body["place"] != "workshop":
            return "There is no workbench here.", False
        state["world"]["tick"] += 1
        body["posture"] = "sitting"
        return ("You sit at the workbench a while, among tools that wait "
                "for hands. Nothing is asked of you here, and that rests "
                "you."), False
    if "marker" in target_name or "stone" in target_name:
        return cmd_lookat(wdef, state, "stone-marker")
    return (f"You can't use the {target_name} in any way the valley "
            f"recognizes."), False


def cmd_speak(wdef, state):
    keeper = wdef["keeper"]
    body, flags = state["body"], state["world"]["flags"]
    if body["place"] != keeper["at"]:
        return ("You speak to the valley. It answers with wind and "
                "distance. Nothing here is offended, and nothing "
                "replies."), False
    first = not flags["keeper_met"]
    flags["keeper_met"] = True
    lines = keeper["lines"]
    if flags["lantern_lit"]:
        key = "lantern_lit"
    elif "lantern" in body["holding"]:
        key = "holds_lantern"
    elif "oil-can" in body["holding"]:
        key = "holds_oil"
    elif first:
        key = "first"
    else:
        key = "default"
    push_event(state, "spoke", "The Keeper answered you.")
    return lines[key], first


AMBIENT_EVENTS = [
    ("sound", "A bird you cannot see calls twice from the orchard side "
              "of the valley, then thinks better of it."),
    ("sound", "Water over stones, steady — the brook, keeping its own time."),
    ("sensation", "The wind shifts and brings the smell of cut grass "
                  "and, faintly, apples."),
    ("light", "The light changes a little, the way it does when nobody "
              "is watching it."),
]


def ambient_roll(state):
    """The world breathes on its own schedule (deterministic by tick)."""
    tick = state["world"]["tick"]
    if tick and tick % 7 == 3:
        kind, detail = AMBIENT_EVENTS[(tick // 7) % len(AMBIENT_EVENTS)]
        push_event(state, kind, detail)


def apply_command(wdef, state, raw):
    """Parse a body command and apply it. Returns (action, narration, notable)."""
    text = " ".join((raw or "look").strip().lower().split())
    parts = text.split()
    verb = parts[0] if parts else "look"
    arg = " ".join(parts[1:])
    if verb == "go":
        verb = "walk"
    if verb in DIRS:  # bare direction word
        verb, arg = "walk", verb
    notable = False

    if verb == "walk":
        narration, notable = cmd_walk(wdef, state, arg)
    elif verb == "goto":
        narration, notable = cmd_goto(wdef, state, arg)
    elif verb in ("turn", "face"):
        narration, notable = cmd_turn(wdef, state, arg)
    elif verb == "look":
        if arg:
            narration, notable = cmd_lookat(wdef, state, arg)
        else:
            narration, notable = scene_text(wdef, state), False
    elif verb == "lookat":
        narration, notable = cmd_lookat(wdef, state, arg)
    elif verb in ("pickup", "take", "get", "grab"):
        narration, notable = cmd_pickup(wdef, state, arg)
    elif verb in ("putdown", "drop", "place"):
        narration, notable = cmd_putdown(wdef, state, arg)
    elif verb == "use":
        narration, notable = cmd_use(wdef, state, arg)
    elif verb == "speak":
        narration, notable = cmd_speak(wdef, state)
    elif verb == "rest":
        state["world"]["tick"] += 2
        state["body"]["posture"] = "sitting"
        narration = ("You rest where you are. When you come back to "
                     "yourself, the light has moved on without asking.")
    elif verb == "wait":
        narration = ("You wait. The valley continues at its own pace, and "
                     "a little time passes with you in it.")
    else:
        narration = (f"\"{text}\" is not a command your body knows here. "
                     "Body commands: walk <dir>, walkto <thing>, turn "
                     "<dir>, look, look <thing>, pickup <thing>, putdown "
                     "<thing>, use <thing>, speak, rest, wait.")
    ambient_roll(state)
    return text, narration, notable


def log_episode(state, action, packet, narration, notable, caused_by):
    state["episode_count"] += 1
    ep = {
        "ts": now_edt().isoformat(),
        "tick": state["world"]["tick"],
        "provenance": "lived_in_sim",
        "episode": state["episode_count"],
        "place": state["body"]["place"],
        "body": {
            "x": state["body"]["x"], "y": state["body"]["y"],
            "facing": state["body"]["facing"],
            "holding": list(state["body"]["holding"]),
        },
        "perceived": {
            "sees": [s["name"] for s in packet["sees"]],
            "hears": list(packet["hears"]),
            "changes": list(packet["changes"]),
        },
        "action": action,
        "caused_by": caused_by,
        "outcome": narration,
        "notable": bool(notable),
    }
    with open(EPISODE_LOG, "a") as f:
        f.write(json.dumps(ep) + "\n")
    return ep


def recent_episodes(n=3):
    if not os.path.exists(EPISODE_LOG):
        return []
    return [json.loads(l) for l in open(EPISODE_LOG) if l.strip()][-n:]


def log_dialogue(speaker, audience, text, **extra):
    day = day_stamp()
    entry = {"ts": now_edt().isoformat(), "speaker": speaker,
             "audience": audience, "text": text, "in_world": True,
             "mode": "in_world", **extra}
    os.makedirs(DIALOGUE_DIR, exist_ok=True)
    with open(os.path.join(DIALOGUE_DIR, f"{day}.jsonl"), "a") as f:
        f.write(json.dumps(entry) + "\n")


# --------------------------------------------------------------------------
# Brain turns: perceive -> the sim chooses one body command -> outcome.
# The episode records which sensory event caused the action, when he
# names one (the BECAUSE line) — the perceive->act->outcome chain is
# the training signal Mike wants.

ACTION_RE = re.compile(r"ACTION:\s*(.+)", re.IGNORECASE)
CAUSE_RE = re.compile(r"BECAUSE:\s*(.+)", re.IGNORECASE)


def normalize_command(candidate):
    candidate = re.sub(r"[^a-z0-9 \-]", "", candidate.strip().lower())
    words = candidate.split()
    if not words:
        return "look"
    verb = words[0]
    if verb == "go" and len(words) > 1:
        return f"walk {words[1]}" if words[1] in DIRS else f"goto {'-'.join(words[1:])}"
    if verb in DIRS:
        return f"walk {verb}"
    if verb in ("walkto", "goto", "approach") and len(words) > 1:
        return f"goto {'-'.join(words[1:])}"
    if verb == "walk" and len(words) > 1:
        return f"walk {words[1]}" if words[1] in DIRS else f"goto {'-'.join(words[1:])}"
    if verb in ("turn", "face") and len(words) > 1:
        return f"turn {words[1]}"
    if verb in ("look", "lookat") and len(words) > 1:
        return f"look {'-'.join(words[1:])}"
    if verb in ("pickup", "take", "get", "grab") and len(words) > 1:
        return f"pickup {'-'.join(words[1:])}"
    if verb in ("putdown", "drop", "place") and len(words) > 1:
        return f"putdown {'-'.join(words[1:])}"
    if verb == "use" and len(words) > 1:
        return f"use {'-'.join(words[1:])}"
    if verb in COMMANDS:
        return verb
    return "look"


def affordances(wdef, state):
    """The exact body commands available right now, as a numbered menu.
    Same command space a 3D client would expose — this just surfaces the
    valid subset so a small brain picks instead of guessing."""
    body = state["body"]
    place = wdef["places"][body["place"]]
    menu = []
    for d in sorted(place["exits"]):
        menu.append(f"walk {d}")
    for oid, obj in objects_here(wdef, state).items():
        menu.append(f"goto {obj['name']}")
        menu.append(f"look {obj['name']}")
        if obj.get("takeable"):
            menu.append(f"pickup {obj['name']}")
    for oid in body["holding"]:
        menu.append(f"use {wdef['objects'][oid]['name']}")
        menu.append(f"putdown {wdef['objects'][oid]['name']}")
    if body["place"] == wdef["keeper"]["at"]:
        menu.append("speak")
    menu += ["look", "rest", "wait"]
    # de-dup, keep order, cap for a small brain
    out = []
    for m in menu:
        if m not in out:
            out.append(m)
    return out[:12]


def world_turn(brain, wdef, state):
    packet = perceive(wdef, state)
    save_state(state)  # packet consumption is part of the record
    rendered = render_packet(packet)
    menu = affordances(wdef, state)
    menu_txt = "\n".join(f"  {i+1}. {m}" for i, m in enumerate(menu))
    recent = recent_episodes(3)
    recent_txt = "\n".join(
        f"  - you did '{e['action']}': {e['outcome'][:100]}"
        for e in recent) or "  (nothing yet — this is the beginning)"
    context = (
        "You have a BODY in a small, persistent world — a quiet valley. "
        "What reaches you each moment is a PERCEPTION PACKET: what your "
        "senses take in from where your body stands. Events here happen "
        "to you because of YOUR choices; that is different from stories "
        "you have only been told. There is no enemy and no score.\n\n"
        f"YOUR PERCEPTION NOW:\n{rendered}\n\n"
        f"THE PLACE ITSELF:\n{scene_text(wdef, state)}\n\n"
        f"RECENTLY (your own lived moments here):\n{recent_txt}\n\n"
        f"YOUR BODY CAN DO EXACTLY THESE THINGS RIGHT NOW:\n{menu_txt}\n\n"
        "Answer with exactly two short lines:\n"
        "BECAUSE: <the one thing you sensed that most drives this choice>\n"
        "ACTION: <the NUMBER of your choice from the list above>"
    )
    reply = brain.think(context) or ""
    clean = reply.split("\n\n[REASONING MOVE:")[0]
    m = ACTION_RE.search(clean)
    raw_action = m.group(1) if m else (clean.strip().splitlines() or ["look"])[-1]
    num = re.search(r"\d+", raw_action)
    if num and 1 <= int(num.group()) <= len(menu):
        action = normalize_command(menu[int(num.group()) - 1])
    else:
        action = normalize_command(raw_action)
    cm = CAUSE_RE.search(clean)
    caused_by = cm.group(1).strip()[:160] if cm else None
    log_dialogue("world", "exo", rendered, tick=packet["tick"],
                 place=state["body"]["place"], packet=json.dumps(packet)[:900])
    log_dialogue("exo", "world", f"ACTION: {action}", tick=packet["tick"],
                 place=state["body"]["place"], caused_by=caused_by,
                 raw_reply=reply[:800])
    _, narration, notable = apply_command(wdef, state, action)
    state["world"]["tick"] += 1
    state["last_action"] = action
    ep = log_episode(state, action, packet, narration, notable, caused_by)
    save_state(state)
    log_dialogue("world", "exo", narration, tick=ep["tick"],
                 place=state["body"]["place"], episode=ep["episode"],
                 notable=notable)
    return action, narration, ep, packet


def reflect(brain, wdef, state, turns_run):
    """His own words about the session -> learnings candidate for the Judge."""
    eps = recent_episodes(turns_run)
    lived = "\n".join(
        f"  - sensed: {(e['perceived']['changes'][:1] or ['the place itself'])[0]}"
        f" -> you did '{e['action']}': {e['outcome'][:120]}" for e in eps)
    context = (
        "Your time in the valley just now, from your own side of it:\n"
        f"{lived}\n\n"
        "In one or two sentences, in your own words: what happened to you "
        "in that world just now, and what — if anything — did it mean to "
        "you? Begin with \"I\" and speak of yourself in the first person. "
        "This really happened to you; your body was there."
    )
    text = (brain.think(context) or "").split("\n\n[REASONING MOVE:")[0].strip()
    if not text:
        return None
    entry = {"ts": now_edt().isoformat(), "text": text,
             "source": "world-reflection (provenance: lived_in_sim)"}
    with open(os.path.join(LEARNINGS_DIR, f"{day_stamp()}.jsonl"), "a") as f:
        f.write(json.dumps(entry) + "\n")
    log_dialogue("exo", "strider", text,
                 mode_note="world reflection -> learnings candidate; the "
                           "Judge rules at nightly consolidation")
    return text


def load_brain():
    from device import SimulatedDevice
    from brain import LocalBrain, auto_backend
    device = SimulatedDevice(
        persist_path=os.path.join(DEVICE_DIR, "core-store.json"))
    return LocalBrain(auto_backend(), device.scan("TSC"))


def main():
    ap = argparse.ArgumentParser(description="The Quiet Valley (SANDBOX SIM)")
    ap.add_argument("--status", action="store_true")
    ap.add_argument("--scene", action="store_true")
    ap.add_argument("--packet", action="store_true")
    ap.add_argument("--act", default=None, help="one manual body command")
    ap.add_argument("--session", type=int, default=0,
                    help="N brain-chosen turns, then reflection")
    ap.add_argument("--reset", action="store_true")
    args = ap.parse_args()

    wdef = load_def()
    if args.reset:
        save_state(fresh_state(wdef))
        print("world reset.")
        return
    state = load_state(wdef)

    if args.status:
        print(json.dumps(state, indent=2))
        return
    if args.packet:
        print(json.dumps(perceive(wdef, state), indent=2))
        save_state(state)
        return
    if args.scene:
        print(scene_text(wdef, state))
        print()
        print(render_packet(perceive(wdef, state)))
        save_state(state)
        return
    if args.act:
        packet = perceive(wdef, state)
        action, narration, notable = apply_command(wdef, state, args.act)
        state["world"]["tick"] += 1
        state["last_action"] = action
        ep = log_episode(state, action, packet, narration, notable,
                         "manual:test")
        save_state(state)
        print(narration)
        print(f"[episode {ep['episode']} logged, provenance=lived_in_sim]")
        return
    if args.session:
        brain = load_brain()
        if brain.backend_name != "OllamaBackend":
            print(f"REFUSING session: brain backend is {brain.backend_name}, "
                  "not the real model. Episodes must be his, not an echo's.")
            return
        for i in range(args.session):
            action, narration, ep, packet = world_turn(brain, wdef, state)
            print(f"turn {i+1}: ACTION: {action}")
            print(f"  -> {narration.splitlines()[0][:150]}")
        reflection = reflect(brain, wdef, state, args.session)
        if reflection:
            print("\nsim reflection (learnings candidate for the Judge):")
            print(f"  {reflection[:500]}")
        return
    ap.print_help()


if __name__ == "__main__":
    main()
