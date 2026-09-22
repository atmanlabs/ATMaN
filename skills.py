"""Core Skill Repository for ATMAN (ATMAN Live).

Stores, indexes, and retrieves learned skills across domains:
- 'minecraft' (e.g. mine_tree, place_block, craft)
- 'desktop'   (e.g. open_app, window_manage)
- 'web'       (e.g. search, navigate)

Each skill contains:
- name: Unique identifier (e.g. 'mine_tree')
- domain: Operational domain tag ('minecraft', 'desktop', 'web')
- description: Human-readable purpose
- preconditions: What must be true before execution
- steps: Ordered list of discrete executable steps
- effects: What changes when successfully executed
- governance: Security & judge gating requirements (requires_supervision=True)
- metadata: Creation time, author, demonstration source

All skill executions must be gated by the Judge before dispatch.
A learned skill is NEVER auto-authorized.
"""
from dataclasses import dataclass, field, asdict
import json
import os
from pathlib import Path
import time
from typing import Any, Dict, List, Optional

HERE = Path(__file__).resolve().parent
DEFAULT_SKILLS_PATH = HERE / "skills.json"


def validate_minecraft_skill(skill):
    """Reject malformed/unimplemented procedures before storage or dispatch."""
    import re
    if not isinstance(skill, dict) or skill.get("domain") != "minecraft":
        raise ValueError("Expected a Minecraft skill")
    if not re.fullmatch(r"[a-z0-9][a-z0-9_]{0,47}", skill.get("name", "")):
        raise ValueError("Invalid skill name")
    steps = skill.get("steps")
    if not isinstance(steps, list) or not 1 <= len(steps) <= 128:
        raise ValueError("A skill needs 1 to 128 demonstrated steps")
    allowed = {"break", "place", "equip", "craft", "locate_target", "approach_target", "equip_tool", "dig_block", "collect_drop"}
    def identifier(value):
        return isinstance(value, str) and re.fullmatch(r"[a-z0-9_]+", value)
    for step in steps:
        if not isinstance(step, dict) or step.get("action") not in allowed or not isinstance(step.get("params"), dict):
            raise ValueError("Unknown or invalid skill step")
        action, params = step["action"], step["params"]
        if action in ("break", "place") and not identifier(params.get("block")):
            raise ValueError("Block step needs a block type")
        if action in ("equip", "craft") and not identifier(params.get("item")):
            raise ValueError("Equipment/crafting step needs an item")
        if action == "craft" and (type(params.get("count")) is not int or not 1 <= params["count"] <= 2304):
            raise ValueError("Invalid crafted item count")
        if action == "place" or "offset" in params:
            offset = params.get("offset")
            if not isinstance(offset, list) or len(offset) != 3 or any(type(n) is not int or abs(n) > 32 for n in offset):
                raise ValueError("Placement needs a demonstrated offset within 32 blocks")


@dataclass
class SkillStep:
    step: int
    action: str
    description: str
    params: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Skill:
    name: str
    domain: str
    description: str
    preconditions: Dict[str, Any] = field(default_factory=dict)
    steps: List[Dict[str, Any]] = field(default_factory=list)
    effects: Dict[str, Any] = field(default_factory=dict)
    governance: Dict[str, Any] = field(default_factory=lambda: {
        "requires_supervision": True,
        "judge_gated": True,
        "auto_authorized": False
    })
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Skill":
        return cls(
            name=data.get("name", ""),
            domain=data.get("domain", "general"),
            description=data.get("description", ""),
            preconditions=data.get("preconditions", {}),
            steps=data.get("steps", []),
            effects=data.get("effects", {}),
            governance=data.get("governance", {
                "requires_supervision": True,
                "judge_gated": True,
                "auto_authorized": False
            }),
            metadata=data.get("metadata", {})
        )


class SkillRepository:
    """Core persistent repository for cross-domain learned skills."""

    def __init__(self, storage_path: Optional[Path | str] = None):
        self.storage_path = Path(storage_path) if storage_path else DEFAULT_SKILLS_PATH
        self._skills: Dict[str, Dict[str, Any]] = {}
        self._load()

    def _load(self):
        if self.storage_path.exists():
            try:
                data = json.loads(self.storage_path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    self._skills = data
                elif isinstance(data, list):
                    self._skills = {s.get("name", f"skill_{i}"): s for i, s in enumerate(data)}
            except Exception as e:
                print(f"[SKILL REPO] Error loading {self.storage_path}: {e}")
                self._skills = {}
        else:
            self._skills = {}

    def _save(self):
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.storage_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._skills, indent=2), encoding="utf-8")
        tmp.replace(self.storage_path)

    def store_skill(self, skill_data: Dict[str, Any]) -> Dict[str, Any]:
        """Store or update a learned skill in the repository."""
        name = skill_data.get("name", "").strip().lower()
        if not name:
            raise ValueError("Skill name cannot be empty")

        domain = skill_data.get("domain", "general").strip().lower()

        if domain == "minecraft":
            validate_minecraft_skill(skill_data)

        # Enforce governance: a learned skill is never auto-authorized
        governance = skill_data.get("governance", {})
        governance["requires_supervision"] = True
        governance["judge_gated"] = True
        governance["auto_authorized"] = False

        metadata = skill_data.get("metadata", {})
        if "created_at" not in metadata:
            metadata["created_at"] = time.time()
        if "author" not in metadata:
            metadata["author"] = "the operator (Operator)"

        entry = {
            "name": name,
            "domain": domain,
            "description": skill_data.get("description", ""),
            "preconditions": skill_data.get("preconditions", {}),
            "steps": skill_data.get("steps", []),
            "effects": skill_data.get("effects", {}),
            "governance": governance,
            "metadata": metadata
        }

        self._skills[name] = entry
        self._save()
        print(f"[SKILL REPO] Stored skill '{name}' in domain '{domain}' with {len(entry['steps'])} steps.")
        return entry

    def get_skill(self, name: str, domain: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieve a skill by name and optional domain."""
        name = name.strip().lower()
        skill = self._skills.get(name)
        if skill and domain:
            if skill.get("domain", "").lower() != domain.lower():
                return None
        return skill

    def list_skills(self, domain: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all stored skills, optionally filtered by domain."""
        res = list(self._skills.values())
        if domain:
            res = [s for s in res if s.get("domain", "").lower() == domain.lower()]
        return res

    def find_skill(self, query: str, domain: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Match skill by name or keywords."""
        q = query.strip().lower()
        # Direct name match
        if q in self._skills:
            s = self._skills[q]
            if not domain or s.get("domain") == domain:
                return s

        # Keyword matching
        for name, skill in self._skills.items():
            if domain and skill.get("domain") != domain:
                continue
            if name in q or q in name:
                return skill
            # Check description or keywords
            desc = skill.get("description", "").lower()
            if any(term in q for term in name.split("_")):
                return skill
            if "tree" in q and "tree" in name:
                return skill
            if "mine" in q and "mine" in name:
                return skill

        return None


# Global singleton repository in CORE
skill_repo = SkillRepository()
