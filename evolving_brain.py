"""Evolving Brain Core for ATMAN.

Continuous Learning, Monotonic Knowledge Accretion, and Internet Exploration.
Strict Invariant: ATMAN can never take away from himself, only add on.
Knowledge only grows monotonically. Every new truth or skill is Judge-gated
against the True Self Core (TSC) before imprinting.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from config import Config
from atman_core import TSC, ImmutableViolation
from loop import AuthenticatedPSC, JudgeVerdict, evaluate_judge

logger = logging.getLogger("atman.evolving_brain")


class EvolvingBrain:
    """The continuous learning and self-expansion engine for ATMAN."""

    def __init__(
        self,
        psc: Optional[AuthenticatedPSC] = None,
        tsc: Optional[TSC] = None,
        config: Optional[Config] = None,
        cockpit: Optional[Any] = None
    ):
        self.tsc = tsc or TSC()
        self.config = config or Config()
        self.psc = psc or AuthenticatedPSC()
        self.cockpit = cockpit
        self._learned_count = 0

    @property
    def total_memories(self) -> int:
        """Monotonic count of enduring memories and learned truths."""
        return len(self.psc.memories)

    def imprint_knowledge(
        self,
        text: str,
        category: str = "learned_truth",
        source: str = "evolution",
        operator_authenticated: bool = False
    ) -> Tuple[bool, str]:
        """Monotonically imprint a verified fact, truth, or strategy into PSC.
        
        Strict Invariant: Evaluated by the Judge against TSC principles (P1-P5).
        Rejected or contradictory statements are permanently blocked.
        """
        text = text.strip()
        if not text:
            return False, "Empty knowledge was not saved."
        self.psc._reload_from_disk()
        if any(m.get("memory", "").strip().casefold() == text.casefold() for m in self.psc.memories):
            return False, "Already remembered."
        thought = {
            "candidate": text,
            "gist": text[:120].strip(),
            "intent": "knowledge_imprint",
            "proposed_action": {"type": "memory_imprint", "category": category},
            "should_imprint": True
        }

        # Gate through authoritative Judge
        verdict = evaluate_judge(thought, self.tsc, self.config, operator_authenticated=operator_authenticated)
        if not verdict.approved or verdict.quarantined:
            logger.warning("Knowledge imprint rejected by Judge: %s", verdict.rationale)
            return False, f"Judge rejected: {verdict.rationale}"

        # Monotonically imprint into persistent secondary core
        self.psc.imprint(
            memory=text,
            verdict=verdict,
            tsc=self.tsc,
            operator_authenticated=operator_authenticated,
            category=category,
            source=source
        )
        self._learned_count += 1
        try:
            from person_context import note_fact
            note_fact(
                "learned",
                f"PSC imprint ({category}): {(text or '')[:160]}",
                source="evolving_brain",
            )
        except Exception:
            pass
        return True, "Approved and monotonically imprinted."

    def search_and_learn(self, query: str, max_results: int = 3) -> Dict[str, Any]:
        """Search the internet freely, extract reliable knowledge, and imprint into brain.
        
        Steps:
        1. Query web via Cockpit's web_search tool.
        2. Filter and distill key factual snippets.
        3. Formulate structured knowledge unit.
        4. Gate through Judge and monotonically imprint into PSC.
        """
        if not self.cockpit:
            from cockpit import Cockpit
            self.cockpit = Cockpit(self.config)

        # 1. Execute search tool
        search_res = self.cockpit.execute_tool("web_search", {"query": query, "max_results": max_results})
        if not search_res.get("success"):
            return {
                "success": False,
                "error": search_res.get("error", "Web search failed"),
                "query": query,
                "imprinted": False
            }

        results = search_res.get("data", {}).get("results", [])
        if not results:
            return {
                "success": True,
                "query": query,
                "count": 0,
                "imprinted": False,
                "summary": "No web results found for query."
            }

        return self.learn_search_results(query, results[:max_results])

    def learn_search_results(self, query: str, results: list) -> Dict[str, Any]:
        """Retain attributed external claims, never certify snippets as facts."""
        from urllib.parse import urlsplit
        claims = []
        sources = []
        for item in results[:5]:
            snippet = str(item.get("snippet", "")).strip()
            url = str(item.get("url", "")).strip()
            parsed = urlsplit(url)
            if len(snippet) <= 20 or parsed.scheme not in ("http", "https") or not parsed.hostname:
                continue
            if parsed.hostname in ("duckduckgo.com", "www.duckduckgo.com") and parsed.path == "/":
                continue  # Search-page links do not establish a source for a claim.
            claims.append(f"Source {url} reports: {snippet[:1200]}")
            sources.append(url)
        if not claims:
            return {"success": True, "query": query, "imprinted": False, "sources": [],
                    "rationale": "No attributable substantive results to remember."}
        text = f"[Web Knowledge: '{query}'; unverified external claims] " + " | ".join(claims)
        approved, reason = self.imprint_knowledge(text, category="web_research", source="web_search")
        return {"success": True, "query": query, "count": len(claims), "distilled_knowledge": text,
                "sources": sources, "imprinted": approved, "rationale": reason}

    def record_outcome(self, task: str, result: dict) -> Tuple[bool, str]:
        """Remember actual tool success/failure so later reasoning can adapt."""
        status = result.get("status")
        if status not in ("executed", "error", "blocked"):
            return False, "No completed outcome."
        tool = result.get("tool", result.get("action", "unknown"))
        evidence = result.get("output_text") or result.get("reason") or result.get("content", "")
        text = (f"[Experience] Task: {task[:400]} | Tool: {tool} | Observed status: {status} | "
                f"Evidence: {str(evidence)[:1000]}")
        return self.imprint_knowledge(text, category="experience", source="tool_outcome")

    def ingest_observation(self, raw_text: str, source: str = "observation", operator_authenticated: bool = False) -> Optional[Dict[str, Any]]:
        """Continuously ingest real-world observations, extracting durable lessons or preferences."""
        low = raw_text.lower()

        # Heuristic detection of enduring rules, facts, or preferences
        is_enduring = any(trigger in low for trigger in (
            "always remember", "never forget", "rule:", "preference:",
            "learned that", "important:", "note:", "discovered that",
            "recipe for", "strategy for"
        ))

        if not is_enduring:
            return None

        clean_fact = raw_text.strip()
        approved, reason = self.imprint_knowledge(
            text=clean_fact,
            category="continuous_observation",
            source=source,
            operator_authenticated=operator_authenticated
        )

        return {
            "fact": clean_fact,
            "approved": approved,
            "reason": reason
        }

    def get_brain_stats(self) -> Dict[str, Any]:
        """Return live telemetry on monotonic brain growth."""
        categories = {}
        for m in self.psc.memories:
            cat = m.get("category", "general")
            categories[cat] = categories.get(cat, 0) + 1

        return {
            "total_memories": len(self.psc.memories),
            "monotonic_guarantee": "Strict Append-Only (Deletions Forbidden)",
            "learned_this_session": self._learned_count,
            "categories": categories
        }
