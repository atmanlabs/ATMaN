"""ATMAN Chat Relay Bridge Server.

Exposes a unified HTTP endpoint serving both the local Minecraft bot and remote phone clients:
- Bound strictly to localhost (127.0.0.1) and Tailscale interface (100.x.x.x) -- OFF 0.0.0.0.
- Serves single-page chat UI at GET /
- POST /chat: runs input through authoritative live ATMAN cognitive loop (Governor -> Capture -> Emotion -> WFC -> Reason -> Judge -> Act -> Outcome -> Memory Update).
- Proves core wiring with detailed execution trace logging.
- Token authenticated (0151c1b8c9fda7c07fe8965423e28042415ece45ea07b944).
"""
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import json
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import threading
import time
from typing import Any, Dict, List, Optional

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from config import Config
from loop import MindLoop
from governor import governor
from skills import skill_repo

PORT = 18790
AUTHORITATIVE_TOKEN = "0151c1b8c9fda7c07fe8965423e28042415ece45ea07b944"
CHAT_UI_PATH = HERE / "ui" / "chat.html"


def get_tailscale_ip() -> Optional[str]:
    """Dynamically discover the Tailscale IPv4 address on the host."""
    try:
        # Check tailscale cli
        res = subprocess.run(
            ["C:\\Program Files\\Tailscale\\tailscale.exe", "ip", "-4"],
            capture_output=True,
            text=True,
            timeout=2
        )
        if res.returncode == 0:
            ip = res.stdout.strip().splitlines()[0]
            if ip.startswith("100."):
                return ip
    except Exception:
        pass

    # Scan host interfaces for 100.x.x.x (Carrier Grade NAT used by Tailscale)
    try:
        addrs = socket.getaddrinfo(socket.gethostname(), None)
        for addr in addrs:
            ip = addr[4][0]
            if ip.startswith("100."):
                return ip
    except Exception:
        pass

    return "100.114.96.84"  # Authoritative host Tailscale IP


class RelayHandler(BaseHTTPRequestHandler):
    mind: Optional[MindLoop] = None
    lock = threading.Lock()

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            if CHAT_UI_PATH.exists():
                content = CHAT_UI_PATH.read_bytes()
            else:
                content = b"<h1>ATMAN Core Online</h1><p>UI file not found.</p>"
            self.wfile.write(content)
        elif self.path in ("/health", "/status"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            status_data = {
                "status": "online",
                "mind": "ATMAN",
                "core": "authoritative_atman_live",
                "cycles": self.mind.cycle_count if self.mind else 0,
                "learning": self.mind.brain.get_brain_stats() if self.mind else None,
                "governor_active": governor.active_count,
                "timestamp": time.time()
            }
            self.wfile.write(json.dumps(status_data).encode("utf-8"))
        elif self.path in ("/skills", "/skills/list") or self.path.startswith("/skills?"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            domain = None
            if "?" in self.path:
                q = self.path.split("?", 1)[1]
                for part in q.split("&"):
                    if part.startswith("domain="):
                        domain = part.split("=")[1]
            skills_data = skill_repo.list_skills(domain=domain)
            self.wfile.write(json.dumps({"ok": True, "skills": skills_data}).encode("utf-8"))
        elif self.path in ("/episodes", "/episodes/list"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            from episode_segmenter import episode_segmenter
            active = [ep.to_dict() for ep in episode_segmenter.active_episodes.values()]
            buffered = [ep.to_dict() for ep in episode_segmenter.rolling_buffer]
            self.wfile.write(json.dumps({"ok": True, "active": active, "rolling_buffer": buffered}).encode("utf-8"))
        elif self.path in ("/drives", "/drives/status"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            from drives import drive_manager
            drives_data = [d.to_dict() for d in drive_manager.drives.values()]
            history = [a.to_dict() for a in drive_manager.activity_log[-10:]]
            self.wfile.write(json.dumps({"ok": True, "drives": drives_data, "activity_log": history}).encode("utf-8"))
        elif self.path in ("/initiative/pending", "/initiative/check"):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            # Freeplay idle hook: park gated skill proposals for the operator (no auto-apply)
            try:
                from self_improve.freeplay_proposer import maybe_propose
                maybe_propose({"mode": "initiative", "source": "initiative_pending", "propose_source": "freeplay_initiative"})
            except Exception as _fp_err:
                print(f"[FREEPLAY] propose hook skipped: {_fp_err}")
            try:
                from self_improve.rolling_evolve import maybe_evolve
                maybe_evolve({"mode": "initiative", "source": "initiative_pending"})
            except Exception as _ev_err:
                print(f"[EVOLVE] rolling tick skipped: {_ev_err}")
            from drives import drive_manager
            from loop import evaluate_judge
            init_action = drive_manager.evaluate_initiative()
            if init_action and init_action.get("type") == "minecraft_initiative":
                v = evaluate_judge({
                    "candidate": init_action["description"],
                    "proposed_action": init_action,
                    "intent": "initiative_action"
                }, self.mind.tsc if self.mind else None, self.mind.config if self.mind else None, operator_authenticated=True)
                if v.approved:
                    self.wfile.write(json.dumps({"ok": True, "initiative": init_action, "approved": True}).encode("utf-8"))
                    return
                else:
                    self.wfile.write(json.dumps({"ok": False, "reason": v.rationale}).encode("utf-8"))
                    return
            elif init_action and init_action.get("type") == "proposal":
                self.wfile.write(json.dumps({"ok": True, "proposal": init_action["proposal"]}).encode("utf-8"))
                return
            self.wfile.write(json.dumps({"ok": False, "reason": "No drive crossed threshold"}).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path in ("/initiative/complete", "/initiative/action_completed"):
            if self.headers.get("Authorization") != f"Bearer {AUTHORITATIVE_TOKEN}":
                self.send_response(401)
                self.end_headers()
                return
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len).decode("utf-8", errors="replace")
            try:
                data = json.loads(post_body)
                from drives import drive_manager
                details = data.get("details", {})
                if self.mind:
                    with self.lock:
                        self.mind.brain.record_outcome(data.get("description", "Minecraft initiative"), {
                            "tool": data.get("action_type", "minecraft_initiative"),
                            "status": "error" if details.get("success") is False else "executed",
                            "output_text": details.get("error") or details.get("observation", "Adapter reported completion.")
                        })
                drive_manager.record_action_completed(
                    drive_id=data.get("drive_id", "keep_base_safe_and_tidy"),
                    action_type=data.get("action_type", "initiative_action"),
                    description=data.get("description", "Completed initiative action"),
                    why=data.get("why", "Wanted to maintain base readiness"),
                    details=data.get("details", {}),
                    psc=self.mind.psc if self.mind else None,
                    tsc=self.mind.tsc if self.mind else None
                )
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": True}).encode("utf-8"))
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        if self.path == "/drives/emotion":
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len).decode("utf-8", errors="replace")
            try:
                data = json.loads(post_body)
                from drives import drive_manager
                drive_manager.update_with_emotion(data)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                drives_data = [d.to_dict() for d in drive_manager.drives.values()]
                self.wfile.write(json.dumps({"ok": True, "drives": drives_data}).encode("utf-8"))
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        if self.path == "/events":
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len).decode("utf-8", errors="replace")
            try:
                data = json.loads(post_body)
                from observer import continuous_observer
                continuous_observer.ingest_domain_event(
                    domain=data.get("domain", "minecraft"),
                    actor=data.get("actor") or data.get("player") or "the operator",
                    action=data.get("action", ""),
                    params=data.get("params", {}),
                    timestamp=data.get("timestamp") or data.get("time")
                )
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": True}).encode("utf-8"))
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        if self.path in ("/skills/store", "/skills"):
            client_ip = self.client_address[0]
            content_len = int(self.headers.get("Content-Length", 0))
            post_body = self.rfile.read(content_len).decode("utf-8", errors="replace")
            try:
                data = json.loads(post_body)
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": f"Invalid JSON: {e}"}).encode("utf-8"))
                return

            try:
                if self.headers.get("Authorization") != f"Bearer {AUTHORITATIVE_TOKEN}":
                    raise PermissionError("Skill storage requires operator authentication")
                from loop import evaluate_judge
                v = evaluate_judge({"candidate": f"Store demonstrated skill {data.get('name', '')}",
                    "contradictions": [], "proposed_action": {"type": "minecraft_skill", "domain": data.get("domain"),
                    "action": "learn_store", "skill": data}}, self.mind.tsc, self.mind.config, operator_authenticated=True)
                if not v.approved:
                    raise PermissionError(v.rationale)
                with self.lock:
                    stored = skill_repo.store_skill(data)
                from significant_events import SignificantEventsLog
                SignificantEventsLog().log_event(
                    f"Skill '{stored['name']}' learned and stored in core repository (domain: {stored['domain']}).",
                    source="skill_learning",
                    metadata={"skill": stored['name'], "domain": stored['domain'], "steps": len(stored.get("steps", []))}
                )
                if self.mind and self.mind.psc:
                    self.mind.psc.imprint(
                        f"Learned skill '{stored['name']}' in domain '{stored['domain']}': {stored.get('description', '')}",
                        v,
                        self.mind.tsc,
                        operator_authenticated=True
                    )
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": True, "skill": stored}).encode("utf-8"))
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        if self.path != "/chat":
            self.send_response(404)
            self.end_headers()
            return
            self.send_response(404)
            self.end_headers()
            return

        client_ip = self.client_address[0]
        content_len = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_len).decode("utf-8", errors="replace")

        text = ""
        source = "untrusted_client"
        chat_context = None
        token = ""

        # Extract token from Authorization header or body
        auth_header = self.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:].strip()

        try:
            payload = json.loads(post_body)
            if isinstance(payload, dict):
                text = payload.get("text") or payload.get("message") or payload.get("content") or ""
                source = payload.get("source", "untrusted_client")
                chat_context = payload.get("context")
                if not token:
                    token = payload.get("token", "")
            elif isinstance(payload, str):
                text = payload
        except json.JSONDecodeError:
            text = post_body.strip()

        if not text:
            self.send_response(400)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Empty text payload"}).encode("utf-8"))
            return

        # Security Authentication Check
        # Localhost (127.0.0.1) internal loop and clients providing valid operator token are authenticated
        is_authenticated = (token == AUTHORITATIVE_TOKEN) or (client_ip == "127.0.0.1" and source in ("minecraft", "minecraft_safety", "minecraft_health", "minecraft_world", "minecraft_observation"))

        if not is_authenticated and not (client_ip in ("127.0.0.1", "::1")):
            print(f"[RELAY AUTH DENIED] Unauthorized request from {client_ip} (token: '{token[:8]}...')")
            self.send_response(401)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Unauthorized: Valid operator token required"}).encode("utf-8"))
            return

        # Health probes are transport checks, not cognitive events. Never queue them
        # behind player chat or run them through the locked authoritative MindLoop.
        if source == "minecraft_health":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({
                "ok": True,
                "reply": "",
                "action": "health",
                "core": "authoritative_atman_live",
                "reachable": True
            }).encode("utf-8"))
            return

        # Explicit Request Trace Logging (Step 4 Proof of Core Wiring)
        spawn_id = f"relay_{int(time.time() * 1000)}"
        print(f"\n=======================================================")
        print(f"[RELAY TRACE] Incoming POST /chat from {client_ip} (source: {source})")
        print(f"[RELAY TRACE] Raw payload: \"{text}\"")

        # Check for hard calm down command directly through Governor
        if governor.is_calm_down_trigger(text):
            print("[RELAY GOVERNOR] Hard calm down command recognized!")
            calm_res = governor.calm_down()
            reply = "Understood. Calming down immediately. All processes halted."
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"ok": True, "reply": reply, "calm_down": True}).encode("utf-8"))
            return

        # Governor Concurrency Guard
        try:
            governor.acquire_spawn(spawn_id, f"Chat from {source}")
            print(f"[GOVERNOR TRACE] Concurrency slot acquired: {spawn_id} (Active: {governor.active_count}/{governor.max_concurrent})")
        except Exception as e:
            print(f"[GOVERNOR REJECT] {e}")
            self.send_response(429)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
            return

        # Process through Authoritative live ATMAN MindLoop
        try:
            with self.lock:
                if self.mind is None:
                    self.mind = MindLoop(operator_authenticated=is_authenticated)

                print(f"[ATMAN LOOP TRACE] Entering authoritative MindLoop.run_cycle...")
                cycle_res = self.mind.run_cycle(
                    {"raw": text, "source": source, "t": time.time(), "chat_context": chat_context if is_authenticated and source == "minecraft" else None},
                    operator_authenticated=is_authenticated
                )

            cycle_id = cycle_res.get("cycle")
            verdict = cycle_res.get("verdict")
            action_result = cycle_res.get("action_result", {})
            thought = cycle_res.get("thought", {})
            outcome = cycle_res.get("outcome", {})

            # Step 4: Show full trace through ATMAN components in logs
            print(f"[ATMAN CAPTURE TRACE] Cycle {cycle_id} captured event from '{source}'")
            print(f"[ATMAN REASON TRACE] Intent: '{thought.get('intent')}' | Proposed: '{thought.get('proposed_action', {}).get('type')}'")
            print(f"[ATMAN JUDGE TRACE] Verdict: {'APPROVED' if (verdict and verdict.approved) else 'REJECTED'} | Rationale: {verdict.rationale if verdict else 'None'}")
            print(f"[ATMAN ACTION TRACE] Action status: {action_result.get('status')} | Action: {action_result.get('action')}")
            print(f"[ATMAN MEMORY TRACE] Outcome: {outcome.get('outcome')} | WFC working memory updated")

            # Extract reply safely
            if verdict and not verdict.approved:
                reply = f"Request rejected by Judge: {verdict.rationale}"
            elif action_result.get("status") == "executed" and action_result.get("content"):
                reply = action_result["content"]
            elif thought.get("proposed_action", {}).get("content"):
                reply = thought["proposed_action"]["content"]
            elif action_result.get("details"):
                reply = str(action_result["details"])
            else:
                reply = "Acknowledged."

            if source == "minecraft" and (not isinstance(reply, str) or "Observation/reflection recorded in memory trace" in reply):
                reply = "I'm right here with you, the operator."

            if isinstance(reply, str):

                try:
                    from reason import naturalize_reply
                    reply = naturalize_reply(reply)
                except Exception:
                    reply = re.sub(r"\s+", " ", reply).strip()
                reply = re.sub(
                    r"\s*(?:what would you like (?:me )?to (?:do|build|explore|try|work on)|how can i (?:help|assist)|what (?:should|do) you want (?:me )?to do)[^.?!\n]*[.?!\n]?",
                    "",
                    reply,
                    flags=re.I
                ).strip()

            action_type = action_result.get("action") or thought.get("proposed_action", {}).get("action") or thought.get("proposed_action", {}).get("type")

            print(f"[RELAY OUTGOING] Reply: \"{reply}\" | Action: {action_type}")
            print(f"=======================================================\n")

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            resp_data = {
                "ok": True,
                "reply": reply,
                "action": action_type,
                "intent": thought.get("intent"),
                "skill": action_result.get("skill") or thought.get("proposed_action", {}).get("skill"),
                "domain": action_result.get("domain") or thought.get("proposed_action", {}).get("domain", "minecraft"),
                "steps": action_result.get("steps") or (thought.get("proposed_action", {}).get("skill", {}).get("steps", []) if isinstance(thought.get("proposed_action", {}).get("skill"), dict) else []),
                "approved": verdict.approved if verdict else True,
                "initiative": action_result.get("initiative") or thought.get("proposed_action", {}).get("initiative") or (action_result.get("details", {}).get("initiative") if isinstance(action_result.get("details"), dict) else None),
                "drive_id": action_result.get("drive_id") or thought.get("proposed_action", {}).get("drive_id"),
                "cancel_follow": bool(action_result.get("cancel_follow") or thought.get("proposed_action", {}).get("cancel_follow") or (isinstance(action_result.get("details"), dict) and action_result.get("details", {}).get("cancel_follow"))),
                "stay_mode": bool(action_result.get("stay_mode") or thought.get("proposed_action", {}).get("stay_mode") or (isinstance(action_result.get("details"), dict) and action_result.get("details", {}).get("stay_mode"))),
                "cycle": cycle_id
            }
            self.wfile.write(json.dumps(resp_data).encode("utf-8"))
        finally:
            governor.release_spawn(spawn_id)

    def log_message(self, format, *args):
        # Quiet default BaseHTTPRequestHandler logging
        pass


def run_relay(port: int = PORT):
    mind = MindLoop(operator_authenticated=False)
    RelayHandler.mind = mind

    from observer import continuous_observer
    continuous_observer.attach_mind(mind)
    continuous_observer.start()

    tailscale_ip = get_tailscale_ip()
    servers: List[ThreadingHTTPServer] = []

    # 1. Bind to Localhost (127.0.0.1)
    server_local = ThreadingHTTPServer(("127.0.0.1", port), RelayHandler)
    servers.append(server_local)
    print(f"[RELAY] Bound to Localhost: 127.0.0.1:{port}")

    # 2. Bind to Tailscale interface (OFF 0.0.0.0)
    if tailscale_ip and tailscale_ip != "127.0.0.1":
        try:
            server_ts = ThreadingHTTPServer((tailscale_ip, port), RelayHandler)
            servers.append(server_ts)
            print(f"[RELAY] Bound to Tailscale interface: {tailscale_ip}:{port}")
        except Exception as e:
            print(f"[RELAY WARN] Could not bind to Tailscale IP {tailscale_ip}:{port} ({e}). Serving on localhost.")

    print(f"[RELAY] Authoritative ATMAN relay server active -- OFF 0.0.0.0.")
    print(f"[RELAY] Serving single-page Chat UI on GET /")

    # Start listener threads
    threads = []
    for s in servers:
        t = threading.Thread(target=s.serve_forever, daemon=True)
        t.start()
        threads.append(t)

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[RELAY] Shutting down relay server...")
    finally:
        try:
            from observer import continuous_observer
            continuous_observer.stop()
        except Exception:
            pass
        for s in servers:
            s.shutdown()
            s.server_close()


if __name__ == "__main__":
    run_relay()
