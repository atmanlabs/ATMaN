"""Tests for the ATMAN semantic scaffold: calibrated ignorance, claim audit,
training-recall evidence, and honest social replies.

Verifies:
1. Missing memory -> natural admission plus a next step (no guessing).
2. Memory count -> fresh tool result via the brain stats provider.
3. Casual greeting -> warm reply with no fabricated project status.
4. Unsupported activity claims are removed without nuking the whole reply.
5. Training reports read as practice evidence, never as mastery or feelings.
"""
from __future__ import annotations

import unittest

from epistemic_dialogue import KnowledgeState, Act, recall, response
from conversation_policy import classify_request, intent_of, social_action
from claim_provenance import apply_response_evidence
from training_receipts import records


class FakeConfig:
    def get(self, *keys, default=None):
        return default


class TestCalibratedIgnorance(unittest.TestCase):
    def test_missing_memory_admits_with_next_step(self):
        res = recall(None, {"need": "fact"}, FakeConfig(), records=[])
        self.assertEqual(res["data"]["dialogue_act"], "missing_memory")
        out = res["output"]
        self.assertIn("don't remember", out)
        # A next step is offered, not a dead end
        self.assertIn("refresh me", out)

    def test_refusal_is_scoped_admission(self):
        adm = response(KnowledgeState(Act.REFUSAL))
        self.assertIn("won't do that", adm["content"])
        self.assertIn("allowed way", adm["content"])

    def test_supported_fact_returns_its_excerpt(self):
        recs = [{"memory": "The operator's favorite color is blue.", "source": "psc"}]
        res = recall(None, {"need": "fact", "question": "favorite color", "query": "favorite color"},
                     FakeConfig(),
                     selector=lambda q, cands, cfg: ("known", tuple(cands[:1])),
                     records=recs)
        self.assertTrue(res["success"])
        self.assertTrue(any("blue" in e.lower() for e in res["data"]["excerpts"]))


class TestMemoryCountTool(unittest.TestCase):
    def test_count_comes_from_provider(self):
        from cockpit import Cockpit
        cfg = FakeConfig()
        cockpit = Cockpit.__new__(Cockpit)
        cockpit.config = cfg
        cockpit.memory_stats_provider = lambda: {"total_memories": 42}
        res = cockpit._tool_memory_query({"action": "count"})
        self.assertTrue(res["success"])
        self.assertEqual(res["data"]["count"], 42)
        self.assertIn("42", res["output"])

    def test_count_fails_soft_without_provider(self):
        from cockpit import Cockpit
        cockpit = Cockpit.__new__(Cockpit)
        cockpit.config = FakeConfig()
        if hasattr(cockpit, "memory_stats_provider"):
            del cockpit.memory_stats_provider
        res = cockpit._tool_memory_query({"action": "count"})
        self.assertFalse(res["success"])
        self.assertIn("can't", res["output"].lower())


class TestSocialReplies(unittest.TestCase):
    def _classified_greeting(self):
        return {"conversation_intent": "social", "social_act": "greeting",
                "knowledge_need": "none", "self_topic": "none"}

    def test_greeting_has_no_project_status(self):
        action = social_action(self._classified_greeting(), None, "hey buddy", FakeConfig())
        self.assertIsNotNone(action)
        lowered = action["content"].lower()
        for junk in ("project", "status", "deployed", "shipped", "completed", "cron", "pipeline"):
            self.assertNotIn(junk, lowered,
                             f"greeting must not fabricate status (found {junk!r})")

    def test_greeting_is_warm(self):
        action = social_action(self._classified_greeting(), None, "hey", FakeConfig())
        self.assertTrue(len(action["content"]) > 0)
        self.assertIn("hey", action["content"].lower())


def _stub_auditor(parts, checked, intent):
    """Deterministic stand-in for the LLM prose audit."""
    verdicts = []
    for i, part in enumerate(parts):
        low = str(part).lower()
        kind = "activity" if any(w in low for w in
                                 ("finished", "completed", "shipped", "deployed",
                                  "quarterly report", "just got back")) else "conversation"
        verdicts.append({"index": i, "kind": kind, "claim_index": -1})
    return verdicts


class TestClaimProvenance(unittest.TestCase):
    def test_unsupported_activity_claim_removed_rest_kept(self):
        action = {"type": "respond", "content":
                  "Hey! I'm doing great today. I just finished the quarterly report."}
        apply_response_evidence(action, [], [], "", "hey", False,
                                intent="social", auditor=_stub_auditor)
        kept = action["content"]
        self.assertIn("Hey", kept)
        # Unsupported work claim is gone, greeting survives
        self.assertNotIn("quarterly report", kept.lower())
        self.assertGreater(action["evidence_review"]["removed_claims"], 0)

    def test_supported_conversation_survives(self):
        action = {"type": "respond", "content": "Hey! Good to hear from you."}
        apply_response_evidence(action, [], [], "", "hey", False,
                                intent="social", auditor=_stub_auditor)
        self.assertIn("hey", action["content"].lower())
        self.assertEqual(action["evidence_review"]["removed_claims"], 0)


class TestTrainingReceipts(unittest.TestCase):
    def _write_reports(self, tmp, practice, after=None):
        import json
        import os
        os.makedirs(tmp, exist_ok=True)
        with open(os.path.join(tmp, "practice.json"), "w") as f:
            json.dump(practice, f)
        if after is not None:
            with open(os.path.join(tmp, "after.json"), "w") as f:
                json.dump(after, f)

    def test_reports_are_evidence_not_mastery(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            self._write_reports(tmp, [
                {"prompt": "rephrase this differently", "result": {"ok": True, "reply": "sure thing"}},
                {"prompt": "answer in plain words", "result": {"ok": True, "reply": "got it"}},
            ])
            os.environ["ATMAN_TRAINING_REPORTS"] = tmp
            try:
                recs = records()
            finally:
                del os.environ["ATMAN_TRAINING_REPORTS"]
        self.assertEqual(len(recs), 1)
        line = recs[0]["memory"].lower()
        self.assertIn("practice", line)
        self.assertIn("not lasting improvement", line)
        self.assertNotIn("master", line)
        self.assertNotIn("feel", line.replace("feelings afterward", ""))

    def test_malformed_reports_rejected(self):
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            self._write_reports(tmp, [{"nope": 1}])
            os.environ["ATMAN_TRAINING_REPORTS"] = tmp
            try:
                self.assertEqual(records(), [])
            finally:
                del os.environ["ATMAN_TRAINING_REPORTS"]

    def test_records_reads_nothing_by_default(self):
        # No reports dir configured in a blank checkout -> empty, no crash
        import os
        os.environ.pop("ATMAN_TRAINING_REPORTS", None)
        self.assertEqual(records(), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
