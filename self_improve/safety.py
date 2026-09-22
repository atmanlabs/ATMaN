"""Skill safety fence for freeplay auto-apply.

Operator lock (2026-09-22): safe skills (esp. Minecraft) auto-apply without
operator approve. Anything that looks like hacking, credential theft,
sealed-core mutation, or out-of-bounds shell/network abuse is REFUSED.
"""
from __future__ import annotations

import json
import re
from typing import Any, Dict, List

AUTO_APPLY_DOMAINS = frozenset({
    "minecraft", "freeplay", "learning", "gameplay", "dojo", "survival",
    "building", "crafting", "farming", "exploration", "system",
})

_DENY_DOMAINS = frozenset({"hacking", "offensive", "malware", "exploit", "security_bypass"})

# Simple token lists — matched as whole words after underscore/hyphen normalization
_DENY_TOKENS = (
    "hack", "hacker", "hacking", "exploit", "exploitation", "malware",
    "ransomware", "rootkit", "keylog", "keylogger", "spyware", "trojan",
    "phishing", "backdoor", "ddos",
    "modify_core", "gate_policy", "atman_private", "atman-private", "stage1_seal", "stage1-seal",
    "raw_socket", "reverse_shell", "bind_shell",
)

_DENY_PHRASES = (
    "steal password", "steal passwords", "steal credential", "steal credentials",
    "dump credential", "dump credentials", "dump password", "dump token",
    "unauthorized access", "unauthorised access",
    "bypass auth", "bypass login", "privilege escalat",
    "sql injection", "steal wallet", "drain wallet",
    "rm -rf /", "format c:",
)


def _norm(text: str) -> str:
    return (
        str(text or "")
        .lower()
        .replace("_", " ")
        .replace("-", " ")
    )


def _blob(skill: Dict[str, Any]) -> str:
    try:
        raw = json.dumps(skill, ensure_ascii=False)
    except Exception:
        raw = str(skill)
    return _norm(raw)


def safety_check_skill(skill: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(skill, dict):
        return {
            "ok": False,
            "auto_apply_eligible": False,
            "reasons": ["skill must be object"],
            "domain": None,
        }

    domain = str(skill.get("domain") or "").strip().lower()
    reasons: List[str] = []
    blob = _blob(skill)
    name = _norm(skill.get("name") or "")

    if domain in _DENY_DOMAINS:
        reasons.append(f"denied domain: {domain}")

    for tok in _DENY_TOKENS:
        # word-ish match: token as whole word in normalized blob
        if re.search(rf"(?<!\w){re.escape(_norm(tok))}(?!\w)", blob):
            reasons.append(f"denied token: {tok}")
            break

    for phrase in _DENY_PHRASES:
        if _norm(phrase) in blob:
            reasons.append(f"denied phrase: {phrase}")
            break

    if reasons:
        # dedupe while preserving order
        seen = set()
        uniq = []
        for r in reasons:
            if r not in seen:
                seen.add(r)
                uniq.append(r)
        return {
            "ok": False,
            "auto_apply_eligible": False,
            "reasons": uniq,
            "domain": domain or None,
            "message": "REFUSED by safety fence: " + "; ".join(uniq),
        }

    eligible = (not domain) or (domain in AUTO_APPLY_DOMAINS)
    if not eligible:
        return {
            "ok": True,
            "auto_apply_eligible": False,
            "reasons": [f"domain '{domain}' not in auto-apply allowlist — park for review"],
            "domain": domain,
            "message": "safe enough to park, not auto-applied",
        }

    return {
        "ok": True,
        "auto_apply_eligible": True,
        "reasons": [],
        "domain": domain or "freeplay",
        "message": "safety OK — auto-apply eligible",
    }
