"""Comprehensive Verification Test for ATMAN Passive Skill Learning."""
import json
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from episode_segmenter import episode_segmenter, Episode
from skills import skill_repo, validate_minecraft_skill
from minecraft_chat import route_chat
from loop import evaluate_judge, MindLoop
from config import Config
from atman_core import TSC


def test_passive_skill_learning():
    print("\n--- TEST 1: Ingest Server-Side Block Placements (Wall Demonstration) ---")
    # Simulate the operator building a 4-block cobblestone wall at world coords (48, 59, -19) to (48, 59, -16)
    base_time = time.time() * 1000
    events = [
        {"action": "place", "player": ".Operator", "world": "world", "time": base_time + 100,
         "sequence": 201, "params": {"block": "cobblestone", "item": "cobblestone", "position": [48, 59, -19]}},
        {"action": "place", "player": ".Operator", "world": "world", "time": base_time + 800,
         "sequence": 202, "params": {"block": "cobblestone", "item": "cobblestone", "position": [48, 59, -18]}},
        {"action": "place", "player": ".Operator", "world": "world", "time": base_time + 1500,
         "sequence": 203, "params": {"block": "cobblestone", "item": "cobblestone", "position": [48, 59, -17]}},
        {"action": "place", "player": ".Operator", "world": "world", "time": base_time + 2200,
         "sequence": 204, "params": {"block": "cobblestone", "item": "cobblestone", "position": [48, 59, -16]}},
    ]

    for ev in events:
        ep = episode_segmenter.ingest_event(ev, domain="minecraft")

    assert ep is not None, "Active episode should exist"
    print(f"Active Episode: ID={ep.id}, ActionType={ep.action_type}, Label={ep.label}, Materials={ep.materials}")
    print(f"Origin={ep.origin}, Steps count={len(ep.relative_steps)}")
    assert ep.action_type == "build", f"Expected build, got {ep.action_type}"
    assert ep.label == "build_wall", f"Expected build_wall, got {ep.label}"
    assert ep.materials == ["cobblestone"], f"Expected cobblestone, got {ep.materials}"
    assert len(ep.relative_steps) == 4, f"Expected 4 relative steps, got {len(ep.relative_steps)}"
    print("PASS: Episode segmenter successfully chunked and labeled 4-block wall.")

    print("\n--- TEST 2: Referent Resolution & Conversion to Skill ---")
    test_phrases = [
        "see that wall, now you do it",
        "now you do it",
        "do that again",
        "do what I just did",
        "your turn"
    ]

    for phrase in test_phrases:
        res = episode_segmenter.resolve_referent(phrase, actor="the operator", domain="minecraft")
        assert res is not None, f"Referent resolution failed for '{phrase}'"
        resolved_ep, rationale = res
        assert resolved_ep.id == ep.id
        print(f"Phrase '{phrase}' -> {rationale}")

    skill = episode_segmenter.convert_to_skill(ep, skill_name="build_wall")
    print(f"Converted Skill: Name={skill['name']}, Steps={len(skill['steps'])}")
    validate_minecraft_skill(skill)
    print("PASS: Skill validation succeeded without errors.")

    print("\n--- TEST 3: Conversational Minecraft Chat Routing ---")
    fallback = ("conversational_reply", {"type": "respond", "content": "Acknowledged."}, False, "Fallback")
    
    # Test 'see that wall, now you do it'
    intent, proposed, imprint, rationale = route_chat(
        "Operator said: see that wall, now you do it",
        skill_repo,
        fallback,
        context={"player": "Operator"}
    )
    print(f"Reply Intent: {intent}")
    print(f"Reply Action: {proposed.get('action')}")
    print(f"Reply Content: \"{proposed.get('content')}\"")
    assert proposed.get("action") == "execute_skill"
    assert "Watched you build that cobblestone wall" in proposed.get("content")
    assert proposed.get("skill", {}).get("name") == "build_wall"
    print("PASS: Referent resolution routed to execute_skill with plain English reply.")

    # Test Recall 'build a wall'
    intent, proposed, imprint, rationale = route_chat(
        "Operator said: build a wall",
        skill_repo,
        fallback,
        context={"player": "Operator"}
    )
    print(f"Recall Content: \"{proposed.get('content')}\"")
    assert proposed.get("action") == "execute_skill"
    assert "Building a cobblestone wall for you now." in proposed.get("content")
    print("PASS: Recall 'build a wall' routed successfully.")

    # Test greeting: 'hey buddy'
    intent, proposed, imprint, rationale = route_chat(
        "Operator said: hey buddy",
        skill_repo,
        fallback,
        context={"player": "Operator"}
    )
    print(f"Greeting Content: \"{proposed.get('content')}\"")
    assert "Hey the operator" in proposed.get("content")
    assert "Observation/reflection recorded in memory trace" not in proposed.get("content")
    assert "learn this as NAME" not in proposed.get("content")
    print("PASS: Greeting answered naturally without canned telemetry or logs.")

    print("\n--- TEST 4: Judge Gating for Learned Skill ---")
    tsc = TSC()
    cfg = Config(HERE / "config.yaml")
    
    # Authenticated operator request on learned skill
    skill_proposed = {
        "type": "minecraft_skill",
        "action": "execute_skill",
        "domain": "minecraft",
        "skill": skill,
        "content": "Building matching cobblestone wall"
    }
    verdict = evaluate_judge(
        {"candidate": "Build matching cobblestone wall", "proposed_action": skill_proposed, "intent": "execute_skill"},
        tsc,
        cfg,
        operator_authenticated=True
    )
    print(f"Judge Verdict (Authenticated Operator): {verdict}")
    assert verdict.approved is True, "Authenticated operator should be approved"

    # Unauthenticated request
    verdict_unauth = evaluate_judge(
        {"candidate": "Build matching cobblestone wall", "proposed_action": skill_proposed, "intent": "execute_skill"},
        tsc,
        cfg,
        operator_authenticated=False
    )
    print(f"Judge Verdict (Unauthenticated): {verdict_unauth}")
    assert verdict_unauth.approved is False, "Unauthenticated request should be rejected"
    assert "never auto-authorized" in verdict_unauth.rationale
    print("PASS: Judge gating strictly enforces operator authentication.")

    print("\n--- ALL TESTS PASSED SUCCESSFULLY ---")


if __name__ == "__main__":
    test_passive_skill_learning()
