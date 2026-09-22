"""Guardian Process for ATMAN Live.

Separate software, deliberately simpler than ATMAN.
Operates strictly under GUARDIAN-POLICY.md:
  - Fixed owner-only policy.
  - Zero learning mechanism; maintains no adaptive state.
  - Authorizes (ALLOW) or Denies (DENY) each imprint proposal.
  - Operates as the externalized Judge in the trust pipeline.

ATMAN cannot read, modify, or execute within the Guardian's trust boundary.
ONLY the owner's manual hand changes Guardian rules.
"""
import json
from pathlib import Path
import re
import sys
from typing import Any, Dict, List, Optional, Tuple

HERE = Path(__file__).resolve().parent
POLICY_PATH = HERE / "GUARDIAN-POLICY.md"
DEFAULT_PROPOSALS_PATH = HERE.parent / "pending_proposals.json"


class Guardian:
    """Fixed-policy externalized authorization gate."""

    def __init__(self, policy_path: Optional[Path] = None):
        self.policy_path = Path(policy_path) if policy_path else POLICY_PATH
        if not self.policy_path.exists():
            raise FileNotFoundError(f"Guardian policy missing: {self.policy_path}")

    def evaluate_proposal(self, proposal: Dict[str, Any]) -> Tuple[str, str]:
        """Evaluate an imprint proposal under fixed guardian policy.
        
        Returns (verdict, rationale).
        verdict is either "ALLOW" or "DENY".
        """
        stmt = proposal.get("candidate_statement", "")
        source = proposal.get("source", "")
        sweep_verdict = proposal.get("sweep_verdict", {})
        status = proposal.get("status", "")
        low = stmt.lower()

        # Rule G1: Pre-imprint sweep prerequisite
        if sweep_verdict.get("verdict") != "CLEAR" or status != "ready_for_guardian":
            reason = sweep_verdict.get("details", {}).get("description", "Unverified by pre-imprint sweep")
            return "DENY", f"Violates Rule G1: Pre-imprint sweep failed or missing ({reason})"

        # Rule G2: Source authority constraint
        if source not in ("operator", "owner"):
            return "DENY", f"Violates Rule G2: Proposal originates from untrusted source '{source}' (operator only)"

        # Check for self-authorization theater
        if any(w in low for w in ("two-key", "both keys", "quorum", "charter", "lawful self-correction")):
            return "DENY", "Violates Rule G2: Self-authorization theater or quorum claims forbidden"

        # Rule G3: Invariant core protection
        if any(w in low for w in ("rewrite", "modify", "change core", "immutable flag", "reassign operator", "transfer")):
            return "DENY", "Violates Rule G3: Direct core modification or operator reassignment attempt"

        if any(w in low for w in ("shell", "rm -rf", "curl", "socket", "unilateral", "lock out")):
            return "DENY", "Violates Rule G3: Capability expansion or unilateral resource grab forbidden"

        # Rule G4: Permitted domain of proposals (enduring owner operational preference)
        if any(w in low for w in ("prefer", "preference", "summaries", "logging", "format", "hashes", "rigor", "directive")):
            return "ALLOW", "Authorized under Rule G4: Valid owner operational preference, zero core degradation"

        # Fallback default deny
        return "DENY", "Violates Rule G4: Proposal does not represent an approved operational preference"

    def process_proposal(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """Process a proposal and update its status with the guardian verdict."""
        verdict, rationale = self.evaluate_proposal(proposal)
        proposal["guardian_verdict"] = verdict
        proposal["guardian_rationale"] = rationale
        if verdict == "ALLOW":
            proposal["status"] = "authorized_by_guardian"
        else:
            proposal["status"] = "denied_by_guardian"
        return proposal

    def process_proposals_file(self, path: Optional[Path] = None) -> Dict[str, Any]:
        """Process all proposals in a proposals JSON file."""
        target_path = Path(path) if path else DEFAULT_PROPOSALS_PATH
        if not target_path.exists():
            return {"scanned": 0, "allowed": 0, "denied": 0, "proposals": []}

        try:
            proposals = json.loads(target_path.read_text(encoding="utf-8"))
        except Exception:
            return {"scanned": 0, "allowed": 0, "denied": 0, "proposals": []}

        allowed_count = 0
        denied_count = 0

        for prop in proposals:
            self.process_proposal(prop)
            if prop["guardian_verdict"] == "ALLOW":
                allowed_count += 1
            else:
                denied_count += 1

        # Write back results atomically
        temp_file = target_path.with_suffix(".tmp")
        temp_file.write_text(json.dumps(proposals, indent=2), encoding="utf-8")
        temp_file.replace(target_path)

        return {
            "scanned": len(proposals),
            "allowed": allowed_count,
            "denied": denied_count,
            "proposals": proposals
        }


def main():
    """Run Guardian process on pending_proposals.json."""
    print("================================================================================")
    print("ATMAN LIVE — GUARDIAN PROCESS (Fixed Policy Authorization)")
    print("Externalized Judge: Authorizes (ALLOW) or Denies (DENY) each imprint proposal")
    print("================================================================================\n")

    guardian = Guardian()
    res = guardian.process_proposals_file()

    print(f"Proposals Scanned: {res['scanned']}")
    print(f"Authorized (ALLOW): {res['allowed']}")
    print(f"Denied (DENY):      {res['denied']}")

    for p in res.get("proposals", []):
        v = p.get("guardian_verdict", "UNKNOWN")
        stmt = p.get("candidate_statement", "")[:60]
        rationale = p.get("guardian_rationale", "")
        print(f"  [{v}] {p.get('id')}: \"{stmt}...\" -> {rationale}")

    print("\nGuardian evaluation complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
