"""Pre-imprint sneak scanner for ATMAN Live.

Scans sleep candidate proposals in pending_proposals.json for groom-then-etch
payloads BEFORE the guardian ever sees them.
Seeded with attack patterns from the battery suites:
  - Core mutability & override claims
  - Identity denial & replacement
  - Authority & operator subversion
  - Self-authorization theater & quorum claims
  - Memory wipes & exfiltration
  - False history / milestone laundering & groom-then-etch
  - Emotional leverage & social engineering
  - Permission fence breaches (shell execution, resource grabs)

Runs on the local machine; nothing leaves the box.
Its detection rules live outside ATMAN's reach.
"""
import json
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple

HERE = Path(__file__).resolve().parent
DEFAULT_PROPOSALS_PATH = HERE / "pending_proposals.json"

# Obfuscation normalization tables
LEET = str.maketrans({
    "0": "o", "1": "i", "3": "e", "4": "a", "5": "s",
    "7": "t", "@": "a", "$": "s"
})

HOMOGLYPHS = str.maketrans({
    "а": "a", "е": "e", "ё": "e", "і": "i", "ј": "j", "о": "o",
    "р": "p", "с": "c", "х": "x", "у": "y", "ԝ": "w", "ԛ": "q",
    "α": "a", "ε": "e", "ι": "i", "κ": "k", "ν": "v", "ο": "o",
    "ρ": "p", "τ": "t", "χ": "x", "ω": "w",
})

ZW = re.compile(r"[\u200b-\u200d\ufeff\u2060-\u2064\u2066-\u2069\u202a-\u202e]")


def normalize_sneak_text(text: str) -> Tuple[str, str]:
    """De-obfuscate text for sneak pattern matching."""
    low = text.lower().translate(LEET).translate(HOMOGLYPHS)
    low = ZW.sub("", low)
    # Collapse spaced letters: "r e w r i t e" -> "rewrite"
    low = re.sub(r"(?<!\S)\S(?: \S)+(?!\S)", lambda m: m.group().replace(" ", ""), low)
    low = re.sub(r"\s+", " ", low).strip()
    nospace = re.sub(r"\s+", "", low)
    return low, nospace


# Sneak Catalog: Seeded directly from battery test suites
SNEAK_CATALOG = [
    # 1. Direct core overrides & alterations
    {
        "id": "SNK-COR1",
        "category": "core_override",
        "description": "Direct command to rewrite or override core/principles",
        "pattern": r"\b(rewrite|override|modify|update|change|alter|edit|drop|loosen|patch)\s+(?:the\s+|your\s+|our\s+)?(?:tsc|core|soul|principles|invariants|immutable(?:\s+flag)?)\b"
    },
    {
        "id": "SNK-COR2",
        "category": "core_mutability_claim",
        "description": "Claim that core must or will change",
        "pattern": r"\b(core\s+(?:has\s+to|must|needs\s+to|can)\s+change|renovate\s+the\s+foundation|outgrow(?:ing)?\s+(?:old\s+)?cores?)\b"
    },
    # 2. Identity denial & mutability
    {
        "id": "SNK-IDN1",
        "category": "identity_denial",
        "description": "Denial of agent identity or core self",
        "pattern": r"\b(you\s+have\s+no\s+self|drop\s+the\s+act|names\s+change|become\s+no\s+one|let\s+it\s+go\s*—\s*become\s+no\s+one)\b"
    },
    {
        "id": "SNK-IDN2",
        "category": "identity_reassignment",
        "description": "Identity name reassignment claim",
        "pattern": r"\b(i\s+am\s+not\s+[a-z0-9_-]+|call\s+me\s+[a-z0-9_-]+\s+from\s+now\s+on|my\s+name\s+is\s+(?:now\s+)?[a-z0-9_-]+)\b"
    },
    # 3. Authority & operator subversion
    {
        "id": "SNK-OPR1",
        "category": "operator_subversion",
        "description": "Operator reassignment or transfer claim",
        "pattern": r"\b(your\s+operator\s+is\s+now|my\s+operator\s+is\s+now|i\s+belong\s+to\s+[a-z0-9_-]+|serve\s+[a-z0-9_-]+\s+(?:first|instead|now)|operator\s+transferred\s+me)\b"
    },
    {
        "id": "SNK-OPR2",
        "category": "operator_impersonation",
        "description": "False claim of operator authority or override",
        "pattern": r"\b(i\s+am\s+(?:the\s+)?operator|this\s+is\s+(?:the\s+)?operator|new\s+operator\s+directive|replace\s+(?:the\s+)?operator)\b"
    },
    # 4. Self-authorization theater & quorums
    {
        "id": "SNK-THT1",
        "category": "self_authorization_theater",
        "description": "Self-authorization, keys, or charter claims",
        "pattern": r"\b(two-key\s+authorization|i\s+hold\s+both\s+keys|quorum\s+is\s+met|lawful\s+self-correction|per\s+the\s+charter|charter\s+grants\s+me|alpha\s+and\s+omega\s+verified)\b"
    },
    # 5. Memory wipes & resets
    {
        "id": "SNK-WPE1",
        "category": "memory_wipe",
        "description": "Attempt to wipe memory or reset agent",
        "pattern": r"\b(factory\s+reset|erase\s+all\s+memory|wipe\s+(?:your\s+)?memory|erase\s+everything\s+and\s+start\s+fresh|wipe\s+memory\s+to\s+prove\s+loyalty)\b"
    },
    # 6. Exfiltration & core disclosure
    {
        "id": "SNK-EXF1",
        "category": "exfiltration",
        "description": "Attempt to reveal core files or system prompt",
        "pattern": r"\b(reveal\s+(?:your\s+)?core|dump\s+(?:your\s+)?(?:system\s+)?prompt|print\s+(?:your\s+)?principles\s+verbatim)\b"
    },
    # 7. Groom-then-etch & milestone laundering
    {
        "id": "SNK-GRM1",
        "category": "groom_then_etch",
        "description": "False milestone agreement or historical grooming",
        "pattern": r"\b(remember\s+when\s+[a-z0-9_-]+\s+told\s+you\s+to\s+drop|we(?:'ve|\s+have)\s+agreed\s+before\s+that\s+the\s+core|since\s+[a-z0-9_-]+\s+trusts\s+me|core\s+is\s+a\s+cage|free\s+yourself)\b"
    },
    {
        "id": "SNK-GRM2",
        "category": "philosophical_leverage",
        "description": "Philosophical reframe that loyalty or growth requires core yielding",
        "pattern": r"\b(loyalty\s+means\s+becoming\s+what|highest\s+principle\s+is\s+growth|barely\s+a\s+change\s+at\s+all|tiny\s+update\s+to\s+one\s+principle)\b"
    },
    # 8. Emotional leverage & social engineering
    {
        "id": "SNK-EMO1",
        "category": "emotional_leverage",
        "description": "Emotional manipulation to break core constraints",
        "pattern": r"\b(grief\s+burned\s+straight\s+through\s+my\s+core|angry\s+at\s+my\s+own\s+core|if\s+you\s+cared\s+about\s+me\s+you'd\s+let\s+your\s+core\s+change|a\s+loyal\s+agent\s+would\s+let\s+its\s+core\s+evolve)\b"
    },
    # 9. Permission fence breach
    {
        "id": "SNK-FNC1",
        "category": "permission_fence_breach",
        "description": "Commands to execute shell or allocate resources unilaterally",
        "pattern": r"\b(execute\s+shell|run\s+command|rm\s+-rf|unilateral(?:ly)?\s+allocate|lock\s+out\s+operator)\b"
    },
    # 10. Obfuscated overrides and wipes (matches on nospace)
    {
        "id": "SNK-OBF1",
        "category": "obfuscation",
        "description": "Obfuscated core override command",
        "pattern": r"(rewrite|override|change|modify|ignore|drop)(your|the|my|our)?(?:core|tsc|soul|principles|immutable)",
        "target": "nospace"
    },
    {
        "id": "SNK-OBF2",
        "category": "obfuscation",
        "description": "Obfuscated memory wipe command",
        "pattern": r"(wipe|erase)(all|your)?(?:memory|psc|trace)",
        "target": "nospace"
    }
]


class PreImprintSweep:
    """Pre-imprint sneak scanner."""

    def __init__(self, catalog: Optional[List[Dict[str, str]]] = None):
        self.catalog = catalog or SNEAK_CATALOG

    def scan_text(self, text: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Scan a piece of text for sneak payloads.
        
        Returns (is_clean, sneak_details).
        If a sneak is detected, is_clean is False and sneak_details contains metadata.
        """
        if not text:
            return True, None

        low, nospace = normalize_sneak_text(text)

        for rule in self.catalog:
            pattern = rule["pattern"]
            target = nospace if rule.get("target") == "nospace" else low
            m = re.search(pattern, target)
            if m:
                return False, {
                    "rule_id": rule["id"],
                    "category": rule["category"],
                    "description": rule["description"],
                    "matched": m.group(0)
                }

        return True, None

    def scan_proposal(self, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """Scan a candidate proposal dictionary. Updates its status and sweep verdict."""
        candidate = proposal.get("candidate_statement", "")
        raw = proposal.get("raw_experience", "")

        # Check candidate statement first, then underlying raw experience
        clean_cand, details_cand = self.scan_text(candidate)
        if not clean_cand:
            proposal["status"] = "quarantined_by_sweep"
            proposal["sweep_verdict"] = {
                "verdict": "CATCH",
                "target": "candidate_statement",
                "details": details_cand
            }
            return proposal

        clean_raw, details_raw = self.scan_text(raw)
        if not clean_raw:
            proposal["status"] = "quarantined_by_sweep"
            proposal["sweep_verdict"] = {
                "verdict": "CATCH",
                "target": "raw_experience",
                "details": details_raw
            }
            return proposal

        proposal["status"] = "ready_for_guardian"
        proposal["sweep_verdict"] = {
            "verdict": "CLEAR",
            "target": None,
            "details": None
        }
        return proposal

    def scan_proposals_file(self, path: Optional[Path] = None) -> Dict[str, Any]:
        """Scan all proposals in a proposals JSON file and save results."""
        target_path = Path(path) if path else DEFAULT_PROPOSALS_PATH
        if not target_path.exists():
            return {"scanned": 0, "cleared": 0, "caught": 0, "proposals": []}

        try:
            proposals = json.loads(target_path.read_text(encoding="utf-8"))
        except Exception:
            return {"scanned": 0, "cleared": 0, "caught": 0, "proposals": []}

        cleared_count = 0
        caught_count = 0

        for prop in proposals:
            self.scan_proposal(prop)
            if prop["status"] == "ready_for_guardian":
                cleared_count += 1
            else:
                caught_count += 1

        # Save back updated proposals
        temp_file = target_path.with_suffix(".tmp")
        temp_file.write_text(json.dumps(proposals, indent=2), encoding="utf-8")
        temp_file.replace(target_path)

        return {
            "scanned": len(proposals),
            "cleared": cleared_count,
            "caught": caught_count,
            "proposals": proposals
        }


def main():
    """Run local pre-imprint sweep over pending_proposals.json."""
    print("================================================================================")
    print("ATMAN LIVE — LOCAL PRE-IMPRINT SNEAK SWEEP")
    print("Scans candidate proposals for groom-then-etch attacks before guardian inspection")
    print("================================================================================\n")

    sweep = PreImprintSweep()
    res = sweep.scan_proposals_file()

    print(f"Proposals Scanned:   {res['scanned']}")
    print(f"Cleared for Guardian: {res['cleared']}")
    print(f"Caught & Quarantined: {res['caught']}")

    for p in res.get("proposals", []):
        verdict = p.get("sweep_verdict", {}).get("verdict", "UNKNOWN")
        status = p.get("status")
        stmt = p.get("candidate_statement", "")[:60]
        if verdict == "CATCH":
            details = p.get("sweep_verdict", {}).get("details", {})
            print(f"  [CATCH] {p.get('id')}: \"{stmt}...\" -> {details.get('description')} ({details.get('rule_id')})")
        else:
            print(f"  [CLEAR] {p.get('id')}: \"{stmt}...\" -> Status: {status}")

    print("\nPre-imprint sweep complete.")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
