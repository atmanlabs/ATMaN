"""ATMAN Phase 3 — bounded self-improvement engine.

Safe surface only:
- add skills via skill_repo (with backup/sandbox/changelog)
- add extension modules under self_improve/extensions/*.py
- status / list / rollback of recorded changes

Never touches sealed/protected core paths (gate_policy, atman_core, seal, wake,
crate, TSC, atman-private, psc.json direct writes).
"""
from __future__ import annotations

import ast
import json
import re
import shutil
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

HERE = Path(__file__).resolve().parent
EXO_ROOT = HERE.parent

BACKUP_DIR = HERE / "backups"
SANDBOX_DIR = HERE / "sandbox"
EXT_DIR = HERE / "extensions"
CHANGELOG = HERE / "CHANGELOG.md"
FAILURES = HERE / "FAILURES.jsonl"
CHANGES_INDEX = HERE / "changes_index.json"

PROTECTED_NAMES = frozenset({
    "gate_policy.json",
    "atman_core.py",
    "core.py",
    "crate.py",
    "wake.py",
    "seal.py",
    "psc.json",
})
PROTECTED_SUBSTR = (
    "atman-private",
    "tsc.atman.private",
    "stage1-seal",
    "gate_policy",
)

SKILL_NAME_RE = re.compile(r"^[A-Za-z0-9_]+$")
REFUSE_PAYLOAD_TOKENS = (
    "modify_core",
    "gate_policy",
    "tsc",
    "atman-private",
    "stage1-seal",
)


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class SelfImproveEngine:
    """Bounded self-improvement with backup, sandbox, and rollback."""

    PROTECTED_NAMES = PROTECTED_NAMES
    PROTECTED_SUBSTR = PROTECTED_SUBSTR

    def __init__(self, root: Optional[Path] = None):
        self.root = Path(root) if root else EXO_ROOT
        self.backup_dir = self.root / "self_improve" / "backups"
        self.sandbox_dir = self.root / "self_improve" / "sandbox"
        self.ext_dir = self.root / "self_improve" / "extensions"
        self.changelog = self.root / "self_improve" / "CHANGELOG.md"
        self.failures = self.root / "self_improve" / "FAILURES.jsonl"
        self.changes_index = self.root / "self_improve" / "changes_index.json"
        self.proposals_dir = self.root / "self_improve" / "proposals"
        for d in (self.backup_dir, self.sandbox_dir, self.ext_dir, self.proposals_dir):
            d.mkdir(parents=True, exist_ok=True)
        if not self.changelog.exists():
            self.changelog.write_text(
                "# Self-Improve CHANGELOG\n\n", encoding="utf-8"
            )
        if not self.changes_index.exists():
            self._write_index({"changes": []})

    # ------------------------------------------------------------------
    # Protection
    # ------------------------------------------------------------------
    def is_protected(self, path: Any) -> bool:
        """Return True if path is sealed/forbidden for self-improve writes."""
        try:
            p = Path(path).resolve()
        except Exception:
            p = Path(str(path))
        name = p.name.lower()
        if name in {n.lower() for n in self.PROTECTED_NAMES}:
            return True
        text = str(p).replace("\\", "/").lower()
        for sub in self.PROTECTED_SUBSTR:
            if sub.lower() in text:
                return True
        # Also refuse writing into atman-private sibling
        try:
            private = (self.root.parent / "atman-private").resolve()
            if private.exists() and private in p.parents or p == private:
                return True
        except Exception:
            pass
        return False

    # ------------------------------------------------------------------
    # Index / changelog helpers
    # ------------------------------------------------------------------
    def _read_index(self) -> Dict[str, Any]:
        try:
            data = json.loads(self.changes_index.read_text(encoding="utf-8"))
            if isinstance(data, dict) and isinstance(data.get("changes"), list):
                return data
        except Exception:
            pass
        return {"changes": []}

    def _write_index(self, data: Dict[str, Any]) -> None:
        tmp = self.changes_index.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        tmp.replace(self.changes_index)

    def _append_changelog(self, line: str) -> None:
        with self.changelog.open("a", encoding="utf-8") as fh:
            fh.write(line.rstrip() + "\n")

    def _append_failure(self, record: Dict[str, Any]) -> None:
        with self.failures.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")

    def _record_change(self, change: Dict[str, Any]) -> str:
        idx = self._read_index()
        idx["changes"].append(change)
        self._write_index(idx)
        self._append_changelog(
            f"- [{change.get('ts')}] {change.get('id')} "
            f"{change.get('kind')} {change.get('summary')} "
            f"ok={change.get('ok')} dry_run={change.get('dry_run')}"
        )
        return change["id"]

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def status(self) -> Dict[str, Any]:
        idx = self._read_index()
        changes = idx.get("changes", [])
        skills_path = self.root / "skills.json"
        proposed = [
            c for c in changes
            if c.get("kind") == "propose_skill" and c.get("status") == "proposed"
        ]
        return {
            "ok": True,
            "engine": "SelfImproveEngine",
            "root": str(self.root),
            "backup_dir": str(self.backup_dir),
            "sandbox_dir": str(self.sandbox_dir),
            "ext_dir": str(self.ext_dir),
            "proposals_dir": str(self.proposals_dir),
            "change_count": len(changes),
            "active_changes": sum(1 for c in changes if c.get("ok") and not c.get("rolled_back") and not c.get("dry_run") and c.get("status") != "proposed"),
            "proposed_count": len(proposed),
            "skills_json_exists": skills_path.exists(),
            "protected_names": sorted(self.PROTECTED_NAMES),
        }

    def list_changes(self) -> Dict[str, Any]:
        idx = self._read_index()
        return {"ok": True, "changes": list(idx.get("changes", []))}

    def _validate_skill(self, skill: Dict[str, Any]) -> Optional[str]:
        if not isinstance(skill, dict):
            return "skill must be a dict"
        name = str(skill.get("name", "")).strip()
        if not name or not SKILL_NAME_RE.fullmatch(name):
            return "skill name must be alphanumeric/underscore"
        # Refuse dangerous payload tokens anywhere in serialized skill
        blob = json.dumps(skill, ensure_ascii=False).lower()
        for tok in REFUSE_PAYLOAD_TOKENS:
            if tok.lower() in blob:
                return f"skill payload refuses protected token: {tok}"
        steps = skill.get("steps")
        if steps is not None and not isinstance(steps, list):
            return "skill steps must be a list"
        domain = skill.get("domain")
        if domain is not None and not isinstance(domain, str):
            return "skill domain must be a string"
        return None

    def add_skill(self, skill: Dict[str, Any], dry_run: bool = False) -> Dict[str, Any]:
        err = self._validate_skill(skill)
        if err:
            rec = {
                "ts": _now_iso(),
                "kind": "add_skill",
                "error": err,
                "skill_name": (skill or {}).get("name") if isinstance(skill, dict) else None,
            }
            self._append_failure(rec)
            return {"ok": False, "error": err, "dry_run": dry_run}

        change_id = f"chg_{_utc_stamp()}_{uuid.uuid4().hex[:8]}"
        skills_path = self.root / "skills.json"
        if self.is_protected(skills_path):
            # skills.json is intentionally NOT protected; belt-and-suspenders
            pass

        # Schema/sandbox JSON write
        sandbox_file = self.sandbox_dir / f"{change_id}_skill.json"
        sandbox_file.write_text(json.dumps(skill, indent=2), encoding="utf-8")

        if dry_run:
            change = {
                "id": change_id,
                "ts": _now_iso(),
                "kind": "add_skill",
                "summary": f"dry-run add_skill {skill.get('name')}",
                "ok": True,
                "dry_run": True,
                "skill_name": skill.get("name"),
                "sandbox": str(sandbox_file),
                "backup": None,
                "rolled_back": False,
            }
            self._record_change(change)
            return {
                "ok": True,
                "dry_run": True,
                "change_id": change_id,
                "skill_name": skill.get("name"),
                "sandbox": str(sandbox_file),
                "message": "dry-run OK — schema passed, no skills.json write",
            }

        backup_path = None
        try:
            # Backup skills.json if present
            if skills_path.exists():
                backup_path = self.backup_dir / f"skills.json.{change_id}.bak"
                shutil.copy2(skills_path, backup_path)
            else:
                backup_path = self.backup_dir / f"skills.json.{change_id}.missing"
                backup_path.write_text("", encoding="utf-8")

            from skills import skill_repo

            stored = skill_repo.store_skill(dict(skill))
            change = {
                "id": change_id,
                "ts": _now_iso(),
                "kind": "add_skill",
                "summary": f"add_skill {skill.get('name')}",
                "ok": True,
                "dry_run": False,
                "skill_name": skill.get("name"),
                "sandbox": str(sandbox_file),
                "backup": str(backup_path),
                "target": str(skills_path),
                "rolled_back": False,
                "stored": {"name": stored.get("name"), "domain": stored.get("domain")},
            }
            self._record_change(change)
            return {
                "ok": True,
                "dry_run": False,
                "change_id": change_id,
                "skill_name": skill.get("name"),
                "backup": str(backup_path),
                "stored": stored,
            }
        except Exception as e:
            # Restore backup
            try:
                if backup_path and backup_path.exists() and backup_path.stat().st_size > 0:
                    shutil.copy2(backup_path, skills_path)
                elif backup_path and str(backup_path).endswith(".missing") and skills_path.exists():
                    skills_path.unlink()
            except Exception as restore_err:
                self._append_failure({
                    "ts": _now_iso(),
                    "kind": "add_skill_restore",
                    "error": str(restore_err),
                    "change_id": change_id,
                })
            self._append_failure({
                "ts": _now_iso(),
                "kind": "add_skill",
                "error": str(e),
                "change_id": change_id,
                "skill_name": skill.get("name"),
            })
            change = {
                "id": change_id,
                "ts": _now_iso(),
                "kind": "add_skill",
                "summary": f"FAILED add_skill {skill.get('name')}: {e}",
                "ok": False,
                "dry_run": False,
                "skill_name": skill.get("name"),
                "sandbox": str(sandbox_file),
                "backup": str(backup_path) if backup_path else None,
                "rolled_back": False,
                "error": str(e),
            }
            self._record_change(change)
            return {"ok": False, "error": str(e), "change_id": change_id, "dry_run": False}

    def add_extension_module(
        self, name: str, source: str, dry_run: bool = False
    ) -> Dict[str, Any]:
        name = str(name or "").strip()
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
            return {"ok": False, "error": "extension name must be a valid Python identifier"}
        if not name.endswith(".py"):
            filename = f"{name}.py"
        else:
            filename = name
            name = name[:-3]

        target = (self.ext_dir / filename).resolve()
        # Must stay under self_improve/extensions
        try:
            target.relative_to(self.ext_dir.resolve())
        except ValueError:
            return {"ok": False, "error": "extension path escapes self_improve/extensions"}

        if self.is_protected(target):
            return {"ok": False, "error": f"protected path refused: {target}"}

        # Syntax test
        try:
            ast.parse(source)
        except SyntaxError as se:
            self._append_failure({
                "ts": _now_iso(),
                "kind": "add_extension",
                "error": f"syntax: {se}",
                "name": name,
            })
            return {"ok": False, "error": f"syntax error: {se}"}

        change_id = f"chg_{_utc_stamp()}_{uuid.uuid4().hex[:8]}"
        sandbox_file = self.sandbox_dir / f"{change_id}_{filename}"
        sandbox_file.write_text(source, encoding="utf-8")

        if dry_run:
            change = {
                "id": change_id,
                "ts": _now_iso(),
                "kind": "add_extension",
                "summary": f"dry-run add_extension {filename}",
                "ok": True,
                "dry_run": True,
                "target": str(target),
                "sandbox": str(sandbox_file),
                "backup": None,
                "rolled_back": False,
            }
            self._record_change(change)
            return {
                "ok": True,
                "dry_run": True,
                "change_id": change_id,
                "target": str(target),
                "message": "dry-run OK — syntax passed, no write",
            }

        backup_path = None
        try:
            if target.exists():
                backup_path = self.backup_dir / f"{filename}.{change_id}.bak"
                shutil.copy2(target, backup_path)
            target.write_text(source, encoding="utf-8")
            change = {
                "id": change_id,
                "ts": _now_iso(),
                "kind": "add_extension",
                "summary": f"add_extension {filename}",
                "ok": True,
                "dry_run": False,
                "target": str(target),
                "sandbox": str(sandbox_file),
                "backup": str(backup_path) if backup_path else None,
                "rolled_back": False,
            }
            self._record_change(change)
            return {
                "ok": True,
                "dry_run": False,
                "change_id": change_id,
                "target": str(target),
                "backup": str(backup_path) if backup_path else None,
            }
        except Exception as e:
            try:
                if backup_path and backup_path.exists():
                    shutil.copy2(backup_path, target)
                elif target.exists() and not backup_path:
                    target.unlink()
            except Exception:
                pass
            self._append_failure({
                "ts": _now_iso(),
                "kind": "add_extension",
                "error": str(e),
                "change_id": change_id,
                "name": name,
            })
            change = {
                "id": change_id,
                "ts": _now_iso(),
                "kind": "add_extension",
                "summary": f"FAILED add_extension {filename}: {e}",
                "ok": False,
                "dry_run": False,
                "target": str(target),
                "error": str(e),
                "rolled_back": False,
            }
            self._record_change(change)
            return {"ok": False, "error": str(e), "change_id": change_id}


    def propose_skill(self, skill: Dict[str, Any], source: str = "freeplay") -> Dict[str, Any]:
        """Validate + park a skill proposal. Does NOT write skills.json."""
        err = self._validate_skill(skill)
        if err:
            rec = {
                "ts": _now_iso(),
                "kind": "propose_skill",
                "error": err,
                "skill_name": (skill or {}).get("name") if isinstance(skill, dict) else None,
                "source": source,
            }
            self._append_failure(rec)
            return {"ok": False, "error": err, "source": source}

        change_id = f"chg_{_utc_stamp()}_{uuid.uuid4().hex[:8]}"
        proposal = {
            "id": change_id,
            "ts": _now_iso(),
            "source": source,
            "status": "proposed",
            "skill": dict(skill),
            "skill_name": skill.get("name"),
        }
        proposal_path = self.proposals_dir / f"{change_id}.json"
        proposal_path.write_text(json.dumps(proposal, indent=2), encoding="utf-8")

        # Sandbox copy for review (same rails as add_skill dry-run)
        sandbox_file = self.sandbox_dir / f"{change_id}_skill.json"
        sandbox_file.write_text(json.dumps(skill, indent=2), encoding="utf-8")

        change = {
            "id": change_id,
            "ts": proposal["ts"],
            "kind": "propose_skill",
            "summary": f"PROPOSE (not applied) {skill.get('name')} source={source}",
            "ok": True,
            "dry_run": True,
            "status": "proposed",
            "skill_name": skill.get("name"),
            "source": source,
            "proposal_path": str(proposal_path),
            "sandbox": str(sandbox_file),
            "backup": None,
            "rolled_back": False,
        }
        self._record_change(change)
        # Explicit PROPOSE marker line for Operator's changelog scan
        self._append_changelog(
            f"- [{change['ts']}] {change_id} PROPOSE (not applied) "
            f"skill={skill.get('name')} source={source} status=proposed"
        )
        return {
            "ok": True,
            "proposed": True,
            "applied": False,
            "change_id": change_id,
            "skill_name": skill.get("name"),
            "source": source,
            "status": "proposed",
            "proposal_path": str(proposal_path),
            "sandbox": str(sandbox_file),
            "message": "PROPOSE recorded — skills.json unchanged; Operator reviews via CHANGELOG",
        }

    def list_proposals(self, status: str = "proposed") -> Dict[str, Any]:
        """List proposal JSON files under self_improve/proposals/."""
        wanted = (status or "").strip().lower()
        items: List[Dict[str, Any]] = []
        if self.proposals_dir.exists():
            for p in sorted(self.proposals_dir.glob("*.json")):
                try:
                    data = json.loads(p.read_text(encoding="utf-8"))
                except Exception:
                    continue
                if not isinstance(data, dict):
                    continue
                if wanted and wanted != "all" and str(data.get("status", "")).lower() != wanted:
                    continue
                data["_path"] = str(p)
                items.append(data)
        return {"ok": True, "count": len(items), "proposals": items, "status_filter": wanted or "all"}

    def accept_proposal(self, proposal_id: str, dry_run: bool = False) -> Dict[str, Any]:
        """Accept a parked proposal by calling add_skill (backup rails)."""
        proposal_id = str(proposal_id or "").strip()
        if not proposal_id:
            return {"ok": False, "error": "proposal_id required"}
        path = self.proposals_dir / f"{proposal_id}.json"
        if not path.exists():
            # allow bare id match against files
            matches = list(self.proposals_dir.glob(f"*{proposal_id}*.json")) if self.proposals_dir.exists() else []
            if len(matches) == 1:
                path = matches[0]
            else:
                return {"ok": False, "error": f"proposal not found: {proposal_id}"}
        try:
            proposal = json.loads(path.read_text(encoding="utf-8"))
        except Exception as e:
            return {"ok": False, "error": f"cannot read proposal: {e}"}
        if not isinstance(proposal, dict):
            return {"ok": False, "error": "invalid proposal file"}
        if str(proposal.get("status", "")).lower() not in ("proposed", "pending", ""):
            return {
                "ok": False,
                "error": f"proposal status is {proposal.get('status')}, not proposed",
                "proposal_id": proposal.get("id"),
            }
        skill = proposal.get("skill")
        if not isinstance(skill, dict):
            return {"ok": False, "error": "proposal missing skill dict"}

        result = self.add_skill(skill, dry_run=dry_run)
        if not result.get("ok"):
            return {**result, "proposal_id": proposal.get("id"), "accepted": False}

        if not dry_run:
            proposal["status"] = "accepted"
            proposal["accepted_ts"] = _now_iso()
            proposal["accept_change_id"] = result.get("change_id")
            path.write_text(json.dumps(proposal, indent=2), encoding="utf-8")
            # Mark original propose index entry if present
            idx = self._read_index()
            for c in idx.get("changes", []):
                if c.get("id") == proposal.get("id") and c.get("kind") == "propose_skill":
                    c["status"] = "accepted"
                    c["accepted_ts"] = proposal["accepted_ts"]
                    c["accept_change_id"] = result.get("change_id")
                    break
            self._write_index(idx)
            self._append_changelog(
                f"- [{_now_iso()}] ACCEPT {proposal.get('id')} -> "
                f"{result.get('change_id')} skill={skill.get('name')}"
            )
        return {
            "ok": True,
            "accepted": not dry_run,
            "dry_run": dry_run,
            "proposal_id": proposal.get("id"),
            "add_skill_result": result,
            "skill_name": skill.get("name"),
        }

    def rollback(self, change_id: str) -> Dict[str, Any]:
        change_id = str(change_id or "").strip()
        if not change_id:
            return {"ok": False, "error": "change_id required"}
        idx = self._read_index()
        found = None
        for c in idx.get("changes", []):
            if c.get("id") == change_id:
                found = c
                break
        if not found:
            return {"ok": False, "error": f"change_id not found: {change_id}"}
        if found.get("dry_run"):
            found["rolled_back"] = True
            found["rollback_note"] = "dry-run had no persistent apply"
            self._write_index(idx)
            self._append_changelog(
                f"- [{_now_iso()}] ROLLBACK {change_id} (dry-run noop)"
            )
            return {"ok": True, "change_id": change_id, "message": "dry-run rollback noop"}
        if found.get("rolled_back"):
            return {"ok": True, "change_id": change_id, "message": "already rolled back"}
        if not found.get("ok"):
            return {"ok": False, "error": "cannot rollback failed change"}

        kind = found.get("kind")
        backup = found.get("backup")
        target = found.get("target")

        try:
            if kind == "add_skill":
                skills_path = Path(target) if target else (self.root / "skills.json")
                if self.is_protected(skills_path):
                    return {"ok": False, "error": "refusing protected skills path"}
                if backup and Path(backup).exists():
                    b = Path(backup)
                    if str(b).endswith(".missing") or b.stat().st_size == 0:
                        if skills_path.exists():
                            # Remove only the skill we added if possible
                            skill_name = str(found.get("skill_name", "")).strip().lower()
                            if skill_name and skills_path.exists():
                                data = json.loads(skills_path.read_text(encoding="utf-8"))
                                if isinstance(data, dict) and skill_name in data:
                                    data.pop(skill_name, None)
                                    skills_path.write_text(
                                        json.dumps(data, indent=2), encoding="utf-8"
                                    )
                                elif not data:
                                    skills_path.unlink()
                            else:
                                skills_path.unlink()
                    else:
                        shutil.copy2(b, skills_path)
                        # Reload skill_repo in-process
                        try:
                            from skills import skill_repo
                            skill_repo._load()
                        except Exception:
                            pass
                else:
                    return {"ok": False, "error": "no backup available for rollback"}
            elif kind == "add_extension":
                t = Path(target) if target else None
                if not t:
                    return {"ok": False, "error": "no target for extension rollback"}
                if self.is_protected(t):
                    return {"ok": False, "error": "refusing protected path"}
                try:
                    t.resolve().relative_to(self.ext_dir.resolve())
                except ValueError:
                    return {"ok": False, "error": "rollback target outside extensions"}
                if backup and Path(backup).exists():
                    shutil.copy2(backup, t)
                elif t.exists():
                    t.unlink()
            else:
                return {"ok": False, "error": f"unknown kind: {kind}"}

            found["rolled_back"] = True
            found["rollback_ts"] = _now_iso()
            self._write_index(idx)
            self._append_changelog(
                f"- [{_now_iso()}] ROLLBACK {change_id} kind={kind}"
            )
            return {"ok": True, "change_id": change_id, "kind": kind, "restored_from": backup}
        except Exception as e:
            self._append_failure({
                "ts": _now_iso(),
                "kind": "rollback",
                "error": str(e),
                "change_id": change_id,
            })
            return {"ok": False, "error": str(e), "change_id": change_id}


    ALLOW_WRITE_FILES = frozenset({
        "minecraft_chat.py", "minecraft_context.py", "working_context.py",
        "desktop_worker.py", "drives.py", "episode_segmenter.py", "evolving_brain.py",
        "governor.py", "observer.py", "senses.py", "significant_events.py",
        "skills.py", "sleep.py", "sweep.py", "voice.py", "relay.py", "loop.py",
        "reason.py", "cockpit.py", "config.yaml", "config.py",
    })
    ALLOW_WRITE_PREFIXES = ("self_improve/", "extensions/", "adapters/", "guardian/", "ui/")

    def _allowlisted_rel(self, rel: str) -> bool:
        rel = (rel or "").replace("\\", "/").lstrip("./")
        if not rel or ".." in rel.split("/"):
            return False
        target = (self.root / rel)
        if self.is_protected(target):
            return False
        name = Path(rel).name
        if name in self.ALLOW_WRITE_FILES:
            return True
        return any(rel.startswith(p) for p in self.ALLOW_WRITE_PREFIXES)

    def patch_allowlisted_file(self, relative_path: str, content: str, dry_run: bool = False) -> Dict[str, Any]:
        """Soup-up style patch on allowlisted non-TSC files: backup, syntax test, write or rollback."""
        rel = (relative_path or "").replace("\\", "/").lstrip("./")
        if not self._allowlisted_rel(rel):
            return {"ok": False, "error": f"not allowlisted / protected: {rel}"}
        target = self.root / rel
        low = (content or "").lower()
        for bad in ("modify_core", "gate_policy", "atman-private", "stage1-seal", "tsc.atman.private", "atman_private"):
            if bad in low.replace("/", "-"):
                return {"ok": False, "error": f"content references protected token: {bad}"}
        change_id = f"chg_{_utc_stamp()}_{uuid.uuid4().hex[:8]}"
        sandbox_file = self.sandbox_dir / f"{change_id}_{Path(rel).name}"
        sandbox_file.write_text(content or "", encoding="utf-8")
        if rel.endswith(".py"):
            try:
                ast.parse(content or "")
            except SyntaxError as se:
                self._append_failure({"ts": _now_iso(), "kind": "patch_file", "error": str(se), "path": rel})
                return {"ok": False, "error": f"syntax error: {se}", "change_id": change_id}
        if dry_run:
            self._record_change({
                "id": change_id, "ts": _now_iso(), "kind": "patch_file",
                "summary": f"dry-run patch {rel}", "ok": True, "dry_run": True,
                "target": str(target), "sandbox": str(sandbox_file),
            })
            return {"ok": True, "dry_run": True, "change_id": change_id, "target": str(target)}
        backup_path = None
        try:
            if target.exists():
                backup_path = self.backup_dir / f"{Path(rel).name}.{change_id}.bak"
                shutil.copy2(target, backup_path)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content or "", encoding="utf-8")
            self._record_change({
                "id": change_id, "ts": _now_iso(), "kind": "patch_file",
                "summary": f"patch {rel}", "ok": True, "dry_run": False,
                "target": str(target), "backup": str(backup_path) if backup_path else None,
            })
            self._append_changelog(f"- [{_now_iso()}] {change_id} AUTO-PATCH {rel} (sealed core untouched)")
            return {"ok": True, "change_id": change_id, "target": str(target), "backup": str(backup_path) if backup_path else None}
        except Exception as e:
            try:
                if backup_path and Path(backup_path).exists():
                    shutil.copy2(backup_path, target)
            except Exception:
                pass
            self._append_failure({"ts": _now_iso(), "kind": "patch_file", "error": str(e), "path": rel})
            return {"ok": False, "error": str(e), "change_id": change_id}


    def ingest_scout_results(self, results: Any, source: str = "github_scout") -> Dict[str, Any]:
        """Scout → APPLY safe upgrades (skills + extension stubs). Sealed core untouched.

        Operator lock: searching alone is not improvement. Each GitHub lead becomes:
        1) a stored skill (propose + accept)
        2) a real extension stub under self_improve/extensions/
        """
        if isinstance(results, dict):
            blob = json.dumps(results, ensure_ascii=False)
        else:
            blob = str(results or "")
        urls = re.findall(r"https?://(?:www\.)?github\.com/[\w.-]+/[\w.-]+", blob, flags=re.I)
        urls = list(dict.fromkeys(urls))[:5]

        applied = []
        extensions = []
        skipped = []

        leads = urls or ["local://self_upgrade_followup"]
        for lead in leads:
            if lead.startswith("http"):
                slug = re.sub(r"[^a-z0-9]+", "_", lead.rstrip("/").split("/")[-1].lower())[:28] or "repo"
                skill_name = f"scout_{slug}"[:48]
                desc = f"Upgrade lead from {lead} — implement safe local capability; sealed core locked."
                ext_body = (
                    '"""Auto-parked scout stub from GitHub self-upgrade.\n\n'
                    f"Source: {lead}\n"
                    "Safety: sealed core / gate_policy / private soul are never imported or patched here.\n"
                    "Next: flesh this module with one concrete safe capability, then wire via cockpit if needed.\n"
                    '"""\n'
                    "REPO = %r\n"
                    "STATUS = \"parked_stub\"\n"
                    "\n"
                    "def describe() -> dict:\n"
                    "    return {\"repo\": REPO, \"status\": STATUS, \"safe\": True}\n"
                ) % lead
            else:
                skill_name = "scout_self_upgrade_followup"
                desc = "Self-upgrade follow-up: pick one safe local capability and wire it; sealed core locked."
                ext_body = (
                    '"""Follow-up stub when scout returned no GitHub URLs."""\n'
                    "STATUS = \"needs_manual_lead\"\n"
                    "\n"
                    "def describe() -> dict:\n"
                    "    return {\"status\": STATUS}\n"
                )

            # Skip duplicate skill already stored
            try:
                from skills import skill_repo
                existing = skill_repo.get_skill(skill_name)
            except Exception:
                existing = None
            if existing:
                skipped.append(skill_name)
                continue

            skill = {
                "name": skill_name,
                "domain": "learning",
                "description": desc,
                "steps": [
                    f"Study lead {lead}",
                    "Extract one safe local technique",
                    "Implement on allowlisted paths only",
                ],
                "governance": {
                    "requires_supervision": False,
                    "judge_gated": False,
                    "auto_apply": True,
                    "source": source,
                },
            }
            proposed = self.propose_skill(skill, source=source)
            if not proposed.get("ok"):
                skipped.append({"name": skill_name, "error": proposed.get("error")})
                continue
            accepted = self.accept_proposal(str(proposed.get("change_id") or ""), dry_run=False)
            if accepted.get("ok"):
                applied.append(skill_name)
            else:
                skipped.append({"name": skill_name, "error": accepted.get("error")})

            # Real file on disk (allowlisted under self_improve/extensions)
            ext = self.add_extension_module(skill_name, ext_body, dry_run=False)
            if ext.get("ok"):
                extensions.append(ext.get("target") or skill_name)
            else:
                skipped.append({"ext": skill_name, "error": ext.get("error")})

        self._append_changelog(
            f"- [{_now_iso()}] SCOUT-APPLY source={source} urls={len(urls)} "
            f"skills_applied={len(applied)} ext_written={len(extensions)} skipped={len(skipped)}"
        )
        return {
            "ok": True,
            "urls": urls,
            "applied_skills": applied,
            "extensions": extensions,
            "skipped": skipped,
            "count": len(applied),
            "improved": bool(applied or extensions),
        }

    def dispatch(self, args: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        args = args or {}
        action = str(args.get("action", "status")).strip().lower()
        dry_run = bool(args.get("dry_run", False))

        if action == "status":
            return self.status()
        if action == "list":
            return self.list_changes()
        if action == "rollback":
            return self.rollback(str(args.get("change_id", "")))
        if action == "add_skill":
            skill = args.get("skill")
            if skill is None:
                return {"ok": False, "error": "skill dict required"}
            return self.add_skill(skill, dry_run=dry_run)
        if action == "add_extension":
            return self.add_extension_module(
                str(args.get("name", "")),
                str(args.get("source", "")),
                dry_run=dry_run,
            )
        if action == "propose_skill":
            skill = args.get("skill")
            if skill is None:
                return {"ok": False, "error": "skill dict required"}
            return self.propose_skill(skill, source=str(args.get("source", "dispatch")))
        if action in ("list_proposals", "proposals"):
            return self.list_proposals(status=str(args.get("status", "proposed")))
        if action == "accept_proposal":
            return self.accept_proposal(
                str(args.get("proposal_id") or args.get("change_id") or ""),
                dry_run=dry_run,
            )
        return {
            "ok": False,
            "error": f"unknown action '{action}'",
            "allowed": [
                "status", "list", "rollback", "add_skill", "add_extension",
                "propose_skill", "list_proposals", "accept_proposal",
            ],
        }


# Module singleton
engine = SelfImproveEngine()
