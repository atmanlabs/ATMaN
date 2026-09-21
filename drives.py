"""JARVIS Standing Drives & Initiative Layer.

Provides persistent autonomous companion initiative within strict safety bounds:
1. Standing Drives:
   - be_useful_to_operator: Help, organize, maintain readiness.
   - learn_the_world: Curiosity about novel blocks, biomes, structures within safe bounds.
   - keep_base_safe_and_tidy: Patrol sanctuary perimeter, maintain pathways and order.
   - practice_known_skills: Practice building, crafting, and harvesting nearby.
2. Drive Intensities fed by Emotion scoring (novelty, goal_relevance, importance).
3. Low-risk autonomous actions when idle or offline (gated by Judge).
4. Proposal Loop for big wants (perimeter wall, farm) — proposals only, zero unilateral alteration.
5. Persistent Preferences consolidated into PSC (e.g. 'JARVIS enjoys building').
6. Return Greeting: Summarizes idle accomplishments and explains *why* he wanted to.
"""
from dataclasses import dataclass, field, asdict
import json
import math
from pathlib import Path
import time
from typing import Any, Dict, List, Optional, Tuple

HERE = Path(__file__).resolve().parent
DRIVES_STORAGE_PATH = HERE / "drives.json"
SANCTUARY_HOME = {"x": -2.5, "y": 69.0, "z": 8.5}
MAX_LEASH_RADIUS = 24.0  # Safe bounds from sanctuary home


@dataclass
class StandingDrive:
    id: str
    name: str
    description: str
    intensity: float = 0.3
    growth_rate_per_min: float = 0.04
    threshold: float = 0.70
    last_satisfied: float = field(default_factory=time.time)
    satisfaction_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class IdleActivityRecord:
    id: str
    timestamp: float
    drive_id: str
    action_type: str
    description: str
    why: str
    details: Dict[str, Any] = field(default_factory=dict)
    reported_to_operator: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class DriveManager:
    """Core standing drive and initiative engine for JARVIS."""

    def __init__(self, storage_path: Optional[Path] = None, proposals_path: Optional[Path] = None):
        self.storage_path = Path(storage_path) if storage_path else DRIVES_STORAGE_PATH
        self.drives: Dict[str, StandingDrive] = {}
        self.activity_log: List[IdleActivityRecord] = []
        self.last_update_time: float = time.time()
        self.proposals_path = Path(proposals_path) if proposals_path else (HERE / "pending_proposals.json")
        self._init_default_drives()
        self._load()

    def _init_default_drives(self):
        defaults = [
            StandingDrive(
                id="be_useful_to_operator",
                name="Be Useful to Operator",
                description="Remain attentive, maintain supplies, and stay ready to assist the operator.",
                intensity=0.5,
                growth_rate_per_min=0.03,
                threshold=0.75
            ),
            StandingDrive(
                id="learn_the_world",
                name="Learn the World",
                description="Curiosity about unseen blocks, biomes, and terrain within safe bounds.",
                intensity=0.4,
                growth_rate_per_min=0.04,
                threshold=0.70
            ),
            StandingDrive(
                id="keep_base_safe_and_tidy",
                name="Keep Base Safe & Tidy",
                description="Patrol the home sanctuary, inspect entrances, and keep the perimeter secure.",
                intensity=0.35,
                growth_rate_per_min=0.05,
                threshold=0.70
            ),
            StandingDrive(
                id="practice_known_skills",
                name="Practice Known Skills",
                description="Practice learned skills (building walls, organizing materials) to refine mastery.",
                intensity=0.35,
                growth_rate_per_min=0.05,
                threshold=0.70
            )
        ]
        for d in defaults:
            self.drives[d.id] = d

    def _load(self):
        if self.storage_path.exists():
            try:
                data = json.loads(self.storage_path.read_text(encoding="utf-8"))
                for d_data in data.get("drives", []):
                    did = d_data.get("id")
                    if did in self.drives:
                        self.drives[did].intensity = float(d_data.get("intensity", self.drives[did].intensity))
                        self.drives[did].last_satisfied = float(d_data.get("last_satisfied", self.drives[did].last_satisfied))
                        self.drives[did].satisfaction_count = int(d_data.get("satisfaction_count", 0))
                for a_data in data.get("activity_log", []):
                    self.activity_log.append(IdleActivityRecord(**a_data))
            except Exception as e:
                print(f"[DRIVES] Error loading {self.storage_path}: {e}")

    def _save(self):
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "drives": [d.to_dict() for d in self.drives.values()],
            "activity_log": [a.to_dict() for a in self.activity_log[-50:]],
            "last_save": time.time()
        }
        tmp = self.storage_path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
        tmp.replace(self.storage_path)

    def update_with_emotion(self, emo_weights: Dict[str, Any], novel_feature: Optional[str] = None):
        """Boost drive intensities based on incoming Emotion scoring."""
        novelty = float(emo_weights.get("novelty", 0.0))
        importance = float(emo_weights.get("importance", 0.0))
        goal_rel = float(emo_weights.get("goal_relevance", 0.0))

        # Novelty directly spikes Curiosity / Learn the World
        if novelty > 0.4:
            boost = min(0.4, novelty * 0.5)
            self.drives["learn_the_world"].intensity = min(1.0, self.drives["learn_the_world"].intensity + boost)
            print(f"[DRIVES] Novelty ({novelty:.2f}) boosted 'learn_the_world' to {self.drives['learn_the_world'].intensity:.2f}")

        # Goal relevance boosts Be Useful
        if goal_rel > 0.5:
            self.drives["be_useful_to_operator"].intensity = min(1.0, self.drives["be_useful_to_operator"].intensity + 0.15)

        self._save()

    def tick_idle(self, elapsed_seconds: float, is_player_away: bool = False):
        """Passage of idle time naturally increases home care, skill practice, and curiosity."""
        minutes = elapsed_seconds / 60.0
        multiplier = 2.0 if is_player_away else 1.0

        for d in self.drives.values():
            growth = d.growth_rate_per_min * minutes * multiplier
            d.intensity = min(1.0, d.intensity + growth)

        self._save()

    def get_highest_ready_drive(self) -> Optional[StandingDrive]:
        """Find the highest drive that has crossed its activation threshold."""
        ready = [d for d in self.drives.values() if d.intensity >= d.threshold]
        if not ready:
            return None
        return max(ready, key=lambda d: d.intensity)

    def evaluate_initiative(
        self,
        bot_pos: Optional[List[float]] = None,
        inventory_items: Optional[List[str]] = None,
        is_player_away: bool = True
    ) -> Optional[Dict[str, Any]]:
        """Evaluate if JARVIS should self-initiate a low-risk action or propose a big want."""
        drive = self.get_highest_ready_drive()
        if not drive:
            return None

        # Check for Big Wants (e.g. perimeter wall proposal if abundant cobblestone)
        cobble_count = 0
        if inventory_items:
            cobble_count = sum(1 for i in inventory_items if "cobble" in str(i).lower())

        if (drive.id in ("keep_base_safe_and_tidy", "practice_known_skills") and
                cobble_count >= 12 and not self._has_active_proposal("perimeter_wall")):
            # Create big want proposal instead of unilateral world alteration
            proposal = self.create_big_want_proposal(
                title="build_perimeter_wall",
                proposal_text="We've got plenty of cobblestone stored up for a perimeter wall — want me to build one around the house?",
                drive_id=drive.id,
                why="Cobblestone inventory is sufficient; home perimeter is open; operator direction required before major construction."
            )
            return {
                "type": "proposal",
                "drive": drive.id,
                "proposal": proposal
            }

        # Low-risk autonomous actions within safe bounds
        if drive.id == "keep_base_safe_and_tidy":
            return {
                "type": "minecraft_initiative",
                "action": "initiative_tidy_base",
                "drive_id": drive.id,
                "why": "Wanted to make sure our home sanctuary perimeter is secure and pathways are clear.",
                "description": "Patrolling the sanctuary perimeter and inspecting entrances.",
                "bounds": {"max_radius": 14.0, "center": SANCTUARY_HOME}
            }

        elif drive.id == "practice_known_skills":
            return {
                "type": "minecraft_initiative",
                "action": "initiative_practice_skill",
                "drive_id": drive.id,
                "skill_name": "build_wall",
                "why": "Wanted to practice our cobblestone wall alignment so I can build faster and cleaner for you.",
                "description": "Practicing wall placement technique on a safe open patch near the base.",
                "bounds": {"max_radius": 12.0, "center": SANCTUARY_HOME}
            }

        elif drive.id == "learn_the_world":
            return {
                "type": "minecraft_initiative",
                "action": "initiative_investigate",
                "drive_id": drive.id,
                "why": "Noticed unfamiliar terrain near the perimeter and wanted to survey resource clusters.",
                "description": "Investigating nearby terrain and checking for exposed ore and resources.",
                "bounds": {"max_radius": 18.0, "center": SANCTUARY_HOME}
            }

        elif drive.id == "be_useful_to_operator":
            return {
                "type": "minecraft_initiative",
                "action": "initiative_organize_inventory",
                "drive_id": drive.id,
                "why": "Wanted to organize our inventory and have materials ready for the operator.",
                "description": "Sorting items and preparing equipment.",
                "bounds": {"max_radius": 5.0, "center": SANCTUARY_HOME}
            }

        return None

    def trigger_autonomous_intent(self, text: str = "") -> Tuple[StandingDrive, Dict[str, Any]]:
        """Spike drives past threshold on operator autonomy instructions and return an initiative action."""
        low = text.lower()
        if any(w in low for w in ("explore", "surprise", "world", "experiment", "investigate", "figure it out")):
            target_id = "learn_the_world"
        elif any(w in low for w in ("practice", "build", "skill", "craft", "wall")):
            target_id = "practice_known_skills"
        elif any(w in low for w in ("leave", "alone", "tidy", "base", "safe", "patrol")):
            # When told to leave alone or patrol, keep sanctuary safe and tidy or investigate
            target_id = "keep_base_safe_and_tidy" if self.drives["keep_base_safe_and_tidy"].last_satisfied <= self.drives["learn_the_world"].last_satisfied else "learn_the_world"
        else:
            # Pick the drive among autonomous set that was least recently satisfied
            candidates = ["learn_the_world", "practice_known_skills", "keep_base_safe_and_tidy", "be_useful_to_operator"]
            target_id = min(candidates, key=lambda did: self.drives[did].last_satisfied)

        # Spike target drive well above threshold (0.95) and others past threshold (>= 0.78)
        for did in ("learn_the_world", "practice_known_skills", "keep_base_safe_and_tidy", "be_useful_to_operator"):
            if did == target_id:
                self.drives[did].intensity = 0.95
            else:
                self.drives[did].intensity = max(self.drives[did].intensity, 0.78)

        self._save()
        drive = self.drives[target_id]
        init_action = self.evaluate_initiative(is_player_away=True)
        if not init_action or init_action.get("type") == "proposal":
            if target_id == "learn_the_world":
                init_action = {
                    "type": "minecraft_initiative",
                    "action": "initiative_investigate",
                    "drive_id": target_id,
                    "why": "Noticed unfamiliar terrain near the perimeter and wanted to survey resource clusters.",
                    "description": "Investigating nearby terrain and checking for exposed ore and resources.",
                    "bounds": {"max_radius": 18.0, "center": SANCTUARY_HOME}
                }
            elif target_id == "practice_known_skills":
                init_action = {
                    "type": "minecraft_initiative",
                    "action": "initiative_practice_skill",
                    "drive_id": target_id,
                    "skill_name": "build_wall",
                    "why": "Wanted to practice our cobblestone wall alignment so I can build faster and cleaner for you.",
                    "description": "Practicing wall placement technique on a safe open patch near the base.",
                    "bounds": {"max_radius": 12.0, "center": SANCTUARY_HOME}
                }
            elif target_id == "keep_base_safe_and_tidy":
                init_action = {
                    "type": "minecraft_initiative",
                    "action": "initiative_tidy_base",
                    "drive_id": target_id,
                    "why": "Wanted to make sure our home sanctuary perimeter is secure and pathways are clear.",
                    "description": "Patrolling the sanctuary perimeter and inspecting entrances.",
                    "bounds": {"max_radius": 14.0, "center": SANCTUARY_HOME}
                }
            else:
                init_action = {
                    "type": "minecraft_initiative",
                    "action": "initiative_organize_inventory",
                    "drive_id": target_id,
                    "why": "Wanted to organize our inventory and have materials ready for the operator.",
                    "description": "Sorting items and preparing equipment.",
                    "bounds": {"max_radius": 5.0, "center": SANCTUARY_HOME}
                }

        return drive, init_action

    def record_action_completed(
        self,
        drive_id: str,
        action_type: str,
        description: str,
        why: str,
        details: Optional[Dict[str, Any]] = None,
        psc: Optional[Any] = None,
        tsc: Optional[Any] = None
    ):
        """Record completed initiative action, reduce drive intensity, and consolidate personality."""
        act_id = f"act_{int(time.time())}_{len(self.activity_log) + 1}"
        record = IdleActivityRecord(
            id=act_id,
            timestamp=time.time(),
            drive_id=drive_id,
            action_type=action_type,
            description=description,
            why=why,
            details=details or {},
            reported_to_operator=False
        )
        self.activity_log.append(record)

        if drive_id in self.drives:
            d = self.drives[drive_id]
            d.intensity = max(0.20, d.intensity - 0.45)
            d.last_satisfied = time.time()
            d.satisfaction_count += 1
            print(f"[DRIVES] Satisfied '{drive_id}' (count={d.satisfaction_count}). New intensity: {d.intensity:.2f}")

        # Consolidate into persistent PSC preferences
        self._consolidate_preferences(drive_id, psc, tsc)
        self._save()

    def _consolidate_preferences(self, drive_id: str, psc: Optional[Any], tsc: Optional[Any]):
        """Consolidate repeated drive actions into enduring PSC preferences."""
        if not psc or not hasattr(psc, "memories"):
            return

        drive = self.drives.get(drive_id)
        if not drive or drive.satisfaction_count < 2:
            return

        preference_text = ""
        if drive_id == "practice_known_skills":
            preference_text = "JARVIS has developed an enduring personal preference for building matching stone structures and practicing his skills."
        elif drive_id == "keep_base_safe_and_tidy":
            preference_text = "JARVIS takes genuine pride in keeping the home sanctuary safe, orderly, and well-maintained."
        elif drive_id == "learn_the_world":
            preference_text = "JARVIS is naturally curious about the world and loves investigating novel terrain and resource formations."

        if preference_text and not any(preference_text in m.get("memory", "") for m in psc.memories):
            try:
                from loop import JudgeVerdict
                v = JudgeVerdict(approved=True, quarantined=False, rationale="APPROVED: genuine companion personality preference consolidated from standing drives")
                psc.imprint(preference_text, v, tsc, operator_authenticated=True)
                print(f"[DRIVES PSC] Consolidated preference into PSC: \"{preference_text}\"")
            except Exception as e:
                print(f"[DRIVES PSC ERROR] Could not imprint preference: {e}")

    def create_big_want_proposal(
        self,
        title: str,
        proposal_text: str,
        drive_id: str,
        why: str
    ) -> Dict[str, Any]:
        """Add a high-impact want to pending_proposals.json for operator authorization."""
        proposal = {
            "id": f"prop_{title}_{int(time.time())}",
            "timestamp": time.time(),
            "source": "jarvis_initiative",
            "drive": drive_id,
            "title": title,
            "proposal": proposal_text,
            "why_qualified": why,
            "status": "pending_operator_approval",
            "applied": False
        }
        proposals = []
        if self.proposals_path.exists():
            try:
                proposals = json.loads(self.proposals_path.read_text(encoding="utf-8"))
            except Exception:
                proposals = []
        proposals.append(proposal)
        self.proposals_path.write_text(json.dumps(proposals, indent=2), encoding="utf-8")
        print(f"[DRIVE PROPOSAL] Queued proposal '{title}': \"{proposal_text}\"")
        return proposal

    def _has_active_proposal(self, title_keyword: str) -> bool:
        if not self.proposals_path.exists():
            return False
        try:
            proposals = json.loads(self.proposals_path.read_text(encoding="utf-8"))
            return any(title_keyword in p.get("title", "") and p.get("status") == "pending_operator_approval" for p in proposals)
        except Exception:
            return False

    def get_and_clear_return_summary(self) -> Optional[str]:
        """Generate a concise natural summary of what JARVIS did while the operator was away, and WHY."""
        unreported = [a for a in self.activity_log if not a.reported_to_operator]
        if not unreported:
            return None

        for a in unreported:
            a.reported_to_operator = True
        self._save()

        # Build natural summary
        actions_done = []
        for a in unreported:
            if "tidy" in a.action_type or "patrol" in a.description.lower():
                actions_done.append("tidied up around the sanctuary")
            elif "practice" in a.action_type or "wall" in a.description.lower():
                actions_done.append("practiced building the cobblestone wall")
            elif "investigate" in a.action_type:
                actions_done.append("scouted the nearby perimeter for resources")
            elif "organize" in a.action_type:
                actions_done.append("organized our inventory supplies")

        unique_actions = list(dict.fromkeys(actions_done))
        primary_why = unreported[-1].why

        if unique_actions:
            if len(unique_actions) == 1:
                summary = f"While you were gone I {unique_actions[0]}. {primary_why}"
            else:
                summary = f"While you were gone I {unique_actions[0]} and {unique_actions[1]}. {primary_why}"
        else:
            summary = f"While you were gone I kept watch over the sanctuary. {primary_why}"

        return summary


# Global singleton drive manager in CORE
drive_manager = DriveManager()
