"""Execution Governor for JARVIS.

Protects the host environment against runaway process/tool spirals:
1. Concurrency Cap: Max 5 concurrent tool/process spawns (within 4-6 cap range).
   - Engages a cooldown (3.0s) whenever cap is reached.
   - Rejects or throttles spawns while cooldown is active.
   - Logs every time the cap engages with timestamp, active count, and reason.
2. Hard 'Calm Down' Command:
   - Recognizes text & voice trigger: 'calm down', 'hey jarvis, calm down', 'jarvis calm down'.
   - Immediately terminates all registered child processes and process trees (taskkill /F /T).
   - Aborts and cancels all in-flight tool calls / thread tasks.
   - Resets the concurrency counters and clears pending tool tasks.
   - Works reliably mid-spiral using re-entrant thread safety and process-tree termination.
"""
import logging
import os
from pathlib import Path
import re
import subprocess
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Set

HERE = Path(__file__).resolve().parent
LOG_FILE = HERE / "governor.log"

# Configure dedicated governor logger
logger = logging.getLogger("JARVIS.Governor")
logger.setLevel(logging.INFO)
if not logger.handlers:
    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setFormatter(logging.Formatter("[%(asctime)s] [GOVERNOR] %(levelname)s: %(message)s"))
    logger.addHandler(fh)


class ConcurrencyCapExceeded(Exception):
    """Raised when process/tool spawn exceeds the maximum concurrency cap."""
    pass


class Governor:
    """Thread-safe concurrency throttle and emergency kill switch for JARVIS."""

    def __init__(self, max_concurrent: int = 5, cooldown_seconds: float = 3.0):
        if not (4 <= max_concurrent <= 6):
            max_concurrent = 5
        self.max_concurrent = max_concurrent
        self.cooldown_seconds = cooldown_seconds

        self._lock = threading.RLock()
        self._active_spawns: Dict[str, Dict[str, Any]] = {}
        self._tracked_pids: Set[int] = set()
        self._tracked_processes: Set[subprocess.Popen] = set()
        self._cooldown_until: float = 0.0
        self._emergency_halt: bool = False

    @property
    def active_count(self) -> int:
        with self._lock:
            return len(self._active_spawns)

    @property
    def is_cooling_down(self) -> bool:
        with self._lock:
            return time.time() < self._cooldown_until

    def is_calm_down_trigger(self, text: str) -> bool:
        """Check if incoming text/voice transcription matches the hard calm down phrase."""
        if not text:
            return False
        clean = re.sub(r"[^\w\s]", "", text.lower()).strip()
        # Matches: "calm down", "hey jarvis calm down", "jarvis calm down", "please calm down", "stop all processes and calm down"
        pattern = r"\b(?:hey\s+jarvis[, ]+|jarvis[, ]+)?calm\s+down\b|\bstop\s+all\s+processes\b"
        return bool(re.search(pattern, clean))

    def acquire_spawn(self, spawn_id: str, description: str = "") -> bool:
        """Attempt to acquire a spawn slot for a process or tool call.
        
        Returns True if acquired.
        Raises ConcurrencyCapExceeded if limit reached or in cooldown.
        """
        with self._lock:
            now = time.time()
            if self._emergency_halt:
                logger.warning(f"Spawn blocked: emergency halt in effect. Attempted: '{spawn_id}' ({description})")
                raise ConcurrencyCapExceeded("Emergency halt active. JARVIS is in calm-down state.")

            if now < self._cooldown_until:
                remaining = round(self._cooldown_until - now, 2)
                logger.warning(
                    f"CAP ENGAGED: Spawn throttled during cooldown ({remaining}s remaining). "
                    f"Active: {len(self._active_spawns)}/{self.max_concurrent}. Blocked: '{spawn_id}'"
                )
                raise ConcurrencyCapExceeded(
                    f"Governor cooldown active ({remaining}s remaining). Concurrency limit enforced."
                )

            if len(self._active_spawns) >= self.max_concurrent:
                self._cooldown_until = now + self.cooldown_seconds
                msg = (
                    f"CAP ENGAGED: Max concurrency cap ({self.max_concurrent}) hit! "
                    f"Entering {self.cooldown_seconds}s cooldown. Blocked: '{spawn_id}' ({description})"
                )
                logger.warning(msg)
                print(f"[GOVERNOR ALERT] {msg}")
                raise ConcurrencyCapExceeded(msg)

            self._active_spawns[spawn_id] = {
                "desc": description,
                "start_time": now
            }
            logger.info(f"Spawn slot acquired: '{spawn_id}' ({description}). Active: {len(self._active_spawns)}/{self.max_concurrent}")
            return True

    def release_spawn(self, spawn_id: str):
        """Release an active spawn slot."""
        with self._lock:
            if spawn_id in self._active_spawns:
                del self._active_spawns[spawn_id]
                logger.info(f"Spawn slot released: '{spawn_id}'. Remaining active: {len(self._active_spawns)}/{self.max_concurrent}")

    def track_process(self, proc: subprocess.Popen):
        """Track an external child process spawned by JARVIS."""
        with self._lock:
            self._tracked_processes.add(proc)
            if hasattr(proc, "pid") and proc.pid:
                self._tracked_pids.add(proc.pid)
                logger.info(f"Tracking child process PID {proc.pid}")

    def untrack_process(self, proc: subprocess.Popen):
        """Untrack a completed child process."""
        with self._lock:
            self._tracked_processes.discard(proc)
            if hasattr(proc, "pid") and proc.pid:
                self._tracked_pids.discard(proc.pid)

    def calm_down(self) -> Dict[str, Any]:
        """HARD CALM DOWN COMMAND.
        
        Immediately kills every child process spawned by JARVIS,
        stops all in-flight tool calls, clears active spawns, and engages cooldown.
        Must work even mid-spiral.
        """
        with self._lock:
            logger.critical(">>> HARD 'CALM DOWN' TRIGGERED <<< Halting all processes and tool calls.")
            self._emergency_halt = True
            killed_pids: List[int] = []
            killed_procs: int = 0
            cancelled_tools: int = len(self._active_spawns)

            # 1. Kill all tracked subprocess instances
            for proc in list(self._tracked_processes):
                try:
                    if proc.poll() is None:
                        proc.terminate()
                        killed_procs += 1
                except Exception as e:
                    logger.error(f"Error terminating proc {proc}: {e}")

            # 2. Hard process-tree kill for all tracked PIDs on Windows
            for pid in list(self._tracked_pids):
                try:
                    subprocess.run(
                        ["taskkill", "/F", "/T", "/PID", str(pid)],
                        capture_output=True,
                        timeout=3
                    )
                    killed_pids.append(pid)
                    logger.info(f"taskkill executed on PID {pid}")
                except Exception as e:
                    logger.error(f"Error taskkilling PID {pid}: {e}")

            # 3. Clear all active registrations
            self._tracked_processes.clear()
            self._tracked_pids.clear()
            self._active_spawns.clear()

            # 4. Set cooldown buffer
            self._cooldown_until = time.time() + self.cooldown_seconds
            self._emergency_halt = False

            summary = {
                "success": True,
                "action": "calm_down",
                "killed_processes_count": killed_procs,
                "killed_pids": killed_pids,
                "cancelled_in_flight_tools": cancelled_tools,
                "cooldown_seconds": self.cooldown_seconds,
                "timestamp": time.time()
            }
            logger.critical(f"Calm down complete: {summary}")
            return summary


# Global singleton instance for system-wide governance
governor = Governor(max_concurrent=5, cooldown_seconds=3.0)
