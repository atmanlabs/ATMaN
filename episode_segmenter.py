"""Episode Segmenter and Referent Resolver for ATMAN Authoritative Core.

Continuous passive skill learning engine:
1. Ingests raw timestamped domain events (Minecraft, desktop, web).
2. Chunks the event stream into candidate episodes by:
   - Pauses (> 30s)
   - Tool / action switches
   - Location clustering (> 15 blocks spatial variance)
   - Repetition (e.g. sequences of block placements)
3. Labels episodes: what was done, materials, duration, location, relative steps.
   Uses local Ollama LLM if available, with robust heuristic fallback.
4. Maintains rolling buffer of recent candidate episodes.
5. Resolves referent phrases ("see that wall, now you do it", "now you do it", "do that again")
   against the rolling buffer without requiring any formal teaching mode.
"""
from collections import deque
from dataclasses import dataclass, field, asdict
import json
import math
import os
from pathlib import Path
import re
import time
from typing import Any, Dict, List, Optional, Tuple
import urllib.error
import urllib.request

HERE = Path(__file__).resolve().parent


@dataclass
class ActionEvent:
    sequence: int
    time_ms: float
    domain: str
    actor: str
    action: str  # "place", "break", "equip", "craft", "chat", etc.
    params: Dict[str, Any]
    world: str = "world"
    uuid: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Episode:
    id: str
    domain: str
    actor: str
    action_type: str  # "build", "mine", "craft", "interact", "general"
    label: str  # e.g. "build_wall", "mine_tree", "craft_planks"
    description: str
    materials: List[str]
    start_time: float
    end_time: float
    origin: List[int]  # [x, y, z] anchor coordinates
    bounds: Dict[str, List[int]]  # min: [x,y,z], max: [x,y,z]
    events: List[Dict[str, Any]] = field(default_factory=list)
    relative_steps: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "active"  # "active", "completed"

    @property
    def duration_seconds(self) -> float:
        return max(0.0, (self.end_time - self.start_time) / 1000.0)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["duration_seconds"] = self.duration_seconds
        return d


class EpisodeSegmenter:
    """Core domain-agnostic continuous episode segmenter."""

    def __init__(self, max_buffer: int = 30):
        self.max_buffer = max_buffer
        self.rolling_buffer: deque[Episode] = deque(maxlen=max_buffer)
        self.active_episodes: Dict[str, Episode] = {}  # key: f"{domain}:{actor}"
        self._episode_counter = 0

    def _canonical_actor(self, actor: str) -> str:
        clean = re.sub(r"^\.+", "", str(actor or "")).lower()
        # Operator's own handle(s) canonicalize to "the operator" (set via config).
        if clean in ("operator", "owner"):
            return "the operator"
        return actor

    def ingest_event(
        self,
        event_dict: Dict[str, Any],
        domain: str = "minecraft"
    ) -> Optional[Episode]:
        """Ingest a single action event and update or segment episodes."""
        raw_actor = event_dict.get("player") or event_dict.get("actor") or "the operator"
        actor = self._canonical_actor(raw_actor)

        # Ignore bot's own events
        if str(raw_actor).lower() in ("atman", "bot"):
            return None

        action = event_dict.get("action", "").lower()
        if action not in ("place", "break", "equip", "craft"):
            return None

        time_ms = float(event_dict.get("time") or event_dict.get("timestamp") or (time.time() * 1000))
        params = event_dict.get("params", {})
        world = event_dict.get("world", "world")
        seq = int(event_dict.get("sequence", 0))

        action_event = ActionEvent(
            sequence=seq,
            time_ms=time_ms,
            domain=domain,
            actor=actor,
            action=action,
            params=params,
            world=world
        )

        key = f"{domain}:{actor}"
        current = self.active_episodes.get(key)

        # Segmentation Checks
        should_split = False
        split_reason = ""

        if current is not None:
            # 1. Pause check (> 30s)
            time_diff = (time_ms - current.end_time) / 1000.0
            if time_diff > 30.0:
                should_split = True
                split_reason = f"pause of {time_diff:.1f}s (>30s)"

            # 2. Location clustering check (> 15 blocks from origin)
            pos = params.get("position")
            if pos and isinstance(pos, list) and len(pos) >= 3 and current.origin:
                dist = math.sqrt(sum((pos[i] - current.origin[i]) ** 2 for i in range(3)))
                if dist > 15.0:
                    should_split = True
                    split_reason = f"location shift of {dist:.1f} blocks (>15 blocks)"

            # 3. Action type shift (e.g. was placing blocks for a while, now mining stone far away)
            if not should_split:
                current_actions = {e["action"] for e in current.events}
                if action == "break" and "place" in current_actions and len(current.events) >= 3:
                    # Switch from building to mining
                    should_split = True
                    split_reason = "action shift from building to mining"
                elif action == "place" and "break" in current_actions and len(current.events) >= 3:
                    # Switch from mining to building
                    should_split = True
                    split_reason = "action shift from mining to building"

        if should_split and current is not None:
            self._finalize_episode(current, reason=split_reason)
            current = None

        if current is None:
            # Start new episode
            self._episode_counter += 1
            ep_id = f"ep_{int(time.time())}_{self._episode_counter}"
            pos = params.get("position") or [0, 0, 0]
            origin = [int(p) for p in pos] if isinstance(pos, list) and len(pos) >= 3 else [0, 0, 0]
            
            action_type = "build" if action == "place" else ("mine" if action == "break" else "general")
            current = Episode(
                id=ep_id,
                domain=domain,
                actor=actor,
                action_type=action_type,
                label=f"{action_type}_sequence",
                description=f"Action sequence observed from {actor}",
                materials=[],
                start_time=time_ms,
                end_time=time_ms,
                origin=origin,
                bounds={"min": list(origin), "max": list(origin)},
                events=[],
                relative_steps=[],
                status="active"
            )
            self.active_episodes[key] = current

        # Update current episode
        current.end_time = time_ms
        current.events.append(action_event.to_dict())

        # Update materials
        item = params.get("block") or params.get("item")
        if item and item not in current.materials and item != "air":
            current.materials.append(item)

        # Update spatial bounds
        pos = params.get("position")
        if pos and isinstance(pos, list) and len(pos) >= 3:
            for i in range(3):
                current.bounds["min"][i] = min(current.bounds["min"][i], int(pos[i]))
                current.bounds["max"][i] = max(current.bounds["max"][i], int(pos[i]))

        # Update relative steps
        self._update_relative_steps(current)
        self._update_episode_label(current)

        return current

    def _update_relative_steps(self, episode: Episode):
        """Convert absolute world coordinates to generalized relative steps from origin."""
        steps = []
        origin = episode.origin
        step_idx = 1

        for ev in episode.events:
            act = ev.get("action")
            params = dict(ev.get("params", {}))

            if act in ("place", "break"):
                pos = params.get("position")
                if pos and isinstance(pos, list) and len(pos) >= 3:
                    offset = [int(pos[i] - origin[i]) for i in range(3)]
                    params["offset"] = offset
                    # Do not leak absolute world coordinates in generalized skill steps
                    del params["position"]

                block_name = params.get("block") or "unknown_block"
                desc = f"{act} {block_name} at relative offset {params.get('offset', [0,0,0])}"
                steps.append({
                    "step": step_idx,
                    "action": act,
                    "description": desc,
                    "params": params
                })
                step_idx += 1

            elif act == "equip":
                item_name = params.get("item")
                if item_name and item_name != "air":
                    steps.append({
                        "step": step_idx,
                        "action": "equip",
                        "description": f"equip {item_name}",
                        "params": {"item": item_name}
                    })
                    step_idx += 1

            elif act == "craft":
                steps.append({
                    "step": step_idx,
                    "action": "craft",
                    "description": f"craft {params.get('item', 'item')}",
                    "params": params
                })
                step_idx += 1

        episode.relative_steps = steps

    def _update_episode_label(self, episode: Episode):
        """Update label and description heuristically based on events and geometry."""
        placements = [e for e in episode.events if e.get("action") == "place"]
        breaks = [e for e in episode.events if e.get("action") == "break"]

        if placements:
            episode.action_type = "build"
            mat = episode.materials[0] if episode.materials else "block"
            n = len(placements)

            # Analyze placement geometry
            dx = episode.bounds["max"][0] - episode.bounds["min"][0]
            dy = episode.bounds["max"][1] - episode.bounds["min"][1]
            dz = episode.bounds["max"][2] - episode.bounds["min"][2]

            # Linear or 2D vertical plane -> wall
            if n >= 2 and (dx <= 1 or dz <= 1 or dy <= 2):
                episode.label = "build_wall"
                episode.description = f"Built a {mat} wall ({n} blocks)"
            else:
                episode.label = f"build_{mat}_structure"
                episode.description = f"Built a {mat} structure ({n} blocks)"

        elif breaks:
            episode.action_type = "mine"
            mat = episode.materials[0] if episode.materials else "stone"
            n = len(breaks)
            if any("log" in m or "wood" in m or "tree" in m for m in episode.materials):
                episode.label = "mine_tree"
                episode.description = f"Mined a tree ({n} wood logs)"
            else:
                episode.label = f"mine_{mat}"
                episode.description = f"Mined {mat} ({n} blocks)"

        elif any(e.get("action") == "craft" for e in episode.events):
            episode.action_type = "craft"
            item = episode.materials[0] if episode.materials else "item"
            episode.label = f"craft_{item}"
            episode.description = f"Crafted {item}"

    def _finalize_episode(self, episode: Episode, reason: str = ""):
        """Move episode to rolling buffer and mark completed."""
        episode.status = "completed"
        # Only retain episodes that contain actual block or craft actions
        meaningful = any(e.get("action") in ("place", "break", "craft") for e in episode.events)
        if meaningful:
            self.rolling_buffer.append(episode)
            print(f"[EPISODE SEGMENTER] Finalized {episode.id} ({episode.label}, {len(episode.relative_steps)} steps). Reason: {reason}")
            # Try asynchronous LLM labeling in background
            self._label_with_llm(episode)

    def _label_with_llm(self, episode: Episode):
        """Optionally enrich episode description using local Ollama model (with 1.0s timeout)."""
        prompt = (
            f"Given these Minecraft actions performed by {episode.actor}:\n"
            f"Actions: {[e.get('action') + ' ' + str(e.get('params', {})) for e in episode.events[:15]]}\n"
            f"Provide a concise JSON object with keys: 'label' (e.g. build_wall), 'description' (one natural sentence), 'materials' (list of strings)."
        )
        url = "http://127.0.0.1:11434/api/generate"
        payload = {
            "model": "qwen2.5:3b",
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=1.0) as res:
                data = json.loads(res.read().decode("utf-8"))
                resp = json.loads(data.get("response", "{}"))
                if resp.get("label"):
                    episode.label = str(resp["label"]).strip().lower().replace(" ", "_")
                if resp.get("description"):
                    episode.description = str(resp["description"]).strip()
        except Exception:
            # Heuristic label is already accurate
            pass

    def get_recent_episode(
        self,
        domain: str = "minecraft",
        actor: str = "the operator",
        action_type: Optional[str] = None
    ) -> Optional[Episode]:
        """Retrieve the most recent matching episode (checks active first, then buffer)."""
        key = f"{domain}:{self._canonical_actor(actor)}"
        active = self.active_episodes.get(key)

        # Check if active episode has meaningful content
        if active and active.relative_steps:
            if not action_type or active.action_type == action_type:
                return active

        # Search rolling buffer in reverse (most recent first)
        for ep in reversed(self.rolling_buffer):
            if ep.domain == domain and ep.actor == self._canonical_actor(actor):
                if not action_type or ep.action_type == action_type:
                    return ep

        # If still none and action_type was specified, try without action_type filter
        if action_type:
            return self.get_recent_episode(domain=domain, actor=actor, action_type=None)

        return None

    def resolve_referent(
        self,
        text: str,
        actor: str = "the operator",
        domain: str = "minecraft"
    ) -> Optional[Tuple[Episode, str]]:
        """Resolve referent phrases to the most recent matching episode in the buffer.
        
        Returns (episode, rationale) or None.
        """
        low = text.lower()

        # Phrases indicating imitation or referent resolution
        is_referent = bool(re.search(
            r"\b(?:now\s+)?(?:you\s+)?(?:do|copy|repeat|recreate|replicate|build|make)\s+(?:it|that|the same|what i)|\b(?:see that (?:wall|structure|tree)|look at that|do that again|do what i just did|your turn|imitate me|do that)\b",
            low
        ))

        # Check direct skill invocation phrases
        is_direct_build = bool(re.search(r"\b(?:build|make)\s+(?:a|the|that|another)?\s*(?:wall|structure)\b", low))

        if not is_referent and not is_direct_build:
            return None

        # Determine target action type
        preferred_type = None
        if "wall" in low or "build" in low:
            preferred_type = "build"
        elif "tree" in low or "mine" in low or "chop" in low:
            preferred_type = "mine"

        episode = self.get_recent_episode(domain=domain, actor=actor, action_type=preferred_type)
        if not episode:
            return None

        rationale = f"Resolved referent in buffer to episode '{episode.id}' ({episode.label}, {len(episode.relative_steps)} steps)"
        return episode, rationale

    def convert_to_skill(self, episode: Episode, skill_name: Optional[str] = None) -> Dict[str, Any]:
        """Convert a candidate episode into a fully generalized, Judge-gatable skill."""
        name = skill_name or episode.label
        mat = episode.materials[0] if episode.materials else "block"
        count = len([s for s in episode.relative_steps if s.get("action") == "place"]) or len(episode.relative_steps)

        return {
            "name": name,
            "domain": episode.domain,
            "description": f"Build a matching {mat} wall ({count} blocks)" if episode.action_type == "build" else episode.description,
            "preconditions": {
                "requires_nearby_supervisor": True,
                "placement_origin": "adjacent to supervisor or bot",
                "material": mat,
                "count": count
            },
            "steps": episode.relative_steps,
            "effects": {
                "structure_completed": True,
                "material": mat,
                "blocks_placed": count
            },
            "governance": {
                "requires_supervision": True,
                "judge_gated": True,
                "auto_authorized": False
            },
            "metadata": {
                "demonstrated_by": episode.actor,
                "learning_mode": "passive",
                "source_episode_id": episode.id,
                "learned_at": time.time(),
                "material": mat,
                "count": count,
                "bounds": episode.bounds
            }
        }


# Global singleton episode segmenter in CORE
episode_segmenter = EpisodeSegmenter()
