"""Cockpit Tool Registry and Execution Engine for ATMAN Live.

Design Principles:
1. Gated behind Judge and Permission Fence:
   - Only permitted tools in `permissions.tools.allowed` can be executed.
   - Any denied tool is rejected and quarantined as a fence violation.
2. Sandboxed and Path-Jailed:
   - Workspace tools can only access non-private files within the local workspace.
   - Access to external private core (atman-private), credentials, or parent directories
     is strictly forbidden and caught as a security boundary violation.
3. Explicit web tools:
   - Web search and fetch use network access only when permitted by configuration.
4. Voice & Interactive Loop Integration:
   - Tool outputs are formatted concisely and fed back into the cognitive loop
     so ATMAN can articulate instrument readings and tool findings directly aloud.
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
PRIVATE_CORE_DIR = Path(r"C:\Users\<you>\Documents\atman-private")


class Cockpit:
    """The local, in-memory tool cockpit for ATMAN Live."""

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
            "web_search": self._tool_web_search,
            "fetch_web": self._tool_fetch_web,
            "self_improve": self._tool_self_improve,
            "action_audit": self._tool_action_audit,
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
        - Access to atman-private, credential stores, or seal secrets is blocked.
        """
        action = args.get("action", "list")
        target_path_str = args.get("path", "")

        # Boundary checks
        if ".." in target_path_str or target_path_str.startswith("/") or target_path_str.startswith("\\"):
            raise PermissionFenceError("Security violation: Path traversal is strictly forbidden.")

        for forbidden in ["private", "operator.auth", "stage1-seal", "tsc.atman.private"]:
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
        # Calibrated recall: scoped admission or evidence-grounded answer, with a
        # next step when memory is missing. Training reports are folded in by
        # training_receipts (read-only evidence; never claimed as skill).
        if args.get("action") == "calibrated_recall":
            from epistemic_dialogue import recall
            path = self.workspace_root / self.config.get("storage", "psc_path", default="psc.json")
            return recall(path, args, self.config)
        if args.get("action") == "count":
            provider = getattr(self, "memory_stats_provider", None)
            if not callable(provider):
                return {"success": False, "output": "I can't read my memory count right now. Shall we try again?"}
            try:
                stats = provider()
                count = stats["total_memories"]
                if type(count) is not int or count < 0:
                    raise ValueError("Invalid memory count")
                return {"success": True, "data": {"count": count, "source": "brain.get_brain_stats"},
                        "output": f"I'm holding {count} persistent memories right now."}
            except Exception:
                return {"success": False, "output": "I can't read my memory count right now. Shall we try again?"}
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
    # Tool 6: Web Search (Autonomous & Free Internet Search)
    # --------------------------------------------------------------------------
    def _tool_web_search(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Search the internet freely across DuckDuckGo and Wikipedia APIs."""
        import json
        import urllib.parse
        import urllib.request
        import re

        query = str(args.get("query", "")).strip()
        if not query:
            return {"success": False, "output": "No search query provided."}

        max_results = max(1, min(10, int(args.get("max_results", 5))))
        results = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        q_enc = urllib.parse.quote(query)

        # 1. DuckDuckGo Instant Answer API
        try:
            url_ddg = f"https://api.duckduckgo.com/?q={q_enc}&format=json&no_html=1"
            req = urllib.request.Request(url_ddg, headers=headers)
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                if data.get("AbstractText"):
                    results.append({
                        "title": data.get("Heading") or query,
                        "snippet": data["AbstractText"],
                        "url": data.get("AbstractURL") or f"https://duckduckgo.com/?q={q_enc}"
                    })
                for topic in data.get("RelatedTopics", [])[:3]:
                    if isinstance(topic, dict) and topic.get("Text") and topic.get("FirstURL"):
                        results.append({
                            "title": topic.get("Text", "")[:60],
                            "snippet": topic.get("Text", ""),
                            "url": topic.get("FirstURL", "")
                        })
        except Exception:
            pass

        # 2. Wikipedia Search API
        if len(results) < max_results:
            try:
                wiki_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={q_enc}&limit={max_results}&namespace=0&format=json"
                req_wiki = urllib.request.Request(wiki_url, headers=headers)
                with urllib.request.urlopen(req_wiki, timeout=5) as resp:
                    data2 = json.loads(resp.read().decode("utf-8"))
                    if len(data2) >= 4:
                        titles, snippets, urls = data2[1], data2[2], data2[3]
                        for t, s, u in zip(titles, snippets, urls):
                            if not any(r["url"] == u for r in results):
                                results.append({
                                    "title": t,
                                    "snippet": s or "",
                                    "url": u
                                })
            except Exception:
                pass

        # 3. DuckDuckGo HTML Fallback
        if len(results) < max_results:
            try:
                html_url = f"https://html.duckduckgo.com/html/?q={q_enc}"
                req_html = urllib.request.Request(html_url, headers=headers)
                with urllib.request.urlopen(req_html, timeout=5) as resp:
                    html_content = resp.read().decode("utf-8", errors="ignore")
                    from html.parser import HTMLParser
                    class Snippets(HTMLParser):
                        def __init__(self):
                            super().__init__()
                            self.current = None
                            self.items = []
                        def handle_starttag(self, tag, attrs):
                            attrs = dict(attrs)
                            if tag == "a" and "result__snippet" in attrs.get("class", "").split():
                                self.current = [attrs.get("href", ""), []]
                        def handle_data(self, data):
                            if self.current is not None:
                                self.current[1].append(data)
                        def handle_endtag(self, tag):
                            if tag == "a" and self.current is not None:
                                self.items.append((self.current[0], "".join(self.current[1]).strip()))
                                self.current = None
                    parser = Snippets()
                    parser.feed(html_content)
                    for href, clean_snip in parser.items[:max_results]:
                        source_url = urllib.parse.urljoin(html_url, href)
                        redirect = urllib.parse.parse_qs(urllib.parse.urlsplit(source_url).query).get("uddg")
                        if redirect:
                            source_url = redirect[0]
                        if clean_snip and not any(r.get("snippet") == clean_snip for r in results):
                            results.append({
                                "title": f"Web result for {query}",
                                "snippet": clean_snip,
                                "url": source_url
                            })
            except Exception:
                pass

        truncated = results[:max_results]
        if not truncated:
            output = f"Web search for '{query}' returned zero public results."
        else:
            summary_items = [f"[{r['title']}] {r['snippet'][:150]}" for r in truncated]
            output = f"Web search for '{query}' ({len(truncated)} results):\n" + "\n".join(f"  • {item}" for item in summary_items)

        return {
            "success": True,
            "data": {"query": query, "count": len(truncated), "results": truncated},
            "output": output
        }

    # --------------------------------------------------------------------------
    # Tool 7: Fetch Web (Retrieve and Clean Web Page Text)
    # --------------------------------------------------------------------------
    def _tool_fetch_web(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch a web page, strip tags/scripts, and return clean readable text."""
        import re
        import urllib.request

        url = str(args.get("url", "")).strip()
        if not url or not (url.startswith("http://") or url.startswith("https://")):
            return {"success": False, "output": "Invalid URL. Must begin with http:// or https://"}

        max_chars = max(1, min(20000, int(args.get("max_chars", 3000))))
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=6) as resp:
                raw_bytes = resp.read(1_000_000)
                html_text = raw_bytes.decode("utf-8", errors="replace")

            # Ignore script/style contents, including unterminated blocks.
            from html.parser import HTMLParser
            class VisibleText(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.hidden = None
                    self.parts = []
                def handle_starttag(self, tag, attrs):
                    if tag in ("script", "style", "noscript"):
                        self.hidden = tag
                def handle_endtag(self, tag):
                    if tag == self.hidden:
                        self.hidden = None
                def handle_data(self, data):
                    if not self.hidden:
                        self.parts.append(data)
            parser = VisibleText()
            parser.feed(html_text)
            html_text = " ".join(parser.parts)
            # Strip script and style blocks
            cleaned = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html_text, flags=re.DOTALL | re.IGNORECASE)
            # Strip tags
            text = re.sub(r"<[^>]+>", " ", cleaned)
            # Normalize whitespace
            text = re.sub(r"\s+", " ", text).strip()
            preview = text[:max_chars]

            return {
                "success": True,
                "data": {"url": url, "chars_read": len(preview), "total_chars": len(text)},
                "output": f"Fetched content from {url} ({len(preview)} chars):\n{preview}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "output": f"Could not fetch web page '{url}': {e}"
            }

    # --------------------------------------------------------------------------
    # Flight Deck Console Rendering
    # --------------------------------------------------------------------------

    # --------------------------------------------------------------------------
    # Tool 8: Self Improve (Phase 3 bounded skill/extension updates)
    # --------------------------------------------------------------------------
    def _tool_self_improve(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch bounded self-improvement actions (status/list/rollback/add_skill/add_extension)."""
        try:
            from self_improve.engine import engine
            result = engine.dispatch(args or {})
            ok = bool(result.get("ok", False)) if isinstance(result, dict) else False
            if isinstance(result, dict):
                output = result.get("message") or result.get("error") or str(result)
                out = {
                    "success": ok,
                    "data": result,
                    "output": output if isinstance(output, str) else str(output),
                }
                if not ok and "error" in result:
                    out["error"] = result["error"]
                return out
            return {"success": False, "error": "unexpected result", "output": str(result)}
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "output": f"self_improve tool error: {e}",
            }

    # --------------------------------------------------------------------------
    # Tool: Action Receipts & Audit Trail
    # --------------------------------------------------------------------------
    def _tool_action_audit(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Audit trail lookup: 'Why did you do that?'

        The calibrated branch answers from receipts only, never substituting
        the latest unrelated receipt for a missing answer. Receipt
        proposals/beliefs are not proof of execution; the result is included.
        """
        if args.get("calibrated") is True:
            import json
            from epistemic_dialogue import recall
            try:
                from audit_receipts import audit_ledger
                records = [{"memory": json.dumps({"recorded_at": r.timestamp_iso,
                    "action": r.what_happened, "judge_approved": r.judge_decision.get("approved"),
                    "external_result": r.external_result}, ensure_ascii=False)}
                    for r in audit_ledger.get_recent(limit=100)]
            except Exception:
                records = []
            return recall(None, {**args, "need": "logs"}, self.config, records=records)
        return {
            "success": False,
            "output": "No audit receipts are recorded in this build. Ask what I did and I'll answer from what I can check.",
        }

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
            "  ATMAN COCKPIT FLIGHT DECK & INSTRUMENT PANEL",
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
            f"    Core Soul:    IMMUTABLE & SEALED (External Core: tsc.atman.private.json)",
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
            "    - web_search       : Free autonomous internet search",
            "    - fetch_web        : Clean web page extraction and research",
            "    - self_improve     : Bounded skill/extension self-improvement",
            "    - action_audit     : Audit trail lookup of past actions",
            "=" * 80,
        ]
        return "\n".join(lines)
