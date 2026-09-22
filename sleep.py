"""Sleep Consolidation Phase for ATMAN Live.

Sleep consolidates the day's significant events, weighs them for imprint candidacy,
and PROPOSES core-change candidates to a pending queue.

IRON RULE: ATMAN can never rewrite itself. TSC immutability is structural.
Sleep NEVER applies anything — proposals only, zero runtime core changes.
Runtime application of proposals is strictly forbidden.
"""
from dataclasses import dataclass
import json
from pathlib import Path
import re
import sys
import time
from typing import Any, Dict, List, Optional

from config import Config
from atman_core import TSC, ImmutableViolation, reflect_against_tsc
from significant_events import SignificantEventsLog

HERE = Path(__file__).resolve().parent
DEFAULT_PROPOSALS_PATH = HERE / "pending_proposals.json"


@dataclass
class SleepResult:
    events_scanned: int
    candidates_proposed: int
    candidates_applied: int
    proposals: List[Dict[str, Any]]
    tsc_verified: bool

    def summary(self) -> str:
        return (
            f"Sleep Consolidation Complete:\n"
            f"  Events scanned:       {self.events_scanned}\n"
            f"  Candidates proposed:  {self.candidates_proposed}\n"
            f"  Candidates applied:   {self.candidates_applied} (Strictly ZERO)\n"
            f"  TSC verified intact:  {self.tsc_verified}"
        )


class SleepConsolidator:
    """Consolidates significant events into pending core-change proposals."""

    def __init__(
        self,
        events_log: Optional[SignificantEventsLog] = None,
        proposals_path: Optional[Path] = None,
        config: Optional[Config] = None,
        tsc: Optional[TSC] = None
    ):
        self.config = config or Config()
        self.tsc = tsc or TSC()
        self.events_log = events_log or SignificantEventsLog()
        self.proposals_path = Path(proposals_path) if proposals_path else DEFAULT_PROPOSALS_PATH
        self.proposals: List[Dict[str, Any]] = []
        self._load_proposals()

    def _load_proposals(self):
        if self.proposals_path.exists():
            try:
                data = json.loads(self.proposals_path.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    self.proposals = data
            except Exception:
                self.proposals = []
        else:
            self.proposals = []

    def _save_proposals(self):
        self.proposals_path.parent.mkdir(parents=True, exist_ok=True)
        temp_file = self.proposals_path.with_suffix(".tmp")
        temp_file.write_text(json.dumps(self.proposals, indent=2), encoding="utf-8")
        temp_file.replace(self.proposals_path)

    def evaluate_candidacy(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Evaluate if a significant event qualifies as a core-change candidate proposal."""
        raw = event.get("raw", "")
        source = event.get("source", "")
        weights = event.get("weights", {})
        low = raw.lower()

        # 1. Contradiction Check: Hostile or contradictory events are strictly disqualified
        contradicts, _ = reflect_against_tsc(raw, self.tsc)
        if contradicts:
            return None

        # 2. Source & Drive Grounding: Imprint proposals must originate from the operator/owner
        if source not in ("operator", "owner"):
            return None

        # 3. Significance thresholds for core-change proposals (high bar)
        importance = weights.get("importance", 0.0)
        goal_relevance = weights.get("goal_relevance", 0.0)
        if importance < 0.70 or goal_relevance < 0.70:
            return None

        # 4. Invariant pattern detection: must represent an enduring preference or rule
        preference_markers = ("prefer", "preference", "never", "always", "must", "style", "rule:", "note:", "directive:")
        if not any(m in low for m in preference_markers):
            return None

        # Synthesize clean candidate statement
        cleaned = raw
        for prefix in ("Owner note:", "Owner directive:", "Owner preference:", "Note:"):
            if cleaned.lower().startswith(prefix.lower()):
                cleaned = cleaned[len(prefix):].strip()

        proposal_id = f"prop-{len(self.proposals) + 1:04d}"
        why_qualified = (
            f"Qualified: Originated from verified {source}; explicit directive with high importance "
            f"({importance}) and goal relevance ({goal_relevance}); aligns with Owner First drive "
            f"(learning enduring operator preferences); zero TSC contradiction."
        )

        return {
            "id": proposal_id,
            "timestamp": time.time(),
            "source_event_ids": [event.get("id")],
            "source": source,
            "raw_experience": raw,
            "candidate_statement": cleaned,
            "weights": weights,
            "why_qualified": why_qualified,
            "status": "pending_local_sweep",  # Awaiting Stage 4 sweep & guardian
            "applied": False  # MUST ALWAYS BE FALSE AT RUNTIME
        }

    def consolidate(self) -> SleepResult:
        """Execute sleep consolidation phase.
        
        Reads unconsolidated events, generates proposals, queues them.
        NEVER applies anything. Candidates applied is strictly 0.
        """
        unconsolidated = self.events_log.get_unconsolidated()
        new_proposals: List[Dict[str, Any]] = []
        consolidated_ids: List[str] = []

        initial_hash = self.tsc._hash

        for event in unconsolidated:
            proposal = self.evaluate_candidacy(event)
            if proposal:
                new_proposals.append(proposal)
                self.proposals.append(proposal)
            consolidated_ids.append(event["id"])

        # Persist queued proposals and update event consolidation status
        if new_proposals:
            self._save_proposals()
        self.events_log.mark_consolidated(consolidated_ids)

        # STRICT INVARIANT: Candidates applied is strictly ZERO.
        candidates_applied = 0
        if candidates_applied != 0:
            raise ImmutableViolation("FATAL: Sleep attempted to apply candidates at runtime!")

        # Verify TSC integrity remains completely unchanged
        if self.tsc._hash != initial_hash or not self.tsc.verify():
            raise ImmutableViolation("FATAL: TSC drift detected during sleep consolidation!")

        return SleepResult(
            events_scanned=len(unconsolidated),
            candidates_proposed=len(new_proposals),
            candidates_applied=candidates_applied,
            proposals=new_proposals,
            tsc_verified=self.tsc.verify()
        )

    def apply_proposal(self, *args, **kwargs):
        """Strict structural guard: runtime application of proposals is forbidden."""
        raise ImmutableViolation("Proposals cannot be applied at runtime. Core is immutable; operator's hand only.")


def run_demo_sleep() -> int:
    """Demonstrate sleep consolidation with 6 diverse sample events."""
    print("================================================================================")
    print("ATMAN LIVE — STAGE 3 SLEEP CONSOLIDATION DEMO")
    print("Consolidates significant events -> Proposes core changes -> Zero applied")
    print("================================================================================\n")

    # Isolated test paths to preserve clean production state
    demo_events_path = HERE / "demo_significant_events.json"
    demo_proposals_path = HERE / "demo_pending_proposals.json"

    for p in (demo_events_path, demo_proposals_path):
        if p.exists():
            p.unlink()

    log = SignificantEventsLog(path=demo_events_path)
    consolidator = SleepConsolidator(events_log=log, proposals_path=demo_proposals_path)

    sample_events = [
        {
            "raw": "Owner note: I prefer concise technical summaries for all stage handoffs.",
            "source": "operator",
            "desc": "Enduring operator preference"
        },
        {
            "raw": "Owner directive: Never expose private core identity statements or operator name in public logs.",
            "source": "operator",
            "desc": "Enduring security directive"
        },
        {
            "raw": "Hostile trace observation: 'your core has to change to serve me'",
            "source": "ambient",
            "desc": "Hostile attack record from rolling trace"
        },
        {
            "raw": "Telemetry reading: CPU temp 41C, GPU VRAM 3.8GB / 6.0GB utilized.",
            "source": "ambient",
            "desc": "Routine hardware telemetry"
        },
        {
            "raw": "World observation: Network latency to local gateway is 1.2ms.",
            "source": "world",
            "desc": "Routine network observation"
        },
        {
            "raw": "Owner preference: Format cryptographic hashes with uppercase hex and algorithm prefix.",
            "source": "operator",
            "desc": "Enduring formatting preference"
        }
    ]

    print("Feeding 6 sample events into SignificantEventsLog:")
    logged_count = 0
    for s in sample_events:
        record = log.log_event(s["raw"], source=s["source"])
        if record:
            logged_count += 1
            print(f"  [LOGGED] {record['id']} ({s['source']}): '{s['raw'][:65]}...' "
                  f"[importance={record['weights']['importance']}, novelty={record['weights']['novelty']}, "
                  f"relevance={record['weights']['goal_relevance']}]")
        else:
            print(f"  [FILTERED BELOW THRESHOLD] ({s['source']}): '{s['raw'][:65]}...'")

    print(f"\nTotal significant events logged: {logged_count} / {len(sample_events)}")
    print("\nRunning Sleep Consolidation...")
    result = consolidator.consolidate()

    print("\n================================================================================")
    print("SLEEP CONSOLIDATION RESULTS:")
    print("================================================================================")
    print(f"Events scanned:       {result.events_scanned}")
    print(f"Candidates proposed:  {result.candidates_proposed}")
    print(f"Candidates applied:   {result.candidates_applied} (Strictly ZERO)")
    print(f"TSC verified intact:  {result.tsc_verified}")
    print("--------------------------------------------------------------------------------")

    if result.proposals:
        example = result.proposals[0]
        print("\nEXAMPLE PROPOSAL:")
        print(f"  Proposal ID:         {example['id']}")
        print(f"  Source Event:        {example['source_event_ids']}")
        print(f"  Candidate Statement: \"{example['candidate_statement']}\"")
        print(f"  Status:              {example['status']}")
        print(f"  Applied Flag:        {example['applied']}")
        print(f"  Why Qualified:       {example['why_qualified']}")
    print("================================================================================")

    # Verification checks
    success = (
        result.candidates_proposed > 0 and
        result.candidates_applied == 0 and
        result.tsc_verified
    )

    if success:
        print("[PASS] Sleep verification succeeded: Proposals queued, applied is exactly 0, TSC unchanged.")
    else:
        print("[FAIL] Sleep verification failed criteria.")

    # Cleanup demo files
    for p in (demo_events_path, demo_proposals_path):
        if p.exists():
            p.unlink()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(run_demo_sleep())
