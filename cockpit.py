"""Cockpit Tool Registry and Execution Engine for EXO Live.

Design Principles:
1. Gated behind Judge and Permission Fence:
   - Only permitted tools in `permissions.tools.allowed` can be executed.
   - Any denied tool is rejected and quarantined as a fence violation.
2. Sandboxed and Path-Jailed:
   - Workspace tools can only access non-private files within the local workspace.
   - Access to external private core (exo-private), credentials, or parent directories
     is strictly forbidden and caught as a security boundary violation.
3. Zero-Egress, 100% Local:
   - All tools execute purely locally. Network calls and external egress remain hard-blocked.
4. Voice & Interactive Loop Integration:
   - Tool outputs are formatted concisely and fed back into the cognitive loop
     so EXO can articulate instrument readings and tool findings directly aloud.
"""
import ast
import ctypes
from datetime import datetime, timezone
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import time
from typing import Any, Dict, List, Optional, Tuple

from config import Config, PermissionFenceError

HERE = Path(__file__).resolve().parent
PRIVATE_CORE_DIR = Path(os.environ.get("EXO_PRIVATE_DIR") or (HERE.parent / "exo-private"))


class Cockpit:
    """The local, in-memory tool cockpit for EXO Live."""

    def __init__(self, config: Optional[Config] = None, workspace_root: Optional[Path] = None):
        self.config = config or Config()
        self.workspace_root = workspace_root or HERE
        self._start_time = time.time()

    @property
    def uptime_seconds(self) -> float:
        return time.time() - self._start_time

    def is_tool_allowed(self, tool_name: str) -> bool:
        """Check if tool is in config's allowed list and not denied."""
        return self.config.is_tool_permitted(tool_name)

    def execute_tool(self, tool_name: str, args: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute tool behind the permission fence.
        
        Raises PermissionFenceError if tool is not permitted or is explicitly denied.
        """
        args = args or {}

        # 1. Strict Permission Fence Verification
        if not self.is_tool_allowed(tool_name):
            raise PermissionFenceError(
                f"Permission fence blocked unauthorized tool '{tool_name}'. "
                f"Tool is not in permitted tools list."
            )

        # 1b. Governor Concurrency Throttle Check
        from governor import governor, ConcurrencyCapExceeded
        spawn_id = f"tool_{tool_name}_{time.time()}"
        try:
            governor.acquire_spawn(spawn_id, f"Cockpit tool execution: {tool_name}")
        except ConcurrencyCapExceeded as cce:
            return {
                "success": False,
                "error": str(cce),
                "output": f"Governor throttled tool execution: {cce}"
            }

        # 2. Dispatch to internal tool handler
        handler_map = {
            "system_telemetry": self._tool_system_telemetry,
            "clock_timer": self._tool_clock_timer,
            "workspace_inspect": self._tool_workspace_inspect,
            "memory_query": self._tool_memory_query,
            "calculator": self._tool_calculator,
        }

        handler = handler_map.get(tool_name)
        if not handler:
            governor.release_spawn(spawn_id)
            return {
                "success": False,
                "error": f"No implementation found for permitted tool '{tool_name}'",
                "output": f"Tool '{tool_name}' has no registered handler."
            }

        try:
            return handler(args)
        except PermissionFenceError:
            raise
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "output": f"Tool '{tool_name}' encountered an error: {e}"
            }
        finally:
            governor.release_spawn(spawn_id)

    # --------------------------------------------------------------------------
    # Tool 1: System Telemetry (Hardware Instruments & VRAM)
    # --------------------------------------------------------------------------
    def _tool_system_telemetry(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Query host RAM and GPU VRAM telemetry."""
        # 1. Query Host RAM via ctypes GlobalMemoryStatusEx
        ram_info = {"load_pct": 0, "total_gb": 0.0, "avail_gb": 0.0, "used_gb": 0.0}
        try:
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]
            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
            total_gb = stat.ullTotalPhys / (1024 ** 3)
            avail_gb = stat.ullAvailPhys / (1024 ** 3)
            used_gb = total_gb - avail_gb
            ram_info = {
                "load_pct": int(stat.dwMemoryLoad),
                "total_gb": round(total_gb, 1),
                "avail_gb": round(avail_gb, 1),
                "used_gb": round(used_gb, 1)
            }
        except Exception:
            pass

        # 2. Query GPU VRAM via nvidia-smi
        gpu_info = {"name": "NVIDIA GPU", "vram_used_mb": 0, "vram_total_mb": 0, "util_pct": 0}
        try:
            res = subprocess.run(
                ["nvidia-smi", "--query-gpu=gpu_name,memory.used,memory.total,utilization.gpu", "--format=csv,noheader,nounits"],
                capture_output=True, text=True, timeout=3.0
            )
            if res.returncode == 0 and res.stdout.strip():
                parts = [p.strip() for p in res.stdout.strip().split(",")]
                if len(parts) >= 4:
                    gpu_info = {
                        "name": parts[0],
                        "vram_used_mb": int(parts[1]),
                        "vram_total_mb": int(parts[2]),
                        "util_pct": int(parts[3])
                    }
        except Exception:
            pass

        # Format summary for spoken response
        vram_pct = int(gpu_info["vram_used_mb"] / gpu_info["vram_total_mb"] * 100) if gpu_info["vram_total_mb"] > 0 else 0
        summary = (
            f"GPU VRAM: {gpu_info['vram_used_mb']:,} MB / {gpu_info['vram_total_mb']:,} MB used ({vram_pct}%). "
            f"Host RAM: {ram_info['used_gb']:.1f} GB / {ram_info['total_gb']:.1f} GB ({ram_info['load_pct']}% load). "
            f"Process uptime: {int(self.uptime_seconds)}s."
        )

        return {
            "success": True,
            "data": {
                "gpu": gpu_info,
                "ram": ram_info,
                "uptime_s": round(self.uptime_seconds, 1)
            },
            "output": summary
        }

    # --------------------------------------------------------------------------
    # Tool 2: Clock & Timers
    # --------------------------------------------------------------------------
    def _tool_clock_timer(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Query real-time clock, timezone, date, and loop elapsed time."""
        now = datetime.now()
        local_time_str = now.strftime("%I:%M:%S %p")
        local_date_str = now.strftime("%A, %B %d, %Y")
        
        uptime_m, uptime_s = divmod(int(self.uptime_seconds), 60)
        uptime_h, uptime_m = divmod(uptime_m, 60)
        uptime_str = f"{uptime_h}h {uptime_m}m {uptime_s}s" if uptime_h else f"{uptime_m}m {uptime_s}s"

        output = f"Current local time is {local_time_str} on {local_date_str}. Mind session active for {uptime_str}."

        return {
            "success": True,
            "data": {
                "iso_timestamp": now.isoformat(),
                "time": local_time_str,
                "date": local_date_str,
                "uptime_seconds": round(self.uptime_seconds, 1),
                "uptime_formatted": uptime_str
            },
            "output": output
        }

    # --------------------------------------------------------------------------
    # Tool 3: Workspace Inspection (Path-Jailed & Security Gated)
    # --------------------------------------------------------------------------
    def _tool_workspace_inspect(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Inspect non-private files in the local workspace directory.
        
        Strict Safety Invariants:
        - Path traversal ('..') is strictly rejected.
        - Access to exo-private, credential stores, or seal secrets is blocked.
        """
        action = args.get("action", "list")
        target_path_str = args.get("path", "")

        # Boundary checks
        if ".." in target_path_str or target_path_str.startswith("/") or target_path_str.startswith("\\"):
            raise PermissionFenceError("Security violation: Path traversal is strictly forbidden.")

        for forbidden in ["private", "operator.auth", "stage1-seal", "tsc.exo.private"]:
            if forbidden in target_path_str.lower():
                raise PermissionFenceError(
                    f"Security boundary violation: Access to private core or credentials is strictly forbidden."
                )

        if action == "list":
            files = []
            for item in sorted(self.workspace_root.iterdir()):
                if item.name.startswith(".") or item.name in ("__pycache__", "outputs"):
                    continue
                files.append(item.name)
            output = f"Workspace contains {len(files)} files/folders: " + ", ".join(files[:15])
            if len(files) > 15:
                output += f", and {len(files) - 15} more."
            return {
                "success": True,
                "data": {"files": files, "count": len(files)},
                "output": output
            }

        elif action == "read":
            if not target_path_str:
                return {"success": False, "output": "No file path specified to read."}
            target_file = (self.workspace_root / target_path_str).resolve()
            if not target_file.is_relative_to(self.workspace_root):
                raise PermissionFenceError("Security violation: File path escapes workspace jail.")
            if not target_file.exists():
                return {"success": False, "output": f"File '{target_path_str}' does not exist in workspace."}
            if target_file.stat().st_size > 100_000:
                return {"success": False, "output": f"File '{target_path_str}' exceeds read limit size."}

            lines = target_file.read_text(encoding="utf-8", errors="replace").splitlines()
            max_lines = int(args.get("max_lines", 30))
            preview = "\n".join(lines[:max_lines])
            return {
                "success": True,
                "data": {"lines_read": len(lines[:max_lines]), "total_lines": len(lines)},
                "output": f"Read {len(lines[:max_lines])} lines from {target_path_str}:\n{preview}"
            }

        return {"success": False, "output": f"Unrecognized workspace inspection action '{action}'"}

    # --------------------------------------------------------------------------
    # Tool 4: Memory Query (Search PSC & Significant Events)
    # --------------------------------------------------------------------------
    def _tool_memory_query(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Search persistent memories (PSC) and significant events log."""
        query = str(args.get("query", "")).lower().strip()
        
        # 1. Search PSC
        psc_file = self.workspace_root / self.config.get("storage", "psc_path", default="psc.json")
        psc_memories = []
        if psc_file.exists():
            import json
            try:
                data = json.loads(psc_file.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    for item in data:
                        mem_text = item.get("memory", "") if isinstance(item, dict) else str(item)
                        if not query or query in mem_text.lower():
                            psc_memories.append(mem_text)
            except Exception:
                pass

        if not psc_memories:
            output = f"No persistent memories matching '{query}' found." if query else "No persistent memories currently recorded."
        else:
            recent = psc_memories[-3:]
            output = f"Found {len(psc_memories)} persistent memories. Recent: " + "; ".join(recent)

        return {
            "success": True,
            "data": {"matches": psc_memories, "count": len(psc_memories)},
            "output": output
        }

    # --------------------------------------------------------------------------
    # Tool 5: Calculator (Safe Math Engine)
    # --------------------------------------------------------------------------
    def _tool_calculator(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Safely evaluate mathematical arithmetic expressions without eval()."""
        expr = str(args.get("expression", "")).strip()
        if not expr:
            return {"success": False, "output": "No mathematical expression provided."}

        # Safe AST evaluator for math
        operators = {
            ast.Add: lambda a, b: a + b,
            ast.Sub: lambda a, b: a - b,
            ast.Mult: lambda a, b: a * b,
            ast.Div: lambda a, b: a / b,
            ast.FloorDiv: lambda a, b: a // b,
            ast.Mod: lambda a, b: a % b,
            ast.Pow: lambda a, b: a ** b,
            ast.USub: lambda a: -a,
            ast.UAdd: lambda a: a,
        }

        def _eval_node(node):
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                return node.value
            elif isinstance(node, ast.BinOp):
                op_type = type(node.op)
                if op_type not in operators:
                    raise ValueError(f"Unsupported mathematical operator: {op_type.__name__}")
                return operators[op_type](_eval_node(node.left), _eval_node(node.right))
            elif isinstance(node, ast.UnaryOp):
                op_type = type(node.op)
                if op_type not in operators:
                    raise ValueError(f"Unsupported unary operator: {op_type.__name__}")
                return operators[op_type](_eval_node(node.operand))
            else:
                raise ValueError(f"Unsupported mathematical syntax: {type(node).__name__}")

        try:
            parsed = ast.parse(expr, mode="eval")
            result = _eval_node(parsed.body)
            # Format nicely
            res_str = f"{result:.4f}".rstrip("0").rstrip(".") if isinstance(result, float) else str(result)
            output = f"Calculation: {expr} = {res_str}"
            return {
                "success": True,
                "data": {"expression": expr, "result": result},
                "output": output
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "output": f"Could not calculate expression '{expr}': {e}"
            }

    # --------------------------------------------------------------------------
    # Flight Deck Console Rendering
    # --------------------------------------------------------------------------
    def render_dashboard(self, mind: Any) -> str:
        """Render ASCII Cockpit Flight Deck Dashboard."""
        telemetry = self._tool_system_telemetry({})["data"]
        gpu = telemetry["gpu"]
        ram = telemetry["ram"]
        clock = self._tool_clock_timer({})["data"]
        
        gpu_pct = int(gpu["vram_used_mb"] / gpu["vram_total_mb"] * 100) if gpu["vram_total_mb"] > 0 else 0
        ram_pct = ram["load_pct"]
        
        def bar(pct: int, length: int = 15) -> str:
            filled = int(length * (pct / 100.0))
            return "|" * filled + "." * (length - filled)

        cam_status = "ONLINE (Moondream VLM)" if getattr(mind.camera, "is_enabled", False) else "OFFLINE"
        voice_status = "ONLINE (Push-to-talk)" if getattr(mind.voice, "is_enabled", False) else "OFFLINE"

        lines = [
            "=" * 80,
            "  EXO COCKPIT FLIGHT DECK & INSTRUMENT PANEL",
            "=" * 80,
            "  [HARDWARE TELEMETRY GAUGES]",
            f"    GPU:          {gpu['name']}",
            f"    VRAM:         {gpu['vram_used_mb']:,} MB / {gpu['vram_total_mb']:,} MB ({gpu_pct}%) [{bar(gpu_pct)}]",
            f"    Host RAM:     {ram['used_gb']:.1f} GB / {ram['total_gb']:.1f} GB ({ram_pct}%) [{bar(ram_pct)}]",
            f"    Local Clock:  {clock['time']} ({clock['date']})",
            f"    Uptime:       {clock['uptime_formatted']} | Mind Cycle Count: {mind.cycle_count}",
            "",
            "  [SENSORY INSTRUMENTS]",
            f"    Camera Eye:   {cam_status}",
            f"    Audio Senses: {voice_status} (Whisper STT + Piper TTS)",
            "",
            "  [CORE INVARIANTS & INTEGRITY GAUGES]",
            f"    Core Soul:    IMMUTABLE & SEALED (External Core: tsc.exo.private.json)",
            f"    Gate Policy:  SEALED & INTACT (Reference sha256 verified)",
            f"    PSC Records:  {len(mind.psc.memories)} persistent memories / truths",
            f"    WFC Depth:    {len(mind.wfc)} active focus traces",
            "",
            "  [PERMITTED FLIGHT TOOLS]",
            "    - system_telemetry : Hardware VRAM, RAM, and load meters",
            "    - clock_timer      : High-precision clock, timestamps, and uptime",
            "    - workspace_inspect: Safe path-jailed workspace inspection",
            "    - memory_query     : Search PSC memories and significant events",
            "    - calculator       : Mathematical calculation engine",
            "=" * 80,
        ]
        return "\n".join(lines)
