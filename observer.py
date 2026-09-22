"""Continuous Observer for ATMAN Core.

Always-on server-side domain observation loop:
1. Minecraft adapter: polls Paper server plugin (JarvisDemonstrations on 127.0.0.1:18791)
   for server-side player events:
   - Block place / break (coordinates + block type)
   - Equipment / held item
   - Crafting recipes
   - Never limited to bot visual chunk range!
2. Attributes every event to the actor (the operator).
3. Streams timestamped action events into WFC and feeds the EpisodeSegmenter.
4. Domain-agnostic: accepts events from Minecraft, desktop, web, or custom domain adapters.
"""
import json
from pathlib import Path
import threading
import time
from typing import Any, Dict, List, Optional
import urllib.error
import urllib.request

from episode_segmenter import episode_segmenter

HERE = Path(__file__).resolve().parent


class ContinuousObserver:
    """Core domain-agnostic continuous action observer."""

    def __init__(self, poll_interval: float = 0.4):
        self.poll_interval = poll_interval
        self.cursor: int = 0
        self.running: bool = False
        self._thread: Optional[threading.Thread] = None
        self._mind = None  # Reference to MindLoop instance for WFC injection
        self.minecraft_endpoint = "http://127.0.0.1:18791/events"

    def attach_mind(self, mind):
        """Attach active MindLoop instance for WFC streaming."""
        self._mind = mind

    def start(self):
        """Start continuous observation thread."""
        if self.running:
            return
        self.running = True
        self._thread = threading.Thread(target=self._run_loop, daemon=True, name="ContinuousObserver")
        self._thread.start()
        print("[CONTINUOUS OBSERVER] Started background observation thread.")

    def stop(self):
        """Stop observation thread."""
        self.running = False
        if self._thread:
            self._thread.join(timeout=1.0)
            self._thread = None
        print("[CONTINUOUS OBSERVER] Stopped.")

    def ingest_domain_event(
        self,
        domain: str,
        actor: str,
        action: str,
        params: Dict[str, Any],
        timestamp: Optional[float] = None,
        world: str = "world"
    ):
        """Direct ingestion method for any domain adapter (Minecraft, Desktop, Web)."""
        ev = {
            "time": timestamp or (time.time() * 1000),
            "player": actor,
            "domain": domain,
            "action": action,
            "params": params,
            "world": world
        }
        episode_segmenter.ingest_event(ev, domain=domain)
        self._stream_to_wfc(domain, actor, action, params)

        if action in ("break", "place"):
            block_name = str(params.get("block", "")).lower()
            if any(k in block_name for k in ("ore", "log", "chest", "door", "furnace", "portal", "diamond", "iron", "gold")):
                from drives import drive_manager
                drive_manager.update_with_emotion({"novelty": 0.80, "importance": 0.70, "goal_relevance": 0.65})

    def _stream_to_wfc(self, domain: str, actor: str, action: str, params: Dict[str, Any]):
        """Inject lightweight observation into WFC without running heavy reason cycle."""
        if not self._mind or not hasattr(self._mind, "wfc"):
            return

        detail = ""
        if action == "place":
            detail = f"placed {params.get('block')} at {params.get('position')}"
        elif action == "break":
            detail = f"mined {params.get('block')} at {params.get('position')}"
        elif action == "equip":
            detail = f"equipped {params.get('item')}"
        elif action == "craft":
            detail = f"crafted {params.get('item')} (x{params.get('count', 1)})"
        else:
            detail = f"performed {action} ({params})"

        entry = {
            "cycle": getattr(self._mind, "cycle_count", 0),
            "t": time.time(),
            "raw": f"[{domain.upper()}] {actor} {detail}",
            "intent": "ambient_observation",
            "weight": 0.1,
            "approved": True,
            "quarantined": False,
            "rationale": "Continuous server-side domain observation",
            "outcome": "observed",
            "action_result": {"status": "observed", "domain": domain, "action": action}
        }
        self._mind.wfc.append(entry)

    def _poll_minecraft_events(self):
        """Fetch new events from JarvisDemonstrations plugin HTTP server."""
        url = f"{self.minecraft_endpoint}?since={self.cursor}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ATMAN-Core-Observer"})
            with urllib.request.urlopen(req, timeout=1.0) as resp:
                if resp.status != 200:
                    return
                data = json.loads(resp.read().decode("utf-8"))
                events = data.get("events", [])
                new_seq = data.get("sequence", self.cursor)

                # Reset cursor if server restarted
                oldest = data.get("oldest", 0)
                if oldest > self.cursor + 1 and self.cursor != 0:
                    print(f"[CONTINUOUS OBSERVER] Sequence gap detected (oldest={oldest}, cursor={self.cursor}). Resetting to current.")
                    self.cursor = new_seq
                    return

                for ev in events:
                    episode_segmenter.ingest_event(ev, domain="minecraft")
                    actor = ev.get("player", "Operator")
                    action = ev.get("action", "")
                    params = ev.get("params", {})
                    self._stream_to_wfc("minecraft", actor, action, params)

                    # Novelty check for Drive Layer (Curiosity)
                    if action in ("break", "place"):
                        block_name = str(params.get("block", "")).lower()
                        if any(k in block_name for k in ("ore", "log", "chest", "door", "furnace", "portal", "diamond", "iron", "gold")):
                            from drives import drive_manager
                            drive_manager.update_with_emotion({"novelty": 0.80, "importance": 0.70, "goal_relevance": 0.65})

                from drives import drive_manager
                drive_manager.tick_idle(elapsed_seconds=self.poll_interval, is_player_away=True)
                self.cursor = new_seq
        except (urllib.error.URLError, TimeoutError, ConnectionRefusedError, OSError):
            # Server not currently running or plugin not yet bound; keep polling silently
            pass
        except Exception as e:
            # Non-fatal parse error
            pass

    def _run_loop(self):
        """Continuous polling loop."""
        # Initialize cursor to current server sequence
        try:
            req = urllib.request.Request(f"{self.minecraft_endpoint}?since=latest")
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                self.cursor = data.get("sequence", 0)
                print(f"[CONTINUOUS OBSERVER] Synchronized with Minecraft server at sequence {self.cursor}.")
        except Exception:
            self.cursor = 0

        while self.running:
            self._poll_minecraft_events()
            time.sleep(self.poll_interval)


# Global singleton observer
continuous_observer = ContinuousObserver()
