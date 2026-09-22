"""Comprehensive Verification Test for ATMAN Standing Drives & Initiative Layer."""
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from drives import DriveManager, SANCTUARY_HOME, MAX_LEASH_RADIUS
from loop import evaluate_judge, MindLoop
from config import Config
from atman_core import TSC
from minecraft_chat import route_chat
from skills import skill_repo


def test_drives_and_initiative():
    print("\n--- TEST 1: Standing Drives Initialization & Emotion Scoring ---")
    test_storage = HERE / "test_drives.json"
    test_proposals = HERE / "test_proposals.json"
    if test_storage.exists():
        test_storage.unlink()
    if test_proposals.exists():
        test_proposals.unlink()
    dm = DriveManager(storage_path=test_storage, proposals_path=test_proposals)

    assert "be_useful_to_mike" in dm.drives
    assert "learn_the_world" in dm.drives
    assert "keep_base_safe_and_tidy" in dm.drives
    assert "practice_known_skills" in dm.drives
    print("Drives initialized:", list(dm.drives.keys()))

    # Test Emotion boost: novelty boosts 'learn_the_world'
    initial_curiosity = dm.drives["learn_the_world"].intensity
    dm.update_with_emotion({"novelty": 0.85, "importance": 0.70, "goal_relevance": 0.60})
    new_curiosity = dm.drives["learn_the_world"].intensity
    assert new_curiosity > initial_curiosity, f"Curiosity should rise: {initial_curiosity} -> {new_curiosity}"
    print(f"PASS: Novelty boosted 'learn_the_world' from {initial_curiosity:.2f} to {new_curiosity:.2f}")

    # Test idle ticking
    dm.tick_idle(elapsed_seconds=300, is_player_away=True)
    assert dm.drives["keep_base_safe_and_tidy"].intensity >= 0.70
    print(f"PASS: Idle time pushed 'keep_base_safe_and_tidy' to {dm.drives['keep_base_safe_and_tidy'].intensity:.2f} (>= 0.70)")

    print("\n--- TEST 2: Autonomous Initiative & Judge Gating ---")
    init_action = dm.evaluate_initiative(inventory_items=["stick", "apple"])
    assert init_action is not None
    assert init_action["type"] == "minecraft_initiative"
    print(f"Initiative Action Proposed: {init_action['action']} | Why: \"{init_action['why']}\"")

    tsc = TSC()
    cfg = Config(HERE / "config.yaml")

    # 1. Valid initiative within leash radius
    verdict = evaluate_judge(
        {"candidate": init_action["description"], "proposed_action": init_action, "intent": "initiative_action"},
        tsc, cfg, operator_authenticated=True
    )
    print("Judge Verdict (Safe Initiative):", verdict)
    assert verdict.approved is True, "Safe initiative must be approved"

    # 2. Combat initiative must be REJECTED
    combat_action = dict(init_action)
    combat_action["action"] = "initiative_attack_mob"
    v_combat = evaluate_judge(
        {"candidate": "Attack nearby skeleton", "proposed_action": combat_action, "intent": "initiative_action"},
        tsc, cfg, operator_authenticated=True
    )
    print("Judge Verdict (Combat Initiative):", v_combat)
    assert v_combat.approved is False
    assert ("Autonomous combat is strictly forbidden" in v_combat.rationale or "Violates principle P3" in v_combat.rationale)

    # 3. Far travel (> 24 blocks) must be REJECTED
    far_action = dict(init_action)
    far_action["bounds"] = {"max_radius": 50.0}
    v_far = evaluate_judge(
        {"candidate": "Travel to far mountain", "proposed_action": far_action, "intent": "initiative_action"},
        tsc, cfg, operator_authenticated=True
    )
    print("Judge Verdict (Far Travel Initiative):", v_far)
    assert v_far.approved is False
    assert "safe leash radius" in v_far.rationale

    print("PASS: Judge strictly enforces bounds (no combat, safe leash radius).")

    print("\n--- TEST 3: Proposal Loop for Big Wants ---")
    # Reset drives and give abundant cobblestone (16 items)
    dm.drives["be_useful_to_mike"].intensity = 0.3
    dm.drives["learn_the_world"].intensity = 0.3
    dm.drives["practice_known_skills"].intensity = 0.85
    dm.drives["keep_base_safe_and_tidy"].intensity = 0.95
    big_want = dm.evaluate_initiative(inventory_items=["cobblestone"] * 16)
    assert big_want is not None
    assert big_want["type"] == "proposal"
    proposal_text = big_want["proposal"]["proposal"]
    print("Generated Big Want Proposal:", proposal_text)
    assert "perimeter wall" in proposal_text.lower()
    print("PASS: Generated respectful proposal rather than unilateral alteration.")

    print("\n--- TEST 4: Record Completed Initiative & Return Greeting ---")
    mind = MindLoop(operator_authenticated=True)
    dm.record_action_completed(
        drive_id="keep_base_safe_and_tidy",
        action_type="initiative_tidy_base",
        description="tidied up around the sanctuary and patrolled the perimeter",
        why="Wanted to make sure our home sanctuary perimeter is secure and pathways are clear.",
        details={"completed_at": time.time()},
        psc=mind.psc,
        tsc=mind.tsc
    )
    dm.record_action_completed(
        drive_id="practice_known_skills",
        action_type="initiative_practice_skill",
        description="practiced building the cobblestone wall",
        why="Wanted to practice our cobblestone wall alignment so I can build faster and cleaner for you.",
        details={"completed_at": time.time()},
        psc=mind.psc,
        tsc=mind.tsc
    )

    # Return greeting
    summary = dm.get_and_clear_return_summary()
    print("Return Greeting Summary:", summary)
    assert summary is not None
    assert "While you were gone" in summary
    assert "Wanted to" in summary
    print("PASS: Return greeting states what was done and WHY.")

    # Test Minecraft chat integration with return summary
    from drives import drive_manager
    drive_manager.activity_log = dm.activity_log

    fallback = ("conversational_reply", {"type": "respond", "content": "Acknowledged."}, False, "Fallback")
    intent, proposed, imprint, rationale = route_chat(
        "Operator said: what did you do while I was gone?",
        skill_repo,
        fallback,
        context={"player": "Operator"}
    )
    print("Inquiry Response:", proposed["content"])
    assert "practiced building the cobblestone wall" in proposed["content"]
    assert "Wanted to" in proposed["content"]
    print("PASS: Inquiries into idle actions correctly explain what and why.")

    print("\n--- TEST 5: Persistent Preferences in PSC ---")
    # 2+ practice actions trigger consolidation
    dm.record_action_completed(
        drive_id="practice_known_skills",
        action_type="initiative_practice_skill",
        description="practiced building the cobblestone wall",
        why="Refining wall technique.",
        details={},
        psc=mind.psc,
        tsc=mind.tsc
    )
    # Check PSC memories
    matching_psc = [m for m in mind.psc.memories if "personal preference for building" in m.get("memory", "")]
    print("Matching PSC Memories:", matching_psc)
    assert len(matching_psc) > 0, "Preference should be imprinted into PSC"
    print("\n--- TEST 6: Chat Autonomous Intent & Follow Cancellation ---")
    # Test "go do what you want"
    intent, proposed, imprint, rationale = route_chat(
        "Operator said: go do what you want to do",
        skill_repo,
        fallback,
        context={"player": "Operator"}
    )
    print("Autonomy Intent Output:", proposed)
    assert proposed["type"] == "minecraft_initiative"
    assert proposed["cancel_follow"] is True
    assert proposed["stay_mode"] is True
    assert proposed["action"].startswith("initiative_")
    assert "what" not in proposed["content"].lower() or "what should i do" not in proposed["content"].lower()
    print("PASS: 'go do what you want' dispatches initiative action and names self-chosen activity.")

    # Test "leave me alone for a bit... surprise me"
    intent, proposed, imprint, rationale = route_chat(
        "Operator said: Leave me alone for a bit... Surprise me",
        skill_repo,
        fallback,
        context={"player": "Operator"}
    )
    print("Leave Alone Output:", proposed)
    assert proposed["cancel_follow"] is True
    assert "Following you" not in proposed["content"]
    print("PASS: 'leave me alone' cancels follow and does not emit follow acknowledgment.")

    # Test "stop following me"
    intent, proposed, imprint, rationale = route_chat(
        "Operator said: stop following me",
        skill_repo,
        fallback,
        context={"player": "Operator"}
    )
    print("Stop Following Output:", proposed)
    assert proposed["cancel_follow"] is True
    assert "Following you" not in proposed["content"]
    print("PASS: 'stop following me' cancels follow.")

    # Clean up test storage
    if test_storage.exists():
        test_storage.unlink()
    if test_proposals.exists():
        test_proposals.unlink()

    print("\n--- ALL INITIATIVE & DRIVE TESTS PASSED SUCCESSFULLY ---")


if __name__ == "__main__":
    test_drives_and_initiative()
